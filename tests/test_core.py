from __future__ import annotations

import csv
import shutil
from pathlib import Path

import fitz
import pytest

from papersort.executor import apply_plan, undo_manifest
from papersort.exporter import export_bibtex, export_csv
from papersort.metadata import build_proposed_filename, normalize_doi, validate_rename_template
from papersort.models import PaperRecord, PlanItem
from papersort.planner import build_plan
from papersort.scanner import scan_folder


def make_pdf(path: Path, title: str, author: str, year: str, doi: str, extra: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 80), title, fontsize=16)
    page.insert_text((72, 110), f"{author}\n{year}\nDOI: {doi}\n{extra}", fontsize=11)
    doc.set_metadata({"title": title, "author": author, "subject": f"DOI: {doi}", "creationDate": f"D:{year}0101000000"})
    doc.save(path)
    doc.close()


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1234/ABC.567") == "10.1234/abc.567"


def test_scan_extracts_metadata_and_exact_duplicate(tmp_path: Path):
    original = tmp_path / "1.pdf"
    make_pdf(original, "A Useful Paper About Cats", "Ada Smith", "2025", "10.1234/cats.1")
    shutil.copy2(original, tmp_path / "copy.pdf")

    result = scan_folder(tmp_path)
    assert result.total == 2
    assert result.duplicates == 2
    assert all(r.duplicate_kind == "exact" for r in result.records)
    assert all(r.doi == "10.1234/cats.1" for r in result.records)
    assert all(r.year == "2025" for r in result.records)
    assert all("Smith" in r.proposed_filename for r in result.records)


def test_same_doi_nonidentical_is_flagged(tmp_path: Path):
    make_pdf(tmp_path / "a.pdf", "First Paper", "Alice Zhang", "2024", "10.5678/shared", "one")
    make_pdf(tmp_path / "b.pdf", "Second Paper", "Bob Li", "2024", "10.5678/shared", "two")
    result = scan_folder(tmp_path)
    assert {r.duplicate_kind for r in result.records} == {"doi"}


def test_custom_rename_template(tmp_path: Path):
    record = PaperRecord(
        path=tmp_path / "messy.pdf",
        size_bytes=123,
        sha256="b" * 64,
        title="Useful Research",
        authors=["Ada Smith"],
        year="2025",
        doi="10.1234/example",
    )
    assert build_proposed_filename(record, "{author}_{year}_{title}") == "Smith_2025_Useful_Research.pdf"
    assert build_proposed_filename(record, "{year}-{doi}") == "2025-10_1234_example.pdf"
    assert build_proposed_filename(record, "{title}.pdf") == "Useful_Research.pdf"
    with pytest.raises(ValueError, match="不支持的模板字段"):
        validate_rename_template("{journal}_{title}")


def test_plan_uses_custom_rename_template(tmp_path: Path):
    make_pdf(tmp_path / "messy.pdf", "Clean Research Title", "Ada Smith", "2026", "10.1111/example")
    result = scan_folder(tmp_path)
    plan = build_plan(result.records, rename_template="{author}-{year}")
    assert plan[0].target.name == "Smith-2026.pdf"


def test_apply_and_undo(tmp_path: Path):
    make_pdf(tmp_path / "messy.pdf", "Clean Research Title", "Ada Smith", "2026", "10.1111/example")
    result = scan_folder(tmp_path)
    plan = build_plan(result.records)
    assert len(plan) == 1
    assert plan[0].action == "rename"
    old_path = plan[0].source
    new_path = plan[0].target
    manifest = apply_plan(tmp_path, plan)
    assert not old_path.exists()
    assert new_path.exists()
    restored = undo_manifest(manifest)
    assert restored == 1
    assert old_path.exists()
    assert not new_path.exists()


def test_duplicate_rows_default_unselected(tmp_path: Path):
    first = tmp_path / "x.pdf"
    make_pdf(first, "Duplicate Study", "Kai Chen", "2023", "10.2222/dup")
    shutil.copy2(first, tmp_path / "y.pdf")
    result = scan_folder(tmp_path)
    plan = build_plan(result.records)
    assert plan
    assert all(not item.selected for item in plan)


def test_organize_by_year_uses_library_root(tmp_path: Path):
    nested = tmp_path / "Downloads" / "topic"
    make_pdf(nested / "messy.pdf", "A Better Filename", "Ada Smith", "2026", "10.3333/year")
    result = scan_folder(tmp_path)
    plan = build_plan(result.records, organize_by_year=True, root=tmp_path)
    assert len(plan) == 1
    assert plan[0].target.parent == (tmp_path / "2026").resolve()


def test_export_csv_and_bibtex(tmp_path: Path):
    record = PaperRecord(
        path=tmp_path / "paper.pdf",
        size_bytes=123,
        sha256="a" * 64,
        page_count=12,
        title="Useful Research",
        authors=["Ada Smith", "Kai Chen"],
        year="2025",
        doi="10.1234/example",
    )
    csv_path = export_csv([record], tmp_path / "library.csv")
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows[0][0:5] == ["file", "title", "authors", "year", "doi"]
    assert rows[1][1] == "Useful Research"
    assert rows[1][4] == "10.1234/example"

    bib_path = export_bibtex([record], tmp_path / "library.bib")
    text = bib_path.read_text(encoding="utf-8")
    assert "@article{Smith2025" in text
    assert "title = {Useful Research}" in text
    assert "author = {Ada Smith and Kai Chen}" in text
    assert "doi = {10.1234/example}" in text


def test_apply_rolls_back_when_batch_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    a2 = tmp_path / "a2.pdf"
    b2 = tmp_path / "b2.pdf"
    plan = [
        PlanItem(source=a, target=a2, action="rename", selected=True),
        PlanItem(source=b, target=b2, action="rename", selected=True),
    ]

    import papersort.executor as executor

    real_replace = executor.os.replace
    calls = 0

    def flaky_replace(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated failure")
        return real_replace(source, target)

    monkeypatch.setattr(executor.os, "replace", flaky_replace)
    with pytest.raises(RuntimeError, match="已尝试回滚"):
        apply_plan(tmp_path, plan)

    assert a.exists()
    assert b.exists()
    assert not a2.exists()
    assert not b2.exists()

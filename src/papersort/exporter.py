from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import PaperRecord


def export_csv(records: list[PaperRecord], destination: Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "file",
            "title",
            "authors",
            "year",
            "doi",
            "pages",
            "duplicate_kind",
            "duplicate_group",
            "warnings",
        ])
        for record in records:
            writer.writerow([
                str(record.path),
                record.title,
                "; ".join(record.authors),
                record.year,
                record.doi,
                record.page_count,
                record.duplicate_kind,
                record.duplicate_group,
                "; ".join(record.warnings),
            ])
    return destination


def _bib_escape(value: str) -> str:
    return (value or "").replace("\\", "\\textbackslash{}") .replace("{", "\\{").replace("}", "\\}")


def _bib_key(record: PaperRecord, used: set[str]) -> str:
    surname = "paper"
    if record.authors:
        author = record.authors[0].strip()
        surname = author.split(",", 1)[0] if "," in author else author.split()[-1]
    raw = f"{surname}{record.year or ''}"
    base = re.sub(r"[^A-Za-z0-9]+", "", raw) or "paper"
    key = base
    suffix = 2
    while key.lower() in used:
        key = f"{base}{suffix}"
        suffix += 1
    used.add(key.lower())
    return key


def export_bibtex(records: list[PaperRecord], destination: Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    entries: list[str] = []
    for record in records:
        key = _bib_key(record, used)
        fields: list[tuple[str, str]] = []
        if record.title:
            fields.append(("title", record.title))
        if record.authors:
            fields.append(("author", " and ".join(record.authors)))
        if record.year:
            fields.append(("year", record.year))
        if record.doi:
            fields.append(("doi", record.doi))
        fields.append(("file", str(record.path)))
        body = ",\n".join(f"  {name} = {{{_bib_escape(value)}}}" for name, value in fields)
        entries.append(f"@article{{{key},\n{body}\n}}")
    destination.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")
    return destination

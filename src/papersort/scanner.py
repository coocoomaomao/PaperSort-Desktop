from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from .duplicates import mark_duplicates
from .metadata import extract_paper_record
from .models import PaperRecord, ScanResult

ProgressCallback = Callable[[int, int, Path], None]


def discover_pdfs(root: Path) -> list[Path]:
    root = Path(root)
    if root.is_file():
        return [root] if root.suffix.lower() == ".pdf" else []
    return sorted(
        (p for p in root.rglob("*.pdf") if p.is_file() and ".papersort" not in p.parts),
        key=lambda p: str(p).lower(),
    )


def scan_paths(paths: Iterable[Path], root: Path | None = None, progress: ProgressCallback | None = None) -> ScanResult:
    pdfs = sorted({Path(p).resolve() for p in paths if Path(p).suffix.lower() == ".pdf"}, key=lambda p: str(p).lower())
    if root is None:
        root = pdfs[0].parent if pdfs else Path.cwd()
    records: list[PaperRecord] = []
    total = len(pdfs)
    for index, path in enumerate(pdfs, start=1):
        if progress:
            progress(index, total, path)
        records.append(extract_paper_record(path))
    mark_duplicates(records)
    return ScanResult(root=Path(root).resolve(), records=records)


def scan_folder(root: Path, progress: ProgressCallback | None = None) -> ScanResult:
    root = Path(root).resolve()
    return scan_paths(discover_pdfs(root), root=root, progress=progress)

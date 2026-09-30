from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


DuplicateKind = Literal["", "exact", "doi"]
ActionKind = Literal["rename", "skip"]


@dataclass(slots=True)
class PaperRecord:
    path: Path
    size_bytes: int
    sha256: str
    page_count: int = 0
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    doi: str = ""
    proposed_filename: str = ""
    duplicate_kind: DuplicateKind = ""
    duplicate_group: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def first_author(self) -> str:
        return self.authors[0] if self.authors else ""


@dataclass(slots=True)
class PlanItem:
    source: Path
    target: Path
    action: ActionKind
    selected: bool = True
    reason: str = ""


@dataclass(slots=True)
class ScanResult:
    root: Path
    records: list[PaperRecord]

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def renameable(self) -> int:
        return sum(1 for r in self.records if r.proposed_filename and r.proposed_filename != r.path.name)

    @property
    def duplicates(self) -> int:
        return sum(1 for r in self.records if r.duplicate_kind)

    @property
    def missing_metadata(self) -> int:
        return sum(1 for r in self.records if not r.title or not r.year or not r.authors)

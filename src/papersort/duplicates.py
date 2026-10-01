from __future__ import annotations

from collections import defaultdict

from .models import PaperRecord


def mark_duplicates(records: list[PaperRecord]) -> None:
    """Mark exact-file and same-DOI duplicates without deleting anything."""
    by_hash: dict[str, list[PaperRecord]] = defaultdict(list)
    by_doi: dict[str, list[PaperRecord]] = defaultdict(list)

    for record in records:
        by_hash[record.sha256].append(record)
        if record.doi:
            by_doi[record.doi].append(record)

    for digest, group in by_hash.items():
        if len(group) > 1:
            for record in group:
                record.duplicate_kind = "exact"
                record.duplicate_group = f"sha256:{digest[:12]}"

    for doi, group in by_doi.items():
        if len(group) > 1:
            for record in group:
                if record.duplicate_kind != "exact":
                    record.duplicate_kind = "doi"
                    record.duplicate_group = f"doi:{doi}"


def duplicate_groups(records: list[PaperRecord]) -> list[tuple[str, list[PaperRecord]]]:
    """Return stable duplicate groups for review UIs without changing files."""
    grouped: dict[str, list[PaperRecord]] = defaultdict(list)
    for record in records:
        if record.duplicate_group:
            grouped[record.duplicate_group].append(record)

    result: list[tuple[str, list[PaperRecord]]] = []
    for group_id in sorted(grouped):
        group = sorted(grouped[group_id], key=lambda record: str(record.path).lower())
        if len(group) > 1:
            result.append((group_id, group))
    return result

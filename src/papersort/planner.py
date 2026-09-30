from __future__ import annotations

from pathlib import Path

from .models import PaperRecord, PlanItem


def _unique_target(candidate: Path, reserved: set[Path]) -> Path:
    if candidate not in reserved and not candidate.exists():
        reserved.add(candidate)
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(2, 10000):
        alt = candidate.with_name(f"{stem}_{index}{suffix}")
        if alt not in reserved and not alt.exists():
            reserved.add(alt)
            return alt
    raise RuntimeError(f"无法生成唯一文件名: {candidate}")


def build_plan(
    records: list[PaperRecord],
    organize_by_year: bool = False,
    root: Path | None = None,
) -> list[PlanItem]:
    reserved: set[Path] = {r.path.resolve() for r in records}
    plan: list[PlanItem] = []
    library_root = Path(root).resolve() if root is not None else None

    for record in records:
        source = record.path.resolve()
        reserved.discard(source)
        filename = record.proposed_filename or source.name
        folder = source.parent
        if organize_by_year and record.year:
            # Organizing means a library-level year folder, not a nested year folder
            # inside every existing subdirectory.
            folder = (library_root or source.parent) / record.year
        candidate = (folder / filename).resolve()
        target = _unique_target(candidate, reserved)

        if target == source:
            plan.append(PlanItem(source=source, target=source, action="skip", selected=False, reason="文件名已规范"))
            reserved.add(source)
            continue

        reason_parts: list[str] = []
        if record.duplicate_kind == "exact":
            reason_parts.append("完全重复文件，建议人工确认后再处理")
        elif record.duplicate_kind == "doi":
            reason_parts.append("相同 DOI，建议人工确认")
        if record.warnings:
            reason_parts.append("元数据不完整")

        plan.append(
            PlanItem(
                source=source,
                target=target,
                action="rename",
                selected=not bool(record.duplicate_kind),
                reason="；".join(reason_parts),
            )
        )
    return plan

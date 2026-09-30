from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .models import PlanItem


def _history_dir(root: Path) -> Path:
    path = root / ".papersort" / "history"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _selected_operations(root: Path, plan: list[PlanItem]) -> list[tuple[Path, Path]]:
    operations: list[tuple[Path, Path]] = []
    seen_targets: set[Path] = set()
    for item in plan:
        if not item.selected or item.action != "rename" or item.source == item.target:
            continue
        source = item.source.resolve()
        target = item.target.resolve()
        try:
            source.relative_to(root)
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError("PaperSort 只允许在所选文献文件夹内修改文件") from exc
        if source in seen_targets:
            raise ValueError(f"整理计划存在路径依赖，暂不执行: {source}")
        if target in seen_targets:
            raise ValueError(f"整理计划存在重复目标路径: {target}")
        seen_targets.add(target)
        if not source.exists():
            raise FileNotFoundError(source)
        if target.exists():
            raise FileExistsError(target)
        operations.append((source, target))
    return operations


def apply_plan(root: Path, plan: list[PlanItem]) -> Path:
    root = Path(root).resolve()
    operations = _selected_operations(root, plan)
    completed: list[tuple[Path, Path]] = []

    try:
        for source, target in operations:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
            completed.append((source, target))
    except Exception as exc:
        rollback_errors: list[str] = []
        for source, target in reversed(completed):
            try:
                if target.exists() and not source.exists():
                    source.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(target, source)
            except Exception as rollback_exc:  # pragma: no cover - filesystem edge case
                rollback_errors.append(f"{target} → {source}: {rollback_exc}")
        detail = f"修改过程中出错，已尝试回滚: {exc}"
        if rollback_errors:
            detail += "；以下项目需要人工检查：" + " | ".join(rollback_errors)
        raise RuntimeError(detail) from exc

    history = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "operations": [{"source": str(source), "target": str(target)} for source, target in completed],
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    manifest = _history_dir(root) / f"{stamp}.json"
    manifest.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def latest_manifest(root: Path) -> Path | None:
    history = _history_dir(Path(root).resolve())
    files = sorted(history.glob("*.json"), reverse=True)
    return files[0] if files else None


def undo_manifest(manifest: Path) -> int:
    manifest = Path(manifest)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    operations = data.get("operations", [])
    restored = 0
    for op in reversed(operations):
        source = Path(op["source"])
        target = Path(op["target"])
        if not target.exists():
            continue
        if source.exists():
            raise FileExistsError(f"撤销目标已存在，未覆盖: {source}")
        source.parent.mkdir(parents=True, exist_ok=True)
        os.replace(target, source)
        restored += 1
    manifest.rename(manifest.with_suffix(".undone.json"))
    return restored

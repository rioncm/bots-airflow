from __future__ import annotations

from pathlib import Path


def candidate_botscore_roots(project_root: Path) -> tuple[Path, ...]:
    workspace_root = project_root.parent
    sibling_root = workspace_root / 'bots_edi'
    return (
        (workspace_root / 'bots_core' / 'src').resolve(),
        (sibling_root / 'botscore' / 'src').resolve(),
        (sibling_root / 'bots').resolve(),
    )


def find_local_botscore_checkout(project_root: Path) -> tuple[Path, Path] | None:
    for root in candidate_botscore_roots(project_root):
        package_root = root / 'botscore'
        if package_root.exists():
            return root, package_root.resolve()
    return None

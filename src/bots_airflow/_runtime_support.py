from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ._core_discovery import find_local_botscore_checkout


def _resolve_project_root() -> Path:
    package_root = Path(__file__).resolve().parent
    if package_root.parent.name == 'src':
        return package_root.parent.parent
    return package_root.parent


def ensure_botscore_importable() -> None:
    if importlib.util.find_spec('botscore') is not None:
        return

    bots_spec = importlib.util.find_spec('bots')
    if bots_spec is not None and bots_spec.submodule_search_locations:
        package_root = Path(next(iter(bots_spec.submodule_search_locations))).resolve()
        candidate_root = package_root.parent
        if (candidate_root / 'botscore').exists():
            candidate_text = str(candidate_root)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            return

    fallback = find_local_botscore_checkout(_resolve_project_root())
    if fallback is not None:
        fallback_root, _package_root = fallback
        fallback_text = str(fallback_root)
        if fallback_text not in sys.path:
            sys.path.insert(0, fallback_text)

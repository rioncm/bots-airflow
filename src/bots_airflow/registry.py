from __future__ import annotations

import importlib
from types import ModuleType

ModuleRef = str | ModuleType

_IMPORT_REGISTRY: dict[tuple[str, ...], ModuleRef] = {}


def _module_file(module: ModuleType, key: tuple[str, ...]) -> str:
    return getattr(module, '__file__', '') or f'<registered:{"/".join(key)}>'


def register_import(key: tuple[str, ...], module: ModuleRef) -> None:
    _IMPORT_REGISTRY[tuple(key)] = module


def register_grammar(editype: str, grammarname: str, module: ModuleRef) -> None:
    register_import(('grammars', editype, grammarname), module)


def register_mapping(name: str, module: ModuleRef) -> None:
    register_import(('mappings', *name.split('.')), module)


def resolve_import(*key: str) -> tuple[ModuleType, str] | None:
    module_ref = _IMPORT_REGISTRY.get(tuple(key))
    if module_ref is None:
        return None

    if isinstance(module_ref, ModuleType):
        return module_ref, _module_file(module_ref, tuple(key))

    module = importlib.import_module(module_ref)
    return module, _module_file(module, tuple(key))


def clear_import_registry() -> None:
    _IMPORT_REGISTRY.clear()


def registry_snapshot() -> dict[tuple[str, ...], str]:
    snapshot = {}
    for key, value in _IMPORT_REGISTRY.items():
        if isinstance(value, ModuleType):
            snapshot[key] = _module_file(value, key)
        else:
            snapshot[key] = value
    return snapshot

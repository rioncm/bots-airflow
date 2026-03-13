from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GrammarSpec:
    """Minimal grammar descriptor for the Airflow-facing translator facade."""

    editype: str
    messagetype: str
    usersys_root: str | Path | None = None
    charset: str = 'utf-8'
    module: str | Any | None = None
    support_modules: dict[str, str | Any] = field(default_factory=dict)


def coerce_grammar_spec(value: GrammarSpec | dict[str, Any] | Any) -> GrammarSpec:
    if isinstance(value, GrammarSpec):
        return value

    if isinstance(value, dict):
        return GrammarSpec(**value)

    editype = getattr(value, 'editype', None)
    messagetype = getattr(value, 'messagetype', None)
    usersys_root = getattr(value, 'usersys_root', None)
    charset = getattr(value, 'charset', 'utf-8')
    module = getattr(value, 'module', None)
    support_modules = getattr(value, 'support_modules', {})

    if editype and messagetype:
        return GrammarSpec(
            editype=editype,
            messagetype=messagetype,
            usersys_root=usersys_root,
            charset=charset,
            module=module,
            support_modules=dict(support_modules or {}),
        )

    raise TypeError(
        'Grammar specification must be a GrammarSpec, a mapping, or an object '
        'with editype and messagetype attributes.'
    )

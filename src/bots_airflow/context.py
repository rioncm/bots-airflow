from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class TranslationContext:
    """Explicit per-run values passed in by Airflow or other callers."""

    frompartner: str = ''
    topartner: str = ''
    alt: str = ''
    testindicator: str = ''
    reference: str = '1'
    metadata: Mapping[str, Any] = field(default_factory=dict)
    values: Mapping[str, Any] = field(default_factory=dict)
    partners: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def value(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def partner_value(self, partner_id: str, field: str, default: Any = '') -> Any:
        if not partner_id:
            return default
        return self.partners.get(partner_id, {}).get(field, default)


def coerce_translation_context(
    value: TranslationContext | Mapping[str, Any] | None,
) -> TranslationContext:
    if value is None:
        return TranslationContext()
    if isinstance(value, TranslationContext):
        return value
    if isinstance(value, Mapping):
        return TranslationContext(**value)
    raise TypeError(
        'Translation context must be a TranslationContext, a mapping, or None.'
    )

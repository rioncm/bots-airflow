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

    def required_value(self, key: str, *, allow_blank: bool = True) -> Any:
        value = self.value(key, None)
        if value is None:
            raise ValueError(f"Required context.values[{key!r}] was not provided.")
        if not allow_blank and isinstance(value, str) and value.strip() == '':
            raise ValueError(f"Required context.values[{key!r}] was blank.")
        return value

    def _resolve_partner_id(self, partner_id: str) -> str:
        if partner_id in ('from', 'frompartner'):
            return self.frompartner
        if partner_id in ('to', 'topartner'):
            return self.topartner
        return partner_id

    def partner_value(self, partner_id: str, field: str, default: Any = '') -> Any:
        resolved_partner_id = self._resolve_partner_id(partner_id)
        if not resolved_partner_id:
            return default
        return self.partners.get(resolved_partner_id, {}).get(field, default)

    def required_partner_value(
        self,
        partner_id: str,
        field: str,
        *,
        allow_blank: bool = True,
    ) -> Any:
        resolved_partner_id = self._resolve_partner_id(partner_id)
        if not resolved_partner_id:
            raise ValueError(
                f"Required partner reference {partner_id!r} did not resolve to a partner id."
            )

        value = self.partner_value(partner_id, field, None)
        if value is None:
            raise ValueError(
                f"Required partner field {field!r} was not provided for partner "
                f"{resolved_partner_id!r}."
            )
        if not allow_blank and isinstance(value, str) and value.strip() == '':
            raise ValueError(
                f"Required partner field {field!r} for partner {resolved_partner_id!r} was blank."
            )
        return value


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

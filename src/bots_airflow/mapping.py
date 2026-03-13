from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .context import TranslationContext, coerce_translation_context

PartnerLookup = Callable[[str, str, Any], Any]
CodeLookup = Callable[..., Any]
PersistLookup = Callable[[str, Any], Any]
PersistStore = Callable[[str, Any], None]
UniqueValue = Callable[[str], Any]


@dataclass(frozen=True)
class MappingServices:
    """Stable helper interfaces shared across mapping instances."""

    partner_lookup: PartnerLookup | None = None
    code_lookup: CodeLookup | None = None
    persist_lookup: PersistLookup | None = None
    persist_store: PersistStore | None = None
    unique_value: UniqueValue | None = None


class BaseMapping(ABC):
    """
    Base class for state-light mappings.

    Stable dependencies belong on the instance. Per-run values belong in the
    TranslationContext passed to translate(...).
    """

    def __init__(
        self,
        *,
        services: MappingServices | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        self.services = services or MappingServices()
        self.options = dict(options or {})

    def main(self, inn, out, **kwargs):
        context = coerce_translation_context(kwargs.pop('context', None))
        return self.translate(inn, out, context=context, **kwargs)

    @abstractmethod
    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        raise NotImplementedError

    def partner_value(
        self,
        context: TranslationContext,
        partner_id: str,
        field: str,
        default: Any = '',
    ) -> Any:
        if self.services.partner_lookup is not None and partner_id:
            value = self.services.partner_lookup(partner_id, field, default)
            if value not in (None, ''):
                return value
        return context.partner_value(partner_id, field, default)

    def context_value(self, context: TranslationContext, key: str, default: Any = None) -> Any:
        return context.value(key, default)

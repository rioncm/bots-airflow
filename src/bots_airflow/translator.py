from __future__ import annotations

from pathlib import Path
from typing import Any

from .context import TranslationContext, coerce_translation_context
from .mapping import BaseMapping, MappingServices
from .registry import register_grammar
from .runner import TranslationRequest, TranslationResult
from .runner import translate_text as _translate_text
from .specs import GrammarSpec, coerce_grammar_spec


class Translator:
    """Thin facade for direct parse/map/write execution in Airflow tasks."""

    def __init__(
        self,
        *,
        grammar_in: GrammarSpec | dict[str, Any] | Any,
        grammar_out: GrammarSpec | dict[str, Any] | Any,
        map: Any,
        services: MappingServices | None = None,
        mapping_options: dict[str, Any] | None = None,
        runtime_root: str | Path | None = None,
        **compat_kwargs,
    ) -> None:
        compat_kwargs.pop('usersys_root', None)
        legacy_mapping_source = compat_kwargs.pop('mapping_source', None)
        if legacy_mapping_source not in (None, 'python'):
            raise TypeError(
                'mapping_source is no longer supported; use a registered or importable '
                'mapping module instead.'
            )
        if compat_kwargs:
            unexpected = ', '.join(sorted(compat_kwargs))
            raise TypeError(f'Unexpected keyword argument(s): {unexpected}')

        self.grammar_in = coerce_grammar_spec(grammar_in)
        self.grammar_out = coerce_grammar_spec(grammar_out)
        self.map = map
        self.services = services or MappingServices()
        self.mapping_options = dict(mapping_options or {})
        self.runtime_root = runtime_root
        self._register_grammar_specs()

    def _resolve_mapping_reference(self) -> dict[str, Any]:
        if isinstance(self.map, str):
            return {
                'mapping_module': self.map,
            }

        mapping_object = self.map

        if isinstance(self.map, type):
            if issubclass(self.map, BaseMapping):
                mapping_object = self.map(
                    services=self.services,
                    options=self.mapping_options,
                )
            else:
                mapping_object = self.map()

        return {'mapping': mapping_object}

    def _register_grammar_spec(self, spec: GrammarSpec) -> None:
        if spec.module is not None:
            register_grammar(spec.editype, spec.messagetype, spec.module)
        for grammarname, module in spec.support_modules.items():
            register_grammar(spec.editype, grammarname, module)

    def _register_grammar_specs(self) -> None:
        self._register_grammar_spec(self.grammar_in)
        self._register_grammar_spec(self.grammar_out)

    def translate_text(
        self,
        input_text: str,
        *,
        context: TranslationContext | dict[str, Any] | None = None,
        filename: str = 'input.edi',
        output_filename: str | None = None,
        mapping_kwargs: dict[str, Any] | None = None,
    ) -> TranslationResult:
        run_context = coerce_translation_context(context)

        request = TranslationRequest(
            input_text=input_text,
            from_editype=self.grammar_in.editype,
            from_messagetype=self.grammar_in.messagetype,
            to_editype=self.grammar_out.editype,
            to_messagetype=self.grammar_out.messagetype,
            runtime_root=self.runtime_root,
            filename=filename,
            output_filename=output_filename,
            charset=self.grammar_in.charset,
            frompartner=run_context.frompartner,
            topartner=run_context.topartner,
            alt=run_context.alt,
            testindicator=run_context.testindicator,
            reference=run_context.reference,
            context=run_context,
            mapping_kwargs=dict(mapping_kwargs or {}),
            **self._resolve_mapping_reference(),
        )
        return _translate_text(request)

    def translate(
        self,
        input_path: str | Path,
        output_path: str | Path,
        *,
        context: TranslationContext | dict[str, Any] | None = None,
        mapping_kwargs: dict[str, Any] | None = None,
    ) -> TranslationResult:
        input_file = Path(input_path)
        output_file = Path(output_path)
        result = self.translate_text(
            input_file.read_text(encoding=self.grammar_in.charset),
            context=context,
            filename=input_file.name,
            output_filename=output_file.name,
            mapping_kwargs=mapping_kwargs,
        )

        if result.output_text is not None:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(result.output_text, encoding=self.grammar_out.charset)

        return result


def init(**kwargs) -> Translator:
    return Translator(**kwargs)

from __future__ import annotations

import importlib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bootstrap import RuntimePaths, ensure_runtime

EDITYPE_EXTENSIONS = {
    'csv': '.csv',
    'edifact': '.edi',
    'fixed': '.txt',
    'json': '.json',
    'jsonnocheck': '.json',
    'templatehtml': '.html',
    'x12': '.edi',
    'xml': '.xml',
    'xmlnocheck': '.xml',
}


@dataclass
class TranslationRequest:
    input_text: str
    from_editype: str
    from_messagetype: str
    to_editype: str
    to_messagetype: str
    mapping_module: str | None = None
    mapping: Any = None
    usersys_root: str | Path | None = None
    runtime_root: str | Path | None = None
    mapping_source: str = 'usersys'
    filename: str = 'input.edi'
    output_filename: str | None = None
    charset: str = 'utf-8'
    frompartner: str = ''
    topartner: str = ''
    alt: str = ''
    testindicator: str = ''
    reference: str = '1'
    context: Any = None
    mapping_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResult:
    runtime: RuntimePaths
    task_dir: Path
    input_path: Path
    output_path: Path | None
    output_text: str | None
    mapping_result: Any
    ta_info: dict[str, Any]


def _default_output_filename(editype: str) -> str:
    return f'output{EDITYPE_EXTENSIONS.get(editype, ".txt")}'


def _load_mapping_main(mapping_module: str, mapping_source: str):
    if mapping_source == 'usersys':
        from bots import botslib

        module, _modulefile = botslib.botsimport('mappings', *mapping_module.split('.'))
    elif mapping_source == 'python':
        module = importlib.import_module(mapping_module)
    else:
        raise ValueError(f'Unsupported mapping_source {mapping_source!r}.')

    if not hasattr(module, 'main'):
        raise AttributeError(f'Mapping module {mapping_module!r} does not define main(...).')

    return module.main


def _coerce_mapping_main(mapping: Any):
    if hasattr(mapping, 'main') and callable(mapping.main):
        return mapping.main
    if callable(mapping):
        return mapping
    raise TypeError('Mapping must be a callable or an object with main(...).')


def _mapping_divtext(request: TranslationRequest) -> str:
    if request.mapping_module:
        return request.mapping_module

    if request.mapping is None:
        return ''

    return getattr(
        request.mapping,
        '__qualname__',
        getattr(request.mapping, '__name__', request.mapping.__class__.__name__),
    )


def translate_text(request: TranslationRequest) -> TranslationResult:
    runtime = ensure_runtime(
        usersys_root=request.usersys_root,
        runtime_root=request.runtime_root,
    )

    from bots import inmessage, outmessage
    from bots.botsconfig import DONE

    task_dir = Path(
        tempfile.mkdtemp(prefix='translate-', dir=str(runtime.runtime_root))
    )
    input_path = task_dir / request.filename
    output_path = task_dir / (
        request.output_filename or _default_output_filename(request.to_editype)
    )

    input_path.write_text(request.input_text, encoding=request.charset)

    edi_file = inmessage.parse_edi_file(
        editype=request.from_editype,
        messagetype=request.from_messagetype,
        filename=str(input_path),
        charset=request.charset,
        frompartner=request.frompartner,
        topartner=request.topartner,
        alt=request.alt,
        testindicator=request.testindicator,
    )
    edi_file.checkforerrorlist()

    messages = list(edi_file.nextmessage())
    if len(messages) != 1:
        raise ValueError(
            f'translate_text currently expects exactly one split message, found {len(messages)}.'
        )

    inn = messages[0]
    out = outmessage.outmessage_init(
        editype=request.to_editype,
        messagetype=request.to_messagetype,
        filename=str(output_path),
        charset=request.charset,
        frompartner=request.frompartner or inn.ta_info.get('frompartner', ''),
        topartner=request.topartner or inn.ta_info.get('topartner', ''),
        alt=request.alt or inn.ta_info.get('alt', ''),
        testindicator=request.testindicator or inn.ta_info.get('testindicator', ''),
        reference=request.reference or inn.ta_info.get('reference', '1'),
        statust=0,
        divtext=_mapping_divtext(request),
    )

    if request.mapping is not None:
        mapping_main = _coerce_mapping_main(request.mapping)
    elif request.mapping_module:
        mapping_main = _load_mapping_main(
            mapping_module=request.mapping_module,
            mapping_source=request.mapping_source,
        )
    else:
        raise ValueError('TranslationRequest requires mapping or mapping_module.')

    mapping_kwargs = dict(request.mapping_kwargs)
    if request.context is not None and 'context' not in mapping_kwargs:
        mapping_kwargs['context'] = request.context

    mapping_result = mapping_main(inn=inn, out=out, **mapping_kwargs)

    if out.ta_info.get('statust') == DONE:
        return TranslationResult(
            runtime=runtime,
            task_dir=task_dir,
            input_path=input_path,
            output_path=None,
            output_text=None,
            mapping_result=mapping_result,
            ta_info=dict(out.ta_info),
        )

    out.writeall()
    output_text = output_path.read_text(encoding=request.charset)

    return TranslationResult(
        runtime=runtime,
        task_dir=task_dir,
        input_path=input_path,
        output_path=output_path,
        output_text=output_text,
        mapping_result=mapping_result,
        ta_info=dict(out.ta_info),
    )

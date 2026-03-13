# Quickstart

This quickstart assumes:

- you have Python 3.11+
- you can install package dependencies
- you want to run translations explicitly from Python, not through Bots engine routes

## Install

For local development:

```bash
pip install -e .[dev,test,docs]
```

## Basic facade usage

```python
from pathlib import Path

from bots_airflow import TranslationContext, init
from bots_airflow.grammar.livingspaces import x12_in
from bots_airflow.grammar.osas import sscc_out
from bots_airflow.mappings.x12.ls_to_osas_sscc import LivingSpacesToOsasSscc

translator = init(
    grammar_in=x12_in,
    grammar_out=sscc_out,
    map=LivingSpacesToOsasSscc,
)

translator.translate(
    Path("input.edi"),
    Path("output.csv"),
    context=TranslationContext(
        frompartner="DEMORETAIL",
        topartner="DEMOFULFILL",
        partners={
            "DEMORETAIL": {"attr2": "900001"},
        },
    ),
)
```

## Low-level usage

If you want to work directly with text:

```python
from bots_airflow import GrammarSpec, init

translator = init(
    grammar_in=GrammarSpec(
        editype="x12",
        messagetype="x12",
        module="bots_airflow.grammars.x12.x12",
        support_modules={
            "850_ls_inbound4010": "bots_airflow.grammars.x12._850_ls_inbound4010",
        },
    ),
    grammar_out=GrammarSpec(
        editype="x12",
        messagetype="850_ls_inbound4010",
        module="bots_airflow.grammars.x12._850_ls_inbound4010",
        support_modules={
            "x12": "bots_airflow.grammars.x12.x12",
        },
    ),
    map="bots_airflow.mappings.x12.pass_through",
    mapping_source="python",
)

result = translator.translate_text(input_text)
print(result.output_text)
```

## Notes

- `TranslationContext` is the preferred place for run-specific values.
- mapping constructors should hold stable dependencies and options, not per-run state.
- `usersys/` is still present for compatibility, but new flows should use first-class `bots_airflow.grammars` and `bots_airflow.mappings` modules.

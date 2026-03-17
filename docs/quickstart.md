# Quickstart

This quickstart assumes:

- you have Python 3.11+
- you want to run translations explicitly from Python, not through Bots engine routes
- your project-specific grammars and mappings live in your own runtime modules

## Install in Airflow

Production install:

```bash
pip install bots-airflow
pip install my-company-edi-runtime
```

If your runtime modules are not distributed as a wheel, make sure they are still
importable in the Airflow environment, for example by placing them on the DAG
`PYTHONPATH`.

## Local development

For local workspace development against the sibling extracted runtime checkout:

```bash
pip install -e ../bots_core
pip install -e .[dev,test,docs]
```

If `botscore` has already been published and you do not have the sibling checkout,
the normal editable install also works:

```bash
pip install -e .[dev,test,docs]
```

## Direct use with imported modules

```python
import my_company_edi.grammars.csv.order_lines_out as order_lines_out
import my_company_edi.grammars.json.orders_in as orders_in

from bots_airflow import GrammarSpec, TranslationContext, init
from my_company_edi.mappings.order_lines import OrdersToCsv

translator = init(
    grammar_in=GrammarSpec(
        editype="json",
        messagetype="orders",
        module=orders_in,
    ),
    grammar_out=GrammarSpec(
        editype="csv",
        messagetype="order_lines",
        module=order_lines_out,
    ),
    map=OrdersToCsv,
)

result = translator.translate_text(
    input_text,
    context=TranslationContext(
        reference="batch-001",
        values={"order_prefix": "WEB-"},
    ),
)
print(result.output_text)
```

## Use import path strings

If you prefer to keep the DAG code more declarative, use import path strings:

```python
from bots_airflow import GrammarSpec, TranslationContext, init

translator = init(
    grammar_in=GrammarSpec(
        editype="json",
        messagetype="orders",
        module="my_company_edi.grammars.json.orders_in",
    ),
    grammar_out=GrammarSpec(
        editype="csv",
        messagetype="order_lines",
        module="my_company_edi.grammars.csv.order_lines_out",
    ),
    map="my_company_edi.mappings.order_lines_module",
)

translator.translate(
    "input.json",
    "output.csv",
    context=TranslationContext(reference="batch-002"),
)
```

## Notes

- `TranslationContext` is the preferred place for run-specific values.
- mapping constructors should hold stable dependencies and options, not per-run state.
- registered mappings can be classes, callable objects, or importable modules that expose `main(...)`.
- the public package does not ship partner-specific grammars or mappings.

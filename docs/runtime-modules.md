# Runtime Modules

`bots_airflow` is a public runtime package. Your grammars and mappings are expected
to live outside that package and be imported at runtime.

## Where custom modules live

Typical options:

- a private wheel installed in the Airflow image, such as `my-company-edi-runtime`
- Python modules stored alongside your DAGs and made importable on the Airflow `PYTHONPATH`
- local workspace modules imported directly by task code

## Grammar references

`GrammarSpec` accepts either:

- an import path string
- an imported module object

Example with module objects:

```python
import my_company_edi.grammars.csv.order_lines_out as order_lines_out
import my_company_edi.grammars.json.orders_in as orders_in

from bots_airflow import GrammarSpec

grammar_in = GrammarSpec(
    editype="json",
    messagetype="orders",
    module=orders_in,
)

grammar_out = GrammarSpec(
    editype="csv",
    messagetype="order_lines",
    module=order_lines_out,
)
```

Example with import path strings:

```python
from bots_airflow import GrammarSpec

grammar_in = GrammarSpec(
    editype="json",
    messagetype="orders",
    module="my_company_edi.grammars.json.orders_in",
)

grammar_out = GrammarSpec(
    editype="csv",
    messagetype="order_lines",
    module="my_company_edi.grammars.csv.order_lines_out",
)
```

If your grammar needs support modules, use `support_modules`:

```python
GrammarSpec(
    editype="x12",
    messagetype="x12",
    module="my_company_edi.grammars.x12.envelope",
    support_modules={
        "850_inbound": "my_company_edi.grammars.x12.orders_850",
    },
)
```

## Mapping references

Mappings can be supplied as:

- a mapping class derived from `BaseMapping`
- an object with `main(...)`
- a callable
- an import path string for a module exposing `main(...)`

Example with a class:

```python
from bots_airflow import init
from my_company_edi.mappings.order_lines import OrdersToCsv

translator = init(
    grammar_in=grammar_in,
    grammar_out=grammar_out,
    map=OrdersToCsv,
)
```

Example with a module path string:

```python
translator = init(
    grammar_in=grammar_in,
    grammar_out=grammar_out,
    map="my_company_edi.mappings.order_lines_module",
)
```

## Registry aliases

If you want to decouple DAG code from the full module path, register an alias:

```python
from bots_airflow import register_mapping

register_mapping(
    "runtime.order_lines",
    "my_company_edi.mappings.order_lines_module",
)
```

Then use `map="runtime.order_lines"`.

## Deployment model

In Airflow, every component that imports DAG code should be able to import:

- `bots_airflow`
- `botscore`
- your own runtime modules

That usually means installing both `bots-airflow` and your private runtime package
into the same scheduler and worker image.

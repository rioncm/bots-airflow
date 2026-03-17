# bots-airflow

`bots_airflow` is an Airflow-oriented extraction of the core Bots EDI translation
runtime: grammar loading, parsing into message trees, mapping execution, and
serialization.

Architecture and release target: [docs/architecture.md](docs/architecture.md)

## Current scope

This package provides:

- a `botscore`-backed translation runtime for grammar loading, parse/tree handling,
  mapping execution, and serialization
- a lean bootstrap that initializes extracted runtime state in memory without the
  full Bots engine control path
- a direct translation runner that does not use Bots engine, routes, channels, or
  translate tables
- a thin `Translator` facade plus lower-level `TranslationRequest` and
  `translate_text(...)` APIs for direct task execution
- a registry-backed import hook for explicit grammar and mapping resolution
- an explicit `TranslationContext` model for per-run values
- a `BaseMapping` class and service model for state-light, dependency-injected
  mappings
- developer utilities for extracting reduced recorddefs packs from larger legacy
  sources

## Public boundary

`bots_airflow` is the public runtime package, not a distribution of partner-specific
flows.

The supported runtime:

- runs on `botscore`
- does not require the legacy Bots engine
- does not require `usersys`
- does not bundle project-specific grammars, mappings, or sample partner files

Project-specific grammars and mappings should live in your own runtime modules and
be installed or imported alongside `bots_airflow` in Airflow.

## Install

Published-package install:

```bash
pip install bots-airflow
```

This pulls in the declared standalone `botscore` dependency.

For local workspace development against the sibling extracted runtime checkout:

```bash
pip install -e ../bots_core
pip install -e .[dev,test,docs]
```

## Runtime modules

The intended production model is:

1. install `bots_airflow`
2. install your own private runtime package, or make your runtime modules importable
   on the Airflow `PYTHONPATH`
3. import those modules in DAG code and pass them to `bots_airflow`

Example with imported runtime modules:

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

The same runtime modules can also be referenced by import path strings:

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

## Layout

- `src/bots_airflow/bootstrap.py`
  Initializes the extracted runtime state and import paths needed for parse/map/write execution.
- `src/bots_airflow/context.py`
  Defines explicit per-run translation inputs passed from Airflow tasks and upstream code.
- `src/bots_airflow/translator.py`
  Provides the main Airflow-facing facade for direct translation execution.
- `src/bots_airflow/runner.py`
  Executes the low-level parse/map/write flow directly against the extracted runtime.
- `src/bots_airflow/registry.py`
  Registers explicit grammar and mapping modules for runtime import resolution.
- `src/bots_airflow/mapping.py`
  Defines mapping base classes and injected service interfaces.
- `src/bots_airflow/devtools/`
  Contains developer-only extraction and maintenance utilities.

## Developer utilities

To extract a reduced recorddefs pack for a grammar in your own runtime modules:

```bash
python3 -m bots_airflow.devtools.extract_recorddefs \
  --source-recorddefs path/to/legacy_recorddefs.py \
  --grammar my_company_edi.grammars.x12.orders_850 \
  --output path/to/generated_segments.py
```

This utility is intentionally outside the runtime path. Developers use it to turn
large shared segment catalogs into small reviewed Python modules that the runtime
imports directly.

## Mapping model

Use the mapping constructor for stable dependencies and options:

- partner or code resolver services
- feature flags
- mapping-level configuration

Use `TranslationContext` for per-run values:

- partner ids
- routing decisions
- metadata from upstream Airflow tasks
- run-specific configuration payloads

That split keeps mappings easy to test and makes retries explicit.

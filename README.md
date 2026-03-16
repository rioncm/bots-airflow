# bots-airflow

## Objective

`bots_airflow` is an Airflow-oriented extraction of the core Bots EDI translation runtime: grammar loading, parsing into message trees, mapping execution, and serialization.

Architecture and release target: [docs/architecture.md](docs/architecture.md)

The goal is to keep the pieces Bots is good at:

- grammar loading
- parsing into message trees
- mapping execution
- serialization

and move the rest into Airflow or explicit Python code:

- orchestration
- retries
- partner and route selection
- persistent business configuration
- downstream delivery

## Current scope

This package currently provides:

- a `botscore`-backed translation runtime for grammar loading, parse/tree handling, mapping execution, and serialization
- a lean bootstrap that initializes extracted runtime state in memory without the full Bots engine control path
- a direct translation runner that does not use Bots engine, routes, channels, or translate tables
- a thin `Translator` facade plus lower-level `TranslationRequest` and `translate_text(...)` APIs for direct task execution
- a registry-backed import hook for explicit grammar and mapping resolution
- an explicit `TranslationContext` model for per-run values
- a `BaseMapping` class and service model for state-light, dependency-injected mappings
- first-class `bots_airflow.grammar.*` helpers that package common `GrammarSpec` combinations
- first-class `bots_airflow.grammars.*` modules for Living Spaces X12, OSAS inventory JSON, and SSCC CSV paths
- first-class `bots_airflow.mappings.*` modules, including extracted SSCC and 846 mappings driven by `TranslationContext`
- a small remaining compatibility surface around upstream packaging and legacy metadata while the supported API stays direct module and registry-based

## Current boundaries

`bots_airflow` is centered on the extracted translation runtime, not on the legacy Bots engine.

Today the primary translation path runs on `botscore` and no longer goes through the full Bots `generalinit()` bootstrap, engine, routes, channels, translate tables, or public `usersys` conventions.

The supported runtime no longer bootstraps an internal `usersys` stub. Unsupported legacy `usersys` imports now fail explicitly instead of being satisfied by a temporary package shim.

This is still not a full fork or full replacement for the entire legacy Bots distribution. The supported runtime now targets standalone `botscore`, while some compatibility surfaces still exist upstream in the broader Bots codebase.

Django is no longer part of the primary translation runtime path for extracted flows. Remaining Django usage is confined to legacy upstream compatibility paths rather than the main Airflow parse/map/write flow.

Grammars do not need to be reachable through Bots `usersys` lookup rules. `GrammarSpec` can bind explicit module paths, and the registry-backed import hook satisfies grammar reads from those explicit registrations first.

For local development in this workspace, the bootstrap prefers a sibling standalone `../bots_edi/botscore/src` checkout. It can still fall back to `../bots_edi/bots` while the upstream repo remains in transition.

For packaging, docs, and tests in a local workspace, install the sibling `botscore`
package first:

```bash
pip install -e ../bots_edi/botscore
pip install -e .[dev,test,docs]
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
- `src/bots_airflow/grammar/`
  Exposes reviewed `GrammarSpec` helpers for common extracted flows.
- `src/bots_airflow/grammars/`
  Contains first-class grammar modules and extracted segment packs used by the runtime.
- `src/bots_airflow/mappings/`
  Contains first-class mapping modules that can be instantiated directly.
- `src/bots_airflow/devtools/`
  Contains developer-only extraction and maintenance utilities.
- `examples/fixtures/`
  Contains local sample inputs used by docs and smoke tests.

## Examples

Real extracted SSCC flow:

```python
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
    "input.edi",
    "sscc.csv",
    context=TranslationContext(
        frompartner="DEMORETAIL",
        topartner="DEMOFULFILL",
        partners={
            "DEMORETAIL": {"attr2": "900001"},
        },
    ),
)
```

This path does not use `transform.partnerlookup(...)`. Partner data is resolved from `TranslationContext` or injected mapping services instead.

Real extracted 846 flow:

```python
from bots_airflow import TranslationContext, init
from bots_airflow.grammar.osas import inventory_json_in
from bots_airflow.grammar.livingspaces import x12_846_out
from bots_airflow.mappings.json.inventory_to_livingspaces_846 import InventoryJsonToLivingSpaces846

translator = init(
    grammar_in=inventory_json_in,
    grammar_out=x12_846_out,
    map=InventoryJsonToLivingSpaces846,
)

translator.translate(
    "inventory.json",
    "inventory_846.edi",
    context=TranslationContext(
        values={
            "icn": "123456",
            "as_of_date": "20260313",
        },
    ),
)
```

Registry-only facade:

```python
from bots_airflow import GrammarSpec, TranslationContext, init
from bots_airflow.mappings.x12.ls_to_osas_sscc import LivingSpacesToOsasSscc

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
    map=LivingSpacesToOsasSscc,
)

translator.translate(
    "input.edi",
    "sscc.csv",
    context=TranslationContext(
        frompartner="DEMORETAIL",
        topartner="DEMOFULFILL",
        partners={"DEMORETAIL": {"attr2": "900001"}},
    ),
)
```

## Path to objective

The remaining path is:

1. keep runtime resolution focused on explicit module paths and registry-based imports
2. keep first-class grammars and mappings in local modules instead of legacy Bots package conventions
3. publish and release `botscore` as the supported runtime dependency
4. trim remaining compatibility-only release and documentation language now that `bots_airflow` depends on `botscore`
5. continue reducing any unsupported legacy references that are still only present for coexistence with the upstream Bots repo

## Developer utilities

To extract a reduced recorddefs pack for a specific grammar:

```bash
python3 -m bots_airflow.devtools.extract_recorddefs \
  --source-recorddefs examples/fixtures/legacy_records004010.py \
  --grammar bots_airflow.grammars.x12._850_ls_inbound4010 \
  --output src/bots_airflow/grammars/x12/segments_004010_ls_850.py
```

This utility is intentionally outside the runtime path. Developers use it to turn large shared segment catalogs into small reviewed Python modules that the runtime imports directly.

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

## Extraction strategy

The intended sequence is:

1. Replace Bots engine/runtime control with explicit Airflow tasks.
2. Move project grammars and mappings into first-class `src/bots_airflow/grammars` and `src/bots_airflow/mappings` modules.
3. Replace DB-backed mapping helpers with explicit context providers.
4. Keep the supported runtime module-first and registry-driven, with no internal `usersys` stub in the hot path.
5. Use `botscore` as the standalone runtime dependency and keep the supported path independent of the legacy package.
6. Remove any remaining compatibility-only release surface where practical.

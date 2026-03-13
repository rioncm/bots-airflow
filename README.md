# bots-airflow

`bots_airflow` is the start of an Airflow-oriented extraction layer around Bots core.

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

- a lean core bootstrap that initializes Bots parse/tree/write state in memory
- a direct translation runner that does not use Bots engine, routes, channels, or translate tables
- a registry-backed import hook for grammars and mappings
- a thin `Translator` facade for Airflow tasks
- an explicit `TranslationContext` model for per-run values
- a `BaseMapping` class for state-light, dependency-injected mappings
- first-class `bots_airflow.grammars.*` modules for Living Spaces X12, OSAS inventory JSON, and SSCC CSV paths
- first-class `bots_airflow.mappings.*` modules, including real SSCC and 846 mappings driven by `TranslationContext`
- a transitional local `usersys` tree for compatibility while extraction continues
- standalone repo scaffolding under `src/`, `docs/`, `tests/`, and `examples/`

## Important caveat

This is an extraction layer, not a full fork of Bots core.

Today it still depends on the `bots` runtime package distributed as `bots-ediint`, but it no longer runs the full Bots `generalinit()` path for translations. The current bootstrap configures only the core state needed for grammar loading, parse/tree handling, and write operations, plus minimal in-memory Django settings for Bots' translation/error machinery. For migration work in this workspace, the bootstrap can also fall back to a sibling `../bots_edi` checkout if the package is not installed.

Grammars no longer have to be reachable only through Bots `usersys` lookup rules. `GrammarSpec` can bind explicit module paths, and the import hook will satisfy Bots grammar reads from that registry first.

## Layout

- `src/bots_airflow/bootstrap.py`
  Initializes the minimum Bots globals and import paths needed for parse/tree/write.
- `src/bots_airflow/registry.py`
  Registers explicit grammar and mapping modules for Bots import calls.
- `src/bots_airflow/runner.py`
  Parses input text, loads a mapping explicitly, runs it, and returns output text.
- `src/bots_airflow/devtools/extract_recorddefs.py`
  Developer utility that extracts a minimal recorddefs module from a larger legacy source.
- `src/bots_airflow/grammars/`
  First-class grammar modules that no longer depend on Bots `usersys` naming.
- `src/bots_airflow/mappings/`
  First-class mapping modules that can be instantiated directly.
- `src/bots_airflow/usersys/`
  Transitional compatibility layer while more flows move to first-class modules.
- `examples/fixtures/`
  Local sample inputs used by docs and smoke tests.

## Example

Low-level runner:

```python
from pathlib import Path

from bots_airflow.runner import TranslationRequest, translate_text

request = TranslationRequest(
    input_text=Path(
        "examples/fixtures/sample_850.edi"
    ).read_text(),
    from_editype="x12",
    from_messagetype="850_ls_inbound4010",
    to_editype="x12",
    to_messagetype="850_ls_inbound4010",
    mapping_module="bots_airflow.mappings.x12.pass_through",
    mapping_source="python",
)

result = translate_text(request)
print(result.output_text)
```

Airflow-facing facade:

```python
from bots_airflow import GrammarSpec, TranslationContext, init
from bots_airflow.mapping import BaseMapping


class PassThrough(BaseMapping):
    def translate(self, inn, out, *, context, **kwargs):
        from bots import transform
        transform.inn2out(inn, out)


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
    map=PassThrough,
)

translator.translate(
    "input.edi",
    "output.edi",
    context=TranslationContext(
        frompartner="DEMORETAIL",
        topartner="DEMOFULFILL",
        metadata={"run_id": "abc123"},
    ),
)
```

Registry-only facade with no `usersys_root`:

```python
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
```

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

This path does not use `transform.partnerlookup(...)`. Partner data is resolved from
`TranslationContext` or injected mapping services instead.

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

## Developer utilities

To extract a reduced recorddefs pack for a specific grammar:

```bash
python3 -m bots_airflow.devtools.extract_recorddefs \
  --source-recorddefs examples/fixtures/legacy_records004010.py \
  --grammar bots_airflow.grammars.x12._850_ls_inbound4010 \
  --output src/bots_airflow/grammars/x12/segments_004010_ls_850.py
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

## Extraction strategy

The intended sequence is:

1. Replace Bots engine/runtime control with explicit Airflow tasks.
2. Move project grammars and mappings into first-class `src/bots_airflow/grammars` and `src/bots_airflow/mappings` modules.
3. Replace DB-backed mapping helpers with explicit context providers.
4. Keep `usersys` only as a compatibility layer while older flows are migrated.
5. Reduce or eliminate the remaining Django/bootstrap dependency where practical.

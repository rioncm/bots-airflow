# Architecture and Release Vision

This document describes the target end state for `bots_airflow`.

## Purpose

`bots_airflow` exists to narrow Bots down to the parts that are valuable in a
modern Apache Airflow DAG:

- grammar loading
- parsing into message trees
- mapping execution
- serialization

Everything else should move to explicit application code and orchestration outside
Bots.

## Product boundary

Target responsibility split:

- Airflow owns orchestration, retries, schedules, branching, persistence, callbacks,
  object storage, and business configuration.
- `bots_airflow` owns translation execution: parse, tree, map, write.
- project-specific grammars and mappings live outside the public package and are
  imported at runtime.
- developer tools under `src/bots_airflow/devtools` help extract and curate
  runtime artifacts.

What should not remain in the hot path:

- Bots engine
- Bots routes and channels
- Bots translate table
- Bots partner database schema
- required `usersys` runtime conventions
- full `generalinit()` bootstrap
- Django as a full translation runtime dependency

## Runtime model

Representative call shape:

```python
translator = init(
    grammar_in=...,
    grammar_out=...,
    map=...,
)

translator.translate(input_path, output_path, context=...)
```

Execution inputs should be explicit:

- input grammar
- output grammar
- mapping
- run context
- optional injected services

Execution state should not be pulled implicitly from a Bots database.

## Runtime modules

The public package no longer ships partner-specific flows. Consumers provide their
own runtime modules in one of two forms:

- importable package modules installed alongside `bots_airflow`
- local modules available on the Airflow `PYTHONPATH`

`GrammarSpec` accepts import path strings or imported module objects, and mappings
can be passed as classes, callables, objects with `main(...)`, or importable
module paths.

This keeps the public package generic while allowing project-specific flows to
evolve independently.

## Mapping model

Mappings should follow a clear split:

- constructor arguments for stable dependencies and options
- `TranslationContext` for per-run values

Examples of stable dependencies:

- unique value generator
- code lookup service
- partner resolver
- persistence adapter

Examples of per-run values:

- partner ids
- routing results
- purchase order numbers
- object storage paths
- metadata from prior Airflow tasks

This keeps mappings testable, deterministic, and retry-safe.

## Package layout

Public package shape:

- `src/bots_airflow/translator.py`
  Public translation facade.
- `src/bots_airflow/context.py`
  Per-run context model.
- `src/bots_airflow/mapping.py`
  Base classes and service interfaces.
- `src/bots_airflow/registry.py`
  Explicit grammar and mapping registry.
- `src/bots_airflow/devtools/`
  Developer-only extraction and maintenance utilities.

Project-specific runtime modules should live outside `src/bots_airflow`.

## Packaging target

The intended distribution model is:

- source code hosted in a GitHub repository
- Python distribution published to PyPI as `bots-airflow`
- import package name remains `bots_airflow`

Recommended packaging approach:

- use `pyproject.toml`
- use a modern build backend such as `hatchling`
- keep runtime dependencies minimal
- provide optional dependency groups for `dev`, `docs`, and `test`

Recommended packaging rule:

- the public distribution ships the runtime, not partner-specific grammars or mappings
- developer-generated runtime artifacts are reviewed and shipped in the owning
  runtime module package
- runtime should not generate or mutate package assets

## Repository target

Recommended repository layout:

```text
repo-root/
  src/bots_airflow/
  tests/
  docs/
  pyproject.toml
  README.md
  .github/workflows/
  .readthedocs.yaml
```

Project-specific runtime modules can live in separate repositories or local
workspace directories, but they should not be part of the public package boundary.

## CI/CD target

Recommended GitHub Actions pipeline:

### Pull Request / Push Validation

Jobs:

- lint
- unit tests
- package build
- documentation build

Typical checks:

- `python -m py_compile` or equivalent
- test suite with `pytest`
- package build with `python -m build`
- docs build for regression detection

### Release Build

Jobs:

- build sdist and wheel
- publish artifacts
- create GitHub release

Recommended publishing model:

- use PyPI Trusted Publisher with GitHub OIDC
- do not store long-lived PyPI API tokens in repository secrets unless absolutely necessary

## Definition of done

This package is close to its intended end state when:

- public translation APIs do not expose or require `usersys`
- runtime resolution is module-first and registry-driven
- no internal `usersys` stub remains in the supported runtime
- project-specific flows are maintained outside the public distribution
- Airflow supplies all business configuration explicitly
- package builds cleanly as a standard Python distribution
- docs build cleanly and publish to Read the Docs
- release publishing to PyPI is handled by CI

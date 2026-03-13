# Architecture and Release Vision

This document describes the target end state for `bots_airflow`.

It is intentionally a design target, not a statement that every item below is already implemented.

## Purpose

`bots_airflow` exists to narrow Bots down to the parts that are valuable in a modern Apache Airflow DAG:

- grammar loading
- parsing into message trees
- mapping execution
- serialization

Everything else should move to explicit application code and orchestration outside Bots.

## Product Boundary

Target responsibility split:

- Airflow owns orchestration, retries, schedules, branching, persistence, callbacks, object storage, and business configuration.
- `bots_airflow` owns translation execution: parse, tree, map, write.
- Developer tools under `src/bots_airflow/devtools` help extract and curate artifacts used by the runtime.
- Transitional compatibility code such as `usersys/` exists only to support migration and should shrink over time.

What should not remain in the hot path:

- Bots engine
- Bots routes and channels
- Bots translate table
- Bots partner database schema
- required `usersys` runtime conventions
- full `generalinit()` bootstrap
- Django as a full translation runtime dependency

## Runtime Model

The runtime API should stay explicit.

Representative call shapes:

```python
translator = init(
    grammar_in=...,
    grammar_out=...,
    map=...,
)

translator.translate(input_path, output_path, context=...)
```

or:

```python
result = translator.translate_text(input_text, context=...)
```

Execution inputs should be explicit:

- input grammar
- output grammar
- mapping
- run context
- optional injected services

Execution state should not be pulled implicitly from a Bots database.

## Mapping Model

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

## Package Layout

Target package shape:

- `src/bots_airflow/translator.py`
  Public translation facade.
- `src/bots_airflow/context.py`
  Per-run context model.
- `src/bots_airflow/mapping.py`
  Base classes and service interfaces.
- `src/bots_airflow/registry.py`
  Explicit grammar and mapping registry.
- `src/bots_airflow/grammars/`
  First-class grammar modules and extracted segment packs.
- `src/bots_airflow/mappings/`
  First-class mapping modules.
- `src/bots_airflow/devtools/`
  Developer-only extraction and maintenance utilities.
- `src/bots_airflow/usersys/`
  Transitional compatibility only.

## Packaging Target

The intended distribution model is:

- source code hosted in a GitHub repository
- Python distribution published to PyPI as `bots-airflow`
- import package name remains `bots_airflow`

Recommended packaging approach:

- use `pyproject.toml`
- use a modern build backend such as `hatchling`
- keep runtime dependencies minimal
- provide optional dependency groups for `dev`, `docs`, and `test`

Recommended package metadata:

- project name: `bots-airflow`
- python package: `bots_airflow`
- semantic versioning
- long description sourced from project docs or README
- project URLs for GitHub, documentation, issue tracker, and PyPI

Recommended packaging rule:

- runtime artifacts such as extracted segment packs ship as normal Python modules committed in the repo
- developer-generated artifacts are reviewed and committed before release
- runtime should not generate or mutate package assets

## Repository Target

Recommended repository layout:

```text
repo-root/
  src/bots_airflow/
  examples/
  tests/
  docs/
  pyproject.toml
  README.md
  .github/workflows/
  .readthedocs.yaml
```

Recommended top-level concerns:

- package source in `src/bots_airflow/`
- example fixtures in `examples/`
- tests separated from package code
- documentation in `docs/`
- GitHub Actions for test/build/release workflows
- Read the Docs configuration in `.readthedocs.yaml`

## CI/CD Target

Recommended GitHub Actions pipeline:

### Pull Request / Push Validation

Trigger:

- pull requests
- pushes to main branches

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

Trigger:

- version tag such as `v0.1.0`

Jobs:

- build sdist and wheel
- publish artifacts
- create GitHub release

Recommended publishing model:

- use PyPI Trusted Publisher with GitHub OIDC
- do not store long-lived PyPI API tokens in repository secrets unless absolutely necessary

Recommended release flow:

1. merge release-ready changes
2. create version tag
3. CI builds distribution
4. CI publishes to PyPI
5. CI creates GitHub release notes or attaches artifacts

## Documentation Target

The goal is full package documentation published separately from the legacy repo docs.

Recommended documentation stack:

- Markdown-based docs
- MkDocs with Material theme
- `mkdocstrings` for API reference pages
- Read the Docs for hosted builds

Why this stack:

- good code-and-guide balance
- simple Markdown authoring
- easy API extraction from Python modules
- straightforward Read the Docs support

Recommended documentation structure:

```text
docs/
  index.md
  architecture.md
  quickstart.md
  concepts/
  guides/
  examples/
  api/
```

Suggested pages:

- architecture and package boundaries
- quickstart
- grammar authoring
- mapping authoring
- context and services
- developer tools
- examples for 850 and 846 flows
- API reference
- release and publishing guide

## Read the Docs Target

Recommended Read the Docs setup:

- `.readthedocs.yaml` committed in the repo
- docs build installed via `pip install .[docs]`
- documentation versioned from Git tags or branches

Recommended behavior:

- build docs for pull requests in CI
- publish docs from the default branch
- allow tagged releases to appear as versioned docs

## Example End-to-End Flows

### 850 inbound

- input: X12 850
- parse using first-class `bots_airflow.grammars.x12`
- map with first-class `bots_airflow.mappings.x12`
- output: CSV or other explicit target format
- routing and downstream steps remain outside the package

### 846 outbound

- input: inventory JSON
- parse using first-class `bots_airflow.grammars.json`
- map with first-class `bots_airflow.mappings.json`
- output: X12 846
- control numbers and partner-specific values come from context or injected services

## Migration Target

The practical migration sequence should be:

1. move real grammars into `src/bots_airflow/grammars`
2. move real mappings into `src/bots_airflow/mappings`
3. replace DB-backed Bots helper usage with explicit context and services
4. use developer tools to extract minimal segment packs from legacy shared files
5. shrink and eventually remove `usersys` compatibility
6. reduce the bootstrap to only the parser/tree/write requirements
7. remove any remaining unnecessary Django coupling

## Definition of Done

This package is close to its intended end state when:

- first-class flows no longer depend on `usersys`
- first-class flows no longer depend on shared legacy recorddef catalogs
- first-class mappings do not use Bots DB-backed helpers
- Airflow supplies all business configuration explicitly
- package builds cleanly as a standard Python distribution
- docs build cleanly and publish to Read the Docs
- release publishing to PyPI is handled by CI

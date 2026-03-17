# Release and Documentation Workflow

This page describes the intended packaging and publishing workflow for
`bots_airflow`.

## Package build

Build the distribution locally with:

```bash
python -m build
```

This should produce:

- source distribution
- wheel

`bots_airflow` depends on standalone `botscore`, so the release order is:

1. build and publish `botscore`
2. update or verify the `bots_airflow` dependency range if needed
3. build and publish `bots_airflow`

## Test and validation

Recommended local validation sequence:

```bash
ruff check src/bots_airflow tests
pytest
mkdocs build --strict
python -m build
```

If the runtime extraction changed, also validate the sibling `botscore` package build:

```bash
cd ../bots_core
python -m build --wheel --sdist --no-isolation
```

For local workspace development, `bots_airflow` prefers a sibling `../bots_core/src`
checkout. That sibling checkout is a local development convenience, not the release
model.

## GitHub Actions

Recommended workflows:

- `ci.yml`
  Runs lint, tests, docs build, and package build on pull requests and branch pushes.
- `publish.yml`
  Publishes tagged releases to PyPI and attaches build artifacts to the workflow or release.

## PyPI publishing

Recommended model:

- publish package name `botscore` before any dependent `bots-airflow` release
- publish package name `bots-airflow`
- use GitHub Trusted Publisher via OIDC
- publish only from tagged releases

Suggested tag pattern:

```text
v0.1.0
v0.1.1
v0.2.0
```

## Read the Docs

Recommended flow:

- docs source remains in `docs/`
- `mkdocs.yml` points there as `docs_dir`
- `.readthedocs.yaml` installs the package with docs extras
- documentation is published from the default branch and versioned from tags

## Versioning

Both packages should use semantic versioning, but they do not need lockstep versions.

Recommended policy:

- `botscore` versions track runtime compatibility and parser/map/write behavior
- `bots_airflow` versions track the public Airflow-facing API, docs, and developer tooling
- project-specific runtime modules version independently from `bots_airflow`
- `bots_airflow` should express compatibility through its dependency range on `botscore`

Suggested release meanings:

- patch for fixes and low-risk compatibility work
- minor for new public runtime APIs, docs, or generic developer utilities that are backwards compatible
- major for breaking runtime or mapping API changes

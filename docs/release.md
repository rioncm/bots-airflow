# Release and Documentation Workflow

This page describes the intended packaging and publishing workflow for `bots_airflow`.

## Package build

Build the distribution locally with:

```bash
python -m build
```

This should produce:

- source distribution
- wheel

## Test and validation

Recommended local validation sequence:

```bash
ruff check src/bots_airflow tests
pytest
mkdocs build --strict
python -m build
```

## GitHub Actions

Recommended workflows:

- `ci.yml`
  Runs lint, tests, docs build, and package build on pull requests and branch pushes.
- `publish.yml`
  Publishes tagged releases to PyPI and attaches build artifacts to the workflow or release.

## PyPI publishing

Recommended model:

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

The package should use semantic versioning.

Suggested release meanings:

- patch for fixes and low-risk compatibility work
- minor for new flows, new grammars, or new mapping APIs that are backwards compatible
- major for breaking runtime or mapping API changes

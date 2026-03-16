# GitHub Actions Workflows

This directory contains the validation and publishing workflows for `bots_airflow`.

## `ci.yml`

Runs on pull requests and pushes to the main branches.

Jobs:

- `test`
  Installs `botscore` from the sibling `rioncm/bots-edi-k8s` checkout, then runs
  lint, tests, and a compile check across the supported Python versions.
- `docs`
  Installs `botscore` from the sibling checkout, installs docs dependencies, and
  builds the MkDocs site in strict mode.
- `build`
  Builds the source distribution and wheel for `bots_airflow`.

The explicit sibling checkout keeps CI aligned with the extracted-runtime development
model even before a new `botscore` release is published.

## `publish.yml`

Runs on version tags like `v0.1.0` and on manual dispatch.

Jobs:

- `build`
  Builds the `bots_airflow` source distribution and wheel and uploads them as an
  artifact.
- `publish-pypi`
  Publishes the uploaded distributions to PyPI using GitHub Trusted Publisher.

This workflow assumes the required standalone `botscore` release has already been
published according to the release order documented in `docs/release.md`.

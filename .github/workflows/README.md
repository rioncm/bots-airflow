# GitHub Actions Workflows

This directory contains the validation and publishing workflows for `bots_airflow`.

## `ci.yml`

Runs on pull requests and pushes to the main branches.

Jobs:

- `test`
  Installs the declared `botscore` dependency through normal package resolution, then
  runs lint, tests, and a compile check across the supported Python versions.
- `docs`
  Installs the declared `botscore` dependency, installs docs dependencies, and builds
  the MkDocs site in strict mode.
- `build`
  Builds the source distribution and wheel for `bots_airflow`.

This workflow intentionally validates the released package boundary. Local workspace
development can still install `../bots_edi/botscore`, but repo CI should not depend
on a sibling checkout existing in GitHub Actions.

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

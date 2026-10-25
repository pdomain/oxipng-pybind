---
kind: process
status: active
last_verified: 2026-10-25
---
# Unfinished Work

This file tracks active work that is not covered by durable process docs.

Last checked: 2026-10-25.

## What's Already Working

Repository release automation is implemented.

- Dependency refresh classification is wired in
  `.github/workflows/dependency-health.yml`.
- The latest hosted dependency refresh run passed.
- Dependency refresh PR #7 used the `no-release-needed` label and rebase
  auto-merge.
- GitHub Actions are enabled for `pdomain/oxipng-pybind`.
- The GitHub `pypi` and `testpypi` environments exist.
- `RELEASE_TAG_TOKEN`, `UPSTREAM_BUMP_TOKEN`, and `DEPENDENCY_REFRESH_TOKEN`
  exist as repository secrets.
- TestPyPI publishing passed through `.github/workflows/wheels.yml`.
- PyPI hosts `oxipng-pybind` at `10.2.1.post1`, with ten wheels and one
  source distribution. See [PyPI metadata](https://pypi.org/pypi/oxipng-pybind/json).
- The 10.2.0 upstream bump created its release tag and published to PyPI.
- The 10.2.0.post1 dependency refresh passed TestPyPI, created the
  `v10.2.0.post1` tag, and published ten wheels plus one source distribution
  to PyPI.

See the durable process docs for implementation details:

- [Dependency Health](../process/dependency-health.md)
- [GitHub Settings](../process/github-settings.md)
- [Release Artifacts](../process/release-artifacts.md)
- [Manual Release Process](../process/manual-release.md)
- [Rust oxipng updates](../process/upstream-bumps.md)

## What's Left To Do

No release or dependency work remains from the 10.2.1.post1 refresh. Release
preparation commit `d7c0f86` passed hosted `ci`, `api-matrix`, and `wheels` checks.

The GitHub settings audit does not read the active repository ruleset. It
reports missing protection and required checks even though the ruleset enforces
them. See [GitHub Settings](../process/github-settings.md) for the separate
ruleset check and the disabled Actions pull-request permission.

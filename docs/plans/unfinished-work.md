# Unfinished Work

This file tracks active work that is not covered by durable process docs.

Last checked: 2026-05-27.

## Verified Baseline

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
- PyPI does not yet have the `oxipng-pybind` project.

See the durable process docs for implementation details:

- [Dependency Health](../process/dependency-health.md)
- [GitHub Settings](../process/github-settings.md)
- [Release Artifacts](../process/release-artifacts.md)
- [Rust oxipng updates](../process/upstream-bumps.md)

## Remaining Work

### Publish the first PyPI release

Confirm that the real PyPI Trusted Publisher exists for:

- project: `oxipng-pybind`
- owner: `pdomain`
- repository: `oxipng-pybind`
- workflow: `wheels.yml`
- environment: `pypi`

Then publish `v10.1.1` through the tag-driven release flow in
[Release Artifacts](../process/release-artifacts.md).

After publishing, smoke-test the PyPI wheel in a clean environment.

### Prove automated upstream release tags

Upstream `oxipng` is still at `10.1.1`, which matches this repo.

When upstream publishes a newer release on GitHub and crates.io, run the hosted
upstream bump workflow. Confirm that the bump PR merges only after required
checks pass.

After the bump lands on `main`, confirm that
`.github/workflows/release-tag.yml` creates the matching release tag and that
`.github/workflows/wheels.yml` publishes it through `environment: pypi`.

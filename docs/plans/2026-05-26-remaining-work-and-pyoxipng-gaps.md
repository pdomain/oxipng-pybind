# Remaining Work and pyoxipng Gaps

This roadmap records the active project state after the hosted CI, wheel, and
dependency-health automation were proved on GitHub Actions. Completed
implementation plans live in `docs/archive/`.

`pyoxipng` comparison notes use the PyPI page for `pyoxipng` 9.1.1, released
2025-08-21: [pyoxipng on PyPI](https://pypi.org/project/pyoxipng/).

## Current Status

The package shape is in place:

- Distribution name: `oxipng-pybind`.
- Import package: `oxipng`.
- Native module: `_oxipng`.
- Package version and Rust `oxipng` dependency: upstream `oxipng` 10.1.1.
- API surface manifest: `docs/api-surface/oxipng-10.1.1.toml`.

The supported API is in place:

- `optimize`, `optimize_from_memory`, `analyze`, `OptimizationResult`,
  `PngError`, option enums, raw-image enums, and `RawImage` are exported.
- Type stubs, `py.typed`, and runtime docstrings exist for the supported API.
- File optimization supports in-place writes, explicit output paths,
  path-like inputs, `backup`, `preserve_attrs`, level checks, option parsing,
  and predictable Python exceptions.
- Memory optimization supports `bytes`, `bytearray`, and `memoryview`.
- `RawImage` supports packed pixel data, indexed palettes, transparency checks,
  ancillary chunks, ICC profiles, and `create_optimized_png`.
- Supported option values accept stable strings and Python enum `.value`
  strings. Rust code does not depend on Python enum object identity.

Tests and docs are in place:

- Public API tests cover imports, signatures, aliases, file optimization,
  memory optimization, raw image creation, validation errors, corrupt PNG
  failures, `preserve_attrs`, ICC output, and `.value` error propagation.
- Scanner tests cover Rust surface parsing, comparison reports, generated
  docs, and stable scan output.
- Documentation covers usage, architecture, API compatibility, option surface,
  release artifacts, upstream bumps, dependency health, local development, and
  lint deviations.
- The pyoxipng migration guide is at `docs/usage/pyoxipng-migration.md`.

## Automation Status

Hosted automation is active and has been proved:

- `ci.yml` runs source CI on pushes and PRs to `main`, and supports manual
  dispatch.
- `api-matrix.yml` runs public API tests on Python 3.11, 3.12, 3.13, and 3.14.
- `wheels.yml` builds and smoke-tests artifact-only ABI3 wheels for Linux
  x86_64, Linux aarch64, macOS x86_64, macOS arm64, and Windows x86_64.
- `dependency-health.yml` refreshes lockfiles, runs audits and CI, opens a
  dependency refresh PR when lockfiles change, and enables merge-commit
  auto-merge after required checks pass.
- `upstream-bump.yml` prepares upstream `oxipng` bump PRs, scans upstream API
  surface, updates triage issues, waits for wheels, and enables merge-commit
  auto-merge.
- `retry-failed-checks.yml` waits 10 minutes and reruns failed jobs once for
  failed `ci`, `api-matrix`, or `wheels` runs.

Repository setup is in place:

- Required checks are configured through the GitHub branch ruleset.
- Auto-merge is enabled.
- External fork PR workflows require approval before running.
- `DEPENDENCY_REFRESH_TOKEN` and `UPSTREAM_BUMP_TOKEN` are configured.
- Write-scoped `peter-evans/create-pull-request` usage is pinned to a reviewed
  full commit SHA and checkout credentials are not persisted in publish jobs.

## Active Next Work

1. Dependency refresh release classification.
   Add automation that labels dependency refresh PRs as `release-needed` or
   `no-release-needed`. Runtime Cargo graph changes and Python
   `[project.dependencies]` changes should require release attention. Tooling
   lockfile-only changes should auto-merge as `no-release-needed`.

2. PyPI release pipeline.
   Decide whether the first public release is wheel-only. If yes, add Trusted
   Publishing, a release aggregation job, final artifact verification, and a
   first-release checklist.

3. Generated third-party notices.
   Replace the hand-maintained `THIRD_PARTY_NOTICES.md` dependency list with
   generated Rust notices from `Cargo.lock` and generated Python notices from
   `uv.lock` when Python runtime dependencies are distributed.

4. Upstream bump proof.
   Run the first real `upstream-bump.yml` after upstream `oxipng` releases a
   version newer than 10.1.1. Verify release discovery, manifest copying,
   scanner output, docs updates, issue upsert, wheel waiting, and auto-merge.

5. Migration guide example tests.
   Add tests for examples in `docs/usage/pyoxipng-migration.md`, adapted only
   where behavior intentionally differs from `pyoxipng`.

## Remaining pyoxipng Gaps

This project is not a full drop-in replacement for `pyoxipng`.

- Python version policy differs. `pyoxipng` 9.1.1 advertises Python 3.8+; this
  project requires Python 3.11+.
- Distribution artifacts differ. `pyoxipng` publishes PyPI wheels and an
  sdist. This project currently builds artifact-only wheels and does not
  publish to PyPI.
- Wheel strategy differs. `pyoxipng` publishes CPython-version-specific
  wheels. This project targets ABI3 `cp311-abi3` wheels for Python 3.11+.
- Platform coverage differs. `pyoxipng` publishes extra targets such as
  musllinux and 32-bit Windows. This project currently targets manylinux
  x86_64/aarch64, macOS x86_64/arm64, and Windows x86_64.
- stdin and stdout stream handling is caller-owned. Use
  `optimize_from_memory` after reading bytes.
- `backup` and `preserve_attrs` are wrapper-specific controls, not pyoxipng
  parity targets.

## Optional Future Work

- Add Windows ARM64 wheels if there is user demand.
- Add musllinux x86_64/aarch64 wheels if Alpine users need native wheels.
- Decide whether to publish an sdist. Current docs defer sdist support because
  source installs require Rust and a compatible build environment.
- Document and test exact default interlace behavior more prominently if users
  need to reason about default interlace preservation.
- Test sliced or non-contiguous `memoryview` inputs only if those buffers
  become a product requirement.

## Recommended Next Order

1. Implement dependency refresh release classification.
2. Re-run `dependency-health.yml` and confirm `no-release-needed` auto-merge.
3. Choose PyPI release policy: wheel-only first release or wheel plus sdist.
4. If PyPI is approved, implement Trusted Publishing and release aggregation.
5. Implement generated third-party notices before publishing public artifacts.
6. Add migration guide example tests if pyoxipng migration confidence becomes
   the next priority.

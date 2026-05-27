# Unfinished Work

This is the only current planning doc. Older plans, specs, Superpowers plans,
and the 2026-05-26 security review report were removed from the current tree.
Use Git history to inspect them.

## Current State

The package shape is in place:

- Distribution name: `oxipng-pybind`.
- Import package: `oxipng`.
- Native module: `_oxipng`.
- Package version and Rust `oxipng` dependency follow upstream `oxipng` 10.1.1.
- The API surface manifest is
  [oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

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
- Third-party notices are generated from locked Cargo metadata and checked for
  drift in CI.
- Migration guide examples have focused tests.

Hosted automation is active:

- `ci.yml` runs source CI on pushes and pull requests to `main`.
- `api-matrix.yml` runs public API tests on Python 3.11, 3.12, 3.13, and 3.14.
- `wheels.yml` builds and smoke-tests ABI3 wheels for Linux x86_64,
  Linux aarch64, macOS x86_64, macOS arm64, and Windows x86_64.
- `dependency-health.yml` refreshes lockfiles, runs audits and CI, and opens
  a dependency refresh pull request when lockfiles change. It regenerates
  third-party notices and includes them in the pull request when needed.
- `upstream-bump.yml` prepares upstream `oxipng` bump pull requests. It also
  regenerates third-party notices after changing the Rust dependency graph.
- `retry-failed-checks.yml` waits 10 minutes and reruns failed CI, API matrix,
  or wheel jobs once.

## Next Work

1. **Validate dependency refresh automation on hosted CI.**
   After this branch merges, run `dependency-health.yml` on `main`. Confirm a
   tooling-only lockfile change gets `no-release-needed`, notice drift is
   handled automatically, and the pull request auto-merges after required
   checks pass.

2. **Configure PyPI Trusted Publishing.**
   Configure a pending trusted publisher for project `oxipng-pybind`, owner
   `pdomain`, repository `oxipng-pybind`, workflow `wheels.yml`, and
   environment `pypi`. Do this before creating the first release tag.

3. **Prove the upstream bump workflow.**
   Run the first real `upstream-bump.yml` after upstream `oxipng` releases a
   version newer than 10.1.1. Verify release discovery, manifest copying,
   scanner output, third-party notice generation, docs updates, issue upsert,
   wheel waiting, and auto-merge.

## Known Compatibility Differences

This project is a drop-in replacement for supported `pyoxipng` workflows, but
it is not a full clone of every old package behavior.

- Python support differs. `pyoxipng` 9.1.1 advertises Python 3.8+. This project
  requires Python 3.11+.
- Wheel strategy differs. `pyoxipng` publishes CPython-version-specific wheels.
  This project targets ABI3 `cp311-abi3` wheels for Python 3.11+.
- Platform coverage differs. This project targets manylinux x86_64/aarch64,
  macOS x86_64/arm64, and Windows x86_64.
- stdin and stdout stream handling is caller-owned. Use
  `optimize_from_memory` after reading bytes.
- `backup` and `preserve_attrs` are wrapper-specific file controls, not
  pyoxipng parity targets.

## Optional Future Work

- Add Windows ARM64 wheels if there is user demand.
- Add musllinux x86_64/aarch64 wheels if Alpine users need native wheels.
- Decide whether to publish an sdist. Source installs require Rust and a
  compatible build environment.
- Document and test exact default interlace behavior more prominently if users
  need to reason about default interlace preservation.
- Test sliced or non-contiguous `memoryview` inputs only if those buffers become
  a product requirement.

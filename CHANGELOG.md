---
kind: reference
status: active
last_verified: 2026-10-25
---
# Changelog

## Release Notes

## 10.2.1.post1 - Refresh dependencies and development tooling

- Updated Rust dependencies, including PyO3 from 0.29.2 to 0.29.3,
  `libdeflate-sys` and `libdeflater` from 1.26.0 to 1.26.1, and `zopfli`
  from 0.8.3 to 0.8.4. Refreshed third-party notices.
- Refreshed Python development dependencies. Updated `virtualenv` to
  21.14.13 and removed the vulnerable Python 3.10 `filelock` resolution.
  Kept the `click` and `sh` security overrides because they are still needed.
- Pre-commit tooling now runs in a separate, locked Python 3.13 environment.
  The project environment keeps its selected Python version, including 3.10.
- Fixed Pillow 13 type checking for Python 3.10 in test helpers and wheel
  smoke checks.
- Updated the Rust toolchain to 1.99.1, pre-commit hooks, and reviewed
  GitHub Action pins.
- The public Python API is unchanged. The package still wraps upstream
  `oxipng` 10.2.1. Python runtime dependencies remain empty.

## 10.2.1 - Bump Version

- Rebuilt `oxipng-pybind` to track upstream `oxipng` 10.2.1.

## 10.2.0.post1 - Refresh runtime dependencies and release tooling

- Updated `crc32fast` from 1.5.0 to 1.5.1, `libdeflate-sys` and `libdeflater`
  from 1.25.2 to 1.26.0, and `log` from 0.4.33 to 0.4.34.
- Refreshed Python development dependencies, including Maturin 1.15.0. Kept
  the `click` and `sh` security overrides because `gitlint-core` still needs
  them.
- Reviewed and pinned `taiki-e/install-action` v2.86.7 for CI and dependency
  automation.
- The public API and optimization behavior did not change. The package still
  wraps upstream `oxipng` 10.2.0.

## 10.2.0 - Upstream and dependency refresh

- The binding now uses upstream `oxipng` 10.2.0, up from 10.1.1. The new
  `PngError::ChunkPreventsChanges` variant still maps to the flat Python
  `PngError`, so the public binding surface did not change.
- Rust runtime and Python development dependencies were refreshed. Upstream
  10.2.0 removed `bitvec`, `funty`, `radium`, `tap`, and `wyz` from the runtime
  dependency set.
- The Rust toolchain now uses 1.98.0, up from 1.97.1. Ruff now uses 0.16.4,
  up from 0.16.2. Reviewed new `setup-uv` v10.0.1 and `install-action` v2.86.4
  pins.

## 10.1.1.post4 - Refresh runtime dependencies and release tooling

- Updated PyO3 from 0.29.0 to 0.29.2. Refreshed bundled runtime Rust crates.
- Required `sh>=2.2.4` to clear PYSEC-2026-3540 and GHSA-q38v-wp89-2w55 from
  the development lockfile.
- Updated the Rust toolchain and pre-commit hooks. Reviewed GitHub Action pins
  used to build and publish releases.
- The public API and optimization behavior did not change. The package still
  wraps upstream `oxipng` 10.1.1.

## 10.1.1.post3 - Security-hygiene rebuild on PyO3 0.29

- Rebuilt the extension on PyO3 0.29.0. This cleared RUSTSEC-2026-0176 and
  RUSTSEC-2026-0177.
- Refreshed bundled runtime Rust crates (bitvec, log, rustc-hash).
- The public API and optimization behavior did not change. The package still
  wraps upstream `oxipng` 10.1.1.

## 10.1.1.post2 - Work around Pylint/Astroid facade analysis recursion

- Reworked the Python compatibility facade for consumers running Pylint 4.0.x /
  Astroid 4.0.x. They can import `oxipng` without Astroid recursion warnings or
  crashes.
- The change works around a Pylint/Astroid static-analysis bug. It does not fix
  a runtime correctness issue in `oxipng-pybind`.
- Kept the public typing surface intact. Added a Pylint consumer regression
  test that covers the public facade.

## 10.1.1.post1 - Add Python 3.10 support

- The package and wheel policy now also target Python 3.10:
  - `requires-python >= 3.10`
  - Wheel tag validation and release tooling now expect `cp310-abi3` and `cp311-abi3` lanes.
  - PyO3 ABI features split into `abi3-py310` and `abi3-py311` build lanes.
  - Reworked memoryview ingestion to use the native `PyBuffer` path when PyO3 exposes it. For Python 3.10 ABI3 builds, it falls back to `memoryview.tobytes()`.
- Fixed type-check compatibility for Python 3.10-based tooling:
  - Added `scripts/_toml_compat.py` as a TOML parser shim. It uses `tomllib` when available and `tomlkit` fallback.
  - Switched release/wheel/metadata scripts to use the shim for Python 3.10.

## 10.1.1 - Initial release

- Initial release of `oxipng-pybind` for Python 3.11 to 3.14.

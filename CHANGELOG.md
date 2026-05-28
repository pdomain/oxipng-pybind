# Changelog

## Release Notes

## 10.1.1.post1 - Add python 3.10 support

- Also allow the package and wheel policy to target Python 3.10:
  - `requires-python >= 3.10`
  - wheel tag validation and release tooling now expect `cp310-abi3` and `cp311-abi3` lanes
  - PyO3 ABI features split into `abi3-py310` and `abi3-py311` build lanes
  - Reworked memoryview ingestion to use the native `PyBuffer` path when PyO3 exposes it, while falling back to `memoryview.tobytes()` for Python 3.10 ABI3 builds.
- Fixed type-check compatibility for Python 3.10-based tooling:
  - Added `scripts/_toml_compat.py` as a TOML parser shim using `tomllib` when available and `tomlkit` fallback.
  - Switched release/wheel/metadata scripts to use the shim for Python 3.10

## 10.1.1 - Initial release

- Initial release of `oxipng-pybind` for Python 3.11 to 3.14

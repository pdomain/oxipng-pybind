# oxipng-pybind

`oxipng-pybind` is a Python wrapper for the Rust `oxipng` PNG optimizer.
It optimizes PNG files, PNG bytes, and raw pixel data through the `oxipng`
Python module.

## Install

The distribution name is `oxipng-pybind`. The import module is `oxipng`.

Release artifacts require Python 3.11 or newer. PyPI publishing is not enabled
yet. Install from a built wheel artifact, or build a local wheel:

```bash
make wheel
```

## Basic API

The main entry points are `optimize`, `optimize_from_memory`, and `RawImage`.

- `optimize` reads and writes PNG files.
  See [File Optimization](docs/usage/file-optimization.md).
- `optimize_from_memory` reads PNG data from memory and returns optimized bytes.
  See [Memory Optimization](docs/usage/memory-optimization.md).
- `RawImage` builds optimized PNG data from packed pixel bytes.
  See [Raw Image Usage](docs/usage/raw-image.md).

PNG decode and optimization failures raise `PngError`. Caller errors raise
standard Python exceptions such as `TypeError` or `ValueError`.

## pyoxipng Compatibility

Some `pyoxipng` compatibility paths exist for migration tests. These paths emit
`DeprecationWarning`. New code should use the stable `oxipng-pybind` API.

Compatibility-only paths include explicit chunk keep/strip lists and upstream
alpha options. They emit `DeprecationWarning` and are not the stable API.

stdin/stdout optimization is still unsupported.

## Development

Set up the pinned Rust toolchain, Python dependencies, editable extension, and
pre-commit hooks:

```bash
make setup
```

Common checks:

```bash
make test
make lint
make typecheck
make ci
```

## Upstream Tracking

Project versions track upstream `oxipng` versions when practical. A scheduled
workflow checks for new upstream releases and opens a pull request when an
update is available.

## License

This wrapper is released under the Unlicense. See `LICENSE`.

Upstream `oxipng` is MIT licensed. See `THIRD_PARTY_NOTICES.md`.

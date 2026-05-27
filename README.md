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

The main entry points are `optimize`, `optimize_from_memory`, `RawImage`, and
`analyze`.

- `optimize` reads and writes PNG files.
  See [File Optimization](docs/usage/file-optimization.md).
- `optimize_from_memory` reads PNG data from memory and returns optimized bytes.
  See [Memory Optimization](docs/usage/memory-optimization.md).
- `RawImage` builds optimized PNG data from packed pixel bytes.
  See [Raw Image Usage](docs/usage/raw-image.md).
- `analyze` reports original and optimized sizes without writing output.

PNG decode and optimization failures raise `PngError`. Caller errors and file
I/O failures raise standard Python exceptions such as `TypeError`,
`ValueError`, `FileNotFoundError`, or `OSError`.

## Untrusted Input

PNG optimization can spend CPU and memory while decoding and recompressing
images. When processing attacker-controlled files or bytes, pass explicit
resource limits:

```python
from oxipng import optimize_from_memory

optimized = optimize_from_memory(data, timeout=2.0, max_decompressed_size=50_000_000)
```

The default options preserve upstream `oxipng` behavior and do not impose a
decompression cap. Use conservative compression settings for request-time
workloads, and enable `fix_errors` or `force` only when the caller accepts the
additional processing.

## pyoxipng Compatibility

Most practical upstream options are stable API. Remaining `pyoxipng`
compatibility paths emit `DeprecationWarning`. New code should use the stable
`oxipng-pybind` API. See [Move from pyoxipng](docs/usage/pyoxipng-migration.md).

The API maps supported Rust options to Python types. It does not expose Rust
stdin or stdout stream arguments.

stdin and stdout optimization are not part of this API. Callers own reading
from stdin and writing to stdout.

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

Python tests import the compiled `_oxipng` extension. Use `make test-py` or
rebuild with `maturin develop` before running focused pytest commands. See
`docs/process/local-development.md`.

## Upstream Tracking

Project versions track upstream `oxipng` versions when practical. A scheduled
workflow checks for new upstream releases and opens a pull request when an
update is available.

## License

This wrapper is released under the Unlicense. See `LICENSE`.

Upstream `oxipng` is MIT licensed. See `THIRD_PARTY_NOTICES.md`.

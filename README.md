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

```python
from pathlib import Path

from oxipng import BitDepth, ColorType, RawImage
from oxipng import optimize, optimize_from_memory

path = Path("cover.png")
optimize(path, level=6)

png_bytes = path.read_bytes()
optimized_bytes = optimize_from_memory(png_bytes, strip="safe")

raw = RawImage(
    1,
    1,
    ColorType.rgba,
    BitDepth.eight,
    bytes([255, 0, 0, 255]),
)
raw_png = raw.create_optimized_png()
```

`optimize` reads a PNG file. If `output` is omitted, it writes the optimized
PNG back to the input path.

```python
optimize("cover.png", output="cover.optimized.png", level=4)
```

`optimize_from_memory` reads PNG data from `bytes`, `bytearray`, or
`memoryview`. It returns optimized PNG data as `bytes`.

```python
optimized_bytes = optimize_from_memory(png_bytes, level=4)
```

`RawImage` builds an optimized PNG from packed pixel bytes.

```python
raw_png = raw.create_optimized_png(level=3)
```

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

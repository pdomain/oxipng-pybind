# oxipng-pybind

`oxipng-pybind` is a focused Python wrapper around the Rust
[`oxipng`](https://github.com/oxipng/oxipng) library.

It supports file-based and in-memory PNG optimization while tracking current
upstream `oxipng` releases.

## Install

Release artifacts use PyO3 ABI3 wheels for Python 3.11 and newer. Until PyPI
publishing is enabled, install from a built wheel artifact or build locally with
`make wheel`.

## Supported API

The distribution is named `oxipng-pybind`, but the import module is `oxipng`.

```python
from oxipng import Deflater, FilterStrategy, Interlacing, StripChunks
from oxipng import BitDepth, ColorType, RawImage
from oxipng import optimize, optimize_from_memory

optimize(path, level=6)
data = optimize_from_memory(png_bytes, strip=StripChunks.safe)
raw_png = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))
optimized = raw_png.create_optimized_png()
```

Supported objects:

- `oxipng.optimize(input, output=None, *, level=2, interlace=None, strip=None,
  deflate=None, filter=None, fix_errors=False, force=False, backup=False,
  preserve_attrs=False)`
- `oxipng.optimize_from_memory(data, *, level=2, interlace=None, strip=None,
  deflate=None, filter=None, fix_errors=False, force=False)`
- `oxipng.PngError`
- `oxipng.Interlacing`
- `oxipng.StripChunks`
- `oxipng.Deflater`
- `oxipng.FilterStrategy`
- `oxipng.ColorType`
- `oxipng.BitDepth`
- `oxipng.RawImage`

`input` and `output` may be strings, bytes paths, or `os.PathLike` values.
When `output` is omitted, the input file is optimized in place.

`level` must be an integer from `0` through `6`. Enum-like options accept the
documented enum members or their string aliases.

## Unsupported pyoxipng APIs

This package is not a full `pyoxipng` replacement. These APIs are intentionally
not provided:

- `RowFilter`
- arbitrary chunk keep/strip lists
- stdin/stdout optimization
- lossy transparent-pixel optimization knobs

Unsupported keyword arguments raise `TypeError`.

## Development

`make setup` installs the pinned Rust toolchain through `rustup` when needed,
installs `cargo-deny`, syncs Python development dependencies, builds the editable
extension, and installs pre-commit hooks.

```bash
make setup
make test
make lint
make typecheck
make ci
```

## Upstream Tracking

Package versions mirror upstream `oxipng` versions when practical. The
scheduled upstream bump workflow opens a pull request when a new upstream
release is available. Auto-merge is enabled only after the repository's
required checks pass.

## License

This wrapper is MIT licensed. See `LICENSE`. Upstream `oxipng` is MIT
licensed; see `THIRD_PARTY_NOTICES.md`.

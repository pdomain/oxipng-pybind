# oxipng-pybind

`oxipng-pybind` is a focused Python wrapper around the Rust
[`oxipng`](https://github.com/oxipng/oxipng) library.

It supports file-based PNG optimization while tracking current upstream
`oxipng` releases.

## Install

```bash
pip install oxipng-pybind
```

## Supported API

The distribution is named `oxipng-pybind`, but the import module is `oxipng`.

```python
from oxipng import optimize

optimize(path, level=6)
```

Supported objects:

- `oxipng.optimize(input, output=None, *, level=2)`
- `oxipng.PngError`

`input` and `output` may be strings, bytes paths, or `os.PathLike` values.
When `output` is omitted, the input file is optimized in place.

`level` must be an integer from `0` through `6`.

## Unsupported pyoxipng APIs

This package is not a full `pyoxipng` replacement. These APIs are intentionally
not provided:

- `optimize_from_memory`
- `RawImage`
- `ColorType`
- `RowFilter`
- `Interlacing`
- `StripChunks`
- `Deflaters`

Unsupported keyword arguments to `optimize()` raise `TypeError`.

## Development

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

This wrapper is MIT licensed. Upstream `oxipng` is MIT licensed. See
`THIRD_PARTY_NOTICES.md`.

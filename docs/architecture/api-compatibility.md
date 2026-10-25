---
kind: architecture
status: built
last_verified: 2026-10-25
---
# API Compatibility

`oxipng-pybind` exposes a small stable API over Rust `oxipng`. Stable names are
safe for normal callers. They must not emit compatibility warnings.

For option values, see [Options Surface](options-surface.md). For old pyoxipng
code, see [Move from pyoxipng](../usage/pyoxipng-migration.md).

## Stable API Names

These top-level names are the public contract:

- `optimize`
- `optimize_from_memory`
- `analyze`
- `OptimizationResult`
- `PngError`
- `Interlacing`
- `StripChunks`
- `Deflater`
- `Deflaters`
- `FilterStrategy`
- `ColorType`
- `BitDepth`
- `RawImage`

The stable method and factory surface includes:

- `RawImage.add_png_chunk`
- `RawImage.add_icc_profile`
- `RawImage.create_optimized_png`
- `StripChunks.strip`
- `StripChunks.keep`
- `Deflaters.libdeflater`
- `Deflaters.zopfli`
- `FilterStrategy.predefined`

## pyoxipng Compatibility Shims

This package keeps selected old `pyoxipng` shapes as migration paths.
`pyoxipng` exposed these older Python shapes, and some do not match Rust
`oxipng`'s option contracts.

Common warning-emitting paths include:

- `ColorType` descriptor calls
- `RawImage(data, width, height, ...)`
- `StripChunks.none()`, `StripChunks.safe()`, and `StripChunks.all()`
- `Interlacing.Off`
- `Interlacing.Adam7`
- `RowFilter`

Compatibility paths emit `DeprecationWarning`. They are not stable API. Each
warning says the path will be removed in a future release.

Stable enum members and factories do not warn. For example,
`FilterStrategy.none`, `ColorType.rgba`, `StripChunks.strip`, and
`Deflaters.libdeflater` are stable.

`RowFilter` exists only for old pyoxipng-style code. Use `FilterStrategy` or
`FilterStrategy.predefined(...)` in new code.

## Unsupported Paths

These paths are not supported:

- stdin and stdout stream handling inside the library

Unsupported paths may fail, warn, or stay absent.

## The Machine-Readable Surface Record

The machine-readable Rust surface record is
[oxipng-10.2.1.toml](../api-surface/oxipng-10.2.1.toml).

Upstream 10.2.1 keeps the same tracked surface as 10.2.0. Rust PNG decode and
optimization errors map to one Python `PngError` exception. Read and write
failures map to normal Python file exceptions. See
[Error Mapping](overview.md#error-mapping).

### oxipng 10.2.0

- `PngError::ChunkPreventsChanges`

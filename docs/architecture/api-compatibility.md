# API Compatibility

`oxipng-pybind` exposes a small stable API over Rust `oxipng`. A stable API is
safe for normal callers to use. Stable API calls must not emit compatibility
warnings.

## Stable API

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

## pyoxipng Compatibility

`pyoxipng` exposed older Python shapes. Some of those shapes do not match Rust
`oxipng` option contracts. This package keeps selected old shapes as migration
paths. They emit `DeprecationWarning` and are not stable API.

Common warning-emitting paths include:

- `ColorType` descriptor calls
- `RawImage(data, width, height, ...)`
- `StripChunks.none()`, `StripChunks.safe()`, and `StripChunks.all()`
- `Interlacing.Off`
- `Interlacing.Adam7`
- `RowFilter`

Every compatibility warning says the path will be removed in a future release.
Stable enum members do not warn.

Examples:

- `Interlacing.off`
- `FilterStrategy.none`
- `ColorType.rgba`
- `BitDepth.eight`
- `FilterStrategy.predefined(...)`
- `StripChunks.strip`
- `StripChunks.keep`
- `Deflaters.libdeflater`
- `Deflaters.zopfli`

`RowFilter` exists only for old pyoxipng-style code. Do not use it in new code.
Use `FilterStrategy` or `FilterStrategy.predefined(...)` instead.

## Unsupported Paths

These paths are not supported:

- stdin and stdout stream handling inside the library

Unsupported paths may fail, warn, or stay absent.

## Source Of Truth

The machine-readable Rust surface record is
[oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Rust Surface

No generated Rust surface additions have been recorded for 10.1.1.

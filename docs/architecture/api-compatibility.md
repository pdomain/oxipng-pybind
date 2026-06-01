# API Compatibility

`oxipng-pybind` exposes a small stable API over Rust `oxipng`. Stable names are
safe for normal callers. They must not emit compatibility warnings.

For option values, see [Options Surface](options-surface.md). For old pyoxipng
code, see [Move from pyoxipng](../usage/pyoxipng-migration.md).

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

`pyoxipng` exposed older Python shapes. Some do not match Rust `oxipng` option
contracts. This package keeps selected old shapes as migration paths.

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

## Source Of Truth

The machine-readable Rust surface record is
[oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

No generated Rust surface additions have been recorded for 10.1.1.

### oxipng 10.1.1

- `InFile::Path`
- `InFile::StdIn`
- `OutFile::None`
- `OutFile::Path`
- `OutFile::StdOut`
- `PngError::APNGOutOfOrder`
- `PngError::C2PAMetadataPreventsChanges`
- `PngError::CRCMismatch`
- `PngError::ChunkMissing`
- `PngError::DeflatedDataTooLong`
- `PngError::IncorrectDataLength`
- `PngError::InflatedDataTooLong`
- `PngError::InvalidData`
- `PngError::InvalidDepthForType`
- `PngError::NotPNG`
- `PngError::Other`
- `PngError::ReadFailed`
- `PngError::TruncatedData`
- `PngError::WriteFailed`

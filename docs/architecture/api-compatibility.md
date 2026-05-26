# API Compatibility

`oxipng-pybind` exposes a small stable API over upstream `oxipng`. A stable API
is an API that callers can use without compatibility warnings.

Stable API calls must remain warning-free.

## Stable API

The stable no-warning Python surface is:

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

These names are the public contract for normal use.

## pyoxipng Compatibility

`pyoxipng` exposed a broader Python API. Most practical upstream surfaces are
now stable API in `oxipng-pybind`.

Compatibility paths emit `DeprecationWarning`. They are unsupported migration
paths. A migration path is a short-term bridge for old callers, not a stable
API.

Warning-emitting compatibility paths are:

- `ColorType` descriptor calls;
- `RawImage(data, width, height, color_type=...)`;
- pyoxipng enum aliases such as `Interlacing.Off`, `Interlacing.Adam7`, and
  `RowFilter`.

Every compatibility warning states that the path will be removed in a future
release.

Stable enum members such as `Interlacing.off`, `FilterStrategy.none`,
`ColorType.rgba`, and `BitDepth.eight` do not warn. `StripChunks.strip`,
`StripChunks.keep`, `Deflaters.libdeflater`, and `Deflaters.zopfli` also do not
warn.

`RowFilter` is exported only for old pyoxipng-style code. Do not use it in new
code. Use `FilterStrategy` or `FilterStrategy.predefined(...)` instead.

## Unsupported Paths

These paths are not supported:

- pyoxipng-specific raw buffer helpers beyond `RawImage`
- stdin and stdout stream handling

Unsupported paths may fail, warn, or stay absent.

## Source Of Truth

The machine-readable upstream-surface source of truth for upstream `oxipng`
10.1.1 is [oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Upstream Surface

No generated upstream-surface additions have been recorded for 10.1.1.

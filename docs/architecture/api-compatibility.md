# API Compatibility

`oxipng-pybind` exposes a small stable API over upstream `oxipng`. A stable API
is an API that callers can use without compatibility warnings.

Stable API calls must remain warning-free.

## Stable API

The supported Python surface is:

- `optimize`
- `optimize_from_memory`
- `PngError`
- `Interlacing`
- `StripChunks`
- `Deflater`
- `FilterStrategy`
- `ColorType`
- `BitDepth`
- `RawImage`

These names are the public contract for normal use. They do not try to mirror
every upstream CLI flag, Rust type, or `Options` field.

## pyoxipng Compatibility

`pyoxipng` exposed a broader Python API. `oxipng-pybind` keeps practical
compatibility paths for path-based optimization, enum-like options, explicit
chunk keep/strip lists, raw-image construction, and upstream option keywords.

Compatibility paths emit `DeprecationWarning`. They are unsupported migration
paths. A migration path is a short-term bridge for old callers, not a stable API.

## Unsupported Paths

These paths are not supported:

- pyoxipng-specific raw buffer helpers beyond `RawImage`
- stdin/stdout behavior
- automatic stable exposure of every upstream `Options` field

Unsupported paths may fail, warn, or stay absent.

## Source Of Truth

The machine-readable compatibility source of truth for upstream `oxipng`
10.1.1 is [oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Upstream Surface

No generated upstream-surface additions have been recorded for 10.1.1.

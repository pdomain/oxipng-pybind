# API Compatibility

`oxipng-pybind` exposes a small Python API over upstream `oxipng`. It does not
try to mirror every CLI flag or Rust type.

Upstream `oxipng` provides Rust APIs for file optimization, memory optimization,
raw image construction, stdin/stdout, and detailed `Options` fields.

`pyoxipng` exposes a broader Python compatibility surface including raw image
helpers. `oxipng-pybind` only targets practical compatibility for path-based
optimization and common enum-like options.

Supported Python surface:

- `optimize`
- `optimize_from_memory`
- `PngError`
- `Interlacing`
- `StripChunks`
- `Deflater`
- `FilterStrategy`

Unsupported compatibility surface:

- `RawImage`
- raw pixel buffer APIs
- arbitrary chunk keep/strip lists
- stdin/stdout behavior
- automatic exposure of every upstream `Options` field

The machine-readable compatibility source of truth for upstream `oxipng`
10.1.1 is [oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Upstream Surface

No generated upstream-surface additions have been recorded for 10.1.1.

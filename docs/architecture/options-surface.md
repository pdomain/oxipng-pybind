# Options Surface

Options start from `oxipng::Options::from_preset(level)` and then apply explicit
Python overrides.

| Python option | Supported values |
| --- | --- |
| `level` | integers `0` through `6` |
| `interlace` | `None`, `Interlacing.keep`, `Interlacing.off`, `Interlacing.on`, `"keep"`, `"off"`, `"on"`, `"0"`, `"1"` |
| `strip` | `None`, `StripChunks.none`, `StripChunks.safe`, `StripChunks.all`, `"none"`, `"safe"`, `"all"` |
| `deflate` | `None`, `Deflater.libdeflater`, `Deflater.zopfli`, `"libdeflater"`, `"zopfli"` |
| `filter` | `None`, one filter value, or a non-empty sequence of filter values |
| `fix_errors` | `bool` |
| `force` | `bool` |
| `backup` | `bool`, file API only |
| `preserve_attrs` | `bool`, file API only |

`FilterStrategy` exposes `none`, `sub`, `up`, `average`, `paeth`, `minsum`,
`entropy`, `bigrams`, `bigent`, and `brute`. String aliases also include
numeric values `"0"` through `"9"` in that order.

Intentionally unexposed upstream `Options` fields:

- `optimize_alpha`
- `bit_depth_reduction`
- `color_type_reduction`
- `palette_reduction`
- `grayscale_reduction`
- `idat_recoding`
- `scale_16`
- `fast_evaluation`
- `timeout`
- `max_decompressed_size`

Intentionally unexposed upstream enum variants:

- `StripChunks::Strip`
- `StripChunks::Keep`
- `FilterStrategy::Predefined`

The machine-readable compatibility source of truth is
[oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Upstream Surface

No generated upstream-surface additions have been recorded for 10.1.1.

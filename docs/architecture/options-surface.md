# Options Surface

Python options map to upstream `oxipng::Options`.

Rust starts with `oxipng::Options::from_preset(level)`. Then it applies explicit
Python overrides. The Rust extension owns validation for native options. Python
wrappers own ergonomic names and path handling.

## Supported Options

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
| `optimize_alpha` | `bool` or `None` |
| `bit_depth_reduction` | `bool` or `None` |
| `color_type_reduction` | `bool` or `None` |
| `palette_reduction` | `bool` or `None` |
| `grayscale_reduction` | `bool` or `None` |
| `idat_recoding` | `bool` or `None` |
| `scale_16` | `bool` or `None` |
| `fast_evaluation` | `bool` or `None` |
| `timeout` | non-negative seconds or `None` |
| `max_decompressed_size` | non-negative integer bytes or `None` |

## Filter Values

`FilterStrategy` exposes `none`, `sub`, `up`, `average`, `paeth`, `minsum`,
`entropy`, `bigrams`, `bigent`, and `brute`. String aliases also include
numeric values `"0"` through `"9"` in that order.

`FilterStrategy.predefined(...)` exposes upstream `FilterStrategy::Predefined`.
It accepts a non-empty sequence of basic row filters.

## Stable Factories

These factories expose upstream option objects:

- `StripChunks.strip(names)`
- `StripChunks.keep(names)`
- `Deflaters.libdeflater(compression)`
- `Deflaters.zopfli(iterations)`

## Dry Run

`analyze(input, **options)` maps to upstream `OutFile::None`. It returns
`OptimizationResult` with `original_size` and `optimized_size`.

## Source Of Truth

The machine-readable compatibility source of truth is
[oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Upstream Surface

No generated upstream-surface additions have been recorded for 10.1.1.

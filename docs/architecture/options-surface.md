# Options Surface

Python options map to upstream `oxipng::Options`.

Rust starts with `oxipng::Options::from_preset(level)`. Then it applies explicit
Python overrides. The Rust extension owns validation and path conversion. The
Python facade owns ergonomic names.

## Supported Options

| Python option | Supported values |
| --- | --- |
| `level` | integers `0` through `6` |
| `interlace` | `None`, `Interlacing.keep`, `Interlacing.off`, `Interlacing.on`, `"keep"`, `"off"`, `"on"`, `"0"`, `"1"` |
| `strip` | `None`, `StripChunks.none`, `StripChunks.safe`, `StripChunks.all`, `StripChunks.strip(names)`, `StripChunks.keep(names)`, `"none"`, `"safe"`, `"all"` |
| `deflate` | `None`, `Deflater.libdeflater`, `Deflater.zopfli`, `Deflaters.libdeflater(compression)`, `Deflaters.zopfli(iterations)`, `"libdeflater"`, `"zopfli"` |
| `filter` | `None`, one scalar filter value, `FilterStrategy.predefined(filters)`, or a non-empty `list`, `tuple`, or `set` of scalar filter values |
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
It accepts a non-empty ordered iterable of basic row filters, including ordered
sequences and generators. Basic row filters are `none`, `sub`, `up`, `average`,
and `paeth`.

Predefined filter order is meaningful. `FilterStrategy.predefined(...)` rejects
`set` and `frozenset`; callers that want sorted set contents should pass
`sorted(values)` explicitly. A predefined-filter object is valid only as the
whole `filter=` value, not inside a scalar filter collection.

`RowFilter` values also parse as filters for old pyoxipng-style code. Accessing
`RowFilter` values emits `DeprecationWarning`.

## Stable Factories

These factories create Python option objects. Rust maps them to upstream
options:

- `StripChunks.strip(names)`
- `StripChunks.keep(names)`
- `Deflaters.libdeflater(compression)`
- `Deflaters.zopfli(iterations)`

`Deflaters.libdeflater(compression)` accepts `0` through `12`.
`Deflaters.zopfli(iterations)` accepts `1` through `255`.

## Dry Run

`analyze(input, **options)` maps to upstream `OutFile::None`. It returns
`OptimizationResult` with `original_size` and `optimized_size`.

`analyze` uses the same parser as memory mode. It rejects `backup` and
`preserve_attrs`.

## Source Of Truth

The machine-readable upstream-surface source of truth is
[oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).

## Unexposed Upstream Surface

No generated upstream-surface additions have been recorded for 10.1.1.

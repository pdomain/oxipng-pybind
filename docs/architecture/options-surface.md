# Options Surface

Most Python keyword options map to Rust
[`oxipng::Options`](https://docs.rs/oxipng/10.1.1/oxipng/struct.Options.html).
`backup` and `preserve_attrs` are Python-only file options.

## Option Parsing

Rust starts with `oxipng::Options::from_preset(level)`. Then it applies
explicit Python overrides.

The Rust extension owns validation and path conversion. The Python facade keeps
the public names ergonomic.

## Python Keyword Options

Use these options with `optimize`, `optimize_from_memory`, `analyze`, or
`RawImage.create_optimized_png`.

| Python option | Supported values |
| --- | --- |
| `level` | integers `0` through `6` |
| `interlace` | enum values or aliases: `keep`, `off`, `on`, `0`, `1` |
| `strip` | enum values, `StripChunks` factories, or aliases: `none`, `safe`, `all` |
| `deflate` | enum values, `Deflaters` factories, or aliases: `libdeflater`, `zopfli` |
| `filter` | `FilterStrategy` value or alias; non-empty list, tuple, or set |
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

`backup` and `preserve_attrs` are valid only for `optimize`. Memory mode,
`analyze`, and `RawImage.create_optimized_png` reject them.

## Filter Values

`FilterStrategy` exposes Rust `oxipng` filter strategies as Python enum values.
It also accepts documented aliases.

`FilterStrategy.predefined(...)` maps to Rust `FilterStrategy::Predefined`. It
accepts a non-empty sequence of basic row filters:

- `none`
- `sub`
- `up`
- `average`
- `paeth`

`RowFilter` values are accepted only for old pyoxipng code. See
[Move from pyoxipng](../usage/pyoxipng-migration.md#row-filters).

## Factory Values

Use these factories for explicit chunk or DEFLATE settings:

- `StripChunks.strip(names)`
- `StripChunks.keep(names)`
- `Deflaters.libdeflater(compression)`
- `Deflaters.zopfli(iterations)`

`Deflaters.libdeflater(compression)` accepts `0` through `12`.
`Deflaters.zopfli(iterations)` accepts `1` through `255`.

## Dry Run

[`analyze`](../../oxipng/__init__.pyi#L234) maps to Rust `OutFile::None`. It
uses the memory-mode option parser.

For return values and examples, see
[Analyze Without Writing](../usage/file-optimization.md#analyze-without-writing).

## Source Of Truth

The machine-readable Rust surface record is
[oxipng-10.1.1.toml](../api-surface/oxipng-10.1.1.toml).
It records mapped upstream items and intentional gaps for `oxipng` 10.1.1.

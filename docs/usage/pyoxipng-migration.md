# Move From pyoxipng

Use this guide when old code depends on the `pyoxipng` distribution or uses
old pyoxipng API shapes.

Compatibility behavior is checked against
[`pyoxipng` 9.1.1](https://github.com/nfrasser/pyoxipng/tree/v9.1.1),
commit `357ea12453f352685acaf1b7a9c4573866b5bbf6`.

`pyoxipng` exposed older Python shapes over Rust `oxipng`. Those shapes are
not this project's stable API contract. For supported names, see
[API Compatibility](../architecture/api-compatibility.md).

Compatibility paths emit `DeprecationWarning`, and a future release will
remove them.

Some names also existed in pyoxipng and are stable here, so they do not warn.
Examples include `StripChunks.strip`, `StripChunks.keep`,
`Deflaters.libdeflater`, and `Deflaters.zopfli`.

## Package And Import Names

`pyoxipng` was the package name on PyPI. Its import module was already
`oxipng`.

Keep imports as `oxipng`:

```python
from oxipng import optimize, optimize_from_memory
```

Change package metadata and install commands from `pyoxipng` to
`oxipng-pybind`.

## Row Filters

Use `FilterStrategy` in new code:

```python
from oxipng import FilterStrategy

filter = FilterStrategy.none
filters = FilterStrategy.predefined(["none", "sub", "up"])
```

Do not use `RowFilter` in new code. It exists only for old pyoxipng code and
warns when you access its members:

```python
from oxipng import RowFilter

filter = RowFilter.none  # emits DeprecationWarning
```

Migration rule:

| Old pyoxipng shape | Stable oxipng-pybind shape |
| --- | --- |
| `RowFilter.none` | `FilterStrategy.none` |
| `RowFilter.sub` | `FilterStrategy.sub` |
| `RowFilter.up` | `FilterStrategy.up` |
| `RowFilter.average` | `FilterStrategy.average` |
| `RowFilter.paeth` | `FilterStrategy.paeth` |
| `RowFilter.NoOp` | `FilterStrategy.none` |
| `RowFilter.Sub` | `FilterStrategy.sub` |
| `RowFilter.Up` | `FilterStrategy.up` |
| `RowFilter.Average` | `FilterStrategy.average` |
| `RowFilter.Paeth` | `FilterStrategy.paeth` |
| `RowFilter.MinSum` | `FilterStrategy.minsum` |
| `RowFilter.Entropy` | `FilterStrategy.entropy` |
| `RowFilter.Bigrams` | `FilterStrategy.bigrams` |
| `RowFilter.BigEnt` | `FilterStrategy.bigent` |
| `RowFilter.Brute` | `FilterStrategy.brute` |
| `[RowFilter.none, RowFilter.sub]` | `FilterStrategy.predefined(["none", "sub"])` |

`FilterStrategy.predefined(...)` preserves order. It accepts ordered iterables
and rejects mappings and scalar values. Pass `sorted(values)` if old code built
predefined filters from a set.

For full option values, see
[Options Surface](../architecture/options-surface.md#filter-values).

## Interlacing

Use lowercase names:

```python
from oxipng import Interlacing

interlace = Interlacing.off
interlace = Interlacing.on
```

Old pyoxipng aliases warn:

| Old pyoxipng shape | Stable oxipng-pybind shape |
| --- | --- |
| `Interlacing.Off` | `Interlacing.off` |
| `Interlacing.Adam7` | `Interlacing.on` |

## Raw Images

Use the stable `RawImage` order:

```python
from oxipng import BitDepth, ColorType, RawImage

data = bytes([255, 0, 0, 255])
raw = RawImage(
    width=1,
    height=1,
    color_type=ColorType.rgba,
    bit_depth=BitDepth.eight,
    data=data,
)
```

The old pyoxipng order still works only as a migration path:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
raw = RawImage(data, 1, 1, color_type=ColorType.rgba())
```

Do not mix the two shapes. The old-order path emits `DeprecationWarning`, and
so does the callable `ColorType` value.

This call is rejected:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
raw = RawImage(data, 1, 1, color_type=ColorType.rgba)
```

The pyoxipng order requires a descriptor such as `ColorType.rgba()`. The stable
order requires an enum value such as `ColorType.rgba`.

For constructor details, defaults, palette rules, and examples, see
[Create PNGs From Raw Pixels](raw-image.md).

## Color Types

Use enum values in new code:

```python
ColorType.rgba
ColorType.rgb
ColorType.indexed
```

Callable color types are compatibility paths:

```python
ColorType.rgba()
ColorType.rgb(None)
ColorType.indexed([(255, 0, 0)])
```

They emit `DeprecationWarning`.

For palette and transparency rules, see
[Create PNGs From Raw Pixels](raw-image.md).

## Other Stable Options

Common optimization options are stable. Use Python option names directly:

```python
optimize_from_memory(
    data=png_bytes,
    optimize_alpha=True,
    bit_depth_reduction=True,
    color_type_reduction=True,
    palette_reduction=True,
    grayscale_reduction=True,
    idat_recoding=True,
    scale_16=True,
    fast_evaluation=False,
    timeout=10,
    max_decompressed_size=256 * 1024 * 1024,
)
```

Use `StripChunks` and `Deflaters` factories as stable API:

```python
from oxipng import Deflaters, StripChunks

strip = StripChunks.strip(["tEXt"])
deflater = Deflaters.libdeflater(11)
```

These callable enum members are deprecated and emit `DeprecationWarning`:

```python
from oxipng import StripChunks

strip = StripChunks.none()
strip = StripChunks.safe()
strip = StripChunks.all()
```

For the full option surface, see
[Options Surface](../architecture/options-surface.md).

## stdin and stdout

stdin and stdout are caller-owned. Read bytes first. Then call
`optimize_from_memory`.

See
[Optimize PNG data in memory](memory-optimization.md#stdin-and-stdout)
for the stream example.

## Migration Checklist

1. Change dependency metadata from `pyoxipng` to `oxipng-pybind`.
2. Keep imports as `oxipng`.
3. Replace `RowFilter` with `FilterStrategy`.
4. Replace `Interlacing.Off` and `Interlacing.Adam7`.
5. Replace callable `ColorType` values in new `RawImage` code.
6. Use the stable `RawImage(width, height, color_type, bit_depth, data)` order.
7. Replace `StripChunks.none()`, `StripChunks.safe()`, and `StripChunks.all()`.
8. Run tests with `DeprecationWarning` visible.
9. Remove all compatibility paths before a future release removes them.

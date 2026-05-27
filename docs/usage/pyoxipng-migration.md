# Move From pyoxipng

Use this guide when old code imports `pyoxipng` or uses pyoxipng names.

Stable API means the supported `oxipng-pybind` names. A compatibility path is
an old pyoxipng shape that still works for now. Compatibility paths emit
`DeprecationWarning` and will be removed in a future release.

Some names also existed in pyoxipng and are stable here. They do not warn.

Examples:

- `StripChunks.strip`
- `StripChunks.keep`
- `Deflaters.libdeflater`
- `Deflaters.zopfli`

## Import Name

Change imports to `oxipng`:

```python
from oxipng import optimize, optimize_from_memory
```

Do not import `pyoxipng` from this package.

## Row Filters

Use `FilterStrategy` in new code:

```python
from oxipng import FilterStrategy

filter = FilterStrategy.none
filters = FilterStrategy.predefined(["none", "sub", "up"])
```

Do not use `RowFilter` in new code.

`RowFilter` exists only for old pyoxipng code. It warns when you access a
member:

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
| `[RowFilter.none, RowFilter.sub]` | `FilterStrategy.predefined(["none", "sub"])` |

`FilterStrategy.predefined(...)` preserves the supplied order. It accepts
ordered sequences and generators, and it rejects `set` and `frozenset`. Pass
`sorted(values)` if old code intentionally built predefined filters from a set.

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
width = 1
height = 1
raw = RawImage(
    width=width,
    height=height,
    color_type=ColorType.rgba,
    bit_depth=BitDepth.eight,
    data=data,
)
```

The old pyoxipng order still works only as a migration path:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(data, width, height, color_type=ColorType.rgba())
```

That path emits `DeprecationWarning`. Do not mix the two shapes.

This call is rejected:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(data, width, height, color_type=ColorType.rgba)
```

The pyoxipng order requires a descriptor such as `ColorType.rgba()`. The stable
order requires an enum value such as `ColorType.rgba`.

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

Indexed palettes preserve order. Tuple palette entries are the canonical style,
but both stable `RawImage(..., palette=...)` and the `ColorType.indexed(...)`
compatibility path accept ordered 3- or 4-channel sequences, including
JSON-style lists. They reject strings, bytes, mappings, sets, frozensets, wrong
entry lengths, boolean channels, and channel values outside `0..255`.

## Other Options

Most practical options are stable now.

Underlying option behavior comes from Rust
[`oxipng::Options`](https://docs.rs/oxipng/latest/oxipng/struct.Options.html).
This package maps those options to Python names and values.

Use these names directly:

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

## stdin and stdout

stdin and stdout are caller-owned. Read bytes first. Then call
`optimize_from_memory`:

```python
import sys

from oxipng import optimize_from_memory

data = sys.stdin.buffer.read()
optimized = optimize_from_memory(data=data)
sys.stdout.buffer.write(optimized)
```

This keeps process stream handling in caller code.

## Migration Checklist

1. Change imports from `pyoxipng` to `oxipng`.
2. Replace `RowFilter` with `FilterStrategy`.
3. Replace `Interlacing.Off` and `Interlacing.Adam7`.
4. Replace callable `ColorType` values in new `RawImage` code.
5. Use the stable `RawImage(width=..., height=..., color_type=..., bit_depth=..., data=...)` order.
6. Run tests with `DeprecationWarning` visible.
7. Remove all compatibility paths before a future release removes them.

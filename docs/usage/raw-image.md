# Create PNGs From Raw Pixels

Use [`RawImage`](../../oxipng/__init__.pyi) when you have packed pixel bytes
but no PNG file yet.

It wraps Rust
[`oxipng::RawImage`](https://docs.rs/oxipng/latest/oxipng/struct.RawImage.html).

## Basic Use

Create a one-pixel RGBA PNG:

```python
from oxipng import BitDepth, ColorType, RawImage

raw = RawImage(
    width=1,
    height=1,
    color_type=ColorType.rgba,
    bit_depth=BitDepth.eight,
    data=bytes([255, 0, 0, 255]),
)
png_bytes = raw.create_optimized_png(level=3)
```

## Constructor

`RawImage` accepts:

- width
- height
- color type
- bit depth
- packed pixel data

Width and height are in pixels. These values may be positional or keyword
arguments.

`color_type` accepts `ColorType` enum values or string aliases.
See Rust
[`ColorType`](https://docs.rs/oxipng/latest/oxipng/enum.ColorType.html)
for the underlying color model.

`bit_depth` accepts `BitDepth` enum values or integer bit depths.
See Rust
[`BitDepth`](https://docs.rs/oxipng/latest/oxipng/enum.BitDepth.html)
for the underlying bit depth model.

Supported string color types are:

- `grayscale`
- `rgb`
- `indexed`
- `grayscale_alpha`
- `rgba`

Supported bit depths are `1`, `2`, `4`, `8`, and `16`.

Pixel data may be:

- [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes)
- [`bytearray`](https://docs.python.org/3/library/stdtypes.html#bytearray)
- [`memoryview`](https://docs.python.org/3/library/stdtypes.html#memoryview)

## Optimization Options

`create_optimized_png()` returns `bytes`. It accepts the same in-memory
optimization options as `optimize_from_memory`.

Common options include `level`, `interlace`, `strip`, `deflate`, `filter`,
`fix_errors`, and `force`. `interlace` accepts `keep`, `off`, or `on`.

See [Options Surface](../architecture/options-surface.md) for the full option
list and value types.

## Indexed Images

Indexed images require a palette:

```python
from oxipng import RawImage

raw = RawImage(
    width=2,
    height=1,
    color_type="indexed",
    bit_depth=8,
    data=bytes([0, 1]),
    palette=[(255, 0, 0), (0, 0, 255, 128)],
)
png_bytes = raw.create_optimized_png()
```

## Transparency

Transparent colors are supported for grayscale and RGB raw images:

```python
from oxipng import BitDepth, ColorType, RawImage

gray = RawImage(
    width=1,
    height=1,
    color_type=ColorType.grayscale,
    bit_depth=BitDepth.eight,
    data=bytes([0]),
    transparent=0,
)
rgb = RawImage(
    width=1,
    height=1,
    color_type=ColorType.rgb,
    bit_depth=BitDepth.eight,
    data=bytes([255, 0, 0]),
    transparent=(255, 0, 0),
)
```

`transparent` is not accepted for indexed, grayscale-alpha, or RGBA images. Use
alpha values in palette entries for indexed transparency. Transparent values
must fit the selected bit depth.

## PNG Chunks

Add an auxiliary PNG chunk before optimization:

```python
from oxipng import BitDepth, ColorType, RawImage

raw = RawImage(
    width=1,
    height=1,
    color_type=ColorType.grayscale,
    bit_depth=BitDepth.eight,
    data=bytes([0]),
)
raw.add_png_chunk(b"tEXt", b"Comment\x00created from raw pixels")
png_bytes = raw.create_optimized_png()
```

The chunk name must be four ASCII letters. It must be public, ancillary, and
safe to copy. The binding rejects structural chunks such as:

- `IHDR`
- `PLTE`
- `IDAT`
- `IEND`
- `tRNS`
- `iCCP`

## ICC Profiles

Attach an ICC profile before optimization:

```python
from oxipng import BitDepth, ColorType, RawImage

icc_profile_bytes = b"example ICC profile bytes"
raw = RawImage(
    width=1,
    height=1,
    color_type=ColorType.grayscale,
    bit_depth=BitDepth.eight,
    data=bytes([0]),
)
raw.add_icc_profile(icc_profile_bytes)
png_bytes = raw.create_optimized_png()
```

## Errors

These inputs raise `ValueError`:

- invalid bit depths
- invalid color types
- invalid palette values
- invalid transparency values
- invalid chunk names

Unsupported keywords raise `TypeError`.

Invalid raw image data raises `PngError`. One example is data with the wrong
length for the image shape.

```python
from oxipng import BitDepth, ColorType, PngError, RawImage

try:
    RawImage(
        width=1,
        height=1,
        color_type=ColorType.rgb,
        bit_depth=BitDepth.eight,
        data=bytes([255]),
    )
except PngError:
    print("not valid raw image data")
```

## pyoxipng Migration

The old pyoxipng constructor order still works as a migration path:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(data, width, height, color_type=ColorType.rgba())
```

This path emits `DeprecationWarning`. Move color details into stable `RawImage`
arguments:

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

Do not mix the two shapes. This call is rejected:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(data, width, height, color_type=ColorType.rgba)
```

The pyoxipng order requires a descriptor such as `ColorType.rgba()`.

See [Move from pyoxipng](pyoxipng-migration.md) for all migration rules.

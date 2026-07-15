# Create PNGs From Raw Pixels

Use [`RawImage`](../../oxipng/__init__.pyi) when you have packed pixel bytes
but no PNG file yet.

It wraps Rust [`oxipng::RawImage`].

[`oxipng::RawImage`]: https://docs.rs/oxipng/latest/oxipng/struct.RawImage.html

## Create a One-Pixel RGBA PNG

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

## Constructor Arguments

Use the stable constructor order:

```python
RawImage(width, height, color_type, bit_depth, data)
```

Width and height are pixels. You can pass the five stable arguments as
positional or keyword arguments.

`color_type` accepts `ColorType` enum values or string aliases.
See Rust [`ColorType`] for the underlying color model.

`bit_depth` accepts `BitDepth` enum values or integer bit depths.
See Rust [`BitDepth`] for the underlying bit depth model.

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

[`ColorType`]: https://docs.rs/oxipng/latest/oxipng/enum.ColorType.html
[`BitDepth`]: https://docs.rs/oxipng/latest/oxipng/enum.BitDepth.html

## Optimization Options

`create_optimized_png()` returns `bytes`. It accepts the same in-memory
optimization options as `optimize_from_memory` and rejects file-only options.

See [Options Surface](../architecture/options-surface.md) for option names,
value types, and rejected file-only options.

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

`RawImage` supports transparent colors for grayscale and RGB raw images:

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

`RawImage` does not accept `transparent` for indexed, grayscale-alpha, or RGBA
images. Use alpha values in palette entries for indexed transparency instead.
Transparent values must fit the selected bit depth.

## PNG Chunks

Use `add_png_chunk()` to add an auxiliary PNG chunk before optimization:

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
safe to copy. The binding rejects structural chunks, such as `IHDR`, `PLTE`,
`IDAT`, `IEND`, `tRNS`, and `iCCP`.

## ICC Profiles

Use `add_icc_profile()` to attach an ICC profile before optimization:

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

Bad argument values raise `ValueError`. Examples include invalid bit depths,
color types, palette values, transparency values, and chunk names.

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

The old pyoxipng constructor order still works only as a migration path:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(data, width, height, color_type=ColorType.rgba())
```

This path emits `DeprecationWarning`. The pyoxipng order requires a descriptor
such as `ColorType.rgba()`. Do not mix it with the stable enum value:

```python
from oxipng import ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(data, width, height, color_type=ColorType.rgba)
```

Use `RawImage(width, height, color_type, bit_depth, data)` in new code. See
[Move from pyoxipng](pyoxipng-migration.md#raw-images) for all migration
rules.

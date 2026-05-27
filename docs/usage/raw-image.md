# Create PNGs From Raw Pixels

Use `RawImage` when pixels are available as packed channel bytes and no input
PNG file exists yet.

## Basic Use

Create a one-pixel RGBA PNG:

```python
from oxipng import BitDepth, ColorType, RawImage

raw = RawImage(
    1,
    1,
    ColorType.rgba,
    BitDepth.eight,
    bytes([255, 0, 0, 255]),
)
png_bytes = raw.create_optimized_png(level=3)
```

## Options

The `RawImage` constructor accepts width, height, color type, bit depth, and
packed pixel data. Width and height are in pixels. These values may be
positional or keyword arguments.

`color_type` accepts `ColorType` enum values or string aliases. `bit_depth`
accepts `BitDepth` enum values or integer bit depths. Pixel data may be
`bytes`, `bytearray`, or `memoryview`.

Indexed images require a palette:

```python
from oxipng import RawImage

raw = RawImage(
    2,
    1,
    "indexed",
    8,
    bytes([0, 1]),
    palette=[(255, 0, 0), (0, 0, 255, 128)],
)
png_bytes = raw.create_optimized_png()
```

Transparent colors are supported for grayscale and RGB raw images:

```python
from oxipng import BitDepth, ColorType, RawImage

gray = RawImage(
    1,
    1,
    ColorType.grayscale,
    BitDepth.eight,
    bytes([0]),
    transparent=0,
)
rgb = RawImage(
    1,
    1,
    ColorType.rgb,
    BitDepth.eight,
    bytes([255, 0, 0]),
    transparent=(255, 0, 0),
)
```

`transparent` is not accepted for indexed, grayscale-alpha, or RGBA images. Use
alpha values in palette entries for indexed transparency. Transparent values
must fit the selected bit depth.

Add an auxiliary PNG chunk before optimization:

```python
from oxipng import BitDepth, ColorType, RawImage

raw = RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]))
raw.add_png_chunk(b"tEXt", b"Comment\x00created from raw pixels")
png_bytes = raw.create_optimized_png()
```

The chunk name must be four ASCII letters. It must be public, ancillary, and
safe to copy. The binding rejects structural chunks such as `IHDR`, `PLTE`,
`IDAT`, `IEND`, `tRNS`, and `iCCP`.

Attach an ICC profile before optimization:

```python
from oxipng import BitDepth, ColorType, RawImage

icc_profile_bytes = b"example ICC profile bytes"
raw = RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]))
raw.add_icc_profile(icc_profile_bytes)
png_bytes = raw.create_optimized_png()
```

## Errors

Invalid bit depths, color types, palette values, transparency values, and chunk
names raise `ValueError`. Unsupported keywords raise `TypeError`. Invalid raw
image data, such as the wrong data length for the image shape, raises
`PngError`.

```python
from oxipng import BitDepth, ColorType, PngError, RawImage

try:
    RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255]))
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

This path emits `DeprecationWarning`. The warning says it will be removed in a
future release.

Move the color details into stable `RawImage` arguments:

```python
from oxipng import BitDepth, ColorType, RawImage

data = bytes([255, 0, 0, 255])
width = 1
height = 1
raw = RawImage(width, height, ColorType.rgba, BitDepth.eight, data)
```

Do not mix the two shapes. For example, `RawImage(data, width, height,
color_type=ColorType.rgba)` is rejected because pyoxipng order requires a
`ColorType.rgba()` descriptor.

See [Move from pyoxipng](pyoxipng-migration.md) for all migration rules.

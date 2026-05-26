# Raw Image Usage

Use `RawImage` when pixels are already available as packed channel bytes and no
input PNG file exists yet.

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

The constructor accepts:

- `width` and `height` in pixels;
- `ColorType` enum values or string aliases;
- `BitDepth` enum values or integer bit depths;
- packed pixel data as `bytes`, `bytearray`, or `memoryview`.

Indexed images require a palette:

```python
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
gray = RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]), transparent=0)
rgb = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]), transparent=(255, 0, 0))
```

`transparent` is not accepted for indexed, grayscale-alpha, or RGBA images.
Indexed images should express transparency with alpha values in palette entries.

Auxiliary chunks can be added before optimization:

```python
raw.add_png_chunk(b"tEXt", b"Comment\x00created from raw pixels")
```

The Python binding accepts public, ancillary, safe-to-copy chunk names and
rejects structural chunks. For encoder behavior, see upstream
[`oxipng` `RawImage` documentation](https://docs.rs/oxipng/latest/oxipng/struct.RawImage.html);
for detailed PNG chunk naming semantics, see the
[PNG file structure specification](https://libpng.org/pub/png/spec/1.2/PNG-Structure.html).

ICC profiles can be attached before optimization:

```python
raw.add_icc_profile(icc_profile_bytes)
```

Invalid raw image definitions raise `PngError` when upstream rejects the bit
depth, color type, or data length. Invalid Python-side palette and transparency
values raise `ValueError`.

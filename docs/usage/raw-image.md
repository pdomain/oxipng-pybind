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

Auxiliary chunks can be added before optimization:

```python
raw.add_png_chunk(b"tEXt", b"Comment\x00created from raw pixels")
```

Invalid raw image definitions raise `PngError` when upstream rejects the bit
depth, color type, or data length. Invalid Python-side palette and transparency
values raise `ValueError`.

"""Focused type-checking fixture for option shapes."""

from oxipng import BitDepth, ColorType, FilterStrategy, RawImage, optimize_from_memory

png_data = b"not used by basedpyright"

optimize_from_memory(png_data, filter=FilterStrategy.predefined(["none", "sub"]))
optimize_from_memory(png_data, filter=[FilterStrategy.none, "sub"])
optimize_from_memory(
    png_data,
    filter={FilterStrategy.none, FilterStrategy.sub},  # pyright: ignore[reportArgumentType]
)
optimize_from_memory(
    png_data,
    filter=[FilterStrategy.predefined(["none", "sub"])],  # pyright: ignore[reportArgumentType]
)

RawImage(1, 1, ColorType.indexed, BitDepth.eight, b"\x00", palette=[(255, 0, 0)])
RawImage(1, 1, ColorType.indexed, BitDepth.eight, b"\x00", palette=[[255, 0, 0]])
RawImage(
    1,
    1,
    ColorType.indexed,
    BitDepth.eight,
    b"\x00",
    palette=[b"red"],  # pyright: ignore[reportArgumentType]
)

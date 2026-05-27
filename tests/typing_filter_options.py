"""Focused type-checking fixture for filter option shapes."""

from oxipng import FilterStrategy, optimize_from_memory

png_data = b"not used by basedpyright"

optimize_from_memory(png_data, filter=FilterStrategy.predefined(["none", "sub"]))
optimize_from_memory(png_data, filter=[FilterStrategy.none, "sub"])
optimize_from_memory(
    png_data,
    filter=[FilterStrategy.predefined(["none", "sub"])],  # pyright: ignore[reportArgumentType]
)

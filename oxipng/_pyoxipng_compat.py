"""pyoxipng compatibility helpers slated for removal."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TypeAlias, TypeVar, cast
from warnings import warn

_T = TypeVar("_T")

StableIterable: TypeAlias = Iterable[_T]

PYOXIPNG_COMPAT_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)

BASIC_ROW_FILTERS = {"none", "sub", "up", "average", "paeth"}


def warn_pyoxipng_compat(*, stacklevel: int = 3) -> None:
    """Emit the pyoxipng compatibility removal warning."""
    warn(PYOXIPNG_COMPAT_WARNING, DeprecationWarning, stacklevel=stacklevel)


def stable_values(values: object, *, context: str) -> tuple[object, ...]:
    """Return stable API iterable values after rejecting scalar containers."""
    if isinstance(values, (str, bytes, bytearray, memoryview, Mapping)):
        raise TypeError(f"{context} must be an iterable of values")
    if not isinstance(values, Iterable):
        raise TypeError(f"{context} must be an iterable of values")
    return tuple(values)


def chunk_names(names: StableIterable[str]) -> tuple[str, ...]:
    """Return stable API chunk names as strings."""
    normalized: list[str] = []
    for name in stable_values(names, context="chunk names"):
        if not isinstance(name, str):
            raise TypeError("chunk names must be strings")
        normalized.append(str(name))
    return tuple(normalized)


class DeprecatedAlias:
    """Descriptor for deprecated pyoxipng enum aliases."""

    value: object

    def __init__(self, value: object) -> None:
        self.value = value

    def __get__(self, obj: object, owner: object = None) -> object:
        warn_pyoxipng_compat(stacklevel=3)
        return self.value


@dataclass(frozen=True)
class CompatColorType:
    kind: str
    bit_depth: int
    palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None
    transparent: int | tuple[int, int, int] | None = None


def color_type_call(
    value: object,
    transparent: object = None,
    *,
    bit_depth: object,
) -> CompatColorType:
    """Create a pyoxipng-compatible color descriptor."""
    warn_pyoxipng_compat()
    raw_bit_depth = cast("int", getattr(bit_depth, "value", bit_depth))
    raw_value = cast("str", getattr(value, "value", value))
    if raw_value == "indexed":
        if not isinstance(transparent, list):
            raise ValueError("indexed color_type requires a palette")
        transparent_palette = cast(
            "list[tuple[int, int, int] | tuple[int, int, int, int]]", transparent
        )
        palette = list(transparent_palette)
        return CompatColorType("indexed", raw_bit_depth, palette=palette)
    if raw_value in {"rgba", "grayscale_alpha"}:
        if transparent is not None:
            raise ValueError(f"{raw_value} does not accept transparent")
        return CompatColorType(raw_value, raw_bit_depth)
    if isinstance(transparent, list):
        raise TypeError(f"{raw_value} does not accept palette")
    transparent_value = cast("int | tuple[int, int, int] | None", transparent)
    return CompatColorType(raw_value, raw_bit_depth, transparent=transparent_value)


@dataclass(frozen=True)
class CompatStripChunks:
    mode: str
    names: tuple[str, ...]


def strip_chunks(names: StableIterable[str]) -> CompatStripChunks:
    """Create a strip-chunk option for explicit PNG chunk names."""
    return CompatStripChunks("strip", chunk_names(names))


def keep_chunks(names: StableIterable[str]) -> CompatStripChunks:
    """Create a keep-chunk option for explicit PNG chunk names."""
    return CompatStripChunks("keep", chunk_names(names))


@dataclass(frozen=True)
class CompatDeflater:
    kind: str
    value: int


def libdeflater(compression: int = 11) -> CompatDeflater:
    """Create a libdeflater option with an explicit compression level."""
    if isinstance(compression, bool):
        warn_pyoxipng_compat()
    return CompatDeflater("libdeflater", compression)


def zopfli(iterations: int = 15) -> CompatDeflater:
    """Create a zopfli option with an explicit iteration count."""
    if isinstance(iterations, bool):
        warn_pyoxipng_compat()
        if iterations is False:
            raise TypeError("deflate zopfli iterations must be an integer")
    return CompatDeflater("zopfli", iterations)


@dataclass(frozen=True)
class PredefinedFilters:
    filters: tuple[str, ...]


def predefined_filters(filters: StableIterable[object]) -> PredefinedFilters:
    """Create a predefined row-filter sequence."""
    values = stable_values(filters, context="predefined filters")
    if not values:
        raise ValueError("predefined filter must not be empty")
    parsed = tuple(basic_row_filter_value(filter_value) for filter_value in values)
    return PredefinedFilters(parsed)


def basic_row_filter_value(value: object) -> str:
    """Return the string value for a basic row filter."""
    raw_value = getattr(value, "value", value)
    if not isinstance(raw_value, str):
        raise TypeError("predefined filter entries must be row filter names")
    if raw_value not in BASIC_ROW_FILTERS:
        raise ValueError("predefined filter entries must be one of: none, sub, up, average, paeth")
    return raw_value

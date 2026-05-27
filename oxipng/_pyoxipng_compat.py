"""pyoxipng compatibility helpers slated for removal."""
# pyright: reportImplicitOverride=false

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
from enum import EnumMeta
from warnings import warn

PYOXIPNG_COMPAT_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)

BASIC_ROW_FILTERS = {"none", "sub", "up", "average", "paeth"}


def warn_pyoxipng_compat(*, stacklevel: int = 3) -> None:
    """Emit the pyoxipng compatibility removal warning."""
    warn(PYOXIPNG_COMPAT_WARNING, DeprecationWarning, stacklevel=stacklevel)


class PyoxipngCompatEnumMeta(EnumMeta):
    """Warn when deprecated pyoxipng enum aliases are accessed."""

    def __getattribute__(cls, name: str) -> object:
        value = super().__getattribute__(name)
        if not name.startswith("_"):
            deprecated_names = (
                super()
                .__getattribute__("__dict__")
                .get("__pyoxipng_deprecated_names__", frozenset())
            )
            if name in deprecated_names:
                warn_pyoxipng_compat(stacklevel=3)
        return value


@dataclass(frozen=True)
class CompatColorType:
    kind: str
    bit_depth: int
    palette: list[Sequence[int]] | None = None
    transparent: int | tuple[int, int, int] | None = None


@dataclass(frozen=True)
class CompatStripChunks:
    mode: str
    names: tuple[str, ...]


@dataclass(frozen=True)
class CompatDeflater:
    kind: str
    value: int


@dataclass(frozen=True)
class PredefinedFilters:
    filters: tuple[str, ...]


def reject_unordered_predefined_filters(value: object) -> None:
    """Reject unordered predefined-filter containers."""
    if isinstance(value, (set, frozenset)):
        raise TypeError(
            "predefined filter must be an ordered iterable; pass sorted(values) explicitly"
        )


def ordered_palette_sequence(value: object, context: str) -> Sequence[object]:
    """Return an ordered finite palette sequence or raise TypeError."""
    if isinstance(value, (str, bytes, bytearray, memoryview, Mapping, Set)):
        raise TypeError(f"{context} must be an ordered sequence")
    if not isinstance(value, Sequence):
        raise TypeError(f"{context} must be an ordered sequence")
    return value


def basic_row_filter_value(value: object) -> str:
    """Return the string value for a basic row filter."""
    raw_value = getattr(value, "value", value)
    if not isinstance(raw_value, str):
        raise TypeError("predefined filter entries must be row filter names")
    if raw_value not in BASIC_ROW_FILTERS:
        raise ValueError("predefined filter entries must be one of: none, sub, up, average, paeth")
    return raw_value

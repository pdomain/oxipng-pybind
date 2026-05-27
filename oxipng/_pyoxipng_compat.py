"""pyoxipng compatibility helpers slated for removal."""
# pyright: reportImplicitOverride=false

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, field
from enum import EnumMeta
from typing import Any
from warnings import warn

PYOXIPNG_COMPAT_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)

BASIC_ROW_FILTERS = {"none", "sub", "up", "average", "paeth"}
COMPAT_UNORDERED_FILTER_WARNING = (
    "set and other unordered filter collections are accepted only for pyoxipng "
    "compatibility; use an ordered list or tuple with oxipng-pybind's stable API."
)
_COMPAT_MARKER = object()


def warn_pyoxipng_compat(*, stacklevel: int = 3) -> None:
    """Emit the pyoxipng compatibility removal warning."""
    warn(PYOXIPNG_COMPAT_WARNING, DeprecationWarning, stacklevel=stacklevel)


def warn_unordered_filter_compat(*, stacklevel: int = 3) -> None:
    """Emit the pyoxipng unordered filter compatibility warning."""
    warn(COMPAT_UNORDERED_FILTER_WARNING, DeprecationWarning, stacklevel=stacklevel)


class PyoxipngCompatEnumMeta(EnumMeta):
    """Warn when deprecated pyoxipng enum aliases are accessed."""

    def __call__(cls, value: object, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        result = super().__call__(value, *args, **kwargs)
        deprecated_names = (
            super().__getattribute__("__dict__").get("__pyoxipng_deprecated_names__", frozenset())
        )
        if value in deprecated_names:
            warn_pyoxipng_compat(stacklevel=3)
        return result

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

    def __getitem__(cls, name: str) -> object:
        value = super().__getitem__(name)
        deprecated_names = (
            super().__getattribute__("__dict__").get("__pyoxipng_deprecated_names__", frozenset())
        )
        if name in deprecated_names:
            warn_pyoxipng_compat(stacklevel=3)
        return value


@dataclass(frozen=True)
class CompatColorType:
    kind: str
    bit_depth: int
    palette: tuple[tuple[int, ...], ...] | None = None
    transparent: int | tuple[int, int, int] | None = None
    _oxipng_pybind_compat_marker: object = field(default=_COMPAT_MARKER, init=False, repr=False)


@dataclass(frozen=True)
class CompatStripChunks:
    mode: str
    names: tuple[str, ...]
    _oxipng_pybind_compat_marker: object = field(default=_COMPAT_MARKER, init=False, repr=False)


@dataclass(frozen=True)
class CompatDeflater:
    kind: str
    value: int
    _oxipng_pybind_compat_marker: object = field(default=_COMPAT_MARKER, init=False, repr=False)


@dataclass(frozen=True)
class PredefinedFilters:
    filters: tuple[str, ...]
    _oxipng_pybind_compat_marker: object = field(default=_COMPAT_MARKER, init=False, repr=False)


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

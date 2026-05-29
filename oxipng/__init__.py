"""Python facade for the native oxipng extension."""

import inspect
from enum import Enum
from typing import TYPE_CHECKING, cast

from . import _pyoxipng_compat as _compat


class Interlacing(Enum):
    """PNG interlacing behavior."""

    keep = "keep"
    off = "off"
    on = "on"


# Keep deprecated aliases as simple class assignments. Astroid 4.0.x can
# recurse while transforming module-level setattr/helper calls around Enum
# aliases.
Interlacing.Off = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    Interlacing.off
)
Interlacing.Adam7 = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    Interlacing.on
)


class StripChunks(Enum):
    """Metadata stripping behavior."""

    none = "none"
    safe = "safe"
    all = "all"

    @staticmethod
    def strip(
        names: "_compat.StableIterable[str]",
    ) -> "_compat.CompatStripChunks":
        """Create a strip-chunk option for explicit PNG chunk names."""
        return _compat.strip_chunks(names)

    @staticmethod
    def keep(
        names: "_compat.StableIterable[str]",
    ) -> "_compat.CompatStripChunks":
        """Create a keep-chunk option for explicit PNG chunk names."""
        return _compat.keep_chunks(names)

    def __call__(self) -> "StripChunks":
        """Create a deprecated pyoxipng-compatible factory."""
        _compat.warn_pyoxipng_compat()
        return self


class Deflater(Enum):
    """DEFLATE backend."""

    libdeflater = "libdeflater"
    zopfli = "zopfli"


class Deflaters:
    """DEFLATE option factories."""

    @staticmethod
    def libdeflater(compression: "int" = 11) -> "_compat.CompatDeflater":
        """Create a libdeflater option with an explicit compression level."""
        return _compat.libdeflater(compression)

    @staticmethod
    def zopfli(iterations: "int" = 15) -> "_compat.CompatDeflater":
        """Create a zopfli option with an explicit iteration count."""
        return _compat.zopfli(iterations)


class FilterStrategy(Enum):
    """PNG row filter strategy."""

    none = "none"
    sub = "sub"
    up = "up"
    average = "average"
    paeth = "paeth"
    minsum = "minsum"
    entropy = "entropy"
    bigrams = "bigrams"
    bigent = "bigent"
    brute = "brute"

    @staticmethod
    def predefined(
        filters: "_compat.StableIterable[object]",
    ) -> "_compat.PredefinedFilters":
        """Create a predefined row-filter sequence."""
        return _compat.predefined_filters(filters)


class RowFilter(Enum):
    """PNG row filter names."""

    _none = "none"
    _sub = "sub"
    _up = "up"
    _average = "average"
    _paeth = "paeth"
    _minsum = "minsum"
    _entropy = "entropy"
    _bigrams = "bigrams"
    _bigent = "bigent"
    _brute = "brute"


# Keep assignments value-based rather than calling RowFilter("...") here.
# Astroid 4.0.x can recurse while transforming those compatibility calls.
_ROW_FILTER_MEMBERS = RowFilter.__members__
RowFilter.none = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_none"]
)
RowFilter.sub = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_sub"]
)
RowFilter.up = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_up"]
)
RowFilter.average = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_average"]
)
RowFilter.paeth = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_paeth"]
)
RowFilter.minsum = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_minsum"]
)
RowFilter.entropy = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_entropy"]
)
RowFilter.bigrams = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_bigrams"]
)
RowFilter.bigent = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_bigent"]
)
RowFilter.brute = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_brute"]
)
RowFilter.NoOp = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_none"]
)
RowFilter.Sub = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_sub"]
)
RowFilter.Up = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_up"]
)
RowFilter.Average = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_average"]
)
RowFilter.Paeth = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_paeth"]
)
RowFilter.MinSum = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_minsum"]
)
RowFilter.Entropy = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_entropy"]
)
RowFilter.Bigrams = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_bigrams"]
)
RowFilter.BigEnt = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_bigent"]
)
RowFilter.Brute = _compat.DeprecatedAlias(  # pyright: ignore[reportAttributeAccessIssue]
    _ROW_FILTER_MEMBERS["_brute"]
)


class BitDepth(Enum):
    """Raw image bit depth."""

    one = 1
    two = 2
    four = 4
    eight = 8
    sixteen = 16


class ColorType(Enum):
    """Raw image color type."""

    grayscale = "grayscale"
    rgb = "rgb"
    indexed = "indexed"
    grayscale_alpha = "grayscale_alpha"
    rgba = "rgba"


def _color_type_call(
    self: "ColorType",
    transparent: (
        "int | tuple[int, int, int] | list[tuple[int, int, int] | tuple[int, int, int, int]] | None"
    ) = None,
    *,
    bit_depth: "int | BitDepth" = BitDepth.eight,
) -> "_compat.CompatColorType":
    """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""
    return _compat.color_type_call(self, transparent, bit_depth=bit_depth)


# Keep ColorType callable assignment outside the Enum body. Astroid 4.0.x can
# recurse while transforming callable Enum methods during Pylint analysis.
setattr(ColorType, "__call__", _color_type_call)  # noqa: B010


if TYPE_CHECKING:
    from collections.abc import Callable

    from .__init__ import (
        OptimizationResult,
        PngError,
        RawImage,
    )

    _analyze = cast("Callable[..., OptimizationResult]", None)
    _optimize = cast("Callable[..., None]", None)
    _optimize_from_memory = cast("Callable[..., bytes]", None)
else:
    from _oxipng import (
        OptimizationResult,
        PngError,
        RawImage,
    )
    from _oxipng import (
        analyze as _analyze,
    )
    from _oxipng import (
        optimize as _optimize,
    )
    from _oxipng import (
        optimize_from_memory as _optimize_from_memory,
    )


def _set_signature(function: object, signature: "inspect.Signature") -> None:
    """Attach a native signature to a Python wrapper."""
    setattr(function, "__signature__", signature)  # noqa: B010


# Reuse native PyO3 text signatures. Astroid 4.0.x can recurse while
# transforming large inline inspect.Signature(parameters=[...]) literals.
_SUPPORTED_ANALYZE_SIGNATURE = inspect.signature(_analyze)
_SUPPORTED_OPTIMIZE_SIGNATURE = inspect.signature(_optimize)
_SUPPORTED_OPTIMIZE_FROM_MEMORY_SIGNATURE = inspect.signature(_optimize_from_memory)


def analyze(  # noqa: PLR0913
    input: "object",
    *,
    level: "int" = 2,
    interlace: "Interlacing | str | None" = None,
    strip: "StripChunks | _compat.CompatStripChunks | str | None" = None,
    deflate: "Deflater | _compat.CompatDeflater | str | None" = None,
    filter: "FilterStrategy | RowFilter | _compat.PredefinedFilters | str | list[FilterStrategy | RowFilter | _compat.PredefinedFilters | str] | tuple[FilterStrategy | RowFilter | _compat.PredefinedFilters | str, ...] | None" = None,
    fix_errors: "bool" = False,
    force: "bool" = False,
    optimize_alpha: "bool | None" = None,
    bit_depth_reduction: "bool | None" = None,
    color_type_reduction: "bool | None" = None,
    palette_reduction: "bool | None" = None,
    grayscale_reduction: "bool | None" = None,
    idat_recoding: "bool | None" = None,
    scale_16: "bool | None" = None,
    fast_evaluation: "bool | None" = None,
    timeout: "float | None" = None,
    max_decompressed_size: "int | None" = None,
    **unsupported: "object",
) -> "OptimizationResult":
    """Return PNG optimization sizes without writing output."""
    if isinstance(level, bool):
        raise TypeError("level must be an integer")
    return _analyze(
        input,
        level=level,
        interlace=interlace,
        strip=strip,
        deflate=deflate,
        filter=filter,
        fix_errors=fix_errors,
        force=force,
        optimize_alpha=optimize_alpha,
        bit_depth_reduction=bit_depth_reduction,
        color_type_reduction=color_type_reduction,
        palette_reduction=palette_reduction,
        grayscale_reduction=grayscale_reduction,
        idat_recoding=idat_recoding,
        scale_16=scale_16,
        fast_evaluation=fast_evaluation,
        timeout=timeout,
        max_decompressed_size=max_decompressed_size,
        **unsupported,
    )


_set_signature(analyze, _SUPPORTED_ANALYZE_SIGNATURE)


def optimize(  # noqa: PLR0913
    input: "object",
    output: "object | None" = None,
    *,
    level: "int" = 2,
    interlace: "Interlacing | str | None" = None,
    strip: "StripChunks | _compat.CompatStripChunks | str | None" = None,
    deflate: "Deflater | _compat.CompatDeflater | str | None" = None,
    filter: "FilterStrategy | RowFilter | _compat.PredefinedFilters | str | list[FilterStrategy | RowFilter | _compat.PredefinedFilters | str] | tuple[FilterStrategy | RowFilter | _compat.PredefinedFilters | str, ...] | None" = None,
    fix_errors: "bool" = False,
    force: "bool" = False,
    backup: "bool" = False,
    preserve_attrs: "bool" = False,
    optimize_alpha: "bool | None" = None,
    bit_depth_reduction: "bool | None" = None,
    color_type_reduction: "bool | None" = None,
    palette_reduction: "bool | None" = None,
    grayscale_reduction: "bool | None" = None,
    idat_recoding: "bool | None" = None,
    scale_16: "bool | None" = None,
    fast_evaluation: "bool | None" = None,
    timeout: "float | None" = None,
    max_decompressed_size: "int | None" = None,
    **unsupported: "object",
) -> "None":
    """Optimize a PNG file on disk."""
    if isinstance(level, bool):
        raise TypeError("level must be an integer")
    return _optimize(
        input,
        output,
        level=level,
        interlace=interlace,
        strip=strip,
        deflate=deflate,
        filter=filter,
        fix_errors=fix_errors,
        force=force,
        backup=backup,
        preserve_attrs=preserve_attrs,
        optimize_alpha=optimize_alpha,
        bit_depth_reduction=bit_depth_reduction,
        color_type_reduction=color_type_reduction,
        palette_reduction=palette_reduction,
        grayscale_reduction=grayscale_reduction,
        idat_recoding=idat_recoding,
        scale_16=scale_16,
        fast_evaluation=fast_evaluation,
        timeout=timeout,
        max_decompressed_size=max_decompressed_size,
        **unsupported,
    )


_set_signature(optimize, _SUPPORTED_OPTIMIZE_SIGNATURE)


def optimize_from_memory(  # noqa: PLR0913
    data: "object",
    *,
    level: "int" = 2,
    interlace: "Interlacing | str | None" = None,
    strip: "StripChunks | _compat.CompatStripChunks | str | None" = None,
    deflate: "Deflater | _compat.CompatDeflater | str | None" = None,
    filter: "FilterStrategy | RowFilter | _compat.PredefinedFilters | str | list[FilterStrategy | RowFilter | _compat.PredefinedFilters | str] | tuple[FilterStrategy | RowFilter | _compat.PredefinedFilters | str, ...] | None" = None,
    fix_errors: "bool" = False,
    force: "bool" = False,
    optimize_alpha: "bool | None" = None,
    bit_depth_reduction: "bool | None" = None,
    color_type_reduction: "bool | None" = None,
    palette_reduction: "bool | None" = None,
    grayscale_reduction: "bool | None" = None,
    idat_recoding: "bool | None" = None,
    scale_16: "bool | None" = None,
    fast_evaluation: "bool | None" = None,
    timeout: "float | None" = None,
    max_decompressed_size: "int | None" = None,
    **unsupported: "object",
) -> "bytes":
    """Optimize PNG bytes in memory."""
    if isinstance(level, bool):
        raise TypeError("level must be an integer")
    return _optimize_from_memory(
        data,
        level=level,
        interlace=interlace,
        strip=strip,
        deflate=deflate,
        filter=filter,
        fix_errors=fix_errors,
        force=force,
        optimize_alpha=optimize_alpha,
        bit_depth_reduction=bit_depth_reduction,
        palette_reduction=palette_reduction,
        grayscale_reduction=grayscale_reduction,
        idat_recoding=idat_recoding,
        color_type_reduction=color_type_reduction,
        scale_16=scale_16,
        fast_evaluation=fast_evaluation,
        timeout=timeout,
        max_decompressed_size=max_decompressed_size,
        **unsupported,
    )


_set_signature(optimize_from_memory, _SUPPORTED_OPTIMIZE_FROM_MEMORY_SIGNATURE)

__all__ = [
    "BitDepth",
    "ColorType",
    "Deflater",
    "Deflaters",
    "FilterStrategy",
    "Interlacing",
    "OptimizationResult",
    "PngError",
    "RawImage",
    "RowFilter",
    "StripChunks",
    "analyze",
    "optimize",
    "optimize_from_memory",
]

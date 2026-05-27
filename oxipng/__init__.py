"""Python facade for the native oxipng extension."""

import inspect
from enum import Enum
from typing import TYPE_CHECKING

from . import _pyoxipng_compat as _compat


class Interlacing(Enum, metaclass=_compat.PyoxipngCompatEnumMeta):
    """PNG interlacing behavior."""

    __pyoxipng_deprecated_names__ = frozenset({"Off", "Adam7"})

    keep = "keep"
    off = "off"
    on = "on"
    Off = "off"
    Adam7 = "on"


class StripChunks(Enum):
    """Metadata stripping behavior."""

    none = "none"
    safe = "safe"
    all = "all"

    @staticmethod
    def strip(
        names: _compat.StableIterable[str],
    ) -> _compat.CompatStripChunks:
        """Create a strip-chunk option for explicit PNG chunk names."""
        return _compat.CompatStripChunks("strip", _compat.chunk_names(names))

    @staticmethod
    def keep(
        names: _compat.StableIterable[str],
    ) -> _compat.CompatStripChunks:
        """Create a keep-chunk option for explicit PNG chunk names."""
        return _compat.CompatStripChunks("keep", _compat.chunk_names(names))

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
    def libdeflater(compression: int = 11) -> _compat.CompatDeflater:
        """Create a libdeflater option with an explicit compression level."""
        if isinstance(compression, bool):
            _compat.warn_pyoxipng_compat()
        return _compat.CompatDeflater("libdeflater", compression)

    @staticmethod
    def zopfli(iterations: int = 15) -> _compat.CompatDeflater:
        """Create a zopfli option with an explicit iteration count."""
        if isinstance(iterations, bool):
            _compat.warn_pyoxipng_compat()
            if iterations is False:
                raise TypeError("deflate zopfli iterations must be an integer")
        return _compat.CompatDeflater("zopfli", iterations)


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
        filters: _compat.StableIterable[object],
    ) -> _compat.PredefinedFilters:
        """Create a predefined row-filter sequence."""
        values = _compat.stable_values(filters, context="predefined filters")
        if not values:
            raise ValueError("predefined filter must not be empty")
        parsed = tuple(_compat.basic_row_filter_value(filter_value) for filter_value in values)
        return _compat.PredefinedFilters(parsed)


class RowFilter(Enum, metaclass=_compat.PyoxipngCompatEnumMeta):
    """PNG row filter names."""

    __pyoxipng_deprecated_names__ = frozenset(
        {
            "none",
            "sub",
            "up",
            "average",
            "paeth",
            "minsum",
            "entropy",
            "bigrams",
            "bigent",
            "brute",
            "NoOp",
            "Sub",
            "Up",
            "Average",
            "Paeth",
            "MinSum",
            "Entropy",
            "Bigrams",
            "BigEnt",
            "Brute",
        }
    )

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

    NoOp = "none"
    Sub = "sub"
    Up = "up"
    Average = "average"
    Paeth = "paeth"
    MinSum = "minsum"
    Entropy = "entropy"
    Bigrams = "bigrams"
    BigEnt = "bigent"
    Brute = "brute"


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

    def __call__(
        self,
        transparent: int
        | tuple[int, int, int]
        | list[tuple[int, int, int] | tuple[int, int, int, int]]
        | None = None,
        *,
        bit_depth: int | BitDepth = BitDepth.eight,
    ) -> _compat.CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""
        _compat.warn_pyoxipng_compat()
        raw_bit_depth = bit_depth.value if isinstance(bit_depth, BitDepth) else bit_depth
        if self is ColorType.indexed:
            if not isinstance(transparent, list):
                raise ValueError("indexed color_type requires a palette")
            return _compat.CompatColorType("indexed", raw_bit_depth, palette=list(transparent))
        if self in {ColorType.rgba, ColorType.grayscale_alpha}:
            if transparent is not None:
                raise ValueError(f"{self.value} does not accept transparent")
            return _compat.CompatColorType(self.value, raw_bit_depth)
        if isinstance(transparent, list):
            raise TypeError(f"{self.value} does not accept palette")
        return _compat.CompatColorType(self.value, raw_bit_depth, transparent=transparent)


ColorType.__call__.__doc__ = (
    "Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."
)

if TYPE_CHECKING:
    from .__init__ import (
        OptimizationResult,
        PngError,
        RawImage,
        analyze,
        optimize,
        optimize_from_memory,
    )
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

    _SUPPORTED_ANALYZE_SIGNATURE = inspect.Signature(
        parameters=[
            inspect.Parameter("input", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(
                "level",
                inspect.Parameter.KEYWORD_ONLY,
                default=2,
            ),
            inspect.Parameter(
                "interlace",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "strip",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "deflate",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "filter",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "fix_errors",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
            ),
            inspect.Parameter(
                "force",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
            ),
            inspect.Parameter(
                "optimize_alpha",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "bit_depth_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "color_type_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "palette_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "grayscale_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "idat_recoding",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "scale_16",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "fast_evaluation",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "timeout",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "max_decompressed_size",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
        ]
    )

    _SUPPORTED_OPTIMIZE_SIGNATURE = inspect.Signature(
        parameters=[
            inspect.Parameter("input", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("output", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
            inspect.Parameter("level", inspect.Parameter.KEYWORD_ONLY, default=2),
            inspect.Parameter("interlace", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("strip", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("deflate", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("filter", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("fix_errors", inspect.Parameter.KEYWORD_ONLY, default=False),
            inspect.Parameter("force", inspect.Parameter.KEYWORD_ONLY, default=False),
            inspect.Parameter("backup", inspect.Parameter.KEYWORD_ONLY, default=False),
            inspect.Parameter("preserve_attrs", inspect.Parameter.KEYWORD_ONLY, default=False),
            inspect.Parameter(
                "optimize_alpha",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "bit_depth_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "color_type_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "palette_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "grayscale_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "idat_recoding",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "scale_16",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "fast_evaluation",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter("timeout", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter(
                "max_decompressed_size",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
        ]
    )

    _SUPPORTED_OPTIMIZE_FROM_MEMORY_SIGNATURE = inspect.Signature(
        parameters=[
            inspect.Parameter("data", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("level", inspect.Parameter.KEYWORD_ONLY, default=2),
            inspect.Parameter("interlace", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("strip", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("deflate", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("filter", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter("fix_errors", inspect.Parameter.KEYWORD_ONLY, default=False),
            inspect.Parameter("force", inspect.Parameter.KEYWORD_ONLY, default=False),
            inspect.Parameter(
                "optimize_alpha",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "bit_depth_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "color_type_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "palette_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "grayscale_reduction",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "idat_recoding",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "scale_16",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter(
                "fast_evaluation",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
            inspect.Parameter("timeout", inspect.Parameter.KEYWORD_ONLY, default=None),
            inspect.Parameter(
                "max_decompressed_size",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            ),
        ]
    )

    def analyze(  # noqa: PLR0913
        input: object,
        *,
        level: int = 2,
        interlace: Interlacing | str | None = None,
        strip: StripChunks | _compat.CompatStripChunks | str | None = None,
        deflate: Deflater | _compat.CompatDeflater | str | None = None,
        filter: FilterStrategy
        | RowFilter
        | _compat.PredefinedFilters
        | str
        | list[FilterStrategy | RowFilter | _compat.PredefinedFilters | str]
        | tuple[FilterStrategy | RowFilter | _compat.PredefinedFilters | str, ...]
        | set[FilterStrategy | RowFilter | _compat.PredefinedFilters | str]
        | None = None,
        fix_errors: bool = False,
        force: bool = False,
        optimize_alpha: bool | None = None,
        bit_depth_reduction: bool | None = None,
        color_type_reduction: bool | None = None,
        palette_reduction: bool | None = None,
        grayscale_reduction: bool | None = None,
        idat_recoding: bool | None = None,
        scale_16: bool | None = None,
        fast_evaluation: bool | None = None,
        timeout: float | None = None,
        max_decompressed_size: int | None = None,
        **unsupported: object,
    ) -> OptimizationResult:
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

    analyze.__signature__ = _SUPPORTED_ANALYZE_SIGNATURE

    def optimize(  # noqa: PLR0913
        input: object,
        output: object | None = None,
        *,
        level: int = 2,
        interlace: Interlacing | str | None = None,
        strip: StripChunks | _compat.CompatStripChunks | str | None = None,
        deflate: Deflater | _compat.CompatDeflater | str | None = None,
        filter: FilterStrategy
        | RowFilter
        | _compat.PredefinedFilters
        | str
        | list[FilterStrategy | RowFilter | _compat.PredefinedFilters | str]
        | tuple[FilterStrategy | RowFilter | _compat.PredefinedFilters | str, ...]
        | set[FilterStrategy | RowFilter | _compat.PredefinedFilters | str]
        | None = None,
        fix_errors: bool = False,
        force: bool = False,
        backup: bool = False,
        preserve_attrs: bool = False,
        optimize_alpha: bool | None = None,
        bit_depth_reduction: bool | None = None,
        color_type_reduction: bool | None = None,
        palette_reduction: bool | None = None,
        grayscale_reduction: bool | None = None,
        idat_recoding: bool | None = None,
        scale_16: bool | None = None,
        fast_evaluation: bool | None = None,
        timeout: float | None = None,
        max_decompressed_size: int | None = None,
        **unsupported: object,
    ) -> None:
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

    optimize.__signature__ = _SUPPORTED_OPTIMIZE_SIGNATURE

    def optimize_from_memory(  # noqa: PLR0913
        data: object,
        *,
        level: int = 2,
        interlace: Interlacing | str | None = None,
        strip: StripChunks | _compat.CompatStripChunks | str | None = None,
        deflate: Deflater | _compat.CompatDeflater | str | None = None,
        filter: FilterStrategy
        | RowFilter
        | _compat.PredefinedFilters
        | str
        | list[FilterStrategy | RowFilter | _compat.PredefinedFilters | str]
        | tuple[FilterStrategy | RowFilter | _compat.PredefinedFilters | str, ...]
        | set[FilterStrategy | RowFilter | _compat.PredefinedFilters | str]
        | None = None,
        fix_errors: bool = False,
        force: bool = False,
        optimize_alpha: bool | None = None,
        bit_depth_reduction: bool | None = None,
        color_type_reduction: bool | None = None,
        palette_reduction: bool | None = None,
        grayscale_reduction: bool | None = None,
        idat_recoding: bool | None = None,
        scale_16: bool | None = None,
        fast_evaluation: bool | None = None,
        timeout: float | None = None,
        max_decompressed_size: int | None = None,
        **unsupported: object,
    ) -> bytes:
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

    optimize_from_memory.__signature__ = _SUPPORTED_OPTIMIZE_FROM_MEMORY_SIGNATURE

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

"""Python facade for the native oxipng extension."""

import inspect
from os import PathLike

from _oxipng import PngError, optimize as _optimize

StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]


def optimize(
    input: StrOrBytesPath,
    output: StrOrBytesPath | None = None,
    **kwargs: object,
) -> None:
    """Optimize a PNG file on disk."""
    _optimize(input, output, **kwargs)


optimize.__signature__ = inspect.Signature(
    parameters=[
        inspect.Parameter("input", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter(
            "output",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=None,
        ),
        inspect.Parameter(
            "level",
            inspect.Parameter.KEYWORD_ONLY,
            default=2,
        ),
    ],
)

__all__ = ["PngError", "optimize"]

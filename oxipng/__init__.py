"""Python facade for the native oxipng extension."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

    StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]

    class PngError(Exception):
        """Raised when oxipng cannot optimize the input PNG."""

    def optimize(
        input: StrOrBytesPath,
        output: StrOrBytesPath | None = None,
        *,
        level: int = 2,
    ) -> None:
        """Optimize a PNG file on disk."""
        _ = (input, output, level)

else:
    from _oxipng import PngError, optimize

__all__ = ["PngError", "optimize"]

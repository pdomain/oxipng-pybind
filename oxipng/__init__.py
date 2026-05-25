"""Python facade for the native oxipng extension."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .__init__ import PngError, optimize
else:
    from _oxipng import PngError, optimize

__all__ = ["PngError", "optimize"]

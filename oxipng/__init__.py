"""Python facade for the native oxipng extension."""

from _oxipng import PngError, optimize

__all__ = ["PngError", "optimize"]

"""Typing stub for the supported se-pyoxipng API."""

from os import PathLike
from typing import Union

StrOrBytesPath = Union[str, bytes, PathLike[str], PathLike[bytes]]


class PngError(Exception):
    """Raised when oxipng cannot optimize the input PNG."""


def optimize(input: StrOrBytesPath, output: StrOrBytesPath | None = None, *, level: int = 2) -> None:
    """Optimize a PNG file on disk."""

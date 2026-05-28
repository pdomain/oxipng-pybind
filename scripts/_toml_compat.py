"""TOML parsing helpers compatible with Python 3.10+ environments."""

from __future__ import annotations

import importlib
from typing import Any, BinaryIO, TextIO, cast

_FALLBACK_IMPORT_ERROR = "tomllib and tomlkit are both unavailable in this environment."
try:
    _toml = importlib.import_module("tomllib")
except ModuleNotFoundError:
    try:
        _toml = importlib.import_module("tomlkit")
    except ModuleNotFoundError as error:  # pragma: no cover - requires both modules missing.
        raise RuntimeError(_FALLBACK_IMPORT_ERROR) from error


def _loads_text(data: str) -> dict[str, Any]:
    loads = getattr(_toml, "loads", None)
    if callable(loads):
        return cast("dict[str, Any]", loads(data))

    parse = getattr(_toml, "parse", None)
    if callable(parse):
        return cast("dict[str, Any]", parse(data))

    raise RuntimeError("No TOML parser with loads/parse support is available.")


def load(fp: TextIO | BinaryIO) -> dict[str, Any]:
    """Parse TOML text from an open text stream."""
    data = fp.read()
    if isinstance(data, bytes):
        return _loads_text(data.decode("utf-8"))
    return _loads_text(data)


def loads(text: str) -> dict[str, Any]:
    """Parse TOML from text."""
    return _loads_text(text)


def load_file(path: str) -> dict[str, Any]:
    """Read and parse TOML from a filesystem path."""
    with open(path, encoding="utf-8") as file:
        return _loads_text(file.read())

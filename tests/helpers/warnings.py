"""Shared warning assertions for tests."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable
    from warnings import WarningMessage

PYOXIPNG_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)

T = TypeVar("T")


def _format_unexpected_warning(warning: WarningMessage) -> str:
    category_name = warning.category.__name__
    message = warning.message
    if issubclass(warning.category, DeprecationWarning):
        return f"unexpected {category_name} (unexpected warning): {message}"
    return f"unexpected warning: {category_name}: {message}"


def assert_no_deprecation_warning(callback: Callable[[], T]) -> T:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = callback()

    if caught:
        raise AssertionError(_format_unexpected_warning(caught[0]))
    return result


def assert_pyoxipng_warning(callback: Callable[[], T]) -> T:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = callback()

    matches = [
        warning
        for warning in caught
        if issubclass(warning.category, DeprecationWarning)
        and str(warning.message) == PYOXIPNG_WARNING
    ]
    unexpected = [warning for warning in caught if warning not in matches]
    if unexpected:
        raise AssertionError(_format_unexpected_warning(unexpected[0]))
    if len(matches) != 1:
        raise AssertionError(f"expected one pyoxipng compatibility warning, got {len(matches)}")
    return result

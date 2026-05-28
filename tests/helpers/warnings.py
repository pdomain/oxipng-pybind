"""Shared warning assertions for tests."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

PYOXIPNG_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)

T = TypeVar("T")


def assert_no_deprecation_warning(callback: Callable[[], T]) -> T:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = callback()

    matches = [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
    if matches:
        raise AssertionError(f"unexpected DeprecationWarning: {matches[0].message}")
    return result


def assert_pyoxipng_warning(callback: Callable[[], T]) -> T:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = callback()

    matches = [
        warning
        for warning in caught
        if issubclass(warning.category, DeprecationWarning)
        and PYOXIPNG_WARNING in str(warning.message)
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one pyoxipng compatibility warning, got {len(matches)}")
    return result

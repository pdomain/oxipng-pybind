"""Tests for shared warning assertion helpers."""

from __future__ import annotations

import warnings

import pytest

from tests.helpers.warnings import (
    PYOXIPNG_WARNING,
    assert_no_deprecation_warning,
    assert_pyoxipng_warning,
)


def test_assert_no_deprecation_warning_accepts_clean_call() -> None:
    result = assert_no_deprecation_warning(lambda: "ok")

    assert result == "ok"


def test_assert_no_deprecation_warning_rejects_deprecation() -> None:
    def warn() -> None:
        warnings.warn("deprecated", DeprecationWarning, stacklevel=2)

    with pytest.raises(AssertionError, match="unexpected DeprecationWarning"):
        assert_no_deprecation_warning(warn)


def test_assert_no_deprecation_warning_rejects_unexpected_warning() -> None:
    def warn() -> None:
        warnings.warn("surprise", UserWarning, stacklevel=2)

    with pytest.raises(AssertionError, match="unexpected warning"):
        assert_no_deprecation_warning(warn)


def test_assert_pyoxipng_warning_returns_value() -> None:
    def warn() -> str:
        warnings.warn(PYOXIPNG_WARNING, DeprecationWarning, stacklevel=2)
        return "compat"

    assert assert_pyoxipng_warning(warn) == "compat"


def test_assert_pyoxipng_warning_rejects_extra_unexpected_warning() -> None:
    def warn() -> None:
        warnings.warn(PYOXIPNG_WARNING, DeprecationWarning, stacklevel=2)
        warnings.warn("surprise", UserWarning, stacklevel=2)

    with pytest.raises(AssertionError, match="unexpected warning"):
        assert_pyoxipng_warning(warn)

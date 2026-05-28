"""Tests for the installed wheel smoke check."""

from __future__ import annotations

import re
from importlib import metadata

import pytest

from scripts import smoke_wheel


def test_smoke_wheel_main_exercises_installed_package_with_stdlib_png() -> None:
    assert smoke_wheel.main(["--allow-editable", "--stdlib-png"]) == 0


def test_smoke_wheel_release_mode_has_no_editable_typing_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_files(_distribution: str) -> list[str]:
        return ["oxipng_pybind.pth"]

    monkeypatch.setattr(metadata, "files", fake_files)

    missing_typing_files = "wheel is missing oxipng/__init__.pyi, oxipng/py.typed"
    with pytest.raises(RuntimeError, match=re.escape(missing_typing_files)):
        smoke_wheel.verify_packaged_typing_files()

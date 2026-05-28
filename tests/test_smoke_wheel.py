"""Tests for the installed wheel smoke check."""

from __future__ import annotations

import re
from importlib import machinery, metadata, util
from typing import TYPE_CHECKING

import pytest

from scripts import smoke_wheel

if TYPE_CHECKING:
    from pathlib import Path


def test_smoke_wheel_main_exercises_installed_package_with_stdlib_png() -> None:
    assert smoke_wheel.main(["--allow-editable", "--stdlib-png"]) == 0


def test_smoke_wheel_uses_editable_typing_fallback_only_when_allowed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_files(_distribution: str) -> list[str]:
        return ["oxipng_pybind.pth"]

    package_root = tmp_path / "src" / "oxipng"
    package_root.mkdir(parents=True)
    (package_root / "__init__.pyi").write_text("def optimize() -> None: ...\n", encoding="utf-8")
    (package_root / "py.typed").write_text("", encoding="utf-8")

    def fake_find_spec(_name: str) -> machinery.ModuleSpec:
        spec = machinery.ModuleSpec("oxipng", loader=None, is_package=True)
        spec.submodule_search_locations = [str(package_root)]
        return spec

    monkeypatch.setattr(metadata, "files", fake_files)
    monkeypatch.setattr(util, "find_spec", fake_find_spec)

    missing_typing_files = "wheel is missing oxipng/__init__.pyi, oxipng/py.typed"
    with pytest.raises(RuntimeError, match=re.escape(missing_typing_files)):
        smoke_wheel.verify_packaged_typing_files()

    smoke_wheel.verify_packaged_typing_files(allow_editable=True)

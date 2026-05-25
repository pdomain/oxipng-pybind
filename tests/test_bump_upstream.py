"""Tests for upstream bump helpers."""

from pathlib import Path

import tomlkit

from scripts.bump_upstream import normalize_version, update_cargo_toml, update_pyproject_toml


def test_normalize_version_strips_v_prefix() -> None:
    assert normalize_version("v10.1.1") == "10.1.1"
    assert normalize_version("10.1.1") == "10.1.1"


def test_update_pyproject_toml(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        """
[project]
name = "se-pyoxipng"
version = "10.1.0"
""".lstrip(),
        encoding="utf-8",
    )

    update_pyproject_toml(path, "10.1.1")

    data = tomlkit.parse(path.read_text(encoding="utf-8"))
    assert data["project"]["version"] == "10.1.1"


def test_update_cargo_toml(tmp_path: Path) -> None:
    path = tmp_path / "Cargo.toml"
    path.write_text(
        """
[package]
name = "se-pyoxipng"
version = "10.1.0"

[dependencies]
oxi = { package = "oxipng", version = "=10.1.0", default-features = false, features = ["parallel", "zopfli"] }
""".lstrip(),
        encoding="utf-8",
    )

    update_cargo_toml(path, "10.1.1")

    data = tomlkit.parse(path.read_text(encoding="utf-8"))
    assert data["package"]["version"] == "10.1.1"
    assert data["dependencies"]["oxi"]["version"] == "=10.1.1"

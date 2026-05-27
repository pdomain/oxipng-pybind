"""Tests for release tag validation helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scripts.validate_release_tag import (
    ReleaseTagError,
    read_project_version,
    release_version_from_tag,
    validate_tag_matches_project_version,
)

if TYPE_CHECKING:
    from pathlib import Path


def write_pyproject(tmp_path: Path, version: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        f"""
[project]
name = "oxipng-pybind"
version = "{version}"
""".lstrip(),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("tag", "version"),
    [
        ("v10.1.1", "10.1.1"),
        ("v10.1.1.post1", "10.1.1.post1"),
        ("v0.0.1", "0.0.1"),
    ],
)
def test_release_version_from_tag_accepts_final_release_tags(tag: str, version: str) -> None:
    assert release_version_from_tag(tag) == version


@pytest.mark.parametrize(
    "tag",
    [
        "10.1.1",
        "vtest",
        "v10",
        "v10.1",
        "v10.1.1.dev1",
        "v10.1.1rc1",
        "v10.1.1-alpha",
        "v10.1.1.post",
    ],
)
def test_release_version_from_tag_rejects_non_release_tags(tag: str) -> None:
    with pytest.raises(ReleaseTagError, match="must match"):
        release_version_from_tag(tag)


def test_read_project_version_reads_project_table(tmp_path: Path) -> None:
    assert read_project_version(write_pyproject(tmp_path, "10.1.1")) == "10.1.1"


def test_validate_tag_matches_project_version_accepts_matching_tag(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "10.1.1.post1")

    assert validate_tag_matches_project_version("v10.1.1.post1", pyproject) == "10.1.1.post1"


def test_validate_tag_matches_project_version_rejects_mismatch(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "10.1.1")

    with pytest.raises(ReleaseTagError, match=r"does not match project\.version"):
        validate_tag_matches_project_version("v10.1.2", pyproject)

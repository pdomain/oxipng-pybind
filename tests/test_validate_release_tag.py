"""Tests for release tag validation helpers."""

from __future__ import annotations

import urllib.error
import urllib.request
from email.message import Message
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from scripts.validate_release_tag import (
    ReleaseTagError,
    ensure_pypi_version_absent,
    main,
    pypi_version_exists,
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


def http_error(code: int, message: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://pypi.org/pypi/oxipng-pybind/10.1.1/json",
        code,
        message,
        hdrs=Message(),
        fp=None,
    )


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


def test_ensure_pypi_version_absent_accepts_missing_version() -> None:
    with patch("scripts.validate_release_tag.pypi_version_exists", return_value=False) as exists:
        ensure_pypi_version_absent("oxipng-pybind", "10.1.1", "https://pypi.org")

    exists.assert_called_once_with("oxipng-pybind", "10.1.1", "https://pypi.org")


def test_ensure_pypi_version_absent_rejects_existing_version() -> None:
    with (
        patch("scripts.validate_release_tag.pypi_version_exists", return_value=True),
        pytest.raises(ReleaseTagError, match="already exists"),
    ):
        ensure_pypi_version_absent("oxipng-pybind", "10.1.1", "https://pypi.org")


def test_pypi_version_exists_returns_true_for_200_response_and_builds_url() -> None:
    with patch("scripts.validate_release_tag.urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value = object()

        result = pypi_version_exists("oxipng-pybind", "10.1.1", "https://pypi.org/")

    assert result is True
    urlopen.assert_called_once()
    request = urlopen.call_args.args[0]
    assert isinstance(request, urllib.request.Request)
    assert request.full_url == "https://pypi.org/pypi/oxipng-pybind/10.1.1/json"
    assert request.get_header("User-agent") == "oxipng-pybind-release-check"
    assert urlopen.call_args.kwargs == {"timeout": 20}


def test_pypi_version_exists_returns_false_for_404_response() -> None:
    with patch(
        "scripts.validate_release_tag.urllib.request.urlopen",
        side_effect=http_error(404, "Not Found"),
    ):
        result = pypi_version_exists("oxipng-pybind", "10.1.1", "https://pypi.org")

    assert result is False


def test_pypi_version_exists_raises_for_non_404_response() -> None:
    with (
        patch(
            "scripts.validate_release_tag.urllib.request.urlopen",
            side_effect=http_error(500, "Internal Server Error"),
        ),
        pytest.raises(ReleaseTagError, match="HTTP 500"),
    ):
        pypi_version_exists("oxipng-pybind", "10.1.1", "https://pypi.org")


def test_pypi_version_exists_raises_for_url_error() -> None:
    with (
        patch(
            "scripts.validate_release_tag.urllib.request.urlopen",
            side_effect=urllib.error.URLError("network unavailable"),
        ),
        pytest.raises(ReleaseTagError, match="network unavailable"),
    ):
        pypi_version_exists("oxipng-pybind", "10.1.1", "https://pypi.org")


def test_cli_returns_zero_for_matching_tag_when_external_checks_are_skipped(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "10.1.1")

    result = main(
        [
            "--tag",
            "v10.1.1",
            "--pyproject",
            str(pyproject),
            "--skip-main-check",
            "--skip-pypi-check",
        ]
    )

    assert result == 0


def test_cli_returns_one_for_mismatched_tag(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "10.1.1")

    result = main(
        [
            "--tag",
            "v10.1.2",
            "--pyproject",
            str(pyproject),
            "--skip-main-check",
            "--skip-pypi-check",
        ]
    )

    assert result == 1


def test_cli_returns_one_when_pypi_check_fails(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "10.1.1")

    with patch(
        "scripts.validate_release_tag.ensure_pypi_version_absent",
        side_effect=ReleaseTagError("PyPI check failed"),
    ) as pypi_check:
        result = main(
            [
                "--tag",
                "v10.1.1",
                "--pyproject",
                str(pyproject),
                "--skip-main-check",
            ]
        )

    assert result == 1
    pypi_check.assert_called_once_with("oxipng-pybind", "10.1.1", "https://pypi.org")


def test_cli_runs_main_and_pypi_checks(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "10.1.1")

    with (
        patch("scripts.validate_release_tag.ensure_ref_is_on_main") as main_check,
        patch("scripts.validate_release_tag.ensure_pypi_version_absent") as pypi_check,
    ):
        result = main(["--tag", "v10.1.1", "--pyproject", str(pyproject)])

    assert result == 0
    main_check.assert_called_once_with("v10.1.1", "origin/main")
    pypi_check.assert_called_once_with("oxipng-pybind", "10.1.1", "https://pypi.org")

"""Tests for the GitHub repository settings audit helper."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts import audit_github_settings
from tests.helpers.automation import completed_json

if TYPE_CHECKING:
    import subprocess

    import pytest


def test_audit_github_settings_accepts_expected_settings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payloads: dict[str, object] = {
        "repos/example/oxipng-pybind": {
            "default_branch": "main",
            "allow_auto_merge": True,
            "allow_rebase_merge": True,
            "allow_merge_commit": False,
            "allow_squash_merge": False,
        },
        "repos/example/oxipng-pybind/branches/main/protection": {
            "required_status_checks": {
                "contexts": [
                    "pre-commit checks",
                    "python tests",
                    "rust tests",
                    "dependency audit",
                    "release file checks",
                    "public api py3.10",
                    "public api py3.11",
                    "public api py3.12",
                    "public api py3.13",
                    "public api py3.14",
                ],
                "checks": [],
            }
        },
        "repos/example/oxipng-pybind/actions/secrets": {
            "secrets": [
                {"name": "DEPENDENCY_REFRESH_TOKEN"},
                {"name": "UPSTREAM_BUMP_TOKEN"},
            ]
        },
    }

    def run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return completed_json(payloads[command[-1]])

    assert audit_github_settings.main(["--repo", "example/oxipng-pybind"], run_gh=run) == 0
    output = capsys.readouterr().out
    assert "PASS default branch is main" in output
    assert "PASS required check present: pre-commit checks" in output
    assert "PASS required check present: public api py3.10" in output
    assert "PASS merge commits are disabled" in output
    assert "PASS squash merges are disabled" in output
    assert "PASS required secret available: UPSTREAM_BUMP_TOKEN" in output


def test_audit_github_settings_reports_failed_checks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payloads: dict[str, object] = {
        "repos/example/oxipng-pybind": {
            "default_branch": "develop",
            "allow_auto_merge": False,
            "allow_rebase_merge": False,
            "allow_merge_commit": True,
            "allow_squash_merge": True,
        },
        "repos/example/oxipng-pybind/branches/develop/protection": {
            "required_status_checks": {"contexts": ["lint"], "checks": []}
        },
        "repos/example/oxipng-pybind/actions/secrets": {"secrets": []},
    }

    def run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return completed_json(payloads[command[-1]])

    assert audit_github_settings.main(["--repo", "example/oxipng-pybind"], run_gh=run) == 1
    output = capsys.readouterr().out
    assert "FAIL default branch is develop, expected main" in output
    assert "FAIL repository auto-merge is disabled" in output
    assert "FAIL rebase merge is disabled" in output
    assert "FAIL merge commits are enabled" in output
    assert "FAIL squash merges are enabled" in output
    assert "FAIL required check missing: pre-commit checks" in output
    assert "FAIL required check missing: public api py3.10" in output
    assert "FAIL required secret missing: DEPENDENCY_REFRESH_TOKEN" in output

"""Unit tests for release workflow checks."""

from __future__ import annotations

from scripts.verify_release_checks import check_required_workflows


def test_required_workflows_pass_when_all_successful() -> None:
    """No errors when required source workflows passed for the tag SHA."""
    runs = [
        {"name": "ci", "headSha": "abc", "status": "completed", "conclusion": "success"},
        {"name": "api-matrix", "headSha": "abc", "status": "completed", "conclusion": "success"},
    ]

    errors = check_required_workflows(runs, sha="abc", required=("ci", "api-matrix"))

    assert errors == []


def test_required_workflows_fail_when_missing() -> None:
    """Missing source workflow entries produce a missing-workflow error."""
    runs = [
        {"name": "ci", "headSha": "abc", "status": "completed", "conclusion": "success"},
    ]

    errors = check_required_workflows(runs, sha="abc", required=("ci", "api-matrix"))

    assert errors == ["api-matrix did not complete successfully for abc"]


def test_required_workflows_fail_when_not_successful() -> None:
    """Failed source workflows are treated as missing checks."""
    runs = [
        {"name": "ci", "headSha": "abc", "status": "completed", "conclusion": "failure"},
        {"name": "api-matrix", "headSha": "abc", "status": "completed", "conclusion": "success"},
    ]

    errors = check_required_workflows(runs, sha="abc", required=("ci", "api-matrix"))

    assert errors == ["ci did not complete successfully for abc"]

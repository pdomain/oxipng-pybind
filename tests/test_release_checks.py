"""Unit tests for release workflow checks."""

from __future__ import annotations

from scripts.verify_release_checks import REQUIRED_WORKFLOWS, check_required_workflows

WORKFLOW_IDS = {path: idx + 1 for idx, (_, path, _) in enumerate(REQUIRED_WORKFLOWS)}


def test_required_workflows_pass_when_all_successful() -> None:
    """No errors when required source workflows passed for the tag SHA."""
    runs = [
        {
            "name": "ci",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/ci.yml"],
        },
        {
            "name": "api-matrix",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        },
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == []


def test_required_workflows_fail_when_missing() -> None:
    """Missing source workflow entries produce a missing-workflow error."""
    runs = [
        {
            "name": "ci",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/ci.yml"],
        },
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["api-matrix did not complete successfully for abc"]


def test_required_workflows_fail_when_not_successful() -> None:
    """Failed source workflows are treated as missing checks."""
    runs = [
        {
            "name": "ci",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "failure",
            "event": "push",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/ci.yml"],
        },
        {
            "name": "api-matrix",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        },
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]


def test_required_workflows_fail_for_untrusted_event() -> None:
    """Workflow runs started by non-push events do not satisfy source checks."""
    runs = [
        {
            "name": "ci",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "workflow_dispatch",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/ci.yml"],
        },
        {
            "name": "api-matrix",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "workflow_dispatch",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        },
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == [
        "ci did not complete successfully for abc",
        "api-matrix did not complete successfully for abc",
    ]


def test_required_workflows_fail_for_trusted_workflow_mismatch() -> None:
    """Runs from non-trusted workflow instances do not satisfy source checks."""
    runs = [
        {
            "name": "ci",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "workflowDatabaseId": 999_999,
        },
        {
            "name": "api-matrix",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "workflowDatabaseId": WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        },
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]

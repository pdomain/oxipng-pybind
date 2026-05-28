"""Unit tests for release workflow checks."""

from __future__ import annotations

from scripts.verify_release_checks import REQUIRED_WORKFLOWS, check_required_workflows
from tests.helpers.artifacts import workflow_run

WORKFLOW_IDS = {path: idx + 1 for idx, (_, path, _) in enumerate(REQUIRED_WORKFLOWS)}


def test_required_workflows_pass_when_all_successful() -> None:
    """No errors when required source workflows passed for the tag SHA."""
    runs = [
        workflow_run(workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"]),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
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
        workflow_run(workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"]),
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
        workflow_run(
            conclusion="failure",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"],
        ),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]


def test_required_workflows_fail_for_wrong_head_sha() -> None:
    runs = [
        workflow_run(
            name="ci",
            head_sha="other",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"],
        ),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]


def test_required_workflows_fail_when_status_is_not_completed() -> None:
    runs = [
        workflow_run(
            name="ci",
            status="in_progress",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"],
        ),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
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
        workflow_run(
            event="workflow_dispatch",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"],
        ),
        workflow_run(
            name="api-matrix",
            event="workflow_dispatch",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
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
        workflow_run(workflow_database_id=999_999),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]

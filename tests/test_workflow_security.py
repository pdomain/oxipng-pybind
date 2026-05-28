"""Static checks for GitHub workflow security policy."""

from __future__ import annotations

from tests.helpers.workflows import (
    REVIEWED_ACTION_REFS,
    ROOT,
    Step,
    assert_action_ref_is_reviewed,
    load_workflow,
    parse_action_ref,
    step_by_name,
    step_index,
)

WRITE_TOKEN_WORKFLOWS = (
    ".github/workflows/upstream-bump.yml",
    ".github/workflows/dependency-health.yml",
)


def _reviewed_ref(action: str) -> str:
    return REVIEWED_ACTION_REFS[action]


def assert_release_tag_checkout_uses_ephemeral_credentials(step: Step) -> None:
    assert step["uses"] == f"actions/checkout@{_reviewed_ref('actions/checkout')}"
    assert step["with"] == {
        "fetch-depth": 0,
        "persist-credentials": False,
    }
    assert "token" not in step["with"]
    assert "RELEASE_TAG_TOKEN" not in str(step)


def test_write_token_workflows_pin_create_pull_request_to_sha() -> None:
    """Write-scoped PR creation actions must be pinned to immutable SHAs."""
    for relative in WRITE_TOKEN_WORKFLOWS:
        workflow = load_workflow(relative)
        publish = workflow["jobs"]["publish"]
        steps = publish["steps"]

        assert publish["permissions"] in (
            {
                "contents": "write",
                "pull-requests": "write",
            },
            {
                "contents": "write",
                "issues": "write",
                "pull-requests": "write",
            },
        )
        assert steps[0]["uses"] == f"actions/checkout@{_reviewed_ref('actions/checkout')}"
        assert steps[0]["with"]["persist-credentials"] is False

        create_pr = step_by_name(steps, "Create pull request")
        action, ref = parse_action_ref(create_pr["uses"])
        assert action == "peter-evans/create-pull-request"
        assert ref == _reviewed_ref("peter-evans/create-pull-request")
        assert len(ref) == 40
        assert all(char in "0123456789abcdef" for char in ref)


def test_workflow_actions_are_pinned_to_commit_shas() -> None:
    """Workflow actions use immutable refs except the Rust toolchain selector."""
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        workflow = load_workflow(str(path.relative_to(ROOT)))
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if not isinstance(uses, str) or uses.startswith("dtolnay/rust-toolchain@"):
                    continue
                _, ref = parse_action_ref(uses)
                assert len(ref) == 40, uses
                assert all(char in "0123456789abcdef" for char in ref), uses


def test_release_actions_are_pinned_to_reviewed_shas() -> None:
    """Release workflow actions that build or publish artifacts use immutable refs."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    build_steps = workflow["jobs"]["build"]["steps"]
    sdist_steps = workflow["jobs"]["sdist"]["steps"]
    publish_steps = workflow["jobs"]["publish"]["steps"]

    assert step_by_name(build_steps, "Build wheel")["uses"] == (
        f"PyO3/maturin-action@{_reviewed_ref('PyO3/maturin-action')}"
    )
    assert step_by_name(sdist_steps, "Build sdist")["uses"] == (
        f"PyO3/maturin-action@{_reviewed_ref('PyO3/maturin-action')}"
    )
    assert step_by_name(build_steps, "Upload wheels")["uses"] == (
        f"actions/upload-artifact@{_reviewed_ref('actions/upload-artifact')}"
    )
    assert step_by_name(sdist_steps, "Upload sdist")["uses"] == (
        f"actions/upload-artifact@{_reviewed_ref('actions/upload-artifact')}"
    )
    assert publish_steps[0]["uses"] == f"actions/checkout@{_reviewed_ref('actions/checkout')}"
    assert step_by_name(publish_steps, "Download release artifacts")["uses"] == (
        f"actions/download-artifact@{_reviewed_ref('actions/download-artifact')}"
    )
    assert step_by_name(publish_steps, "Verify release artifact set")["run"] == (
        "python scripts/verify_release_artifacts.py dist/*"
    )
    assert step_index(publish_steps, "Verify release artifact set") < step_index(
        publish_steps, "Publish to PyPI"
    )
    assert step_by_name(publish_steps, "Publish to PyPI")["uses"] == (
        f"pypa/gh-action-pypi-publish@{_reviewed_ref('pypa/gh-action-pypi-publish')}"
    )
    for step in publish_steps:
        uses = step.get("uses")
        if isinstance(uses, str):
            if uses == f"actions/checkout@{_reviewed_ref('actions/checkout')}":
                continue
            _, ref = parse_action_ref(uses)
            assert len(ref) == 40
            assert all(char in "0123456789abcdef" for char in ref)


def test_workflow_actions_use_reviewed_refs() -> None:
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        workflow = load_workflow(str(path.relative_to(ROOT)))
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if isinstance(uses, str):
                    assert_action_ref_is_reviewed(uses)


def test_release_tag_workflow_contains_release_token_to_push_step() -> None:
    """Release tag credentials are scoped to the tag-push step only."""
    workflow = load_workflow(".github/workflows/release-tag.yml")
    steps = workflow["jobs"]["create-release-tag"]["steps"]

    assert not any(step.get("name") == "Check release tag token" for step in steps)
    assert_release_tag_checkout_uses_ephemeral_credentials(steps[0])

    create = step_by_name(steps, "Create and push release tag")
    assert create["env"] == {"RELEASE_TAG_TOKEN": "${{ secrets.RELEASE_TAG_TOKEN }}"}
    assert "x-access-token:${RELEASE_TAG_TOKEN}" in create["run"]
    token_steps = [step for step in steps if "RELEASE_TAG_TOKEN" in str(step)]
    assert token_steps == [create]

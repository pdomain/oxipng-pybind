"""Static checks for GitHub workflow automation policy."""

from __future__ import annotations

from tests.helpers.workflows import (
    REVIEWED_ACTION_REFS,
    ROOT,
    RUST_TOOLCHAIN_VERSION,
    assert_ordered_steps,
    load_workflow,
    step_by_name,
    workflow_trigger,
)

API_TEST_TARGETS = (
    "tests/test_api_surface.py",
    "tests/test_optimize_file_api.py",
    "tests/test_optimize_memory_api.py",
    "tests/test_option_validation.py",
    "tests/test_pyoxipng_compat.py",
    "tests/test_raw_image_api.py",
)
API_TEST_COMMAND = f"uv run --locked --group dev pytest {' '.join(API_TEST_TARGETS)} -v -ra"


def _reviewed_ref(action: str) -> str:
    return REVIEWED_ACTION_REFS[action]


def test_dependabot_version_updates_are_not_configured() -> None:
    """The dependency-health workflow owns scheduled dependency update PRs."""
    assert not (ROOT / ".github/dependabot.yml").exists()
    assert not (ROOT / ".github/dependabot.yaml").exists()


def test_workflows_use_current_rust_toolchain() -> None:
    """GitHub workflows install the reviewed stable Rust toolchain."""
    for relative in (
        ".github/workflows/api-matrix.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/dependency-health.yml",
        ".github/workflows/upstream-bump.yml",
        ".github/workflows/wheels.yml",
    ):
        workflow = load_workflow(relative)
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if isinstance(uses, str) and uses.startswith("dtolnay/rust-toolchain@"):
                    assert uses == f"dtolnay/rust-toolchain@{RUST_TOOLCHAIN_VERSION}"


def test_upstream_bump_auto_merge_is_gated_by_ci_and_wheels() -> None:
    """Native dependency bump PRs auto-merge only after required automation gates."""
    workflow = load_workflow(".github/workflows/upstream-bump.yml")
    prepare = workflow["jobs"]["prepare"]
    publish = workflow["jobs"]["publish"]
    prepare_steps = prepare["steps"]
    publish_steps = publish["steps"]

    assert workflow["permissions"] == {"contents": "read"}
    assert publish["needs"] == "prepare"
    assert prepare["outputs"]["upstream-crate-available"] == (
        "${{ steps.bump.outputs.upstream-crate-available }}"
    )
    assert publish["permissions"] == {
        "contents": "write",
        "issues": "write",
        "pull-requests": "write",
    }

    assert_ordered_steps(
        prepare_steps,
        [
            "Sync dependencies",
            "Bump upstream",
            "Generate third-party notices",
            "Scan upstream surface",
            "Run CI before opening PR",
            "Upload bump workspace",
        ],
    )
    assert step_by_name(prepare_steps, "Sync dependencies")["run"] == "uv sync --locked --group dev"
    assert step_by_name(prepare_steps, "Upload bump workspace")["uses"] == (
        f"actions/upload-artifact@{_reviewed_ref('actions/upload-artifact')}"
    )
    assert step_by_name(prepare_steps, "Bump upstream")["run"] == (
        "uv run --locked --group dev python scripts/bump_upstream.py"
    )
    assert step_by_name(prepare_steps, "Generate third-party notices")["run"] == (
        "make third-party-notices"
    )
    for gated_step in (
        "Fetch upstream source",
        "Prepare API surface manifest",
        "Scan upstream surface",
    ):
        assert step_by_name(prepare_steps, gated_step)["if"] == (
            "steps.bump.outputs.upstream-crate-available != 'false'"
        )
    assert step_by_name(prepare_steps, "Scan upstream surface")["run"] == (
        "uv run --locked --group dev python scripts/scan_upstream_surface.py --update-docs"
    )
    assert step_by_name(prepare_steps, "Run CI before opening PR")["if"] == (
        "steps.changes.outputs.changed == 'true'"
    )
    assert step_by_name(prepare_steps, "Run CI before opening PR")["run"] == "make ci"

    assert_ordered_steps(
        publish_steps,
        ["Create pull request", "Wait for wheel workflow", "Enable auto-merge"],
    )
    assert publish_steps[1]["uses"] == (
        f"actions/download-artifact@{_reviewed_ref('actions/download-artifact')}"
    )
    wait = step_by_name(publish_steps, "Wait for wheel workflow")
    assert 'contains(fromJSON(\'["created", "updated"]\')' in wait["if"]
    assert "gh run list --workflow wheels.yml" in wait["run"]

    auto_merge = step_by_name(publish_steps, "Enable auto-merge")
    assert auto_merge["env"] == {"GH_TOKEN": "${{ secrets.UPSTREAM_BUMP_TOKEN }}"}
    assert 'contains(fromJSON(\'["created", "updated"]\')' in auto_merge["if"]
    assert "gh pr merge" in auto_merge["run"]
    assert "--auto --rebase --delete-branch" in auto_merge["run"]
    assert "--merge" not in auto_merge["run"]
    assert "--squash" not in auto_merge["run"]


def test_upstream_bump_docs_describe_ci_gated_auto_merge() -> None:
    """Process docs must document automation-gated auto-merge."""
    text = (ROOT / "docs/process/upstream-bumps.md").read_text(encoding="utf-8").lower()

    assert "auto-merge" in text
    assert "the workflow waits for wheel checks before enabling auto-merge" in text
    assert "human review is required" not in text


def test_dependency_refresh_auto_merge_is_ci_gated() -> None:
    """Dependency refresh PRs auto-merge through branch protection after audits and CI."""
    workflow = load_workflow(".github/workflows/dependency-health.yml")
    prepare = workflow["jobs"]["prepare"]
    publish = workflow["jobs"]["publish"]
    prepare_steps = prepare["steps"]
    publish_steps = publish["steps"]

    assert workflow["permissions"] == {"contents": "read"}
    assert prepare["outputs"] == {
        "changed": "${{ steps.changes.outputs.changed }}",
        "changed-paths": "${{ steps.changes.outputs.paths }}",
        "release-label": "${{ steps.classification.outputs.label }}",
        "release-needed": "${{ steps.classification.outputs.release-needed }}",
        "release-reason": "${{ steps.classification.outputs.reason }}",
    }
    assert publish["needs"] == "prepare"
    assert publish["if"] == "needs.prepare.outputs.changed == 'true'"
    assert publish["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
    }

    assert_ordered_steps(
        prepare_steps,
        [
            "Refresh lockfiles",
            "Sync refreshed dependencies",
            "Refresh pre-commit hooks",
            "Refresh GitHub Actions",
            "Apply lint and generated-file fixes",
            "Generate third-party notices",
            "Run dependency audits",
            "Run CI",
            "Check for changes",
            "Classify dependency refresh",
            "Upload dependency refresh workspace",
        ],
    )
    assert step_by_name(prepare_steps, "Refresh lockfiles")["run"] == (
        "uv lock --upgrade\ncargo update\n"
    )
    assert step_by_name(prepare_steps, "Sync refreshed dependencies")["run"] == (
        "uv sync --locked --group dev"
    )
    assert step_by_name(prepare_steps, "Refresh pre-commit hooks")["run"] == (
        "uv run --locked --group dev pre-commit autoupdate"
    )
    assert step_by_name(prepare_steps, "Refresh GitHub Actions")["run"] == (
        "uv run --locked --group dev python scripts/update_github_actions.py"
    )
    assert step_by_name(prepare_steps, "Apply lint and generated-file fixes")["run"] == (
        "make lint-fix"
    )
    assert step_by_name(prepare_steps, "Generate third-party notices")["run"] == (
        "make third-party-notices"
    )
    assert step_by_name(prepare_steps, "Run dependency audits")["run"] == "make dependency-audit"
    assert step_by_name(prepare_steps, "Run CI")["run"] == "make ci"

    changes = step_by_name(prepare_steps, "Check for changes")
    assert changes["id"] == "changes"
    assert "git diff --name-only" in changes["run"]
    assert "git ls-files --others --exclude-standard" in changes["run"]
    assert "paths<<EOF" in changes["run"]

    classify = step_by_name(prepare_steps, "Classify dependency refresh")
    assert classify["id"] == "classification"
    assert classify["if"] == "steps.changes.outputs.changed == 'true'"
    assert classify["run"] == (
        "uv run --locked --group dev python "
        "scripts/classify_dependency_refresh.py --base-ref origin/main"
    )

    artifact = step_by_name(prepare_steps, "Upload dependency refresh workspace")
    assert artifact["if"] == "steps.changes.outputs.changed == 'true'"
    assert artifact["uses"] == f"actions/upload-artifact@{_reviewed_ref('actions/upload-artifact')}"
    assert artifact["with"] == {
        "name": "dependency-refresh",
        "include-hidden-files": True,
        "path": "${{ steps.changes.outputs.paths }}",
    }

    assert_ordered_steps(publish_steps, ["Create pull request", "Enable auto-merge"])
    assert publish_steps[1]["uses"] == (
        f"actions/download-artifact@{_reviewed_ref('actions/download-artifact')}"
    )
    create_pr = step_by_name(publish_steps, "Create pull request")
    assert create_pr["with"]["add-paths"] == "${{ needs.prepare.outputs.changed-paths }}"
    assert "scripts/update_github_actions.py" in create_pr["with"]["body"]
    assert "Release classification:" in create_pr["with"]["body"]
    assert "${{ needs.prepare.outputs.release-label }}" in create_pr["with"]["body"]
    assert create_pr["with"]["labels"] == (
        "dependencies, automated, ${{ needs.prepare.outputs.release-label }}"
    )

    auto_merge = step_by_name(publish_steps, "Enable auto-merge")
    assert auto_merge["env"] == {"GH_TOKEN": "${{ secrets.DEPENDENCY_REFRESH_TOKEN }}"}
    assert "needs.prepare.outputs.release-needed == 'false'" in auto_merge["if"]
    assert 'contains(fromJSON(\'["created", "updated"]\')' in auto_merge["if"]
    assert "gh pr merge" in auto_merge["run"]
    assert "--auto --rebase --delete-branch" in auto_merge["run"]
    assert "--merge" not in auto_merge["run"]
    assert "--squash" not in auto_merge["run"]


def test_dependency_refresh_docs_describe_ci_gated_auto_merge() -> None:
    """Dependency health docs must document automation-gated auto-merge."""
    text = (ROOT / "docs/process/dependency-health.md").read_text(encoding="utf-8").lower()

    assert "auto-merge" in text
    assert "required checks pass" in text
    assert "classify_dependency_refresh.py --base-ref origin/main" in text
    assert "review lockfile diffs before merge" not in text


def test_api_matrix_uses_locked_dev_dependencies() -> None:
    """API matrix jobs consume locked dependencies and matching ABI lanes."""
    workflow = load_workflow(".github/workflows/api-matrix.yml")
    job = workflow["jobs"]["public-api"]
    steps = job["steps"]

    assert workflow["permissions"] == {"contents": "read"}
    assert job["env"] == {"UV_PYTHON": "${{ matrix.python-version }}"}
    assert job["strategy"]["matrix"]["include"] == [
        {"python-version": "3.10", "cargo-features": "abi3-py310"},
        {"python-version": "3.11", "cargo-features": "abi3-py311"},
        {"python-version": "3.12", "cargo-features": "abi3-py311"},
        {"python-version": "3.13", "cargo-features": "abi3-py311"},
        {"python-version": "3.14", "cargo-features": "abi3-py311"},
    ]
    assert step_by_name(steps, "Sync dependencies")["run"] == "uv sync --locked --group dev"
    assert step_by_name(steps, "Build editable extension")["run"] == (
        "uv run --locked --group dev maturin develop --no-default-features "
        "--features ${{ matrix.cargo-features }}"
    )
    assert step_by_name(steps, "Run public API tests")["run"] == API_TEST_COMMAND


def test_ci_workflow_splits_independent_checks() -> None:
    """Remote CI runs independent source checks as parallel jobs with locked dependencies."""
    workflow = load_workflow(".github/workflows/ci.yml")
    jobs = workflow["jobs"]

    assert set(jobs) == {
        "pre-commit",
        "python-tests",
        "rust-tests",
        "dependency-audit",
        "release-files",
    }
    for name in ("pre-commit", "python-tests", "dependency-audit", "release-files"):
        steps = jobs[name]["steps"]
        assert step_by_name(steps, "Sync dependencies")["run"] == "uv sync --locked --group dev"

    assert jobs["pre-commit"]["steps"][-1]["run"] == "make pre-commit-check"
    assert jobs["python-tests"]["steps"][-1]["run"] == "make test-py"
    assert jobs["rust-tests"]["steps"][-1]["run"] == "make test-rust"
    assert jobs["dependency-audit"]["steps"][-1]["run"] == "make dependency-audit"
    assert jobs["release-files"]["steps"][-2]["run"] == "make third-party-notices-check"
    assert jobs["release-files"]["steps"][-1]["run"] == "make wheel"


def test_ci_rust_tests_install_rust_before_rust_tests() -> None:
    """The rust-tests job installs Rust before invoking the Rust test target."""
    workflow = load_workflow(".github/workflows/ci.yml")
    steps = workflow["jobs"]["rust-tests"]["steps"]
    rust_install_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("uses") == f"dtolnay/rust-toolchain@{RUST_TOOLCHAIN_VERSION}"
    )
    rust_test_index = next(
        index for index, step in enumerate(steps) if step.get("run") == "make test-rust"
    )

    assert rust_install_index < rust_test_index


def test_failed_check_retry_is_single_attempt_and_delayed() -> None:
    """Transient CI failures get one delayed failed-job rerun without retry loops."""
    workflow = load_workflow(".github/workflows/retry-failed-checks.yml")
    retry = workflow["jobs"]["retry"]
    steps = retry["steps"]

    assert workflow_trigger(workflow)["workflow_run"] == {
        "workflows": ["ci", "api-matrix", "wheels"],
        "types": ["completed"],
    }
    assert workflow["permissions"] == {"actions": "write", "contents": "read"}
    assert retry["if"] == (
        "github.event.workflow_run.conclusion == 'failure' && "
        "github.event.workflow_run.run_attempt == 1 && "
        'contains(fromJSON(\'["automation/bump-oxipng", "automation/dependency-refresh"]\'), '
        "github.event.workflow_run.head_branch)"
    )
    assert [step["name"] for step in steps] == ["Wait before retry", "Rerun failed jobs"]
    assert step_by_name(steps, "Wait before retry")["run"] == "sleep 600"

    rerun = step_by_name(steps, "Rerun failed jobs")
    assert rerun["env"] == {
        "GH_TOKEN": "${{ github.token }}",
        "RUN_ID": "${{ github.event.workflow_run.id }}",
        "REPOSITORY": "${{ github.event.repository.full_name }}",
    }
    assert rerun["run"] == 'gh run rerun "$RUN_ID" --repo "$REPOSITORY" --failed\n'

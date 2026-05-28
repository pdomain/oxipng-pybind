"""Static checks for GitHub workflow security policy."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
Workflow = dict[Any, Any]
Step = dict[str, Any]
FULL_SHA = "e83996d129638aa358a18fbd1dfb82f0b0fb5d3b"
PYPI_PUBLISH_SHA = "cef221092ed1bacb1cc03d23a2d87d1d172e277b"
CHECKOUT_SHA = "de0fac2e4500dabe0009e67214ff5f5447ce83dd"
SETUP_PYTHON_SHA = "a309ff8b426b58ec0e2a45f0f869d46889d02405"
UPLOAD_ARTIFACT_SHA = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
DOWNLOAD_ARTIFACT_SHA = "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
CREATE_PULL_REQUEST_SHA = "5f6978faf089d4d20b00c7766989d076bb2fc7f1"
RUST_TOOLCHAIN_VERSION = "1.95.0"
WRITE_TOKEN_WORKFLOWS = (
    ".github/workflows/upstream-bump.yml",
    ".github/workflows/dependency-health.yml",
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


def load_workflow(relative: str) -> Workflow:
    """Load a workflow as parsed YAML."""
    data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast("Workflow", data)


def step_by_name(steps: list[Step], name: str) -> Step:
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1
    return matches[0]


def step_index(steps: list[Step], name: str) -> int:
    return steps.index(step_by_name(steps, name))


def assert_ordered_steps(steps: list[Step], names: list[str]) -> None:
    indexes = [step_index(steps, name) for name in names]
    assert indexes == sorted(indexes)


def assert_release_tag_checkout_uses_ephemeral_credentials(step: Step) -> None:
    assert step["uses"] == f"actions/checkout@{CHECKOUT_SHA}"
    assert step["with"] == {
        "fetch-depth": 0,
        "persist-credentials": False,
    }
    assert "token" not in step["with"]
    assert "RELEASE_TAG_TOKEN" not in str(step)


def assert_release_tag_wait_step(step: Step, workflow: str) -> None:
    assert step["if"] == "steps.eligibility.outputs.eligible == 'true'"
    assert step["env"] == {"GH_TOKEN": "${{ github.token }}"}
    assert f"gh run list --workflow {workflow}" in step["run"]
    assert '--commit "$sha"' in step["run"]
    assert '"completed success") exit 0' in step["run"]


def workflow_trigger(workflow: Workflow) -> Workflow:
    trigger = workflow.get("on", workflow[True])
    assert isinstance(trigger, dict)
    return cast("Workflow", trigger)


def test_dependabot_version_updates_are_not_configured() -> None:
    """The dependency-health workflow owns scheduled dependency update PRs."""
    assert not (ROOT / ".github/dependabot.yml").exists()
    assert not (ROOT / ".github/dependabot.yaml").exists()


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
        assert steps[0]["uses"] == f"actions/checkout@{CHECKOUT_SHA}"
        assert steps[0]["with"]["persist-credentials"] is False

        create_pr = step_by_name(steps, "Create pull request")
        action, ref = create_pr["uses"].rsplit("@", 1)
        assert action == "peter-evans/create-pull-request"
        assert ref == CREATE_PULL_REQUEST_SHA
        assert len(ref) == 40
        assert all(char in "0123456789abcdef" for char in ref)


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


def test_workflow_actions_are_pinned_to_commit_shas() -> None:
    """Workflow actions use immutable refs except the Rust toolchain selector."""
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        workflow = load_workflow(str(path.relative_to(ROOT)))
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if not isinstance(uses, str) or uses.startswith("dtolnay/rust-toolchain@"):
                    continue
                _, ref = uses.rsplit("@", 1)
                assert len(ref) == 40, uses
                assert all(char in "0123456789abcdef" for char in ref), uses


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
        f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}"
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
    assert publish_steps[1]["uses"] == f"actions/download-artifact@{DOWNLOAD_ARTIFACT_SHA}"
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


def test_release_docs_describe_tag_gates_and_automation() -> None:
    """Release docs must describe TestPyPI rehearsal, PyPI gates, and tag automation."""
    release = (ROOT / "docs/process/release-artifacts.md").read_text(encoding="utf-8")
    upstream = (ROOT / "docs/process/upstream-bumps.md").read_text(encoding="utf-8")
    release_lower = release.lower()
    upstream_lower = upstream.lower()

    assert "workflow_dispatch" in release
    assert "testpypi" in release_lower
    assert ".devnnn" in release_lower
    assert "tag-driven" in release_lower
    assert "pypi" in release_lower
    assert re.search(r"already\s+present\s+on\s+pypi", release_lower)
    for accepted_tag in ("v10.1.1", "v10.1.1.post1"):
        assert accepted_tag in release
    for rejected_tag in ("vtest", "v10.1", "v10.1.1.dev1", "v10.1.1rc1"):
        assert rejected_tag in release
    for trusted_publisher_value in (
        "oxipng-pybind",
        "pdomain",
        "wheels.yml",
        "pypi",
        "testpypi",
    ):
        assert trusted_publisher_value in release
    assert "trusted publisher" in release_lower
    assert "environment: `pypi`" in release_lower
    assert "environment: `testpypi`" in release_lower

    assert "release-tag.yml" in upstream
    assert "workflow_run" in upstream
    assert "ci" in upstream_lower
    assert "main" in upstream_lower
    assert "project.version" in upstream
    assert "ci.yml" in upstream
    assert "api-matrix.yml" in upstream
    assert "still matches" in upstream_lower
    assert re.search(r"no\s+matching\s+`?git`?\s+tag\s+exists", upstream_lower)
    assert "absent from pypi" in upstream_lower
    assert "release_tag_token" in upstream_lower
    assert "github_token" in upstream_lower
    assert "pat" in upstream_lower
    assert "github app" in upstream_lower


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
    assert artifact["uses"] == f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}"
    assert artifact["with"] == {
        "name": "dependency-refresh",
        "include-hidden-files": True,
        "path": "${{ steps.changes.outputs.paths }}",
    }

    assert_ordered_steps(publish_steps, ["Create pull request", "Enable auto-merge"])
    assert publish_steps[1]["uses"] == f"actions/download-artifact@{DOWNLOAD_ARTIFACT_SHA}"
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


def test_wheel_tag_checker_uses_only_stdlib_dependencies() -> None:
    """Wheel workflow runs the tag checker before installing project dependencies."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    script = (ROOT / "scripts/check_wheel_tags.py").read_text(encoding="utf-8")
    steps = workflow["jobs"]["build"]["steps"]

    assert step_index(steps, "Check wheel tags") < step_index(steps, "Smoke wheel")
    assert "python scripts/check_wheel_tags.py" in step_by_name(steps, "Check wheel tags")["run"]
    assert "import tomlkit" not in script
    assert "from packaging" not in script
    assert "import packaging" not in script


def test_wheel_smoke_installs_local_wheel_with_pinned_test_dependency() -> None:
    """Wheel smoke installs the built wheel with lane-specific test dependencies."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    build = workflow["jobs"]["build"]
    steps = build["steps"]

    assert workflow["permissions"] == {"contents": "read"}
    assert build["strategy"]["fail-fast"] is False
    assert steps[0]["uses"] == f"actions/checkout@{CHECKOUT_SHA}"
    assert steps[1]["uses"] == f"actions/setup-python@{SETUP_PYTHON_SHA}"
    assert steps[2]["uses"] == f"dtolnay/rust-toolchain@{RUST_TOOLCHAIN_VERSION}"
    assert step_index(steps, "Set TestPyPI version") < step_index(steps, "Build wheel")
    assert step_by_name(steps, "Build wheel")["uses"] == f"PyO3/maturin-action@{FULL_SHA}"
    assert step_by_name(steps, "Build wheel")["with"]["args"] == (
        "--release --locked --out dist --interpreter python${{ matrix.python }} "
        "--no-default-features --features ${{ matrix.cargo-features }}"
    )
    assert {entry["expected-python"] for entry in build["strategy"]["matrix"]["include"]} == {
        "cp310",
        "cp311",
    }
    assert {entry["cargo-features"] for entry in build["strategy"]["matrix"]["include"]} == {
        "abi3-py310",
        "abi3-py311",
    }
    py310_entries = [
        entry
        for entry in build["strategy"]["matrix"]["include"]
        if entry["expected-python"] == "cp310"
    ]
    py311_entries = [
        entry
        for entry in build["strategy"]["matrix"]["include"]
        if entry["expected-python"] == "cp311"
    ]
    assert all(entry["smoke-extra"] == "" for entry in py310_entries)
    assert all(entry["smoke-args"] == "--stdlib-png" for entry in py310_entries)
    assert all(entry["smoke-extra"] == "pillow==12.2.0" for entry in py311_entries)
    assert all(entry["smoke-args"] == "" for entry in py311_entries)

    smoke = step_by_name(steps, "Smoke wheel")
    assert smoke["if"] == "matrix.smoke"
    assert '"$smoke_python" -m pip install dist/*.whl ${{ matrix.smoke-extra }}' in smoke["run"]
    assert '"$smoke_python" scripts/smoke_wheel.py ${{ matrix.smoke-args }}' in smoke["run"]
    assert "dist/*.whl pillow" not in smoke["run"]
    assert step_index(steps, "Smoke wheel") < step_index(steps, "Upload wheels")


def test_release_actions_are_pinned_to_reviewed_shas() -> None:
    """Release workflow actions that build or publish artifacts use immutable refs."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    build_steps = workflow["jobs"]["build"]["steps"]
    sdist_steps = workflow["jobs"]["sdist"]["steps"]
    publish_steps = workflow["jobs"]["publish"]["steps"]

    assert step_by_name(build_steps, "Build wheel")["uses"] == f"PyO3/maturin-action@{FULL_SHA}"
    assert step_by_name(sdist_steps, "Build sdist")["uses"] == f"PyO3/maturin-action@{FULL_SHA}"
    assert step_by_name(build_steps, "Upload wheels")["uses"] == (
        f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}"
    )
    assert step_by_name(sdist_steps, "Upload sdist")["uses"] == (
        f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}"
    )
    assert publish_steps[0]["uses"] == f"actions/checkout@{CHECKOUT_SHA}"
    assert step_by_name(publish_steps, "Download release artifacts")["uses"] == (
        f"actions/download-artifact@{DOWNLOAD_ARTIFACT_SHA}"
    )
    assert step_by_name(publish_steps, "Verify release artifact set")["run"] == (
        "python scripts/verify_release_artifacts.py dist/*"
    )
    assert step_index(publish_steps, "Verify release artifact set") < step_index(
        publish_steps, "Publish to PyPI"
    )
    assert step_by_name(publish_steps, "Publish to PyPI")["uses"] == (
        f"pypa/gh-action-pypi-publish@{PYPI_PUBLISH_SHA}"
    )
    for step in publish_steps:
        uses = step.get("uses")
        if isinstance(uses, str):
            if uses == f"actions/checkout@{CHECKOUT_SHA}":
                continue
            _, ref = uses.rsplit("@", 1)
            assert len(ref) == 40
            assert all(char in "0123456789abcdef" for char in ref)


def test_wheel_workflow_can_publish_to_testpypi_manually() -> None:
    """Manual wheel runs can publish verified artifacts to TestPyPI only when requested."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    dispatch = workflow_trigger(workflow)["workflow_dispatch"]
    build_steps = workflow["jobs"]["build"]["steps"]
    sdist_steps = workflow["jobs"]["sdist"]["steps"]
    publish = workflow["jobs"]["publish"]
    testpypi = workflow["jobs"]["publish-testpypi"]
    steps = testpypi["steps"]
    version_step = step_by_name(build_steps, "Set TestPyPI version")

    assert dispatch["inputs"]["publish-target"] == {
        "description": "Optional publish target for verified artifacts",
        "type": "choice",
        "required": True,
        "default": "none",
        "options": ["none", "testpypi"],
    }
    assert publish["if"] == (
        "github.event_name == 'push' && needs.validate-release-tag.outputs.release-version != ''"
    )
    assert testpypi["if"] == (
        "github.event_name == 'workflow_dispatch' && inputs.publish-target == 'testpypi'"
    )
    assert version_step["if"] == (
        "github.event_name == 'workflow_dispatch' && inputs.publish-target == 'testpypi'"
    )
    assert "GITHUB_RUN_NUMBER" in version_step["run"]
    assert "GITHUB_RUN_ATTEMPT" in version_step["run"]
    assert 'dev_number = int(f"{run_number}{run_attempt:02d}")' in version_step["run"]
    assert ".dev{dev_number}" in version_step["run"]
    assert step_index(build_steps, "Set TestPyPI version") < step_index(build_steps, "Build wheel")
    assert step_index(sdist_steps, "Set TestPyPI version") < step_index(sdist_steps, "Build sdist")
    assert testpypi["environment"] == "testpypi"
    assert testpypi["permissions"] == {"id-token": "write", "contents": "read"}
    assert steps[0]["uses"] == f"actions/checkout@{CHECKOUT_SHA}"
    assert step_by_name(steps, "Download release artifacts")["uses"] == (
        f"actions/download-artifact@{DOWNLOAD_ARTIFACT_SHA}"
    )
    assert step_by_name(steps, "Verify release artifact set")["run"] == (
        "python scripts/verify_release_artifacts.py dist/*"
    )
    assert step_index(steps, "Verify release artifact set") < step_index(
        steps, "Publish to TestPyPI"
    )
    publish_step = step_by_name(steps, "Publish to TestPyPI")
    assert publish_step["uses"] == f"pypa/gh-action-pypi-publish@{PYPI_PUBLISH_SHA}"
    assert publish_step["with"] == {
        "packages-dir": "dist",
        "repository-url": "https://test.pypi.org/legacy/",
    }


def test_pypi_publish_requires_strict_release_tag_validation() -> None:
    """Real PyPI publish is gated by strict tag validation and the pypi environment."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    jobs = workflow["jobs"]
    validate = jobs["validate-release-tag"]
    publish = jobs["publish"]
    validate_steps = validate["steps"]

    assert list(jobs).index("validate-release-tag") < list(jobs).index("publish")
    assert validate["name"] == "validate release tag"
    assert validate["runs-on"] == "ubuntu-latest"
    assert validate["if"] == (
        "github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')"
    )
    assert validate["permissions"] == {"contents": "read"}
    assert validate["outputs"] == {
        "release-version": "${{ steps.validate.outputs.release-version }}"
    }
    checkout = validate_steps[0]
    assert checkout["uses"] == f"actions/checkout@{CHECKOUT_SHA}"
    assert checkout["with"]["fetch-depth"] == 0

    validate_step = step_by_name(validate_steps, "Validate release tag")
    assert validate_step["id"] == "validate"
    assert "python scripts/validate_release_tag.py" in validate_step["run"]
    assert '--tag "$GITHUB_REF_NAME"' in validate_step["run"]
    assert "release-version=" in validate_step["run"]
    assert '>> "$GITHUB_OUTPUT"' in validate_step["run"]

    assert publish["needs"] == ["build", "sdist", "validate-release-tag"]
    assert publish["if"] == (
        "github.event_name == 'push' && needs.validate-release-tag.outputs.release-version != ''"
    )
    assert publish["environment"] == "pypi"
    assert publish["permissions"] == {"id-token": "write", "contents": "read"}

    paths = workflow_trigger(workflow)["pull_request"]["paths"]
    assert "scripts/validate_release_tag.py" in paths


def test_wheel_workflow_waits_on_tag_commit_checks() -> None:
    """Release checks are looked up on the commit behind a tag."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    wait = workflow["jobs"]["wait-for-release-checks"]
    run = step_by_name(wait["steps"], "Wait for required checks on tag commit")["run"]

    assert 'sha="${GITHUB_SHA}"' in run
    assert "refs/tags/${GITHUB_REF_NAME}^{}" in run
    assert 'sha="$peeled_sha"' in run
    assert 'gh run list --repo "${{ github.repository }}"' in run
    assert '--commit "$sha"' in run


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


def test_makefile_has_local_api_matrix_target() -> None:
    """Local API matrix mirrors the supported Python and ABI feature lanes."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert (
        "api-matrix: ## Run focused public API tests on all supported Python versions" in makefile
    )
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert version in makefile
    assert "abi3-py310" in makefile
    assert "abi3-py311" in makefile
    assert "UV_PROJECT_ENV=.venv-api-{}" in makefile
    assert "uv sync --locked --group dev" in makefile
    assert API_TEST_COMMAND in makefile


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


def test_release_tag_workflow_creates_tags_only_after_main_checks() -> None:
    """Automated release tags are created only for eligible upstream bump commits."""
    workflow = load_workflow(".github/workflows/release-tag.yml")
    trigger = workflow_trigger(workflow)
    job = workflow["jobs"]["create-release-tag"]
    steps = job["steps"]

    assert trigger["workflow_run"] == {
        "workflows": ["ci"],
        "types": ["completed"],
        "branches": ["main"],
    }
    assert "workflow_dispatch" in trigger
    assert workflow["permissions"] == {"contents": "read", "actions": "read"}
    assert job["if"] == (
        "github.event_name == 'workflow_dispatch' || "
        "github.event.workflow_run.conclusion == 'success'"
    )
    assert job["permissions"] == {"contents": "write", "actions": "read"}

    assert not any(step.get("name") == "Check release tag token" for step in steps)
    assert_release_tag_checkout_uses_ephemeral_credentials(steps[0])

    eligibility = step_by_name(steps, "Check automated release eligibility")
    assert "git fetch --quiet origin main --tags" in eligibility["run"]
    assert "git checkout --quiet origin/main" in eligibility["run"]
    assert 'main_sha="$(git rev-parse HEAD)"' in eligibility["run"]
    assert "${{ github.event.workflow_run.head_sha }}" in eligibility["run"]
    assert (
        'if [ "${{ github.event_name }}" = "workflow_run" ] &&\n'
        '  [ "$main_sha" != "${{ github.event.workflow_run.head_sha }}" ]; then'
    ) in eligibility["run"]
    assert 'echo "eligible=false" >> "$GITHUB_OUTPUT"' in eligibility["run"]
    assert 'if [ "$subject" != "chore: bump upstream oxipng" ]; then' in eligibility["run"]
    assert "git show HEAD^:pyproject.toml" in eligibility["run"]
    assert 'if [ "$before_version" = "$version" ]; then' in eligibility["run"]
    assert (
        'python scripts/validate_release_tag.py --tag "$tag" --skip-main-check --skip-pypi-check'
    ) in eligibility["run"]
    assert 'git rev-parse "$tag"' in eligibility["run"]
    assert 'echo "eligible=true" >> "$GITHUB_OUTPUT"' in eligibility["run"]
    assert 'echo "version=$version" >> "$GITHUB_OUTPUT"' in eligibility["run"]
    assert 'echo "tag=$tag" >> "$GITHUB_OUTPUT"' in eligibility["run"]

    assert_release_tag_wait_step(step_by_name(steps, "Wait for CI on main commit"), "ci.yml")
    assert_release_tag_wait_step(
        step_by_name(steps, "Wait for API matrix on main commit"),
        "api-matrix.yml",
    )

    pypi = step_by_name(steps, "Check PyPI version does not exist")
    assert "python scripts/validate_release_tag.py" in pypi["run"]
    assert '--pypi-url "https://pypi.org"' in pypi["run"]
    assert "oxipng-pybind" in pypi["run"]

    create = step_by_name(steps, "Create and push release tag")
    assert create["env"] == {"RELEASE_TAG_TOKEN": "${{ secrets.RELEASE_TAG_TOKEN }}"}
    assert "git tag -a" in create["run"]
    assert "x-access-token:${RELEASE_TAG_TOKEN}" in create["run"]
    assert "git push" in create["run"]
    token_steps = [step for step in steps if "RELEASE_TAG_TOKEN" in str(step)]
    assert token_steps == [create]
    assert_ordered_steps(
        steps,
        [
            "Wait for CI on main commit",
            "Wait for API matrix on main commit",
            "Create and push release tag",
        ],
    )

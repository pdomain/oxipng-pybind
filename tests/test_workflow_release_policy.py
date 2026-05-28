"""Static checks for GitHub release workflow policy."""

from __future__ import annotations

import re

from tests.helpers.workflows import (
    REVIEWED_ACTION_REFS,
    ROOT,
    RUST_TOOLCHAIN_VERSION,
    Step,
    assert_ordered_steps,
    load_workflow,
    step_by_name,
    step_index,
    workflow_trigger,
)


def _reviewed_ref(action: str) -> str:
    return REVIEWED_ACTION_REFS[action]


def assert_release_tag_wait_step(step: Step, workflow: str) -> None:
    assert step["if"] == "steps.eligibility.outputs.eligible == 'true'"
    assert step["env"] == {"GH_TOKEN": "${{ github.token }}"}
    assert f"gh run list --workflow {workflow}" in step["run"]
    assert '--commit "$sha"' in step["run"]
    assert '"completed success") exit 0' in step["run"]


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
    assert steps[0]["uses"] == f"actions/checkout@{_reviewed_ref('actions/checkout')}"
    assert steps[1]["uses"] == f"actions/setup-python@{_reviewed_ref('actions/setup-python')}"
    assert steps[2]["uses"] == f"dtolnay/rust-toolchain@{RUST_TOOLCHAIN_VERSION}"
    assert step_index(steps, "Set TestPyPI version") < step_index(steps, "Build wheel")
    assert step_by_name(steps, "Build wheel")["uses"] == (
        f"PyO3/maturin-action@{_reviewed_ref('PyO3/maturin-action')}"
    )
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
    assert steps[0]["uses"] == f"actions/checkout@{_reviewed_ref('actions/checkout')}"
    assert step_by_name(steps, "Download release artifacts")["uses"] == (
        f"actions/download-artifact@{_reviewed_ref('actions/download-artifact')}"
    )
    assert step_by_name(steps, "Verify release artifact set")["run"] == (
        "python scripts/verify_release_artifacts.py dist/*"
    )
    assert step_index(steps, "Verify release artifact set") < step_index(
        steps, "Publish to TestPyPI"
    )
    publish_step = step_by_name(steps, "Publish to TestPyPI")
    assert publish_step["uses"] == (
        f"pypa/gh-action-pypi-publish@{_reviewed_ref('pypa/gh-action-pypi-publish')}"
    )
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
    assert checkout["uses"] == f"actions/checkout@{_reviewed_ref('actions/checkout')}"
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
    assert "git tag -a" in create["run"]
    assert "git push" in create["run"]
    assert_ordered_steps(
        steps,
        [
            "Wait for CI on main commit",
            "Wait for API matrix on main commit",
            "Create and push release tag",
        ],
    )


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

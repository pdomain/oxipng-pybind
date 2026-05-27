# Release Tag Gates And Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a gated release process where strict version tags publish to PyPI, TestPyPI remains manual, and trusted automation can create release tags after an upstream bump lands on `main`.

**Architecture:** Keep one artifact/publish workflow in `.github/workflows/wheels.yml`; add a release-tag validation script that both tests and CI can exercise. Add a separate `.github/workflows/release-tag.yml` workflow that creates `v<project.version>` tags only for eligible automated upstream-bump commits on `main`, then lets the existing tag-triggered wheel workflow perform a fresh build and PyPI publish.

**Tech Stack:** GitHub Actions, Python 3.11+ stdlib, `uv`, `pytest`, PyPI/TestPyPI trusted publishing, Git tags.

---

## Operator And Automation Responsibilities

I can implement and verify in the repository:

- release tag validation script and unit tests;
- stricter `wheels.yml` gates before PyPI publish;
- a `release-tag.yml` workflow for the automated upstream-bump path;
- workflow static tests in `tests/test_workflows.py`;
- release process documentation in `docs/process/release-artifacts.md` and `docs/process/upstream-bumps.md`;
- local verification with focused pytest, workflow YAML checks, and `make ci AI=1`;
- push the changes and watch hosted `ci`, `api-matrix`, and workflow syntax checks.

You need to configure repository/package settings that code cannot safely create:

- Create a PyPI trusted publisher for:
  - project: `oxipng-pybind`
  - owner: `pdomain`
  - repository: `oxipng-pybind`
  - workflow: `wheels.yml`
  - environment: `pypi`
- Correct the TestPyPI pending publisher to use:
  - project: `oxipng-pybind`
  - owner: `pdomain`
  - repository: `oxipng-pybind`
  - workflow: `wheels.yml`
  - environment: `testpypi`
- Create a GitHub environment named `pypi`; add required reviewers if you want a human approval gate before real PyPI uploads.
- Create a `RELEASE_TAG_TOKEN` repository secret backed by a PAT or GitHub App token that can push tags and will trigger workflows. Do not use the default `GITHUB_TOKEN` for automated release tags because pushes made with it do not trigger normal downstream workflows.
- Ensure branch protection on `main` requires `ci`, `api-matrix`, and the pull-request wheel checks.

## File Structure

- Create `scripts/validate_release_tag.py`: single-purpose CLI and library helpers for validating release tag names, matching `pyproject.toml`, checking tag ancestry, checking PyPI existence, and checking GitHub workflow conclusions.
- Create `tests/test_validate_release_tag.py`: unit tests for tag/version parsing and subprocess/API decision logic.
- Modify `.github/workflows/wheels.yml`: add `validate-release-tag` and make `publish` depend on it; move real PyPI publish behind the `pypi` environment.
- Create `.github/workflows/release-tag.yml`: automated tag creation for upstream-bump commits after main-branch checks pass.
- Modify `tests/test_workflows.py`: static tests for the new release gates and automation workflow.
- Modify `docs/process/release-artifacts.md`: document manual release tags, strict tag gates, PyPI/TestPyPI environments, and TestPyPI rehearsal.
- Modify `docs/process/upstream-bumps.md`: document the automated upstream-bump release tag path and required `RELEASE_TAG_TOKEN`.

---

### Task 1: Add Release Tag Validation Helpers

**Files:**

- Create: `scripts/validate_release_tag.py`
- Test: `tests/test_validate_release_tag.py`

- [ ] **Step 1: Write failing tests for tag and version validation**

Create `tests/test_validate_release_tag.py`:

```python
"""Tests for release tag validation helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validate_release_tag import (
    ReleaseTagError,
    read_project_version,
    release_version_from_tag,
    validate_tag_matches_project_version,
)


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

    with pytest.raises(ReleaseTagError, match="does not match project.version"):
        validate_tag_matches_project_version("v10.1.2", pyproject)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_validate_release_tag.py -q
```

Expected: failure with `ModuleNotFoundError: No module named 'scripts.validate_release_tag'`.

- [ ] **Step 3: Implement minimal validation helpers**

Create `scripts/validate_release_tag.py`:

```python
"""Validate release tags before publishing artifacts."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

RELEASE_TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+(?:\.post\d+)?)$")


class ReleaseTagError(RuntimeError):
    """Raised when a release tag is not eligible for publishing."""


@dataclass(frozen=True)
class WorkflowCheck:
    """A GitHub workflow conclusion required before automated tag creation."""

    workflow: str
    conclusion: str


def release_version_from_tag(tag: str) -> str:
    """Return the project version encoded by a strict release tag."""
    match = RELEASE_TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ReleaseTagError(
            f"release tag {tag!r} must match vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH.postN"
        )
    return match.group("version")


def read_project_version(pyproject: Path) -> str:
    """Read project.version from pyproject.toml."""
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project")
    if not isinstance(project, dict):
        raise ReleaseTagError("pyproject.toml is missing [project]")
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ReleaseTagError("pyproject.toml is missing project.version")
    return version


def validate_tag_matches_project_version(tag: str, pyproject: Path) -> str:
    """Validate that a strict release tag matches project.version."""
    tag_version = release_version_from_tag(tag)
    project_version = read_project_version(pyproject)
    if tag_version != project_version:
        raise ReleaseTagError(
            f"release tag {tag!r} resolves to {tag_version!r}, "
            f"which does not match project.version {project_version!r}"
        )
    return tag_version


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the completed process."""
    return subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ensure_ref_is_on_main(ref: str, main_ref: str) -> None:
    """Require a release ref to be reachable from the configured main ref."""
    fetch = run_git(["fetch", "--quiet", "origin", "main"])
    if fetch.returncode != 0:
        raise ReleaseTagError(fetch.stderr.strip() or "failed to fetch origin/main")
    result = run_git(["merge-base", "--is-ancestor", ref, main_ref])
    if result.returncode != 0:
        raise ReleaseTagError(f"{ref!r} is not contained in {main_ref!r}")


def pypi_version_exists(project: str, version: str, index_url: str) -> bool:
    """Return whether a project version already exists on a PyPI-compatible JSON API."""
    url = f"{index_url.rstrip('/')}/pypi/{project}/{version}/json"
    request = urllib.request.Request(url, headers={"User-Agent": "oxipng-pybind-release-check"})
    try:
        with urllib.request.urlopen(request, timeout=20):
            return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise ReleaseTagError(f"PyPI version check failed with HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise ReleaseTagError(f"PyPI version check failed: {error.reason}") from error


def ensure_pypi_version_absent(project: str, version: str, index_url: str) -> None:
    """Reject release versions that already exist on PyPI."""
    if pypi_version_exists(project, version, index_url):
        raise ReleaseTagError(f"{project} {version} already exists at {index_url}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag name, for example v10.1.1")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--project", default="oxipng-pybind")
    parser.add_argument("--pypi-url", default="https://pypi.org")
    parser.add_argument("--skip-main-check", action="store_true")
    parser.add_argument("--skip-pypi-check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run release tag validation."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        version = validate_tag_matches_project_version(args.tag, args.pyproject)
        if not args.skip_main_check:
            ensure_ref_is_on_main(args.tag, args.main_ref)
        if not args.skip_pypi_check:
            ensure_pypi_version_absent(args.project, version, args.pypi_url)
    except ReleaseTagError as error:
        print(f"release tag validation failed: {error}", file=sys.stderr)
        return 1
    print(f"release tag validation passed for {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_validate_release_tag.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/validate_release_tag.py tests/test_validate_release_tag.py
git commit -m "ci: add release tag validation helper"
```

---

### Task 2: Expand Validation Tests For Git And PyPI Checks

**Files:**

- Modify: `tests/test_validate_release_tag.py`
- Modify: `scripts/validate_release_tag.py`

- [ ] **Step 1: Add failing tests for PyPI and CLI behavior**

Append to `tests/test_validate_release_tag.py`:

```python
from unittest.mock import Mock, patch

from scripts.validate_release_tag import ensure_pypi_version_absent, main


def test_ensure_pypi_version_absent_accepts_missing_version() -> None:
    with patch("scripts.validate_release_tag.pypi_version_exists", return_value=False) as exists:
        ensure_pypi_version_absent("oxipng-pybind", "10.1.1", "https://pypi.org")

    exists.assert_called_once_with("oxipng-pybind", "10.1.1", "https://pypi.org")


def test_ensure_pypi_version_absent_rejects_existing_version() -> None:
    with patch("scripts.validate_release_tag.pypi_version_exists", return_value=True):
        with pytest.raises(ReleaseTagError, match="already exists"):
            ensure_pypi_version_absent("oxipng-pybind", "10.1.1", "https://pypi.org")


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
```

- [ ] **Step 2: Run tests to verify failure if imports or CLI behavior are incomplete**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_validate_release_tag.py -q
```

Expected: pass if Task 1 implementation already includes the CLI and PyPI helpers. If import sorting fails later, the formatting task will fix it.

- [ ] **Step 3: Run lints for the new script and tests**

Run:

```bash
uv run --no-sync --group dev ruff check scripts/validate_release_tag.py tests/test_validate_release_tag.py
uv run --no-sync --group dev basedpyright scripts/validate_release_tag.py tests/test_validate_release_tag.py
```

Expected: both commands pass. If ruff reports import ordering, run:

```bash
uv run --no-sync --group dev ruff check --fix scripts/validate_release_tag.py tests/test_validate_release_tag.py
```

Then rerun the two lint commands.

- [ ] **Step 4: Commit**

Run:

```bash
git add scripts/validate_release_tag.py tests/test_validate_release_tag.py
git commit -m "test: cover release tag validation checks"
```

---

### Task 3: Gate Real PyPI Publishing In wheels.yml

**Files:**

- Modify: `.github/workflows/wheels.yml`
- Modify: `tests/test_workflows.py`

- [ ] **Step 1: Add failing static workflow test**

Append this test to `tests/test_workflows.py`:

```python
def test_pypi_publish_requires_strict_release_tag_validation() -> None:
    """Real PyPI publish is gated by strict tag validation and the pypi environment."""
    workflow = load_workflow(".github/workflows/wheels.yml")
    jobs = workflow["jobs"]
    validate = jobs["validate-release-tag"]
    publish = jobs["publish"]
    validate_steps = validate["steps"]

    assert validate["name"] == "validate release tag"
    assert validate["runs-on"] == "ubuntu-latest"
    assert validate["if"] == "startsWith(github.ref, 'refs/tags/v')"
    assert validate["permissions"] == {"contents": "read"}
    assert validate["outputs"] == {"release-version": "${{ steps.validate.outputs.release-version }}"}
    assert validate_steps[0]["uses"] == "actions/checkout@v6"

    validate_step = step_by_name(validate_steps, "Validate release tag")
    assert validate_step["id"] == "validate"
    assert "python scripts/validate_release_tag.py" in validate_step["run"]
    assert "--tag \"$GITHUB_REF_NAME\"" in validate_step["run"]
    assert "release-version=" in validate_step["run"]

    assert publish["needs"] == ["build", "sdist", "validate-release-tag"]
    assert publish["if"] == "needs.validate-release-tag.outputs.release-version != ''"
    assert publish["environment"] == "pypi"
    assert publish["permissions"] == {"id-token": "write", "contents": "read"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py::test_pypi_publish_requires_strict_release_tag_validation -q
```

Expected: failure because `validate-release-tag` does not exist yet.

- [ ] **Step 3: Add validate-release-tag job and gate publish**

In `.github/workflows/wheels.yml`, insert this job before `publish`:

```yaml
  validate-release-tag:
    name: validate release tag
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    permissions:
      contents: read
    outputs:
      release-version: ${{ steps.validate.outputs.release-version }}
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - name: Validate release tag
        id: validate
        shell: bash
        run: |
          python scripts/validate_release_tag.py --tag "$GITHUB_REF_NAME"
          version="${GITHUB_REF_NAME#v}"
          echo "release-version=$version" >> "$GITHUB_OUTPUT"
```

Change the existing `publish` job to:

```yaml
  publish:
    name: publish
    runs-on: ubuntu-latest
    needs:
      - build
      - sdist
      - validate-release-tag
    if: needs.validate-release-tag.outputs.release-version != ''
    environment: pypi
    permissions:
      id-token: write
      contents: read
```

Leave the existing publish steps intact.

- [ ] **Step 4: Run workflow test**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py::test_pypi_publish_requires_strict_release_tag_validation -q
```

Expected: pass.

- [ ] **Step 5: Run workflow YAML validation**

Run:

```bash
uv run --group dev pre-commit run check-yaml --files .github/workflows/wheels.yml
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add .github/workflows/wheels.yml tests/test_workflows.py
git commit -m "ci: gate pypi publish on release tag validation"
```

---

### Task 4: Add Automated Release Tag Workflow

**Files:**

- Create: `.github/workflows/release-tag.yml`
- Modify: `tests/test_workflows.py`

- [ ] **Step 1: Add failing static workflow test**

Append this test to `tests/test_workflows.py`:

```python
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
    assert step_by_name(steps, "Check release tag token")["env"] == {
        "RELEASE_TAG_TOKEN": "${{ secrets.RELEASE_TAG_TOKEN }}"
    }
    assert "RELEASE_TAG_TOKEN is required" in step_by_name(steps, "Check release tag token")["run"]
    assert "chore: bump upstream oxipng" in step_by_name(steps, "Check automated release eligibility")["run"]
    assert "gh run list --workflow api-matrix.yml" in step_by_name(
        steps, "Wait for API matrix on main commit"
    )["run"]
    assert "https://pypi.org/pypi/oxipng-pybind/" in step_by_name(
        steps, "Check PyPI version does not exist"
    )["run"]
    create = step_by_name(steps, "Create and push release tag")
    assert create["env"] == {"RELEASE_TAG_TOKEN": "${{ secrets.RELEASE_TAG_TOKEN }}"}
    assert "git tag -a" in create["run"]
    assert "git push" in create["run"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py::test_release_tag_workflow_creates_tags_only_after_main_checks -q
```

Expected: failure because `.github/workflows/release-tag.yml` does not exist.

- [ ] **Step 3: Create the workflow**

Create `.github/workflows/release-tag.yml`:

```yaml
name: release-tag

on:
  workflow_dispatch:
  workflow_run:
    workflows: ["ci"]
    types: ["completed"]
    branches: ["main"]

permissions:
  contents: read
  actions: read

jobs:
  create-release-tag:
    name: create release tag
    runs-on: ubuntu-latest
    if: >-
      github.event_name == 'workflow_dispatch' ||
      github.event.workflow_run.conclusion == 'success'
    permissions:
      contents: write
      actions: read
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          token: ${{ secrets.RELEASE_TAG_TOKEN }}
      - name: Check release tag token
        env:
          RELEASE_TAG_TOKEN: ${{ secrets.RELEASE_TAG_TOKEN }}
        run: |
          if [ -z "$RELEASE_TAG_TOKEN" ]; then
            echo "RELEASE_TAG_TOKEN is required to create release tags that trigger the wheels workflow."
            exit 1
          fi
      - name: Check automated release eligibility
        id: eligibility
        shell: bash
        run: |
          git fetch --quiet origin main --tags
          git checkout --quiet origin/main
          subject="$(git log -1 --pretty=%s)"
          if [ "$subject" != "chore: bump upstream oxipng" ]; then
            echo "eligible=false" >> "$GITHUB_OUTPUT"
            echo "latest main commit is not an automated upstream bump: $subject"
            exit 0
          fi
          before_version="$(git show HEAD^:pyproject.toml | python -c 'import sys,tomllib; print(tomllib.loads(sys.stdin.read())["project"]["version"])')"
          version="$(python -c 'import pathlib,tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])')"
          if [ "$before_version" = "$version" ]; then
            echo "eligible=false" >> "$GITHUB_OUTPUT"
            echo "project.version did not change"
            exit 0
          fi
          tag="v$version"
          python scripts/validate_release_tag.py --tag "$tag" --skip-main-check --skip-pypi-check
          if git rev-parse "$tag" >/dev/null 2>&1; then
            echo "eligible=false" >> "$GITHUB_OUTPUT"
            echo "tag already exists: $tag"
            exit 0
          fi
          echo "eligible=true" >> "$GITHUB_OUTPUT"
          echo "version=$version" >> "$GITHUB_OUTPUT"
          echo "tag=$tag" >> "$GITHUB_OUTPUT"
      - name: Wait for API matrix on main commit
        if: steps.eligibility.outputs.eligible == 'true'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          sha="$(git rev-parse HEAD)"
          for attempt in $(seq 1 60); do
            conclusion="$(gh run list --workflow api-matrix.yml --commit "$sha" --json status,conclusion --jq '.[0] | "\(.status) \(.conclusion)"')"
            case "$conclusion" in
              "completed success") exit 0 ;;
              "completed failure"|"completed cancelled"|"completed timed_out") echo "api-matrix failed: $conclusion"; exit 1 ;;
            esac
            sleep 30
          done
          echo "timed out waiting for api-matrix"
          exit 1
      - name: Check PyPI version does not exist
        if: steps.eligibility.outputs.eligible == 'true'
        run: |
          python scripts/validate_release_tag.py \
            --tag "${{ steps.eligibility.outputs.tag }}" \
            --skip-main-check \
            --pypi-url "https://pypi.org"
      - name: Create and push release tag
        if: steps.eligibility.outputs.eligible == 'true'
        env:
          RELEASE_TAG_TOKEN: ${{ secrets.RELEASE_TAG_TOKEN }}
        run: |
          tag="${{ steps.eligibility.outputs.tag }}"
          version="${{ steps.eligibility.outputs.version }}"
          git config user.name "oxipng-pybind release automation"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -a "$tag" -m "Release oxipng-pybind $version"
          git push "https://x-access-token:${RELEASE_TAG_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" "$tag"
```

- [ ] **Step 4: Run workflow static test**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py::test_release_tag_workflow_creates_tags_only_after_main_checks -q
```

Expected: pass.

- [ ] **Step 5: Run YAML validation**

Run:

```bash
uv run --group dev pre-commit run check-yaml --files .github/workflows/release-tag.yml
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add .github/workflows/release-tag.yml tests/test_workflows.py
git commit -m "ci: automate upstream release tag creation"
```

---

### Task 5: Document Manual And Automated Release Processes

**Files:**

- Modify: `docs/process/release-artifacts.md`
- Modify: `docs/process/upstream-bumps.md`

- [ ] **Step 1: Update release artifact docs**

Edit `docs/process/release-artifacts.md` so the publishing section ends with:

```markdown
## Publishing Gates

Manual `workflow_dispatch` runs are build-only by default. Maintainers can set
`publish-target` to `testpypi` to publish the verified wheel and sdist artifacts
to TestPyPI through the `testpypi` GitHub environment and TestPyPI Trusted
Publishing. TestPyPI artifacts use a `.devNNN` version derived from the GitHub
workflow run number and attempt so repeated rehearsals do not collide with
already-published files.

Real PyPI publishing is tag driven. The release tag must be an annotated tag on
`main` and must match `project.version` in `pyproject.toml` exactly:

- `v10.1.1` publishes `10.1.1`;
- `v10.1.1.post1` publishes `10.1.1.post1`.

The release workflow rejects broad or non-final tags such as `vtest`,
`v10.1`, `v10.1.1.dev1`, and `v10.1.1rc1`. It also checks that the target
version does not already exist on PyPI before uploading.

The PyPI publish job runs in the `pypi` GitHub environment. Configure that
environment and the matching PyPI Trusted Publisher before pushing release
tags:

- project: `oxipng-pybind`
- owner: `pdomain`
- repository: `oxipng-pybind`
- workflow: `wheels.yml`
- environment: `pypi`
```

- [ ] **Step 2: Update upstream bump docs**

Edit `docs/process/upstream-bumps.md` after the merge policy section:

```markdown
## Automated Release Tags

After an automated upstream bump PR is rebased into `main`, the
`.github/workflows/release-tag.yml` workflow can create the release tag. It runs
after `ci` completes on `main`, waits for `api-matrix` on the same commit, and
only proceeds when the latest commit subject is `chore: bump upstream oxipng`
and `project.version` changed from the previous commit.

The workflow creates an annotated `v<project.version>` tag only when that tag
does not already exist and the version is absent from PyPI. The tag push then
starts `.github/workflows/wheels.yml`, which rebuilds artifacts and publishes
through the normal PyPI tag path.

`RELEASE_TAG_TOKEN` must be a repository secret backed by a PAT or GitHub App
token that can push tags and trigger workflows. The default `GITHUB_TOKEN` must
not be used for this tag push because pushes made with it do not trigger the
downstream tag workflow.
```

- [ ] **Step 3: Add failing docs test**

Append to `tests/test_workflows.py`:

```python
def test_release_docs_describe_tag_gates_and_automation() -> None:
    """Release docs describe manual tags, automated tags, and required settings."""
    release_text = (ROOT / "docs/process/release-artifacts.md").read_text(
        encoding="utf-8"
    ).lower()
    upstream_text = (ROOT / "docs/process/upstream-bumps.md").read_text(
        encoding="utf-8"
    ).lower()

    assert "v10.1.1" in release_text
    assert "project.version" in release_text
    assert "pypi trusted publisher" in release_text
    assert "environment: `pypi`" in release_text
    assert "vtest" in release_text
    assert "release_tag_token" in upstream_text
    assert "default `github_token` must not be used" in upstream_text
    assert "wheels.yml" in upstream_text
```

- [ ] **Step 4: Run docs test**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py::test_release_docs_describe_tag_gates_and_automation -q
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/process/release-artifacts.md docs/process/upstream-bumps.md tests/test_workflows.py
git commit -m "docs: document gated release automation"
```

---

### Task 6: Full Verification And Push

**Files:**

- Verify all modified files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_validate_release_tag.py tests/test_workflows.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run workflow YAML checks**

Run:

```bash
uv run --group dev pre-commit run check-yaml --files .github/workflows/wheels.yml .github/workflows/release-tag.yml
```

Expected: pass.

- [ ] **Step 3: Run full CI locally**

Run:

```bash
make ci AI=1
```

Expected: pass.

- [ ] **Step 4: Push branch/main as agreed**

If working directly on `main` after prior approval:

```bash
git status --short --branch
git push origin main
```

Expected: push succeeds.

If working on a branch:

```bash
git status --short --branch
git push -u origin HEAD
```

Expected: push succeeds and hosted checks start.

- [ ] **Step 5: Watch hosted checks**

Run:

```bash
gh run list --branch main --limit 10
```

Expected: `ci` and `api-matrix` complete successfully for the pushed commit. If the implementation was pushed to a branch, watch PR checks instead.

---

### Task 7: Post-Merge Repository And Package Setup

**Files:**

- No repository files changed.

- [ ] **Step 1: Configure TestPyPI trusted publisher**

In TestPyPI, remove the pending publisher that uses `testpypi.yml`. Create or replace it with:

```text
Project: oxipng-pybind
Owner: pdomain
Repository: oxipng-pybind
Workflow: wheels.yml
Environment name: testpypi
```

- [ ] **Step 2: Configure PyPI trusted publisher**

In PyPI, create the publisher:

```text
Project: oxipng-pybind
Owner: pdomain
Repository: oxipng-pybind
Workflow: wheels.yml
Environment name: pypi
```

- [ ] **Step 3: Configure GitHub environments**

In GitHub repository settings, ensure:

```text
Environment: testpypi
Allowed branches/tags: main and v*

Environment: pypi
Allowed branches/tags: v*
Required reviewers: maintainers, if human approval is desired
```

- [ ] **Step 4: Configure release tag secret**

Create `RELEASE_TAG_TOKEN` as a repository secret. The token must be able to push tags to `pdomain/oxipng-pybind` and must not be the default `GITHUB_TOKEN`.

- [ ] **Step 5: Rehearse TestPyPI**

Run:

```bash
gh workflow run wheels.yml --ref main -f publish-target=testpypi
```

Expected: all artifacts build, `publish` is skipped, `publish-testpypi` succeeds, and TestPyPI receives a version like `10.1.1.dev801`.

- [ ] **Step 6: Verify real release path without publishing**

Do not push a real `v*` tag until PyPI settings are confirmed. Validate locally with:

```bash
uv run --no-sync --group dev python scripts/validate_release_tag.py --tag "v$(python -c 'import pathlib,tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])')" --skip-main-check
```

Expected: pass only if that version does not already exist on PyPI.

## Self-Review

- Spec coverage: The plan covers manual tags, automated upstream-bump tags, PyPI/TestPyPI trusted publishing, strict tag/version matching, main ancestry checks, PyPI duplicate checks, and operator-owned settings.
- Placeholder scan: No `TBD`, `TODO`, or open-ended implementation placeholders remain.
- Type consistency: The plan consistently uses `ReleaseTagError`, `release_version_from_tag`, `read_project_version`, `validate_tag_matches_project_version`, `ensure_ref_is_on_main`, `ensure_pypi_version_absent`, `validate-release-tag`, `release-tag.yml`, `pypi`, and `testpypi`.

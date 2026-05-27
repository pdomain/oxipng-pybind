# Release Readiness And Remaining Work Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the remaining release-readiness work after the local `main`
integration: wire dependency refresh classification, complete external PyPI and
tag-automation setup, validate hosted automation, publish the first real
release, and keep only this file as the active plan.

**Architecture:** Keep repository implementation work separate from external
operator actions. Repository tasks must be TDD-driven and verified locally
before commit. External tasks must use exact GitHub/PyPI project, workflow, and
environment names so the trusted-publishing and tag-triggered workflows match
the code already checked in.

**Tech Stack:** GitHub Actions, GitHub CLI, PyPI/TestPyPI Trusted Publishing,
OpenID Connect, `uv`, Cargo, PyO3/maturin, pytest, basedpyright, pre-commit,
`scripts/classify_dependency_refresh.py`,
`scripts/validate_release_tag.py`, `scripts/verify_release_artifacts.py`.

---

## Current Baseline

This plan was written against local `main` at `f76e483`.

Already implemented in the repository:

- `.github/workflows/wheels.yml` builds five ABI3 wheels, builds an sdist,
  verifies artifacts, publishes manual TestPyPI rehearsals through
  `environment: testpypi`, and publishes real releases through
  `environment: pypi` on strict `v*` tag pushes.
- `.github/workflows/release-tag.yml` can create automated release tags for
  eligible `chore: bump upstream oxipng` commits after same-commit `ci.yml` and
  `api-matrix.yml` success.
- `scripts/validate_release_tag.py` validates strict final release tags,
  `pyproject.toml` version matching, `main` ancestry, and PyPI duplicate
  status.
- `scripts/verify_release_artifacts.py` validates wheel and sdist contents.
- TestPyPI trusted publishing is configured and already published
  `10.1.1.dev801`; a smoke test from that TestPyPI wheel passed.
- `scripts/classify_dependency_refresh.py` and
  `tests/test_dependency_refresh_classification.py` exist, but
  `.github/workflows/dependency-health.yml` does not yet call the classifier.
- `scripts/generate_third_party_notices.py`,
  `tests/test_third_party_notices.py`, `THIRD_PARTY_NOTICES.md`, and the
  dependency refresh/upstream bump notice-generation steps exist.

External state still required:

- GitHub Actions for `pdomain/oxipng-pybind` are currently disabled.
- The GitHub `pypi` environment still needs to be created.
- The real PyPI trusted publisher still needs to be configured for
  `workflow: wheels.yml` and `environment: pypi`.
- `RELEASE_TAG_TOKEN` still needs to be added as a repository secret backed by
  a PAT or GitHub App token that can push tags and trigger workflows.

## File Structure

- `.github/workflows/dependency-health.yml`: run the dependency classifier,
  include its outputs in the PR body and labels, and auto-merge only
  `no-release-needed` refreshes.
- `tests/test_workflows.py`: structural workflow tests for dependency
  classification wiring and auto-merge gating.
- `docs/process/dependency-health.md`: durable process documentation for the
  dependency classification behavior.
- `docs/process/release-artifacts.md`: durable process documentation for PyPI,
  TestPyPI, and first-release verification.
- `docs/process/upstream-bumps.md`: durable process documentation for
  `RELEASE_TAG_TOKEN` and automated release tags.
- `docs/plans/unfinished-work.md`: this single active implementation plan.

## Task 1: Wire Dependency Refresh Classification

**Files:**

- Modify: `.github/workflows/dependency-health.yml`
- Modify: `tests/test_workflows.py`
- Modify: `docs/process/dependency-health.md`

- [ ] **Step 1: Add failing workflow assertions**

In `tests/test_workflows.py`, extend
`test_dependency_refresh_auto_merge_is_ci_gated` so it asserts the classifier
is run after dependency changes are detected and before artifact upload:

```python
assert_ordered_steps(
    prepare_steps,
    [
        "Refresh lockfiles",
        "Sync refreshed dependencies",
        "Refresh pre-commit hooks",
        "Apply lint and generated-file fixes",
        "Generate third-party notices",
        "Run dependency audits",
        "Run CI",
        "Check for changes",
        "Classify dependency refresh",
        "Upload dependency refresh workspace",
    ],
)

classify = step_by_name(prepare_steps, "Classify dependency refresh")
assert classify["id"] == "classification"
assert classify["if"] == "steps.changes.outputs.changed == 'true'"
assert classify["run"] == (
    "uv run --locked --group dev python "
    "scripts/classify_dependency_refresh.py --base-ref origin/main"
)

assert prepare["outputs"]["release-label"] == "${{ steps.classification.outputs.label }}"
assert prepare["outputs"]["release-needed"] == (
    "${{ steps.classification.outputs.release-needed }}"
)
assert prepare["outputs"]["release-reason"] == "${{ steps.classification.outputs.reason }}"

create_pr = step_by_name(publish_steps, "Create pull request")
assert "Release classification:" in create_pr["with"]["body"]
assert "${{ needs.prepare.outputs.release-label }}" in create_pr["with"]["body"]
assert create_pr["with"]["labels"] == (
    "dependencies, automated, ${{ needs.prepare.outputs.release-label }}"
)

auto_merge = step_by_name(publish_steps, "Enable auto-merge")
assert "needs.prepare.outputs.release-needed == 'false'" in auto_merge["if"]
```

- [ ] **Step 2: Run the focused test and confirm it fails**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py::test_dependency_refresh_auto_merge_is_ci_gated -q
```

Expected: fail because `.github/workflows/dependency-health.yml` does not have
the `Classify dependency refresh` step or classifier outputs yet.

- [ ] **Step 3: Add classifier outputs to the prepare job**

In `.github/workflows/dependency-health.yml`, extend
`jobs.prepare.outputs`:

```yaml
      release-needed: ${{ steps.classification.outputs.release-needed }}
      release-label: ${{ steps.classification.outputs.label }}
      release-reason: ${{ steps.classification.outputs.reason }}
```

Add this step after `Check for changes` and before
`Upload dependency refresh workspace`:

```yaml
      - name: Classify dependency refresh
        id: classification
        if: steps.changes.outputs.changed == 'true'
        run: uv run --locked --group dev python scripts/classify_dependency_refresh.py --base-ref origin/main
```

- [ ] **Step 4: Add classification to the PR body and labels**

In the `Create pull request` step body, include:

```markdown
            Release classification:

            - `${{ needs.prepare.outputs.release-label }}`
            - `${{ needs.prepare.outputs.release-reason }}`

            `no-release-needed` PRs auto-merge after required checks pass.
            `release-needed` PRs stay open for an explicit wrapper version bump
            before merge.
```

Change labels to:

```yaml
          labels: dependencies, automated, ${{ needs.prepare.outputs.release-label }}
```

- [ ] **Step 5: Gate auto-merge to no-release-needed refreshes**

Change the `Enable auto-merge` step `if` condition to:

```yaml
        if: >-
          needs.prepare.outputs.release-needed == 'false' &&
          steps.cpr.outputs.pull-request-number != '' &&
          contains(fromJSON('["created", "updated"]'), steps.cpr.outputs.pull-request-operation)
```

- [ ] **Step 6: Update dependency process docs**

In `docs/process/dependency-health.md`, update `Scheduled Refresh` and
`Release Classification` so they state:

```markdown
The prepare job runs `scripts/classify_dependency_refresh.py --base-ref origin/main`
after it detects changed files. The publish job adds the classifier label and
reason to the PR.

`no-release-needed` PRs may auto-merge after required checks pass.
`release-needed` PRs are opened but not auto-merged; they stay open for wrapper
version review.
```

- [ ] **Step 7: Verify and commit**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_dependency_refresh_classification.py tests/test_workflows.py -q
uv run --no-sync --group dev basedpyright scripts/classify_dependency_refresh.py tests/test_dependency_refresh_classification.py tests/test_workflows.py
uv run --group dev pre-commit run check-yaml --files .github/workflows/dependency-health.yml
```

Expected: all pass.

Commit:

```bash
git add .github/workflows/dependency-health.yml tests/test_workflows.py docs/process/dependency-health.md
git commit -m "ci: gate dependency refresh auto-merge by classification"
```

## Task 2: Configure External Release Settings

**Files:**

- No repository files should change.

- [ ] **Step 1: Create the GitHub PyPI environment**

Run:

```bash
gh api --method PUT repos/pdomain/oxipng-pybind/environments/pypi
```

Expected: command exits 0. In GitHub, the repository has an environment named
`pypi`.

- [ ] **Step 2: Configure the real PyPI trusted publisher**

In PyPI project publishing settings, create a pending or trusted publisher with
exactly:

```text
project: oxipng-pybind
owner: pdomain
repository: oxipng-pybind
workflow: wheels.yml
environment: pypi
```

Expected: PyPI shows a publisher for `pdomain/oxipng-pybind`,
`.github/workflows/wheels.yml`, environment `pypi`.

- [ ] **Step 3: Add the release tag token**

Create a PAT or GitHub App token that can push tags and trigger workflows, then
store it:

```bash
gh secret set RELEASE_TAG_TOKEN --repo pdomain/oxipng-pybind
```

Expected: `gh secret list --repo pdomain/oxipng-pybind` includes
`RELEASE_TAG_TOKEN`.

- [ ] **Step 4: Re-enable GitHub Actions**

Run:

```bash
gh api --method PUT repos/pdomain/oxipng-pybind/actions/permissions -F enabled=true
```

Expected: GitHub Actions are enabled for `pdomain/oxipng-pybind`.

## Task 3: Validate Hosted Dependency Refresh

**Files:**

- No repository files should change unless the workflow opens an automated PR.

- [ ] **Step 1: Push local main first**

Confirm local `main` is clean and contains Task 1 if it was needed:

```bash
git status --short --branch
```

Expected: `## main...origin/main [ahead N]` with no changed files.

Push only after the user explicitly approves:

```bash
git push origin main
```

- [ ] **Step 2: Run dependency-health on hosted main**

Run:

```bash
gh workflow run dependency-health.yml --repo pdomain/oxipng-pybind --ref main
```

Watch it:

```bash
gh run list --repo pdomain/oxipng-pybind --workflow dependency-health.yml --limit 3
gh run watch --repo pdomain/oxipng-pybind
```

Expected: the workflow completes successfully. If it creates a PR, the PR body
contains a release classification.

- [ ] **Step 3: Confirm no-release-needed behavior**

For a tooling-only refresh, confirm:

```text
label: no-release-needed
auto-merge: enabled
merge method: rebase
```

Expected: the PR auto-merges only after required checks pass.

- [ ] **Step 4: Confirm release-needed behavior when applicable**

For a runtime dependency or `[project.dependencies]` change, confirm:

```text
label: release-needed
auto-merge: not enabled
```

Expected: the PR stays open for wrapper version review.

## Task 4: Publish The First Real PyPI Release

**Files:**

- No repository files should change.

- [ ] **Step 1: Confirm pre-release gates**

Run locally:

```bash
make ci AI=1
uv run --no-sync python scripts/validate_release_tag.py --tag v10.1.1 --project oxipng-pybind --pypi-url https://pypi.org
```

Expected: CI passes and tag validation reports success for `v10.1.1`.

- [ ] **Step 2: Confirm hosted checks on the release commit**

For the commit being released, confirm hosted checks:

```bash
gh run list --repo pdomain/oxipng-pybind --workflow ci.yml --commit "$(git rev-parse HEAD)" --limit 1
gh run list --repo pdomain/oxipng-pybind --workflow api-matrix.yml --commit "$(git rev-parse HEAD)" --limit 1
```

Expected: both latest runs for the commit are `completed success`.

- [ ] **Step 3: Create and push the release tag**

Create an annotated tag:

```bash
git tag -a v10.1.1 -m "Release oxipng-pybind 10.1.1"
git push origin v10.1.1
```

Expected: `.github/workflows/wheels.yml` starts from the tag push, builds fresh
wheels and sdist, validates the release tag, enters `environment: pypi`, and
publishes through PyPI Trusted Publishing.

- [ ] **Step 4: Watch the publish workflow**

Run:

```bash
gh run list --repo pdomain/oxipng-pybind --workflow wheels.yml --limit 5
gh run watch --repo pdomain/oxipng-pybind
```

Expected: all wheel jobs, `sdist`, `validate-release-tag`, and `publish`
complete successfully.

- [ ] **Step 5: Smoke-test the real PyPI artifact**

Use a throwaway environment:

```bash
tmpdir="$(mktemp -d)"
python -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --upgrade pip
"$tmpdir/venv/bin/python" -m pip install "oxipng-pybind==10.1.1" "pillow==12.2.0"
"$tmpdir/venv/bin/python" scripts/smoke_wheel.py
```

Expected: smoke test passes and `import oxipng` imports the PyPI wheel.

## Task 5: Prove Automated Upstream Bump Release Tags

**Files:**

- No repository files should change unless an upstream `oxipng` release exists
  and the workflow opens a bump PR.

- [ ] **Step 1: Wait for a newer upstream oxipng release**

Check upstream and crates.io:

```bash
gh release list --repo oxipng/oxipng --limit 5
cargo search oxipng --limit 1
```

Expected: a version newer than `10.1.1` exists on both GitHub releases and
crates.io.

- [ ] **Step 2: Run upstream-bump**

Run:

```bash
gh workflow run upstream-bump.yml --repo pdomain/oxipng-pybind --ref main
```

Expected: the workflow opens or updates a `chore: bump upstream oxipng` PR when
files change.

- [ ] **Step 3: Verify bump PR behavior**

Confirm the PR:

```text
title: chore: bump upstream oxipng
branch: automation/bump-oxipng
checks: ci, api-matrix, wheels
auto-merge: rebase after required checks pass
```

Expected: the PR merges only after required checks pass.

- [ ] **Step 4: Verify release-tag automation after merge**

After the bump commit lands on `main`, watch:

```bash
gh run list --repo pdomain/oxipng-pybind --workflow release-tag.yml --limit 5
gh run list --repo pdomain/oxipng-pybind --workflow wheels.yml --limit 5
```

Expected: `release-tag.yml` creates `v<project.version>` only if latest `main`
is the eligible bump commit, then `wheels.yml` publishes that tag through
`environment: pypi`.

## Task 6: Optional Future Artifact Targets

**Files:**

- Modify only after there is user demand:
  `.github/workflows/wheels.yml`, `scripts/check_wheel_tags.py`,
  `tests/test_workflows.py`, `docs/process/release-artifacts.md`.

- [ ] **Step 1: Decide whether demand exists**

Do not implement by default. Open an issue or maintainer note only if users ask
for one of:

```text
Windows ARM64 wheels
musllinux x86_64/aarch64 wheels
additional source-install support beyond the current sdist smoke
```

Expected: no repository change unless there is a specific user or maintainer
request.

- [ ] **Step 2: Add target-specific workflow tests before implementation**

For a new wheel target, add a test in `tests/test_workflows.py` that asserts the
matrix entry, expected platform tag, and smoke policy.

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py -q
```

Expected before implementation: the new target test fails.

- [ ] **Step 3: Implement the requested target**

Add only the requested target to `.github/workflows/wheels.yml` and update
`scripts/check_wheel_tags.py` or artifact verification only if the target needs
new platform matching.

- [ ] **Step 4: Verify**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py tests/test_release_artifacts.py -q
make ci AI=1
```

Expected: all pass before pushing.

## Self-Review

- Completed implementation plans and review reports are intentionally not kept
  as active docs. Use Git history for old plans and reports.
- The only active plan file is this file:
  `docs/plans/unfinished-work.md`.
- Remaining implementation work is limited to dependency refresh classifier
  workflow wiring. Other required work is external setup or hosted validation.
- TestPyPI workflow creation is not listed because TestPyPI publishing is
  already implemented in `.github/workflows/wheels.yml` and proved with
  `10.1.1.dev801`.
- Release tag validation and automation are not listed as implementation tasks
  because `scripts/validate_release_tag.py`, `tests/test_validate_release_tag.py`,
  `.github/workflows/release-tag.yml`, and the `wheels.yml` tag gate already
  exist.

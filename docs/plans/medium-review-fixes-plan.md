# Medium Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all medium-severity findings from `docs/plans/full-code-review-report.md`.

**Architecture:** Treat release, workflow, dependency, and API-surface findings as separate workstreams with focused tests. Keep API behavior stable unless this plan explicitly broadens accepted ordered inputs.

**Tech Stack:** Rust/PyO3, Python facade and stubs, maturin, uv, GitHub Actions, pytest, basedpyright.

---

## Agreed Review Decisions

This plan records the interactive review decisions for the 15 medium findings.

### Medium 1: File APIs are symlink and TOCTOU sensitive

**Disposition:** Fix now, docs only.

**Files:**

- Modify: `docs/usage/untrusted-input.md`
- Modify: `docs/usage/file-optimization.md`
- Modify: `docs/architecture/overview.md`

**How:**

- Add the main guidance to `docs/usage/untrusted-input.md`.
- Add only a short cross-reference phrase in file optimization and architecture docs.
- Tell service callers to use private work directories, server-generated filenames, and avoid caller-controlled output or backup paths for untrusted files.

**Recommendation:** Do not add Rust file-open hardening in this pass. Keep low-level `openat`/`O_NOFOLLOW` style hardening deferred unless the project commits to a hardened file API.

### Medium 2: The wheel smoke step installs live PyPI dependencies

**Disposition:** Fix now.

**Files:**

- Modify: `.github/workflows/wheels.yml`
- Modify: `tests/test_workflows.py`
- Possibly create or modify a lock-backed smoke dependency helper or constraints file.

**How:**

- Keep installing the local built wheel from `dist/*.whl`.
- Replace bare `pillow` in the smoke step with a pinned dependency path derived from `uv.lock` where practical.
- If exporting constraints from the lockfile adds too much machinery, use a direct pinned Pillow constraint as the fallback.

**Recommendation:** Prefer a lock-backed constraints approach so the smoke dependency follows the committed dependency state.

### Medium 3: Source distribution docs are ahead of release support

**Disposition:** Fix now by adding tested sdist support.

**Files:**

- Modify: `.github/workflows/wheels.yml`
- Modify: `scripts/verify_release_artifacts.py`
- Modify: `tests/test_release_artifacts.py`
- Modify: `docs/process/release-artifacts.md`
- Modify: `docs/usage/build-from-source.md`
- Possibly modify: `pyproject.toml`

**How:**

- Build an sdist in the release workflow.
- Verify the sdist before publish.
- Smoke-test source install or source wheel build behavior in a clean environment.
- Publish the sdist only after its verification gate passes.

**Recommendation:** Add sdist support only with explicit verification that the sdist contains required project files and can build a wheel from source.

### Medium 4: Release artifact verification checks filenames more than wheel contents

**Disposition:** Fix now.

**Files:**

- Modify: `scripts/verify_release_artifacts.py`
- Modify: `tests/test_release_artifacts.py`
- Modify: `docs/process/release-artifacts.md`

**How:**

- Open each wheel ZIP and verify required contents, including wheel metadata, license files, notice files, package files, stubs, `py.typed`, and exactly one native extension in the expected layout.
- Add separate verification for sdists when Medium 3 is implemented.

**Recommendation:** Add tests for invalid ZIPs, missing metadata, missing typing files, missing license or notice files, missing native extension, and duplicate or unexpected extension layout.

### Medium 5: Some workflow tests still use substring checks

**Disposition:** Fix now.

**Files:**

- Modify: `tests/test_workflows.py`

**How:**

- Convert security and release workflow tests from broad substring checks to parsed YAML assertions.
- Assert job permissions, `needs`, step names and order, action refs, `if` conditions, and command fragments inside the intended named step.

**Recommendation:** Prioritize `wheels.yml`, `dependency-health.yml`, and `upstream-bump.yml`. Keep prose-only doc checks lightweight.

### Medium 6: Dependency refresh classification can miss duplicate Cargo package names

**Disposition:** Fix now.

**Files:**

- Modify: `scripts/classify_dependency_refresh.py`
- Modify: `tests/test_dependency_refresh_classification.py`

**How:**

- Key Cargo lock packages by `name`, `version`, and `source`.
- Preserve duplicate names as distinct packages.
- Use stable display strings in release classification reasons.
- Make inverse `cargo tree` calls precise enough to avoid duplicate-name ambiguity.

**Recommendation:** Add tests with duplicate Cargo package names at different versions and verify both are preserved and classified independently.

### Medium 7: Hosted automation syncs unlocked Python dependencies in some jobs

**Disposition:** Fix now.

**Files:**

- Modify: `.github/workflows/api-matrix.yml`
- Modify: `.github/workflows/dependency-health.yml`
- Modify: `.github/workflows/upstream-bump.yml`
- Modify: `tests/test_workflows.py`

**How:**

- Use `uv sync --locked --group dev` everywhere jobs consume an existing or freshly generated lockfile.
- Keep unlocked operations only where the workflow intentionally changes lockfiles, such as `uv lock --upgrade`.

**Recommendation:** Add structural workflow tests that normal sync steps include `--locked` and the intentional lock-refresh step remains allowed.

### Medium 8: Docs conflict on release readiness

**Disposition:** Fix now.

**Intended state:** PyPI publishing is the supported release path.

**Files:**

- Modify: `README.md`
- Modify: `docs/process/release-artifacts.md`
- Modify: `docs/plans/unfinished-work.md`
- Possibly modify: `.github/workflows/wheels.yml`

**How:**

- Remove stale “PyPI publishing is not enabled yet” language.
- Document normal installation as PyPI wheels.
- Keep source builds as the fallback for unsupported platforms.

**Recommendation:** Align README, release docs, and unfinished-work notes after wheel, Trusted Publishing, and sdist verification gates are in place.

### Medium 9: Merge policy docs conflict with automation

**Disposition:** Fix now.

**Policy:** Rebase only.

**Files:**

- Modify: `CONTRIBUTING.md`
- Modify: `docs/process/upstream-bumps.md`
- Modify: `docs/process/dependency-health.md`
- Modify: `tests/test_workflows.py`

**How:**

- Update project merge policy to require rebase merges for human and automation PRs.
- Keep automation using `gh pr merge --auto --rebase`.
- Remove conflicting merge-commit guidance.

**Recommendation:** Tests should assert `--rebase` and the absence of `--merge` and `--squash`.

### Medium 10: Auto-merge safety depends on settings that are not checked in

**Disposition:** Fix now with docs plus an audit helper.

**Files:**

- Create: `docs/process/github-settings.md`
- Modify: `docs/process/upstream-bumps.md`
- Modify: `docs/process/dependency-health.md`
- Create: `scripts/audit_github_settings.py`
- Create or modify focused script tests under `tests/`

**How:**

- Centralize required repository settings in one process doc.
- Add a `gh`-based audit script for settings that can be checked reliably: default branch protection, required checks, auto-merge allowance, rebase merge enabled, and available automation secrets where the API exposes them.

**Recommendation:** Make the script a maintainer tool first. Do not make it a blocking CI gate until token permissions and API coverage are confirmed.

### Medium 11: Pre-commit dependency health is not automated

**Disposition:** Fix now by folding pre-commit hook refresh into dependency health automation.

**Files:**

- Modify: `.github/workflows/dependency-health.yml`
- Modify: `scripts/classify_dependency_refresh.py`
- Modify: `tests/test_workflows.py`
- Modify: `tests/test_dependency_refresh_classification.py`
- Modify: `docs/process/dependency-health.md`

**How:**

- Extend the dependency-health workflow order:
  1. `uv lock --upgrade`
  2. `cargo update`
  3. `uv sync --locked --group dev`
  4. `uv run --locked --group dev pre-commit autoupdate`
  5. `make lint-fix`
  6. `make third-party-notices`
  7. `make dependency-audit`
  8. `make ci`
  9. detect changed files and create the PR
- Ensure the PR includes `.pre-commit-config.yaml` and hook or fix-generated formatting changes.
- Prefer a changed-file driven artifact and add-path strategy so autoformatted files are not silently dropped.

**Recommendation:** Classify pre-commit and formatting-only refreshes as `no-release-needed` unless runtime dependency files changed.

### Medium 12: Upstream bump can race GitHub releases and crates.io

**Disposition:** Fix now.

**Files:**

- Modify: `scripts/bump_upstream.py`
- Modify: `tests/test_bump_upstream.py`
- Modify: `docs/process/upstream-bumps.md`

**How:**

- Check crates.io for the target `oxipng` crate version before editing files or running `cargo update`.
- If GitHub has the release but crates.io does not have the crate yet, exit successfully with no changes and a clear retryable message.

**Recommendation:** Treat a missing crate as a clean scheduled no-op, not a failed workflow.

### Medium 13: `FilterStrategy.predefined()` accepts unordered collections

**Disposition:** Fix now.

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/_pyoxipng_compat.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`
- Modify: `docs/architecture/options-surface.md`

**How:**

- Reject `set` and `frozenset` in `FilterStrategy.predefined()` with `TypeError`.
- Continue accepting ordered sequences and generators.

**Recommendation:** Do not sort unordered collections. Predefined filter order is meaningful; callers that want sorted order should pass `sorted(values)` themselves.

### Medium 14: Filter type annotations allow invalid nested predefined filters

**Disposition:** Fix now.

**Files:**

- Modify: `oxipng/__init__.pyi`
- Add or modify a focused basedpyright typing fixture/test

**How:**

- Split scalar filter values from whole-option predefined values.
- Make `_PredefinedFilters` valid only as the entire `filter=` value, not inside a list, tuple, or set.
- Keep direct scalar filter collections limited to scalar filter values.

**Recommendation:** Add a type-checking fixture that accepts `filter=FilterStrategy.predefined(...)` and rejects `filter=[FilterStrategy.predefined(...)]`.

### Medium 15: pyoxipng palette compatibility is narrower than pyoxipng

**Disposition:** Fix now for stable and compatibility paths.

**Files:**

- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`
- Modify: `docs/usage/raw-image.md`
- Modify: `docs/usage/pyoxipng-migration.md`

**How:**

- Accept palette entries as ordered finite sequences of length 3 or 4.
- Reject strings, bytes, mappings, sets, frozensets, wrong lengths, bool channels, and out-of-range channel values.
- Keep outer palette order meaningful and reject unordered outer containers.

**Recommendation:** Use tuple examples as the canonical docs style, but document that ordered 3- or 4-channel sequences are accepted for JSON and pyoxipng compatibility.

## Recommended Execution Order

- [ ] **Task 1:** Fix documentation-only policy items: Medium 1, Medium 8, Medium 9, and the docs portions of Medium 10.
- [ ] **Task 2:** Harden workflow tests structurally for Medium 5, then use those helpers in workflow changes.
- [ ] **Task 3:** Fix workflow dependency determinism and dependency refresh automation: Medium 2, Medium 7, and Medium 11.
- [ ] **Task 4:** Add release artifact content verification and sdist support: Medium 3 and Medium 4.
- [ ] **Task 5:** Fix dependency and upstream automation scripts: Medium 6, Medium 10 audit helper, and Medium 12.
- [ ] **Task 6:** Fix filter API and typing behavior: Medium 13 and Medium 14.
- [ ] **Task 7:** Broaden ordered palette-entry handling: Medium 15.
- [ ] **Task 8:** Run focused tests for changed areas, then run `make ci AI=1`.

## Verification

- Run focused tests after each task:
  - `uv run --no-sync --group dev pytest tests/test_workflows.py -q`
  - `uv run --no-sync --group dev pytest tests/test_release_artifacts.py -q`
  - `uv run --no-sync --group dev pytest tests/test_dependency_refresh_classification.py tests/test_bump_upstream.py -q`
  - `make develop AI=1`
  - `uv run --no-sync --group dev pytest tests/test_api.py -q`
- Run type checking after stub changes:
  - `make typecheck AI=1`
- Final verification:
  - `make ci AI=1`

## Self-Review

- All 15 medium findings from `docs/plans/full-code-review-report.md` are covered above.
- The plan records every interactive decision made during review.
- No finding is silently downgraded to “won't fix”; deferred hardening for Medium 1 is explicitly documented as a recommendation.

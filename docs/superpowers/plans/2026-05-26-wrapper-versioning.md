# Wrapper Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split Python wrapper release versions from Cargo SemVer and upstream `oxipng` pins.

**Architecture:** Keep the Python package version as the public wrapper release version. Keep Cargo package versions SemVer-valid and keep the `oxi` dependency pin as the upstream source of truth. Add a wrapper-only post-release bump path that updates only Python package metadata and `uv.lock`.

**Tech Stack:** Python 3.11+, tomlkit, pytest, Cargo, uv, GitHub Actions.

---

## Task 1: Add Version Helpers

**Files:**

- Modify: `scripts/bump_upstream.py`
- Modify: `tests/test_bump_upstream.py`

- [x] **Step 1: Add tests for post-release version helpers**

Add tests that cover `10.1.1 -> 10.1.1.post1`, `10.1.1.post1 -> 10.1.1.post2`, invalid inputs, and reading the pinned upstream version from `Cargo.toml`.

- [x] **Step 2: Run helper tests and verify failure**

Run: `uv run --group dev pytest tests/test_bump_upstream.py -q`

Expected: tests fail because the helper functions do not exist.

- [x] **Step 3: Implement version helpers**

Add regex-based helpers in `scripts/bump_upstream.py`:

- `next_post_release(version: str) -> str`
- `read_pyproject_version(path: Path) -> str`
- `read_pinned_upstream_version(path: Path) -> str`

- [x] **Step 4: Run helper tests**

Run: `uv run --group dev pytest tests/test_bump_upstream.py -q`

Expected: helper tests pass.

## Task 2: Split Upstream and Wrapper Bumps

**Files:**

- Modify: `scripts/bump_upstream.py`
- Modify: `tests/test_bump_upstream.py`

- [x] **Step 1: Add tests for bump behavior**

Add tests that prove:

- upstream checks do not reset `10.1.1.post1` when the pinned upstream is still `10.1.1`
- upstream bumps reset the Python version to the new upstream base
- wrapper post bumps update only `pyproject.toml` and `uv.lock`

- [x] **Step 2: Run behavior tests and verify failure**

Run: `uv run --group dev pytest tests/test_bump_upstream.py -q`

Expected: tests fail until script behavior is split.

- [x] **Step 3: Implement CLI modes**

Update `scripts/bump_upstream.py` so default mode performs an upstream check and `--wrapper-post` bumps only the Python package version to the next `.postN`.

- [x] **Step 4: Run script tests**

Run: `uv run --group dev pytest tests/test_bump_upstream.py tests/test_scripts.py -q`

Expected: all selected script tests pass.

## Task 3: Document Version Policy

**Files:**

- Modify: `docs/process/upstream-bumps.md`

- [x] **Step 1: Document wrapper and upstream versions**

Add a short section that defines Python wrapper version, Cargo crate version, upstream dependency pin, and API manifest version.

- [x] **Step 2: Lint docs**

Run: `uv run --group dev pre-commit run markdownlint-cli2 --files docs/process/upstream-bumps.md docs/superpowers/plans/2026-05-26-wrapper-versioning.md`

Expected: markdownlint passes.

## Task 4: Final Verification

**Files:**

- Verify: `scripts/bump_upstream.py`
- Verify: `tests/test_bump_upstream.py`
- Verify: `docs/process/upstream-bumps.md`

- [x] **Step 1: Run focused verification**

Run:

```bash
uv run --group dev pytest tests/test_bump_upstream.py tests/test_scan_upstream_surface.py tests/test_scripts.py -q
uv run --group dev ruff check scripts/bump_upstream.py tests/test_bump_upstream.py tests/test_scripts.py
uv run --group dev basedpyright
uv run --group dev pre-commit run markdownlint-cli2 --files docs/process/upstream-bumps.md docs/superpowers/plans/2026-05-26-wrapper-versioning.md
```

Expected: all commands pass.

- [x] **Step 2: Commit**

Commit the script, tests, docs, and plan.

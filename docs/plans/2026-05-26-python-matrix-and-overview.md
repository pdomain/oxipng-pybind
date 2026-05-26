# Python Matrix and Architecture Overview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the remaining concrete gaps from `docs/specs/2026-05-25-api-and-wheels-design.md`: public API tests across Python 3.11 through 3.14 and the architecture overview document.

**Architecture:** Keep regular source CI fast on Python 3.13, and add a separate API matrix workflow that builds the editable extension and runs the public API test suite on Python 3.11, 3.12, 3.13, and 3.14. Add `docs/architecture/overview.md` as the human-readable package layout and data-flow overview linked from the docs index.

**Tech Stack:** GitHub Actions, uv, Rust 1.85.1, maturin, pytest, markdownlint.

---

## File Structure

Modify existing files:

- `.github/workflows/ci.yml`
- `README.md`
- `docs/README.md`
- `docs/specs/2026-05-25-api-and-wheels-design.md`

Create new files:

- `.github/workflows/api-matrix.yml`
- `docs/architecture/overview.md`

Do not modify the public API implementation in this follow-up unless tests show
the matrix exposes a real compatibility bug.

---

## Task 1: Add Architecture Overview Documentation

**Files:**

- Create: `docs/architecture/overview.md`
- Modify: `docs/README.md`
- Modify: `README.md`

- [x] **Step 1: Create architecture overview**

Create `docs/architecture/overview.md` with sections covering:

- package layout
- Rust/Python boundary
- file optimization data flow
- memory optimization data flow
- error mapping
- wheel strategy
- upstream surface policy

Expected: the document explains how `oxipng/__init__.py`, `oxipng/__init__.pyi`,
`src/lib.rs`, and the workflows fit together.

- [x] **Step 2: Link the overview from docs index**

Update `docs/README.md` so the architecture section links to:

- `architecture/overview.md`
- `architecture/api-compatibility.md`
- `architecture/options-surface.md`

Expected: docs navigation exposes the overview.

- [x] **Step 3: Mention wheel availability in README**

Update `README.md` to state that ABI3 wheels target Python 3.11+ and are
produced by the artifact workflow before PyPI publishing is enabled.

Expected: the README matches the 2026-05-25 spec's documentation split.

- [x] **Step 4: Run markdown lint**

Run:

```bash
make md-lint
```

Expected: markdownlint passes.

---

## Task 2: Add Public API Python Version Matrix

**Files:**

- Create: `.github/workflows/api-matrix.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/specs/2026-05-25-api-and-wheels-design.md`

- [x] **Step 1: Add API matrix workflow**

Create `.github/workflows/api-matrix.yml` with:

- `push` and `pull_request` triggers for `main`
- `workflow_dispatch`
- Python matrix `["3.11", "3.12", "3.13", "3.14"]`
- `actions/checkout@v6`
- `astral-sh/setup-uv@v7`
- `dtolnay/rust-toolchain@1.85.1`
- `uv sync --group dev`
- `uv run --group dev maturin develop`
- `uv run --group dev pytest tests/test_api.py -v -ra`

Expected: the workflow verifies the public API suite across the supported
Python range without building separate release wheels.

- [x] **Step 2: Cross-link CI workflow**

Update `.github/workflows/ci.yml` path comments or job naming if needed so the
source CI and API matrix responsibilities are clear.

Expected: regular `ci` still runs `make ci`; the new matrix owns Python-version
coverage.

- [x] **Step 3: Update umbrella spec status**

Append an implementation note to `docs/specs/2026-05-25-api-and-wheels-design.md`
stating that Python-version API coverage is implemented by
`.github/workflows/api-matrix.yml`.

Expected: the spec records how the matrix requirement is satisfied.

- [x] **Step 4: Validate workflow YAML**

Run:

```bash
uv run --group dev pre-commit run check-yaml --files .github/workflows/api-matrix.yml .github/workflows/ci.yml
```

Expected: workflow YAML passes.

---

## Task 3: Final Verification and Commit

**Files:**

- Modify as needed based on verification failures only.

- [x] **Step 1: Run focused checks**

Run:

```bash
uv run --group dev pytest tests/test_api.py -v -ra
make md-lint
uv run --group dev pre-commit run check-yaml --files .github/workflows/api-matrix.yml .github/workflows/ci.yml
```

Expected: focused API tests, docs lint, and YAML validation pass.

- [x] **Step 2: Run full pre-commit**

Run:

```bash
make pre-commit-check
```

Expected: all hooks pass.

- [x] **Step 3: Commit and push**

Run:

```bash
git add .github/workflows/api-matrix.yml .github/workflows/ci.yml
git add README.md docs
git commit -m "ci: add public api python matrix"
git push origin main
```

Expected: the commit succeeds and is pushed to `origin/main`.

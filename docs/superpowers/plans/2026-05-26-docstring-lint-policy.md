# Docstring Lint Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make docstring linting enforce concise, specific public API documentation for production Python and automation scripts while keeping tests name-first.

**Architecture:** Use Ruff `D` rules as the mechanical gate for production Python and scripts. Keep tests exempt from `D` rules because test names are the behavior contract. Document the policy in `docs/conventions/lint-deviations.md` so future suppressions stay narrow and justified.

**Tech Stack:** Ruff pydocstyle rules, pyproject lint configuration, markdown docs, uv, pre-commit.

---

## File Structure

Modify existing files:

- `scripts/__init__.py`: add a package docstring.
- `pyproject.toml`: remove broad docstring ignores for scripts; narrow global docstring ignores.
- `docs/conventions/lint-deviations.md`: update the lint deviation record and add docstring quality rules.

No source API behavior should change.

## Policy

Production Python and automation scripts are docstring-first:

- public modules, packages, classes, functions, and methods get docstrings;
- docstrings are concise, specific, and concrete;
- one sentence is preferred;
- docstrings name the contract or side effect, not the implementation mechanics;
- avoid filler such as "This function...", "Responsible for...", "Handles...", or broad LLM-style summaries;
- private helpers get docstrings only when they encode policy, parsing rules, external assumptions, or non-obvious behavior.

Tests are name-first:

- test function names describe behavior;
- test module docstrings are enough for file-level context;
- helper docstrings are allowed when they clarify shared fixtures or assertions;
- do not add docstrings to every test function just to satisfy lint.

## Task 1: Add the Missing Scripts Package Docstring

**Files:**

- Modify: `scripts/__init__.py`

- [x] **Step 1: Verify the current production/script docstring failure**

Run:

```bash
uv run --group dev ruff check oxipng scripts --isolated --select D --ignore D203,D212
```

Expected: one failure:

```text
D104 Missing docstring in public package
--> scripts/__init__.py:1:1
```

- [x] **Step 2: Add a concise package docstring**

Edit `scripts/__init__.py` to contain exactly:

```python
"""Automation helpers for local and CI workflows."""
```

This is intentionally short. Do not add a paragraph.

- [x] **Step 3: Verify production/script docstrings pass in isolation**

Run:

```bash
uv run --group dev ruff check oxipng scripts --isolated --select D --ignore D203,D212
```

Expected:

```text
All checks passed!
```

## Task 2: Narrow Ruff Docstring Ignores

**Files:**

- Modify: `pyproject.toml`

- [x] **Step 1: Remove broad global docstring ignores**

In `[tool.ruff.lint].ignore`, remove these entries:

```toml
    "D100", # Public package/module docs live in README/docs; file-level docstrings add noise here.
    "D104", # Package docs live in README/docs; __init__ exports are documented by stubs.
    "D107", # __init__ behavior is covered by class/function docs and type stubs.
```

Keep these entries:

```toml
    "COM812", # Formatter owns trailing-comma layout; recommended by Ruff formatter docs.
    "D203", # Incompatible with D211; Google docstring convention uses D211.
    "D212", # Incompatible with D213; Google docstring convention uses D213.
    "E501", # Ruff formatter owns line wrapping; long literals and URLs stay readable.
    "TRY003", # Small wrapper errors are clearer inline than as single-use custom exception classes.
```

- [x] **Step 2: Keep tests exempt from docstring rules**

Leave the test per-file ignore unchanged:

```toml
"tests/**/*.py" = ["ANN", "D", "PLR2004", "S101", "S108"]
```

This preserves the name-first test policy.

- [x] **Step 3: Remove `D` from script per-file ignores**

Change:

```toml
"scripts/*.py" = ["D", "S310", "S603", "T201"]
```

to:

```toml
"scripts/*.py" = ["S310", "S603", "T201"]
```

- [x] **Step 4: Update the nearby script-ignore comment**

Change the script-ignore comment to:

```toml
# Helper scripts intentionally perform URL calls, subprocess calls, and printing.
# Docstrings remain enforced because these scripts encode release and CI policy.
"scripts/*.py" = ["S310", "S603", "T201"]
```

- [x] **Step 5: Run Ruff**

Run:

```bash
uv run --group dev ruff check oxipng scripts tests
```

Expected:

```text
All checks passed!
```

## Task 3: Update Lint Deviation Documentation

**Files:**

- Modify: `docs/conventions/lint-deviations.md`

- [x] **Step 1: Remove obsolete global docstring ignores**

In the "Ruff Global Ignores" table, delete rows for:

```text
D100
D104
D107
```

Keep rows for `COM812`, `D203`, `D212`, `E501`, and `TRY003`.

- [x] **Step 2: Update script per-file ignores**

In the "Ruff Per-File Ignores" table, replace the script row with:

```markdown
| `S310`, `S603`, `T201` | `scripts/*.py` in `pyproject.toml` | Helper scripts intentionally perform URL calls, subprocess calls, and printing; docstrings remain enforced because these scripts encode release and CI policy. |
```

- [x] **Step 3: Add a docstring policy section**

Add this section after "Ruff Per-File Ignores":

```markdown
## Docstring Policy

Production Python and automation scripts are docstring-first. Public modules,
packages, classes, functions, and methods need docstrings unless a narrower
exception is documented here.

Docstrings must be concise, specific, and concrete. Prefer one sentence. Name
the contract or side effect. Avoid filler such as "This function", "Responsible
for", "Handles", and broad summaries that restate the identifier.

Tests are name-first. Test function names describe behavior, and `tests/**/*.py`
keeps `D` ignored to avoid duplicate prose. Add test helper docstrings only
when they clarify shared behavior.
```

- [x] **Step 4: Run markdown lint for the docs change**

Run:

```bash
uv run --group dev pre-commit run markdownlint-cli2 --files docs/conventions/lint-deviations.md
```

Expected:

```text
markdownlint-cli2........................................................Passed
```

## Task 4: Final Verification

**Files:**

- Verify: `scripts/__init__.py`
- Verify: `pyproject.toml`
- Verify: `docs/conventions/lint-deviations.md`

- [x] **Step 1: Verify production and scripts enforce docstrings**

Run:

```bash
uv run --group dev ruff check oxipng scripts --isolated --select D --ignore D203,D212
```

Expected:

```text
All checks passed!
```

- [x] **Step 2: Verify tests remain intentionally exempt in repo config**

Run:

```bash
uv run --group dev ruff check tests
```

Expected:

```text
All checks passed!
```

- [x] **Step 3: Verify normal Python lint**

Run:

```bash
uv run --group dev ruff check oxipng scripts tests
```

Expected:

```text
All checks passed!
```

- [x] **Step 4: Verify config and docs formatting**

Run:

```bash
uv run --group dev pre-commit run check-toml --files pyproject.toml
uv run --group dev pre-commit run markdownlint-cli2 --files docs/conventions/lint-deviations.md docs/superpowers/plans/2026-05-26-docstring-lint-policy.md
```

Expected:

```text
check toml...............................................................Passed
markdownlint-cli2........................................................Passed
```

- [x] **Step 5: Review the docstring text manually**

Check every new or changed docstring against this checklist:

```text
- one sentence unless the API contract genuinely needs more;
- names the external contract or side effect;
- avoids "This function", "Responsible for", "Handles", and generic summaries;
- does not repeat the function or module name in prose;
- no broad LLM-style run-on sentences.
```

Expected: only `scripts/__init__.py` gained a docstring, and it is:

```python
"""Automation helpers for local and CI workflows."""
```

## Task 5: Commit

**Files:**

- Add: `docs/superpowers/plans/2026-05-26-docstring-lint-policy.md`
- Modify: `scripts/__init__.py`
- Modify: `pyproject.toml`
- Modify: `docs/conventions/lint-deviations.md`

- [x] **Step 1: Inspect the diff**

Run:

```bash
git diff -- scripts/__init__.py pyproject.toml docs/conventions/lint-deviations.md docs/superpowers/plans/2026-05-26-docstring-lint-policy.md
```

Expected: the diff only changes docstring lint policy, docs, and one concise package docstring.

- [x] **Step 2: Stage the files**

Run:

```bash
git add scripts/__init__.py pyproject.toml docs/conventions/lint-deviations.md docs/superpowers/plans/2026-05-26-docstring-lint-policy.md
```

- [x] **Step 3: Commit**

Run:

```bash
git commit -m "chore: tighten docstring lint policy"
```

Expected: commit succeeds.

## Self-Review

Spec coverage:

- PEP 257-style production/script docstring enforcement is covered by Tasks 1,
  2, and 4.
- Test name-first policy is preserved by Tasks 2 and 4.
- Concise, specific, concrete docstring quality is documented by Tasks 3 and 4.
- Verification commands are explicit in Tasks 1, 2, 3, and 4.

Placeholder scan:

- No placeholder steps remain.
- Every command includes expected output.
- Every code/config change includes exact replacement text.

Type consistency:

- File paths match the current repository.
- Ruff rule names match the current `pyproject.toml`.

# Active Docs Clarity Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite active Markdown docs so they are shorter, clearer, and
accurate for current oxipng-pybind behavior.

**Architecture:** Treat active docs as the supported docs. Treat
`docs/archive/**` as historical records. Rewrite prose in small file groups.
Preserve API contracts, plan status, command blocks, warning text, and release
policy. Verify with markdownlint, diff review, and archive-preservation checks.

**Tech Stack:** Markdown, markdownlint-cli2, git diff checks, existing Python/Rust test commands when examples change.

---

## File Structure

Modify active Markdown docs only:

- `README.md`: project overview, install, API summary, development, upstream tracking.
- `docs/README.md`: documentation index.
- `docs/usage/file-optimization.md`: file optimization usage.
- `docs/usage/memory-optimization.md`: memory optimization usage.
- `docs/usage/raw-image.md`: raw image usage.
- `docs/architecture/overview.md`: architecture overview.
- `docs/architecture/api-compatibility.md`: API compatibility facts.
- `docs/architecture/options-surface.md`: option mapping facts.
- `docs/process/dependency-health.md`: dependency health process.
- `docs/process/release-artifacts.md`: release artifact process.
- `docs/process/upstream-bumps.md`: upstream bump process.
- `docs/conventions/lint-deviations.md`: lint deviation rules.
- `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`: current roadmap.
- `docs/superpowers/specs/2026-05-26-active-docs-clarity-design.md`: approved docs rewrite spec.
- `docs/superpowers/specs/2026-05-26-pyoxipng-compatibility-design.md`: active compatibility design.
- `docs/superpowers/plans/2026-05-26-docstring-lint-policy.md`: active docstring lint plan.
- `docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md`: active compatibility plan.
- `docs/superpowers/plans/2026-05-26-active-docs-clarity-rewrite.md`: this plan.

Do not edit:

- `docs/archive/**`
- `docs/api-surface/oxipng-10.1.1.toml`
- Python or Rust source files.

## Shared Rewrite Rules

Apply these rules to every active doc:

- Put the main fact or purpose first.
- Use short sentences.
- Use common words when a technical term is not needed.
- Define technical terms the first time a doc uses them.
- Prefer active voice.
- Keep one idea per paragraph.
- Keep command blocks exact.
- Keep API signatures exact.
- Keep warning text exact.
- Keep checklist state exact.
- Keep required Superpowers skill names exact.
- Do not change meaning, plan status, or release policy.
- Do not add a pyoxipng migration guide in this pass.

## Task 1: Rewrite Top-Level Docs and Usage Docs

**Files:**

- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/usage/file-optimization.md`
- Modify: `docs/usage/memory-optimization.md`
- Modify: `docs/usage/raw-image.md`

- [x] **Step 1: Read current public API facts**

Run:

```bash
sed -n '1,220p' README.md
sed -n '1,220p' docs/usage/file-optimization.md
sed -n '1,220p' docs/usage/memory-optimization.md
sed -n '1,240p' docs/usage/raw-image.md
```

Expected: API names and examples are visible before editing.

- [x] **Step 2: Rewrite `README.md`**

Rewrite `README.md` so it has these sections in this order:

- `# oxipng-pybind`
- a two-sentence project summary;
- `## Install`;
- `## Basic API`;
- `## pyoxipng Compatibility`;
- `## Development`;
- `## Upstream Tracking`;
- `## License`.

Required facts:

- The distribution name is `oxipng-pybind`.
- The import module is `oxipng`.
- Python 3.11 or newer is required for release artifacts.
- PyPI publishing is not yet enabled.
- `optimize`, `optimize_from_memory`, and `RawImage` are the main entry points.
- pyoxipng compatibility paths emit `DeprecationWarning`.
- stdin/stdout optimization is still unsupported.

- [x] **Step 3: Rewrite `docs/README.md`**

Rewrite the docs index as grouped links with these sections:

- `# oxipng-pybind Docs`
- a one-sentence starting point;
- `## Usage`;
- `## Architecture`;
- `## Process`;
- `## Project State`;
- `## Archive`.

Keep every active docs link reachable from this index.

- [x] **Step 4: Rewrite usage docs**

For each usage doc, use this shape:

- a task-focused title;
- a one-sentence purpose;
- `## Basic Use`;
- `## Options`;
- `## Errors`.

Keep examples runnable and short. Keep API names exact.

- [x] **Step 5: Verify top-level and usage docs**

Run:

```bash
uv run --group dev pre-commit run markdownlint-cli2 --files README.md docs/README.md docs/usage/file-optimization.md docs/usage/memory-optimization.md docs/usage/raw-image.md
git diff --check
```

Expected:

- markdownlint passes.
- `git diff --check` prints no whitespace errors.

- [x] **Step 6: Commit top-level and usage docs**

Run:

```bash
git add README.md docs/README.md docs/usage/file-optimization.md docs/usage/memory-optimization.md docs/usage/raw-image.md
git commit -m "docs: simplify public usage docs"
```

Expected: commit succeeds.

## Task 2: Rewrite Architecture and Process Docs

**Files:**

- Modify: `docs/architecture/overview.md`
- Modify: `docs/architecture/api-compatibility.md`
- Modify: `docs/architecture/options-surface.md`
- Modify: `docs/process/dependency-health.md`
- Modify: `docs/process/release-artifacts.md`
- Modify: `docs/process/upstream-bumps.md`
- Modify: `docs/conventions/lint-deviations.md`

- [x] **Step 1: Read current architecture and process docs**

Run:

```bash
sed -n '1,220p' docs/architecture/overview.md
sed -n '1,180p' docs/architecture/api-compatibility.md
sed -n '1,180p' docs/architecture/options-surface.md
sed -n '1,180p' docs/process/dependency-health.md
sed -n '1,180p' docs/process/release-artifacts.md
sed -n '1,180p' docs/process/upstream-bumps.md
sed -n '1,180p' docs/conventions/lint-deviations.md
```

Expected: current facts are visible before editing.

- [x] **Step 2: Rewrite architecture docs**

Use these purposes:

- `overview.md`: explain package layers and data flow.
- `api-compatibility.md`: explain stable API, compatibility paths, and unsupported paths.
- `options-surface.md`: explain how Python options map to upstream `oxipng`.

Required facts:

- Stable API calls must remain warning-free.
- pyoxipng compatibility paths emit `DeprecationWarning`.
- Compatibility paths are unsupported migration paths.
- The Rust extension owns validation for native options.
- Python wrappers own ergonomic names and path handling.

- [x] **Step 3: Rewrite process and convention docs**

Use these purposes:

- `dependency-health.md`: explain scheduled and manual dependency checks.
- `release-artifacts.md`: explain wheel artifact checks.
- `upstream-bumps.md`: explain upstream `oxipng` version checks.
- `lint-deviations.md`: explain how to document lint exceptions.

Keep commands exact. Keep policy facts unchanged.

- [x] **Step 4: Verify architecture and process docs**

Run:

```bash
uv run --group dev pre-commit run markdownlint-cli2 --files docs/architecture/overview.md docs/architecture/api-compatibility.md docs/architecture/options-surface.md docs/process/dependency-health.md docs/process/release-artifacts.md docs/process/upstream-bumps.md docs/conventions/lint-deviations.md
git diff --check
```

Expected:

- markdownlint passes.
- `git diff --check` prints no whitespace errors.

- [x] **Step 5: Commit architecture and process docs**

Run:

```bash
git add docs/architecture/overview.md docs/architecture/api-compatibility.md docs/architecture/options-surface.md docs/process/dependency-health.md docs/process/release-artifacts.md docs/process/upstream-bumps.md docs/conventions/lint-deviations.md
git commit -m "docs: simplify architecture and process docs"
```

Expected: commit succeeds.

## Task 3: Rewrite Roadmap and Active Superpowers Docs

**Files:**

- Modify: `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`
- Modify: `docs/superpowers/specs/2026-05-26-active-docs-clarity-design.md`
- Modify: `docs/superpowers/specs/2026-05-26-pyoxipng-compatibility-design.md`
- Modify: `docs/superpowers/plans/2026-05-26-docstring-lint-policy.md`
- Modify: `docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md`
- Modify: `docs/superpowers/plans/2026-05-26-active-docs-clarity-rewrite.md`

- [x] **Step 1: Read roadmap and active Superpowers docs**

Run:

```bash
sed -n '1,260p' docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md
sed -n '1,180p' docs/superpowers/specs/2026-05-26-active-docs-clarity-design.md
sed -n '1,220p' docs/superpowers/specs/2026-05-26-pyoxipng-compatibility-design.md
sed -n '1,220p' docs/superpowers/plans/2026-05-26-docstring-lint-policy.md
sed -n '1,260p' docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md
```

Expected: current plan state and completed checkboxes are visible before editing.

- [x] **Step 2: Rewrite the current roadmap**

Rewrite `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md` to make these facts easy to find:

- CI and release workflow status.
- Completed pyoxipng compatibility paths.
- Remaining pyoxipng gaps.
- Recommended next order.

Keep the meaning of open work unchanged.

- [x] **Step 3: Simplify active specs**

Rewrite active specs for clarity while keeping approved scope unchanged.

For the active docs clarity spec, preserve:

- active doc scope;
- archive exclusion;
- writing rules;
- accuracy rules;
- success criteria;
- verification.

For the pyoxipng compatibility spec, preserve:

- warning-emitting unsupported compatibility path;
- no stable API behavior changes;
- concise docstring policy;
- remaining migration expectations.

- [x] **Step 4: Simplify active plans**

Rewrite active plan prose only. Preserve:

- task order;
- command blocks;
- expected outputs;
- checklist state;
- required skill names;
- warning text;
- code snippets;
- commit commands.

Do not change completed boxes to open boxes or open boxes to completed boxes.

- [x] **Step 5: Verify roadmap and active Superpowers docs**

Run:

```bash
uv run --group dev pre-commit run markdownlint-cli2 --files docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/specs/2026-05-26-active-docs-clarity-design.md docs/superpowers/specs/2026-05-26-pyoxipng-compatibility-design.md docs/superpowers/plans/2026-05-26-docstring-lint-policy.md docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md docs/superpowers/plans/2026-05-26-active-docs-clarity-rewrite.md
git diff --check
```

Expected:

- markdownlint passes.
- `git diff --check` prints no whitespace errors.

- [x] **Step 6: Commit roadmap and active Superpowers docs**

Run:

```bash
git add docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/specs/2026-05-26-active-docs-clarity-design.md docs/superpowers/specs/2026-05-26-pyoxipng-compatibility-design.md docs/superpowers/plans/2026-05-26-docstring-lint-policy.md docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md docs/superpowers/plans/2026-05-26-active-docs-clarity-rewrite.md
git commit -m "docs: simplify roadmap and active plans"
```

Expected: commit succeeds.

## Task 4: Final Verification and Review

**Files:**

- Verify: active Markdown docs.
- Verify: `docs/archive/**` is not rewritten.
- Verify: git diff and recent commits.

- [x] **Step 1: Run full docs verification**

Run:

```bash
uv run --group dev pre-commit run markdownlint-cli2 --files README.md docs/README.md docs/architecture/overview.md docs/architecture/api-compatibility.md docs/architecture/options-surface.md docs/conventions/lint-deviations.md docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/process/dependency-health.md docs/process/release-artifacts.md docs/process/upstream-bumps.md docs/superpowers/specs/2026-05-26-active-docs-clarity-design.md docs/superpowers/specs/2026-05-26-pyoxipng-compatibility-design.md docs/superpowers/plans/2026-05-26-docstring-lint-policy.md docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md docs/superpowers/plans/2026-05-26-active-docs-clarity-rewrite.md docs/usage/file-optimization.md docs/usage/memory-optimization.md docs/usage/raw-image.md
git diff --check
```

Expected:

- markdownlint passes.
- `git diff --check` prints no whitespace errors.

- [x] **Step 2: Confirm archive files were not rewritten**

Run:

```bash
git diff --name-only origin/main...HEAD | rg '^docs/archive/' || true
```

Expected: no output, unless a deliberate archive index link correction was made.

- [x] **Step 3: Inspect final docs diff**

Run:

```bash
git diff --stat origin/main...HEAD -- README.md docs
git diff --name-only origin/main...HEAD -- README.md docs
```

Expected:

- Active Markdown docs are listed.
- `docs/api-surface/oxipng-10.1.1.toml` is not listed.
- `docs/archive/**` is not listed.

- [x] **Step 4: Commit final checklist**

Run:

```bash
git add docs/superpowers/plans/2026-05-26-active-docs-clarity-rewrite.md
git commit -m "docs: complete active docs clarity plan"
```

Expected: commit succeeds.

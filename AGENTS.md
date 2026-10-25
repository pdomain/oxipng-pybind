---
kind: process
status: active
last_verified: 2026-10-25
---
# oxipng-pybind — Agent Guidance

This project provides Python bindings for the upstream Rust `oxipng` crate
through PyO3 and maturin. It exposes the `oxipng` Python module, the native
`_oxipng` extension, and a pyoxipng compatibility layer.

This repo does not own PNG optimization logic. Keep optimizer behavior in
upstream `oxipng` unless a plan says otherwise.

## Agent Index

- **Kind:** process
- **Status:** active
- **Read when:** starting any change in this repo — bindings, build, tests,
  docs, releases, or dependency work.
- **Search terms:** oxipng-pybind agent guidance, PyO3 maturin bindings, make
  targets, commands and gates, writing and review, upstream boundary.

## Start Here

Read these files before making changes:

- `CONVENTIONS.md`
- `CONTRIBUTING.md`
- `docs/process/writing-style.md`

For larger work, also check `docs/plans/unfinished-work.md`.

Follow `docs/process/writing-style.md` for docs, reports, issue text, PR text,
and user-facing copy. Keep text short, clear, and DRY. Link to the source doc
instead of copying its details.

## Agent Rules

- Follow `CONVENTIONS.md` for API stability, upstream boundaries, errors,
  release artifacts, dependency refreshes, and license rules.
- Keep the Cargo `extension-module` feature for maturin builds. Cargo tests
  must keep working with this repo's PyO3 setup.
- Interactive agents must not create GitHub PRs from this repo.
- Work locally, verify locally, and commit locally only when asked.
- Do not push or merge without explicit user direction.
- For PRs, pull the branch, rebase it on current `main`, then use a rebase
  merge after required checks pass. See `CONTRIBUTING.md`.

## Project Docs

- `README.md` - user-facing overview and quick start.
- `docs/README.md` - docs folder meanings.
- `docs/usage/` - supported API usage and pyoxipng migration.
- `docs/architecture/` - API compatibility, options surface, and architecture.
- `docs/api-surface/` - tracked upstream `oxipng` API manifests.
- `docs/process/local-development.md` - local development workflow.
- `docs/process/dependency-health.md` - dependency refresh policy.
- `docs/process/upstream-bumps.md` - upstream `oxipng` bump automation.
- `docs/process/release-artifacts.md` - wheel and publish policy.
- `docs/process/lint-deviations.md` - documented lint exceptions.

This repo does not keep `docs/archive/`. Use Git history for old plans, specs,
and reports.

## Superpowers Redirect

When a Superpowers skill says to save to one of these paths, save to
`docs/plans/<file>.md` instead:

- `docs/superpowers/specs/<file>.md`
- `docs/superpowers/plans/<file>.md`
- `docs/specs/<file>.md`
- `docs/plans/<file>.md`

This repo keeps all current Superpowers specs and plans in `docs/plans/`.

<!-- workspace-process:start -->

## Before Coding

These workspace defaults apply to coding tasks. User-level settings or direct
conversation instructions can override them.

1. Invoke relevant Superpowers skills before starting. Use process skills
   before implementation skills.
2. Run `git status --short`. Read this file, `CONVENTIONS.md`, and
   `CONTRIBUTING.md`.
3. Check relevant `docs/` folders for plans, specs, decisions, and
   architecture.
4. For issue work, confirm the issue is open with
   `gh issue view <N> --repo <owner/repo>` and note its milestone.
5. Check open PRs and branches for work touching the same area.
6. Check `.claude/agent-memory/<repo>/feedback_*.md` for corrections that are
   not yet in `CONVENTIONS.md`.
7. Use an `Explore` subagent for broad code searches. Dispatch subagents for
   non-trivial independent work, and run independent agent calls in parallel.
8. Use the `using-git-worktrees` skill before code changes in the interactive
   checkout at `/workspaces/ocr-container/<repo>/`. Full-power implementation
   agents should use `isolation: "worktree"`. Docs agents and the `driver`
   agent may skip this when directed.
9. Write a failing test first when behavior changes or the plan calls for TDD.
10. Before committing, run focused verification plus `make ci AI=1`.
11. Commit locally only when asked. Do not push without explicit user direction.

<!-- workspace-process:end -->

<!-- >>> repo-setup:repo-facts sha256:cdde2060b7e4456a7d26183ba8331fe03ced3db0e19305c0d17f8559779c41a9 -->
## Repository Facts

Stack: Rust + Python. PyO3 0.29 and maturin expose the upstream `oxipng` crate
(pinned `=10.2.1`) to Python as a native extension.

- Rust crate `_oxipng` lives in `src/lib.rs` — `crate-type = ["cdylib",
  "rlib"]`, built with the `pyo3/extension-module` feature.
- Python package `oxipng/` holds `__init__.py` and `_pyoxipng_compat.py`, the
  pyoxipng compatibility layer.
- Build backend is maturin (`module-name = "_oxipng"`, set in
  `pyproject.toml`); Python is `>=3.10` and wheels are ABI3.
- Tests: Rust tests run under Cargo; Python tests in `tests/` need the compiled
  extension installed first.
- `oxipng/` here is this repo's binding package; the `oxipng` crate itself is
  upstream and is not vendored.
<!-- <<< repo-setup:repo-facts -->

<!-- >>> repo-setup:commands-and-gates sha256:3c759fc2e7ae0f52cc854824a009133bcc01600e734d1510fb2882bf50a030a2 -->
## Commands and Gates

Prefer Make targets; use direct `cargo`, `uv`, or `maturin` only when no target
exists. `AI=1` writes verbose output to `.ci-ai.log` and prints a concise
result or a filtered failure summary.

- `make setup AI=1` — Rust, Python deps, editable extension, and hooks.
- `make develop AI=1` — rebuild and install the editable extension.
- `make test AI=1` — Rust and Python tests (`test-rust` plus `test-py`).
- `make lint AI=1` / `make format AI=1` / `make typecheck AI=1` — lint, format,
  and basedpyright.
- `make ci AI=1` — the full local CI gate; run before committing.

Run `make help` for the full target list (`test-rust`, `test-py`, `lint-fix`,
`format-check`, `dependency-audit`, `dependency-refresh-check`,
`pre-commit-check`, `wheel`, and more).

Never run bare `python -m pytest`: Python tests need the compiled extension.
Run `make develop AI=1` first, then focused
`uv run --no-sync --group dev pytest ...`. See `CONTRIBUTING.md` and
`docs/process/local-development.md`.
<!-- <<< repo-setup:commands-and-gates -->

<!-- >>> repo-setup:writing-and-review sha256:f34103d00bec27655df57a75a5023da61ff633e35194451ed0446738dd5879e7 -->
## Writing and Review

- New durable reader-facing docs: route through the `write-readably` skill.
- Edits to existing prose: route through the `edit-for-readability` skill.
- Python changes must pass the `writing-python` mandatory gate (ruff plus
  basedpyright plus tests) on touched files.
- Adversarial review follows the consuming plugin's policy.
- Repo writing conventions live in `docs/process/writing-style.md`.
<!-- <<< repo-setup:writing-and-review -->

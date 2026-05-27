# CLAUDE.md - oxipng-pybind

This project provides Python bindings for the upstream Rust `oxipng` crate
through PyO3 and maturin. It exposes the `oxipng` Python module, the native
`_oxipng` extension, and a pyoxipng compatibility layer.

This repo does not own PNG optimization logic. Keep optimizer behavior in
upstream `oxipng` unless a plan says otherwise.

## Start Here

Read these files before making changes:

- `CONVENTIONS.md`
- `CONTRIBUTING.md`
- `docs/process/writing-style.md`

For larger work, also check `docs/plans/unfinished-work.md`.

Follow `docs/process/writing-style.md` for docs, reports, issue text, PR text,
and user-facing copy. Keep text short, clear, and DRY. Link to the source doc
instead of copying its details.

## Commands

Prefer Make targets. Use direct `cargo`, `uv`, or `maturin` commands only when
no target exists.

| target | use |
| --- | --- |
| `make setup AI=1` | set up Rust, Python deps, editable extension, and hooks |
| `make develop AI=1` | rebuild and install the editable extension |
| `make test AI=1` | run Rust and Python tests |
| `make test-rust AI=1` | run Cargo tests |
| `make test-py AI=1` | rebuild the extension and run pytest |
| `make lint AI=1` / `make lint-fix AI=1` | run or fix lint |
| `make format AI=1` / `make format-check AI=1` | format or check formatting |
| `make typecheck AI=1` | run basedpyright |
| `make dependency-audit AI=1` | run dependency audits |
| `make dependency-refresh-check AI=1` | refresh lockfiles, audit, and run CI |
| `make pre-commit-check AI=1` | run all pre-commit hooks |
| `make wheel AI=1` | build the ABI3 wheel |
| `make ci AI=1` | run the full local CI gate |

`AI=1` writes verbose output to `.ci-ai.log`. Stdout shows a concise result or
a filtered failure summary. Use the plain target only when you need full output
while debugging.

Never use bare `python -m pytest`. Python tests need the compiled extension.
Use `make test-py AI=1`, or run `make develop AI=1` before focused
`uv run --no-sync --group dev pytest ...` commands.

See `CONTRIBUTING.md` and `docs/process/local-development.md` for setup and
focused test workflows.

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

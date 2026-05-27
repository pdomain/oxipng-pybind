# CLAUDE - oxipng-pybind

Python bindings around the upstream Rust `oxipng` crate via PyO3 and maturin.
This project does not own PNG optimization logic; it exposes a stable Python
API and pyoxipng compatibility layer over upstream `oxipng`.

Distribution name: `oxipng-pybind`. Import module: `oxipng`. Native extension:
`_oxipng`.

## Commands

| target | does |
| --- | --- |
| `make setup AI=1` | install pinned Rust toolchain, sync Python deps, build editable extension, install hooks |
| `make develop AI=1` | build and install the editable extension |
| `make test AI=1` | run Rust tests and Python tests |
| `make test-rust AI=1` / `make test-py AI=1` | run Cargo tests / rebuild extension and run pytest |
| `make coverage AI=1` | run pytest with branch coverage and HTML report |
| `make lint AI=1` / `make lint-fix AI=1` | run or fix Rust, Python, and Markdown lint |
| `make format AI=1` / `make format-check AI=1` | format Rust/Python or check formatting |
| `make typecheck AI=1` | run basedpyright |
| `make dependency-audit AI=1` | run cargo-deny and the locked Python audit |
| `make dependency-refresh-check AI=1` | upgrade lockfiles, audit, and run full CI |
| `make pre-commit-check AI=1` | run all pre-commit hooks |
| `make wheel AI=1` | build optimized ABI3 wheel into `target/wheels/` |
| `make ci AI=1` | setup, hooks, lint, audits, typecheck, tests, and wheel build |
| `make clean` / `make reset` | remove generated artifacts / rebuild local environment |
| `make upgrade-deps` | upgrade Python and Rust lockfiles locally |

`AI=1` captures verbose output to `.ci-ai.log`; stdout shows a concise pass or
filtered failure summary. Use the plain target only when full command output is
needed for debugging.

`make setup` is the normal first command in a fresh checkout. See
`CONTRIBUTING.md` and the `setup` target in `Makefile` for setup details.

## Rules

- Before committing, follow the verification step in the "Before coding"
  workflow below.
- Prefer Make targets first; fall back to direct `cargo`, `uv`, or `maturin`
  commands only when no target exists.
- Never use bare `python -m pytest`. Python tests need the compiled extension;
  use `make test-py` or `make develop` before focused
  `uv run --no-sync --group dev pytest ...` commands.
- Follow `CONVENTIONS.md` for API stability, upstream `oxipng` boundaries,
  predictable errors, release artifacts, dependency refreshes, and license
  rules.
- The Cargo `extension-module` feature is for maturin builds. Keep Cargo tests
  compatible with the repository's existing PyO3 setup.
- Update `THIRD_PARTY_NOTICES.md` or generated-notice tooling whenever shipped
  dependencies change.

## Writing Style

Follow `docs/process/writing-style.md` for docs, reports, issue text, PR text,
and user-facing copy. In short: write clear text, avoid repeated ideas, link to
the better source instead of copying details, and group command steps when they
should run together.

## Project State

Core API, compatibility, CI, wheel, dependency health, and release artifact
work are mostly in place. Check the active roadmap before planning new work:

- `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`
- `docs/superpowers/plans/2026-05-27-next-work.md`

## Key Docs

- `README.md` - user-facing positioning and quick start.
- `docs/usage/` - supported API usage and pyoxipng migration guidance.
- `docs/architecture/` - API compatibility, options surface, and architecture.
- `docs/api-surface/oxipng-10.1.1.toml` - tracked upstream surface manifest.
- `docs/process/local-development.md` - local development workflow.
- `docs/process/dependency-health.md` - dependency refresh classification and
  release/no-release policy.
- `docs/process/upstream-bumps.md` - upstream `oxipng` bump automation.
- `docs/process/release-artifacts.md` - wheel policy and PyPI Trusted
  Publishing setup.
- `docs/conventions/lint-deviations.md` - documented lint exceptions.
- `docs/archive/` - completed plans and historical notes.

## GitHub Workflow

Interactive agents must not create GitHub PRs from this repository. Work
locally, verify locally, commit locally, and wait for explicit user direction
before pushing or merging. The repository uses merge commits; see
`CONTRIBUTING.md` for PR workflow.

<!-- workspace-process:start -->

## Before coding

These steps are workspace defaults for any coding task. **User-level settings
override them** - a user's own `~/.claude/CLAUDE.md`, `settings.json`, or a
direct instruction in the conversation takes precedence and may waive or
change any step below.

### Working principles

- **Use skills.** Invoke the relevant superpowers skill before starting -
  process skills first (`brainstorming`, `systematic-debugging`,
  `writing-plans`, `test-driven-development`), then implementation skills.
  If a skill applies, using it is not optional.
- **Delegate by default.** Dispatch subagents for non-trivial work: per-repo
  agents for repo changes, `Explore` for code searches. This keeps large tool
  output out of the parent context.
- **Parallelize.** Run independent tasks as concurrent subagents - multiple
  agent calls in a single message. Set `model: sonnet` on implementers and
  reviewers.

### Steps

1. **Gather local context.** Run `git status --short`, read this repo's
   `CLAUDE.md`, `CONVENTIONS.md`, and `CONTRIBUTING.md`, then consult relevant
   `docs/` folders for plans, specs, decisions, and architecture.
2. **Check live issue status.** `gh issue view <N> --repo <owner/repo>` -
   confirm it isn't already closed; note its milestone.
3. **Check for in-flight work.** Open PRs and existing branches touching the
   same area, to avoid colliding with work-in-progress.
4. **Consult agent memory.** `.claude/agent-memory/<repo>/feedback_*.md` for
   corrections not yet promoted to `CONVENTIONS.md`.
5. **Locate code with `Explore` first.** Use an `Explore` subagent to find
   relevant files before broad `Read`/grep.
6. **Isolate in a worktree.** Never work directly in the interactive checkout
   at `/workspaces/ocr-container/<repo>/`. Use the `using-git-worktrees` skill
   to set up an isolated worktree. When delegating to a full-power
   implementation agent, pass `isolation: "worktree"` on the `Agent` call
   (skip for `-docs` agents and the `driver` agent). When an agent returns a
   worktree path + branch, use the `finishing-a-development-branch` skill to
   decide how to integrate.
7. **TDD.** Write the failing test first where the plan calls for it.
8. **Verify before committing.** Focused verification plus `make ci`.
9. **Commit locally; do not push** without explicit say-so.

<!-- workspace-process:end -->

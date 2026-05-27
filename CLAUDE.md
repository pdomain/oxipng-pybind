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

`make setup` is the normal first command in a fresh checkout. It checks
`uv.lock`, installs the pinned Rust toolchain and `cargo-deny` if needed, syncs
locked Python dev dependencies, builds the editable `_oxipng` extension, and
installs Git hooks.

## Rules

- Always run focused verification plus `make ci AI=1` before committing.
- Prefer Make targets first; fall back to direct `cargo`, `uv`, or `maturin`
  commands only when no target exists.
- Never use bare `python -m pytest`. Python tests need the compiled extension;
  use `make test-py` or `make develop` before focused
  `uv run --no-sync --group dev pytest ...` commands.
- Keep the wrapper API stable. Add compatibility paths deliberately, document
  deprecations, and preserve predictable Python exception behavior.
- Rust code should bind upstream `oxipng`; do not fork or reimplement PNG
  optimizer algorithms here.
- The Cargo `extension-module` feature is for maturin builds. Keep Cargo tests
  compatible with the repository's existing PyO3 setup.
- Update `THIRD_PARTY_NOTICES.md` or generated-notice tooling whenever shipped
  dependencies change.
- No GPL/LGPL dependencies without an explicit licensing decision.
- Release wheels target Python 3.11+ ABI3. Current expected hosted targets are
  Linux x86_64, Linux aarch64, macOS x86_64, macOS arm64, and Windows x86_64.
- PyPI publishing uses Trusted Publishing from `wheels.yml` on protected `v*`
  tags after aggregated wheel verification. Do not add password or API-token
  publishing secrets.
- Dependency refresh automation labels PRs as `release-needed` or
  `no-release-needed`. Tooling-only lockfile refreshes may auto-merge after
  checks; release-affecting refreshes need explicit release/version attention.

## Writing Style

- Write at about a 7th grade English level.
- Make docs, reports, and user-facing text easy for ESL readers to follow.
- Use short, clear sentences.
- Avoid long chains of clauses.
- Do not use parenthetical em dashes.
- Use parentheses rarely.
- Prefer parentheses for first-time acronym write-outs, such as
  `CI (continuous integration)`.
- Link standard library types and tools to official docs when the link helps.
  Link only the first instance per doc.
- When no public docs page exists, link to source code when practical.
  Use this for local API contracts and generated behavior.
- Use line anchors for local source links when practical.
- Link related external project pages when helpful.
- Do not deep-link into external project code unless it is needed.
- Prefer direct wording over dense or tedious prose.
- When writing docs, reports, issue text, PR text, or user-facing copy, read
  `docs/process/writing-style.md`.

## Project State

The supported API is implemented for files, memory buffers, raw pixel data, and
analysis. Type stubs, runtime docstrings, pyoxipng migration docs, upstream API
surface scanning, CI, API matrix, wheel matrix, dependency health automation,
and release artifact verification are in place.

Active roadmap:

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
before pushing or merging. If a PR is needed, the user opens it unless they
explicitly direct otherwise.

The repository uses merge commits, not squash merges.

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

1. **Check the working tree.** `git status --short`. Surface or resolve stray
   uncommitted work before starting - don't build on it.
2. **Read repo guidance.** This repo's `CLAUDE.md` and `CONVENTIONS.md` for
   repo-specific rules. Read `CONTRIBUTING.md` for contributor workflow.
3. **Consult `docs/` for authoritative context** (whichever folders exist):
   `plans/` (the work plan), `specs/` (design specs - follow any `Spec:`
   pointer from the issue), `research/` (prior investigations), `decisions/`
   (ADRs / constraints), `architecture/` (shipped design).
4. **Check live issue status.** `gh issue view <N> --repo <owner/repo>` -
   confirm it isn't already closed; note its milestone.
5. **Check for in-flight work.** Open PRs and existing branches touching the
   same area, to avoid colliding with work-in-progress.
6. **Consult agent memory.** `.claude/agent-memory/<repo>/feedback_*.md` for
   corrections not yet promoted to `CONVENTIONS.md`.
7. **Locate code with `Explore` first.** Use an `Explore` subagent to find
   relevant files before broad `Read`/grep.
8. **Isolate in a worktree.** Never work directly in the interactive checkout
   at `/workspaces/ocr-container/<repo>/`. Use the `using-git-worktrees` skill
   to set up an isolated worktree. When delegating to a full-power
   implementation agent, pass `isolation: "worktree"` on the `Agent` call
   (skip for `-docs` agents and the `driver` agent). When an agent returns a
   worktree path + branch, use the `finishing-a-development-branch` skill to
   decide how to integrate.
9. **TDD.** Write the failing test first where the plan calls for it.
10. **Verify before committing.** Focused verification plus `make ci`.
11. **Commit locally; do not push** without explicit say-so.

<!-- workspace-process:end -->

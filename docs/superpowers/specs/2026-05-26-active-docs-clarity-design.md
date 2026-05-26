# Active Docs Clarity Design

## Goal

Rewrite active documentation so it is clear, concise, and easy to scan.

The target reader can use Python, run shell commands, and read basic API
examples. The prose should stay near a 10th-grade reading level.

## Scope

Rewrite active Markdown docs:

- `README.md`
- `docs/README.md`
- `docs/architecture/*.md`
- `docs/conventions/*.md`
- `docs/process/*.md`
- `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`
- `docs/superpowers/plans/*.md`
- `docs/superpowers/specs/*.md`
- `docs/usage/*.md`

Treat `docs/archive/**` as historical records. Do not rewrite archived plans or
specs for style.

`docs/api-surface/oxipng-10.1.1.toml` is data, not prose. Do not rewrite it.

"Full rewrite" means the active docs may be restructured and simplified. It
does not mean changing facts, plan status, API contracts, or release policy.

For `docs/superpowers/**`, simplify prose around active specs and plans. Keep
task order, required skills, checklist state, command blocks, and acceptance
criteria intact.

## Writing Rules

- Use short sentences.
- Use concrete words.
- Define project terms the first time they appear.
- Prefer active voice.
- Keep one idea per paragraph.
- Keep lists parallel.
- Keep commands and API signatures exact.
- Keep warning text exact.
- Keep plan checkboxes and required skill names intact.
- Avoid filler phrases such as "responsible for", "handles", and "in order to".
- Avoid vague phrases such as "various", "proper", "robust", and "as needed"
  unless the sentence defines what they mean.

## Accuracy Rules

- Do not change API behavior.
- Do not change the meaning of implementation plans.
- Do not mark work complete unless the existing plan already marks it complete.
- Keep pyoxipng compatibility status current:
  warning-emitting compatibility paths exist, but stdin/stdout, migration-guide
  docs, and packaging/platform parity remain open.
- Keep archive references truthful. Link to archives when useful, but do not
  edit archived prose for tone.

## Rewrite Shape

Each active doc should have a clear job:

- `README.md`: quick project overview, install, API summary, development, and
  upstream tracking.
- `docs/README.md`: docs index.
- `docs/usage/*.md`: task-based examples for file, memory, and raw-image use.
- `docs/architecture/*.md`: stable design facts and compatibility decisions.
- `docs/process/*.md`: repeatable project processes.
- `docs/conventions/*.md`: local rules and exceptions.
- `docs/plans/*.md`: current roadmap and open work.
- `docs/superpowers/**`: current specs and plans for active work.

Prefer trimming over adding new prose. Add definitions only where they reduce
confusion.

## Non-Goals

- Do not edit Rust or Python source.
- Do not add new API features.
- Do not rewrite archived docs.
- Do not create a public pyoxipng migration guide in this pass.
- Do not change release or packaging policy.
- Do not make broad formatting churn outside active Markdown docs.

## Success Criteria

- A new contributor can find install, usage, API, release, and roadmap docs from
  the docs index.
- Each active doc starts with its purpose or main fact.
- Long paragraphs are split or trimmed.
- Project terms are defined before they are used in a process or architecture
  decision.
- The remaining pyoxipng parity gaps are easy to identify.
- Archive files are unchanged unless an active index link must be corrected.

## Verification

After edits:

1. Run markdownlint on touched Markdown files.
2. Run `git diff --check`.
3. Inspect the diff for accidental meaning changes.
4. Confirm `git diff --name-only` does not list rewritten files under
   `docs/archive/**`.

If a doc contains executable examples and the rewrite changes those examples,
run the focused test or command that proves the example still works.

# Active Docs Clarity Design

## Goal

Rewrite active documentation so it is clear, short, and easy to scan.

The reader can use Python, run shell commands, and read basic API examples. Keep
the prose near a 10th-grade reading level.

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

Do not rewrite `docs/archive/**`. Archive files are historical records.

Do not rewrite `docs/api-surface/oxipng-10.1.1.toml`. It is data, not prose.

A full rewrite may restructure and simplify active docs. It must not change
facts, plan status, API contracts, or release policy.

For `docs/superpowers/**`, simplify prose around active specs and plans. Keep
task order, required skills, checklist state, command blocks, and acceptance
criteria intact.

## Writing Rules

- Start with the main fact or purpose.
- Use short sentences.
- Use concrete words.
- Define project terms the first time they appear.
- Prefer active voice.
- Keep one idea per paragraph.
- Keep lists parallel.
- Keep commands and API signatures exact.
- Keep warning text exact.
- Keep plan checkboxes and required skill names intact.
- Avoid filler such as "responsible for", "handles", and "in order to".
- Avoid vague words such as "various", "proper", "robust", and "as needed"
  unless the sentence defines them.

## Accuracy Rules

- Do not change API behavior.
- Do not change implementation plan meaning.
- Do not mark work complete unless the existing plan already marks it complete.
- Keep pyoxipng status current: warning-emitting compatibility paths exist, but
  stdin/stdout, migration docs, and packaging/platform parity remain open.
- Keep archive references truthful. Link to archives when useful, but do not
  edit archived prose for tone.

## Rewrite Shape

Each active doc has one job:

- `README.md`: quick project overview, install, API summary, development, and
  upstream tracking.
- `docs/README.md`: docs index.
- `docs/usage/*.md`: task examples for file, memory, and raw-image use.
- `docs/architecture/*.md`: stable design facts and compatibility decisions.
- `docs/process/*.md`: repeatable project processes.
- `docs/conventions/*.md`: local rules and exceptions.
- `docs/plans/*.md`: current roadmap and open work.
- `docs/superpowers/**`: current specs and plans for active work.

Prefer trimming over adding prose. Add definitions only when they prevent
confusion.

## Non-Goals

- Do not edit Rust or Python source.
- Do not add API features.
- Do not rewrite archived docs.
- Do not create a public pyoxipng migration guide in this pass.
- Do not change release or packaging policy.
- Do not make broad formatting churn outside active Markdown docs.

## Success Criteria

- A new contributor can find install, usage, API, release, and roadmap docs from
  the docs index.
- Each active doc starts with its purpose or main fact.
- Long paragraphs are split or trimmed.
- Project terms are defined before use in a process or architecture decision.
- Remaining pyoxipng parity gaps are easy to find.
- Archive files are unchanged unless an active index link must be corrected.

## Verification

After edits:

1. Run markdownlint on touched Markdown files.
2. Run `git diff --check`.
3. Inspect the diff for accidental meaning changes.
4. Confirm `git diff --name-only` does not list rewritten files under
   `docs/archive/**`.

If a rewrite changes executable examples, run the focused test or command that
proves the examples still work.

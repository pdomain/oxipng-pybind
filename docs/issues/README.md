---
Status: active
Owner: pdomain
Created: 2026-07-17
Last verified: 2026-10-25
Kind: process
Level: I1
---

# Issues

## Agent Index

- **Kind:** process
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-10-25
- **Read when:** filing a bug / defect / investigation report, or looking up an
  open issue's status, evidence, or resolution.
- **Search terms:** issues folder, bug report, defect report, issue template,
  issue lifecycle, kind issue.

## Purpose

`docs/issues/` holds **governed, evidence-bearing issue reports** — bugs, silent
failures, regressions, and investigations that need a durable, citable record
(not a throwaway chat summary). Each report is a docgraph node so it is
retrievable, linkable from specs/plans/context, and carried in the repo rather
than in per-machine harness memory.

## Convention

- **Location:** `docs/issues/`
- **Filename:** `YYYY-MM-DD-short-slug.md` (creation date + a terse kebab slug).
- **Metadata:** YAML frontmatter **and** a matching `## Agent Index` block. Keep
  frontmatter `Status:` and Agent Index `Status:` identical — a mismatch trips a
  `field_conflict` (→ `status-reconciler`).
  - `Kind: issue`
  - `Level:` informational scope — `I1` repo-wide, `I2` narrow/local.
  - `Status:` governed lifecycle, **not** the issue's open/closed state (see below).
- **Issue state vs governed status:** the docgraph lifecycle is
  `draft → active → implemented → retired`. Express the *issue's* resolution state
  as a separate **`Resolution:`** line in the Agent Index (`Open` / `Resolved` /
  `Won't fix` / `Duplicate`) and a final `## Resolution` section. Map the governed
  `Status:`:
  - **Open** → `Status: active`.
  - **Resolved / Won't fix / Duplicate** → `Status: retired`, routed through
    `doc-retirer`, with the resolving commit/spec linked in `## Resolution`.
- **Link it (no orphans):** reference every new issue from a governed doc — by
  default an **Open issues** bullet in this `README`. If context docs are added,
  they can also link issues from `docs/context/intent-map.md` or
  `docs/context/current-state.md`. This repo currently has neither context file.
- **Stage + reindex:** under `mode = "git"` a new doc is invisible until
  `git add`ed; stage it, then `docgraph reindex` and `docgraph check --strict` the
  same turn (a new `dangling` blocks completion).
- **Template:** copy `TEMPLATE.md` in this folder. It is index-excluded (a
  top-of-file `<!-- docgraph: ignore -->` marker), so **do not markdown-link to
  it** from a governed doc — the link would dangle. Refer to it by path / inline
  code.

## Recommended structure

Summary · Impact · Environment/versions · Evidence (reproduction & diagnosis,
with commands/output) · Root-cause hypotheses (ranked) · Defects to fix ·
Recommended next steps · What is NOT broken (scopes the fix) · Resolution.

Lead with the **smallest decisive evidence**, separate **observation** from
**hypothesis**, and always include a **What is NOT broken** section.

## Open issues

- *None yet.*

## Resolved issues

- *None yet.*

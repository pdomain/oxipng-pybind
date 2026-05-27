# oxipng-pybind conventions

These rules apply to source code, tests, docs, scripts, and workflows in this
repo. They also guide AI agents working here.

<!-- workspace-conventions:start -->

## Rule: Do not explain obvious code

Do not add comments that repeat what the code says.

Use a comment only when the reason is not clear from the code. Good reasons
include a hidden constraint, a subtle invariant, or a workaround for a known
bug.

Docstrings should be short. Prefer one clear line. Do not add long parameter
lists unless the API docs need them.

Common violations:

- A comment above a function that repeats the function name.
- A comment like `# return the value` before a return statement.
- A long docstring that only repeats names and types.
- Section divider comment blocks in test files.

## Rule: Avoid ambiguous Unicode in code

Characters flagged by Ruff under `RUF001`, `RUF002`, or `RUF003` must be clear.

In strings and docstrings, use `\uXXXX` escapes when Ruff flags a character.
Add a short inline note that names the character.

In comments, replace the character with plain ASCII text.

Do not silence these rules with broad `noqa` entries.

## Rule: Use `uv run` for Python tools

Run Python tools through `uv run`.

Do not call bare `python`, `python3`, `pytest`, `ruff`, `pyright`, or
`pre-commit` from Make targets, scripts, hooks, or workflows.

Use project commands such as:

```bash
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev basedpyright
uv run --group dev pre-commit run --all-files
```

One-off shell use by a human is outside this rule.

## Rule: Keep active specs in `docs/specs/`

Design specs live in `docs/specs/` while the work is active.

After the work ships, move the final design record to `docs/architecture/`.
Update any links that still point to the old spec path.

## Rule: Document each lint suppression

Prefer fixing the lint issue.

If a suppression is correct, make it narrow. Add a short reason next to it.
Also record it in `docs/conventions/lint-deviations.md`.

This applies to:

- `# noqa: ...`
- `# pyright: ignore[...]`
- `# type: ignore[...]`
- Ruff `ignore` or `per-file-ignores` settings

Use basedpyright rule names for Pyright suppressions. Do not use mypy-style
codes for basedpyright.

<!-- workspace-conventions:end -->

## Repo rules

## Rule: Keep the Python API stable

The supported API is stable. Avoid breaking imports, names, signatures, return
types, or documented errors.

Compatibility paths for `pyoxipng` are allowed. Deprecate them before removal.
Document any behavior that is different from `pyoxipng`.

## Rule: Bind upstream `oxipng`

This repo wraps the upstream Rust `oxipng` crate.

Do not add new PNG optimizer algorithms here. If behavior belongs upstream,
prefer an upstream issue or patch.

## Rule: Keep errors predictable

Caller mistakes should raise normal Python exceptions such as `TypeError`,
`ValueError`, `FileNotFoundError`, or `OSError`.

PNG decode and optimization failures should raise `PngError`.

When upstream adds new Rust error variants, capture their string form if needed.
Do not break users only because a new upstream error exists.

## Rule: Treat release artifacts as a contract

Release wheels target Python 3.11+ ABI3.

The expected hosted wheel set is:

- Linux x86_64
- Linux aarch64
- macOS x86_64
- macOS arm64
- Windows x86_64

Publishing must use verified wheel artifacts. Do not publish with API-token or
password secrets. Use PyPI Trusted Publishing.

## Rule: Classify dependency refreshes

Dependency refresh PRs must show whether a release is needed.

Use these labels:

- `release-needed`
- `no-release-needed`

Tooling-only updates can auto-merge after checks pass. Runtime or published
artifact changes need release and version review.

## Rule: Keep docs easy to read

Write at about a 7th grade English level.

Use short sentences. Avoid long clause chains. Avoid parenthetical em dashes.
Use parentheses rarely.

Prefer parentheses for first-time acronym write-outs, such as
`CI (continuous integration)`.

Link standard library types and tools to official docs when the link helps.
Link only the first instance per doc.

When no public docs page exists, link to source code when practical. Use this
for local API contracts and generated behavior.

Use line anchors for local source links when practical.

Link related external project pages when helpful. Do not deep-link into
external project code unless it is needed.

When writing docs, reports, issue text, PR text, or user-facing copy, follow
`docs/process/writing-style.md`.

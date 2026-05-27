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

Run Python tools through `uv run` when no Make target fits.

Do not call bare `python`, `python3`, `pytest`, `ruff`, `pyright`, or
`pre-commit` from Make targets, scripts, hooks, or workflows. See
[Local Development](docs/process/local-development.md) for focused test
commands.

One-off shell use by a human is outside this rule.

## Rule: Keep active specs in `docs/specs/`

Design specs live in `docs/specs/` while the work is active. After the work
ships, move the final design record to `docs/architecture/` and update links
that still point to the old spec path.

## Rule: Document each lint suppression

Prefer fixing the lint issue. If a suppression is correct, make it narrow, add
a short reason next to it, and record it in
`docs/process/lint-deviations.md`.

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

Keep the Python API stable. Follow
[API Compatibility](docs/architecture/api-compatibility.md) for supported names,
pyoxipng migration paths, and deprecation behavior.

## Rule: Bind upstream `oxipng`

This repo wraps the upstream Rust `oxipng` crate.

Do not add new PNG optimizer algorithms here. If behavior belongs upstream,
prefer an upstream issue or patch.

## Rule: Keep errors predictable

Keep errors predictable. Follow the
[error mapping](docs/architecture/overview.md#error-mapping): caller mistakes
use normal Python exceptions, and PNG decode or optimization failures use
`PngError`.

## Rule: Treat release artifacts as a contract

Treat release artifacts as a contract. Follow
[Release Artifacts](docs/process/release-artifacts.md) for wheel targets,
verification, and PyPI Trusted Publishing rules.

## Rule: Classify dependency refreshes

Classify dependency refreshes. Follow
[Dependency Health](docs/process/dependency-health.md#release-classification)
for `release-needed` and `no-release-needed` rules.

## Rule: Keep docs easy to read

Follow [Writing Style](docs/process/writing-style.md) for docs, reports, issue
text, PR text, and user-facing copy.

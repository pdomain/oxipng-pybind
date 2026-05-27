# oxipng-pybind Conventions

These rules apply to source code, tests, docs, scripts, and workflows in this
repo. They also guide AI agents.

<!-- workspace-conventions:start -->

## Rule: Do not explain obvious code

Do not add comments that repeat what the code says.

Use comments for hidden constraints, subtle invariants, and known workarounds.

Keep docstrings short. Follow the docstring policy in
[Lint Deviations](docs/process/lint-deviations.md#docstring-policy).

## Rule: Avoid ambiguous Unicode in code

Make characters flagged by Ruff under `RUF001`, `RUF002`, or `RUF003` clear.

In strings and docstrings, use `\uXXXX` escapes when Ruff flags a character.
Add a short inline note that names the character.

In comments, replace the character with plain ASCII text.

Do not silence these rules with broad suppressions.

## Rule: Use `uv run` for Python tools

Run Python tools through `uv run` when no Make target fits.

Do not call bare `python`, `python3`, `pytest`, `ruff`, `pyright`, or
`pre-commit` from Make targets, scripts, hooks, or workflows. See
[Local Development](docs/process/local-development.md) for focused test
commands.

One-off human shell use is outside this rule.

## Rule: Keep plans in the right docs folder

Use the folder meanings in [docs/README.md](docs/README.md). This repo keeps
current plans in `docs/plans/` and durable design records in
`docs/architecture/`.

## Rule: Document each lint suppression

Prefer fixing the lint issue. If a suppression is correct, make it narrow, add
a short reason next to it, and record it in
`docs/process/lint-deviations.md`.

This applies to inline suppressions and config-level ignores. Use basedpyright
rule names for Pyright suppressions.

<!-- workspace-conventions:end -->

## Repo rules

## Rule: Keep the Python API stable

Follow [API Compatibility](docs/architecture/api-compatibility.md) for
supported names, pyoxipng migration paths, and deprecation behavior.

## Rule: Bind upstream `oxipng`

This repo wraps the upstream Rust `oxipng` crate.

Do not add new PNG optimizer algorithms here. If behavior belongs upstream, use
an upstream issue or patch.

## Rule: Keep errors predictable

Follow the [error mapping](docs/architecture/overview.md#error-mapping). Caller
mistakes use normal Python exceptions. PNG decode and optimization failures use
`PngError`.

## Rule: Treat release artifacts as a contract

Follow [Release Artifacts](docs/process/release-artifacts.md) for wheel
targets, verification, and PyPI Trusted Publishing rules.

## Rule: Classify dependency refreshes

Follow [Dependency Health](docs/process/dependency-health.md#release-classification)
for `release-needed` and `no-release-needed` rules.

## Rule: Keep docs easy to read

Follow [Writing Style](docs/process/writing-style.md) for docs, reports, issue
text, PR text, and user-facing copy.

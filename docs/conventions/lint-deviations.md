# Lint Deviations

This file records intentional lint and type-checking deviations. A deviation is
a rule exception that stays in the project.

Prefer fixing the underlying issue before adding an entry here. When an
exception is needed, document the rule, location, and reason.

## Ruff Global Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `COM812` | `pyproject.toml` | Ruff formatter owns trailing-comma layout. |
| `D203` | `pyproject.toml` | Incompatible with `D211`; the configured Google docstring convention uses `D211`. |
| `D212` | `pyproject.toml` | Incompatible with `D213`; the configured Google docstring convention uses `D213`. |
| `E501` | `pyproject.toml` | Ruff formatter owns line wrapping; long literals and URLs stay readable. |
| `TRY003` | `pyproject.toml` | Small wrapper errors are clearer inline than as single-use custom exception classes. |

## Ruff Per-File Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `ANN`, `D`, `PLR2004`, `S101`, `S108` | `tests/**/*.py` in `pyproject.toml` | Tests intentionally use asserts, fixtures, magic sample values, temporary paths, and descriptive test names instead of production-style docstrings and full annotations. |
| `T201` | `scripts/*.py` in `pyproject.toml` | Helper scripts intentionally print user-facing command output; docstrings remain enforced because these scripts encode release and CI policy. |

## Docstring Policy

Production Python and automation scripts are docstring-first. Public modules,
packages, classes, functions, and methods need docstrings unless this file
documents a narrower exception.

Docstrings must be concise, specific, and concrete. Prefer one sentence. Name
the contract or side effect. Avoid filler such as "This function", "Responsible
for", "Handles", and broad summaries that restate the identifier.

Tests are name-first. Test function names describe behavior, and `tests/**/*.py`
keeps `D` ignored to avoid duplicate prose. Add test helper docstrings only
when they clarify shared behavior.

## Inline Ruff Suppressions

| Rule | Location | Justification |
| --- | --- | --- |
| `S310` | reviewed `urllib.request.urlopen` calls in `scripts/*.py` | Release automation uses fixed HTTPS API endpoints with explicit timeouts. |
| `S603` | reviewed `subprocess.run` calls in `scripts/*.py` | Release automation resolves executable paths explicitly and does not use `shell=True`. |
| `PLC0415` | `scripts/bump_upstream.py` | `tomlkit` is an optional automation dependency loaded only in functions that need to edit TOML. |
| `PLR0912` | `tests/test_real_pngs.py` | The fixture keeps each Pillow PNG mode explicit so real PNG coverage remains easy to audit. |

## Basedpyright Suppressions

| Rule | Location | Justification |
| --- | --- | --- |
| `reportAny` | `pyproject.toml` | Automation scripts parse dynamic JSON/TOML and PyO3-facing tests intentionally exercise dynamic API inputs; narrowing every fixture would reduce readability without improving wrapper safety. |
| `reportExplicitAny` | `pyproject.toml` | Public tests intentionally use `Any` to prove runtime validation rejects or accepts dynamic Python values. |
| `reportUnusedCallResult` | `pyproject.toml` | Tests often call constructors only to assert validation errors, and CLI scripts call parser/writer helpers for side effects. Assigning every result to `_` adds noise. |

## Basedpyright File Suppressions

| Rule | Location | Justification |
| --- | --- | --- |
| `reportImplicitOverride` | `oxipng/_pyoxipng_compat.py` | The enum metaclass overrides `EnumType.__getattribute__` so deprecated pyoxipng names can warn on access. |
| `reportUnknownArgumentType`, `reportUnknownVariableType` | `scripts/scan_upstream_surface.py` | `tomlkit` returns dynamic TOML objects. The scanner narrows only at the comparison boundary. |
| `reportUnannotatedClassAttribute`, `reportUnknownArgumentType`, `reportUnknownLambdaType`, `reportUnusedParameter` | `tests/test_bump_upstream.py` | The tests use small fake response objects and monkeypatched callables to assert subprocess and network behavior. Full fake types would hide the behavior under test. |

## Security Advisory Ignores

No RustSec advisories are ignored. `deny.toml` keeps `[advisories].ignore` empty.

## Gitlint Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `body-is-missing` | `.gitlint` | Workspace conventional commits often use concise one-line messages; subject length, `WIP`, and body line length rules remain enforced. |

## Markdownlint Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `MD013` | `.markdownlint-cli2.jsonc` | Long URLs, command examples, tables, and generated plan excerpts are more readable unwrapped. |
| `MD033` | `.markdownlint-cli2.jsonc` | Some docs include intentional inline HTML copied from upstream or generated tooling output. |

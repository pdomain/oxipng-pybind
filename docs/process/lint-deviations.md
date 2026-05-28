# Lint Deviations

This file records intentional lint and type-check deviations.

Prefer fixing the underlying issue before adding an entry here. When an
exception is needed, document the rule, location, and reason.

## Ruff Global Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `COM812` | `pyproject.toml` | Ruff formatter owns trailing-comma layout. |
| `D203` | `pyproject.toml` | The Google docstring convention uses `D211`, which conflicts with this rule. |
| `D212` | `pyproject.toml` | The Google docstring convention uses `D213`, which conflicts with this rule. |
| `E501` | `pyproject.toml` | Ruff formatter owns line wrapping; long literals and URLs stay readable. |
| `TRY003` | `pyproject.toml` | Small wrapper errors are clearer inline than as single-use custom exception classes. |

## Ruff Per-File Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `ANN`, `D`, `PLR2004`, `S101`, `S108` | `tests/**/*.py` in `pyproject.toml` | Tests use asserts, fixtures, magic sample values, and descriptive test names instead of production-style docstrings and full annotations. |
| `T201` | `scripts/*.py` in `pyproject.toml` | Helper scripts print user-facing command output. Docstrings stay enforced because these scripts encode release and CI policy. |

## Docstring Policy

Production Python and automation scripts are docstring-first. Public modules,
packages, classes, functions, and methods need docstrings unless this file lists
a narrower exception.

Docstrings must be concise, specific, and concrete. Prefer one sentence. Name
the contract or side effect. Avoid filler such as "This function", "Responsible
for", "Handles", and broad summaries that restate the identifier.

Tests are name-first. Test function names describe behavior. Add test helper
docstrings only when they clarify shared behavior.

## Inline Ruff Suppressions

| Rule | Location | Justification |
| --- | --- | --- |
| `E402` | `scripts/classify_dependency_refresh.py`, `scripts/generate_third_party_notices.py`, `scripts/validate_release_tag.py`, and `scripts/verify_release_version.py` | Direct script execution needs to add the repo root before importing local helpers. |
| `PLC0415` | `scripts/bump_upstream.py` | `tomlkit` is an optional automation dependency loaded only in functions that need to edit TOML. |
| `PLC0415` | `scripts/smoke_wheel.py` | Pillow is imported only for 3.11+ smoke lanes so 3.10 wheel smoke can run with stdlib PNG checks. |
| `PLC0415` | `tests/conftest.py` | Pillow is optional in the Python 3.10 API matrix; fixtures fall back to stdlib PNG generation. |
| `PLR0913` | public API wrappers in `oxipng/__init__.py` | The wrapper keeps the upstream option surface as keyword parameters for pyoxipng compatibility. |
| `PLR0912` | `tests/test_real_pngs.py` | The fixture keeps each Pillow PNG mode explicit so real PNG coverage remains easy to audit. |
| `S310` | reviewed URL calls in `scripts/bump_upstream.py` and `scripts/validate_release_tag.py` | Release automation uses validated HTTPS URLs with explicit timeouts. |
| `S603` | reviewed `subprocess.run` calls in `scripts/*.py` | Automation passes argument lists directly and does not use `shell=True`. |
| `S603` | `tests/test_scripts.py` | Direct script execution regression tests use fixed interpreter and script arguments. |

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
| `reportArgumentType` | `tests/typecheck/typing_filter_options.py` | Negative typing samples intentionally pass invalid palette values to exercise static checks. |
| `reportUnknownArgumentType`, `reportUnknownVariableType` | `scripts/scan_upstream_surface.py` | `tomlkit` returns dynamic TOML objects. The scanner narrows only at the comparison boundary. |
| `reportUnannotatedClassAttribute`, `reportUnknownArgumentType`, `reportUnknownLambdaType`, `reportUnusedParameter` | `tests/test_bump_upstream.py` | The tests use small fake response objects and monkeypatched callables to assert subprocess and network behavior. Full fake types would hide the behavior under test. |

## Security Advisory Ignores

No RustSec advisories are ignored. `deny.toml` keeps
`[advisories].ignore` empty. See
[Dependency Health](dependency-health.md) before adding an advisory ignore.

## Gitlint Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `body-is-missing` | `.gitlint` | Workspace conventional commits often use concise one-line messages. Other commit-message rules remain enforced. |

## Markdownlint Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `MD013` | `.markdownlint-cli2.jsonc` | Long URLs, command examples, tables, and generated plan excerpts are more readable unwrapped. |
| `MD033` | `.markdownlint-cli2.jsonc` | Some docs include intentional inline HTML from upstream or generated tooling output. |

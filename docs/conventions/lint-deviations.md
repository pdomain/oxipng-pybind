# Lint Deviations

This file records intentional lint and type-checking deviations. Prefer fixing
the underlying issue before adding entries here.

## Ruff Global Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `COM812` | `pyproject.toml` | Ruff formatter owns trailing-comma layout. |
| `D100` | `pyproject.toml` | Public package and module docs live in README and `docs/`; file-level docstrings add noise. |
| `D104` | `pyproject.toml` | Package docs live in README and `docs/`; `__init__` exports are documented by stubs. |
| `D107` | `pyproject.toml` | Constructor behavior is covered by class/function docs and type stubs. |
| `D203` | `pyproject.toml` | Incompatible with `D211`; the configured Google docstring convention uses `D211`. |
| `D212` | `pyproject.toml` | Incompatible with `D213`; the configured Google docstring convention uses `D213`. |
| `E501` | `pyproject.toml` | Ruff formatter owns line wrapping; long literals and URLs stay readable. |
| `TRY003` | `pyproject.toml` | Small wrapper errors are clearer inline than as single-use custom exception classes. |

## Ruff Per-File Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `ANN`, `D`, `PLR2004`, `S101`, `S108` | `tests/**/*.py` in `pyproject.toml` | Tests intentionally use asserts, fixtures, magic sample values, temporary paths, and descriptive test names instead of production-style docstrings and full annotations. |
| `D`, `S310`, `S603`, `T201` | `scripts/*.py` in `pyproject.toml` | Helper scripts are small command-line tools: docs live in command/help text, subprocess and URL calls are the intended behavior, and printing is their CLI interface. |

## Inline Ruff Suppressions

| Rule | Location | Justification |
| --- | --- | --- |
| `PLC0415` | `scripts/bump_upstream.py` | `tomlkit` is an optional automation dependency loaded only in functions that need to edit TOML. |
| `PLR0912` | `tests/test_real_pngs.py` | The fixture keeps each Pillow PNG mode explicit so real PNG coverage remains easy to audit. |

## Basedpyright Suppressions

| Rule | Location | Justification |
| --- | --- | --- |
| `reportAny` | `pyproject.toml` | Automation scripts parse dynamic JSON/TOML and PyO3-facing tests intentionally exercise dynamic API inputs; narrowing every fixture would reduce readability without improving wrapper safety. |
| `reportExplicitAny` | `pyproject.toml` | Public tests intentionally use `Any` to prove runtime validation rejects or accepts dynamic Python values. |
| `reportUnusedCallResult` | `pyproject.toml` | Tests often call constructors only to assert validation errors, and CLI scripts call parser/writer helpers for side effects. Assigning every result to `_` adds noise. |

## Security Advisory Ignores

No RustSec advisories are ignored. `deny.toml` keeps `[advisories].ignore` empty.

## Gitlint Ignores

| Rule | Location | Justification |
| --- | --- | --- |
| `body-is-missing` | `.gitlint` | Workspace conventional commits often use concise one-line messages; subject length, `WIP`, and body line length rules remain enforced. |

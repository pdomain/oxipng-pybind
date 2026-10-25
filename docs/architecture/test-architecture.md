---
kind: architecture
status: built
last_verified: 2026-10-25
---
# Test Architecture

The test suite is organized as behavior contracts, one file per domain,
backed by a small set of directly-tested helper modules. Tests cover the
Python binding, automation scripts, packaging, and release policy.

The suite does not test PNG optimizer behavior. That logic, and its tests,
stay in the upstream `oxipng` crate.

## Shared helpers

`tests/helpers/` holds small, reusable helper modules. A helper gets its own
direct tests, in `tests/test_helpers_*.py`, when a bug in it could weaken many
other tests.

| Module | Owns |
| --- | --- |
| `helpers/png.py` | PNG fixture generation, structural validity, chunk and text parsing, RGBA decode and pixel-preservation checks (Pillow-gated). |
| `helpers/warnings.py` | Explicit call-site checks for absent `DeprecationWarning` and for pyoxipng compatibility warnings. |
| `helpers/automation.py` | Fake HTTP responses, `subprocess.run` recorders, executable resolvers, GitHub output assertions. |
| `helpers/artifacts.py` | Fake wheels, sdists, wheel filenames, and GitHub workflow-run dictionaries. |
| `helpers/workflows.py` | Workflow YAML loading, `on`-trigger resolution, step lookup and ordering, `uses:` ref parsing, reviewed-action allowlist checks. |

## Domain test files

Each public contract area owns a focused file, not one mixed module.

- API surface and per-entry-point behavior:
  `test_api_surface.py`, `test_optimize_file_api.py`,
  `test_optimize_memory_api.py`, `test_option_validation.py`,
  `test_pyoxipng_compat.py`, `test_raw_image_api.py`.
- PNG fidelity and executable docs examples: `test_real_pngs.py`,
  `test_docs_examples.py`.
- Automation scripts, split by domain: upstream version and release-tag
  validation, upstream bump, dependency-refresh classification, surface
  scanning, Actions update, settings audit, and third-party notices.
- Workflow and Makefile policy: `test_workflow_security.py`,
  `test_workflow_release_policy.py`, `test_workflow_automation_policy.py`, and
  Makefile-only checks in `test_makefile.py`.
- Release and build helpers, kept separate from CLI and smoke tests:
  `test_release_artifacts.py`, `test_wheel_tags.py`, `test_release_checks.py`,
  `test_release_version.py`.

`tests/typecheck/` holds fixtures for basedpyright only; they are not pytest
modules. They only work as long as basedpyright still reports unused
`pyright: ignore` comments.

## Test design principles

- Pair a clear good state with a meaningful bad state. Turn repeated
  constructor and option cases into parametrized contract tables.
- Prefer semantic assertions over full shell-string equality for workflow and
  release policy. Keep exact strings only when the exact command is the contract.
- Workflow security requires a reviewed-action allowlist, not only a 40-character
  SHA pin, because an unreviewed third-party action could still be pinned.
- Treat docs-example tests as executable examples, not a second copy of the API
  suite. Keep migration-guide warning examples, which are user-visible behavior.
- Keep stdlib-safe PNG coverage on lanes that intentionally lack Pillow.

## Verification

- Code: `tests/helpers/` (`png.py`, `warnings.py`, `automation.py`,
  `artifacts.py`, `workflows.py`)
- Tests: `tests/test_helpers_*.py`, `tests/test_*_api.py`,
  `tests/test_option_validation.py`, `tests/test_pyoxipng_compat.py`,
  `tests/test_workflow_*.py`, `tests/test_release_*.py`, `tests/test_wheel_tags.py`,
  `tests/typecheck/typing_filter_options.py`
- Verified 2026-10-25: the documented structure was checked against the
  current `tests/` tree. The mixed `test_api.py`, `test_workflows.py`, and
  `test_scripts.py` modules are gone.

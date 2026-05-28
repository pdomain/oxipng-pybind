# Test Architecture Overhaul Design

## Goal

Rebuild the test suite structure so tests read as clear behavior contracts,
share small verified helpers, and can be assigned to agents by domain.

This work must not change package behavior. It should make existing coverage
easier to understand, reduce duplicated setup, replace low-value source-string
checks when behavior checks are practical, and add high-value missing negative
tests.

## Constraints

- Work on local branch(es). Do not push to origin.
- Keep optimizer behavior in upstream `oxipng`; this repo tests the Python
  binding, automation, packaging, and release policy.
- Prefer Make targets for full verification.
- Use focused `uv run --no-sync --group dev pytest ...` commands only after
  the editable extension is built when tests import the extension.
- Preserve public API behavior unless a test exposes an actual defect.
- Keep refactors small enough for review. Each agent task should own a
  disjoint file set when possible.

## Current Test Suite Findings

The suite has valuable coverage, but several files mix unrelated contracts.

- `tests/test_api.py` is the largest pressure point. It covers API surface,
  optimizer behavior, option parsing, warnings, pyoxipng compatibility, memory
  inputs, and `RawImage` behavior in one file.
- PNG helper logic is split across `tests/conftest.py`, `tests/test_api.py`,
  and `tests/test_real_pngs.py`.
- Warning assertions repeat throughout API and docs tests.
- Automation tests repeat fake HTTP, fake subprocess, fake executable, TOML,
  Cargo metadata, and changelog setup.
- `tests/test_workflows.py` tests important workflow policy, but it mixes
  security, release, automation, docs consistency, and Makefile checks.
- `tests/test_scripts.py` mixes CLI behavior, pure-function behavior, static
  source checks, packaging policy, and smoke tests.
- Some tests assert exact source text or shell strings where a behavior or
  semantic policy assertion would be stronger.
- Some good states are only `assert output`, `assert file.read_bytes()`, or
  raw byte membership. These should become structural PNG, chunk, or pixel
  assertions when the example claims valid image output.

## Target Structure

Use shared helpers plus domain-focused test files.

### Shared Helpers

Create small helper modules under `tests/helpers/`.

- `tests/helpers/png.py`
  - Generate compact PNG fixtures.
  - Assert structural PNG validity.
  - Parse chunk names and text chunks.
  - Decode RGBA pixels when Pillow is available.
  - Assert pixel preservation for real image tests.

- `tests/helpers/warnings.py`
  - Assert no `DeprecationWarning`.
  - Assert pyoxipng compatibility warnings with the project warning phrase.
  - Keep warning checks explicit at call sites.

- `tests/helpers/automation.py`
  - Fake context-manager HTTP responses.
  - Fake `subprocess.run` recorders.
  - Fake executable resolvers.
  - GitHub output assertion helpers.

- `tests/helpers/artifacts.py`
  - Build fake wheels and sdists.
  - Build wheel filenames from distribution, version, tags, and platform.
  - Build GitHub workflow-run dictionaries.

- `tests/helpers/workflows.py`
  - Load workflow YAML.
  - Resolve the `on` trigger despite PyYAML boolean parsing.
  - Find steps by name and assert step order.
  - Parse `uses:` action refs.
  - Enforce reviewed-action allowlists.

Each helper should be narrow. Helpers that can weaken many tests, such as PNG
assertions and workflow policy assertions, need direct tests of their own.

### API Tests

Split `tests/test_api.py` into focused modules:

- `tests/test_api_surface.py`
  - Imports, supported names, signatures, runtime docstrings.

- `tests/test_optimize_file_api.py`
  - File optimization, output paths, analyze no-write behavior, backups,
    preserved attrs, path-like values, and file errors.

- `tests/test_optimize_memory_api.py`
  - `bytes`, `bytearray`, `memoryview`, rejected buffer-like objects, corrupt
    memory input, and memory-only option behavior.

- `tests/test_option_validation.py`
  - Shared option contract tables across `optimize`, `analyze`,
    `optimize_from_memory`, and `RawImage.create_optimized_png`.

- `tests/test_pyoxipng_compat.py`
  - Deprecated aliases, callable compatibility factories, warning behavior,
    and stable paths that must not warn.

- `tests/test_raw_image_api.py`
  - Stable constructor, pyoxipng constructor compatibility, palettes,
    transparency, chunk and ICC profile behavior, overflow safety, data-length
    validation, and create-time option validation.

Repeated constructor and option cases should become parametrized contract
tables. Tests should keep a clear good state and pair risky good states with
meaningful bad states.

### PNG Behavior And Docs Tests

Keep `tests/test_real_pngs.py` focused on public image fidelity.

- Preserve exact pixel equality for file and memory optimization.
- Add a small number of high-value image modes: grayscale-alpha, 16-bit,
  transparent palette, and interlaced PNG if those are supported by the test
  environment.
- Use shared helpers for PNG generation and decoding.

Clarify the purpose of `tests/test_docs_examples.py`.

- Treat docs tests as executable examples, not exhaustive API specs.
- Replace weak output assertions with structural PNG assertions.
- Use parsed chunk assertions for `tEXt` and `iCCP` examples.
- Avoid duplicating every negative case from API tests.
- Keep migration-guide warning examples because they are user-visible
  compatibility behavior.

### Automation Script Tests

Reorganize script tests by automation domain:

- Upstream version and release-tag validation.
- Upstream bump and changelog updates.
- Dependency refresh classification.
- Upstream surface scanning.
- GitHub Actions update automation.
- GitHub settings audit.
- Third-party notice generation.

Shared fake infrastructure should replace repeated local fake HTTP responses,
subprocess runners, executable resolvers, TOML writers, Cargo metadata, and
changelog setup.

High-value missing negatives include:

- Malformed HTTP and JSON responses.
- Missing `tag_name` and invalid SHAs.
- crates.io non-404 failures.
- GitHub output carriage-return injection.
- Missing executable handling.
- GitHub CLI JSON parse failures.
- Blocking upstream surface reports through CLI.

### Workflow And Makefile Policy Tests

Split `tests/test_workflows.py` by policy area:

- `tests/test_workflow_security.py`
  - Reviewed action refs, write-token boundaries, checkout credential policy,
    token containment, and permissions.

- `tests/test_workflow_release_policy.py`
  - Wheels, TestPyPI, PyPI, release-tag creation, strict tag validation, and
    release check waiting.

- `tests/test_workflow_automation_policy.py`
  - Upstream bump, dependency refresh, retry failed checks, CI gates,
    auto-merge policy, and artifact handoff.

Keep Makefile-only checks in `tests/test_makefile.py`.

The workflow security tests must enforce a reviewed-action allowlist. Requiring
a 40-character SHA is not enough because a new unreviewed third-party action
could still be pinned.

Prefer semantic assertions over full shell-string equality when the policy is
about locked dependencies, required gates, token scope, or merge method. Keep
exact strings only when the exact command is the contract.

### Release And Build Helper Tests

Keep pure release-contract tests separate from CLI and smoke tests.

- `tests/test_release_artifacts.py` owns artifact content validation.
- `tests/test_wheel_tags.py` owns pure wheel-tag validation.
- `tests/test_release_checks.py` owns required workflow-run logic.
- `tests/test_release_version.py` or release-tag tests own project/Cargo
  version consistency.
- CLI tests should stay narrow: exit code, stdout/stderr, argument parsing, and
  direct script execution where needed.

`tests/test_scripts.py` should stop owning unrelated pure-function and static
policy checks. Move those tests into focused files.

High-value missing negatives include:

- Missing artifact paths.
- Unsupported artifact suffixes.
- Invalid sdist tarballs.
- Multiple sdist roots.
- Missing `.dist-info`.
- Invalid wheel filename formats.
- CLI `--expected-python` behavior.
- Smoke wheel typing-file failures.

### Typecheck Fixtures

Move typecheck-only fixtures to `tests/typecheck/typing_filter_options.py`.
Keep that directory for files that are validated by basedpyright but are not
pytest test modules.

The value of negative type examples depends on basedpyright reporting unused
`pyright: ignore` comments. The plan should verify that this remains true.

## Agent Tasking Model

Use parallel agents only after the shared helper boundaries are defined.

Each implementation agent should get one domain and a clear write scope:

1. Shared test infrastructure.
2. API and compatibility tests.
3. PNG behavior and docs examples.
4. Automation script tests.
5. Workflow and Makefile policy tests.
6. Release and build helper tests.
7. Typecheck fixture cleanup.

Agents should not revert work from other agents. If an agent needs a helper
owned by another task, it should either wait for that helper to land or add a
small local shim that the integration pass can collapse.

The integration pass should remove duplicate helpers, check imports, and run
the final verification gates.

## Verification

Focused verification should run after each task.

- Helper-only tasks:
  - `uv run --no-sync --group dev pytest tests/helpers -v`
  - Focused tests for domains that imported the helper.

- API and PNG behavior tasks:
  - `make develop AI=1`
  - Focused `uv run --no-sync --group dev pytest ... -v`

- Automation, release, workflow, and Makefile tasks:
  - Focused `uv run --no-sync --group dev pytest tests/<target>.py -v`

Final verification should run:

- `make test-py AI=1`
- `make lint AI=1`
- `make typecheck AI=1`
- `make ci AI=1` before final review, unless the environment blocks it.

## Risks

- A full overhaul creates review churn. Keep commits per domain.
- Helper extraction can hide weak assertions. Test important helpers directly.
- Exact workflow and release text is sometimes intentional. Replace exact
  checks only when a semantic assertion still protects the contract.
- Docs example tests should not become a second copy of all API tests.
- Pixel tests may depend on Pillow availability. Keep stdlib-safe coverage
  where Python 3.10 lanes intentionally lack Pillow.

## Non-Goals

- Do not change optimizer behavior.
- Do not change public API behavior.
- Do not push branches to origin.
- Do not rewrite release automation logic unless a test gap exposes a real
  defect that must be fixed.
- Do not add broad test volume without a clear behavior contract.

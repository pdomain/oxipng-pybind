# Security Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Fix every actionable issue from
`docs/security-code-review-report-2026-05-26.md` and leave any non-code residual risk
explicitly documented.

**Architecture:** Apply small, targeted hardening changes in the existing files without
reshaping the package. Behavior changes get tests first. Process/security-policy changes
are enforced with focused static tests or workflow/docs updates where runtime tests are
not practical.

**Tech Stack:** Rust/PyO3, Python 3.11+, pytest, Ruff, basedpyright, Cargo, cargo-deny,
GitHub Actions, markdownlint.

---

## Coverage Map

- Finding 1: Task 1 pins GitHub Actions and keeps write-token auto-merge gated by CI.
- Finding 2: Task 2 hardens `Makefile` bootstrap.
- Finding 3: Task 1 gates native dependency auto-merge on CI and wheel checks.
- Finding 4: Task 7 adds untrusted-input guidance and resource-limit tests.
- Finding 5: Task 3 includes third-party notices in package metadata and wheel smoke.
- Finding 6: Task 4 maps file I/O failures to Python I/O exceptions.
- Finding 7: Task 5 hardens wheel filename validation.
- Finding 8: Task 3 hardens wheel typing-file smoke checks.
- Finding 9: Task 6 validates upstream versions and GitHub output values.
- Finding 10: Task 2 narrows Ruff script security ignores.
- Finding 11: Task 6 fixes same-line upstream field parsing.
- Finding 12: Task 2 removes unconstrained tar extraction for `cargo-deny`.
- Finding 13: Task 6 adds deterministic dependency audit coverage.
- Finding 14: Task 4 narrows bytes-like runtime support to the documented contract.
- Finding 15: Task 8 documents Python-only `RowFilter` compatibility surface.
- Finding 16: Task 4 adds `preserve_attrs` behavioral coverage.
- Finding 17: Task 4 adds ICC profile behavioral coverage.
- Finding 18: Task 4 adds negative timeout tests.
- Finding 19: Task 8 fixes partial docs examples and adds docs example coverage.
- Finding 20: Task 4 adds memory/raw file-only option rejection tests.
- Finding 21: Task 4 rejects `bool` for `RawImage` numeric fields.
- Finding 22: Task 4 propagates non-`AttributeError` `.value` property errors.
- Finding 23: Task 2 removes unused license allowances.
- Finding 24: Task 8 aligns Python 3.14 classifier with CI coverage.

## Task 1: Harden GitHub Write-Token Workflows

**Files:**

- Modify: `.github/workflows/upstream-bump.yml`
- Modify: `.github/workflows/dependency-health.yml`
- Modify: `docs/process/upstream-bumps.md`
- Modify: `docs/process/dependency-health.md`
- Test: `tests/test_workflows.py`

- [x] **Step 1: Add static workflow-policy tests**

Add `tests/test_workflows.py` with tests that parse workflow text and assert:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_write_token_workflows_pin_create_pull_request_to_sha() -> None:
    for relative in (
        ".github/workflows/upstream-bump.yml",
        ".github/workflows/dependency-health.yml",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "peter-evans/create-pull-request@" in text
        for line in text.splitlines():
            if "peter-evans/create-pull-request@" in line:
                ref = line.rsplit("@", 1)[1].strip()
                assert len(ref) == 40
                assert all(char in "0123456789abcdef" for char in ref)


def test_upstream_bump_auto_merge_is_gated_by_ci_and_wheels() -> None:
    text = (ROOT / ".github/workflows/upstream-bump.yml").read_text(encoding="utf-8")
    assert "Run CI before opening PR" in text
    assert "Wait for wheel workflow" in text
    assert "gh pr merge" in text
    assert "--auto" in text
    assert text.index("Wait for wheel workflow") < text.index("Enable auto-merge")


def test_upstream_bump_docs_describe_ci_gated_auto_merge() -> None:
    text = (ROOT / "docs/process/upstream-bumps.md").read_text(encoding="utf-8").lower()
    assert "auto-merge" in text
    assert "ci and wheel checks pass" in text
    assert "human review is required" not in text
```

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py -v -ra
```

Expected: failures for mutable `peter-evans/create-pull-request@v6` and missing
CI-gated auto-merge.

- [x] **Step 3: Pin write-token action refs and preserve gated auto-merge**

Resolve the current SHA for `peter-evans/create-pull-request@v6`:

```bash
git ls-remote https://github.com/peter-evans/create-pull-request.git refs/tags/v6
```

Replace `@v6` in both workflows with the 40-character SHA. In
`.github/workflows/upstream-bump.yml`, keep `Enable auto-merge` after the wheel
workflow wait step and document that auto-merge is enabled only after required CI and
wheel checks pass. In `.github/workflows/dependency-health.yml`, enable auto-merge for
refresh PRs after branch protection checks pass.

- [x] **Step 4: Update process docs**

Update upstream-bump docs to say native dependency bump PRs auto-merge when CI and wheel
checks pass. Update dependency-health docs to say lockfile refresh PRs auto-merge after
audits and CI pass. Remove statements that mutable tags are accepted future work.

- [x] **Step 5: Verify workflow policy tests pass**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py -v -ra
```

Expected: all tests pass.

## Task 2: Harden Bootstrap, Lint Policy, and License Policy

**Files:**

- Modify: `Makefile`
- Modify: `pyproject.toml`
- Modify: `deny.toml`
- Modify: `docs/process/local-development.md`
- Modify: `docs/conventions/lint-deviations.md`
- Test: `tests/test_makefile.py`
- Test: `tests/test_scripts.py`

- [x] **Step 1: Add failing tests for bootstrap and lint policy**

Extend `tests/test_makefile.py`:

```python
from pathlib import Path


def test_bootstrap_preserves_rustup_shell_installer_for_developer_convenience() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    assert "https://sh.rustup.rs | sh" in makefile
    assert "rustup-init" not in makefile
    assert "sha256sum -c" not in makefile


def test_github_ci_installs_rust_before_make_ci() -> None:
    workflow_dir = Path(".github/workflows")

    for workflow in workflow_dir.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        if "make ci" not in text:
            continue

        assert "dtolnay/rust-toolchain@" in text, workflow
        assert text.index("dtolnay/rust-toolchain@") < text.index("make ci"), workflow


def test_bootstrap_installs_cargo_deny_through_cargo_install() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    assert "cargo install --locked cargo-deny" in makefile
    assert "tar -xzf" not in makefile
    assert "find \"$$tmp_dir\"" not in makefile
```

Add a static test in `tests/test_scripts.py`:

```python
def test_script_security_ignores_are_line_scoped() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"scripts/*.py" = ["S310", "S603", "T201"]' not in pyproject
    assert "# noqa: S310" in Path("scripts/bump_upstream.py").read_text(encoding="utf-8")
    assert "# noqa: S603" in Path("scripts/bump_upstream.py").read_text(encoding="utf-8")
```

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_makefile.py tests/test_scripts.py -v -ra
```

Expected: new tests capture the bootstrap policy and lint policy.

- [x] **Step 3: Update `Makefile` bootstrap**

Keep the Rustup shell installer for local developer convenience, and enforce that GitHub
workflows install Rust before running `make ci`. Replace the GitHub tarball
download/extract with:

```make
cargo install --locked cargo-deny --version $(CARGO_DENY_VERSION)
```

Keep the pinned Rust toolchain install.

- [x] **Step 4: Narrow Ruff ignores**

Remove `S310` and `S603` from the `scripts/*.py` per-file ignore list. Add targeted
`# noqa: S310` on the reviewed GitHub API `urlopen` line and targeted `# noqa: S603` on
the reviewed `subprocess.run` calls that execute resolved binary paths without `shell`.
Keep `T201` as a per-file script ignore.

- [x] **Step 5: Remove unused license allowances**

Remove `BSD-2-Clause`, `BSD-3-Clause`, and `ISC` from `deny.toml` unless current
`cargo deny check` needs them.

- [x] **Step 6: Update docs**

Document that Rust must be installed by the developer or CI image before running
`make bootstrap-rust`, and document the narrower script lint exception policy.

- [x] **Step 7: Verify tests and policy checks**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_makefile.py tests/test_scripts.py -v -ra
uv run --group dev ruff check Makefile scripts tests pyproject.toml
cargo deny check
```

Expected: tests pass; Ruff passes; cargo-deny has no unused license allowance warnings.

## Task 3: Package Third-Party Notices and Harden Wheel Smoke Checks

**Files:**

- Modify: `pyproject.toml`
- Modify: `THIRD_PARTY_NOTICES.md`
- Modify: `scripts/smoke_wheel.py`
- Test: `tests/test_scripts.py`

- [x] **Step 1: Add tests for packaged notices and release-wheel typing checks**

Add tests that assert `THIRD_PARTY_NOTICES.md` is included in `license-files`, that the
notice file mentions runtime Rust dependencies, and that release smoke checks do not use
the editable `.pth` fallback unless explicitly allowed.

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -v -ra
```

Expected: failures for missing package metadata and permissive smoke fallback.

- [x] **Step 3: Update package metadata and notices**

Add `THIRD_PARTY_NOTICES.md` to `license-files`. Expand the notices to cover runtime
Rust dependency families present in `cargo tree`: PyO3, indexmap, oxipng, libdeflater,
zopfli, rayon/crossbeam, rgb/bytemuck, and associated transitive crates.

- [x] **Step 4: Harden smoke wheel typing check**

Change `scripts/smoke_wheel.py` so release mode requires `oxipng/__init__.pyi` and
`oxipng/py.typed` in `importlib.metadata.files("oxipng-pybind")`. Allow source-tree
fallback only when an explicit `--allow-editable` flag is passed.

- [x] **Step 5: Verify focused tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -v -ra
```

Expected: all tests pass.

## Task 4: Fix Native Binding Runtime Behavior and API Tests

**Files:**

- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`
- Modify: `docs/architecture/overview.md`
- Test: `tests/test_api.py`
- Test: `tests/test_real_pngs.py`

- [x] **Step 1: Add failing API tests**

Add focused tests for:

- missing input and missing output parent raising `OSError`/`FileNotFoundError`;
- `RawImage` rejecting `bool` for width, height, bit depth, palette samples, and
  transparent values;
- custom `.value` property exceptions being propagated;
- generic `array.array("B")` and custom `.tobytes()` objects being rejected if narrowing
  runtime support;
- `preserve_attrs=True` preserving output metadata;
- `add_icc_profile()` producing an `iCCP` chunk;
- `timeout=-1` rejection for `optimize_from_memory`, `analyze`, and raw image output;
- file-only option rejection for `optimize_from_memory` and raw image output.

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py tests/test_real_pngs.py -v -ra
```

Expected: new tests fail on current behavior.

- [x] **Step 3: Map file I/O errors to Python I/O exceptions**

Change `map_png_error` to distinguish upstream read/write failures and return
`PyOSError::new_err(error)` for contained `io::Error` values. Preserve `PngError` for
decode/optimization failures.

- [x] **Step 4: Reject bool numeric values**

Add helper extraction functions that check `value.is_instance_of::<PyBool>()` before
extracting `u32`, `u16`, or `u8`. Use them for width, height, bit depth, transparency,
and palette samples.

- [x] **Step 5: Propagate `.value` property errors**

Change enum-like string parsing to treat only `AttributeError` as absent. Do not swallow
other Python exceptions and do not run the property probe twice for filters.

- [x] **Step 6: Narrow bytes-like support**

Keep accepted runtime support aligned with `BytesLike = bytes | bytearray | memoryview`.
Remove the arbitrary `.tobytes()` fallback. If `PyBuffer<u8>` is still used for
memoryview, reject non-memoryview buffers or update docs/stubs instead; this plan chooses
rejection for accidental API minimization.

- [x] **Step 7: Verify focused API tests**

Run:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py tests/test_real_pngs.py -v -ra
```

Expected: all focused tests pass.

## Task 5: Harden Wheel Tag Validation

**Files:**

- Modify: `scripts/check_wheel_tags.py`
- Modify: `pyproject.toml`
- Test: `tests/test_wheel_tags.py`

- [x] **Step 1: Add failing wheel validation tests**

Add tests for wrong distribution name, wrong version, nonexistent wheel path, and extra
wheel artifacts.

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_wheel_tags.py -v -ra
```

Expected: new tests fail.

- [x] **Step 3: Implement robust wheel filename parsing**

Add `packaging>=24` to the test/build tooling group if needed. Use
`packaging.utils.parse_wheel_filename` to validate normalized project name
`oxipng-pybind`, version from `pyproject.toml`, Python tag `cp311`, ABI `abi3`, platform
matches the expected target, path exists, and the wheel count is exactly expected.

- [x] **Step 4: Verify wheel tag tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_wheel_tags.py -v -ra
```

Expected: all tests pass.

## Task 6: Harden Release Automation and Surface Scanning

**Files:**

- Modify: `scripts/bump_upstream.py`
- Modify: `scripts/scan_upstream_surface.py`
- Modify: `Makefile`
- Modify: `docs/process/dependency-health.md`
- Test: `tests/test_bump_upstream.py`
- Test: `tests/test_scan_upstream_surface.py`
- Test: `tests/test_makefile.py`

- [x] **Step 1: Add failing tests**

Add tests for:

- rejecting upstream tags that are not strict `v?MAJOR.MINOR.PATCH`;
- rejecting GitHub output names/values containing newlines;
- parsing same-line Rust public struct fields;
- Makefile exposing a lockfile-based Python audit target.

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_bump_upstream.py tests/test_scan_upstream_surface.py tests/test_makefile.py -v -ra
```

Expected: new tests fail.

- [x] **Step 3: Implement validation and parser fixes**

Add strict upstream version validation. Add newline rejection in `emit_github_output`.
Change `parse_struct_fields` to collect every public field match in the declaration
block, not just the first match per line.

- [x] **Step 4: Add deterministic Python dependency audit path**

Add a `py-audit-lock` or equivalent Make target that exports/audits deterministic locked
dependency inputs. Wire `dependency-audit` to include it or document clearly if local and
lockfile audits are separate targets.

- [x] **Step 5: Verify focused automation tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_bump_upstream.py tests/test_scan_upstream_surface.py tests/test_makefile.py -v -ra
```

Expected: all tests pass.

## Task 7: Document and Test Untrusted Input Resource Controls

**Files:**

- Modify: `README.md`
- Modify: `docs/usage/memory-optimization.md`
- Modify: `docs/usage/file-optimization.md`
- Test: `tests/test_api.py`

- [x] **Step 1: Add tests for `max_decompressed_size` enforcement**

Add a small API test that passes an unrealistically tiny `max_decompressed_size` to a
valid PNG and asserts a `PngError` or appropriate failure from upstream.

- [x] **Step 2: Run test and confirm behavior**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -k max_decompressed_size -v -ra
```

Expected: test passes if upstream already enforces the limit, otherwise fails and guides
implementation/documentation adjustment.

- [x] **Step 3: Add untrusted input docs**

Add concise guidance to README and usage docs recommending `timeout` and
`max_decompressed_size` for attacker-controlled PNGs. Explain that defaults preserve
upstream behavior and do not impose a decompression cap.

- [x] **Step 4: Verify docs lint and focused tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -k max_decompressed_size -v -ra
uv run --group dev pre-commit run markdownlint-cli2 --files README.md docs/usage/memory-optimization.md docs/usage/file-optimization.md
```

Expected: tests and markdown lint pass.

## Task 8: Align Public Docs, API Surface Metadata, and Python Version Metadata

**Files:**

- Modify: `pyproject.toml`
- Modify: `docs/api-surface/oxipng-10.1.1.toml`
- Modify: `docs/usage/raw-image.md`
- Modify: `docs/usage/pyoxipng-migration.md`
- Test: `tests/test_scripts.py`
- Test: `tests/test_api.py`

- [x] **Step 1: Add static tests for docs/API metadata**

Add tests that assert:

- Python 3.14 classifier exists if `.github/workflows/api-matrix.yml` includes 3.14;
- the API surface manifest includes a Python compatibility section for public facade
  `RowFilter` aliases;
- docs snippets with placeholder variables mark them explicitly or are self-contained.

- [x] **Step 2: Run tests and confirm they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py tests/test_api.py -v -ra
```

Expected: metadata/docs tests fail initially.

- [x] **Step 3: Update metadata and docs**

Add `Programming Language :: Python :: 3.14` if CI support remains. Add a
Python-compatibility section to the manifest for `RowFilter` facade aliases. Make partial
examples self-contained or mark placeholders with comments.

- [x] **Step 4: Verify tests and docs lint**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py tests/test_api.py -v -ra
uv run --group dev pre-commit run markdownlint-cli2 --files docs/api-surface/oxipng-10.1.1.toml docs/usage/raw-image.md docs/usage/pyoxipng-migration.md pyproject.toml
```

Expected: tests pass; markdown lint ignores TOML or reports only Markdown files.

## Task 9: Final Verification and Report Closure

**Files:**

- Modify: `docs/security-code-review-report-2026-05-26.md`
- Modify: this plan file

- [x] **Step 1: Run full verification**

Run:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test
uv run --group dev ruff check .
uv run --group dev basedpyright
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest -v -ra
cargo deny check
uv run --group dev pip-audit --local
uv run --group dev pre-commit run markdownlint-cli2 --all-files
```

Expected: all commands pass. `pip-audit` may still skip the local unpublished package.

- [x] **Step 2: Mark findings fixed or intentionally residual**

Update `docs/security-code-review-report-2026-05-26.md` with a short resolution appendix
mapping every finding to its fix commit/file change or residual documented risk.

- [x] **Step 3: Verify no finding was skipped**

Check the coverage map in this plan against the report headings and update any missing
mapping before final response.

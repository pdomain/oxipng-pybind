# Security and Code Review Report - 2026-05-26

Scope: full repository review of `oxipng-pybind`, including Rust/PyO3 binding code,
Python facade and stubs, packaging metadata, release/build automation, tests, docs,
lockfiles, dependency policy, and GitHub workflows.

Review method:

- Four parallel subagent reviews split across native binding safety, automation and
  supply chain, docs/API/test contracts, and whole-repo cross-checks.
- Local static inspection and test/audit commands run from the repository root.
- CodeRabbit CLI was checked but could not run because agent authentication requires
  `--api-key` in this environment.

## Summary

No critical issues were found.

Medium-severity findings:

- Mutable GitHub Actions refs are used in workflows with write-scoped tokens.
- Local bootstrap executes or installs remote code without checksum/signature verification.
- Automated upstream native dependency auto-merge needs explicit CI and wheel gates.
- Untrusted PNG processing defaults and docs do not strongly guide callers toward resource limits.
- Wheel license notices appear incomplete for statically linked Rust dependencies.
- File I/O failures are collapsed into `PngError`.

Low-severity findings:

- Wheel tag checker does not validate distribution name, version, file existence, or artifact count.
- Wheel smoke typing check can be masked by editable/source-tree fallback.
- Upstream release version and GitHub output values are not strictly validated.
- Broad Ruff security ignores suppress future script URL/subprocess warnings.
- Upstream surface parser misses multiple public struct fields on one line.
- `cargo-deny` archive extraction/install path is not constrained.
- Python vulnerability audit is environment-based, not lockfile/artifact-based.
- Runtime bytes-like support is broader than stubs/user docs.
- API surface manifest does not reflect all exported `RowFilter` compatibility members.
- `preserve_attrs` behavior is documented but not behaviorally tested.
- `RawImage.add_icc_profile()` lacks behavioral coverage.
- Negative timeout validation is not covered by tests.
- Some docs examples are partial but not marked as such, and docs examples are not tested.
- Memory/raw APIs lack full negative tests for file-only options.
- `RawImage` numeric fields accept `bool` silently.
- Enum-like parsing swallows arbitrary `.value` property errors.
- `deny.toml` has unused broad license allowances.
- Python support metadata lags CI coverage for Python 3.14.

## Findings

### 1. Medium - Mutable GitHub Actions refs in write-token workflows

Evidence:

- `.github/workflows/upstream-bump.yml:114-118` uses
  `peter-evans/create-pull-request@v6` with `UPSTREAM_BUMP_TOKEN`.
- `.github/workflows/dependency-health.yml:82-85` uses
  `peter-evans/create-pull-request@v6` with `DEPENDENCY_REFRESH_TOKEN`.
- Other workflow dependencies are also tag-pinned rather than SHA-pinned, for example
  `.github/workflows/upstream-bump.yml:21-29`.
- Docs acknowledge mutable tag debt in the upstream bump process.

Impact: if a third-party action tag is moved or compromised, attacker-controlled code
can run in jobs with repository write and pull-request permissions.

Suggested fix: pin all third-party `uses:` entries to reviewed commit SHAs, especially
write-token jobs. Maintain those pins with Dependabot/Renovate or a documented refresh
process that reviews resolved SHAs.

### 2. Medium - Local bootstrap executes or installs remote code without verification

Evidence:

- `Makefile:31` pipes `https://sh.rustup.rs` directly to `sh`.
- `Makefile:47-51` downloads a `cargo-deny` tarball from GitHub releases, extracts it,
  and installs a discovered binary without verifying a checksum, signature, or
  attestation.

Impact: compromised upstream release assets, DNS/TLS path issues, or account compromise
can become arbitrary code execution during local developer bootstrap. Current GitHub CI
installs Rust before running `make ci`, so CI does not depend on the Rustup shell
installer branch.

Suggested fix: for CI and release automation, install Rust before invoking Make targets
that run `setup`. For local developer convenience, accept the official Rustup shell
installer tradeoff. For `cargo-deny`, either verify the exact archive hash or install
with `cargo install --locked cargo-deny --version 0.19.7`.

### 3. Medium - Automated upstream native dependency auto-merge needs explicit CI and wheel gates

Evidence:

- `docs/process/upstream-bumps.md` describes auto-merge after CI and wheel workflow pass.
- `.github/workflows/upstream-bump.yml:155-161` enables auto-merge for the bump PR.
- The workflow bumps a native Rust dependency that is part of the extension binary.

Impact: a malicious or compromised upstream `oxipng` release could be incorporated
automatically if branch protection and workflow checks are not the merge gate.

Suggested fix: preserve automation, but make the merge path fail closed: run repository
CI before opening the PR, wait for the wheel workflow on the PR head commit, require
branch protection checks, and enable auto-merge only after those gates are satisfied.

### 4. Medium - Untrusted PNG resource-limit guidance is weak

Evidence:

- `src/lib.rs:386` initializes `max_decompressed_size` to `None`.
- `src/lib.rs:487-489` only sets `options.max_decompressed_size` when callers pass it.
- `docs/usage/memory-optimization.md` and `docs/usage/file-optimization.md` list
  `timeout` and `max_decompressed_size` as advanced options, but do not provide a clear
  untrusted-input warning.

Impact: callers optimizing attacker-controlled PNGs may omit decompression and CPU
limits, risking denial of service.

Suggested fix: either set a conservative default cap in the binding or add explicit
README and usage-doc guidance for untrusted inputs. Recommend `timeout`,
`max_decompressed_size`, conservative compression settings, and careful use of
`fix_errors`/`force`. Add tests that prove capped inputs are rejected.

### 5. Medium - Third-party license notices appear incomplete for wheel distribution

Evidence:

- `pyproject.toml:11-12` includes only `LICENSE` as license metadata.
- `THIRD_PARTY_NOTICES.md:11` mentions upstream `oxipng`, but the native extension
  statically links runtime crates such as `pyo3`, `indexmap`, `libdeflater`, `zopfli`,
  `rayon`, and transitive dependencies.

Impact: wheels may ship without required third-party notices for bundled Rust
dependencies, creating downstream compliance risk.

Suggested fix: generate a complete runtime dependency notice file with `cargo-about` or
an equivalent tool, include it in `license-files`, and add a wheel smoke check proving
the notice file is present in built artifacts.

### 6. Medium - File I/O failures are collapsed into `PngError`

Evidence:

- `src/lib.rs:516-518` maps every upstream `oxi::PngError` to the package `PngError`.
- `src/lib.rs:595-596` and `src/lib.rs:615-617` use that mapping for file operations.
- A reviewer runtime check confirmed missing input and missing output parent raise
  `oxipng.PngError`, not `FileNotFoundError` or `OSError`.

Impact: callers cannot distinguish corrupt PNG data from path, permission, or filesystem
failures. This weakens error handling for file workflows.

Suggested fix: match upstream `PngError::ReadFailed` and `PngError::WriteFailed` and map
contained `io::Error` values to `PyOSError` or a more specific Python I/O exception.
Keep decode and optimization failures as `PngError`. Add missing-file and
unwritable-output tests.

### 7. Low - Wheel tag checker validates only the last tag components

Evidence:

- `scripts/check_wheel_tags.py:13-20` and `scripts/check_wheel_tags.py:38-44` parse and
  validate only Python/ABI/platform tag pieces.
- Tests in `tests/test_wheel_tags.py` do not cover wrong distribution names, wrong
  versions, nonexistent files, or extra wheel count.

Impact: a file named like another project but ending with acceptable tags could pass the
gate if it appears in the artifact set.

Suggested fix: use `packaging.utils.parse_wheel_filename`, assert normalized project name
is `oxipng-pybind`, assert the version matches `pyproject.toml`, require files to exist,
and require the expected wheel count for each build target.

### 8. Low - Wheel smoke typing check can be masked by source-tree fallback

Evidence:

- `scripts/smoke_wheel.py:40-60` accepts a fallback through `oxipng_pybind.pth` and
  `importlib.util.find_spec` if metadata does not list `oxipng/__init__.pyi` or
  `oxipng/py.typed`.

Impact: a release wheel can pass smoke checks even when typing files are not actually
included in the wheel metadata.

Suggested fix: for release-wheel smoke tests, require typing files to appear in
`metadata.files("oxipng-pybind")`. Keep editable-install fallback only behind an explicit
test/dev flag.

### 9. Low - Upstream release version and GitHub output values are not strictly validated

Evidence:

- `scripts/bump_upstream.py:32-53` normalizes the upstream tag by only removing a leading
  `v`.
- `scripts/bump_upstream.py:115-120` writes output values directly to `GITHUB_OUTPUT`.

Impact: unexpected upstream tag formats can break release automation, produce invalid
Python/Cargo versions, or emit unsafe multiline GitHub output.

Suggested fix: validate release tags with a strict SemVer/PEP 440-compatible regex before
writing files or outputs. Reject newlines in GitHub output values or use GitHub's
documented multiline output form.

### 10. Low - Broad Ruff ignores suppress future script URL/subprocess warnings

Evidence:

- `pyproject.toml:130-132` ignores `S310` and `S603` for all `scripts/*.py`.

Impact: future unsafe URL or subprocess use in release automation will not be flagged by
lint.

Suggested fix: remove broad per-file ignores and use targeted `# noqa` comments with
justification on reviewed lines, or add a small static policy test for approved URL and
subprocess call sites.

### 11. Low - Upstream surface parser misses multiple public struct fields on one line

Evidence:

- `scripts/scan_upstream_surface.py:57-60` uses one `re.match()` per line for struct
  fields.
- A fixture in `tests/test_scan_upstream_surface.py` places multiple public fields on
  one line, but the expected result captures only the first field.

Impact: upstream Rust formatting changes can hide added or removed options from the
compatibility scan.

Suggested fix: parse all field matches within each extracted block, or use `rustdoc` JSON
or a Rust parser instead of line regexes. Add a test that expects both same-line fields.

### 12. Low - `cargo-deny` archive extraction/install path is not constrained

Evidence:

- `Makefile:44-51` extracts the downloaded archive and installs the first `cargo-deny`
  path found by `find ... | head -n 1`.

Impact: if the archive is malicious or malformed, extraction can place unexpected files
inside the temp tree and the first matching binary wins.

Suggested fix: verify archive hash first, extract with constrained options, assert the
expected single binary path, and fail if zero or multiple matching binaries are found.

### 13. Low - Python vulnerability audit was environment-based

Evidence:

- Older Makefile revisions ran `uv run --group dev pip-audit --local`.
- Older dependency-health docs described local environment audit behavior.

Impact: audits can miss packages present in lockfiles but not installed for the current
platform or dependency group, and they do not prove release artifacts were audited from a
deterministic input.

Suggested fix: add a lockfile or exported-requirements audit path in CI and document
which groups/platforms are covered.

### 14. Low - Runtime bytes-like support is broader than stubs and docs

Evidence:

- `oxipng/__init__.pyi:8` defines `BytesLike = bytes | bytearray | memoryview`.
- `docs/usage/memory-optimization.md` documents only `bytes`, `bytearray`, and
  `memoryview`.
- `src/lib.rs:632-635` accepts any `PyBuffer<u8>` and then any object whose
  `tobytes()` returns `bytes`.
- A reviewer runtime check accepted `array.array("B", png_bytes)` and a custom
  `tobytes()` object.

Impact: typed callers get false negatives, and unsupported behavior can become an
accidental public API. The `.tobytes()` fallback can also execute arbitrary Python code
during argument conversion.

Suggested fix: either narrow Rust to the documented/stubbed types or widen stubs and docs
with explicit copy and side-effect warnings. Add tests for whichever behavior is
intended.

### 15. Low - API surface manifest does not reflect all exported `RowFilter` members

Evidence:

- `docs/api-surface/oxipng-10.1.1.toml:92` lists only five upstream `RowFilter` values.
- `oxipng/__init__.pyi:59` and runtime/tests expose ten facade members including
  compatibility names such as `brute`.

Impact: the machine-readable source of truth will not catch drift in public Python facade
compatibility members.

Suggested fix: add a Python-only compatibility section to the manifest, or list all
exported facade aliases with a note separating upstream `RowFilter` from compatibility
surface.

### 16. Low - `preserve_attrs` behavior is not behaviorally tested

Evidence:

- `src/lib.rs:590-592` passes `preserve_attrs` into `oxi::OutFile::Path`.
- `tests/test_api.py` validates flag typing and file-only rejection, but not permissions
  or modification-time preservation.
- `docs/usage/file-optimization.md:55` documents permissions and mtime preservation.

Impact: file metadata preservation can regress across platforms without test failure.

Suggested fix: add tests that set mode and mtime on an input file, optimize to an output
path with `preserve_attrs=True`, and assert expected metadata with OS-specific skips
where needed.

### 17. Low - `RawImage.add_icc_profile()` lacks behavioral coverage

Evidence:

- `src/lib.rs:1072-1075` forwards ICC profile data to upstream.
- `tests/test_api.py:103` checks docstrings, but tests do not call
  `RawImage.add_icc_profile()`.
- `docs/usage/raw-image.md` documents ICC profile attachment.

Impact: ICC embedding, stripping interaction, or upstream API drift could break without
test failure.

Suggested fix: add a test that attaches an ICC profile, creates PNG bytes, and verifies
the `iCCP` chunk or ICC data using direct chunk inspection or Pillow.

### 18. Low - Negative timeout validation is not tested

Evidence:

- `src/lib.rs:75-79` rejects negative timeout values.
- Existing tests cover non-finite values, huge values, booleans, and strings, but not a
  negative number for every public path.

Impact: a resource-control validation can regress without coverage.

Suggested fix: add `timeout=-1` tests for `optimize_from_memory`, `analyze`, and
`RawImage.create_optimized_png`.

### 19. Low - Docs examples are partial and not executed

Evidence:

- `docs/usage/raw-image.md` and `docs/usage/pyoxipng-migration.md` contain examples with
  placeholders such as `data`, `width`, and `height` without marking the snippets as
  partial.
- There is no doctest or example execution coverage.

Impact: copy-paste examples can fail, and API drift in docs can survive tests.

Suggested fix: make snippets self-contained or mark placeholders explicitly with comments
or ellipses, then add lightweight documentation example tests.

### 20. Low - Memory/raw APIs lack full negative tests for file-only options

Evidence:

- Docs state `backup` and `preserve_attrs` are file-only options.
- Tests cover rejection for `analyze` and `RawImage.create_optimized_png(backup=True)`,
  but do not cover every memory/raw combination.

Impact: public rejection contracts for non-file APIs can drift.

Suggested fix: add negative tests for `optimize_from_memory(..., backup=True)`,
`optimize_from_memory(..., preserve_attrs=True)`, and
`RawImage.create_optimized_png(preserve_attrs=True)`.

### 21. Low - `RawImage` numeric fields accept `bool` silently

Evidence:

- `src/lib.rs:645-650` extracts bit depth directly as `u8`.
- `src/lib.rs:657-670` extracts transparency and palette samples directly as integer
  types.
- `src/lib.rs:909-910` extracts width and height directly as `u32`.
- A reviewer runtime check showed `True` is accepted as `1` for these fields.

Impact: caller mistakes become valid image parameters instead of `TypeError`, unlike
boolean options and `timeout` where bool is explicitly rejected.

Suggested fix: reject `PyBool` before integer extraction for width, height, bit depth,
`extract_u16`, and `extract_u8`. Add tests for bool rejection.

### 22. Low - Enum-like parsing swallows arbitrary `.value` property errors

Evidence:

- `src/lib.rs:36-39` probes `value.getattr("value")` and ignores any error.
- `src/lib.rs:327-329` also probes `getattr("value")` when deciding whether to parse a
  filter as enum-like.

Impact: a user object whose `.value` property raises a real exception gets converted
into a generic `ValueError`, hiding the original bug and potentially invoking the
property more than once.

Suggested fix: treat only `AttributeError` as absent and propagate other exceptions,
following the pattern already used by `py_string_attr()`.

### 23. Low - `deny.toml` has unused broad license allowances

Evidence:

- `deny.toml:11-13` allows `BSD-2-Clause`, `BSD-3-Clause`, and `ISC`.
- `cargo deny check` reports those allowances as `license-not-encountered` warnings.

Impact: future dependencies under those licenses would not require a conscious policy
update.

Suggested fix: remove unused allowances or document why the policy intentionally
pre-allows them.

### 24. Low - Python support metadata lags CI coverage

Evidence:

- `pyproject.toml:22-25` lists classifiers for Python 3.11, 3.12, and 3.13.
- `.github/workflows/api-matrix.yml:20` tests Python 3.14.

Impact: package metadata understates the tested support matrix, or CI is testing a
version that is not intended as supported.

Suggested fix: add the Python 3.14 classifier if support is intended, or remove 3.14
from CI/docs until it is official policy.

## Verification

Local commands run in this review:

- `cargo fmt --all -- --check` passed.
- `cargo clippy --workspace --all-targets -- -D warnings` passed.
- `cargo test` passed with 0 Rust tests/doc-tests.
- `uv run --group dev ruff check .` passed.
- `uv run --group dev basedpyright` passed with 0 errors.
- `uv run --group dev maturin develop --quiet && uv run --no-sync --group dev pytest -v -ra`
  passed: 256 Python tests.
- `cargo deny check` passed advisories, bans, licenses, and sources, with warnings for
  unused license allowances.
- `uv audit --locked` found no known Python dependency vulnerabilities.

Additional subagent verification included locked variants of Rust checks, focused Python
tests for API/real PNG behavior, `ruff format --check`, `uv lock --check`, and
`cargo tree --locked -d`; no additional blocking failures were reported.

## Tooling limitation

CodeRabbit CLI version `0.5.2` is installed, but `coderabbit auth status --agent` reported
not authenticated. `coderabbit auth login --agent` failed with:

```text
Localhost callback and stdin fallback are unavailable. Use --api-key for authentication.
```

No CodeRabbit findings are included in this report.

## Resolution Appendix

Implemented on 2026-05-26.

1. Mutable GitHub Actions refs: fixed by pinning write-token
   `peter-evans/create-pull-request` uses to commit
   `c5a7806660adbe173f04e3e038b0ccdcd758773c` and adding
   `tests/test_workflows.py`.
2. Remote bootstrap execution: partially fixed by keeping GitHub CI on
   preinstalled Rust before `make ci`, preserving the Rustup shell installer for
   local developer convenience, and installing `cargo-deny` with
   `cargo install --locked`.
3. Automated upstream native dependency auto-merge: fixed by keeping auto-merge
   gated after the repository CI and wheel workflow checks pass, with workflow
   policy tests covering the gate order.
4. Untrusted PNG resource limits: fixed with README and usage-doc guidance plus
   a `max_decompressed_size` enforcement regression test.
5. Third-party notices: fixed by adding `THIRD_PARTY_NOTICES.md` to
   `license-files`, expanding runtime Rust dependency notices, and adding static
   packaging tests.
6. File I/O error mapping: fixed by mapping upstream read/write `NotFound`
   failures to `FileNotFoundError` and other I/O failures to `OSError`.
7. Wheel tag checker gaps: fixed with `packaging.utils.parse_wheel_filename`,
   distribution/version/existence/count validation, and expanded tests.
8. Wheel smoke typing fallback: fixed by requiring release metadata unless
   `--allow-editable` is explicitly passed.
9. Upstream version and GitHub output validation: fixed with strict upstream
   SemVer tag validation and newline rejection for GitHub outputs.
10. Broad Ruff ignores: fixed by narrowing script per-file ignores to `T201` and
    moving `S310`/`S603` to reviewed line-level suppressions.
11. Upstream surface parser: fixed by collecting all public struct fields in a
    declaration block, including same-line fields.
12. `cargo-deny` tar extraction: fixed by removing tar download/extraction from
    bootstrap.
13. Python audit coverage: fixed with `make py-audit-lock`, which runs
    `uv audit --locked`.
14. Bytes-like runtime support drift: fixed by narrowing native support to
    documented `bytes`, `bytearray`, and `memoryview`.
15. `RowFilter` compatibility metadata: fixed with a
    `[python_compat.RowFilter.aliases]` manifest section.
16. `preserve_attrs` coverage: fixed with a metadata preservation regression
    test.
17. ICC profile coverage: fixed with an `iCCP` chunk regression test.
18. Negative timeout coverage: fixed with negative timeout tests for memory,
    analyze, and raw-image paths.
19. Partial docs examples: fixed by making raw-image migration snippets
    self-contained.
20. File-only option rejection coverage: fixed with memory/raw rejection tests.
21. `RawImage` bool numerics: fixed by rejecting bool values before integer
    extraction for shape, bit depth, palette, and transparency fields.
22. `.value` property error swallowing: fixed by propagating non-`AttributeError`
    exceptions from enum-like `.value` access.
23. Unused license allowances: fixed by removing unused `BSD-2-Clause`,
    `BSD-3-Clause`, and `ISC` allowances from `deny.toml`.
24. Python 3.14 metadata: fixed by adding the Python 3.14 classifier to match
    the API matrix.

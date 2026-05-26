# API, Wheel, and Upstream Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [x]`) syntax for tracking.

**Goal:** Expand `oxipng-pybind` from a narrow file-only wrapper into a
documented Python binding that supports the planned option surface,
`optimize_from_memory()`, ABI3 wheel artifacts, and upstream surface-scan
automation.

**Source Specs:**

- `docs/specs/2026-05-26-api-options-memory-design.md`
- `docs/specs/2026-05-26-wheel-artifacts-design.md`
- `docs/specs/2026-05-26-upstream-surface-scan-design.md`

**Architecture:** Keep `oxipng` as the Python import package with a Python
facade over the native `_oxipng` extension. Public enums live in
`oxipng/__init__.py` as `enum.Enum` classes. The Rust extension accepts enum
`.value` strings and ordinary strings through a small option parsing layer,
then maps them into explicit upstream `oxi::Options`. Release artifacts use
PyO3 ABI3 wheels. Upstream bump automation remains conservative: it documents
new upstream surface but never exposes API automatically.

**Tech Stack:** Rust 2021, PyO3, maturin, upstream `oxipng`, uv, pytest,
Pillow, ruff, basedpyright, cargo-deny, pre-commit, GitHub Actions.

---

## File Structure

Modify existing files:

- `.github/workflows/upstream-bump.yml`
- `Cargo.toml`
- `Makefile`
- `README.md`
- `docs/README.md`
- `docs/process/upstream-bumps.md`
- `docs/usage/file-optimization.md`
- `oxipng/__init__.py`
- `oxipng/__init__.pyi`
- `pyproject.toml`
- `src/lib.rs`
- `tests/conftest.py`
- `tests/test_api.py`
- `tests/test_bump_upstream.py`

Create new files:

- `.github/workflows/wheels.yml`
- `CHANGELOG.md`
- `docs/api-surface/oxipng-10.1.1.toml`
- `docs/architecture/api-compatibility.md`
- `docs/architecture/options-surface.md`
- `docs/process/release-artifacts.md`
- `docs/usage/memory-optimization.md`
- `scripts/check_wheel_tags.py`
- `scripts/scan_upstream_surface.py`
- `scripts/smoke_wheel.py`
- `tests/test_scan_upstream_surface.py`
- `tests/test_wheel_tags.py`

Do not rename the package, repository, or import module.

---

## Task 1: Add Public API Contract Tests

**Files:**

- Modify: `tests/conftest.py`
- Modify: `tests/test_api.py`

- [x] **Step 1: Add PNG byte fixture helpers**

Update `tests/conftest.py` with helpers that return generated PNG bytes in
addition to filesystem paths. Keep using Pillow-generated tiny PNGs.

Expected: tests can request both `png_path` and `png_bytes`.

- [x] **Step 2: Replace the current narrow API import test**

Update `tests/test_api.py` so imports cover:

```python
from oxipng import Deflater, FilterStrategy, Interlacing, PngError, StripChunks
from oxipng import optimize, optimize_from_memory
```

Expected initially: tests fail because the new symbols do not exist.

- [x] **Step 3: Add signature tests**

Assert exact signatures:

```text
(input, output=None, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False, backup=False, preserve_attrs=False)
(data, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False)
```

Expected initially: tests fail because the signatures are still narrow.

- [x] **Step 4: Add enum and string alias tests**

Parametrize all enum members and string aliases from
`docs/specs/2026-05-26-api-options-memory-design.md`:

- `Interlacing.keep`, `Interlacing.off`, `Interlacing.on`
- `StripChunks.none`, `StripChunks.safe`, `StripChunks.all`
- `Deflater.libdeflater`, `Deflater.zopfli`
- all ten `FilterStrategy` members and aliases

For each value, call either `optimize()` or `optimize_from_memory()` with a
generated PNG and assert the output is readable.

Expected initially: tests fail until parsing is implemented.

- [x] **Step 5: Add validation tests**

Cover:

- unsupported keyword raises `TypeError`
- invalid enum/string value raises `ValueError`
- invalid `level` raises `ValueError`
- empty `filter=[]` raises `ValueError`
- non-bool values for `fix_errors`, `force`, `backup`, and `preserve_attrs`
  raise `TypeError`
- `backup=True` with explicit output raises `ValueError`
- existing `<input>.bak` with `backup=True` raises `FileExistsError`

Expected initially: tests fail until behavior is implemented.

- [x] **Step 6: Add memory optimization tests**

Cover:

- `optimize_from_memory(bytes_png)` returns readable bytes
- `optimize_from_memory(bytearray_png)` returns readable bytes
- `optimize_from_memory(memoryview_png)` returns readable bytes
- corrupt memory input raises `PngError`

Expected initially: tests fail until memory API is implemented.

- [x] **Step 7: Run the focused failing test suite**

Run:

```bash
uv run --group dev pytest tests/test_api.py -v -ra
```

Expected: failures are limited to missing new API or unimplemented behavior.

---

## Task 2: Implement Python Facade Enums and Stubs

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`

- [x] **Step 1: Add runtime enums in `oxipng/__init__.py`**

Define Python `enum.Enum` classes:

- `Interlacing`
- `StripChunks`
- `Deflater`
- `FilterStrategy`

Use lower-case member names and stable string `.value` values matching the API
spec. Export them in `__all__`.

- [x] **Step 2: Keep native imports private**

Continue importing `PngError`, `optimize`, and `optimize_from_memory` from
`_oxipng` outside `TYPE_CHECKING`. Public enums stay in the Python facade.

- [x] **Step 3: Update type stubs**

Update `oxipng/__init__.pyi` with:

- enum class definitions
- `BytesLike = bytes | bytearray | memoryview`
- the expanded `optimize()` signature
- `optimize_from_memory()` signature

Use `Literal` only if it materially improves type clarity without making the
stub hard to maintain.

- [x] **Step 4: Run Python-only checks**

Run:

```bash
uv run --group dev ruff check oxipng tests/test_api.py
uv run --group dev basedpyright
```

Expected: Python facade and stubs pass lint and typecheck. API tests may still
fail until Rust parsing exists.

---

## Task 3: Implement Rust Option Parsing and File API

**Files:**

- Modify: `Cargo.toml`
- Modify: `src/lib.rs`

- [x] **Step 1: Add direct dependencies needed by parsing**

If needed, add `indexmap` as a direct dependency because the wrapper constructs
`IndexSet<oxi::FilterStrategy>`.

If `cargo add` is available, run:

```bash
cargo add indexmap
```

If `cargo add` is not available, edit `Cargo.toml` manually and then run:

```bash
cargo update -p indexmap
```

Expected: `Cargo.toml` and `Cargo.lock` update only if direct import is needed.

- [x] **Step 2: Restructure parsing around explicit helpers**

In `src/lib.rs`, implement helpers matching the spec:

- `parse_options(kwargs, mode) -> ParsedOptions`
- `parse_level(value) -> u8`
- `parse_interlace(value) -> Option<bool>`
- `parse_strip(value) -> oxi::StripChunks`
- `parse_deflater(value, preset_deflater) -> oxi::Deflater`
- `parse_filters(value) -> IndexSet<oxi::FilterStrategy>`

`ParsedOptions` should include:

- `options: oxi::Options`
- `backup: bool`
- `preserve_attrs: bool`

- [x] **Step 3: Parse Python enum values as strings**

Accept:

- plain Python strings
- Python enum objects with `.value` strings
- sequences for `filter`

Do not rely on Python enum object identity in Rust.

- [x] **Step 4: Implement file API behavior**

Update `optimize()` to:

- accept the full documented signature
- reject `backup=True` with explicit output
- create `<input>.bak` before in-place optimization when `backup=True`
- refuse to overwrite an existing backup with `FileExistsError`
- pass `preserve_attrs` through `OutFile::Path`
- release the GIL during `oxi::optimize()`

- [x] **Step 5: Preserve current exceptions**

Map:

- invalid caller types to `TypeError`
- invalid caller values to `ValueError`
- upstream `oxi::PngError` to `PngError`

- [x] **Step 6: Run file API tests**

Run the non-memory subset while memory tests are still expected to fail:

```bash
uv run --group dev maturin develop
uv run --group dev pytest tests/test_api.py -v -ra -k 'not memory'
```

Expected: file API tests pass. The full `tests/test_api.py` suite is expected
to pass after Task 4.

---

## Task 4: Implement `optimize_from_memory()`

**Files:**

- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`

- [x] **Step 1: Add the PyO3 function**

Expose:

```rust
#[pyfunction]
#[pyo3(signature = (data, **kwargs))]
fn optimize_from_memory(...)
```

The Python-visible signature must match the spec.

- [x] **Step 2: Accept supported bytes-like inputs**

Accept `bytes`, `bytearray`, and `memoryview`. Copy Python-owned data before
entering `py.allow_threads(...)`.

- [x] **Step 3: Reuse option parsing in memory mode**

Use the same option parser but reject file-only options by construction:

- `backup`
- `preserve_attrs`

Unsupported kwargs still raise `TypeError`.

- [x] **Step 4: Release the GIL during upstream optimization**

Call `oxi::optimize_from_memory(&data, &options)` inside `py.allow_threads(...)`.

- [x] **Step 5: Run API tests**

Run:

```bash
uv run --group dev maturin develop
uv run --group dev pytest tests/test_api.py -v -ra
```

Expected: all public API tests pass.

---

## Task 5: Update User and Architecture Documentation

**Files:**

- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/usage/file-optimization.md`
- Create: `docs/usage/memory-optimization.md`
- Create: `docs/architecture/api-compatibility.md`
- Create: `docs/architecture/options-surface.md`
- Create: `CHANGELOG.md`

- [x] **Step 1: Update README quickstart**

Document:

- install command
- file optimization
- memory optimization
- supported public objects
- explicit unsupported `pyoxipng` APIs

- [x] **Step 2: Update usage docs**

Document file API examples:

- in-place optimization
- output path optimization
- backup behavior
- preserve attrs behavior
- exception behavior

Create memory API docs with:

- `bytes`
- `bytearray`
- `memoryview`
- expected return bytes
- corrupt input behavior

- [x] **Step 3: Add architecture docs**

`api-compatibility.md` must compare:

- upstream `oxipng`
- `pyoxipng`
- `oxipng-pybind`

`options-surface.md` must list every exposed option, enum value, string alias,
and intentionally unexposed upstream field.

- [x] **Step 4: Add changelog**

Create `CHANGELOG.md` with an unreleased section summarizing:

- memory API
- option surface
- enum helpers
- wheel workflow pending
- upstream scan pending

- [x] **Step 5: Run docs checks**

Run:

```bash
make md-lint
```

Expected: markdownlint passes.

---

## Task 6: Enable ABI3 Wheel Builds Locally

**Files:**

- Modify: `Cargo.toml`
- Modify: `pyproject.toml`
- Modify: `Makefile`
- Create: `scripts/check_wheel_tags.py`
- Create: `tests/test_wheel_tags.py`

- [x] **Step 1: Enable PyO3 ABI3**

Update `Cargo.toml`:

```toml
pyo3 = { version = "0.25.1", features = ["extension-module", "abi3-py311"] }
```

- [x] **Step 2: Restrict maturin includes to wheels**

Update `pyproject.toml` so `oxipng/__init__.pyi` and `oxipng/py.typed` use
`format = ["wheel"]`.

- [x] **Step 3: Add wheel tag checker**

Create `scripts/check_wheel_tags.py` with:

- `--expected-platform`
- one or more wheel paths
- failure when no wheels are present
- failure on CPython-specific ABI tags like `cp313-cp313`
- wildcard matching for macOS expected platforms like `macosx_*_arm64`

- [x] **Step 4: Add checker tests**

Create `tests/test_wheel_tags.py` covering:

- valid ABI3 Linux tag
- valid ABI3 macOS wildcard tag
- invalid CPython-specific ABI tag
- missing expected platform
- no wheel paths

- [x] **Step 5: Build local wheel**

Run:

```bash
make wheel
uv run --group dev python scripts/check_wheel_tags.py --expected-platform manylinux_2_34_x86_64 target/wheels/*.whl
```

Expected: local Linux wheel is ABI3. The local platform may be
`manylinux_2_34_x86_64`; CI will target `manylinux_2_28_x86_64`.

---

## Task 7: Add Wheel Smoke Script and Workflow

**Files:**

- Create: `scripts/smoke_wheel.py`
- Create: `.github/workflows/wheels.yml`
- Create: `docs/process/release-artifacts.md`
- Modify: `README.md`

- [x] **Step 1: Add smoke script**

Create `scripts/smoke_wheel.py` that:

- imports `oxipng`
- imports `PngError`, `optimize`, and `optimize_from_memory`
- generates a PNG with Pillow
- optimizes a file in place
- optimizes a file to an output path
- optimizes PNG bytes from memory
- verifies outputs are readable with Pillow

- [x] **Step 2: Add artifact-only workflow**

Create `.github/workflows/wheels.yml` using
`docs/specs/2026-05-26-wheel-artifacts-design.md`.

Requirements:

- `workflow_dispatch`
- version tag trigger
- relevant `pull_request` path filters
- `PyO3/maturin-action@v1`
- stable artifact names
- `scripts/check_wheel_tags.py`
- `scripts/smoke_wheel.py`
- no sdist build or upload

- [x] **Step 3: Add Linux aarch64 exception handling**

If QEMU smoke execution is non-gating, workflow must upload
`linux-aarch64-smoke-exception.txt` with every required field from the spec.

- [x] **Step 4: Document release artifacts**

Create `docs/process/release-artifacts.md` covering:

- artifact-only wheel workflow
- expected wheel tags
- smoke requirements
- no PyPI publishing in this phase
- no sdist in this phase

- [x] **Step 5: Validate workflow YAML**

Run the smoke script against a locally built wheel:

```bash
tmpdir="$(mktemp -d)"
uv run --group dev python -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/pip" install target/wheels/*.whl pillow
"$tmpdir/venv/bin/python" scripts/smoke_wheel.py
```

Expected: the installed wheel passes import, file optimization, and memory
optimization smoke checks outside the repo environment.

- [x] **Step 6: Validate workflow YAML**

Run:

```bash
uv run --group dev pre-commit run check-yaml --files .github/workflows/wheels.yml
```

Expected: workflow YAML passes.

---

## Task 8: Add Upstream API Surface Manifest

**Files:**

- Create: `docs/api-surface/oxipng-10.1.1.toml`
- Modify: `docs/architecture/api-compatibility.md`
- Modify: `docs/architecture/options-surface.md`

- [x] **Step 1: Create manifest directory**

Run:

```bash
mkdir -p docs/api-surface
```

- [x] **Step 2: Write complete manifest**

Create `docs/api-surface/oxipng-10.1.1.toml` with:

- upstream version
- exposed functions
- exposed options
- all exposed enum mappings
- unexposed `Options` fields
- unexposed `StripChunks::Strip`, `StripChunks::Keep`
- unexposed `FilterStrategy::Predefined`
- notes for intentionally collapsed values

- [x] **Step 3: Cross-link docs**

Update architecture docs so the manifest is referenced as the machine-readable
compatibility source of truth.

- [x] **Step 4: Run docs checks**

Run:

```bash
make md-lint
```

Expected: docs pass.

---

## Task 9: Implement Upstream Surface Scanner

**Files:**

- Create: `scripts/scan_upstream_surface.py`
- Create: `tests/test_scan_upstream_surface.py`

- [x] **Step 1: Add parser fixtures**

In `tests/test_scan_upstream_surface.py`, add minimal Rust snippets for:

- `Options`
- `FilterStrategy`
- `Deflater`
- `optimize_from_memory`

Use the exact shapes from
`docs/specs/2026-05-26-upstream-surface-scan-design.md`.

- [x] **Step 2: Implement narrow Rust surface parser**

In `scripts/scan_upstream_surface.py`, parse:

- public struct fields
- public enum variants
- public function names
- attributes before declarations or variants
- multiline variants

Fail closed when a required declaration cannot be found.

- [x] **Step 3: Implement manifest comparison**

Compare parsed upstream surface with the current versioned manifest. Report:

- new upstream fields or variants
- removed exposed mappings
- missing expected functions
- manifest entries not found upstream

- [x] **Step 4: Emit stable outputs**

Write:

- `.cache/upstream-surface/report.json`
- `.cache/upstream-surface/pr-body-section.md`

Keep JSON deterministic for tests.

- [x] **Step 5: Implement docs update mode**

Add `--update-docs` to update:

- `docs/architecture/api-compatibility.md`
- `docs/architecture/options-surface.md`
- `CHANGELOG.md`

Only add new upstream items to unexposed sections.

- [x] **Step 6: Run scanner tests**

Run:

```bash
uv run --group dev pytest tests/test_scan_upstream_surface.py -v -ra
```

Expected: scanner unit tests pass.

---

## Task 10: Integrate Surface Scan into Upstream Bumps

**Files:**

- Modify: `.github/workflows/upstream-bump.yml`
- Modify: `scripts/bump_upstream.py`
- Modify: `tests/test_bump_upstream.py`
- Modify: `docs/process/upstream-bumps.md`

- [x] **Step 1: Teach bump script the target version**

Update `scripts/bump_upstream.py` so it can report the target upstream version
in a machine-readable way or write it to an output file used by the workflow.

- [x] **Step 2: Add upstream checkout step**

In `.github/workflows/upstream-bump.yml`, fetch
`oxipng/oxipng` tag `v<version>` into `.cache/upstream/oxipng`.

- [x] **Step 3: Add manifest copy lifecycle**

Before scanning, copy `docs/api-surface/oxipng-A.toml` to
`docs/api-surface/oxipng-B.toml` when `B` does not already exist.

- [x] **Step 4: Run scanner during bump**

Run:

```bash
uv run --group dev python scripts/scan_upstream_surface.py --update-docs
```

- [x] **Step 5: Include PR body section**

Append `.cache/upstream-surface/pr-body-section.md` to the create-pull-request
body.

- [x] **Step 6: Add issue permissions and triage issue creation**

Add `issues: write`. Use `gh issue list/create/edit` or a small script to
create or update exactly one `upstream-surface` issue per upstream version.

- [x] **Step 7: Preserve auto-merge safety**

Auto-merge is allowed only when:

- source CI passes
- no exposed mapping is broken
- scanner docs/changelog updates are generated successfully

- [x] **Step 8: Test bump helpers**

Add tests for issue duplicate avoidance:

- creating a new issue when no open `upstream-surface` issue exists for the
  target version
- updating the existing issue when one already exists for the target version
- not matching issues for a different upstream version

Then run:

```bash
uv run --group dev pytest tests/test_bump_upstream.py tests/test_scan_upstream_surface.py -v -ra
```

Expected: workflow helper tests pass.

---

## Task 11: Final Verification and Cleanup

**Files:**

- Modify as needed based on verification failures only.

- [x] **Step 1: Run full setup from a clean venv**

Run:

```bash
make remove-venv
make setup
```

Expected: setup installs or reuses Rust, installs cargo-deny, syncs Python dev
deps, builds editable extension, and installs pre-commit hooks.

- [x] **Step 2: Run full CI**

Run:

```bash
make ci
```

Expected: all Rust, Python, docs, cargo-deny, tests, and wheel build checks
pass.

- [x] **Step 3: Run full pre-commit**

Run:

```bash
make pre-commit-check
```

Expected: all hooks pass.

- [x] **Step 4: Run explicit format check**

Run:

```bash
make format-check
```

Expected: Rust and Python formatting checks pass.

- [x] **Step 5: Inspect wheel contents**

Run:

```bash
python -m zipfile -l target/wheels/*.whl | grep -E '(_oxipng|oxipng/__init__\\.pyi|oxipng/py\\.typed)'
```

Expected: wheel contains native extension, typing stub, and `py.typed`.

- [x] **Step 6: Commit**

Run:

```bash
git status --short
git add .github/workflows/upstream-bump.yml .github/workflows/wheels.yml
git add Cargo.toml Cargo.lock Makefile README.md pyproject.toml uv.lock
git add CHANGELOG.md docs oxipng scripts src tests
git commit -m "feat: expand api and wheel automation"
```

Expected: commit succeeds after pre-commit hooks pass.

---

## Completion Criteria

- Public API matches the API/options/memory spec.
- Runtime enums and type stubs match.
- `optimize_from_memory()` works for `bytes`, `bytearray`, and `memoryview`.
- File API supports backup, preserve attrs, force, fix errors, interlace, strip,
  deflater, and filter options.
- ABI3 wheel build is enabled and validated locally.
- Wheel artifact workflow exists and does not build sdists.
- Upstream surface manifest and scanner exist.
- Upstream bump workflow documents new upstream surface and blocks broken
  exposed mappings.
- `make ci`, `make pre-commit-check`, and `make format-check` pass.

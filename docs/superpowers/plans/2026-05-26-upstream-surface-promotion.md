# Upstream Surface Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote all practical upstream `oxipng` 10.1.1 surfaces to stable Python API except stdin/stdout.

**Architecture:** Keep compatibility-only behavior only for pyoxipng constructor/naming aliases. Promote option keywords and factories by removing deprecation warnings, updating stubs, and parsing them as stable Rust options. Add `analyze(...)` as the stable wrapper for upstream `OutFile::None`.

**Tech Stack:** Python facade and stubs, PyO3 Rust extension, pytest, basedpyright, Ruff, cargo fmt/clippy, markdownlint.

---

## File Structure

Modify:

- `oxipng/__init__.py`: stable factory docstrings and exports.
- `oxipng/__init__.pyi`: type stubs for stable options, predefined filters, and `analyze`.
- `src/lib.rs`: option parsing, predefined filters, `max_decompressed_size`, and `analyze`.
- `tests/test_api.py`: public API, warning, validation, and analyze tests.
- `docs/api-surface/oxipng-10.1.1.toml`: surface manifest.
- `docs/architecture/options-surface.md`: stable option docs.
- `docs/architecture/api-compatibility.md`: compatibility policy docs.
- `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`: punchlist update.
- `docs/superpowers/specs/2026-05-26-upstream-surface-promotion-design.md`: final design if needed.
- `docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md`: checklist.

Do not edit:

- `docs/archive/**`
- GitHub workflow files
- packaging configuration

## Task 1: Promote Stable Factories and Advanced Options

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`
- Modify: `docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md`

- [x] **Step 1: Add failing tests for warning-free stable factories and advanced options**

Update `tests/test_api.py`:

- Change factory docstring expectations for `StripChunks.strip`, `StripChunks.keep`, `Deflaters.libdeflater`, and `Deflaters.zopfli` so they no longer mention pyoxipng or `DeprecationWarning`.
- Replace warning tests for those factories with `warnings.catch_warnings(record=True)` checks that no `DeprecationWarning` is emitted.
- Replace warning tests for advanced option keywords and `timeout` with warning-free checks.
- Keep `ColorType` descriptor and pyoxipng `RawImage(data, width, height, color_type=...)` warning tests.

Expected new docstrings:

```python
"Create a strip-chunk option for explicit PNG chunk names."
"Create a keep-chunk option for explicit PNG chunk names."
"Create a libdeflater option with an explicit compression level."
"Create a zopfli option with an explicit iteration count."
```

- [x] **Step 2: Run focused tests and confirm failure**

Run:

```bash
uv run --group dev pytest tests/test_api.py::test_pyoxipng_compatibility_exports_and_docstrings tests/test_api.py::test_pyoxipng_compatibility_factories_warn tests/test_api.py::test_pyoxipng_advanced_bool_options_warn_and_optimize_memory tests/test_api.py::test_pyoxipng_timeout_warns_and_optimizes_memory -v -ra
```

Expected: tests fail because runtime code still warns and docstrings still mention compatibility.

- [x] **Step 3: Promote Python factories**

In `oxipng/__init__.py`:

- Remove `_warn_pyoxipng_compat()` calls from `StripChunks.strip`, `StripChunks.keep`, `Deflaters.libdeflater`, and `Deflaters.zopfli`.
- Update class docstrings:
  - `Deflaters`: `"""DEFLATE option factories."""`
  - `RowFilter`: `"""PNG row filter names."""`
- Update factory docstrings to the four stable strings from Step 1.
- Keep `_CompatStripChunks` and `_CompatDeflater` internal object names to avoid Rust parser churn.

- [x] **Step 4: Update stubs for stable factories and advanced options**

In `oxipng/__init__.pyi`:

- Update factory docstrings to match runtime docstrings.
- Add `max_decompressed_size: int | None = None` to `RawImage.create_optimized_png`, `optimize`, and `optimize_from_memory`.
- Leave advanced option keywords in place.

- [x] **Step 5: Remove Rust deprecation warnings from stable option keywords**

In `src/lib.rs`:

- Remove `warn_pyoxipng_compat(value.py())?` from these parse branches:
  - `optimize_alpha`
  - `bit_depth_reduction`
  - `color_type_reduction`
  - `palette_reduction`
  - `grayscale_reduction`
  - `idat_recoding`
  - `scale_16`
  - `fast_evaluation`
  - `timeout`
- Keep `warn_pyoxipng_compat` for remaining compatibility paths.
- Update `text_signature` strings for `optimize`, `optimize_from_memory`, and `RawImage.create_optimized_png` to include advanced options if tests require signature accuracy.

- [x] **Step 6: Run focused tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -q
```

Expected: tests pass after test names and assertions are updated for stable paths.

- [x] **Step 7: Commit Task 1**

Run:

```bash
git add oxipng/__init__.py oxipng/__init__.pyi src/lib.rs tests/test_api.py docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md
git commit -m "feat: promote stable option factories"
```

Expected: commit succeeds.

## Task 2: Add `max_decompressed_size`

**Files:**

- Modify: `oxipng/__init__.pyi`
- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`
- Modify: `docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md`

- [x] **Step 1: Add failing tests for `max_decompressed_size`**

Add tests that:

- `optimize_from_memory(png_bytes, max_decompressed_size=None)` succeeds without `DeprecationWarning`.
- `optimize_from_memory(png_bytes, max_decompressed_size=10_000_000)` succeeds without `DeprecationWarning`.
- `RawImage(...).create_optimized_png(max_decompressed_size=10_000_000)` succeeds.
- `optimize(png_path, max_decompressed_size=10_000_000)` succeeds.
- invalid values raise:
  - `True` -> `TypeError`
  - `-1` -> `ValueError`
  - `"bad"` -> `TypeError`

- [x] **Step 2: Run focused tests and confirm failure**

Run:

```bash
uv run --group dev pytest tests/test_api.py -q
```

Expected: tests fail with `unsupported option: max_decompressed_size`.

- [x] **Step 3: Implement Rust parsing**

In `src/lib.rs`:

- Add `fn parse_max_decompressed_size(value: &Bound<'_, PyAny>) -> PyResult<Option<usize>>`.
- Reject bools with `TypeError`.
- Return `Ok(None)` for `None`.
- Extract `usize`; map extraction failures to `TypeError`.
- Reject negative values with `ValueError`.
- Store parsed value in `parse_options`.
- Set `options.max_decompressed_size` when present.

- [x] **Step 4: Update stubs and signatures**

In `oxipng/__init__.pyi`, ensure `max_decompressed_size` is present on all three option-bearing APIs.

In `src/lib.rs`, update text signatures to include `max_decompressed_size=None`.

- [x] **Step 5: Run focused tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -q
```

Expected: tests pass.

- [x] **Step 6: Commit Task 2**

Run:

```bash
git add oxipng/__init__.pyi src/lib.rs tests/test_api.py docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md
git commit -m "feat: expose max decompressed size"
```

Expected: commit succeeds.

## Task 3: Add Predefined Filter Factory

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`
- Modify: `docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md`

- [ ] **Step 1: Add failing predefined filter tests**

Add tests that:

- `FilterStrategy.predefined([RowFilter.none, "sub", FilterStrategy.up])` returns an object with `filters == ("none", "sub", "up")`.
- The factory emits no `DeprecationWarning`.
- `optimize_from_memory(png_bytes, filter=FilterStrategy.predefined([...]))` returns readable bytes.
- Empty lists raise `ValueError`.
- Non-basic filters such as `"minsum"` raise `ValueError`.
- Unknown strings raise `ValueError`.

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```bash
uv run --group dev pytest tests/test_api.py -q
```

Expected: tests fail because `FilterStrategy.predefined` does not exist.

- [ ] **Step 3: Add Python predefined object**

In `oxipng/__init__.py`:

- Add `@dataclass(frozen=True) class _PredefinedFilters: filters: tuple[str, ...]`.
- Add a `FilterStrategy.predefined(filters)` static method.
- Validate with the allowed basic values: `none`, `sub`, `up`, `average`, `paeth`.
- Accept values that expose a string `.value`.
- Raise `ValueError` for empty or invalid values.
- Use docstring: `"""Create a predefined row-filter sequence."""`

- [ ] **Step 4: Add stub support**

In `oxipng/__init__.pyi`:

- Add `_PredefinedFilters`.
- Add `FilterStrategy.predefined(...) -> _PredefinedFilters`.
- Include `_PredefinedFilters` in `FilterOption`.

- [ ] **Step 5: Parse predefined filters in Rust**

In `src/lib.rs`:

- Detect `_PredefinedFilters` by module and qualname.
- Read its `filters` tuple.
- Convert each value to upstream `RowFilter`.
- Return `FilterStrategy::Predefined(Vec<RowFilter>)`.
- Keep non-basic filters rejected in Python.

- [ ] **Step 6: Run focused tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -q
```

Expected: tests pass.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add oxipng/__init__.py oxipng/__init__.pyi src/lib.rs tests/test_api.py docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md
git commit -m "feat: add predefined filter strategy"
```

Expected: commit succeeds.

## Task 4: Add Dry-Run `analyze`

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`
- Modify: `docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md`

- [ ] **Step 1: Add failing analyze tests**

Add tests that:

- `analyze` imports from `oxipng`.
- `inspect.signature(analyze)` matches file options without `output`, `backup`, or `preserve_attrs`.
- `analyze(png_path)` returns an `OptimizationResult`.
- `OptimizationResult.original_size` and `optimized_size` are non-negative integers.
- `analyze` does not write to the input file.
- `analyze(png_path, backup=True)` raises `TypeError`.
- `analyze(png_path, preserve_attrs=True)` raises `TypeError`.
- stable analyze calls do not emit `DeprecationWarning`.

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```bash
uv run --group dev pytest tests/test_api.py -q
```

Expected: tests fail because `analyze` and `OptimizationResult` do not exist.

- [ ] **Step 3: Add Rust result class and function**

In `src/lib.rs`:

- Add `#[pyclass(name = "OptimizationResult", frozen)]`.
- Store `original_size: usize` and `optimized_size: usize`.
- Add `#[getter]` methods for both fields.
- Add `analyze(py, input: PathBuf, kwargs)` that parses options with a mode that rejects `backup` and `preserve_attrs`.
- Use `oxi::OutFile::None`.
- Return upstream optimization result sizes.
- Add `OptimizationResult` and `analyze` to the module.

- [ ] **Step 4: Update Python facade and stubs**

In `oxipng/__init__.py`:

- Import/export `OptimizationResult` and `analyze`.

In `oxipng/__init__.pyi`:

- Add `OptimizationResult` with read-only `original_size` and `optimized_size` properties.
- Add `analyze` signature with stable file options except `output`, `backup`, and `preserve_attrs`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -q
```

Expected: tests pass.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add oxipng/__init__.py oxipng/__init__.pyi src/lib.rs tests/test_api.py docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md
git commit -m "feat: add optimization analysis API"
```

Expected: commit succeeds.

## Task 5: Update Docs and Final Verification

**Files:**

- Modify: `docs/api-surface/oxipng-10.1.1.toml`
- Modify: `docs/architecture/options-surface.md`
- Modify: `docs/architecture/api-compatibility.md`
- Modify: `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`
- Modify: `docs/superpowers/specs/2026-05-26-upstream-surface-promotion-design.md`
- Modify: `docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md`

- [ ] **Step 1: Update docs and manifest**

Update docs to show:

- `max_decompressed_size`, advanced options, explicit strip/keep chunks, deflater tuning, predefined filters, and `analyze` are stable API.
- Remaining compatibility-only paths are `ColorType` descriptors, pyoxipng raw-image constructor, and naming aliases.
- stdin/stdout remains unsupported.
- `OutFile::None` is represented by `analyze`.
- `FilterStrategy::Predefined` is represented by `FilterStrategy.predefined`.

- [ ] **Step 2: Run full verification**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest
cargo fmt --check
cargo clippy -- -D warnings
uv run --group dev ruff check oxipng scripts tests
uv run --group dev basedpyright
uv run --group dev pre-commit run markdownlint-cli2 --files docs/api-surface/oxipng-10.1.1.toml docs/architecture/options-surface.md docs/architecture/api-compatibility.md docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/specs/2026-05-26-upstream-surface-promotion-design.md docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md
git diff --check
```

Expected:

- pytest passes.
- cargo fmt passes.
- cargo clippy reports no warnings.
- Ruff passes.
- basedpyright reports no errors.
- markdownlint passes.
- `git diff --check` prints no whitespace errors.

- [ ] **Step 3: Commit docs and checklist**

Run:

```bash
git add docs/api-surface/oxipng-10.1.1.toml docs/architecture/options-surface.md docs/architecture/api-compatibility.md docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/specs/2026-05-26-upstream-surface-promotion-design.md docs/superpowers/plans/2026-05-26-upstream-surface-promotion.md
git commit -m "docs: record upstream surface promotion"
```

Expected: commit succeeds.

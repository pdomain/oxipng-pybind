# pyoxipng Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pyoxipng-style compatibility paths for API migration while warning users to migrate to oxipng-pybind's stable API.

**Architecture:** Keep the existing stable API unchanged. Add narrow Python facade compatibility objects for pyoxipng-style factories, and teach the Rust parser to recognize those objects and pyoxipng keyword names explicitly. Compatibility callables emit `DeprecationWarning`; stable API calls stay warning-free.

**Tech Stack:** Python `Enum`, PyO3, Rust `oxi` options, pytest, basedpyright, Ruff, maturin.

---

## File Structure

Modify existing files:

- `oxipng/__init__.py`: add compatibility facade classes, factories, warning helper, exports, and stable wrapper functions.
- `oxipng/__init__.pyi`: expose compatibility types and overloads for type checkers.
- `src/lib.rs`: parse compatibility objects, compatibility constructor arguments, advanced option keywords, and emit Rust-side warnings for compatibility paths.
- `tests/test_api.py`: add focused public API tests for warnings, docstrings, parsing, and stable API non-warning behavior.
- `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`: mark API compatibility work that this plan covers.

Do not modify packaging, wheel targets, PyPI publishing, or migration-guide docs in this plan.

## Shared Policy

Use this exact warning text everywhere:

```text
pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API.
```

Use concise one-sentence docstrings for new compatibility callables.

Compatibility paths should work where they map cleanly, but they are not the supported long-term API.

## Task 1: Add Compatibility Facade Scaffolding

**Files:**

- Modify: `tests/test_api.py`
- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`

- [ ] **Step 1: Write failing tests for compatibility exports, docstrings, and warnings**

Add these imports to the existing `from oxipng import (...)` block in `tests/test_api.py`:

```python
    Deflaters,
    RowFilter,
```

Add this helper near the other test helpers:

```python
PYROXIPNG_WARNING = (
    "pyoxipng compatibility path is unsupported; "
    "migrate to oxipng-pybind's stable API."
)
```

Add this standard-library import at the top of `tests/test_api.py`:

```python
import warnings
```

Add these tests after `test_public_callables_expose_runtime_docstrings`:

```python
def test_pyoxipng_compatibility_exports_and_docstrings() -> None:
    assert RowFilter.none.value == "none"
    assert RowFilter.brute.value == "brute"
    assert Interlacing.Off.value == "off"
    assert Interlacing.Adam7.value == "on"
    assert callable(Deflaters.libdeflater)
    assert callable(Deflaters.zopfli)
    assert callable(StripChunks.strip)
    assert callable(StripChunks.keep)
    assert ColorType.rgb.__call__.__doc__ == (
        "Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."
    )
    assert StripChunks.strip.__doc__ == "Create a pyoxipng-compatible strip-chunk option; emits DeprecationWarning."
    assert StripChunks.keep.__doc__ == "Create a pyoxipng-compatible keep-chunk option; emits DeprecationWarning."
    assert Deflaters.libdeflater.__doc__ == (
        "Create a pyoxipng-compatible libdeflater option; emits DeprecationWarning."
    )
    assert Deflaters.zopfli.__doc__ == "Create a pyoxipng-compatible zopfli option; emits DeprecationWarning."


def test_pyoxipng_compatibility_factories_warn() -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        color_type = ColorType.rgb(None)
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        rgba = ColorType.rgba()
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        indexed = ColorType.indexed([(255, 0, 0)])
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        grayscale = ColorType.grayscale(None)
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        grayscale_alpha = ColorType.grayscale_alpha()
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        strip = StripChunks.strip(["tEXt"])
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        keep = StripChunks.keep({"iCCP"})
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        libdeflater = Deflaters.libdeflater(12)
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        zopfli = Deflaters.zopfli(15)

    assert color_type.kind == "rgb"
    assert rgba.kind == "rgba"
    assert indexed.kind == "indexed"
    assert grayscale.kind == "grayscale"
    assert grayscale_alpha.kind == "grayscale_alpha"
    assert strip.mode == "strip"
    assert keep.mode == "keep"
    assert libdeflater.kind == "libdeflater"
    assert zopfli.kind == "zopfli"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group dev pytest tests/test_api.py::test_pyoxipng_compatibility_exports_and_docstrings tests/test_api.py::test_pyoxipng_compatibility_factories_warn -v -ra
```

Expected: fail because `RowFilter`, `Deflaters`, and compatibility factories do not exist.

- [ ] **Step 3: Add compatibility objects in `oxipng/__init__.py`**

Replace the imports at the top of `oxipng/__init__.py` with:

```python
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any
from warnings import warn
```

Add this warning constant and helper below the imports:

```python
PYOXIPNG_COMPAT_WARNING = (
    "pyoxipng compatibility path is unsupported; "
    "migrate to oxipng-pybind's stable API."
)


def _warn_pyoxipng_compat() -> None:
    warn(PYOXIPNG_COMPAT_WARNING, DeprecationWarning, stacklevel=3)
```

Update `Interlacing` to include pyoxipng aliases:

```python
class Interlacing(Enum):
    """PNG interlacing behavior."""

    keep = "keep"
    off = "off"
    on = "on"
    Off = "off"
    Adam7 = "on"
```

Add `RowFilter` after `FilterStrategy`:

```python
class RowFilter(Enum):
    """pyoxipng-compatible row filter names."""

    none = "none"
    sub = "sub"
    up = "up"
    average = "average"
    paeth = "paeth"
    minsum = "minsum"
    entropy = "entropy"
    bigrams = "bigrams"
    bigent = "bigent"
    brute = "brute"
```

Add these compatibility data classes above `ColorType`:

```python
@dataclass(frozen=True)
class _CompatColorType:
    kind: str
    bit_depth: int
    palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None
    transparent: int | tuple[int, int, int] | None = None


@dataclass(frozen=True)
class _CompatStripChunks:
    mode: str
    names: tuple[str, ...]


@dataclass(frozen=True)
class _CompatDeflater:
    kind: str
    value: int
```

Add this method to `ColorType`:

```python
    def __call__(
        self,
        transparent: int | tuple[int, int, int] | list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None,
        *,
        bit_depth: int | BitDepth = BitDepth.eight,
    ) -> _CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        raw_bit_depth = bit_depth.value if isinstance(bit_depth, BitDepth) else bit_depth
        if self is ColorType.indexed:
            if transparent is None:
                raise ValueError("indexed color_type requires a palette")
            return _CompatColorType("indexed", raw_bit_depth, palette=list(transparent))
        if self in {ColorType.rgba, ColorType.grayscale_alpha}:
            if transparent is not None:
                raise ValueError(f"{self.value} does not accept transparent")
            return _CompatColorType(self.value, raw_bit_depth)
        return _CompatColorType(self.value, raw_bit_depth, transparent=transparent)
```

Assign concise per-member callable docstrings after `ColorType` is defined:

```python
ColorType.__call__.__doc__ = "Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."
```

Add static factories to `StripChunks`:

```python
    @staticmethod
    def strip(names: list[str] | tuple[str, ...] | set[str]) -> _CompatStripChunks:
        """Create a pyoxipng-compatible strip-chunk option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatStripChunks("strip", tuple(names))

    @staticmethod
    def keep(names: list[str] | tuple[str, ...] | set[str]) -> _CompatStripChunks:
        """Create a pyoxipng-compatible keep-chunk option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatStripChunks("keep", tuple(names))
```

Add `Deflaters` after `Deflater`:

```python
class Deflaters:
    """pyoxipng-compatible DEFLATE option factories."""

    @staticmethod
    def libdeflater(compression: int = 11) -> _CompatDeflater:
        """Create a pyoxipng-compatible libdeflater option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatDeflater("libdeflater", compression)

    @staticmethod
    def zopfli(iterations: int = 15) -> _CompatDeflater:
        """Create a pyoxipng-compatible zopfli option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatDeflater("zopfli", iterations)
```

Add `Deflaters` and `RowFilter` to `__all__`.

- [ ] **Step 4: Update `oxipng/__init__.pyi` for scaffold types**

Add `Any` and overload imports:

```python
from typing import Any, overload
```

Add these compatibility declarations:

```python
class RowFilter(Enum):
    none = "none"
    sub = "sub"
    up = "up"
    average = "average"
    paeth = "paeth"
    minsum = "minsum"
    entropy = "entropy"
    bigrams = "bigrams"
    bigent = "bigent"
    brute = "brute"

class _CompatColorType:
    kind: str
    bit_depth: int
    palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None
    transparent: int | tuple[int, int, int] | None

class _CompatStripChunks:
    mode: str
    names: tuple[str, ...]

class _CompatDeflater:
    kind: str
    value: int

class Deflaters:
    @staticmethod
    def libdeflater(compression: int = 11) -> _CompatDeflater:
        """Create a pyoxipng-compatible libdeflater option; emits DeprecationWarning."""

    @staticmethod
    def zopfli(iterations: int = 15) -> _CompatDeflater:
        """Create a pyoxipng-compatible zopfli option; emits DeprecationWarning."""
```

Add aliases to `Interlacing`:

```python
    Off = "off"
    Adam7 = "on"
```

Add the same static `strip` and `keep` signatures to `StripChunks`.

Add this callable signature to `ColorType`:

```python
    def __call__(
        self,
        transparent: int | tuple[int, int, int] | list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None,
        *,
        bit_depth: BitDepth | int = BitDepth.eight,
    ) -> _CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""
```

- [ ] **Step 5: Run facade tests**

Run:

```bash
uv run --group dev pytest tests/test_api.py::test_pyoxipng_compatibility_exports_and_docstrings tests/test_api.py::test_pyoxipng_compatibility_factories_warn -v -ra
```

Expected: both tests pass.

- [ ] **Step 6: Run Python lint and type checks**

Run:

```bash
uv run --group dev ruff check oxipng tests/test_api.py
uv run --group dev basedpyright
```

Expected: Ruff reports `All checks passed!`; basedpyright reports `0 errors, 0 warnings, 0 notes`.

- [ ] **Step 7: Commit facade scaffolding**

Run:

```bash
git add oxipng/__init__.py oxipng/__init__.pyi tests/test_api.py
git commit -m "feat: add pyoxipng compatibility facade"
```

Expected: commit succeeds.

## Task 2: Parse Compatibility Option Objects in Rust

**Files:**

- Modify: `tests/test_api.py`
- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`

- [ ] **Step 1: Write failing tests for `RowFilter`, `StripChunks`, and `Deflaters` parsing**

Add these tests near the existing option parsing tests:

```python
def test_pyoxipng_rowfilter_values_optimize_memory(png_bytes: bytes) -> None:
    output = optimize_from_memory(png_bytes, filter={RowFilter.none, RowFilter.sub})

    assert_readable_png_bytes(output)


def test_pyoxipng_strip_factories_optimize_file(png_path: Path) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        strip = StripChunks.strip(["tEXt"])

    optimize(png_path, strip=strip)

    assert_readable_png_path(png_path)


def test_pyoxipng_keep_factories_optimize_file(png_path: Path) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        keep = StripChunks.keep({"iCCP"})

    optimize(png_path, strip=keep)

    assert_readable_png_path(png_path)


def test_pyoxipng_deflaters_optimize_memory(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        libdeflater = Deflaters.libdeflater(12)
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        zopfli = Deflaters.zopfli(1)

    assert_readable_png_bytes(optimize_from_memory(png_bytes, deflate=libdeflater))
    assert_readable_png_bytes(optimize_from_memory(png_bytes, deflate=zopfli))


@pytest.mark.parametrize("names", [["abc"], ["abcde"], ["ab1d"]])
def test_pyoxipng_strip_factories_reject_invalid_chunk_names(
    png_bytes: bytes,
    names: list[str],
) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        strip = StripChunks.strip(names)

    with pytest.raises(ValueError, match="chunk name"):
        optimize_from_memory(png_bytes, strip=strip)


@pytest.mark.parametrize(("factory", "value"), [(Deflaters.libdeflater, 13), (Deflaters.zopfli, 0)])
def test_pyoxipng_deflaters_reject_invalid_values(
    png_bytes: bytes,
    factory: Any,
    value: int,
) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        deflater = factory(value)

    with pytest.raises(ValueError, match="deflate"):
        optimize_from_memory(png_bytes, deflate=deflater)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -k "pyoxipng_rowfilter or pyoxipng_strip or pyoxipng_keep or pyoxipng_deflaters" -v -ra
```

Expected: fail because Rust parsing does not recognize sets of enum values or compatibility objects.

- [ ] **Step 3: Add Rust compatibility helpers**

In `src/lib.rs`, add imports:

```rust
use pyo3::ffi::c_str;
use pyo3::exceptions::{PyDeprecationWarning, PyException, PyFileExistsError, PyOSError, PyTypeError, PyValueError};
use std::num::NonZeroU8;
```

Replace the existing exceptions import with the combined import above.

Add these helpers after `parse_bool`:

```rust
fn warn_pyoxipng_compat(py: Python<'_>) -> PyResult<()> {
    PyErr::warn(
        py,
        &py.get_type::<PyDeprecationWarning>(),
        c_str!("pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API."),
        2,
    )
}

fn object_type_name(value: &Bound<'_, PyAny>) -> PyResult<String> {
    value.get_type().qualname().map(|name| name.to_string())
}

fn py_string_attr(value: &Bound<'_, PyAny>, name: &str) -> PyResult<Option<String>> {
    match value.getattr(name) {
        Ok(attr) => Ok(Some(attr.extract()?)),
        Err(_) => Ok(None),
    }
}

fn py_int_attr<T>(value: &Bound<'_, PyAny>, name: &str) -> PyResult<Option<T>>
where
    T: for<'a> FromPyObject<'a, 'a>,
{
    match value.getattr(name) {
        Ok(attr) => Ok(Some(attr.extract()?)),
        Err(_) => Ok(None),
    }
}
```

- [ ] **Step 4: Support sets in `parse_filters` and RowFilter values**

Update imports to include `PySet`:

```rust
use pyo3::types::{PyBool, PyByteArray, PyBytes, PyDict, PyList, PySet, PyString, PyTuple};
```

In `parse_filters`, treat `PySet` like list and tuple:

```rust
    if let Ok(set) = value.downcast::<PySet>() {
        if set.is_empty() {
            return Err(PyValueError::new_err("filter must not be empty"));
        }
        for item in set.iter() {
            filters.insert(parse_filter_strategy(&item)?);
        }
        return Ok(filters);
    }
```

No warning is required for `RowFilter` at parse time because it is an enum-style compatibility alias, not a callable.

- [ ] **Step 5: Parse `_CompatStripChunks`**

Add this helper above `parse_strip`:

```rust
fn parse_chunk_name_text(name: &str) -> PyResult<[u8; 4]> {
    let bytes = name.as_bytes();
    let name: [u8; 4] = bytes
        .try_into()
        .map_err(|_| PyValueError::new_err("chunk name must be exactly 4 ASCII letters"))?;
    validate_png_chunk_name(name)
}
```

Update `parse_strip` before the existing string match:

```rust
    if object_type_name(value)?.ends_with("_CompatStripChunks") {
        let mode = py_string_attr(value, "mode")?
            .ok_or_else(|| PyValueError::new_err("strip compatibility object missing mode"))?;
        let names = value
            .getattr("names")?
            .downcast_into::<PyTuple>()
            .map_err(|_| PyValueError::new_err("strip compatibility object names must be a tuple"))?;
        let mut parsed = IndexSet::new();
        for item in names.iter() {
            let name: String = item.extract()?;
            parsed.insert(parse_chunk_name_text(&name)?);
        }
        return match mode.as_str() {
            "strip" => Ok(oxi::StripChunks::Strip(parsed)),
            "keep" => Ok(oxi::StripChunks::Keep(parsed)),
            _ => Err(PyValueError::new_err("strip compatibility mode must be strip or keep")),
        };
    }
```

- [ ] **Step 6: Parse `_CompatDeflater`**

Update `parse_deflater` before the existing string match:

```rust
    if object_type_name(value)?.ends_with("_CompatDeflater") {
        let kind = py_string_attr(value, "kind")?
            .ok_or_else(|| PyValueError::new_err("deflate compatibility object missing kind"))?;
        let raw_value: i64 = py_int_attr(value, "value")?
            .ok_or_else(|| PyValueError::new_err("deflate compatibility object missing value"))?;
        return match kind.as_str() {
            "libdeflater" => {
                let compression = u8::try_from(raw_value)
                    .map_err(|_| PyValueError::new_err("deflate libdeflater compression must be 0-12"))?;
                if compression > 12 {
                    return Err(PyValueError::new_err("deflate libdeflater compression must be 0-12"));
                }
                Ok(oxi::Deflater::Libdeflater { compression })
            }
            "zopfli" => {
                let iterations = u8::try_from(raw_value)
                    .ok()
                    .and_then(NonZeroU8::new)
                    .ok_or_else(|| PyValueError::new_err("deflate zopfli iterations must be 1-255"))?;
                Ok(oxi::Deflater::Zopfli(oxi::ZopfliOptions {
                    iteration_count: iterations,
                    ..Default::default()
                }))
            }
            _ => Err(PyValueError::new_err("deflate compatibility kind must be libdeflater or zopfli")),
        };
    }
```

- [ ] **Step 7: Run compatibility option tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -k "pyoxipng_rowfilter or pyoxipng_strip or pyoxipng_keep or pyoxipng_deflaters" -v -ra
```

Expected: selected tests pass.

- [ ] **Step 8: Run lint and type checks**

Run:

```bash
cargo fmt --check
cargo clippy -- -D warnings
uv run --group dev ruff check oxipng tests/test_api.py
uv run --group dev basedpyright
```

Expected: all commands pass.

- [ ] **Step 9: Commit compatibility option parsing**

Run:

```bash
git add src/lib.rs oxipng/__init__.pyi tests/test_api.py
git commit -m "feat: parse pyoxipng compatibility options"
```

Expected: commit succeeds.

## Task 3: Add RawImage Constructor Compatibility

**Files:**

- Modify: `tests/test_api.py`
- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`

- [ ] **Step 1: Write failing tests for pyoxipng-style RawImage construction**

Add these tests near the existing raw image tests:

```python
def test_pyoxipng_raw_image_constructor_accepts_rgb_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        color_type = ColorType.rgb(None)
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0]), 1, 1, color_type=color_type)

    output = raw.create_optimized_png()

    assert_readable_png_bytes(output)


def test_pyoxipng_raw_image_constructor_accepts_rgba_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        color_type = ColorType.rgba()
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0, 255]), 1, 1, color_type=color_type)

    assert_readable_png_bytes(raw.create_optimized_png())


def test_pyoxipng_raw_image_constructor_accepts_indexed_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        color_type = ColorType.indexed([(255, 0, 0)])
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        raw = RawImage(bytes([0]), 1, 1, color_type=color_type)

    assert_readable_png_bytes(raw.create_optimized_png())


def test_pyoxipng_raw_image_constructor_requires_compat_color_type() -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        with pytest.raises(TypeError, match="color_type"):
            RawImage(bytes([255, 0, 0]), 1, 1, color_type="rgb")


def test_stable_raw_image_constructor_does_not_warn() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(raw.create_optimized_png())
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -k "pyoxipng_raw_image_constructor or stable_raw_image_constructor" -v -ra
```

Expected: compatibility constructor tests fail because the native `RawImage` constructor does not accept `(data, width, height, color_type=...)`.

- [ ] **Step 3: Change the PyO3 constructor to accept both call shapes**

In `src/lib.rs`, replace the current `#[new]` function signature with a tuple/kwargs parser:

```rust
    #[new]
    #[pyo3(signature = (*args, **kwargs))]
    fn new(args: &Bound<'_, PyTuple>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        if args.len() == 5 {
            return Self::new_stable(args, kwargs);
        }
        if args.len() == 3 {
            return Self::new_pyoxipng_compat(args, kwargs);
        }
        Err(PyTypeError::new_err(
            "RawImage expects either (width, height, color_type, bit_depth, data) or (data, width, height, color_type=...)",
        ))
    }
```

Add `new_stable` and `new_pyoxipng_compat` as private methods in the same `impl PyRawImage` block:

```rust
    fn new_stable(args: &Bound<'_, PyTuple>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let width: u32 = args.get_item(0)?.extract()?;
        let height: u32 = args.get_item(1)?.extract()?;
        let color_type = args.get_item(2)?;
        let bit_depth = args.get_item(3)?;
        let data = args.get_item(4)?;
        let palette = kwargs.and_then(|dict| dict.get_item("palette").transpose()).transpose()?;
        let transparent = kwargs
            .and_then(|dict| dict.get_item("transparent").transpose())
            .transpose()?;
        Self::from_parts(width, height, &color_type, &bit_depth, &data, palette.as_ref(), transparent.as_ref())
    }

    fn new_pyoxipng_compat(args: &Bound<'_, PyTuple>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        warn_pyoxipng_compat(args.py())?;
        let data = args.get_item(0)?;
        let width: u32 = args.get_item(1)?.extract()?;
        let height: u32 = args.get_item(2)?.extract()?;
        let kwargs = kwargs.ok_or_else(|| PyTypeError::new_err("color_type is required"))?;
        let color_type = kwargs
            .get_item("color_type")?
            .ok_or_else(|| PyTypeError::new_err("color_type is required"))?;
        if !object_type_name(&color_type)?.ends_with("_CompatColorType") {
            return Err(PyTypeError::new_err("color_type must be created by ColorType compatibility factories"));
        }
        let kind = py_string_attr(&color_type, "kind")?
            .ok_or_else(|| PyValueError::new_err("color_type compatibility object missing kind"))?;
        let bit_depth: u8 = py_int_attr(&color_type, "bit_depth")?
            .ok_or_else(|| PyValueError::new_err("color_type compatibility object missing bit_depth"))?;
        let palette = color_type.getattr("palette").ok();
        let transparent = color_type.getattr("transparent").ok();
        Self::from_parts(
            width,
            height,
            &kind.into_pyobject(args.py())?,
            &bit_depth.into_pyobject(args.py())?,
            &data,
            palette.as_ref().filter(|value| !value.is_none()),
            transparent.as_ref().filter(|value| !value.is_none()),
        )
    }

    fn from_parts(
        width: u32,
        height: u32,
        color_type: &Bound<'_, PyAny>,
        bit_depth: &Bound<'_, PyAny>,
        data: &Bound<'_, PyAny>,
        palette: Option<&Bound<'_, PyAny>>,
        transparent: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Self> {
        let bit_depth = parse_bit_depth(bit_depth)?;
        let color_type = parse_color_type(color_type, bit_depth, palette, transparent)?;
        let data = bytes_like_to_vec(data)?;
        if let oxi::ColorType::Indexed { palette } = &color_type {
            validate_indexed_pixels(&data, width, height, palette.len(), bit_depth)?;
        }
        let inner = oxi::RawImage::new(width, height, color_type, bit_depth, data)
            .map_err(map_png_error)?;
        Ok(Self { inner })
    }
```

Remove the old constructor body after `from_parts` is in place.

- [ ] **Step 4: Update RawImage stubs with overloads**

In `oxipng/__init__.pyi`, replace the single `RawImage.__init__` signature with:

```python
    @overload
    def __init__(
        self,
        width: int,
        height: int,
        color_type: ColorType | str,
        bit_depth: BitDepth | int,
        data: BytesLike,
        *,
        palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None,
        transparent: int | tuple[int, int, int] | None = None,
    ) -> None:
        """Create a raw image from packed pixel data."""

    @overload
    def __init__(
        self,
        data: BytesLike,
        width: int,
        height: int,
        *,
        color_type: _CompatColorType,
    ) -> None:
        """Create a pyoxipng-compatible raw image; emits DeprecationWarning."""
```

- [ ] **Step 5: Run raw image compatibility tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -k "pyoxipng_raw_image_constructor or stable_raw_image_constructor" -v -ra
```

Expected: selected tests pass.

- [ ] **Step 6: Run full API tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -v -ra
```

Expected: all `tests/test_api.py` tests pass.

- [ ] **Step 7: Run Rust and Python checks**

Run:

```bash
cargo fmt --check
cargo clippy -- -D warnings
uv run --group dev ruff check oxipng tests/test_api.py
uv run --group dev basedpyright
```

Expected: all commands pass.

- [ ] **Step 8: Commit RawImage compatibility**

Run:

```bash
git add src/lib.rs oxipng/__init__.pyi tests/test_api.py
git commit -m "feat: add pyoxipng raw image compatibility"
```

Expected: commit succeeds.

## Task 4: Add Advanced Boolean Options and Timeout

**Files:**

- Modify: `tests/test_api.py`
- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`

- [ ] **Step 1: Write failing tests for advanced options and warnings**

Add these tests near the option parsing tests:

```python
@pytest.mark.parametrize(
    "option",
    [
        "optimize_alpha",
        "bit_depth_reduction",
        "color_type_reduction",
        "palette_reduction",
        "grayscale_reduction",
        "idat_recoding",
        "scale_16",
        "fast_evaluation",
    ],
)
def test_pyoxipng_advanced_bool_options_warn_and_optimize_memory(
    png_bytes: bytes,
    option: str,
) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        output = optimize_from_memory(png_bytes, **{option: False})

    assert_readable_png_bytes(output)


def test_pyoxipng_timeout_warns_and_optimizes_memory(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYROXIPNG_WARNING):
        output = optimize_from_memory(png_bytes, timeout=1.0)

    assert_readable_png_bytes(output)


@pytest.mark.parametrize("option", ["optimize_alpha", "bit_depth_reduction", "timeout"])
def test_pyoxipng_advanced_options_reject_invalid_values(option: str, png_bytes: bytes) -> None:
    value: object = "bad"

    with pytest.raises((TypeError, ValueError), match=option):
        optimize_from_memory(png_bytes, **{option: value})
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -k "pyoxipng_advanced or pyoxipng_timeout" -v -ra
```

Expected: fail because advanced keywords are currently unsupported.

- [ ] **Step 3: Add advanced fields to `parse_options`**

In `src/lib.rs`, add:

```rust
use std::time::Duration;
```

Add variables in `parse_options` after `preserve_attrs`:

```rust
    let mut optimize_alpha = None;
    let mut bit_depth_reduction = None;
    let mut color_type_reduction = None;
    let mut palette_reduction = None;
    let mut grayscale_reduction = None;
    let mut idat_recoding = None;
    let mut scale_16 = None;
    let mut fast_evaluation = None;
    let mut timeout = None;
```

Add this helper near `parse_bool`:

```rust
fn parse_timeout(value: &Bound<'_, PyAny>) -> PyResult<Option<Duration>> {
    if value.is_none() {
        return Ok(None);
    }
    let seconds: f64 = value
        .extract()
        .map_err(|_| PyTypeError::new_err("timeout must be a non-negative number of seconds or None"))?;
    if !seconds.is_finite() || seconds < 0.0 {
        return Err(PyValueError::new_err(
            "timeout must be a non-negative number of seconds or None",
        ));
    }
    Ok(Some(Duration::from_secs_f64(seconds)))
}
```

Add match arms in `parse_options`:

```rust
                "optimize_alpha" => {
                    warn_pyoxipng_compat(value.py())?;
                    optimize_alpha = Some(parse_bool(&value, "optimize_alpha")?);
                }
                "bit_depth_reduction" => {
                    warn_pyoxipng_compat(value.py())?;
                    bit_depth_reduction = Some(parse_bool(&value, "bit_depth_reduction")?);
                }
                "color_type_reduction" => {
                    warn_pyoxipng_compat(value.py())?;
                    color_type_reduction = Some(parse_bool(&value, "color_type_reduction")?);
                }
                "palette_reduction" => {
                    warn_pyoxipng_compat(value.py())?;
                    palette_reduction = Some(parse_bool(&value, "palette_reduction")?);
                }
                "grayscale_reduction" => {
                    warn_pyoxipng_compat(value.py())?;
                    grayscale_reduction = Some(parse_bool(&value, "grayscale_reduction")?);
                }
                "idat_recoding" => {
                    warn_pyoxipng_compat(value.py())?;
                    idat_recoding = Some(parse_bool(&value, "idat_recoding")?);
                }
                "scale_16" => {
                    warn_pyoxipng_compat(value.py())?;
                    scale_16 = Some(parse_bool(&value, "scale_16")?);
                }
                "fast_evaluation" => {
                    warn_pyoxipng_compat(value.py())?;
                    fast_evaluation = Some(parse_bool(&value, "fast_evaluation")?);
                }
                "timeout" => {
                    warn_pyoxipng_compat(value.py())?;
                    timeout = parse_timeout(&value)?;
                }
```

After `let mut options = oxi::Options::from_preset(level);`, apply parsed fields:

```rust
    if let Some(value) = optimize_alpha {
        options.optimize_alpha = value;
    }
    if let Some(value) = bit_depth_reduction {
        options.bit_depth_reduction = value;
    }
    if let Some(value) = color_type_reduction {
        options.color_type_reduction = value;
    }
    if let Some(value) = palette_reduction {
        options.palette_reduction = value;
    }
    if let Some(value) = grayscale_reduction {
        options.grayscale_reduction = value;
    }
    if let Some(value) = idat_recoding {
        options.idat_recoding = value;
    }
    if let Some(value) = scale_16 {
        options.scale_16 = value;
    }
    if let Some(value) = fast_evaluation {
        options.fast_evaluation = value;
    }
    options.timeout = timeout;
```

- [ ] **Step 4: Update stubs for advanced keyword parameters**

In `oxipng/__init__.pyi`, add these keyword parameters to `optimize`, `optimize_from_memory`, and `RawImage.create_optimized_png` signatures:

```python
    optimize_alpha: bool | None = None,
    bit_depth_reduction: bool | None = None,
    color_type_reduction: bool | None = None,
    palette_reduction: bool | None = None,
    grayscale_reduction: bool | None = None,
    idat_recoding: bool | None = None,
    scale_16: bool | None = None,
    fast_evaluation: bool | None = None,
    timeout: float | None = None,
```

Keep existing stable keyword order before these compatibility-only parameters.

- [ ] **Step 5: Run advanced option tests**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -k "pyoxipng_advanced or pyoxipng_timeout" -v -ra
```

Expected: selected tests pass.

- [ ] **Step 6: Verify stable API still does not warn**

Add this test near the advanced option tests:

```python
def test_stable_option_paths_do_not_emit_deprecation_warnings(png_bytes: bytes) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = optimize_from_memory(
            png_bytes,
            level=2,
            interlace=Interlacing.keep,
            strip=StripChunks.none,
            deflate=Deflater.libdeflater,
            filter=FilterStrategy.none,
            fix_errors=False,
            force=False,
        )

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)
```

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py::test_stable_option_paths_do_not_emit_deprecation_warnings -v -ra
```

Expected: test passes.

- [ ] **Step 7: Run full API tests and checks**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -v -ra
cargo fmt --check
cargo clippy -- -D warnings
uv run --group dev ruff check oxipng tests/test_api.py
uv run --group dev basedpyright
```

Expected: all commands pass.

- [ ] **Step 8: Commit advanced compatibility options**

Run:

```bash
git add src/lib.rs oxipng/__init__.pyi tests/test_api.py
git commit -m "feat: add pyoxipng advanced option compatibility"
```

Expected: commit succeeds.

## Task 5: Update Docs and Final Verification

**Files:**

- Modify: `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`
- Verify: `oxipng/__init__.py`
- Verify: `oxipng/__init__.pyi`
- Verify: `src/lib.rs`
- Verify: `tests/test_api.py`

- [ ] **Step 1: Update the remaining-work plan**

In `docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md`, update the `pyoxipng Compatibility Gaps` and `pyoxipng Parity Roadmap` sections:

```markdown
- Naming aliases, raw-image constructor compatibility, explicit strip/keep
  chunk factories, deflater factories, and advanced option keywords now exist
  as warning-emitting migration paths.
- Compatibility paths emit `DeprecationWarning` and remain unsupported for new
  code; users should migrate to the stable oxipng-pybind API.
- Packaging parity, PyPI publishing, musllinux/32-bit wheels, and a migration
  guide remain open.
```

- [ ] **Step 2: Run markdown lint**

Run:

```bash
uv run --group dev pre-commit run markdownlint-cli2 --files docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md
```

Expected:

```text
markdownlint-cli2........................................................Passed
```

- [ ] **Step 3: Run full verification**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest
cargo fmt --check
cargo clippy -- -D warnings
uv run --group dev ruff check oxipng scripts tests
uv run --group dev basedpyright
uv run --group dev pre-commit run markdownlint-cli2 --files docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md
```

Expected:

- pytest passes all tests;
- `cargo fmt --check` exits 0;
- clippy exits 0 with warnings denied;
- Ruff reports `All checks passed!`;
- basedpyright reports `0 errors, 0 warnings, 0 notes`;
- markdownlint passes.

- [ ] **Step 4: Inspect compatibility docstrings manually**

Run:

```bash
uv run --no-sync --group dev python - <<'PY'
import oxipng

objects = [
    oxipng.ColorType.rgb.__call__,
    oxipng.ColorType.rgba.__call__,
    oxipng.ColorType.indexed.__call__,
    oxipng.ColorType.grayscale.__call__,
    oxipng.ColorType.grayscale_alpha.__call__,
    oxipng.StripChunks.strip,
    oxipng.StripChunks.keep,
    oxipng.Deflaters.libdeflater,
    oxipng.Deflaters.zopfli,
]
for obj in objects:
    print(obj.__doc__)
PY
```

Expected: every printed docstring is one concise sentence and mentions `DeprecationWarning`.

- [ ] **Step 5: Inspect final diff**

Run:

```bash
git diff -- oxipng/__init__.py oxipng/__init__.pyi src/lib.rs tests/test_api.py docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md
```

Expected: diff only adds pyoxipng compatibility paths, warnings, docstrings, tests, docs, and plan checkboxes.

- [ ] **Step 6: Commit docs and final checklist**

Run:

```bash
git add docs/plans/2026-05-26-remaining-work-and-pyoxipng-gaps.md docs/superpowers/plans/2026-05-26-pyoxipng-compatibility.md
git commit -m "docs: record pyoxipng compatibility implementation"
```

Expected: commit succeeds.

## Self-Review

Spec coverage:

- Naming aliases are covered by Task 1.
- Compatibility warnings and docstrings are covered by Tasks 1, 2, 3, 4, and 5.
- Raw image constructor compatibility is covered by Task 3.
- Strip and deflater compatibility factories are covered by Tasks 1 and 2.
- Advanced boolean options and timeout are covered by Task 4.
- Stable API non-warning behavior is covered by Tasks 3 and 4.
- Packaging parity is intentionally out of scope.

Placeholder scan:

- No placeholder tasks remain.
- Every task has exact file paths, commands, expected results, and concrete code snippets.
- Open decisions from the spec are resolved in the plan: `RowFilter` is a distinct enum, `Deflaters` coexists with `Deflater`, compatibility objects are Python dataclasses parsed by Rust, and advanced options are implemented as warning-emitting keyword parameters.

Type consistency:

- Compatibility object names match between Python facade, stubs, tests, and Rust parser checks.
- Warning text is identical across Python and Rust.
- Timeout is represented as seconds in Python and converted to `std::time::Duration` in Rust.

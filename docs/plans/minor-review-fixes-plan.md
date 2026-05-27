# Minor Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix or explicitly close the remaining minor code-review findings while preserving the stable API contract and pyoxipng compatibility behavior chosen during interactive review.

**Architecture:** Execute in an isolated git worktree, then dispatch independent implementation bundles in parallel where write sets do not overlap. Runtime API parsing remains in the Rust/PyO3 wrapper, compatibility warnings and helper metadata stay in the Python compatibility layer, and CI helper hardening stays in the script or Makefile that owns each behavior.

**Tech Stack:** Rust, PyO3, Python, pytest, mypy, Ruff, Make, uv, rustdoc JSON, git worktrees.

---

## Execution Model

Use this plan from a clean branch created with `superpowers:using-git-worktrees`. The recommended branch name is `minor-review-fixes`, created from the current `main` that already contains the major and medium review fixes.

Use `superpowers:dispatching-parallel-agents` to run these independent bundles in parallel:

- **Worker A:** Task 1, runtime API validation and compatibility behavior.
- **Worker B:** Task 2, dependency classifier hardening.
- **Worker C:** Task 3, rustdoc JSON upstream scanner.
- **Worker D:** Task 4, streamed AI log filtering.
- **Worker E:** Task 5, pinned cargo-deny bootstrap.

After all workers are merged into the isolated branch, run Task 6 as the final integration and report update task. Use `superpowers:subagent-driven-development` for every implementation task: one fresh subagent per task, review each result before merging, then run the task-specific verification.

## File Structure

- `src/lib.rs`: Rust/PyO3 option parsing, input validation order, backup error mapping, chunk name validation, compatibility object detection, and pyoxipng-compatible filter warning paths.
- `oxipng/_pyoxipng_compat.py`: pyoxipng compatibility descriptors, marker fields, immutable palette snapshots, and deprecated enum lookup warnings.
- `oxipng/__init__.py`: public Python exports and stable API warning behavior if needed.
- `oxipng/__init__.pyi`: stable typing surface for filters, compatibility helpers, and tuple-based palette descriptors.
- `tests/test_api.py`: behavioral tests for runtime parsing, warnings, compatibility, backup errors, max decompressed size range handling, chunk validation, and docs-backed ICC behavior.
- `tests/typing_filter_options.py`: typing assertions for accepted stable filter inputs.
- `scripts/classify_dependency_refresh.py`: executable resolution and GitHub output newline guards.
- `tests/test_dependency_refresh_classification.py`: tests for dependency classifier command resolution and output safety.
- `scripts/scan_upstream_surface.py`: rustdoc JSON collection and public item extraction.
- `tests/test_scan_upstream_surface.py`: rustdoc JSON fixture tests covering comments, strings, macros, `pub fn`, `pub const fn`, and `pub async fn`.
- `.github/workflows/upstream-bump.yml`: install the rustdoc JSON-capable toolchain only if the scanner cannot run on the existing pinned Rust toolchain.
- `scripts/ai_filter_log.py`: bounded streaming or tailing log summarization.
- `tests/test_scripts.py`: large-log tests for AI log filtering.
- `Makefile`: pinned `cargo-deny` installation and version check during setup/bootstrap.
- `tests/test_makefile.py`: Makefile assertions for pinned `cargo-deny` behavior.
- `docs/usage/file-optimization.md`: direct backup-write limitation note, preserving Rust behavior.
- `docs/usage/raw-image.md`: ICC profile behavior note if upstream gives no success signal.
- `docs/plans/full-code-review-report.md`: close minor findings with fixed/no-change disposition after implementation.

## Task 1: Runtime API Validation and Compatibility

**Findings covered:** Minor 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, and 12.

**Files:**

- Modify: `src/lib.rs`
- Modify: `oxipng/_pyoxipng_compat.py`
- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `docs/usage/file-optimization.md`
- Modify: `docs/usage/raw-image.md`
- Test: `tests/test_api.py`
- Test: `tests/typing_filter_options.py`

- [x] **Step 1: Create the API behavior tests**

Add focused tests to `tests/test_api.py`. Reuse existing PNG fixtures and helper functions already present in that file.

```python
class _RaisesOnBytes:
    def __bytes__(self) -> bytes:
        raise AssertionError("buffer conversion should not run before option validation")


class _FakeEnumValue:
    def __init__(self, value: object) -> None:
        self.value = value


def test_optimize_from_memory_validates_options_before_buffer_copy() -> None:
    with pytest.raises(TypeError, match="level"):
        oxipng.optimize_from_memory(_RaisesOnBytes(), level=True)  # type: ignore[arg-type]


def test_backup_missing_input_raises_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "missing.png"
    with pytest.raises(FileNotFoundError):
        oxipng.optimize(missing, backup=True)


@pytest.mark.parametrize("value", [0, 10_000_000, 2**64 - 1])
def test_max_decompressed_size_accepts_u64_range(value: int) -> None:
    options = oxipng.Options(max_decompressed_size=value)
    assert options.max_decompressed_size == value


@pytest.mark.parametrize("value", [-1, 2**64, 10**100])
def test_max_decompressed_size_rejects_out_of_range_ints(value: int) -> None:
    with pytest.raises(ValueError, match="max_decompressed_size"):
        oxipng.Options(max_decompressed_size=value)


@pytest.mark.parametrize("value", [True, 1.5, "100"])
def test_max_decompressed_size_rejects_non_int_values(value: object) -> None:
    with pytest.raises(TypeError, match="max_decompressed_size"):
        oxipng.Options(max_decompressed_size=value)  # type: ignore[arg-type]


def test_numeric_enum_value_rejects_bool_after_value_extraction() -> None:
    with pytest.raises(TypeError, match="bit_depth"):
        oxipng.RawImage(
            data=b"\x00\x00\x00",
            width=1,
            height=1,
            color_type=oxipng.ColorType.RGB,
            bit_depth=_FakeEnumValue(True),  # type: ignore[arg-type]
        )


def test_add_png_chunk_validates_name_before_data_copy() -> None:
    image = oxipng.RawImage(
        data=b"\x00\x00\x00",
        width=1,
        height=1,
        color_type=oxipng.ColorType.RGB,
        bit_depth=8,
    )
    with pytest.raises(ValueError, match="chunk name"):
        image.add_png_chunk("bad", _RaisesOnBytes())  # type: ignore[arg-type]


def test_stable_predefined_filters_reject_unordered_collections() -> None:
    with pytest.raises(TypeError, match="ordered"):
        oxipng.FilterStrategy.predefined({oxipng.RowFilter.NONE, oxipng.RowFilter.SUB})

    with pytest.raises(TypeError, match="ordered"):
        oxipng.Options(filter={oxipng.RowFilter.NONE, oxipng.RowFilter.SUB})  # type: ignore[arg-type]


def test_pyoxipng_filter_set_is_accepted_with_compat_warning(sample_png: bytes) -> None:
    import pyoxipng

    with pytest.warns(DeprecationWarning, match="set"):
        optimized = pyoxipng.optimize_from_memory(
            sample_png,
            filter={pyoxipng.RowFilter.none, pyoxipng.RowFilter.sub},
        )

    assert optimized.startswith(b"\x89PNG")


def test_deprecated_pyoxipng_row_filter_lookups_warn() -> None:
    import pyoxipng

    with pytest.warns(DeprecationWarning, match="RowFilter"):
        assert pyoxipng.RowFilter.none is pyoxipng.RowFilter.NONE

    with pytest.warns(DeprecationWarning, match="RowFilter"):
        assert pyoxipng.RowFilter["none"] is pyoxipng.RowFilter.NONE

    with pytest.warns(DeprecationWarning, match="RowFilter"):
        assert pyoxipng.RowFilter("none") is pyoxipng.RowFilter.NONE


def test_compat_color_type_palette_is_immutable_snapshot() -> None:
    import pyoxipng

    palette = [(1, 2, 3), (4, 5, 6)]
    color_type = pyoxipng.ColorType.indexed(palette)
    palette.append((7, 8, 9))

    assert color_type.palette == ((1, 2, 3), (4, 5, 6))


def test_fake_compat_color_type_without_marker_is_rejected() -> None:
    class ColorType:
        __module__ = "pyoxipng"
        __qualname__ = "ColorType"
        kind = "rgb"

    with pytest.raises(TypeError, match="color_type"):
        oxipng.RawImage(
            data=b"\x00\x00\x00",
            width=1,
            height=1,
            color_type=ColorType(),  # type: ignore[arg-type]
            bit_depth=8,
        )
```

- [x] **Step 2: Run the new API tests and confirm failure**

Run:

```bash
uv run pytest tests/test_api.py -q
```

Expected: the new tests fail on current behavior. Failures should correspond to validation order, error type mapping, set handling, warning coverage, immutable compatibility descriptors, or marker enforcement.

- [x] **Step 3: Implement Rust-side validation changes**

In `src/lib.rs`, change option parsing so `optimize_from_memory()` validates options before extracting the input buffer where practical. Keep stable API semantics unchanged except for earlier error detection.

Implement `parse_max_decompressed_size()` with this behavior:

```rust
fn parse_max_decompressed_size(value: &Bound<'_, PyAny>) -> PyResult<u64> {
    if value.is_instance_of::<pyo3::types::PyBool>() {
        return Err(PyTypeError::new_err(
            "max_decompressed_size must be an integer, not bool",
        ));
    }

    match value.extract::<u64>() {
        Ok(size) => Ok(size),
        Err(_) if value.extract::<i128>().is_ok() => Err(PyValueError::new_err(
            "max_decompressed_size must be between 0 and 18446744073709551615",
        )),
        Err(_) => Err(PyTypeError::new_err(
            "max_decompressed_size must be an integer",
        )),
    }
}
```

For enum-like numeric values, reject `bool` both before and after `.value` extraction. The helper should follow this shape:

```rust
fn extract_non_bool_u8(value: &Bound<'_, PyAny>, field_name: &str) -> PyResult<u8> {
    let candidate = if let Ok(value_attr) = value.getattr("value") {
        value_attr
    } else {
        value.clone()
    };

    if candidate.is_instance_of::<pyo3::types::PyBool>() {
        return Err(PyTypeError::new_err(format!("{field_name} must be an integer, not bool")));
    }

    candidate.extract::<u8>().map_err(|_| {
        PyTypeError::new_err(format!("{field_name} must be an integer between 0 and 255"))
    })
}
```

Map backup source `NotFound` to `PyFileNotFoundError` while preserving existing `FileExistsError` and other `OSError` paths:

```rust
match create_backup(input_path, backup_path) {
    Ok(()) => {}
    Err(err) if err.kind() == std::io::ErrorKind::NotFound => {
        return Err(PyFileNotFoundError::new_err(err.to_string()));
    }
    Err(err) if err.kind() == std::io::ErrorKind::AlreadyExists => {
        return Err(PyFileExistsError::new_err(err.to_string()));
    }
    Err(err) => return Err(PyOSError::new_err(err.to_string())),
}
```

For `RawImage.add_png_chunk()`, validate the chunk name before extracting or copying the payload bytes:

```rust
let chunk_name = parse_chunk_name(name)?;
let chunk_data = data.extract::<Vec<u8>>()?;
self.inner.add_png_chunk(chunk_name, chunk_data);
```

- [x] **Step 4: Implement compatibility marker and immutable palette changes**

In `oxipng/_pyoxipng_compat.py`, add a private marker field to compatibility dataclasses and convert palettes to tuple snapshots:

```python
_COMPAT_MARKER = object()


@dataclass(frozen=True)
class CompatColorType:
    kind: str
    palette: tuple[tuple[int, int, int], ...] | None = None
    _oxipng_pybind_compat_marker: object = field(default=_COMPAT_MARKER, init=False, repr=False)

    @classmethod
    def indexed(cls, palette: Iterable[tuple[int, int, int]]) -> "CompatColorType":
        return cls("indexed", tuple(tuple(color) for color in palette))
```

In `src/lib.rs`, update compatibility object detection so module/name spoofing is insufficient. Require the marker attribute and accept only the marker value exposed by the compatibility module:

```rust
fn is_oxipng_compat_type(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    value
        .getattr("_oxipng_pybind_compat_marker")
        .map(|marker| marker.is_truthy().unwrap_or(false))
        .or(Ok(false))
}
```

Use the project’s existing attribute access and PyO3 style if the exact helper above needs adjustment.

- [x] **Step 5: Implement filter collection and warning behavior**

Keep stable API filter inputs ordered. Accept `Sequence[RowFilter]` and tuples/lists where already supported. Reject unordered `set` and `frozenset` in stable paths with `TypeError` mentioning ordered input.

For pyoxipng compatibility paths, preserve pyoxipng’s ability to accept sets of row filters and emit an additional `DeprecationWarning` explaining that unordered filter collections are compatibility-only and stable `oxipng` requires ordered filters.

In `oxipng/__init__.pyi`, do not advertise `set` or `frozenset` for stable filter inputs. Keep stable predefined filter typing as ordered only:

```python
FilterInput: TypeAlias = RowFilter | FilterStrategy | Sequence[RowFilter]
```

- [x] **Step 6: Implement deprecated pyoxipng enum lookup warnings**

In the compatibility enum layer, ensure these paths emit `DeprecationWarning` while stable enum access does not warn:

```python
pyoxipng.RowFilter.none
pyoxipng.RowFilter["none"]
pyoxipng.RowFilter("none")
```

If metaclass constraints make one lookup path impossible to intercept cleanly, document that limitation in the test with an explicit `pytest.xfail()` and a comment naming the CPython enum behavior that blocks it.

- [x] **Step 7: Add docs-only closure for direct backup and ICC profile limitations**

In `docs/usage/file-optimization.md`, add a concise note under backup behavior:

```markdown
Direct backup writes follow oxipng's file behavior. If the process is interrupted while a `.bak` file is being written, the partially written backup file may remain and should be removed before retrying.
```

In `docs/usage/raw-image.md`, document ICC profile behavior only after confirming upstream behavior from the existing wrapper code. If upstream does not expose a success status, add:

```markdown
`RawImage.add_icc_profile()` forwards the profile to oxipng. The upstream API does not return a separate success status for profile attachment, so callers should treat invalid profile rejection as an exception and successful calls as best-effort attachment.
```

- [x] **Step 8: Run API and typing verification**

Run:

```bash
uv run pytest tests/test_api.py -q
uv run mypy tests/typing_filter_options.py
```

Expected: both commands pass.

- [x] **Step 9: Commit Task 1**

```bash
git add src/lib.rs oxipng/_pyoxipng_compat.py oxipng/__init__.py oxipng/__init__.pyi tests/test_api.py tests/typing_filter_options.py docs/usage/file-optimization.md docs/usage/raw-image.md
git commit -m "fix: harden API validation and compatibility warnings"
```

## Task 2: Dependency Classifier Hardening

**Findings covered:** Minor 13 and 14.

**Files:**

- Modify: `scripts/classify_dependency_refresh.py`
- Test: `tests/test_dependency_refresh_classification.py`

- [x] **Step 1: Add executable resolution and GitHub output tests**

Add tests to `tests/test_dependency_refresh_classification.py`:

```python
def test_run_stdout_resolves_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(classifier.shutil, "which", lambda name: f"/fake/bin/{name}")

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(classifier.subprocess, "run", fake_run)

    assert classifier.run_stdout(["git", "status"]) == "ok"
    assert calls == [["/fake/bin/git", "status"]]


def test_run_stdout_fails_when_executable_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(classifier.shutil, "which", lambda name: None)

    with pytest.raises(RuntimeError, match="Unable to find executable"):
        classifier.run_stdout(["cargo", "tree"])


@pytest.mark.parametrize("name", ["bad\nname", "bad\rname"])
def test_emit_github_output_rejects_newline_in_name(tmp_path: Path, name: str) -> None:
    output = tmp_path / "github-output"
    with pytest.raises(ValueError, match="newline"):
        classifier.emit_github_output(output, name, "value")
    assert not output.exists()


@pytest.mark.parametrize("value", ["bad\nvalue", "bad\rvalue"])
def test_emit_github_output_rejects_newline_in_value(tmp_path: Path, value: str) -> None:
    output = tmp_path / "github-output"
    with pytest.raises(ValueError, match="newline"):
        classifier.emit_github_output(output, "name", value)
    assert not output.exists()
```

- [x] **Step 2: Run classifier tests and confirm failure**

Run:

```bash
uv run pytest tests/test_dependency_refresh_classification.py -q
```

Expected: new tests fail because commands are not resolved through `shutil.which()` and newline guards are absent.

- [x] **Step 3: Implement executable resolution and output guards**

In `scripts/classify_dependency_refresh.py`, import `shutil` and add:

```python
def resolve_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"Unable to find executable: {name}")
    return path


def resolved_command(args: Sequence[str]) -> list[str]:
    if not args:
        raise ValueError("command must not be empty")
    return [resolve_executable(args[0]), *args[1:]]
```

Use `resolved_command(args)` inside `run_stdout()` before `subprocess.run()`.

Update `emit_github_output()`:

```python
def emit_github_output(path: Path, name: str, value: str) -> None:
    if "\n" in name or "\r" in name or "\n" in value or "\r" in value:
        raise ValueError("GitHub output name and value must not contain newline characters")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")
```

- [x] **Step 4: Run classifier verification**

Run:

```bash
uv run pytest tests/test_dependency_refresh_classification.py -q
```

Expected: all tests pass.

- [x] **Step 5: Commit Task 2**

```bash
git add scripts/classify_dependency_refresh.py tests/test_dependency_refresh_classification.py
git commit -m "fix: harden dependency refresh classifier"
```

## Task 3: Rustdoc JSON Upstream Scanner

**Findings covered:** Minor 15 and 16.

**Files:**

- Modify: `scripts/scan_upstream_surface.py`
- Modify: `tests/test_scan_upstream_surface.py`
- Modify if required by local toolchain: `.github/workflows/upstream-bump.yml`

- [x] **Step 1: Add rustdoc JSON fixture tests**

Replace parser-edge tests that rely on Rust source brace scanning with rustdoc JSON fixture tests in `tests/test_scan_upstream_surface.py`:

```python
RUSTDOC_JSON_FIXTURE = {
    "index": {
        "0:0:1": {
            "name": "optimize",
            "visibility": "public",
            "inner": {"function": {"header": {"const": False, "async": False}}},
        },
        "0:0:2": {
            "name": "available_chunks",
            "visibility": "public",
            "inner": {"function": {"header": {"const": True, "async": False}}},
        },
        "0:0:3": {
            "name": "future_async_probe",
            "visibility": "public",
            "inner": {"function": {"header": {"const": False, "async": True}}},
        },
        "0:0:4": {
            "name": "internal_helper",
            "visibility": "crate",
            "inner": {"function": {"header": {"const": False, "async": False}}},
        },
        "0:0:5": {
            "name": "Options",
            "visibility": "public",
            "inner": {"struct": {"kind": "plain"}},
        },
        "0:0:6": {
            "name": "RowFilter",
            "visibility": "public",
            "inner": {"enum": {"variants": []}},
        },
    }
}


def test_public_items_from_rustdoc_json_covers_function_kinds() -> None:
    surface = scanner.public_items_from_rustdoc_json(RUSTDOC_JSON_FIXTURE)

    assert "optimize" in surface.functions
    assert "available_chunks" in surface.functions
    assert "future_async_probe" in surface.functions
    assert "internal_helper" not in surface.functions
    assert "Options" in surface.types
    assert "RowFilter" in surface.types
```

Add a command construction test that avoids requiring nightly in unit tests:

```python
def test_rustdoc_json_command_uses_rustdoc_json_flags(tmp_path: Path) -> None:
    command = scanner.rustdoc_json_command(tmp_path)

    assert command[:4] == ["rustup", "run", "nightly", "cargo"]
    assert "rustdoc" in command
    assert "--output-format" in command
    assert "json" in command
```

- [x] **Step 2: Run scanner tests and confirm failure**

Run:

```bash
uv run pytest tests/test_scan_upstream_surface.py -q
```

Expected: tests fail because `public_items_from_rustdoc_json()` and `rustdoc_json_command()` do not exist.

- [x] **Step 3: Implement rustdoc JSON collection**

In `scripts/scan_upstream_surface.py`, add a command builder and JSON runner:

```python
def rustdoc_json_command(crate_dir: Path) -> list[str]:
    return [
        "rustup",
        "run",
        "nightly",
        "cargo",
        "rustdoc",
        "--lib",
        "--no-deps",
        "--manifest-path",
        str(crate_dir / "Cargo.toml"),
        "--",
        "-Z",
        "unstable-options",
        "--output-format",
        "json",
    ]


def load_rustdoc_json(crate_dir: Path) -> dict[str, object]:
    subprocess.run(rustdoc_json_command(crate_dir), check=True)
    crate_name = crate_dir.name.replace("-", "_")
    json_path = crate_dir / "target" / "doc" / f"{crate_name}.json"
    with json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
```

If the upstream checkout path or crate name is already available elsewhere in the script, use that existing path source instead of `crate_dir.name`.

- [x] **Step 4: Replace source brace scanning with rustdoc JSON item extraction**

Add a rustdoc JSON extraction function that uses public item metadata, not source text:

```python
def public_items_from_rustdoc_json(document: Mapping[str, object]) -> UpstreamSurface:
    functions: set[str] = set()
    types: set[str] = set()
    constants: set[str] = set()

    index = document.get("index", {})
    if not isinstance(index, Mapping):
        raise ValueError("rustdoc JSON does not contain an item index")

    for raw_item in index.values():
        if not isinstance(raw_item, Mapping):
            continue
        if raw_item.get("visibility") != "public":
            continue
        name = raw_item.get("name")
        inner = raw_item.get("inner")
        if not isinstance(name, str) or not isinstance(inner, Mapping):
            continue
        if "function" in inner:
            functions.add(name)
        elif any(kind in inner for kind in ("struct", "enum", "union", "trait", "type_alias")):
            types.add(name)
        elif "constant" in inner or "static" in inner:
            constants.add(name)

    return UpstreamSurface(
        functions=frozenset(functions),
        types=frozenset(types),
        constants=frozenset(constants),
    )
```

Preserve the script’s existing manifest comparison and report output. Only replace how upstream public items are discovered.

- [x] **Step 5: Add workflow support only if the pinned toolchain lacks rustdoc JSON**

Run:

```bash
rustup run nightly cargo --version
```

If nightly is unavailable in CI setup, modify `.github/workflows/upstream-bump.yml` before the scanner step:

```yaml
- name: Install Rust nightly for rustdoc JSON
  run: rustup toolchain install nightly --profile minimal
```

Do not add a Python parser dependency and do not expand a custom Rust parser.

- [x] **Step 6: Run scanner verification**

Run:

```bash
uv run pytest tests/test_scan_upstream_surface.py -q
uv run python scripts/scan_upstream_surface.py --help
```

Expected: scanner tests pass and CLI help exits successfully.

- [x] **Step 7: Commit Task 3**

```bash
git add scripts/scan_upstream_surface.py tests/test_scan_upstream_surface.py .github/workflows/upstream-bump.yml
git commit -m "fix: scan upstream API with rustdoc JSON"
```

If `.github/workflows/upstream-bump.yml` was not changed, omit it from `git add`.

## Task 4: Stream AI Filter Logs

**Findings covered:** Minor 17.

**Files:**

- Modify: `scripts/ai_filter_log.py`
- Test: `tests/test_scripts.py`

- [x] **Step 1: Add large-log bounded memory test**

In `tests/test_scripts.py`, add:

```python
def test_ai_filter_log_streams_large_log(tmp_path: Path) -> None:
    log_path = tmp_path / "large.log"
    log_path.write_text(
        "".join(f"info line {index}\n" for index in range(50_000))
        + "error: final failure summary\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ai_filter_log.py", str(log_path)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "error: final failure summary" in result.stdout
    assert "info line 0" not in result.stdout
```

- [x] **Step 2: Run the AI log test and confirm failure or current over-read**

Run:

```bash
uv run pytest tests/test_scripts.py -q -k ai_filter_log
```

Expected: either the new test fails because output contains too much context, or existing code inspection shows the script reads the entire file into memory.

- [x] **Step 3: Implement bounded streaming**

In `scripts/ai_filter_log.py`, replace full-file reads with line streaming and a bounded deque:

```python
from collections import deque


def summarize_log(path: Path, *, context_lines: int = 200) -> str:
    tail: deque[str] = deque(maxlen=context_lines)
    failures: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            tail.append(line)
            lowered = line.lower()
            if "error" in lowered or "failed" in lowered or "traceback" in lowered:
                failures.append(line)

    selected = failures[-context_lines:] if failures else list(tail)
    return "".join(selected)
```

Wire the CLI to call `summarize_log()` and keep current command-line arguments and exit behavior unchanged.

- [x] **Step 4: Run AI log verification**

Run:

```bash
uv run pytest tests/test_scripts.py -q -k ai_filter_log
```

Expected: all AI log tests pass.

- [x] **Step 5: Commit Task 4**

```bash
git add scripts/ai_filter_log.py tests/test_scripts.py
git commit -m "fix: stream AI log filtering"
```

## Task 5: Pin cargo-deny Bootstrap Version

**Findings covered:** Minor 18.

**Files:**

- Modify: `Makefile`
- Test: `tests/test_makefile.py`

- [x] **Step 1: Add Makefile tests for pinned cargo-deny setup**

In `tests/test_makefile.py`, update the existing cargo-deny assertions:

```python
def test_makefile_pins_cargo_deny_version(makefile_text: str) -> None:
    assert "CARGO_DENY_VERSION :=" in makefile_text
    assert "cargo-deny --version" in makefile_text
    assert "cargo install --locked cargo-deny --version $(CARGO_DENY_VERSION)" in makefile_text
```

If the file uses direct `Path.read_text()` instead of a fixture, adapt the assertion body to the existing local style.

- [x] **Step 2: Run Makefile tests and confirm failure**

Run:

```bash
uv run pytest tests/test_makefile.py -q
```

Expected: the new assertion fails because the Makefile installs unpinned `cargo-deny`.

- [x] **Step 3: Implement pinned cargo-deny bootstrap**

In `Makefile`, add a version variable near the other tool version settings:

```make
CARGO_DENY_VERSION := 0.16.4
```

Update the Rust bootstrap target so it checks the installed version and installs only when missing or mismatched. The recipe lines below must be indented with Make recipe tabs in the actual `Makefile`:

```make
@if ! command -v cargo-deny >/dev/null 2>&1 || ! cargo-deny --version | grep -q " $(CARGO_DENY_VERSION)"; then \
    cargo install --locked cargo-deny --version $(CARGO_DENY_VERSION); \
fi
```

Do not add version checks to the normal audit target; keep the version enforcement in setup/bootstrap.

- [x] **Step 4: Run Makefile verification**

Run:

```bash
uv run pytest tests/test_makefile.py -q
```

Expected: Makefile tests pass.

- [x] **Step 5: Commit Task 5**

```bash
git add Makefile tests/test_makefile.py
git commit -m "fix: pin cargo-deny bootstrap version"
```

## Task 6: Integration, Report Update, and Merge Prep

**Findings covered:** Minor 3 and 19 closure plus final status for all minor findings.

**Files:**

- Modify: `docs/plans/full-code-review-report.md`
- Modify: `docs/plans/minor-review-fixes-plan.md`

- [ ] **Step 1: Rebase the isolated branch on main**

Run from the minor fixes worktree:

```bash
git fetch origin
git rebase main
```

Expected: branch rebases cleanly. Resolve conflicts by preserving all committed worker fixes and the latest report wording from `main`.

- [ ] **Step 2: Run pre-commit before full CI**

Run:

```bash
uv run pre-commit run --all-files
```

Expected: pass. If hooks autoformat files, include those changes in the final docs or integration commit.

- [ ] **Step 3: Run full CI**

Run:

```bash
make ci AI=1
```

Expected: pass.

- [x] **Step 4: Update the full review report**

In `docs/plans/full-code-review-report.md`, move the minor findings out of the open list and record their disposition:

```markdown
### Minor

- Minor 1: Fixed by validating options before memory input extraction where practical.
- Minor 2: Fixed by mapping missing backup inputs to `FileNotFoundError`.
- Minor 3: No code change. Direct backup writes intentionally preserve upstream Rust behavior; docs now describe partial `.bak` files after interruption.
- Minor 4: Fixed by reporting `ValueError` for integer range failures and `TypeError` for non-integer values.
- Minor 5: Fixed by rejecting bool values after enum `.value` extraction.
- Minor 6: Fixed by validating PNG chunk names before payload extraction.
- Minor 7: Closed as a documented limitation because upstream does not expose a separate runtime success status.
- Minor 8: Fixed with the chunk-name validation simplification from Minor 6.
- Minor 9: Fixed by rejecting unordered stable filter collections while preserving pyoxipng set compatibility with warnings.
- Minor 10: Fixed or explicitly documented for pyoxipng deprecated enum lookup warnings.
- Minor 11: Fixed by making compatibility palettes immutable tuple snapshots.
- Minor 12: Fixed by requiring a private compatibility marker.
- Minor 13: Fixed by resolving `git` and `cargo` executables before invocation.
- Minor 14: Fixed by rejecting newline-bearing GitHub output names and values.
- Minor 15: Fixed by using rustdoc JSON instead of a hand-rolled Rust parser.
- Minor 16: Fixed by rustdoc JSON coverage of public `fn`, `const fn`, and `async fn`.
- Minor 17: Fixed by streaming AI log summaries with bounded memory.
- Minor 18: Fixed by enforcing the pinned `cargo-deny` version during bootstrap.
- Minor 19: No code change. The bounded one-time CI retry remains acceptable because it does not checkout secrets or expand permissions.
```

- [ ] **Step 5: Mark this plan complete**

Change this plan’s task checkboxes from incomplete to complete only after the corresponding commits and verification have happened. Final pre-commit, final CI, and merge-back steps remain intentionally unchecked until they have run.

- [x] **Step 6: Commit the integration docs**

```bash
git add docs/plans/full-code-review-report.md docs/plans/minor-review-fixes-plan.md
git commit -m "docs: close minor code review findings"
```

- [ ] **Step 7: Fast-forward main only after verification**

Run:

```bash
git switch main
git merge --ff-only minor-review-fixes
```

Expected: `main` fast-forwards. Do not squash; preserve the task commits for review.

## Self-Review Checklist

- [x] All 19 minor findings have a fix or explicit no-code disposition.
- [x] Stable API filter contracts remain ordered and do not advertise unordered collections.
- [x] pyoxipng compatibility preserves accepted set inputs where pyoxipng accepted them and emits an additional warning.
- [x] Direct backup file behavior preserves upstream Rust behavior.
- [x] The upstream scanner uses rustdoc JSON, not a custom Rust source parser.
- [ ] Full pre-commit and final CI remain pending for merge prep; focused
  markdownlint verification ran for this docs commit.
- [ ] `make ci AI=1` passes before merging back to `main`.

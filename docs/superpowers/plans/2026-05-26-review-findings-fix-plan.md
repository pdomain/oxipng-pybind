# Review Findings Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the security, clarity, performance, release, and coverage gaps found in the post-RawImage deep review.

**Architecture:** Keep the public API small and explicit. Add Python-side validation before handing data to upstream oxipng, make file backup creation atomic, extend the upstream surface scanner to cover every upstream enum now exposed publicly, and harden release automation without changing the package import surface.

**Tech Stack:** Rust, PyO3, upstream `oxi`, Python 3.10+, pytest, Pillow, tomlkit, GitHub Actions, maturin ABI3 wheels.

---

## File Structure

- `src/lib.rs`: owns Python-to-Rust parsing, file backup behavior, RawImage validation, and GIL release boundaries.
- `tests/test_api.py`: focused public API tests for validation failures and option behavior.
- `tests/test_real_pngs.py`: pixel-preservation tests using real PNGs and RawImage-generated PNGs.
- `tests/test_scripts.py`: unit tests for scanner, wheel tag checker, bump helpers, and smoke helper behavior.
- `scripts/scan_upstream_surface.py`: parses upstream Rust surface and compares it to the manifest.
- `scripts/check_wheel_tags.py`: validates wheel Python, ABI, and platform tags.
- `scripts/smoke_wheel.py`: verifies installed wheel runtime behavior and packaged typing files.
- `scripts/bump_upstream.py`: fetches upstream release metadata and creates upstream-surface issues.
- `.github/workflows/upstream-bump.yml`: automated upstream bump workflow.
- `.github/workflows/wheels.yml`: wheel build and smoke workflow.
- `docs/api-surface/oxipng-10.1.1.toml`: compatibility manifest for the pinned upstream version.
- `docs/usage/raw-image.md`: user-facing RawImage behavior documentation.
- `docs/architecture/api-compatibility.md`: compatibility boundary documentation.
- `README.md`: install and supported API summary.
- `docs/process/upstream-bumps.md`: upstream bump operational notes.
- `docs/process/release-artifacts.md`: wheel artifact and tag expectations.

---

### Task 1: RawImage Chunk, Palette, and Transparency Validation

**Files:**

- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`
- Modify: `tests/test_real_pngs.py`

- [ ] **Step 1: Add failing tests for invalid chunk names**

Add these tests to `tests/test_api.py` near the existing RawImage tests:

```python
@pytest.mark.parametrize("name", [b"IHDR", b"IDAT", b"IEND", b"PLTE", b"tRNS", b"iCCP"])
def test_raw_image_rejects_structural_or_dedicated_chunks(name: bytes) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with pytest.raises(ValueError, match="chunk name"):
        raw.add_png_chunk(name, b"payload")


@pytest.mark.parametrize("name", [b"abc", b"abcde", b"ab1d", b"ab_d", b"ab\x00d", b"abCd"])
def test_raw_image_rejects_invalid_chunk_names(name: bytes) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with pytest.raises(ValueError, match="chunk name"):
        raw.add_png_chunk(name, b"payload")
```

- [ ] **Step 2: Add failing tests for indexed palette limits and pixel indices**

Add these tests to `tests/test_api.py`:

```python
def test_raw_image_rejects_too_many_palette_entries_for_bit_depth() -> None:
    palette = [(index, index, index) for index in range(5)]

    with pytest.raises(ValueError, match="palette length"):
        RawImage(1, 1, ColorType.indexed, BitDepth.two, bytes([0]), palette=palette)


def test_raw_image_rejects_indexed_pixels_outside_palette() -> None:
    with pytest.raises(ValueError, match="pixel index"):
        RawImage(
            2,
            1,
            ColorType.indexed,
            BitDepth.eight,
            bytes([0, 2]),
            palette=[(255, 0, 0), (0, 0, 255)],
        )
```

- [ ] **Step 3: Add failing transparency validation tests**

Add these tests to `tests/test_api.py`:

```python
def test_raw_image_rejects_grayscale_transparency_above_bit_depth_range() -> None:
    with pytest.raises(ValueError, match="transparent"):
        RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]), transparent=256)


def test_raw_image_rejects_rgb_transparency_above_bit_depth_range() -> None:
    with pytest.raises(ValueError, match="transparent"):
        RawImage(
            1,
            1,
            ColorType.rgb,
            BitDepth.eight,
            bytes([255, 0, 0]),
            transparent=(256, 0, 0),
        )


@pytest.mark.parametrize("color_type", [ColorType.indexed, ColorType.grayscale_alpha, ColorType.rgba])
def test_raw_image_rejects_transparency_for_unsupported_color_types(color_type: ColorType) -> None:
    kwargs: dict[str, object] = {}
    data = bytes([0])
    if color_type is ColorType.indexed:
        kwargs["palette"] = [(0, 0, 0)]
    elif color_type is ColorType.grayscale_alpha:
        data = bytes([0, 255])
    else:
        data = bytes([0, 0, 0, 255])

    with pytest.raises(ValueError, match="transparent is not supported"):
        RawImage(1, 1, color_type, BitDepth.eight, data, transparent=0, **kwargs)
```

- [ ] **Step 4: Add real PNG tests for valid transparency**

Add these tests to `tests/test_real_pngs.py`:

```python
def test_raw_image_grayscale_transparency_preserves_pixels() -> None:
    raw = RawImage(2, 1, ColorType.grayscale, BitDepth.eight, bytes([0, 255]), transparent=0)

    optimized = raw.create_optimized_png(level=3)

    assert decoded_rgba(optimized) == (
        (2, 1),
        bytes([0, 0, 0, 0, 255, 255, 255, 255]),
    )


def test_raw_image_rgb_transparency_preserves_pixels() -> None:
    raw = RawImage(
        2,
        1,
        ColorType.rgb,
        BitDepth.eight,
        bytes([255, 0, 0, 0, 0, 255]),
        transparent=(255, 0, 0),
    )

    optimized = raw.create_optimized_png(level=3)

    assert decoded_rgba(optimized) == (
        (2, 1),
        bytes([255, 0, 0, 0, 0, 0, 255, 255]),
    )
```

- [ ] **Step 5: Run focused tests and confirm failure**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py tests/test_real_pngs.py -k "raw_image" -v -ra
```

Expected: at least the new invalid chunk, indexed palette, indexed pixel, and transparency range tests fail against the current implementation.

- [ ] **Step 6: Implement RawImage validation helpers**

In `src/lib.rs`, add helpers after `extract_u8`:

```rust
fn bit_depth_value(bit_depth: oxi::BitDepth) -> u8 {
    bit_depth as u8
}

fn max_sample_value(bit_depth: oxi::BitDepth) -> u16 {
    (1_u16 << bit_depth_value(bit_depth)) - 1
}

fn validate_transparent_value(value: u16, bit_depth: oxi::BitDepth) -> PyResult<()> {
    let max = max_sample_value(bit_depth);
    if value > max {
        return Err(PyValueError::new_err(format!(
            "transparent values must be between 0 and {max} for this bit depth"
        )));
    }
    Ok(())
}

fn validate_png_chunk_name(name: [u8; 4]) -> PyResult<[u8; 4]> {
    if !name.iter().all(u8::is_ascii_alphabetic) {
        return Err(PyValueError::new_err(
            "chunk name must contain exactly 4 ASCII letters",
        ));
    }
    if !name[0].is_ascii_lowercase() {
        return Err(PyValueError::new_err(
            "chunk name must be an ancillary PNG chunk",
        ));
    }
    if !name[2].is_ascii_uppercase() {
        return Err(PyValueError::new_err(
            "chunk name must use a valid reserved bit",
        ));
    }
    if matches!(&name, b"IHDR" | b"PLTE" | b"IDAT" | b"IEND" | b"tRNS" | b"iCCP") {
        return Err(PyValueError::new_err(
            "chunk name is reserved for structured RawImage data",
        ));
    }
    Ok(name)
}

fn validate_indexed_pixels(data: &[u8], palette_len: usize, bit_depth: oxi::BitDepth) -> PyResult<()> {
    let max_palette_len = 1_usize << bit_depth_value(bit_depth);
    if palette_len > max_palette_len {
        return Err(PyValueError::new_err(format!(
            "palette length must be at most {max_palette_len} for this bit depth"
        )));
    }

    match bit_depth_value(bit_depth) {
        8 => {
            if data.iter().any(|index| usize::from(*index) >= palette_len) {
                return Err(PyValueError::new_err(
                    "pixel index must be less than palette length",
                ));
            }
        }
        4 => {
            for byte in data {
                for index in [byte >> 4, byte & 0x0f] {
                    if usize::from(index) >= palette_len {
                        return Err(PyValueError::new_err(
                            "pixel index must be less than palette length",
                        ));
                    }
                }
            }
        }
        2 => {
            for byte in data {
                for shift in [6, 4, 2, 0] {
                    if usize::from((byte >> shift) & 0x03) >= palette_len {
                        return Err(PyValueError::new_err(
                            "pixel index must be less than palette length",
                        ));
                    }
                }
            }
        }
        1 => {
            if palette_len < 2 && data.iter().any(|byte| *byte != 0) {
                return Err(PyValueError::new_err(
                    "pixel index must be less than palette length",
                ));
            }
        }
        _ => {}
    }
    Ok(())
}
```

- [ ] **Step 7: Parse bit depth before color type and validate transparent values**

Change `parse_color_type` to accept `bit_depth: oxi::BitDepth`, validate grayscale/RGB transparent values before constructing `oxi::ColorType`, and keep existing unsupported-transparent errors for indexed/alpha types.

```rust
fn parse_color_type(
    color_type: &Bound<'_, PyAny>,
    bit_depth: oxi::BitDepth,
    palette: Option<&Bound<'_, PyAny>>,
    transparent: Option<&Bound<'_, PyAny>>,
) -> PyResult<oxi::ColorType> {
    match value_as_string(color_type, "color_type")?.as_str() {
        "grayscale" => {
            let transparent_shade = transparent
                .map(|value| extract_u16(value, "transparent"))
                .transpose()?;
            if let Some(value) = transparent_shade {
                validate_transparent_value(value, bit_depth)?;
            }
            Ok(oxi::ColorType::Grayscale { transparent_shade })
        }
        "rgb" => {
            let transparent_color = transparent
                .map(|value| parse_rgb16(value, "transparent"))
                .transpose()?;
            if let Some(color) = transparent_color {
                validate_transparent_value(color.r, bit_depth)?;
                validate_transparent_value(color.g, bit_depth)?;
                validate_transparent_value(color.b, bit_depth)?;
            }
            Ok(oxi::ColorType::RGB { transparent_color })
        }
        "indexed" => {
            if transparent.is_some() {
                return Err(PyValueError::new_err(
                    "transparent is not supported for indexed raw images; use alpha values in palette entries",
                ));
            }
            Ok(oxi::ColorType::Indexed {
                palette: parse_palette(palette)?,
            })
        }
        "grayscale_alpha" => {
            if transparent.is_some() {
                return Err(PyValueError::new_err(
                    "transparent is not supported for grayscale_alpha raw images",
                ));
            }
            Ok(oxi::ColorType::GrayscaleAlpha)
        }
        "rgba" => {
            if transparent.is_some() {
                return Err(PyValueError::new_err(
                    "transparent is not supported for rgba raw images",
                ));
            }
            Ok(oxi::ColorType::RGBA)
        }
        _ => Err(PyValueError::new_err(
            "color_type must be one of: grayscale, rgb, indexed, grayscale_alpha, rgba",
        )),
    }
}
```

If `RGB16` fields are not public, destructure by adding a helper that validates the tuple before constructing `RGB16`:

```rust
fn parse_rgb16_with_depth(
    value: &Bound<'_, PyAny>,
    context: &str,
    bit_depth: oxi::BitDepth,
) -> PyResult<oxi::RGB16> {
    let tuple = value
        .downcast::<PyTuple>()
        .map_err(|_| PyValueError::new_err(format!("{context} must be a 3-tuple")))?;
    if tuple.len() != 3 {
        return Err(PyValueError::new_err(format!("{context} must be a 3-tuple")));
    }
    let r = extract_u16(&tuple.get_item(0)?, context)?;
    let g = extract_u16(&tuple.get_item(1)?, context)?;
    let b = extract_u16(&tuple.get_item(2)?, context)?;
    validate_transparent_value(r, bit_depth)?;
    validate_transparent_value(g, bit_depth)?;
    validate_transparent_value(b, bit_depth)?;
    Ok(oxi::RGB16::new(r, g, b))
}
```

- [ ] **Step 8: Wire validation into `RawImage.__new__` and `add_png_chunk`**

In `PyRawImage::new`, parse bit depth before color type and validate indexed image data:

```rust
let bit_depth = parse_bit_depth(bit_depth)?;
let color_type = parse_color_type(color_type, bit_depth, palette, transparent)?;
let data = bytes_like_to_vec(data)?;
if let oxi::ColorType::Indexed { palette } = &color_type {
    validate_indexed_pixels(&data, palette.len(), bit_depth)?;
}
let inner = oxi::RawImage::new(width, height, color_type, bit_depth, data)
    .map_err(map_png_error)?;
```

In `add_png_chunk`, validate the converted name:

```rust
let name = validate_png_chunk_name(name)?;
self.inner.add_png_chunk(name, data);
```

- [ ] **Step 9: Run focused tests and full Python tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py tests/test_real_pngs.py -k "raw_image" -v -ra
uv run --no-sync --group dev pytest tests/test_api.py tests/test_real_pngs.py -v -ra
```

Expected: all selected tests pass.

- [ ] **Step 10: Commit**

Run:

```bash
git add src/lib.rs tests/test_api.py tests/test_real_pngs.py
git commit -m "fix: validate raw image inputs"
git push origin main
```

---

### Task 2: Atomic Backup Creation and GIL Release

**Files:**

- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add failing tests for existing backup behavior**

Keep `test_backup_refuses_to_overwrite_existing_backup` and add this symlink-specific test on Unix:

```python
@pytest.mark.skipif(not hasattr(__import__("os"), "symlink"), reason="symlink unavailable")
def test_backup_refuses_existing_symlink_backup(png_path: Path, tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("do not overwrite", encoding="utf-8")
    backup = png_path.with_name(f"{png_path.name}.bak")
    backup.symlink_to(target)

    with pytest.raises(FileExistsError):
        optimize(png_path, backup=True)

    assert target.read_text(encoding="utf-8") == "do not overwrite"
```

- [ ] **Step 2: Run focused backup tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -k "backup" -v -ra
```

Expected: existing tests pass; the new test documents the symlink refusal behavior before the implementation changes.

- [ ] **Step 3: Implement atomic backup helper**

In `src/lib.rs`, replace `use std::fs;` with:

```rust
use std::fs::{self, OpenOptions};
use std::io;
```

Add this helper near `map_png_error`:

```rust
fn backup_path_for(input: &std::path::Path) -> PathBuf {
    let mut backup = input.as_os_str().to_os_string();
    backup.push(".bak");
    PathBuf::from(backup)
}

fn create_backup(input: &std::path::Path) -> io::Result<PathBuf> {
    let backup = backup_path_for(input);
    let mut source = fs::File::open(input)?;
    let mut destination = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&backup)?;
    io::copy(&mut source, &mut destination)?;
    Ok(backup)
}
```

- [ ] **Step 4: Release the GIL around backup creation**

Replace the current backup block in `optimize` with:

```rust
if parsed.backup {
    let backup_input = input.clone();
    py.allow_threads(move || create_backup(&backup_input))
        .map_err(|error| {
            if error.kind() == io::ErrorKind::AlreadyExists {
                PyFileExistsError::new_err(backup_path_for(&input).display().to_string())
            } else {
                PyOSError::new_err(error)
            }
        })?;
}
```

- [ ] **Step 5: Run backup and file API tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -k "backup or optimize_to_output_path or optimize_in_place" -v -ra
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/lib.rs tests/test_api.py
git commit -m "fix: create backups atomically"
git push origin main
```

---

### Task 3: Upstream Surface Scanner Coverage for RawImage Enums

**Files:**

- Modify: `scripts/scan_upstream_surface.py`
- Modify: `tests/test_scripts.py`
- Modify: `docs/api-surface/oxipng-10.1.1.toml`
- Modify: `docs/specs/2026-05-26-upstream-surface-scan-design.md`

- [ ] **Step 1: Add failing scanner test for `ColorType` and `BitDepth`**

Add a test to `tests/test_scripts.py` that creates a fake upstream checkout with `src/colors.rs` and asserts the scanner reports new variants. Use the existing test style in that file.

Update the module imports first:

```python
from scripts import ai_filter_log, bump_upstream, check_wheel_tags, scan_upstream_surface, smoke_wheel
```

```python
def test_scan_upstream_surface_tracks_color_type_and_bit_depth(tmp_path: Path) -> None:
    upstream = tmp_path / "upstream"
    src = upstream / "src"
    (src / "deflate").mkdir(parents=True)
    (src / "options.rs").write_text("pub struct Options { pub force: bool }\n", encoding="utf-8")
    (src / "filters.rs").write_text(
        "pub enum FilterStrategy { MinSum }\npub enum RowFilter { None }\n",
        encoding="utf-8",
    )
    (src / "headers.rs").write_text("pub enum StripChunks { None }\n", encoding="utf-8")
    (src / "deflate/mod.rs").write_text("pub enum Deflater { Libdeflater }\n", encoding="utf-8")
    (src / "lib.rs").write_text(
        "pub fn optimize() {}\npub fn optimize_from_memory() {}\n",
        encoding="utf-8",
    )
    (src / "colors.rs").write_text(
        "pub enum ColorType { Grayscale, RGB, NewColor }\n"
        "pub enum BitDepth { One = 1, Eight = 8, ThirtyTwo = 32 }\n",
        encoding="utf-8",
    )
    manifest = {
        "upstream_version": "test",
        "options": {"exposed": {"force": "Options.force"}},
        "functions": {"exposed": ["optimize", "optimize_from_memory"]},
        "enums": {
            "FilterStrategy": {"unexposed": {"MinSum": "known"}},
            "RowFilter": {"unexposed": {"None": "known"}},
            "StripChunks": {"unexposed": {"None": "known"}},
            "Deflater": {"unexposed": {"Libdeflater": "known"}},
            "ColorType": {"unexposed": {"Grayscale": "known", "RGB": "known"}},
            "BitDepth": {"unexposed": {"One": "known", "Eight": "known"}},
        },
    }

    surface = scan_upstream_surface.parse_upstream_surface(upstream)
    report = scan_upstream_surface.compare_surface(surface, manifest)

    assert report["enums"]["ColorType"]["new_upstream_variants"] == ["NewColor"]
    assert report["enums"]["BitDepth"]["new_upstream_variants"] == ["ThirtyTwo"]
```

- [ ] **Step 2: Run scanner tests and confirm failure**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -k "surface" -v -ra
```

Expected: the new test fails because `ColorType` and `BitDepth` are not parsed.

- [ ] **Step 3: Extend the scanner**

In `scripts/scan_upstream_surface.py`, read `colors.rs` in `parse_upstream_surface`:

```python
colors_rs = (src / "colors.rs").read_text(encoding="utf-8")
```

Add these entries to the `enums` dict:

```python
"ColorType": parse_enum_variants(colors_rs, "ColorType"),
"BitDepth": parse_enum_variants(colors_rs, "BitDepth"),
```

- [ ] **Step 4: Update the surface design spec**

In `docs/specs/2026-05-26-upstream-surface-scan-design.md`, update the relevant Rust source list so it includes:

```markdown
- `src/colors.rs`: `ColorType`, `BitDepth`
```

- [ ] **Step 5: Run scanner against real upstream**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -k "surface" -v -ra
uv run --no-sync --group dev python scripts/scan_upstream_surface.py --update-docs
```

Expected: tests pass; real scan exits 0 and reports no blocking changes for oxipng 10.1.1.

- [ ] **Step 6: Commit**

Run:

```bash
git add scripts/scan_upstream_surface.py tests/test_scripts.py docs/specs/2026-05-26-upstream-surface-scan-design.md docs/api-surface/oxipng-10.1.1.toml
git commit -m "fix: scan raw image upstream enums"
git push origin main
```

---

### Task 4: Wheel Tag and Smoke Coverage Hardening

**Files:**

- Modify: `scripts/check_wheel_tags.py`
- Modify: `scripts/smoke_wheel.py`
- Modify: `tests/test_scripts.py`
- Modify: `.github/workflows/wheels.yml`
- Modify: `docs/process/release-artifacts.md`

- [ ] **Step 1: Add failing wheel tag tests**

Add tests to `tests/test_scripts.py`:

Update the module imports first if Task 3 has not already done it:

```python
from scripts import ai_filter_log, bump_upstream, check_wheel_tags, scan_upstream_surface, smoke_wheel
```

```python
def test_check_wheel_tags_rejects_wrong_python_tag(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_28_x86_64.whl"
    wheel.write_text("", encoding="utf-8")

    errors = check_wheel_tags.check_wheels([wheel], "manylinux_2_28_x86_64", "cp310")

    assert errors == [f"{wheel.name} uses Python tag cp311, expected cp310"]


def test_check_wheel_tags_accepts_cp310_abi3(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp310-abi3-manylinux_2_28_x86_64.whl"
    wheel.write_text("", encoding="utf-8")

    assert check_wheel_tags.check_wheels([wheel], "manylinux_2_28_x86_64", "cp310") == []
```

- [ ] **Step 2: Run focused script tests and confirm failure**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -k "wheel_tags" -v -ra
```

Expected: tests fail because `check_wheels` does not accept the expected Python tag argument.

- [ ] **Step 3: Add Python tag validation**

Change `scripts/check_wheel_tags.py`:

```python
def check_wheels(wheels: list[Path], expected_platform: str, expected_python: str) -> list[str]:
    """Return validation errors for wheel tags."""
    if not wheels:
        return ["no wheel paths provided"]

    errors: list[str] = []
    for wheel in wheels:
        try:
            python_tag, abi_tag, platform_tag = parse_wheel_tags(wheel)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if python_tag != expected_python:
            errors.append(f"{wheel.name} uses Python tag {python_tag}, expected {expected_python}")
        if abi_tag != "abi3":
            errors.append(f"{wheel.name} uses non-ABI3 tag {python_tag}-{abi_tag}")
        if not fnmatch.fnmatchcase(platform_tag, expected_platform):
            errors.append(
                f"{wheel.name} platform {platform_tag} does not match {expected_platform}"
            )

    return errors
```

Update CLI parsing:

```python
parser.add_argument("--expected-python", default="cp310")
errors = check_wheels(
    [Path(wheel) for wheel in args.wheels],
    args.expected_platform,
    args.expected_python,
)
```

- [ ] **Step 4: Extend wheel smoke to verify packaged typing and RawImage paths**

In `scripts/smoke_wheel.py`, add imports:

```python
from importlib import metadata
```

Add helper:

```python
def verify_packaged_typing_files() -> None:
    """Verify wheel includes typing metadata."""
    files = metadata.files("oxipng-pybind")
    if files is None:
        raise RuntimeError("installed distribution has no file metadata")
    names = {str(path) for path in files}
    if "oxipng/__init__.pyi" not in names:
        raise RuntimeError("wheel is missing oxipng/__init__.pyi")
    if "oxipng/py.typed" not in names:
        raise RuntimeError("wheel is missing oxipng/py.typed")
```

In `main`, call `verify_packaged_typing_files()` and extend runtime checks:

```python
memory_output = optimize_from_memory(bytearray(data), level=2)
view_output = optimize_from_memory(memoryview(data), level=2)
raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))
raw.add_png_chunk(b"tEXt", b"Comment\x00wheel smoke raw chunk")
raw_output = raw.create_optimized_png()
verify_png_bytes(memory_output)
verify_png_bytes(view_output)
verify_png_bytes(raw_output)
```

- [ ] **Step 5: Update wheel workflow to pass explicit Python tag**

Change `.github/workflows/wheels.yml` wheel tag step:

```yaml
run: python scripts/check_wheel_tags.py --expected-python cp310 --expected-platform "${{ matrix.expected-platform }}" dist/*.whl
```

- [ ] **Step 6: Run tests and local smoke script**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -k "wheel_tags or smoke" -v -ra
uv run --no-sync --group dev python scripts/smoke_wheel.py
```

Expected: tests pass; smoke script passes against the editable install.

- [ ] **Step 7: Update release artifact docs**

In `docs/process/release-artifacts.md`, add:

```markdown
Wheel tag validation requires the Python tag `cp310`, ABI tag `abi3`, and the
expected platform tag for each matrix entry.
```

- [ ] **Step 8: Commit**

Run:

```bash
git add scripts/check_wheel_tags.py scripts/smoke_wheel.py tests/test_scripts.py .github/workflows/wheels.yml docs/process/release-artifacts.md
git commit -m "ci: harden wheel tag and smoke checks"
git push origin main
```

---

### Task 5: Upstream Bump Workflow Security and Auto-Merge Gating

**Files:**

- Modify: `.github/workflows/upstream-bump.yml`
- Modify: `scripts/bump_upstream.py`
- Modify: `tests/test_scripts.py`
- Modify: `docs/process/upstream-bumps.md`

- [ ] **Step 1: Add release metadata helper tests**

Add tests to `tests/test_scripts.py`:

Update the module imports first if Task 3 has not already done it:

```python
from scripts import ai_filter_log, bump_upstream, check_wheel_tags, scan_upstream_surface, smoke_wheel
```

```python
def test_normalize_version_removes_leading_v() -> None:
    assert bump_upstream.normalize_version("v10.1.2") == "10.1.2"


def test_issue_body_mentions_manual_surface_triage() -> None:
    body = bump_upstream.issue_body("10.1.2", "## report")

    assert "Upstream version: 10.1.2" in body
    assert "- [ ] expose now" in body
    assert "- [ ] defer and document" in body
    assert "- [ ] reject as intentionally unsupported" in body
```

- [ ] **Step 2: Run bump helper tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -k "bump or issue_body" -v -ra
```

Expected: tests pass before workflow refactoring.

- [ ] **Step 3: Reduce default upstream bump permissions**

Change `.github/workflows/upstream-bump.yml` top-level permissions to:

```yaml
permissions:
  contents: read
```

Move write permissions onto only the PR creation job added in the next step.

- [ ] **Step 4: Split upstream bump into read-only prepare job and write-scoped publish job**

Restructure `.github/workflows/upstream-bump.yml` into two jobs:

```yaml
jobs:
  prepare:
    name: prepare oxipng bump
    runs-on: ubuntu-latest
    outputs:
      changed: ${{ steps.changes.outputs.changed }}
      target-version: ${{ steps.bump.outputs.target-version }}
    env:
      UV_PYTHON: "3.13"
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          version: 0.11.12
      - uses: dtolnay/rust-toolchain@1.85.1
        with:
          components: clippy
      - name: Install cargo-deny
        uses: taiki-e/install-action@v2
        with:
          tool: cargo-deny@0.19.7
      - name: Sync dependencies
        run: uv sync --group dev
      - name: Bump upstream
        id: bump
        run: uv run python scripts/bump_upstream.py
      - name: Fetch upstream source
        run: |
          version="${{ steps.bump.outputs.target-version }}"
          git clone --depth 1 --branch "v$version" https://github.com/oxipng/oxipng .cache/upstream/oxipng
      - name: Prepare API surface manifest
        run: |
          version="${{ steps.bump.outputs.target-version }}"
          mkdir -p docs/api-surface
          if [ ! -f "docs/api-surface/oxipng-$version.toml" ]; then
            previous="$(ls docs/api-surface/oxipng-*.toml | sort -V | tail -n 1)"
            cp "$previous" "docs/api-surface/oxipng-$version.toml"
            sed -i "s/^upstream_version = .*/upstream_version = \"$version\"/" "docs/api-surface/oxipng-$version.toml"
          fi
      - name: Scan upstream surface
        run: uv run --group dev python scripts/scan_upstream_surface.py --update-docs
      - name: Check for changes
        id: changes
        run: |
          if git diff --quiet; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi
      - name: Run CI before opening PR
        if: steps.changes.outputs.changed == 'true'
        run: make ci
      - name: Upload bump workspace
        if: steps.changes.outputs.changed == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: upstream-bump-workspace
          path: |
            Cargo.toml
            Cargo.lock
            pyproject.toml
            uv.lock
            CHANGELOG.md
            docs/api-surface/*.toml
            docs/architecture/api-compatibility.md
            docs/architecture/options-surface.md
            .cache/upstream-bump/target-version.txt
            .cache/upstream-surface/pr-body-section.md

  publish:
    name: publish oxipng bump PR
    needs: prepare
    if: needs.prepare.outputs.changed == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v6
      - uses: actions/download-artifact@v4
        with:
          name: upstream-bump-workspace
      - name: Check upstream bump token
        env:
          UPSTREAM_BUMP_TOKEN: ${{ secrets.UPSTREAM_BUMP_TOKEN }}
        run: |
          if [ -z "$UPSTREAM_BUMP_TOKEN" ]; then
            echo "UPSTREAM_BUMP_TOKEN is required to create bump PRs with normal PR CI checks and auto-merge."
            exit 1
          fi
      - name: Write pull request body
        run: |
          mkdir -p .cache/upstream-bump
          {
            echo "Automated upstream oxipng bump."
            echo
            cat .cache/upstream-surface/pr-body-section.md
            echo
            echo "Auto-merge is enabled only after required checks pass."
          } > .cache/upstream-bump/pr-body.md
      - name: Create pull request
        id: cpr
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.UPSTREAM_BUMP_TOKEN }}
          commit-message: "chore: bump upstream oxipng"
          title: "chore: bump upstream oxipng"
          body-path: .cache/upstream-bump/pr-body.md
          branch: automation/bump-oxipng
          delete-branch: true
          labels: dependencies, automated
      - name: Create or update upstream surface issue
        env:
          GH_TOKEN: ${{ secrets.UPSTREAM_BUMP_TOKEN }}
        run: |
          uv run python - <<'PY'
          from pathlib import Path
          from scripts.bump_upstream import upsert_surface_issue

          version = Path(".cache/upstream-bump/target-version.txt").read_text(encoding="utf-8").strip()
          upsert_surface_issue(version, Path(".cache/upstream-surface/pr-body-section.md"))
          PY
```

When applying this step, preserve the exact current commands from the original workflow for setup, scan, CI, PR creation, issue creation, and auto-merge.

- [ ] **Step 5: Gate auto-merge on wheel checks**

Add this step before `Enable auto-merge` in the `publish` job:

```yaml
- name: Wait for wheel workflow
  if: >-
    steps.cpr.outputs.pull-request-number != '' &&
    contains(fromJSON('["created", "updated"]'), steps.cpr.outputs.pull-request-operation)
  env:
    GH_TOKEN: ${{ secrets.UPSTREAM_BUMP_TOKEN }}
  run: |
    pr="${{ steps.cpr.outputs.pull-request-number }}"
    sha="$(gh pr view "$pr" --json headRefOid --jq .headRefOid)"
    for attempt in $(seq 1 60); do
      conclusion="$(gh run list --workflow wheels.yml --commit "$sha" --json status,conclusion --jq '.[0] | "\(.status) \(.conclusion)"')"
      case "$conclusion" in
        "completed success") exit 0 ;;
        "completed failure"|"completed cancelled"|"completed timed_out") echo "wheels workflow failed: $conclusion"; exit 1 ;;
      esac
      sleep 30
    done
    echo "timed out waiting for wheels workflow"
    exit 1
```

- [ ] **Step 6: Document action pinning follow-up policy inside the repo**

Add this paragraph to `docs/process/upstream-bumps.md`:

```markdown
The upstream bump workflow keeps dependency update, source scan, and CI execution
in a read-only job. Only the PR/issue publication job receives write
permissions. Mutable action tags should be replaced with full commit SHAs during
release-hardening maintenance, and the resolved SHAs should be reviewed before
merge.
```

- [ ] **Step 7: Run YAML and Python checks**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_scripts.py -k "bump or issue_body" -v -ra
uv run --no-sync --group dev ruff check scripts/bump_upstream.py tests/test_scripts.py
uv run --no-sync --group dev basedpyright
```

Expected: all commands pass.

- [ ] **Step 8: Commit**

Run:

```bash
git add .github/workflows/upstream-bump.yml scripts/bump_upstream.py tests/test_scripts.py docs/process/upstream-bumps.md
git commit -m "ci: reduce upstream bump write scope"
git push origin main
```

---

### Task 6: Documentation and Public API Coverage Cleanup

**Files:**

- Modify: `README.md`
- Modify: `docs/architecture/api-compatibility.md`
- Modify: `docs/usage/raw-image.md`
- Modify: `docs/api-surface/oxipng-10.1.1.toml`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Fix install wording**

Replace the README install block with:

```markdown
Release artifacts use PyO3 ABI3 wheels for Python 3.10 and newer. Until PyPI
publishing is enabled, install from a built wheel artifact or build locally with
`make wheel`.
```

Remove the `pip install oxipng-pybind` code block until publishing is enabled.

- [ ] **Step 2: Fix RawImage compatibility wording**

In `docs/architecture/api-compatibility.md`, replace:

```markdown
- raw pixel buffer APIs
```

with:

```markdown
- pyoxipng-specific raw buffer helpers beyond `RawImage`
```

- [ ] **Step 3: Document RawImage transparency, chunks, and ICC**

In `docs/usage/raw-image.md`, add after the palette section:

````markdown
Transparent colors are supported for grayscale and RGB raw images:

```python
gray = RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]), transparent=0)
rgb = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]), transparent=(255, 0, 0))
```

`transparent` is not accepted for indexed, grayscale-alpha, or RGBA images.
Indexed images should express transparency with alpha values in palette entries.
````

Add after the auxiliary chunk example:

````markdown
Only safe ancillary chunk names are accepted by `add_png_chunk`. Structural PNG
chunks such as `IHDR`, `PLTE`, `IDAT`, and `IEND` are generated by the encoder.

ICC profiles can be attached before optimization:

```python
raw.add_icc_profile(icc_profile_bytes)
```
````

- [ ] **Step 4: Clarify stub constructor docstring**

In `oxipng/__init__.pyi`, change the `RawImage.__init__` docstring to:

```python
"""Create a raw image from packed pixel data."""
```

- [ ] **Step 5: Make manifest scope explicit**

In `docs/api-surface/oxipng-10.1.1.toml`, add under `upstream_version`:

```toml
manifest_scope = "Tracks upstream oxipng surface mapped or intentionally not mapped by this package. Python-only options such as backup and preserve_attrs are documented in stubs and usage docs."
```

Add a `[classes.RawImage.methods]` table:

```toml
[classes.RawImage.methods]
constructor = "RawImage(width, height, color_type, bit_depth, data, *, palette=None, transparent=None)"
create_optimized_png = "RawImage.create_optimized_png(**memory_options)"
add_png_chunk = "RawImage.add_png_chunk(name, data)"
add_icc_profile = "RawImage.add_icc_profile(data)"
```

- [ ] **Step 6: Add path-like coverage tests**

Add to `tests/test_api.py`:

```python
class CustomPathLike:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __fspath__(self) -> str:
        return str(self.path)


def test_optimize_accepts_string_paths(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.png"

    optimize(str(png_path), str(output))

    assert_readable_png_path(output)


def test_optimize_accepts_custom_pathlike(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.png"

    optimize(CustomPathLike(png_path), CustomPathLike(output))

    assert_readable_png_path(output)
```

- [ ] **Step 7: Run docs and API tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -v -ra
make md-lint
```

Expected: tests pass; markdown lint passes.

- [ ] **Step 8: Commit**

Run:

```bash
git add README.md docs/architecture/api-compatibility.md docs/usage/raw-image.md docs/api-surface/oxipng-10.1.1.toml oxipng/__init__.pyi tests/test_api.py
git commit -m "docs: clarify raw image public surface"
git push origin main
```

---

### Task 7: Memory-Copy Performance Investigation and Optional Buffer Fast Path

**Files:**

- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`
- Modify: `docs/architecture/overview.md`

- [ ] **Step 1: Add regression tests for bytearray and memoryview**

Keep the existing bytearray and memoryview tests. Add a non-contiguous memoryview rejection test if the implementation moves to `PyBuffer`:

```python
def test_optimize_from_memory_rejects_non_contiguous_memoryview(png_bytes: bytes) -> None:
    view = memoryview(png_bytes)[::2]

    with pytest.raises(TypeError, match="contiguous"):
        optimize_from_memory(view)
```

- [ ] **Step 2: Measure current copy behavior manually**

Run:

```bash
uv run --no-sync --group dev python - <<'PY'
from io import BytesIO
from PIL import Image
from oxipng import optimize_from_memory

buffer = BytesIO()
Image.new("RGBA", (1024, 1024), (255, 0, 0, 255)).save(buffer, format="PNG")
data = buffer.getvalue()
for value in (data, bytearray(data), memoryview(data)):
    out = optimize_from_memory(value)
    print(type(value).__name__, len(data), len(out))
PY
```

Expected: command completes and prints three lines.

- [ ] **Step 3: Implement `PyBuffer` fast path only if it stays simple**

If PyO3 `PyBuffer<u8>` is available with the pinned dependency set, replace the `memoryview` `tobytes()` path in `bytes_like_to_vec` with direct contiguous buffer copying. Keep the owned `Vec<u8>` handoff to upstream unless a borrowed slice can be safely held through `allow_threads` without unsound lifetime work.

Use this shape:

```rust
if let Ok(buffer) = pyo3::buffer::PyBuffer::<u8>::get(data) {
    if !buffer.is_c_contiguous() {
        return Err(PyTypeError::new_err("data buffer must be contiguous"));
    }
    let slice = unsafe { buffer.as_slice(data.py()) }
        .ok_or_else(|| PyTypeError::new_err("data buffer must expose bytes"))?;
    return Ok(slice.to_vec());
}
```

If this does not compile cleanly with the pinned PyO3 version, do not force the refactor. Keep the current copying behavior and document the current cost in `docs/architecture/overview.md`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py -k "memoryview or bytearray or optimize_from_memory" -v -ra
cargo test
```

Expected: all commands pass.

- [ ] **Step 5: Commit**

If code changed, run:

```bash
git add src/lib.rs tests/test_api.py docs/architecture/overview.md
git commit -m "perf: improve bytes-like input handling"
git push origin main
```

If only docs changed, run:

```bash
git add docs/architecture/overview.md
git commit -m "docs: record bytes-like input copy behavior"
git push origin main
```

---

### Task 8: Final Verification

**Files:**

- Verify all modified files from Tasks 1-7.

- [ ] **Step 1: Check worktree**

Run:

```bash
git status --short
```

Expected: clean or only intentional uncommitted plan checkbox updates.

- [ ] **Step 2: Run full verification**

Run:

```bash
make setup
make ci
make pre-commit-check
make format-check
uv run --no-sync --group dev pytest --cov=oxipng --cov=scripts --cov-report=term-missing -q
```

Expected: all commands pass.

- [ ] **Step 3: Build and inspect wheel**

Run:

```bash
make wheel
python scripts/check_wheel_tags.py --expected-python cp310 --expected-platform manylinux_2_34_x86_64 target/wheels/*.whl
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile

wheel = next(Path("target/wheels").glob("*.whl"))
with ZipFile(wheel) as archive:
    names = set(archive.namelist())
required = {"oxipng/__init__.pyi", "oxipng/py.typed"}
missing = sorted(required - names)
if missing:
    raise SystemExit(f"missing wheel files: {missing}")
print(wheel.name)
PY
```

Expected: tag checker passes and wheel inspection prints the wheel filename.

- [ ] **Step 4: Smoke installed wheel**

Run:

```bash
tmpdir="$(mktemp -d)"
uv run --group dev python -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/pip" install target/wheels/*.whl pillow
"$tmpdir/venv/bin/python" scripts/smoke_wheel.py
rm -rf "$tmpdir"
```

Expected: smoke script exits 0.

- [ ] **Step 5: Final commit and push if needed**

If verification produced intentional changes, commit them explicitly:

```bash
git add docs/superpowers/plans/2026-05-26-review-findings-fix-plan.md
git commit -m "docs: plan review finding fixes"
git push origin main
```

Do not use `git add .`.

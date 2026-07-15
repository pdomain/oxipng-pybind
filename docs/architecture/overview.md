# Architecture Overview

`oxipng-pybind` is a Python package that wraps the Rust `oxipng` crate. Users
import it as `oxipng`.

## Package Layout

- `oxipng/__init__.py` is the Python facade.
- `oxipng/__init__.pyi` defines the typed Python API.
- `oxipng/py.typed` marks the package as typed.
- `src/lib.rs` is the PyO3 Rust extension.
- `.github/workflows/ci.yml` runs source checks.
- `.github/workflows/wheels.yml` builds release wheels.
- `.github/workflows/upstream-bump.yml` updates the Rust `oxipng` version.

## Rust and Python Split

The Python facade owns public names and stable call signatures. It also owns
compatibility warnings for old pyoxipng shapes.

See [API Compatibility](api-compatibility.md) for stable names, warnings, and
migration paths.

The Rust extension owns:

- path conversion
- option validation
- file controls
- raw image validation
- GIL release
- calls into upstream Rust `oxipng`

The GIL (Global Interpreter Lock) is the Python lock that normally stops Python
code from running in parallel.

The binding copies Python-owned data into Rust memory before long optimization
work, then releases the GIL.

## File Optimization Flow

`optimize(input=..., output=None, ...)` accepts path-like objects. Rust converts
those paths to `PathBuf` values.

Rust handles file-only controls, such as `backup` and `preserve_attrs`.

Rust then calls `oxipng::optimize` with the GIL released. If `output` is
omitted, Rust `oxipng` writes in place; if `output` is set, it writes to that
path instead.

## Memory Optimization Flow

`optimize_from_memory(data=..., ...)` accepts:

- `bytes`
- `bytearray`
- `memoryview`

The binding copies the input into Rust memory before it releases the GIL. Rust
calls `oxipng::optimize_from_memory`. The Python return value is optimized PNG
bytes.

Memory mode, `analyze`, and `RawImage.create_optimized_png` reject file-only
options. See [Options Surface](options-surface.md) for supported options.

## Raw Image Optimization Flow

`RawImage(width=..., height=..., color_type=..., bit_depth=..., data=...)`
wraps Rust `oxipng::RawImage`. The stable constructor does not warn.

Python `ColorType` and `BitDepth` values become Rust raw-image metadata. Packed
pixel bytes are copied into Rust memory.

`RawImage.create_optimized_png(...)` uses the memory-mode option parser and
returns PNG bytes.

`add_png_chunk` adds auxiliary chunks. It accepts only valid safe-to-copy
ancillary PNG chunk names and rejects structural chunks.

`add_icc_profile` attaches ICC profile data.

## Error Mapping

The wrapper keeps caller mistakes separate from image failures.

- Invalid boolean types raise `TypeError`.
- Invalid known values raise `ValueError`.
- Unsupported option names raise `TypeError`.
- Existing backup paths raise `FileExistsError`.
- File read and write failures raise `FileNotFoundError` or `OSError`.
- PNG decode and optimization failures raise `oxipng.PngError`.

## Wheel Strategy

Release builds use separate `abi3-py310` and `abi3-py311` PyO3 lanes. Each
wheel supports its ABI3 Python floor and newer versions on one platform.

See [Release Artifacts](../process/release-artifacts.md) for wheel targets,
checks, and publishing rules.

## Rust oxipng Surface

This wrapper exposes a small subset of Rust `oxipng`. The API surface manifest
records what is exposed and what is intentionally not exposed.

During Rust `oxipng` updates, `scripts/scan_upstream_surface.py` reports new or
removed Rust surface area. It does not expose new Python API by itself.

See [Upstream Bumps](../process/upstream-bumps.md) for the update workflow.

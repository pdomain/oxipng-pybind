# Architecture Overview

`oxipng-pybind` is a Python package over the Rust `oxipng` crate. The package
name is `oxipng-pybind`. The import name is `oxipng`.

## Package Layout

- `oxipng/__init__.py` is the Python facade.
- `oxipng/__init__.pyi` defines the typed Python API.
- `oxipng/py.typed` marks the package as typed.
- `src/lib.rs` is the PyO3 Rust extension.
- `.github/workflows/ci.yml` runs source checks.
- `.github/workflows/wheels.yml` builds release wheels.
- `.github/workflows/upstream-bump.yml` updates the Rust `oxipng` version.

## Rust and Python Split

The Python facade owns public names, stable call signatures, and compatibility
warnings for old pyoxipng shapes. See
[API Compatibility](api-compatibility.md) for the stable API and migration
paths.

`RowFilter` is available only for old pyoxipng-style code. It emits
compatibility warnings. New code should use `FilterStrategy` or
`FilterStrategy.predefined(...)`.

The Rust extension owns:

- path conversion
- option validation
- file controls
- raw image validation
- GIL release
- calls into Rust `oxipng`

The GIL (Global Interpreter Lock) is the Python lock that normally stops Python
code from running in parallel. Rust copies Python-owned data before long
optimization work. Then it releases the GIL.

## File Flow

`optimize(input=..., output=None, ...)` accepts path-like objects. Rust converts
those paths to `PathBuf` values.

Rust handles file-only controls:

- `backup`
- `preserve_attrs`

When `backup=True`, Rust creates `<input>.bak` before an in-place write.
Existing backup paths raise `FileExistsError`.

Then Rust calls `oxipng::optimize` with the GIL released. If `output` is
omitted, Rust `oxipng` writes in place. If `output` is set, Rust `oxipng` writes
to that path.

## Memory Flow

`optimize_from_memory(data=..., ...)` accepts:

- `bytes`
- `bytearray`
- `memoryview`

The binding copies the input into Rust memory before it releases the GIL. Rust
calls `oxipng::optimize_from_memory`. The Python return value is optimized PNG
bytes.

Memory mode rejects file-write options such as `backup` and `preserve_attrs`.
`analyze` and `RawImage.create_optimized_png` reject those options too.

## Raw Image Flow

`RawImage(width=..., height=..., color_type=..., bit_depth=..., data=...)`
wraps Rust `oxipng::RawImage`. The stable constructor does not warn.

Python `ColorType` and `BitDepth` values become Rust raw-image metadata. Packed
pixel bytes are copied into Rust memory.

`RawImage.create_optimized_png(...)` uses the memory-mode option parser and
returns PNG bytes.

`add_png_chunk` adds auxiliary chunks. `add_icc_profile` attaches ICC profile
data. `add_png_chunk` accepts only valid safe-to-copy ancillary PNG chunk names.
It rejects structural chunks such as:

- `IHDR`
- `IDAT`
- `IEND`
- `PLTE`
- `tRNS`
- `iCCP`

## Error Mapping

The wrapper keeps caller mistakes separate from image failures.

- Invalid boolean types raise `TypeError`.
- Invalid known values raise `ValueError`.
- Unsupported option names raise `TypeError`.
- Existing backup paths raise `FileExistsError`.
- File read and write failures raise `FileNotFoundError` or `OSError`.
- PNG decode and optimization failures raise `oxipng.PngError`.

## Wheel Strategy

PyO3 uses `abi3-py311`. Each release wheel supports Python 3.11 and newer for
one platform. The wheel workflow builds Linux, macOS, and Windows wheels and
uploads wheel artifacts.

On release tags, the workflow verifies source checks and the complete wheel set
before PyPI publishing.

## Rust oxipng Surface

This wrapper exposes a small subset of Rust `oxipng`. The API surface manifest
records what is exposed and what is intentionally not exposed.

During Rust `oxipng` updates, `scripts/scan_upstream_surface.py` reports new or
removed Rust surface area. It does not expose new Python API by itself.

# Architecture Overview

`oxipng-pybind` is a Python package over the upstream Rust `oxipng` crate.
The package name is `oxipng-pybind`, and the import name is `oxipng`.

## Package Layout

- `oxipng/__init__.py` is the Python facade. It exposes public names and
  imports native functions and classes from `_oxipng`.
- `oxipng/__init__.pyi` defines the typed Python API.
- `oxipng/py.typed` tells type checkers that the package is typed.
- `src/lib.rs` is the Rust extension built with PyO3.
- `.github/workflows/ci.yml` runs source checks.
- `.github/workflows/wheels.yml` builds release wheel artifacts.
- `.github/workflows/upstream-bump.yml` updates the pinned upstream version and
  scans the upstream API surface.

## Rust/Python Boundary

The Python facade owns ergonomic names. This includes `Interlacing`,
`StripChunks`, `Deflater`, `Deflaters`, `FilterStrategy`, `ColorType`,
`BitDepth`, and compatibility warnings.

The Rust extension owns path conversion, option validation, file controls, raw
image validation, and GIL release. The GIL is the Python lock that normally
prevents Python code from running in parallel.

Rust accepts strings, enum `.value` strings, and supported factory objects. It
builds `oxipng::Options`, calls upstream `oxipng`, and maps errors back to
Python.

Unsupported keyword names raise `TypeError`. Invalid known values raise
`ValueError`. Upstream PNG failures raise `PngError`.

## File Flow

`optimize(input, output=None, *, ...)` accepts path-like objects. PyO3 converts
them to Rust `PathBuf` values.

Rust handles file-only controls such as `backup` and `preserve_attrs`. When
`backup=True`, Rust first creates `<input>.bak`. This only works for in-place
optimization. Existing backup paths raise `FileExistsError`.

Then Rust calls `oxipng::optimize` while the GIL is released.

If `output` is omitted, upstream writes in place. If `output` is set, upstream
writes to that path.

Callers that process untrusted files must provide safe work directories and
server-generated paths. See [Untrusted Input](../usage/untrusted-input.md).

## Memory Flow

`optimize_from_memory(data, *, ...)` accepts `bytes`, `bytearray`, and
`memoryview`.

Python-visible data is copied into owned Rust memory before the GIL is released.
Rust then calls `oxipng::optimize_from_memory` and returns optimized PNG bytes.

File-write options such as `backup` and `preserve_attrs` are rejected in memory
mode. They are also rejected by `analyze` and `RawImage.create_optimized_png`.

## Raw Image Flow

`RawImage(width, height, color_type, bit_depth, data, *, palette=None,
transparent=None)` wraps upstream `oxipng::RawImage`. This stable constructor
does not warn. Python `ColorType` and `BitDepth` values become upstream raw
image metadata. Packed pixel bytes are copied into Rust memory.

`RawImage.create_optimized_png(**options)` uses the memory-mode option parser
and returns PNG bytes. `add_png_chunk` adds auxiliary chunks. `add_icc_profile`
attaches ICC profile data. `add_png_chunk` only accepts valid safe-to-copy
ancillary PNG chunk names. It rejects structural chunks such as `IHDR`, `IDAT`,
`IEND`, `PLTE`, `tRNS`, and `iCCP`.

## Error Mapping

The wrapper keeps caller mistakes separate from image failures:

- Invalid boolean types use `TypeError`.
- Invalid known values use `ValueError`.
- Unsupported option names use `TypeError`.
- Existing backup paths use `FileExistsError`.
- Upstream file read/write failures become `FileNotFoundError` or `OSError`.
- Upstream PNG decode and optimization failures become `oxipng.PngError`.

## Wheel Strategy

PyO3 uses `abi3-py311`. Release wheels use one ABI3 extension per supported
platform for Python 3.11 and newer.

PyPI wheels are the supported release path. Source builds remain the fallback
for unsupported platforms and require Rust plus a compatible build environment.

## Upstream Surface Policy

The wrapper exposes a small subset of upstream `oxipng`. The checked-in API
surface manifest records exposed and intentionally unexposed items.

During upstream bumps, `scripts/scan_upstream_surface.py` reports new or removed
upstream surface area. It does not expose new Python API by itself.

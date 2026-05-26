# Architecture Overview

`oxipng-pybind` publishes the `oxipng` Python import package and delegates PNG
optimization to the upstream Rust `oxipng` crate.

## Package Layout

- `oxipng/__init__.py` is the Python facade. It exposes public enum helpers and
  imports native functions from `_oxipng`.
- `oxipng/__init__.pyi` is the typing contract for the public API.
- `oxipng/py.typed` marks the package as typed for static analyzers.
- `src/lib.rs` is the PyO3 extension. It parses Python arguments, builds
  upstream `oxipng::Options`, calls upstream optimization functions, and maps
  errors back to Python.
- `.github/workflows/ci.yml` runs source checks.
- `.github/workflows/wheels.yml` builds artifact-only release wheels.
- `.github/workflows/upstream-bump.yml` updates the pinned upstream version and
  runs the surface scanner.

## Rust/Python Boundary

Python owns public convenience objects such as `Interlacing`, `StripChunks`,
`Deflater`, and `FilterStrategy`. Rust accepts strings and enum `.value`
strings, so option parsing does not depend on Python enum object identity.

The extension starts from `oxipng::Options::from_preset(level)` and applies only
the documented overrides. Unsupported keyword names raise `TypeError`, invalid
recognized values raise `ValueError`, and upstream PNG failures raise
`PngError`.

## File Optimization Flow

`optimize(input, output=None, *, ...)` receives path-like objects from Python.
The wrapper validates file-only controls such as `backup` and `preserve_attrs`,
copies `<input>.bak` before in-place optimization when requested, and then calls
`oxipng::optimize` while the GIL is released.

When `output` is omitted, upstream writes in place through `OutFile::Path` with
`path: None`. When `output` is provided, upstream writes to that path.

## Memory Optimization Flow

`optimize_from_memory(data, *, ...)` accepts `bytes`, `bytearray`, and
`memoryview`. The wrapper copies Python-owned bytes before releasing the GIL,
then calls `oxipng::optimize_from_memory` and returns optimized PNG bytes.

File-only options such as `backup` and `preserve_attrs` are rejected for memory
optimization.

## Raw Image Flow

`RawImage(width, height, color_type, bit_depth, data, *, palette=None,
transparent=None)` wraps upstream `oxipng::RawImage`. Python `ColorType` and
`BitDepth` enum values are converted to upstream raw image metadata, and packed
pixel bytes are copied before being passed to Rust.

`RawImage.create_optimized_png(**options)` reuses the memory-mode option parser
and returns PNG bytes. Auxiliary chunks can be added through `add_png_chunk`,
and ICC profile data can be attached through `add_icc_profile`.

## Error Mapping

The wrapper keeps caller mistakes distinct from image processing failures:

- invalid Python types use `TypeError`;
- invalid recognized values use `ValueError`;
- existing backup paths use `FileExistsError`;
- upstream `oxipng::PngError` values become `oxipng.PngError`.

## Wheel Strategy

PyO3 is configured with `abi3-py310`, so release wheels use one ABI3 extension
per supported platform for Python 3.10 and newer. The wheel workflow uploads
artifacts only in this phase; it does not publish to PyPI and does not build an
sdist.

## Upstream Surface Policy

The wrapper intentionally exposes a conservative subset of upstream `oxipng`.
The checked-in API surface manifest records exposed and intentionally unexposed
items. During upstream bumps, `scripts/scan_upstream_surface.py` reports new or
removed upstream surface area and updates docs for human triage without
automatically exposing new Python API.

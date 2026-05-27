# Release Artifacts

PyPI wheels are the supported release path for `oxipng-pybind`.

`.github/workflows/wheels.yml` builds and validates release wheel artifacts.

It runs on `workflow_dispatch`, on `v*` tags, and on pull requests that touch
release-relevant files.

It builds wheels with `PyO3/maturin-action@v1` and Python 3.11. It uploads
platform-specific wheel artifacts for publishing to PyPI.

Source builds are the fallback for unsupported platforms. They require Rust and
a compatible build environment. The release process does not build or upload an
sdist.

## Wheel Tags

Expected wheel Python and ABI tags use `cp311-abi3` for Python 3.11 and newer.
ABI means application binary interface.

The wheel tag check validates the Python tag, ABI tag, and platform tag before
artifacts are uploaded.

Expected platform tags are:

- `manylinux_2_28_x86_64`
- `manylinux_2_28_aarch64`
- `macosx_*_x86_64`
- `macosx_*_arm64`
- `win_amd64`

## Smoke Checks

Each wheel is installed into a clean virtual environment. Then
`scripts/smoke_wheel.py` checks it.

The smoke test imports the package. It optimizes files in place and to an output
path. It optimizes bytes in memory from `bytearray` and `memoryview`. It creates
a `RawImage`, adds a PNG chunk, and optimizes it. It verifies all outputs with
Pillow.

The smoke test also verifies wheel typing files:

- `oxipng/__init__.pyi`
- `oxipng/py.typed`

Linux aarch64 uses GitHub's native `ubuntu-24.04-arm` runner. Runtime smoke
testing gates that target.

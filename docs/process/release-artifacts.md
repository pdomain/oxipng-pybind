# Release Artifacts

`.github/workflows/wheels.yml` builds release wheel artifacts.

The workflow is artifact-only in this phase.

It builds wheels with `PyO3/maturin-action@v1`. It uploads platform-specific
wheel artifacts. It does not publish to PyPI or TestPyPI. It does not build or
upload an sdist.

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
path. It optimizes bytes in memory. It verifies all outputs with Pillow.

Linux aarch64 uses GitHub's native `ubuntu-24.04-arm` runner. Runtime smoke
testing gates that target.

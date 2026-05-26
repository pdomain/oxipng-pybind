# Release Artifacts

Wheel artifact production is handled by `.github/workflows/wheels.yml`.

The workflow is artifact-only in this phase:

- it builds wheels with `PyO3/maturin-action@v1`;
- it uploads platform-specific wheel artifacts;
- it does not publish to PyPI or TestPyPI;
- it does not build or upload an sdist.

Expected wheel Python and ABI tags use `cp310-abi3` for Python 3.10 and newer.
The wheel tag check validates the Python tag, ABI tag, and platform tag before
artifacts are uploaded. Expected platform tags are:

- `manylinux_2_28_x86_64`
- `manylinux_2_28_aarch64`
- `macosx_*_x86_64`
- `macosx_*_arm64`
- `win_amd64`

Each wheel is installed into a clean virtual environment and checked with
`scripts/smoke_wheel.py`. The smoke test imports the package, optimizes files
in place and to an output path, optimizes bytes in memory, and verifies all
outputs with Pillow. Linux aarch64 uses GitHub's native `ubuntu-24.04-arm`
runner so runtime smoke testing is gating for that target.

# Release Artifacts

Wheel artifact production is handled by `.github/workflows/wheels.yml`.

The workflow is artifact-only in this phase:

- it builds wheels with `PyO3/maturin-action@v1`;
- it uploads platform-specific wheel artifacts;
- it does not publish to PyPI or TestPyPI;
- it does not build or upload an sdist.

Expected wheel ABI tags use `cp310-abi3` for Python 3.10 and newer. Expected
platform tags are:

- `manylinux_2_28_x86_64`
- `manylinux_2_28_aarch64`
- `macosx_*_x86_64`
- `macosx_*_arm64`
- `win_amd64`

Each wheel is installed into a clean virtual environment and checked with
`scripts/smoke_wheel.py`. The smoke test imports the package, optimizes files
in place and to an output path, optimizes bytes in memory, and verifies all
outputs with Pillow.

If Linux aarch64 runtime smoke testing is blocked by QEMU-specific behavior,
the workflow must upload `linux-aarch64-smoke-exception.txt` with the wheel
filename, runner image, failing command, QEMU-specific reason, and tracking
issue or link.

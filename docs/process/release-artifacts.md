# Release Artifacts

PyPI wheels are the primary release path for `oxipng-pybind`. The release
workflow also publishes a source distribution for unsupported platforms and
source-build fallback users.

`.github/workflows/wheels.yml` builds and validates release wheel and sdist
artifacts.

It runs on `workflow_dispatch`, on `v*` tags, and on pull requests that touch
release-relevant files.

It builds wheels with `PyO3/maturin-action@v1` and Python 3.11. It also builds
one sdist, verifies it, builds a wheel back from that sdist in a clean virtual
environment, and uploads the verified artifacts for publishing to PyPI.

Source builds require Rust and a compatible build environment.

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

## Artifact Content Verification

`scripts/verify_release_artifacts.py` opens release artifacts before they are
uploaded or published.

For wheels, it verifies:

- wheel metadata files under `.dist-info`;
- license and third-party notice files;
- package files, including stubs and `py.typed`;
- exactly one native extension under the `_oxipng` package layout.

For sdists, it verifies required source, package, metadata, license, and notice
files. The workflow also builds a wheel from the sdist and verifies that derived
wheel before publishing.

The PyPI publish job runs only after all wheel jobs and the sdist job pass.

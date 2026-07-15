# Release Artifacts

PyPI wheels are the main release artifact for `oxipng-pybind`. The release
workflow also publishes one source distribution (sdist) for users who build
from source or use an unsupported platform.

Source builds need Rust and a compatible build environment.

[`.github/workflows/wheels.yml`](../../.github/workflows/wheels.yml) is the
only workflow that publishes artifacts. It runs for:

- `workflow_dispatch`;
- `v*` tags;
- pull requests that touch release files.

Manual runs are build-only by default. Set `publish-target` to `testpypi` to
publish verified artifacts to TestPyPI through the `testpypi` GitHub
environment and TestPyPI Trusted Publishing.

Manual TestPyPI runs rewrite `project.version` only in the workflow workspace.
They add a `.devNNN` suffix from `GITHUB_RUN_NUMBER` and
`GITHUB_RUN_ATTEMPT`. This avoids collisions between rehearsal uploads.

Real PyPI publishing is tag-driven. Push a strict final release tag, or let
[Upstream Bumps](upstream-bumps.md#release-tags) create one for an automated
upstream bump. The wheels workflow builds fresh artifacts from that tag before
publishing. For manual operator steps, see [Manual Release](manual-release.md).

Valid PyPI release tags:

- `v10.1.1`
- `v10.1.1.post1`

Invalid PyPI release tags:

- `vtest`
- `v10.1`
- `v10.1.1.dev1`
- `v10.1.1rc1`

The release tag must match `project.version` in `pyproject.toml`.

The publish gate also checks for duplicate releases. It rejects a release if
the version is already present on PyPI.

The PyPI Trusted Publisher must be configured with:

- project: `oxipng-pybind`
- owner: `pdomain`
- repository: `oxipng-pybind`
- workflow: `wheels.yml`
- environment: `pypi`

The TestPyPI Trusted Publisher must be configured with:

- project: `oxipng-pybind`
- owner: `pdomain`
- repository: `oxipng-pybind`
- workflow: `wheels.yml`
- environment: `testpypi`

## Wheel Tag Requirements

Release wheels use `cp310-abi3` for Python 3.10 and `cp311-abi3` for Python
3.11 and newer.

Before upload, the wheel tag check validates the Python tag, the application
binary interface (ABI) tag, and the platform tag.

Expected platform tags are:

- `manylinux_2_28_x86_64`
- `manylinux_2_28_aarch64`
- `macosx_*_x86_64`
- `macosx_*_arm64`
- `win_amd64`

## Smoke Checks

Each wheel installs into a clean virtual environment. Then
[`scripts/smoke_wheel.py`](../../scripts/smoke_wheel.py) imports the package,
checks common optimization paths, verifies PNG outputs, and checks these
wheel typing files:

- `oxipng/__init__.pyi`
- `oxipng/py.typed`

PNG verification differs by Python version. Python 3.11+ lanes use Pillow.
The Python 3.10 lane uses the script's stdlib PNG checks instead, so release
smoke tests do not depend on third-party wheels that no longer publish
CPython 3.10 artifacts.

Linux aarch64 uses GitHub's native `ubuntu-24.04-arm` runner. Runtime smoke
testing is required for that target.

## Artifact Content Verification

[`scripts/verify_release_artifacts.py`](../../scripts/verify_release_artifacts.py)
opens artifacts before upload and before publish.

For wheels, it verifies:

- wheel metadata files under `.dist-info`;
- required license and notice files;
- package files, stubs, and `py.typed`;
- exactly one native extension under the `_oxipng` package layout.

For sdists, it verifies required source, package, metadata, license, and notice
files. The workflow also builds and verifies a wheel from the sdist.

The PyPI publish job runs only after all wheel jobs, the sdist job, and
release tag validation pass.

The TestPyPI publish job uses the same verified artifact set. It runs only
for manual workflow dispatches where `publish-target` is `testpypi`.

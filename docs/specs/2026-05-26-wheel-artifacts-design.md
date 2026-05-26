# Wheel Artifact Workflow Design

## Summary

Add an artifact-only wheel workflow for `oxipng-pybind`. The workflow builds
installable wheels for supported platforms, smoke-tests each wheel where
practical, and uploads the wheels as GitHub Actions artifacts. It does not
publish to PyPI and does not build an sdist.

## Goals

- Build wheels users can install without a local Rust toolchain.
- Use PyO3 `abi3-py311` so one wheel per platform supports Python 3.11+.
- Build and smoke-test wheels before any PyPI publishing workflow exists.
- Keep release artifact production separate from regular source CI.
- Avoid source distributions in this phase.

## Non-Goals

- No PyPI publish.
- No TestPyPI publish.
- No sdist.
- No 32-bit wheels.
- No musllinux wheels.
- No macOS universal2 wheel unless a later release design requests it.

## Packaging Changes

`Cargo.toml` must enable ABI3:

```toml
pyo3 = { version = "0.25.1", features = ["extension-module", "abi3-py311"] }
```

`pyproject.toml` keeps `requires-python = ">=3.11"` and `module-name =
"_oxipng"`.

The maturin include list should only claim wheel inclusion in this phase:

```toml
include = [
    { path = "oxipng/__init__.pyi", format = ["wheel"] },
    { path = "oxipng/py.typed", format = ["wheel"] },
]
```

This is not enough by itself to prevent local users from running `maturin sdist`,
but it keeps project metadata aligned with the artifact policy. CI must not run
`maturin sdist`.

## Target Matrix

| Target | Runner | Build strategy | Smoke test |
| --- | --- | --- | --- |
| Linux x86_64 manylinux_2_28 | `ubuntu-latest` | `PyO3/maturin-action@v1` | required |
| Linux aarch64 manylinux_2_28 | `ubuntu-24.04-arm` | `PyO3/maturin-action@v1` | required |
| macOS x86_64 | `macos-13` | `PyO3/maturin-action@v1` | required |
| macOS aarch64 | `macos-latest` or ARM runner | `PyO3/maturin-action@v1` | required |
| Windows x86_64 | `windows-latest` | `PyO3/maturin-action@v1` | required |

Linux aarch64 uses a native ARM runner. The workflow must smoke-test the built
wheel at runtime for that target.

## Workflow

Create `.github/workflows/wheels.yml`.

Triggers:

- `workflow_dispatch`
- `push` tags matching `v*`
- `pull_request` when packaging, workflow, Rust, Python package, or test files
  change

Permissions:

```yaml
permissions:
  contents: read
```

The workflow should:

1. Check out the repository.
2. Set up Python 3.11 for build orchestration.
3. Set up Rust 1.85.1 or the repo-pinned Rust toolchain.
4. Build wheels with maturin.
5. Upload wheel artifacts.
6. Install each built wheel into a clean virtual environment.
7. Run a smoke script against the installed wheel.

Required `maturin-action` inputs:

```yaml
uses: PyO3/maturin-action@v1
with:
  command: build
  args: --release --out dist --interpreter python3.11
  manylinux: "2_28"
  target: ${{ matrix.target }}
```

The `target` value is required for Linux and Windows jobs. It is omitted for
native macOS jobs unless the action requires an explicit value. Windows uses
`x64` or the action-supported equivalent for `win_amd64`.

Artifact names must be stable and platform-specific:

- `wheels-linux-x86_64`
- `wheels-linux-aarch64`
- `wheels-macos-x86_64`
- `wheels-macos-aarch64`
- `wheels-windows-x86_64`

The workflow must run a tag check after build:

```bash
python scripts/check_wheel_tags.py --expected-platform "$EXPECTED_PLATFORM" dist/*.whl
```

`scripts/check_wheel_tags.py` fails if no wheel is present, if any wheel has a
CPython-specific ABI tag such as `cp313-cp313`, or if the expected platform tag
for the matrix row is absent. `EXPECTED_PLATFORM` is one of:

- `manylinux_2_28_x86_64`
- `manylinux_2_28_aarch64`
- `macosx_*_x86_64`
- `macosx_*_arm64`
- `win_amd64`

## Expected Wheel Tags

The exact platform tags may vary with maturin and runner images, but the Python
ABI tag must be ABI3:

- `cp311-abi3-manylinux_2_28_x86_64`
- `cp311-abi3-manylinux_2_28_aarch64`
- `cp311-abi3-macosx_*_x86_64`
- `cp311-abi3-macosx_*_arm64`
- `cp311-abi3-win_amd64`

The workflow must fail if a generated wheel is tagged with a CPython-specific
ABI such as `cp313-cp313`.

## Smoke Test Contract

Each smoke test installs the wheel into a clean environment and runs a script
that verifies:

- `import oxipng`
- `from oxipng import PngError, optimize, optimize_from_memory`
- a generated PNG file can be optimized in place
- a generated PNG file can be optimized to an output path
- generated PNG bytes can be optimized from memory
- outputs can be opened by Pillow

The smoke script may live at `scripts/smoke_wheel.py` so both local and CI
wheel jobs use the same checks.

## Source CI Relationship

Regular `ci.yml` remains source-oriented:

- `make ci`
- lint
- typecheck
- tests
- cargo-deny
- local wheel build

`wheels.yml` is artifact-oriented and may take longer. Pull requests touching
only docs do not need to run the full wheel matrix unless they modify release or
packaging documentation that affects the workflow contract.

## Files

Expected implementation files:

- `Cargo.toml`
- `pyproject.toml`
- `Makefile`
- `.github/workflows/wheels.yml`
- `scripts/smoke_wheel.py`
- `scripts/check_wheel_tags.py`
- `tests/test_api.py`
- `docs/process/release-artifacts.md`
- `README.md`

## Acceptance Criteria

- `maturin build --release` produces ABI3 wheels locally.
- The wheel workflow builds all target wheels.
- Every required wheel is smoke-tested after build.
- The workflow uploads wheel artifacts.
- Wheel artifact names match the stable names in this spec.
- `scripts/check_wheel_tags.py` rejects CPython-specific ABI tags.
- No workflow builds or uploads an sdist.
- The generated wheels include `oxipng/__init__.pyi` and `oxipng/py.typed`.
- The package can be imported from a clean virtual environment without the repo
  on `PYTHONPATH`.

## Implementation Notes

- Linux aarch64 wheel builds use GitHub's native `ubuntu-24.04-arm` runner, so
  the wheel smoke test is gating and no QEMU exception artifact is produced.

# Build From Source

Use this guide when your platform does not have a published wheel.

Source builds compile the Rust extension on your machine. They need more tools
than a wheel install.

## Install the Required Tools

Install these tools first:

- [Python 3.10 or newer](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/)
- [Rust and Cargo](https://www.rust-lang.org/tools/install)
- `make`
- A platform C compiler and linker

Platform compiler options:

- Linux: install your distro build tools, such as `build-essential`, `gcc`, or
  `clang`.
- macOS: install [Xcode Command Line Tools](https://developer.apple.com/xcode/resources/).
- Windows: install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

Some Linux distributions package Python build headers separately. If the
build cannot find Python headers, install your distro's Python development
package. It is often named `python3-dev` or `python3-devel`.

The build backend is [maturin](https://www.maturin.rs/).

## Build From an sdist

Use this path to build from the published release source instead of a Git
checkout. A released source distribution, or sdist, includes the source
needed to build a wheel locally.

```bash
python -m pip download --no-binary oxipng-pybind oxipng-pybind
python -m pip wheel --no-binary oxipng-pybind oxipng-pybind-*.tar.gz
python -m pip install oxipng_pybind-*.whl
```

`pip install --no-binary oxipng-pybind oxipng-pybind` also builds from the
sdist in one step.

## Build From a Checkout

From a source checkout:

```bash
make wheel
```

`make wheel` uses the locked maturin version through `uv`.

The wheel is written to `target/wheels/`.

Install that wheel with pip:

```bash
python -m pip install target/wheels/oxipng_pybind-*.whl
```

## Build a Pure Source Tree

Use a pure source tree when you need to confirm that generated files are not
required before packaging.

```bash
git clean -xfd target dist
make wheel
```

Do not run this in a checkout with uncommitted generated files you want to keep.

For released wheel and source distribution policy, see
[Release Artifacts](../process/release-artifacts.md).

## Troubleshooting Source Builds

Source builds are slower than wheel installs.

If the build fails, check that these commands are on `PATH`:

- `rustc`
- `cargo`
- `python`
- `uv`
- `make`
- your compiler

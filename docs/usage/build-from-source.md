# Build From Source

Use this guide when your platform does not have a published wheel, or when you
need to build a local wheel from a source checkout.

Source builds compile the Rust extension on your machine.

They need more tools than a wheel install.

## Required Tools

Install these before building from a source checkout:

- [Python 3.11 or newer](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/)
- [Rust and Cargo](https://www.rust-lang.org/tools/install)
- `make`
- A platform C compiler and linker

Platform compiler options:

- Linux: install your distro build tools, such as `build-essential`, `gcc`, or
  `clang`.
- macOS: install [Xcode Command Line Tools](https://developer.apple.com/xcode/resources/).
- Windows: install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

Some Linux distributions package Python build headers separately.

If the build cannot find Python headers, install your distro's Python
development package. It is often named `python3-dev` or `python3-devel`.

The build backend is [maturin](https://www.maturin.rs/).

`make wheel` runs the maturin version from the project dependency lockfile.

## Build a Local Wheel

From a source checkout:

```bash
make wheel
```

The wheel is written to `target/wheels/`.

Install that wheel with pip:

```bash
python -m pip install target/wheels/oxipng_pybind-*.whl
```

Current releases are wheel-only. Source distributions are deferred until
source-install behavior is tested.

## Notes

Source builds are slower than wheel installs.

If the build fails, check that these commands are on `PATH`:

- `rustc`
- `cargo`
- `python`
- `uv`
- `make`
- your compiler

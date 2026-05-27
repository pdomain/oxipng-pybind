# oxipng-pybind

`oxipng-pybind` optimizes PNG files and bytes from Python.

It wraps Rust `oxipng` and imports as `oxipng`. It is built to replace
`pyoxipng` while adding a stable API for new code.

## Install

The package name is `oxipng-pybind`. The import module is `oxipng`.

Install the supported PyPI wheel on Python 3.11 or newer:

```bash
python -m pip install oxipng-pybind
```

For unsupported platforms, build a local wheel from source:

```bash
make wheel
```

Published wheels use the `cp311-abi3` tag. One wheel per platform supports
CPython 3.11 and newer, including 3.12, 3.13, and 3.14.

## Main API

The main entry points are:

- [`optimize`](docs/usage/file-optimization.md) reads and writes PNG files.
- [`optimize_from_memory`](docs/usage/memory-optimization.md) reads PNG bytes
  and returns optimized bytes.
- [`RawImage`](docs/usage/raw-image.md) builds optimized PNG bytes from packed
  pixel data.
- `analyze` reports original and optimized sizes. It does not write output.

PNG decode and optimization failures raise `PngError`.

Caller mistakes raise normal Python exceptions. These include `TypeError`,
`ValueError`, `FileNotFoundError`, and `OSError`.

stdin and stdout are caller-owned. Use `optimize_from_memory` for byte streams.

For attacker-controlled files or bytes, see
[Untrusted Input](docs/usage/untrusted-input.md).

## pyoxipng Compatibility

This package can replace `pyoxipng` for most callers.

Old `pyoxipng` names are compatibility paths. They still work for now, but some
emit `DeprecationWarning`. Some old shapes also do not match Rust `oxipng`
option contracts. [Migrate those names](docs/usage/pyoxipng-migration.md) to
the stable `oxipng-pybind` API before a future release removes them.

In this project, "upstream" means the Rust `oxipng` optimizer that this package
wraps. This API maps supported Rust `oxipng` options to Python types.

## Contributing

See [Contributing](CONTRIBUTING.md) for setup, checks, and release rules.

## Supported Platforms

Wheels use Python 3.11 ABI3. That means each platform wheel supports
CPython 3.11 and newer.

Platform wheels cover:

- Linux x86_64
- Linux aarch64
- macOS x86_64
- macOS arm64
- Windows x86_64

If your platform is not listed, see
[Build from Source](docs/usage/build-from-source.md).

## More Docs

Start with [the docs index](docs/README.md).

Useful pages:

- [Untrusted input](docs/usage/untrusted-input.md)
- [API compatibility](docs/architecture/api-compatibility.md)
- [Dependency health](docs/process/dependency-health.md)
- [Release artifacts](docs/process/release-artifacts.md)
- [Upstream bumps](docs/process/upstream-bumps.md)

## License

This wrapper is released under the Unlicense. See `LICENSE`.

Upstream `oxipng` is MIT licensed. See `THIRD_PARTY_NOTICES.md`.

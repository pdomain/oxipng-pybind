# oxipng-pybind

`oxipng-pybind` optimizes PNG files and bytes from Python.

It wraps Rust [`oxipng`](https://github.com/oxipng/oxipng) and imports as `oxipng`.

It can replace `pyoxipng` and provides a stable API for new code.

## Install

The package name is `oxipng-pybind`. The import module is `oxipng`.

Install the supported PyPI wheel on Python 3.10 or newer:

```bash
python -m pip install oxipng-pybind
```

If your platform does not have a wheel, see
[Build From Source](docs/usage/build-from-source.md).

## Main API

The main entry points are:

- [`optimize`](docs/usage/file-optimization.md) reads and writes PNG files.
- [`optimize_from_memory`](docs/usage/memory-optimization.md) reads PNG bytes
  and returns optimized bytes.
- [`RawImage`](docs/usage/raw-image.md) builds optimized PNG bytes from packed
  pixel data.
- `analyze` reports original and optimized sizes. It does not write output.

PNG decode and optimization failures raise `PngError`.

Caller mistakes raise normal Python exceptions.

stdin and stdout are caller-owned. Use `optimize_from_memory` for byte streams.

For attacker-controlled files or bytes, see
[Untrusted Input](docs/usage/untrusted-input.md).

## pyoxipng Compatibility

This package can replace `pyoxipng` for most callers.

Old `pyoxipng` names are compatibility paths. Some emit `DeprecationWarning`.
[Migrate those names](docs/usage/pyoxipng-migration.md) to the stable API
before a future release removes them.

In this project, "upstream" means the Rust `oxipng` optimizer that this package
wraps.

This API maps supported Rust `oxipng` options to Python types.

## Contributing

See [Contributing](CONTRIBUTING.md) for setup, checks, and release rules.

## Supported Platforms

Published wheels use Python 3.10 and 3.11 ABI3 lanes to support CPython 3.10
or newer on:

- Linux x86_64
- Linux aarch64
- macOS x86_64
- macOS arm64
- Windows x86_64

For wheel policy, see [Release Artifacts](docs/process/release-artifacts.md).

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

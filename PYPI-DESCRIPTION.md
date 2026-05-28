# oxipng-pybind

`oxipng-pybind` is a Python wrapper for [`oxipng`](https://github.com/oxipng/oxipng). It optimizes PNG files and
raw bytes.

Install it with:

```bash
python -m pip install oxipng-pybind
```

If no wheel is available for your platform, see
[`Build from source`](https://github.com/pdomain/oxipng-pybind/blob/main/docs/usage/build-from-source.md).

## Main API

- [`optimize`](https://github.com/pdomain/oxipng-pybind/blob/main/docs/usage/file-optimization.md)
  reads and writes PNG files.
- [`optimize_from_memory`](https://github.com/pdomain/oxipng-pybind/blob/main/docs/usage/memory-optimization.md)
  reads and writes PNG bytes.
- [`RawImage`](https://github.com/pdomain/oxipng-pybind/blob/main/docs/usage/raw-image.md)
  builds PNG bytes from packed pixel data.
- `analyze` reports size and option details.

Error handling:

- Image decode and optimization failures raise `PngError`.
- Caller mistakes raise normal Python exceptions.

This project can replace `pyoxipng` for most use cases.

It tracks upstream Rust `oxipng` version updates.

## Links

- [Project home](https://github.com/pdomain/oxipng-pybind)
- [Upstream `oxipng` (Rust)](https://github.com/oxipng/oxipng)
- [Contribution guide](https://github.com/pdomain/oxipng-pybind/blob/main/CONTRIBUTING.md)
- [Untrusted input guidance](https://github.com/pdomain/oxipng-pybind/blob/main/docs/usage/untrusted-input.md)

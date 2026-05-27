# Optimize PNG Files

Use `optimize` when the PNG is on disk.

## Basic Use

Write the optimized PNG to a new path:

```python
from oxipng import optimize

optimize(input="cover.png", output="cover.optimized.png", strip="safe")
```

`input` and `output` may be
[`str`](https://docs.python.org/3/library/stdtypes.html#str),
[`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes), or
[`os.PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) values.

If `output` is omitted, `optimize` writes back to the input file.

For files from untrusted users, see
[Handle Untrusted Input](untrusted-input.md).

## Analyze Without Writing

Use [`analyze`](../../oxipng/__init__.pyi#L211) to check sizes without writing a
file:

```python
from oxipng import analyze

result = analyze(input="cover.png", strip="safe")
print(result.original_size, result.optimized_size)
```

`analyze` returns an
[`OptimizationResult`](../../oxipng/__init__.pyi#L118).

The result has `original_size` and `optimized_size` values in bytes.

## Options

`level` must be an integer from `0` through `6`.

Use `backup=True` when an in-place write should keep the original file. The
backup path is the input path plus `.bak`. If that backup file already exists,
`optimize` raises `FileExistsError`. It does not replace the existing backup
file.

```python
from oxipng import optimize

optimize(input="cover.png", backup=True, force=True)
```

Use `preserve_attrs=True` to copy output permissions and modification time from
the input file. This depends on operating system support.

```python
from oxipng import optimize

optimize(input="cover.png", output="out.png", preserve_attrs=True)
```

Most optimization options map to Rust
[`oxipng::Options`](https://docs.rs/oxipng/latest/oxipng/struct.Options.html).

This package uses Python names and Python value types for those options.
See [Options Surface](../architecture/options-surface.md) for the Python
mapping.

Enum-like options accept enum members or string aliases.

`backup` and `preserve_attrs` are only valid for `optimize`. These options are
rejected by:

- `analyze`
- `optimize_from_memory`
- `RawImage.create_optimized_png`

stdin and stdout optimization are caller-owned. Use `optimize_from_memory`
after reading bytes.

## Errors

Caller errors raise
[`TypeError`](https://docs.python.org/3/library/exceptions.html#TypeError) or
[`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError).

PNG decode and optimization errors raise `PngError`.

File I/O problems may raise
[`FileNotFoundError`](https://docs.python.org/3/library/exceptions.html#FileNotFoundError),
[`FileExistsError`](https://docs.python.org/3/library/exceptions.html#FileExistsError),
or [`OSError`](https://docs.python.org/3/library/exceptions.html#OSError).

```python
from oxipng import PngError, optimize

try:
    optimize(input="possibly-corrupt.png", fix_errors=False)
except PngError:
    print("not an optimizable PNG")
```

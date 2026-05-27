# Optimize PNG files

Use [`optimize`](../../oxipng/__init__.pyi#L204) when the PNG is on disk.

## Basic use

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

## Analyze without writing

Use [`analyze`](../../oxipng/__init__.pyi#L234) to check sizes without writing a
file:

```python
from oxipng import analyze

result = analyze(input="cover.png", strip="safe")
print(result.original_size, result.optimized_size)
```

`analyze` returns an
[`OptimizationResult`](../../oxipng/__init__.pyi#L140).
Its `original_size` and `optimized_size` values are byte counts.

## Options

`level` must be an integer from `0` through `6`.

Most optimization options map to Rust
[`oxipng::Options`](https://docs.rs/oxipng/10.1.1/oxipng/struct.Options.html).
See [Options Surface](../architecture/options-surface.md) for the Python names
and value types.

Use `backup=True` when an in-place write should keep the original file. This
requires `output` to be omitted. The backup path is the input path plus `.bak`.
If that backup file already exists, `optimize` raises `FileExistsError`. It does
not replace the existing backup file.

```python
from oxipng import optimize

optimize(input="cover.png", backup=True, force=True)
```

Use `preserve_attrs=True` to copy the input file permissions and modification
time to the output file. This depends on operating system support.

```python
from oxipng import optimize

optimize(input="cover.png", output="out.png", preserve_attrs=True)
```

`backup` and `preserve_attrs` are valid only for `optimize`. Other APIs reject
them.

stdin and stdout optimization are caller-owned. See
[Optimize PNG data in memory](memory-optimization.md#stdin-and-stdout).

## Errors

Caller errors raise `TypeError` or `ValueError`. File I/O errors use normal
Python file exceptions. PNG decode and optimization errors raise `PngError`.

See [Error Mapping](../architecture/overview.md#error-mapping) for the full
mapping.

```python
from oxipng import PngError, optimize

try:
    optimize(input="possibly-corrupt.png", fix_errors=False)
except PngError:
    print("not an optimizable PNG")
```

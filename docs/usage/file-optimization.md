# Optimize PNG Files

Use `optimize` when a PNG is stored on disk.

## Basic Use

Optimize a file in place:

```python
from pathlib import Path

from oxipng import optimize

path = Path("cover.png")
optimize(path, level=6)
```

Write the optimized PNG to a new path:

```python
from oxipng import optimize

optimize("cover.png", "cover.optimized.png", strip="safe")
```

`input` and `output` may be strings, bytes paths, or `os.PathLike` values. If
`output` is omitted, `optimize` writes back to the input file.

Use `analyze` to check sizes without writing a file:

```python
from oxipng import analyze

result = analyze("cover.png", strip="safe")
print(result.original_size, result.optimized_size)
```

`analyze` returns an `OptimizationResult`. It has `original_size` and
`optimized_size` values in bytes.

## Options

`level` must be an integer from `0` through `6`.

Use `backup=True` for in-place optimization when the original file should be
copied first. The backup path is the input path plus `.bak`. Existing backup
files are never overwritten.

```python
from oxipng import optimize

optimize("cover.png", backup=True, force=True)
```

Use `preserve_attrs=True` to copy output permissions and modification time from
the input file where the operating system allows it.

```python
from oxipng import optimize

optimize("cover.png", "out.png", preserve_attrs=True)
```

Enum-like options accept enum members or string aliases. Common options include
`interlace`, `strip`, `deflate`, `filter`, `fix_errors`, and `force`.

Advanced options include `optimize_alpha`, `bit_depth_reduction`,
`color_type_reduction`, `palette_reduction`, `grayscale_reduction`,
`idat_recoding`, `scale_16`, `fast_evaluation`, `timeout`, and
`max_decompressed_size`.

`backup` and `preserve_attrs` are only valid for `optimize`. `analyze`,
`optimize_from_memory`, and `RawImage.create_optimized_png` reject them.

stdin and stdout optimization are not part of this API. Callers must decide
when to read from stdin and when to write to stdout. Use `optimize_from_memory`
after reading bytes.

## Errors

Caller errors raise `TypeError` or `ValueError`. PNG decode and optimization
errors raise `PngError`. Backup file problems may raise `FileExistsError` or
`OSError`.

```python
from oxipng import PngError, optimize

try:
    optimize("possibly-corrupt.png", fix_errors=False)
except PngError:
    print("not an optimizable PNG")
```

The distribution is named `oxipng-pybind`, but the import module is `oxipng`.

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

stdin/stdout optimization is unsupported.

## Errors

Caller errors raise `TypeError` or `ValueError`. PNG decode and optimization
errors raise `PngError`.

```python
from oxipng import PngError, optimize

try:
    optimize("possibly-corrupt.png", fix_errors=False)
except PngError:
    print("not an optimizable PNG")
```

The distribution is named `oxipng-pybind`, but the import module is `oxipng`.

# File Optimization Usage

Use `optimize` from the `oxipng` module for file-based PNG optimization.

```python
from pathlib import Path

from oxipng import optimize

path = Path("cover.png")
optimize(path, level=6)
```

Write to a separate output path by passing the second positional argument:

```python
optimize("cover.png", "cover.optimized.png", strip="safe")
```

For in-place optimization, `backup=True` first copies `cover.png` to
`cover.png.bak`. Existing backup files are never overwritten.

```python
optimize("cover.png", backup=True, force=True)
```

Use `preserve_attrs=True` when output permissions and modification time should
be copied from the input file where the operating system allows it.

```python
optimize("cover.png", "out.png", preserve_attrs=True)
```

Caller errors use `TypeError` or `ValueError`. PNG decoding and optimization
errors raise `PngError`.

```python
from oxipng import PngError

try:
    optimize("possibly-corrupt.png", fix_errors=False)
except PngError:
    print("not an optimizable PNG")
```

The distribution is named `oxipng-pybind`, but the import module remains
`oxipng`.

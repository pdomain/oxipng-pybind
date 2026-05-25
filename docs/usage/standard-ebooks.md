# Standard Ebooks Usage

Standard Ebooks currently imports `optimize` from the `oxipng` module and calls
it with `level=6`.

```python
from pathlib import Path

from oxipng import optimize

path = Path("cover.png")
optimize(path, level=6)
```

This package supports that API directly. It does not require Standard Ebooks to
change the import from `oxipng` to `se_pyoxipng`.

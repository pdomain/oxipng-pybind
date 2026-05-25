# File Optimization Usage

Use `optimize` from the `oxipng` module for file-based PNG optimization.

```python
from pathlib import Path

from oxipng import optimize

path = Path("cover.png")
optimize(path, level=6)
```

The distribution is named `oxipng-pybind`, but the import module remains
`oxipng`.

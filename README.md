# se-pyoxipng

`se-pyoxipng` is a focused Python wrapper around the Rust `oxipng` library.

The distribution is named `se-pyoxipng`, but the import module is `oxipng`.
The supported API is intentionally narrow:

```python
from oxipng import optimize

optimize(path, level=6)
```

# Memory Optimization Usage

Use `optimize_from_memory` when PNG data is already loaded in Python.

```python
from oxipng import optimize_from_memory

optimized = optimize_from_memory(png_bytes, level=4, strip="safe")
```

The input may be `bytes`, `bytearray`, or `memoryview`. The return value is
always `bytes`.

```python
optimized = optimize_from_memory(bytearray(png_bytes))
optimized = optimize_from_memory(memoryview(png_bytes))
```

Invalid PNG data raises `PngError`.

```python
from oxipng import PngError

try:
    optimize_from_memory(b"not a png")
except PngError:
    print("not an optimizable PNG")
```

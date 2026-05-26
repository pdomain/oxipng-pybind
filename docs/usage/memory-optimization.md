# Optimize PNG Data in Memory

Use `optimize_from_memory` when PNG data is already loaded in Python.

## Basic Use

Read PNG bytes, optimize them, and write the result:

```python
from pathlib import Path

from oxipng import optimize_from_memory

png_bytes = Path("cover.png").read_bytes()
optimized = optimize_from_memory(png_bytes, level=4, strip="safe")
Path("cover.optimized.png").write_bytes(optimized)
```

The return value is always `bytes`.

## Options

The input may be `bytes`, `bytearray`, or `memoryview`.

```python
from pathlib import Path

from oxipng import optimize_from_memory

png_bytes = Path("cover.png").read_bytes()
optimized_from_bytearray = optimize_from_memory(bytearray(png_bytes))
optimized_from_view = optimize_from_memory(memoryview(png_bytes))
```

`level` must be an integer from `0` through `6`. Enum-like options accept enum
members or string aliases. Common options include `interlace`, `strip`,
`deflate`, `filter`, `fix_errors`, and `force`.

Advanced options include `optimize_alpha`, `bit_depth_reduction`,
`color_type_reduction`, `palette_reduction`, `grayscale_reduction`,
`idat_recoding`, `scale_16`, `fast_evaluation`, `timeout`, and
`max_decompressed_size`.

`backup` and `preserve_attrs` are file-only options. `optimize_from_memory`
rejects them.

stdin and stdout optimization are not part of this API. Callers must decide
when to read from stdin and when to write to stdout:

```python
import sys

from oxipng import optimize_from_memory

data = sys.stdin.buffer.read()
optimized = optimize_from_memory(data)
sys.stdout.buffer.write(optimized)
```

## Errors

Caller errors raise `TypeError` or `ValueError`. Invalid PNG data raises
`PngError`.

```python
from oxipng import PngError, optimize_from_memory

try:
    optimize_from_memory(b"not a png")
except PngError:
    print("not an optimizable PNG")
```

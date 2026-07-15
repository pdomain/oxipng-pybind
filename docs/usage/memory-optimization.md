# Optimize PNG data in memory

Use [`optimize_from_memory`](../../oxipng/__init__.pyi#L261) when PNG data is
already in Python memory.

## Optimize bytes in three steps

Read PNG bytes, optimize them, and write the result.

```python
from pathlib import Path

from oxipng import optimize_from_memory

png_bytes = Path("cover.png").read_bytes()
optimized = optimize_from_memory(data=png_bytes, level=4, strip="safe")
Path("cover.optimized.png").write_bytes(optimized)
```

The return value is
[`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes).

## Accepted input types

`data` accepts these byte values:

- `bytes`
- [`bytearray`](https://docs.python.org/3/library/stdtypes.html#bytearray)
- byte-oriented
  [`memoryview`](https://docs.python.org/3/library/stdtypes.html#memoryview)

```python
from pathlib import Path

from oxipng import optimize_from_memory

png_bytes = Path("cover.png").read_bytes()
optimized_from_bytearray = optimize_from_memory(data=bytearray(png_bytes))
optimized_from_view = optimize_from_memory(data=memoryview(png_bytes))
```

## Configure common options

Common options include `level`, `strip`, `timeout`, and
`max_decompressed_size`.

See [Options Surface](../architecture/options-surface.md) for all Python names,
value types, and file-only options.

## Untrusted input

For bytes from untrusted users, see
[Handle Untrusted Input](untrusted-input.md).

## stdin and stdout

stdin and stdout are caller-owned. Read bytes first. Then call
`optimize_from_memory`.

```python
import sys

from oxipng import optimize_from_memory

data = sys.stdin.buffer.read()
optimized = optimize_from_memory(data=data)
sys.stdout.buffer.write(optimized)
```

## Errors raised on bad input

Caller errors raise `TypeError` or `ValueError`. Invalid PNG data raises
`PngError`. See [Error Mapping](../architecture/overview.md#error-mapping) for
the full mapping.

```python
from oxipng import PngError, optimize_from_memory

try:
    optimize_from_memory(data=b"not a png")
except PngError:
    print("not an optimizable PNG")
```

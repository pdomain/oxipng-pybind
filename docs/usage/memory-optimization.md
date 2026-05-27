# Optimize PNG data in memory

Use [`optimize_from_memory`](../../oxipng/__init__.pyi#L260) when PNG data is
already loaded in Python.

## Basic use

Read PNG bytes, optimize them, and write the result:

```python
from pathlib import Path

from oxipng import optimize_from_memory

png_bytes = Path("cover.png").read_bytes()
optimized = optimize_from_memory(data=png_bytes, level=4, strip="safe")
Path("cover.optimized.png").write_bytes(optimized)
```

The return value is always
[`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes).

## Inputs

`data` may be:

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

## Options

`level` must be an integer from `0` through `6`.

See [Options Surface](../architecture/options-surface.md) for the Python names
and value types.

Enum-like options accept enum members or documented aliases.

`backup` and `preserve_attrs` are file-only options. `optimize_from_memory`
rejects them.

## Untrusted input

For bytes from untrusted users, see
[Handle Untrusted Input](untrusted-input.md).

## stdin and stdout

stdin and stdout optimization are caller-owned. Read bytes first. Then call
`optimize_from_memory`:

```python
import sys

from oxipng import optimize_from_memory

data = sys.stdin.buffer.read()
optimized = optimize_from_memory(data=data)
sys.stdout.buffer.write(optimized)
```

## Errors

Caller errors raise `TypeError` or `ValueError`. Invalid PNG data raises
`PngError`.

```python
from oxipng import PngError, optimize_from_memory

try:
    optimize_from_memory(data=b"not a png")
except PngError:
    print("not an optimizable PNG")
```

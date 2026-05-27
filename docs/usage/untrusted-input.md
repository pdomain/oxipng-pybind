# Handle Untrusted Input

PNG optimization can use a lot of CPU and memory. Treat user uploads, queues,
and other attacker-controlled sources as untrusted input.

## Use Limits

Set both a timeout and a decompressed-size limit:

```python
from oxipng import optimize_from_memory

optimized = optimize_from_memory(
    data=data,
    timeout=2.0,
    max_decompressed_size=50_000_000,
)
```

`timeout` limits optimizer work.

`max_decompressed_size` rejects PNGs whose decompressed IDAT data exceeds the
configured byte count. It defaults to `None`.

Set a separate upload or read limit before loading bytes. The memory API
receives bytes after Python has already read them.

## File Uploads

Use the same limits for files:

```python
from oxipng import optimize

optimize(input="upload.png", timeout=2.0, max_decompressed_size=50_000_000)
```

## Request-Time Work

Use conservative compression settings during web requests or other
latency-sensitive work. Use `fix_errors` or `force` only when the caller
accepts the extra work.

## Byte Streams

For stdin and stdout, use the memory API and enforce a read limit before
optimization:

```python
import sys

from oxipng import optimize_from_memory

limit = 50_000_000
data = sys.stdin.buffer.read(limit + 1)
if len(data) > limit:
    raise ValueError("input is too large")

optimized = optimize_from_memory(
    data=data,
    timeout=2.0,
    max_decompressed_size=limit,
)
sys.stdout.buffer.write(optimized)
```

See [Optimize PNG data in memory](memory-optimization.md#stdin-and-stdout) for
the basic stream pattern. See
[Options Surface](../architecture/options-surface.md) for supported option
names and value types.

# Handle Untrusted Input

PNG optimization can use a lot of CPU and memory.

This matters when files or bytes come from users, uploads, queues, or other
untrusted sources.

## Use Limits

Pass explicit limits for untrusted input:

```python
from oxipng import optimize_from_memory

optimized = optimize_from_memory(
    data=data,
    timeout=2.0,
    max_decompressed_size=50_000_000,
)
```

`timeout` sets an optimization timeout. Upstream `oxipng` skips further
optimization work after the timeout expires.

`max_decompressed_size` rejects inputs whose decompressed IDAT data would
exceed the configured byte count.

Set a separate upload or read limit before loading untrusted bytes. The memory
API receives bytes after Python has already read them.

Default options follow Rust
[`oxipng::Options`](https://docs.rs/oxipng/10.1.1/oxipng/struct.Options.html)
behavior. They do not set a decompression size limit.

## File Uploads

Use the same limits for files from untrusted users:

```python
from oxipng import optimize

optimize(input="upload.png", timeout=2.0, max_decompressed_size=50_000_000)
```

## Request-Time Work

Use conservative compression settings during web requests or other
latency-sensitive work.

Use `fix_errors` or `force` only when the caller accepts the extra work.

## Byte Streams

stdin and stdout are caller-owned.

Read bytes first. Then call `optimize_from_memory`:

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

# Handle Untrusted Input

PNG optimization can use a lot of CPU and memory.

This matters when files or bytes come from users, uploads, queues, or other
untrusted sources.

## Use Limits

Pass explicit limits for untrusted input:

```python
from oxipng import optimize_from_memory

optimized = optimize_from_memory(data=data, timeout=2.0, max_decompressed_size=50_000_000)
```

`timeout` limits optimization time.

`max_decompressed_size` rejects inputs whose inflated image data would exceed
the configured byte count.

Default options follow Rust
[`oxipng::Options`](https://docs.rs/oxipng/latest/oxipng/struct.Options.html)
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

data = sys.stdin.buffer.read()
optimized = optimize_from_memory(data=data, timeout=2.0, max_decompressed_size=50_000_000)
sys.stdout.buffer.write(optimized)
```

# Untrusted Input

PNG optimization can spend CPU and memory while decoding and recompressing
images. When processing attacker-controlled files or bytes, pass explicit
resource limits:

```python
from oxipng import optimize_from_memory

optimized = optimize_from_memory(
    data,
    timeout=2.0,
    max_decompressed_size=50_000_000,
)
```

The default options preserve upstream `oxipng` behavior and do not impose a
decompression cap. Use conservative compression settings for request-time
workloads, and enable `fix_errors` or `force` only when the caller accepts the
additional processing.

## File Paths

File APIs read and write ordinary filesystem paths. They are not a sandbox and
do not harden caller-controlled paths against symlinks, path races, or
time-of-check/time-of-use changes.

Services that optimize untrusted uploads should use private work directories
owned by the service account. Generate input, output, and temporary filenames
on the server side. Do not let request data choose output paths or backup paths
for untrusted files.

For untrusted bytes, prefer `optimize_from_memory` when the service does not
need file attributes or in-place replacement.

# API, Options, and Memory Optimization Design

## Summary

Expand `oxipng-pybind` from a file-only wrapper into a small, explicit Python
API over upstream `oxipng` 10.1.1. This phase adds `optimize_from_memory()`,
typed option helper enums, and a documented subset of upstream options that can
be mapped directly to `oxipng::Options`.

This spec is based on upstream `oxipng` tag `v10.1.1` at commit `628e241e`.
The local upstream checkout used for analysis lives under the ignored path
`.cache/upstream/oxipng`.

## Goals

- Keep the public import module as `oxipng`.
- Preserve the current file API for `optimize(input, output=None, *, level=2)`.
- Add in-memory optimization with `optimize_from_memory(data, *, ...) -> bytes`.
- Support a conservative option set that maps cleanly to upstream `Options`.
- Accept both strings and typed enum values for enum-like options.
- Keep unsupported upstream options intentionally unexposed and documented.
- Release the GIL while executing upstream optimization calls.
- Keep Python exceptions predictable: caller errors use `TypeError` or
  `ValueError`; PNG processing failures use `PngError`.

## Non-Goals

- No `RawImage` support.
- No stdin/stdout API.
- No dry-run API.
- No multi-file or directory API.
- No global thread-pool configuration.
- No Zopfli tuning knobs beyond selecting the upstream default Zopfli deflater.
- No automatic parity with every `oxipng` CLI flag.

## Public API

```python
from oxipng import Deflater, FilterStrategy, Interlacing, PngError, StripChunks
from oxipng import optimize, optimize_from_memory
```

```python
def optimize(
    input,
    output=None,
    *,
    level=2,
    interlace=None,
    strip=None,
    deflate=None,
    filter=None,
    fix_errors=False,
    force=False,
    backup=False,
    preserve_attrs=False,
) -> None: ...
```

```python
def optimize_from_memory(
    data,
    *,
    level=2,
    interlace=None,
    strip=None,
    deflate=None,
    filter=None,
    fix_errors=False,
    force=False,
) -> bytes: ...
```

`optimize()` accepts `str`, `bytes`, and `os.PathLike` paths. When `output` is
`None`, upstream receives `OutFile::Path { path: None, preserve_attrs }` and the
input file is optimized in place.

`optimize_from_memory()` accepts `bytes`, `bytearray`, and `memoryview` PNG data.
It returns optimized PNG bytes from upstream `oxipng::optimize_from_memory`.

Unsupported keyword names raise `TypeError`. Recognized options with invalid
values raise `ValueError` with allowed values where practical.

## Option Contract

Options are parsed by starting from `oxi::Options::from_preset(level)` and then
applying explicit overrides.

| Python option | Upstream mapping | Supported values |
| --- | --- | --- |
| `level` | `Options::from_preset(level)` | integer `0` through `6` |
| `interlace` | `Options.interlace` | `None`, `Interlacing.keep`, `Interlacing.off`, `Interlacing.on`, `"keep"`, `"off"`, `"on"`, `"0"`, `"1"` |
| `strip` | `Options.strip` | `None`, `StripChunks.none`, `StripChunks.safe`, `StripChunks.all`, `"none"`, `"safe"`, `"all"` |
| `deflate` | `Options.deflater` | `None`, `Deflater.libdeflater`, `Deflater.zopfli`, `"libdeflater"`, `"zopfli"` |
| `filter` | `Options.filters` | `None`, a single filter strategy, or a sequence of filter strategies |
| `fix_errors` | `Options.fix_errors` | `bool` |
| `force` | `Options.force` | `bool` |
| `backup` | wrapper-controlled backup before in-place writes | `bool`, file API only |
| `preserve_attrs` | `OutFile::Path.preserve_attrs` | `bool`, file API only |

`backup=True` is only valid when `optimize()` writes in place. Passing
`backup=True` with an explicit `output` path raises `ValueError`.

Backup behavior:

- The backup path is `<input>.bak`, where `.bak` is appended to the full input
  path string.
- If the backup path already exists, `optimize()` raises `FileExistsError`
  before calling upstream `oxipng`.
- The backup copy is created before the upstream optimization call.
- If the backup copy fails, optimization is not attempted.
- If upstream optimization fails, the input file is left in whatever state
  upstream left it, and the backup remains for caller-managed recovery.
- Backup files preserve file contents only; timestamp and permission
  preservation is controlled separately by `preserve_attrs`.

`preserve_attrs=True` applies to file output only. It is valid with in-place and
explicit output path writes. It is not accepted by `optimize_from_memory()`.

## Enums and Values

Use Python `enum.Enum` values. Public member names are lower-case to support
the documented examples and simple autocomplete.

### `Interlacing`

| Member | String aliases | Upstream value |
| --- | --- | --- |
| `Interlacing.keep` | `"keep"` | `None` |
| `Interlacing.off` | `"off"`, `"0"` | `Some(false)` |
| `Interlacing.on` | `"on"`, `"1"` | `Some(true)` |

If `interlace=None`, the preset value is left unchanged. For the default preset,
that means upstream default `Some(false)`, so existing interlacing is removed
unless the caller passes `interlace="keep"` or `Interlacing.keep`.

### `StripChunks`

| Member | String aliases | Upstream value |
| --- | --- | --- |
| `StripChunks.none` | `"none"` | `StripChunks::None` |
| `StripChunks.safe` | `"safe"` | `StripChunks::Safe` |
| `StripChunks.all` | `"all"` | `StripChunks::All` |

The upstream `Strip` and `Keep` variants are intentionally not exposed in this
phase because they require chunk-name parsing and stronger validation policy.

### `Deflater`

| Member | String aliases | Upstream value |
| --- | --- | --- |
| `Deflater.libdeflater` | `"libdeflater"` | `Deflater::Libdeflater` |
| `Deflater.zopfli` | `"zopfli"` | `Deflater::Zopfli(Default::default())` |

`Deflater.libdeflater` keeps the compression level chosen by the preset unless
a future API adds an explicit compression-level option. `Deflater.zopfli` uses
upstream `ZopfliOptions::default()`.

### `FilterStrategy`

Expose upstream filter choices under `FilterStrategy`. The enum includes both
basic PNG row filters and upstream heuristic strategies because upstream stores
both in `Options.filters`.

| Member | String aliases | Upstream value |
| --- | --- | --- |
| `FilterStrategy.none` | `"none"`, `"0"` | `FilterStrategy::Basic(RowFilter::None)` |
| `FilterStrategy.sub` | `"sub"`, `"1"` | `FilterStrategy::Basic(RowFilter::Sub)` |
| `FilterStrategy.up` | `"up"`, `"2"` | `FilterStrategy::Basic(RowFilter::Up)` |
| `FilterStrategy.average` | `"average"`, `"3"` | `FilterStrategy::Basic(RowFilter::Average)` |
| `FilterStrategy.paeth` | `"paeth"`, `"4"` | `FilterStrategy::Basic(RowFilter::Paeth)` |
| `FilterStrategy.minsum` | `"minsum"`, `"5"` | `FilterStrategy::MinSum` |
| `FilterStrategy.entropy` | `"entropy"`, `"6"` | `FilterStrategy::Entropy` |
| `FilterStrategy.bigrams` | `"bigrams"`, `"7"` | `FilterStrategy::Bigrams` |
| `FilterStrategy.bigent` | `"bigent"`, `"8"` | `FilterStrategy::BigEnt` |
| `FilterStrategy.brute` | `"brute"`, `"9"` | `FilterStrategy::Brute { num_lines: 3, level: 1 }` |

`filter=None` leaves the preset filter set unchanged. A single string or enum
sets `Options.filters` to exactly one strategy. A non-empty sequence sets
`Options.filters` to the ordered unique strategies in the sequence. Empty
sequences raise `ValueError`.

## pyoxipng Compatibility Contract

This phase provides practical compatibility only for code that imports
`optimize` and passes paths plus basic keyword options. It does not claim full
`pyoxipng` parity.

Supported compatibility surface:

- `from oxipng import optimize`
- `optimize(path)`
- `optimize(path, output)`
- `optimize(path, level=...)`
- enum-like string options for common CLI-style values

Intentionally unsupported:

- `RawImage`
- APIs that expose raw pixel buffers
- arbitrary chunk keep/strip lists
- stdin/stdout behavior
- every upstream `Options` field

## Rust/Python Boundary

Keep `src/lib.rs` organized around a small option parsing layer:

- `parse_options(kwargs, mode) -> ParsedOptions`
- `parse_level(value) -> u8`
- `parse_interlace(value) -> Option<bool>`
- `parse_strip(value) -> oxi::StripChunks`
- `parse_deflater(value, preset_deflater) -> oxi::Deflater`
- `parse_filters(value) -> IndexSet<oxi::FilterStrategy>`

Define public enums in Python in `oxipng/__init__.py` using `enum.Enum`. Rust
parsing must accept their stable `.value` strings rather than relying on object
identity.

Optimization calls must copy or extract all Python-owned data before entering
`py.allow_threads(...)`.

## Files

Expected implementation files:

- `src/lib.rs`
- `Cargo.toml`
- `oxipng/__init__.py`
- `oxipng/__init__.pyi`
- `tests/test_api.py`
- `tests/conftest.py`
- `README.md`
- `docs/usage/file-optimization.md`
- `docs/usage/memory-optimization.md`
- `docs/architecture/api-compatibility.md`
- `docs/architecture/options-surface.md`

## Acceptance Criteria

- `optimize_from_memory()` is importable and returns readable PNG bytes.
- `optimize()` keeps the current supported behavior.
- The published signature strings match the documented API.
- Every enum member and string alias above has a passing test.
- `backup=True` creates `<input>.bak`, refuses to overwrite an existing backup,
  and is rejected when `output` is provided.
- `interlace=None` and `interlace="keep"` have separate tests that document the
  default deinterlace behavior.
- Invalid option names raise `TypeError`.
- Invalid option values raise `ValueError`.
- `PngError` is still raised for corrupt PNG input.
- Type stubs expose all public functions and enums.
- `py.typed` remains included in wheels.
- Documentation clearly lists supported and unsupported compatibility surface.

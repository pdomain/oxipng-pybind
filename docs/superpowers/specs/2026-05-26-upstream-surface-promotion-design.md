# Upstream Surface Promotion Design

## Goal

Promote all remaining practical upstream `oxipng` 10.1.1 surfaces to stable
Python API, except stdin and stdout stream handling.

## Scope

Promote these surfaces:

- `Options.max_decompressed_size`
- advanced `Options` fields already parsed as compatibility keywords
- explicit chunk keep/strip lists
- deflater tuning factories
- `FilterStrategy::Predefined`
- `OutFile::None`

Keep stdin and stdout stream handling caller-owned.

## Stable API Changes

### Resource Limit

Add `max_decompressed_size` as a stable keyword on:

- `optimize`
- `optimize_from_memory`
- `RawImage.create_optimized_png`

It accepts `int | None`. `None` keeps the upstream default.

Reject:

- `bool`
- negative integers
- integers larger than Rust `usize`
- non-integers

### Advanced Options

These keywords become stable and warning-free:

- `optimize_alpha`
- `bit_depth_reduction`
- `color_type_reduction`
- `palette_reduction`
- `grayscale_reduction`
- `idat_recoding`
- `scale_16`
- `fast_evaluation`
- `timeout`

Keep current validation. `timeout` rejects booleans, negative values,
non-finite values, and out-of-range values.

### Stable Factories

Promote these factories to stable API:

- `StripChunks.strip(names)`
- `StripChunks.keep(names)`
- `Deflaters.libdeflater(compression)`
- `Deflaters.zopfli(iterations)`

These factories must not emit `DeprecationWarning`.

Keep concise stable docstrings.

Chunk names must be four ASCII letters. Deflater values keep the current
validated ranges:

- libdeflater compression: `0` through `12`
- zopfli iterations: `1` through `255`

### Predefined Filters

Add `FilterStrategy.predefined(filters)`.

The argument is a non-empty sequence. Each item may be a `RowFilter`,
`FilterStrategy`, or string for one basic row filter:

- `none`
- `sub`
- `up`
- `average`
- `paeth`

The factory returns a stable object accepted by the existing `filter` keyword.
It maps to upstream `FilterStrategy::Predefined`.

Reject:

- empty sequences
- unknown filter values
- non-basic filters such as `minsum`, `entropy`, `bigrams`, `bigent`, or
  `brute`

### Dry Run

Expose upstream `OutFile::None` as:

```python
analyze(input, *, **file_options) -> OptimizationResult
```

`analyze` reads a PNG file and runs optimization without writing output.

`OptimizationResult` exposes:

- `original_size: int`
- `optimized_size: int`

The result type should be immutable from Python.

`analyze` accepts the same options as `optimize` except:

- no `output`
- no `backup`
- no `preserve_attrs`

Unsupported options should raise normal Python caller errors.

## Compatibility Policy

The stable API must be warning-free.

Only remaining compatibility-only paths emit the existing exact warning:

```text
pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; this compatibility path will be removed in a future release.
```

After this work, expected compatibility-only paths are:

- `ColorType` descriptor calls
- `RawImage(data, width, height, color_type=...)`
- pyoxipng naming aliases such as `Interlacing.Off` and `Interlacing.Adam7`

stdin and stdout stream handling stays caller-owned and should not get a
compatibility path in this work.

## Docs and Manifest

Update:

- `oxipng/__init__.py`
- `oxipng/__init__.pyi`
- `src/lib.rs`
- `tests/test_api.py`
- `docs/api-surface/oxipng-10.1.1.toml`
- active docs that describe option support and pyoxipng gaps

Do not edit `docs/archive/**`.

## Verification

Run:

- `uv run --group dev maturin develop --quiet`
- `uv run --no-sync --group dev pytest`
- `cargo fmt --check`
- `cargo clippy -- -D warnings`
- `uv run --group dev ruff check oxipng scripts tests`
- `uv run --group dev basedpyright`
- markdownlint on touched docs

Inspect:

- stable paths do not emit `DeprecationWarning`
- remaining compatibility paths still warn
- stdin and stdout stream handling remains documented as caller-owned

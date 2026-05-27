# pyoxipng Compatibility Design

## Goal

Add pyoxipng-style API paths for migration testing. These paths are not the
supported long-term API.

## Status

This design was implemented first. Later work promoted some paths to stable API.
`StripChunks.strip(...)`, `StripChunks.keep(...)`, `Deflaters.*`,
advanced options, `timeout`, `max_decompressed_size`,
`FilterStrategy.predefined(...)`, and `analyze(...)` are now stable and
warning-free.

The remaining warning paths are `ColorType` descriptor calls,
`RawImage(data, width, height, color_type=...)`, `Interlacing.Off`,
`Interlacing.Adam7`, and `RowFilter`.

## Policy

The existing oxipng-pybind API remains the supported API. Compatibility paths
help users port pyoxipng code and should be removed from user code after the
port.

Every compatibility-only callable must:

- work where it maps cleanly to the current implementation;
- emit `DeprecationWarning` when used;
- include a concise docstring that names the compatibility contract;
- point users toward the stable oxipng-pybind API;
- avoid behavior changes for existing stable API calls.

Use `DeprecationWarning` because these calls are transitional API paths, not
ordinary runtime notices.

## Compatibility Surface

### Naming Aliases

Add pyoxipng-style aliases for common option names:

- `Interlacing.Off`
- `Interlacing.Adam7`
- `RowFilter`

Keep current enum values and stable string parsing unchanged. `RowFilter`
should act as a compatibility alias for the current filter strategy surface
unless a separate object is needed for type-checking clarity.

### Raw Image Compatibility

Add a compatibility constructor path:

```python
RawImage(data, width, height, color_type=...)
```

Keep the explicit stable constructor:

```python
RawImage(width, height, color_type, bit_depth, data, *, palette=None, transparent=None)
```

Add `ColorType` helpers where they map cleanly:

- `ColorType.rgb(...)`
- `ColorType.rgba()`
- `ColorType.indexed(...)`
- `ColorType.grayscale(...)`
- `ColorType.grayscale_alpha()`

These helpers should produce values accepted by `RawImage`. They should warn
when called.

### Option Factories

Add compatibility factories for explicit chunk and deflater options:

- `StripChunks.strip(...)`
- `StripChunks.keep(...)`
- `Deflaters.libdeflater(int)`
- `Deflaters.zopfli(int)`

These factories started as compatibility factories. They were later promoted to
stable API. Current code must validate inputs and must not warn when these
factories are used.

### Advanced Options

Evaluate pyoxipng advanced options one at a time:

- `optimize_alpha`
- `bit_depth_reduction`
- `color_type_reduction`
- `palette_reduction`
- `grayscale_reduction`
- `idat_recoding`
- `scale_16`
- `fast_evaluation`
- `timeout`

Start with boolean options that map directly to stable upstream fields. Treat
`timeout` separately because it changes execution behavior and needs focused
tests.

These options were later promoted to stable API. Current code must not warn when
callers use them.

## Warnings and Docs

Remaining compatibility warnings should use this exact text:

```text
pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; this compatibility path will be removed in a future release.
```

Docstrings should be one sentence unless a second sentence is needed to mention
the warning or migration requirement.

Compatibility docstrings must not say the path is supported. Prefer wording
like:

```text
Create a pyoxipng-compatible RGB color descriptor; emits DeprecationWarning.
```

## Testing

Use test-driven development for each compatibility slice.

Tests must prove:

- compatibility-only calls emit `DeprecationWarning`;
- stable API calls do not warn;
- compatibility inputs produce valid optimized PNG output where applicable;
- invalid compatibility inputs raise specific Python exceptions;
- runtime `__doc__` values exist for compatibility callables;
- stubs expose the compatibility surface accurately.

Keep tests name-first. Do not add docstrings to every test function.

## Implementation Boundaries

Keep compatibility parsing narrow and explicit. Do not replace the stable parser
with broad dynamic behavior.

Prefer small helper types or parser functions over repeated ad hoc string
checks. Compatibility types should be easy to remove later.

Do not add PyPI publishing, wheel target changes, or migration-guide prose in
this implementation. Those remain separate milestones.

## Remaining Migration Expectations

Users can use remaining compatibility-only paths to test a port from pyoxipng.
They should migrate to the stable oxipng-pybind API after that port works.

Packaging parity and platform parity remain separate work. Migration docs now
exist. stdin and stdout stream handling stays caller-owned.

## Open Decisions

Implementation planning must decide:

- whether `RowFilter` is a direct alias or a distinct class;
- whether `Deflaters` coexists with current `Deflater` or replaces nothing;
- how compatibility objects are represented in Rust and stubs;
- which advanced option is implemented first.

## Self-Review

- No placeholder requirements remain.
- Stable API behavior stays separate from compatibility behavior.
- Warning policy, docstring policy, and testing expectations are explicit.
- Packaging parity is intentionally out of scope.

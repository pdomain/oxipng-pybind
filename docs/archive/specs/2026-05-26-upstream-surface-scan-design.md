# Upstream Surface Scan Design

## Summary

Add automation that compares the wrapper's explicitly supported API surface with
the relevant upstream `oxipng` option and enum surface during upstream bump
workflows. The scanner reports new upstream surface area as documented gaps; it
must never expose new Python API automatically.

This is a later phase than the core API and wheel workflow. It is intentionally
specified separately because it touches GitHub issues, changelog generation, and
upstream source analysis.

## Goals

- Detect upstream additions, removals, and renames in relevant `oxipng` option
  and enum surfaces.
- Keep `oxipng-pybind` API exposure explicit and reviewable.
- Update compatibility documentation when upstream adds unexposed surface area.
- Add changelog notes for upstream surface changes.
- Include a concise upstream-surface section in automated bump PRs.
- Open or update a GitHub issue for human triage.

## Non-Goals

- Do not expose new enum values or options automatically.
- Do not parse the entire upstream Rust crate.
- Do not require a full Rust semantic analyzer.
- Do not block patch bumps just because upstream added unexposed surface area,
  provided docs/changelog/issue updates were generated successfully.
- Do not close triage issues automatically.

## Source of Truth

The wrapper-owned manifest is the source of truth for supported and intentionally
unexposed API. Add a checked-in machine-readable file:

```text
docs/api-surface/oxipng-10.1.1.toml
```

The manifest records:

- upstream version
- exposed Python options
- exposed enum classes and values
- intentionally unexposed upstream `Options` fields
- intentionally unexposed upstream enum variants
- notes for values that are collapsed or renamed in Python

The scanner compares the manifest against the upstream crate version pinned in
`Cargo.toml`.

Manifest lifecycle:

- Each pinned upstream version has its own manifest file named
  `docs/api-surface/oxipng-<version>.toml`.
- The manifest for the currently pinned version must be present in Git.
- During an upstream bump from version `A` to version `B`, automation copies
  `oxipng-A.toml` to `oxipng-B.toml` before scanning.
- The scan updates `oxipng-B.toml` only by adding newly discovered upstream
  items to unexposed sections or by marking removed upstream items as missing.
- The scan must not add new items to exposed sections.
- The old `oxipng-A.toml` remains in Git as historical compatibility evidence
  unless a later cleanup explicitly removes old manifests.

Partial manifest shape:

```toml
upstream_version = "10.1.1"

[functions]
exposed = ["optimize", "optimize_from_memory"]

[options.exposed]
level = "Options::from_preset"
interlace = "Options.interlace"
strip = "Options.strip"
deflate = "Options.deflater"
filter = "Options.filters"
fix_errors = "Options.fix_errors"
force = "Options.force"

[options.unexposed]
optimize_alpha = "lossy transparent-pixel optimization deferred"
bit_depth_reduction = "kept at preset value"

[enums.FilterStrategy.exposed]
none = "FilterStrategy::Basic(RowFilter::None)"
sub = "FilterStrategy::Basic(RowFilter::Sub)"

[enums.FilterStrategy.unexposed]
Predefined = "requires per-row filter input API"
```

## Relevant Upstream Surface

For upstream `oxipng` 10.1.1, scan these Rust items:

- `src/options.rs`
  - `Options`
  - `Options::from_preset`
  - `OutFile`
  - `InFile`
- `src/filters.rs`
  - `FilterStrategy`
  - `RowFilter`
- `src/headers.rs`
  - `StripChunks`
- `src/colors.rs`
  - `ColorType`
  - `BitDepth`
- `src/deflate/mod.rs`
  - `Deflater`
- `src/lib.rs`
  - `optimize`
  - `optimize_from_memory`

The scanner does not need to inspect implementation internals beyond these
surface declarations.

## Scanner Strategy

Use a small Python script:

```text
scripts/scan_upstream_surface.py
```

Inputs:

- local upstream checkout path, default `.cache/upstream/oxipng`
- expected upstream version from `Cargo.toml`
- wrapper manifest path under `docs/api-surface/`

The script should clone or update upstream only when explicitly requested. In CI,
the bump workflow should provide the checkout path after fetching the matching
tag. Local default behavior should fail with a clear message if the upstream
checkout is missing.

Parsing approach:

- Prefer lightweight Rust source parsing with explicit regexes anchored to known
  declarations.
- Keep parser scope narrow and covered by fixture tests.
- Fail closed when a known declaration cannot be found.
- Emit structured JSON for workflow consumption.

This is acceptable because the scanner is a compatibility tripwire, not a Rust
compiler replacement.

Parser fixture tests must include minimal Rust snippets for these shapes:

```rust
pub struct Options {
    pub fix_errors: bool,
    pub force: bool,
}
```

```rust
pub enum FilterStrategy {
    Basic(RowFilter),
    Brute {
        num_lines: usize,
        level: u8,
    },
    Predefined(Vec<RowFilter>),
}
```

```rust
#[cfg(feature = "zopfli")]
pub enum Deflater {
    Libdeflater { compression: u8 },
    Zopfli(ZopfliOptions),
}
```

```rust
pub fn optimize_from_memory(data: &[u8], opts: &Options) -> PngResult<Vec<u8>> {
    todo!()
}
```

The parser must handle multiline struct fields, multiline enum variants,
attribute lines such as `#[cfg(...)]`, and generic tuple-like enum variants.

## Detected Change Types

The scanner reports:

- new upstream `Options` fields
- removed upstream `Options` fields that are exposed by the wrapper
- new upstream enum variants in relevant enums
- removed upstream enum variants exposed by the wrapper
- changed public function presence for `optimize` and `optimize_from_memory`
- manifest entries for upstream items no longer found

Detected removals of exposed wrapper mappings are blocking. New unexposed items
are non-blocking only if docs, changelog, and issue updates are generated.

## Generated Outputs

The scan command writes:

```text
.cache/upstream-surface/report.json
.cache/upstream-surface/pr-body-section.md
```

When changes are detected during an upstream bump, automation updates:

- `docs/architecture/api-compatibility.md`
- `docs/architecture/options-surface.md`
- `CHANGELOG.md`

The generated docs updates must list new upstream items under an "Unexposed
upstream surface" section with the upstream version that introduced them.

## GitHub Issue Triage

The bump workflow opens or updates one issue per upstream version when new
unexposed surface is detected.

Issue label:

```text
upstream-surface
```

Issue title:

```text
Evaluate upstream oxipng <version> surface changes
```

Issue body includes:

- upstream version
- detected new items
- detected removed items, if any
- generated docs links
- triage checklist:
  - expose now
  - defer and document
  - reject as intentionally unsupported

Automation avoids duplicates by searching open issues with the
`upstream-surface` label and the same upstream version in the title.

## Upstream Bump Workflow Integration

Enhance `.github/workflows/upstream-bump.yml` after the existing version update
step:

1. Determine the target upstream version.
2. Fetch `oxipng/oxipng` tag `v<version>` into `.cache/upstream/oxipng`.
3. Run `uv run python scripts/scan_upstream_surface.py --update-docs`.
4. Run source CI.
5. Include `.cache/upstream-surface/pr-body-section.md` in the PR body.
6. If new unexposed surface is detected, create or update the triage issue.
7. Enable auto-merge only when blocking removals are absent and CI passes.

The workflow needs `issues: write` in addition to existing contents and pull
request permissions once issue filing is implemented.

## Files

Expected implementation files:

- `scripts/scan_upstream_surface.py`
- `tests/test_scan_upstream_surface.py`
- `docs/api-surface/oxipng-10.1.1.toml`
- `docs/architecture/api-compatibility.md`
- `docs/architecture/options-surface.md`
- `docs/process/upstream-bumps.md`
- `CHANGELOG.md`
- `.github/workflows/upstream-bump.yml`

## Acceptance Criteria

- Scanner detects added upstream enum variants in test fixtures.
- Scanner detects removed upstream enum variants that are exposed by the wrapper.
- Scanner detects added and removed upstream `Options` fields in test fixtures.
- Scanner emits stable JSON and PR-body markdown.
- Bumping from one upstream version to another creates a new versioned manifest
  without mutating exposed sections automatically.
- Generated docs list unexposed upstream items without exposing them in Python.
- Upstream bump PR body includes an "Upstream surface changes" section.
- The bump workflow does not enable auto-merge when exposed mappings are broken.
- New unexposed upstream items create or update exactly one triage issue per
  upstream version.

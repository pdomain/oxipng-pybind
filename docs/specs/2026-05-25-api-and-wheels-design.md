# API and Wheel Expansion Design

## Summary

`oxipng-pybind` will grow from a focused file optimizer wrapper into a clean,
oxipng-native Python binding with practical pyoxipng compatibility. This phase
adds in-memory optimization, a conservative option surface, typed enum helpers,
wheel artifact builds for Python 3.10+, and documentation that clearly records
supported APIs and upstream gaps.

The package identity stays unchanged:

- GitHub repository: `ConcaveTrillion/oxipng-pybind`
- PyPI distribution: `oxipng-pybind`
- Python import module: `oxipng`

## Goals

- Keep the public API centered on current upstream `oxipng` behavior.
- Preserve practical pyoxipng compatibility where it maps cleanly.
- Add `optimize_from_memory()` for non-file workflows.
- Support a conservative, documented option set.
- Accept both string values and typed enum values for option-like settings.
- Build installable wheels so users on supported platforms do not need Rust.
- Test every public API surface across Python 3.10 through 3.14.
- Track upstream API surface changes without silently exposing new wrapper APIs.

## Non-Goals

- Do not rename the package or repository.
- Do not implement `RawImage` in this phase.
- Do not publish to PyPI automatically in this phase.
- Do not build or publish an sdist in this phase.
- Do not auto-expose newly discovered upstream options or enum values.

## Public API

The public import remains `oxipng`.

```python
from oxipng import Deflaters, Interlacing, PngError, RowFilter, StripChunks
from oxipng import optimize, optimize_from_memory
```

Supported functions:

```python
optimize(
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
) -> None
```

```python
optimize_from_memory(
    data,
    *,
    level=2,
    interlace=None,
    strip=None,
    deflate=None,
    filter=None,
    fix_errors=False,
    force=False,
) -> bytes
```

The file API accepts string paths, bytes paths, and `os.PathLike` values. If
`output` is omitted, the input file is optimized in place.

The memory API accepts PNG bytes and returns optimized PNG bytes.

Unsupported keyword names raise `TypeError`. Recognized options with invalid
values raise `ValueError` and list the allowed values where practical.

## Option Surface

This phase supports a conservative option set:

- `level`
- `interlace`
- `strip`
- `deflate`
- `filter`
- `fix_errors`
- `force`
- `backup`
- `preserve_attrs`

Option values that map to upstream enum-like concepts accept both strings and
typed enum values. Strings are the primary documented interface because they are
simple to use in scripts and config-driven workflows. Enums provide autocomplete,
type-checking help, and compatibility tripwires for upstream changes.

Example:

```python
optimize("input.png", "output.png", strip="safe", filter="sub")
optimize("input.png", "output.png", strip=StripChunks.safe, filter=RowFilter.sub)
```

The exposed enums intentionally include only values the wrapper commits to
supporting. Upstream values discovered later are documented as unexposed gaps
until they are intentionally added with tests and docs.

## Rust/Python Boundary

The Rust extension should use a small internal option parsing layer rather than
growing ad hoc keyword parsing inside individual pyfunctions.

Responsibilities:

- Convert Python values into explicit `oxi::Options`.
- Validate supported strings, enum values, booleans, and integer ranges.
- Map caller mistakes to Python-native exceptions.
- Map upstream PNG failures to `PngError`.
- Keep enum-to-upstream mappings explicit.

Optimization calls should release the GIL when they do not interact with Python
objects during the upstream `oxipng` call.

Explicit enum mappings are part of the compatibility strategy: when upstream
renames or removes an exposed variant, compilation or mapping tests should fail
in the upstream bump PR.

## Wheel Artifacts

Add an artifact-only wheel workflow before enabling PyPI publishing.

Wheel requirements:

- Use PyO3 `abi3-py310` so one wheel per OS/architecture supports Python 3.10+.
- Build Linux `x86_64` `manylinux_2_28`.
- Build Linux `aarch64` `manylinux_2_28`.
- Build macOS `x86_64`.
- Build macOS `aarch64`.
- Build Windows `x86_64`.
- Upload wheels as GitHub Actions artifacts.
- Do not build or upload an sdist.

Workflow triggers:

- `workflow_dispatch`
- version tags
- optionally pull requests that touch packaging or release files

Each wheel job should smoke-test its own wheel after building it by installing
the wheel into a clean environment and running import, file optimization, and
memory optimization checks.

Linux `aarch64` uses a native ARM runner so its wheel smoke test is a hard gate
for that target.

PyPI publishing is a later phase. That later workflow should use PyPI Trusted
Publishing with `id-token: write` and should publish wheels only unless an sdist
fallback is explicitly accepted.

## CI and Upstream Automation

Regular CI remains the main development gate:

- `make ci`
- Rust lint
- Python lint and typecheck
- unit tests
- `cargo-deny`
- local wheel build

Add Python-version testing for public APIs across Python 3.10, 3.11, 3.12,
3.13, and 3.14. Since release wheels use `abi3-py310`, this verifies runtime
compatibility without building separate wheels for each Python version.

The upstream bump workflow should:

- update the pinned upstream `oxipng` version and lock files
- run full source CI
- run the wheel artifact workflow or an equivalent wheel matrix before merge,
  when feasible
- allow auto-merge for patch, minor, and major upstream bumps if no exposed
  functionality breaks and all required compatibility checks pass
- block auto-merge when tests fail, compatibility scans find unresolved risk, or
  generated docs/changelog updates cannot be produced

Major bumps are not automatically manual-only. They may merge automatically when
the compatibility checks prove that exposed behavior remains intact.

## Upstream Surface Scan

Every upstream bump should scan the relevant upstream option and enum surface and
compare it against the wrapper's exposed API and documented gaps.

When new upstream items are found, automation should:

- update compatibility docs to list them as unexposed gaps
- update `CHANGELOG.md` with an upstream-surface note
- include an "Upstream surface changes" section in the bump PR body
- open or update a GitHub issue for evaluation

The issue should identify the upstream version, list new items, and include a
checkbox-style triage path for expose, defer, or reject decisions. Automation
should avoid duplicate issues by searching for an open issue with the same
upstream version or a stable upstream-surface label.

Automation must not expose new public API values by default.

## Documentation

Use the repository's existing docs taxonomy:

```text
docs/README.md
docs/architecture/overview.md
docs/architecture/api-compatibility.md
docs/architecture/options-surface.md
docs/usage/file-optimization.md
docs/usage/memory-optimization.md
docs/process/upstream-bumps.md
CHANGELOG.md
```

Content split:

- `README.md`: install, quick file and memory examples, supported API summary,
  and wheel availability.
- `docs/README.md`: documentation index.
- `docs/architecture/overview.md`: package layout, Rust/Python boundary, data
  flow, error mapping, and wheel strategy.
- `docs/architecture/api-compatibility.md`: pyoxipng, upstream oxipng, and
  `oxipng-pybind` comparison with documented gaps.
- `docs/architecture/options-surface.md`: exposed options, enum and string
  values, validation rules, and upstream mapping policy.
- `docs/usage/file-optimization.md`: file API examples and error behavior.
- `docs/usage/memory-optimization.md`: bytes API examples and constraints.
- `docs/process/upstream-bumps.md`: bump automation, compatibility scans,
  auto-merge rules, and issue filing.
- `CHANGELOG.md`: wrapper API changes and upstream bump notes.

## Testing

Testing should prove every public API surface, not only the happy path.

Unit and API tests cover:

- imports
- function signatures
- file optimization in place
- file optimization to an output path
- memory optimization
- all supported option keyword arguments
- all exposed enum values
- string aliases for enum values
- invalid option names
- invalid option values
- corrupt PNG errors
- type stubs and `py.typed`

Matrix tests run the public API suite across Python 3.10 through 3.14.

Wheel smoke tests install the built wheel into a clean environment, import
`oxipng`, optimize a generated PNG file, optimize generated PNG bytes, and verify
the outputs are readable PNGs.

Upstream bump tests cover:

- compatibility scan detection of exposed and unexposed upstream surface
- generated docs/changelog updates when new upstream items are found
- patch, minor, and major bump auto-merge policy

## Open Follow-Up Work

- `RawImage` support after the core API and wheel workflow are stable.
- PyPI Trusted Publishing after the artifact-only wheel workflow is proven.
- Optional sdist publishing only if fallback builds requiring Rust are
  intentionally accepted.

## Implementation Notes

- Public API coverage across Python 3.10 through 3.14 is implemented by
  `.github/workflows/api-matrix.yml`.
- Linux aarch64 wheel smoke testing is implemented with GitHub's native
  `ubuntu-24.04-arm` runner.

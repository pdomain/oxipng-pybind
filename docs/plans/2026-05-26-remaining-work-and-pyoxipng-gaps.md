# Remaining Work and pyoxipng Gaps

This roadmap records the project state on 2026-05-26. It lists finished work,
open release work, pyoxipng compatibility status, and the recommended next
order.

`pyoxipng` comparison notes use the PyPI page for `pyoxipng` 9.1.1, released
2025-08-21: [pyoxipng on PyPI](https://pypi.org/project/pyoxipng/).

## Current Status

The package shape is in place:

- The distribution name is `oxipng-pybind`.
- The import package is `oxipng`.
- The native module is `_oxipng`.
- The package version and Rust `oxipng` dependency are pinned to upstream
  `oxipng` 10.1.1.
- The API surface manifest records the same upstream version.

The public Python API is in place:

- `optimize`, `optimize_from_memory`, `analyze`, `OptimizationResult`,
  `PngError`, option enums, raw-image enums, and `RawImage` are exported.
- Type stubs, `py.typed`, and runtime docstrings exist for the supported API.
- File optimization supports in-place writes, explicit output paths,
  path-like inputs, `backup`, `preserve_attrs`, level checks, option parsing,
  and predictable Python exceptions.
- Memory optimization supports `bytes`, `bytearray`, and `memoryview`.
- `RawImage` supports `ColorType`, `BitDepth`, packed pixel data, indexed
  palettes, transparency checks, ancillary chunks, ICC profiles, and
  `create_optimized_png`.
- The option surface includes stable upstream options, explicit strip/keep
  chunks, deflater tuning, predefined filters, and dry-run analysis.
- Supported option values accept stable strings and Python enum `.value`
  strings. Rust code does not depend on Python enum object identity.

Tests and docs are in place:

- Public API tests cover imports, signatures, aliases, file optimization,
  memory optimization, raw image creation, validation errors, and corrupt PNG
  failures.
- Scanner tests cover Rust surface parsing, comparison reports, generated
  docs, and stable scan output.
- Documentation covers usage, architecture, API compatibility, option surface,
  release artifacts, upstream bumps, dependency health, and lint deviations.
- The pyoxipng migration guide is at `docs/usage/pyoxipng-migration.md`.
- Changelog entries record the memory API, raw image API, option surface, ABI3
  wheel metadata, wheel workflow scaffolding, and upstream scanner scaffolding.

## CI and Release Workflow Status

The workflow files exist, but hosted runs still need proof.

Completed workflow pieces:

- Wheel tag and smoke-test helper scripts exist.
- `wheels.yml` builds artifact-only wheels for Linux x86_64, Linux aarch64,
  macOS x86_64, macOS aarch64, and Windows x86_64.
- Wheel builds use PyO3 ABI3 for Python 3.11 and newer.
- `api-matrix.yml` covers Python 3.11, 3.12, 3.13, and 3.14.
- `dependency-health.yml` covers scheduled lockfile refreshes, audits, and
  CI-gated dependency refresh PRs.
- `upstream-bump.yml` covers version updates, manifest preparation, upstream
  surface scans, PR creation, triage issue upsert, wheel workflow waiting, and
  auto-merge.
- Wheel smoke checks verify imports, typing files, file optimization, memory
  optimization, `memoryview`, `RawImage`, custom PNG chunks, and Pillow-readable
  output.

Open CI and release work:

- Prove `wheels.yml`, `api-matrix.yml`, `dependency-health.yml`, and
  `upstream-bump.yml` in GitHub Actions.
- Run the first real upstream bump after 10.1.1. This should prove release
  discovery, manifest copying, scanner output, docs updates, issue upsert,
  wheel workflow waiting, and auto-merge conditions.
- Confirm repository settings outside the workspace: `UPSTREAM_BUMP_TOKEN`,
  `DEPENDENCY_REFRESH_TOKEN`, Actions PR permissions, branch protection,
  required checks, and repository auto-merge.
- Replace mutable GitHub Action references with pinned full commit SHAs before
  release hardening.
- Decide whether the project should publish to PyPI. Current wheel work is
  artifact-only by design.
- If PyPI publishing is approved, add Trusted Publishing and decide whether
  publishing remains wheel-only.
- Decide whether to add an sdist. Current docs defer sdist support because
  source installs require Rust and a compatible build environment.
- Add release notes for first public artifacts after the wheel workflow
  produces verified artifacts.
- Verify local and hosted wheel metadata, especially `oxipng/__init__.pyi`,
  `oxipng/py.typed`, license files, and platform tags.

## Completed pyoxipng Compatibility Paths

`oxipng-pybind` covers the main practical workflows from `pyoxipng`:

- file optimization;
- memory optimization;
- raw image output;
- common options;
- the `oxipng` import name.

These pyoxipng-style compatibility paths exist:

- naming aliases for common option names;
- `RawImage(data, width, height, color_type=...)`;
- callable `ColorType` descriptors;
- `RowFilter`;
- `StripChunks.strip(...)` and `StripChunks.keep(...)`;
- `Deflaters.libdeflater(int)` and `Deflaters.zopfli(int)`;
- advanced boolean option keywords;
- `timeout`;
- `max_decompressed_size`;
- `analyze`, which maps to upstream `OutFile::None`;
- `FilterStrategy.predefined(...)`, which maps to upstream
  `FilterStrategy::Predefined`.

Most of these paths are now stable API. Remaining compatibility-only paths emit
`DeprecationWarning`; new code should use the stable oxipng-pybind API.

## Remaining pyoxipng Gaps

This project is not a full drop-in replacement for `pyoxipng`.

- Python version policy differs. `pyoxipng` 9.1.1 advertises Python 3.8+ on
  PyPI. This project requires Python 3.11+.
- Distribution artifacts differ. `pyoxipng` publishes PyPI wheels and an sdist.
  This project builds artifact-only wheels and does not publish to PyPI.
- Wheel strategy differs. `pyoxipng` publishes CPython-version-specific wheels.
  This project targets ABI3 `cp311-abi3` wheels for Python 3.11+.
- Platform coverage differs. `pyoxipng` publishes extra targets such as
  musllinux and 32-bit Windows. This project targets manylinux
  x86_64/aarch64, macOS x86_64/aarch64, and Windows x86_64.
- A migration guide exists with side-by-side stable and compatibility examples.
- stdin and stdout stream handling is caller-owned. Use `optimize_from_memory`
  after reading bytes.
- `backup` and `preserve_attrs` are wrapper-specific controls, not pyoxipng
  parity targets.

## Remaining Product and Test Work

These gaps are still visible in the workspace:

- Consider tests for `preserve_attrs`. The option is passed to upstream, but
  current tests focus on argument validation and readable PNG output.
- Consider tests for `add_icc_profile`. The method exists, but public API tests
  focus more on chunk preservation than ICC output.
- Consider tests for `optimize_from_memory(memoryview(...))` with sliced or
  non-contiguous buffers if those buffers become a product requirement.
- Decide whether to document and test exact default interlace behavior more
  prominently. The spec separates `interlace=None` and `interlace="keep"`,
  while user docs summarize supported values.

## pyoxipng Parity Roadmap

Preserve the current stable API. Add pyoxipng-compatible aliases only where
they do not create unsafe defaults.

1. Packaging parity:
   - Decide whether `oxipng-pybind` should publish to PyPI.
   - Add Trusted Publishing if PyPI distribution is approved.
   - Decide whether to publish an sdist.
   - Add or reject musllinux and 32-bit Windows wheel targets.

2. Naming and enum parity:
   - pyoxipng-style `Interlacing.Off`, `Interlacing.Adam7`, and `RowFilter`
     exist as compatibility paths.
   - `FilterStrategy` remains the stable name.

3. Raw image constructor parity:
   - `RawImage(data, width, height, color_type=...)` exists as a
     warning-emitting compatibility constructor.
   - `ColorType` helper constructors exist as warning-emitting compatibility
     factories.
   - The explicit constructor path remains the stable API.

4. Option object parity:
   - `StripChunks.strip(...)` and `StripChunks.keep(...)` are stable API for
     explicit chunk-name lists.
   - `Deflaters.libdeflater(int)` and `Deflaters.zopfli(int)` are stable API
     with range validation.
   - `FilterStrategy.predefined(...)` is stable API for predefined row filters.

5. Advanced option parity:
   - `optimize_alpha`, `bit_depth_reduction`, `color_type_reduction`,
     `palette_reduction`, `grayscale_reduction`, `idat_recoding`, `scale_16`,
     `fast_evaluation`, `timeout`, and `max_decompressed_size` are stable API.
   - `timeout` rejects booleans, negative values, non-finite values, and
     out-of-range values with Python exceptions.
   - `analyze(...)` exposes upstream `OutFile::None`.

6. Behavior and migration parity:
   - Keep the pyoxipng migration guide synced with stable API examples.
   - Add tests for pyoxipng-style examples from public docs, adapted only where
     behavior intentionally differs.
   - Keep stdin and stdout stream handling caller-owned.

## Future Work

Split future work into small phases:

- Release hardening: pin GitHub Actions by SHA, prove hosted wheel runs, verify
  artifact metadata, and document the first release checklist.
- PyPI phase: add Trusted Publishing, choose wheel-only or wheel-plus-sdist
  policy, and document rollback expectations.
- Compatibility phase: keep the migration guide synced with tested examples.
- Upstream option phase: keep process stream handling outside this API.
- Platform phase: decide whether musllinux, 32-bit Windows, or extra Linux
  architectures are in scope.
- Documentation phase: keep stable API examples synchronized with any
  compatibility path that graduates to supported API surface.
- Observability phase: make upstream bump reports list exact added and removed
  items, not only a high-level PR body section.

## Recommended Next Order

1. Run and inspect hosted `wheels.yml` with the current tree.
2. Run and inspect hosted `api-matrix.yml`.
3. Confirm required repository secrets and branch protection.
4. Choose the next milestone: PyPI packaging parity or migration guide tests.
5. If packaging parity is chosen, add Trusted Publishing and artifact metadata
   verification first.
6. If migration guide tests are chosen, verify the examples against tests. Make
   the warning-emitting compatibility paths clear.
7. Turn the chosen milestone into a focused implementation plan before adding
   more API surface.

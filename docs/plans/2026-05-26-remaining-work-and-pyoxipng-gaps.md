# Remaining Work and pyoxipng Gaps

This scan reconciles the checked-in docs with the current workspace state on
2026-05-26. It captures completed work, remaining gaps, known differences from
`pyoxipng`, and future work.

`pyoxipng` comparison notes use the current PyPI project page for
`pyoxipng` 9.1.1, released 2025-08-21:
[pyoxipng on PyPI](https://pypi.org/project/pyoxipng/).

## Completed Workspace Items

The repository has completed the main items described by the archived specs and
implementation plans.

- Public package shape is implemented: the distribution remains
  `oxipng-pybind`, the import package remains `oxipng`, and the native module is
  `_oxipng`.
- The package version and upstream Rust dependency are pinned to upstream
  `oxipng` 10.1.1 in `pyproject.toml`, `Cargo.toml`, and the API surface
  manifest.
- The Python facade exports `optimize`, `optimize_from_memory`, `PngError`,
  option enums, raw-image enums, and `RawImage`.
- Type stubs, `py.typed`, and runtime docstrings are present for the supported
  public API.
- File optimization supports in-place and explicit-output workflows, path-like
  inputs, `backup`, `preserve_attrs`, level validation, option parsing, and
  predictable Python exceptions.
- Memory optimization supports `bytes`, `bytearray`, and `memoryview` inputs.
- `RawImage` support is implemented with `ColorType`, `BitDepth`, packed pixel
  data, indexed palettes, transparency validation, ancillary chunk insertion,
  ICC profile insertion, and `create_optimized_png`.
- The conservative option surface is implemented for `level`, `interlace`,
  `strip`, `deflate`, `filter`, `fix_errors`, and `force`.
- Supported option values accept stable strings and Python enum `.value`
  strings rather than depending on enum object identity in Rust.
- pyoxipng-style naming aliases, raw-image constructor compatibility,
  `ColorType` descriptor factories, explicit strip/keep chunk factories,
  deflater tuning factories, and advanced option keywords exist as
  warning-emitting migration paths.
- Public API tests cover imports, signatures, aliases, file optimization,
  memory optimization, raw image creation, validation errors, and corrupt PNG
  failures.
- Scanner tests cover Rust surface parsing, comparison reports, generated docs,
  and deterministic scan outputs.
- Wheel tag and smoke-test helper scripts exist.
- Artifact-only wheel workflow exists for Linux x86_64, Linux aarch64, macOS
  x86_64, macOS aarch64, and Windows x86_64.
- Wheel builds use PyO3 ABI3 for Python 3.11 and newer.
- API matrix workflow exists for Python 3.11, 3.12, 3.13, and 3.14.
- Dependency health workflow exists for scheduled lockfile refreshes, audits,
  and CI-gated dependency refresh PRs.
- Upstream bump workflow exists for version updates, manifest preparation,
  upstream surface scanning, PR creation, triage issue upsert, wheel workflow
  waiting, and auto-merge.
- Documentation now covers usage, architecture, API compatibility, option
  surface, release artifacts, upstream bumps, dependency health, and lint
  deviations.
- Changelog entries record the new memory API, raw image API, option surface,
  ABI3 wheel metadata, wheel workflow scaffolding, and upstream scanner
  scaffolding.

## Remaining Tasks

These are the concrete gaps still visible after comparing docs to workspace
state.

- Prove workflows in GitHub Actions, especially `wheels.yml`,
  `api-matrix.yml`, `dependency-health.yml`, and `upstream-bump.yml`. The files
  exist locally, but the docs do not record successful hosted runs.
- Exercise the first real upstream bump after 10.1.1. This should validate
  release discovery, manifest copying, scanner output, docs updates, issue
  upsert behavior, wheel workflow waiting, and auto-merge conditions.
- Confirm repository secrets and settings outside the workspace:
  `UPSTREAM_BUMP_TOKEN`, `DEPENDENCY_REFRESH_TOKEN`, Actions PR permissions,
  branch protection, required checks, and repository auto-merge.
- Replace mutable GitHub Action references with pinned full commit SHAs before
  release hardening. The upstream-bump docs already call this out.
- Decide whether the project should publish to PyPI. Current wheel work is
  artifact-only by design.
- If PyPI publishing is approved, add a Trusted Publishing workflow and decide
  whether publishing remains wheel-only.
- Decide whether to add an sdist. Current docs intentionally defer sdist support
  because source installs require Rust and a compatible build environment.
- Add release notes for first public artifacts once the wheel workflow has
  produced verified artifacts.
- Verify whether local and hosted wheel artifacts include all expected metadata,
  especially `oxipng/__init__.pyi`, `oxipng/py.typed`, license files, and
  platform tags.
- Consider adding tests for `preserve_attrs` behavior. The option is passed to
  upstream, but workspace tests focus on argument validation and readable PNG
  output.
- Consider adding tests for `add_icc_profile`. The method is implemented, but
  the current public API test file focuses chunk preservation more than ICC
  profile output.
- Consider adding tests for `optimize_from_memory(memoryview(...))` with
  non-trivial buffer views if supporting sliced or non-contiguous buffers is a
  product requirement.
- Decide whether to document and test the exact default interlace behavior more
  prominently. The spec distinguishes `interlace=None` and
  `interlace="keep"`, while user-facing docs summarize supported values.

## pyoxipng Compatibility Gaps

`oxipng-pybind` now covers the most important practical workflows from
`pyoxipng`: file optimization, memory optimization, raw image output, common
options, and the `oxipng` import name. It is still not a full drop-in
replacement.

- Python version policy differs. `pyoxipng` 9.1.1 advertises Python 3.8+ on
  PyPI, while this project requires Python 3.11+.
- Distribution artifacts differ. `pyoxipng` publishes PyPI wheels and an sdist;
  this project currently builds artifact-only wheels and intentionally does not
  publish to PyPI.
- Wheel strategy differs. `pyoxipng` publishes CPython-version-specific wheels
  for multiple versions and platforms; this project targets ABI3 `cp311-abi3`
  wheels for Python 3.11+.
- Platform coverage differs. `pyoxipng` publishes additional targets such as
  musllinux and 32-bit Windows on PyPI; this project currently targets
  manylinux x86_64/aarch64, macOS x86_64/aarch64, and Windows x86_64.
- API compatibility paths now exist for pyoxipng-style naming aliases,
  `RawImage(data, width, height, color_type=...)`, callable `ColorType`
  descriptors, `RowFilter`, explicit `StripChunks.strip(...)` and
  `StripChunks.keep(...)`, `Deflaters.libdeflater(int)`,
  `Deflaters.zopfli(int)`, advanced boolean option keywords, and `timeout`.
- Compatibility paths emit `DeprecationWarning` and remain unsupported for new
  code; users should migrate to the stable oxipng-pybind API.
- A migration guide with side-by-side examples is not written yet.
- stdin/stdout behavior remains unsupported here.
- This project adds file-focused controls, including `backup` and
  `preserve_attrs`, that are wrapper-specific rather than pyoxipng parity
  targets.

## pyoxipng Parity Roadmap

Parity should be treated as a sequence of compatibility layers. Preserve the
current stable API while adding pyoxipng-compatible aliases and constructors
where they do not create unsafe defaults.

1. Packaging parity:
   - Decide whether `oxipng-pybind` should publish to PyPI.
   - Add Trusted Publishing if PyPI distribution is approved.
   - Decide whether to publish an sdist; pyoxipng publishes one, but this
     project currently avoids source-install expectations.
   - Add or explicitly reject musllinux and 32-bit Windows wheel targets.

2. Naming and enum parity:
   - pyoxipng-style `Interlacing.Off`, `Interlacing.Adam7`, and `RowFilter`
     exist as compatibility paths.
   - `FilterStrategy` remains the stable internal name, and `RowFilter` is a
     compatibility enum.

3. Raw image constructor parity:
   - `RawImage(data, width, height, color_type=...)` exists as a warning-emitting
     compatibility constructor.
   - `ColorType` helper constructors such as `rgb(...)`, `rgba()`,
     `indexed(...)`, `grayscale(...)`, and `grayscale_alpha()` exist as
     warning-emitting compatibility factories.
   - The existing explicit constructor path remains the stable API.

4. Option object parity:
   - `StripChunks.strip(...)` and `StripChunks.keep(...)` compatibility
     constructors exist for explicit chunk-name lists.
   - `Deflaters.libdeflater(int)` and `Deflaters.zopfli(int)` compatibility
     constructors exist with range validation.
   - Compatibility factories produce narrow accepted input objects.

5. Advanced option parity:
   - `optimize_alpha`, `bit_depth_reduction`, `color_type_reduction`,
     `palette_reduction`, `grayscale_reduction`, `idat_recoding`, `scale_16`,
     `fast_evaluation`, and `timeout` exist as warning-emitting compatibility
     keywords.
   - `timeout` rejects booleans, negative values, non-finite values, and
     out-of-range values with Python exceptions.

6. Behavior and migration parity:
   - Add a migration guide with side-by-side pyoxipng and oxipng-pybind
     examples.
   - Add tests for pyoxipng-style examples copied from the public docs, adapted
     only where behavior is intentionally different.
   - Decide whether stdin/stdout workflows are required for parity or remain
     explicitly unsupported.

## Future Work

Future work should be split into small, reviewable phases.

- Release hardening: pin GitHub Actions by SHA, prove hosted wheel runs, verify
  artifact metadata, and document the first release checklist.
- PyPI phase: add Trusted Publishing, choose wheel-only or wheel-plus-sdist
  policy, and document rollback expectations.
- Compatibility phase: add a migration guide and decide whether stdin/stdout
  workflows are required for parity.
- Upstream option phase: continue using compatibility warnings for any future
  pyoxipng-only API surface unless it graduates to the stable API.
- Platform phase: decide whether musllinux, 32-bit Windows, or additional Linux
  architectures are in scope.
- Documentation phase: keep stable API examples synchronized with any
  compatibility-path behavior that graduates to supported API surface.
- Observability phase: improve automated upstream bump reports so they include
  a concise list of exact new and removed items, not only the high-level PR body
  section.

## Recommended Next Order

1. Run and inspect hosted `wheels.yml` with the current tree.
2. Run and inspect hosted `api-matrix.yml`.
3. Confirm required repository secrets and branch protection.
4. Choose the next milestone: PyPI packaging parity, migration-guide docs, or
   stdin/stdout compatibility.
5. If packaging parity is chosen, add Trusted Publishing and artifact metadata
   verification first.
6. If migration docs are chosen, write side-by-side pyoxipng and oxipng-pybind
   examples that emphasize warning-emitting compatibility paths.
7. Turn the chosen milestone into a focused implementation plan before adding
   more API surface.

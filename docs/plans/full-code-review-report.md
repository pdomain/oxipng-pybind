# Full Code Review Report

This report consolidates the full-code review findings from the Rust, Python
API, security, CI, release, and test passes.

Status note: the major findings are addressed by
[Major Review Fixes Implementation Plan](major-review-fixes-plan.md). Minor
findings remain recorded here unless they were part of that plan.

## Major

1. **Release actions use mutable tags.**

   Refs: [wheels.yml](../../.github/workflows/wheels.yml:65),
   [wheels.yml](../../.github/workflows/wheels.yml:134)

   Impact: Release builds and PyPI publishing use third-party action tags. A
   moved or compromised tag could affect published wheels.

   Proposed fix: Pin release-path actions to reviewed full SHAs. Keep a planned
   process to refresh those SHAs.

2. **Release tags can publish without proving source CI passed.**

   Refs: [wheels.yml](../../.github/workflows/wheels.yml:3),
   [wheels.yml](../../.github/workflows/wheels.yml:110)

   Impact: Any `v*` tag can run the release path. The workflow builds and smoke
   tests wheels, but it does not require the tagged SHA to have passed `ci.yml`
   and `api-matrix.yml`.

   Proposed fix: Add a release gate that checks required workflows on the tag
   SHA. Also protect release tags and require the PyPI environment approval if
   needed.

3. **Release tag names are not matched to the package version.**

   Refs: [wheels.yml](../../.github/workflows/wheels.yml:95),
   [verify_release_artifacts.py](../../scripts/verify_release_artifacts.py:43)

   Impact: A tag such as `v10.1.0` could publish wheels whose internal version
   is `10.1.1`.

   Proposed fix: Compare `github.ref_name` with `project.version` before
   publish. Fail when they differ.

4. **Wheel builds do not force locked Rust dependencies.**

   Refs: [wheels.yml](../../.github/workflows/wheels.yml:65),
   [Makefile](../../Makefile:124)

   Impact: Release builds can resolve differently from `Cargo.lock` if Cargo
   metadata drifts.

   Proposed fix: Add `--locked` to all release wheel builds.

5. **The dependency refresh token is scoped too widely in the write job.**

   Refs: [dependency-health.yml](../../.github/workflows/dependency-health.yml:78)

   Impact: Every step in the publish job can read `DEPENDENCY_REFRESH_TOKEN`.
   This increases blast radius if a step or action is compromised.

   Proposed fix: Pass the secret only to steps that need it. Keep write-job
   actions pinned to reviewed SHAs.

6. **`RawImage` accepts zero dimensions.**

   Refs: [lib.rs](../../src/lib.rs:954),
   [lib.rs](../../src/lib.rs:1087)

   Impact: `RawImage(0, 1, ...)` can create bytes that image readers reject as
   invalid PNG data.

   Proposed fix: Reject `width == 0` and `height == 0` before calling upstream
   `RawImage::new`.

7. **`RawImage` relies on upstream unchecked length arithmetic.**

   Refs: [lib.rs](../../src/lib.rs:1072),
   [lib.rs](../../src/lib.rs:1087)

   Impact: Huge dimensions can overflow expected-size math in upstream code.
   That can panic in debug builds or misvalidate in release builds.

   Proposed fix: Compute expected byte length in the wrapper with checked
   arithmetic. Return `ValueError` before calling upstream.

8. **Indexed `RawImage` validation can loop for a long time on zero width.**

   Refs: [lib.rs](../../src/lib.rs:798),
   [lib.rs](../../src/lib.rs:820)

   Impact: `width=0` with a huge `height` can trigger a long loop before shape
   validation rejects the image.

   Proposed fix: Reject zero dimensions before indexed-pixel validation.

9. **`level` accepts `bool`.**

   Refs: [lib.rs](../../src/lib.rs:198)

   Impact: `level=True` becomes `1`. This conflicts with stricter integer
   parsing used elsewhere.

   Proposed fix: Reject `PyBool` before extracting the integer.

10. **Compatibility deflater values accept `bool`.**

    Refs: [lib.rs](../../src/lib.rs:190),
    [lib.rs](../../src/lib.rs:270)

    Impact: `Deflaters.libdeflater(True)` becomes compression `1`.
    `False` also behaves inconsistently across deflaters.

    Proposed fix: Reject bools in `py_int_attr` or in deflater parsing.

11. **pyoxipng `RawImage(data, width, height)` default compatibility is missing.**

    Refs: [lib.rs](../../src/lib.rs:978),
    [lib.rs](../../src/lib.rs:1095),
    [init.pyi](../../oxipng/__init__.pyi:148)

    Impact: pyoxipng callers that rely on the documented default color type
    fail instead of taking a compatibility path.

    Proposed fix: Match pyoxipng 9.1.1 constructor behavior in the
    compatibility layer. Add the stub overload and tests.

12. **pyoxipng `RawImage(..., bit_depth=...)` compatibility is missing.**

    Refs: [lib.rs](../../src/lib.rs:978),
    [lib.rs](../../src/lib.rs:991)

    Impact: Old callers using pyoxipng's `bit_depth` keyword are rejected.

    Proposed fix: Accept `bit_depth` only on the pyoxipng compatibility
    constructor path. Keep stable constructor rules separate.

13. **Old pyoxipng `RowFilter` names are absent.**

    Refs: [init.py](../../oxipng/__init__.py:114),
    [init.pyi](../../oxipng/__init__.pyi:68)

    Impact: Code using names such as `RowFilter.NoOp`, `RowFilter.MinSum`, or
    `RowFilter.BigEnt` gets `AttributeError`.

    Proposed fix: Add pyoxipng 9.1.1 enum aliases in the compatibility layer.
    Emit `DeprecationWarning`.

14. **Old pyoxipng `StripChunks.none()`, `safe()`, and `all()` factories are absent.**

    Refs: [init.py](../../oxipng/__init__.py:45)

    Impact: Calls such as `StripChunks.safe()` fail because the current names
    are enum members, not old factory methods.

    Proposed fix: Add pyoxipng factory compatibility without weakening the
    stable enum API. Emit `DeprecationWarning`.

## Medium

1. **File APIs are symlink and time-of-check/time-of-use sensitive.**

   Refs: [lib.rs](../../src/lib.rs:586),
   [lib.rs](../../src/lib.rs:623),
   [lib.rs](../../src/lib.rs:649)

   Impact: Services that pass caller-controlled paths may read or overwrite
   unintended files in shared writable directories.

   Proposed fix: Document private work directories and sanitized file names.
   Consider stronger file-open controls where practical.

2. **The wheel smoke step installs live PyPI dependencies.**

   Refs: [wheels.yml](../../.github/workflows/wheels.yml:84),
   [pyproject.toml](../../pyproject.toml:38)

   Impact: Release jobs can flake or execute unpinned dependency install code
   before artifact upload.

   Proposed fix: Use a locked smoke environment or install only from a pinned
   constraints file.

3. **No source distribution is built or published, while docs mention sdists.**

   Refs: [release-artifacts.md](../process/release-artifacts.md:6),
   [build-from-source.md](../usage/build-from-source.md:11),
   [build-from-source.md](../usage/build-from-source.md:46)

   Impact: Unsupported platforms do not have a normal PyPI source-install path
   yet, but docs discuss one.

   Proposed fix: Either add tested sdist publishing or mark sdist install docs
   as future work.

4. **Release artifact verification checks filenames more than wheel contents.**

   Refs: [verify_release_artifacts.py](../../scripts/verify_release_artifacts.py:43)

   Impact: The final publish gate can miss invalid wheel ZIPs, metadata,
   license files, typing files, or native extension layout.

   Proposed fix: Open each wheel and verify `METADATA`, `RECORD`, license
   files, `py.typed`, stubs, and extension layout.

5. **Workflow tests use substring checks.**

   Refs: [test_workflows.py](../../tests/test_workflows.py:27),
   [test_workflows.py](../../tests/test_workflows.py:55),
   [test_workflows.py](../../tests/test_workflows.py:110)

   Impact: Comments or unrelated steps can satisfy tests while workflow
   behavior changes.

   Proposed fix: Parse YAML and assert job permissions, `needs`, steps,
   conditions, and action refs structurally.

6. **Dependency refresh classification can miss duplicate Cargo package names.**

   Refs: [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py:65),
   [deny.toml](../../deny.toml:18)

   Impact: If two versions of the same crate appear, one overwrites the other.
   A runtime or build dependency change can be missed.

   Proposed fix: Key Cargo lock packages by name, version, and source. Treat
   duplicate names as distinct packages.

7. **`api-matrix` does not use locked Python sync.**

   Refs: [api-matrix.yml](../../.github/workflows/api-matrix.yml:29)

   Impact: Python compatibility jobs can resolve a different dev environment
   from the committed lockfile.

   Proposed fix: Use `uv sync --locked --group dev`.

8. **Upstream bump and dependency health sync unlocked dependencies.**

   Refs: [dependency-health.yml](../../.github/workflows/dependency-health.yml:38),
   [upstream-bump.yml](../../.github/workflows/upstream-bump.yml:32)

   Impact: Automation can test with dependency versions that differ from the
   checked-in lock state.

   Proposed fix: Use unlocked sync only when intentionally refreshing. Use
   locked sync after lockfiles are updated.

9. **Docs conflict on release readiness.**

   Refs: [README.md](../../README.md:14),
   [release-artifacts.md](../process/release-artifacts.md:3),
   [wheels.yml](../../.github/workflows/wheels.yml:110)

   Impact: Users and maintainers get mixed signals about whether PyPI publish is
   active.

   Proposed fix: Make the docs match the current release state.

10. **Merge policy docs conflict.**

    Refs: [CONTRIBUTING.md](../../CONTRIBUTING.md:112),
    [upstream-bumps.md](../process/upstream-bumps.md:91),
    [upstream-bump.yml](../../.github/workflows/upstream-bump.yml:167)

    Impact: Maintainers may configure branch protection or merge PRs in a way
    that fights automation.

    Proposed fix: Pick one merge policy. Update all docs and workflow tests to
    match it.

11. **Auto-merge safety depends on settings that are not checked in.**

    Refs: [dependency-health.yml](../../.github/workflows/dependency-health.yml:124),
    [upstream-bump.yml](../../.github/workflows/upstream-bump.yml:160)

    Impact: Branch protection and required checks are part of the safety model,
    but the repo has no machine-readable policy file for them.

    Proposed fix: Document required GitHub settings in one process doc. Add a
    `gh`-based audit script if the settings must be enforced by CI.

12. **Action and pre-commit dependency health is not automated.**

    Refs: no `dependabot` or `renovate` config is tracked.

    Impact: Workflow actions and hook revisions can age without scheduled
    review.

    Proposed fix: Add Dependabot or Renovate for GitHub Actions and pre-commit
    sources.

13. **Upstream bump can race GitHub releases and crates.io.**

    Refs: [bump_upstream.py](../../scripts/bump_upstream.py:53),
    [bump_upstream.py](../../scripts/bump_upstream.py:95)

    Impact: If upstream creates a GitHub release before publishing the crate,
    the scheduled workflow fails.

    Proposed fix: Check crates.io availability before updating files. Treat a
    missing crate as a clean no-op or retryable state.

14. **`FilterStrategy.predefined()` accepts unordered collections.**

    Refs: [init.py](../../oxipng/__init__.py:102),
    [options-surface.md](../architecture/options-surface.md:46)

    Impact: Sets and frozensets can change filter order. That can affect output
    size or runtime.

    Proposed fix: For stable API, accept ordered collections and general
    iterables where order is preserved. Keep exact pyoxipng behavior only in
    explicit compatibility paths.

15. **Filter type annotations allow invalid nested predefined filters.**

    Refs: [init.pyi](../../oxipng/__init__.pyi:97),
    [init.pyi](../../oxipng/__init__.pyi:170)

    Impact: `filter=[FilterStrategy.predefined(...)]` type-checks but runtime
    rejects it.

    Proposed fix: Split scalar filter types from whole-option filter types in
    the stub.

16. **pyoxipng palette compatibility is narrower than pyoxipng.**

    Refs: [lib.rs](../../src/lib.rs:841),
    [init.pyi](../../oxipng/__init__.pyi:80)

    Impact: pyoxipng examples that use list palette entries fail when this
    wrapper requires tuple entries.

    Proposed fix: Accept pyoxipng list entries only through the compatibility
    path. Keep stable palette rules explicit.

## Minor

1. **Memory APIs copy untrusted data before limits can help.**

   Refs: [lib.rs](../../src/lib.rs:81),
   [lib.rs](../../src/lib.rs:1151),
   [untrusted-input.md](../usage/untrusted-input.md:44)

   Impact: Very large byte streams can exhaust memory before
   `max_decompressed_size` applies.

   Proposed fix: Document caller-side byte limits. Parse options before copying
   when possible.

2. **`backup=True` masks missing input as generic `OSError`.**

   Refs: [lib.rs](../../src/lib.rs:586),
   [lib.rs](../../src/lib.rs:637)

   Impact: Caller error handling differs from normal optimize mode, which maps
   missing files to `FileNotFoundError`.

   Proposed fix: Map `NotFound` during backup to `FileNotFoundError`.

3. **`backup=True` can leave partial backup files.**

   Refs: [lib.rs](../../src/lib.rs:586)

   Impact: If copying fails after `create_new`, a retry may raise
   `FileExistsError` for a partial `.bak` file.

   Proposed fix: Copy to a temporary sibling file, flush it, then rename it into
   place.

4. **Docs warn about untrusted PNG data, but not untrusted paths.**

   Refs: [untrusted-input.md](../usage/untrusted-input.md:27),
   [lib.rs](../../src/lib.rs:623)

   Impact: Upload examples may lead callers to pass raw user paths into file
   APIs.

   Proposed fix: Add a short path-safety section. Recommend private temp
   directories and generated file names.

5. **`max_decompressed_size` has inconsistent exception types for huge ints.**

   Refs: [lib.rs](../../src/lib.rs:137),
   [lib.rs](../../src/lib.rs:148)

   Impact: Very large Python integers can raise `TypeError`, while smaller
   out-of-range integers raise `ValueError`.

   Proposed fix: Extract Python integers in a way that preserves integer type
   errors, then map range failures to `ValueError`.

6. **Enum `.value` extraction can accept bool-like values.**

   Refs: [lib.rs](../../src/lib.rs:685)

   Impact: A fake enum object with `.value = True` can be accepted as bit depth
   `1`.

   Proposed fix: Reject bools after enum `.value` extraction too.

7. **Chunk data is copied before chunk-name validation.**

   Refs: [lib.rs](../../src/lib.rs:1111)

   Impact: Invalid chunk names can still force a large data copy first.

   Proposed fix: Validate the chunk name before copying chunk payload data.

8. **`add_icc_profile` reports success if upstream drops the profile.**

   Refs: [lib.rs](../../src/lib.rs:1122)

   Impact: Callers cannot tell whether the ICC profile was attached.

   Proposed fix: Check whether upstream exposes success state. If not, document
   the limitation or validate enough input first to predict failure.

9. **Structured PNG chunk-name branch is effectively unreachable.**

   Refs: [lib.rs](../../src/lib.rs:780),
   [lib.rs](../../src/lib.rs:787)

   Impact: The validation branch is misleading and gives less precise errors
   than intended.

   Proposed fix: Reorder checks or remove the dead branch.

10. **Direct filter parsing accepts sets.**

    Refs: [lib.rs](../../src/lib.rs:403)

    Impact: Set iteration can make filter order nondeterministic.

    Proposed fix: Prefer ordered inputs for sequence semantics. Reject sets if
    output stability matters.

11. **Deprecated enum warnings do not cover all lookup paths.**

    Refs: [pyoxipng compat.py](../../oxipng/_pyoxipng_compat.py:21)

    Impact: `RowFilter["none"]`, `RowFilter("none")`, and similar lookups can
    bypass `DeprecationWarning`.

    Proposed fix: Override enum lookup paths or test and document which paths
    are compatibility warnings.

12. **pyoxipng warning names do not match old pyoxipng names.**

    Refs: [init.py](../../oxipng/__init__.py:117)

    Impact: The warning set covers current lowercase aliases, not the old
    pyoxipng 9.1.1 names.

    Proposed fix: Base compatibility aliases and warning names on pyoxipng
    9.1.1.

13. **pyoxipng compatibility code leaks into the main facade.**

    Refs: [init.py](../../oxipng/__init__.py:3),
    [init.py](../../oxipng/__init__.py:14),
    [pyoxipng compat.py](../../oxipng/_pyoxipng_compat.py:1)

    Impact: Stable API behavior and compatibility behavior are harder to reason
    about.

    Proposed fix: Move pyoxipng-specific helpers into `_pyoxipng_compat.py`.
    Keep `__init__.py` focused on stable public names.

    Status: Addressed by the facade cleanup committed on this branch.

14. **Type aliases add typing clutter.**

    Refs: [init.py](../../oxipng/__init__.py:5)

    Impact: No runtime bug. The facade is harder to read.

    Proposed fix: Remove dead type aliases or move shared typing to the stub.

15. **`CompatColorType` is frozen but can contain a mutable palette.**

    Refs: [pyoxipng compat.py](../../oxipng/_pyoxipng_compat.py:37)

    Impact: Callers can mutate the palette after creating the descriptor.

    Proposed fix: Normalize palette values to tuples when the descriptor is
    created.

16. **Compatibility object detection trusts module and qualname strings.**

    Refs: [lib.rs](../../src/lib.rs:173)

    Impact: A fake object can look like a compatibility object. Values are still
    validated, so this is hardening rather than a known exploit.

    Proposed fix: Import and check real helper classes, or add a private marker
    that is hard to spoof.

17. **`classify_dependency_refresh.py` uses unresolved executables.**

    Refs: [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py:36),
    [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py:93)

    Impact: Local or CI `PATH` hijacking is possible in weaker environments.

    Proposed fix: Use the same executable resolver pattern as
    `bump_upstream.py`.

18. **`classify_dependency_refresh.py` does not validate GitHub output values.**

    Refs: [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py:162),
    [bump_upstream.py](../../scripts/bump_upstream.py:119)

    Impact: Future output values with newlines could corrupt GitHub Actions
    output.

    Proposed fix: Reuse the newline guard from `bump_upstream.py`.

19. **The upstream scanner uses regex and raw brace counting.**

    Refs: [scan_upstream_surface.py](../../scripts/scan_upstream_surface.py:34)

    Impact: Rust comments, docs, or strings with braces can create false API
    drift reports.

    Proposed fix: Use a Rust parser or make the scanner more syntax-aware.

20. **The upstream scanner only sees plain `pub fn`.**

    Refs: [scan_upstream_surface.py](../../scripts/scan_upstream_surface.py:95)

    Impact: It can miss `pub const fn`, `pub async fn`, or future public forms.

    Proposed fix: Extend parsing for valid public function forms or use a Rust
    parser.

21. **`ai_filter_log.py` reads the whole log.**

    Refs: [ai_filter_log.py](../../scripts/ai_filter_log.py:23)

    Impact: Very large logs use avoidable memory.

    Proposed fix: Stream the tail with a bounded buffer.

22. **`cargo-deny` version is not enforced when already installed.**

    Refs: [Makefile](../../Makefile:35)

    Impact: Local `make dependency-audit` can use a stale policy engine.

    Proposed fix: Check the installed version. Install the pinned version when
    it differs.

23. **Local bootstrap uses curl-to-shell.**

    Refs: [Makefile](../../Makefile:28),
    [test_makefile.py](../../tests/test_makefile.py:22)

    Impact: This is a developer supply-chain trust point. It is not used by CI.

    Proposed fix: Keep it only if this convenience tradeoff is intentional.
    Document that `make setup` runs the rustup shell installer.

24. **Retry workflow can spend extra CI minutes.**

    Refs: [retry-failed-checks.yml](../../.github/workflows/retry-failed-checks.yml:12),
    [retry-failed-checks.yml](../../.github/workflows/retry-failed-checks.yml:19)

    Impact: Failed PR checks get one extra run. The workflow does not checkout
    code or expose secrets, so token risk is low.

    Proposed fix: Keep the one-retry limit. Consider scoping retries to trusted
    branches if CI cost becomes a problem.

25. **`make upgrade-deps` uses unlocked sync after updates.**

    Refs: [Makefile](../../Makefile:143)

    Impact: The command can move the environment again after lockfile updates.

    Proposed fix: Use `uv sync --locked --group dev` after `uv lock --upgrade`.

## Checks That Passed

- `make dependency-audit` passed in the security review. `cargo deny` reported
  advisories, bans, licenses, and sources as OK. `uv audit --locked` found no
  known vulnerabilities.
- `cargo test --lib` passed in the Rust review.
- `cargo clippy --all-targets -- -D warnings` passed in the Rust review.
- `uv run --no-sync --group dev ruff check oxipng scripts` passed in the
  Python review.
- `uv run --no-sync --group dev basedpyright oxipng scripts` passed in the
  Python review.
- `uv lock --check` passed in the CI and release review.
- Workflow YAML parsed in the CI and release review.
- Targeted automation tests passed in the CI and release review.
- The full Python suite passed in the CI and release review.
- `cargo test --locked` passed in the CI and release review.
- No `pull_request_target`, PyPI password, or PyPI API token publishing secret
  was found.
- No production Rust `unwrap`, `expect`, `panic!`, `todo!`, or
  `unimplemented!` paths were found.
- No broad Python shell execution, network access, dynamic eval, or hidden file
  writes were found in the facade.

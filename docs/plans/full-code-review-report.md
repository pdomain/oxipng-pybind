# Full Code Review Report

This report tracks current findings from the Rust, Python API, security, CI,
release, and test review passes.

The original major findings are complete. See
[Major Review Fixes Implementation Plan](major-review-fixes-plan.md) for the
closed workstreams.

## Medium

1. **File APIs are symlink and time-of-check/time-of-use sensitive.**

   Refs: [lib.rs](../../src/lib.rs), [Untrusted Input](../usage/untrusted-input.md)

   Impact: Services that pass caller-controlled paths may read or overwrite
   unintended files in shared writable directories.

   Proposed fix: Document private work directories and sanitized file names.
   Consider stronger file-open controls where practical.

2. **The wheel smoke step installs live PyPI dependencies.**

   Refs: [wheels.yml](../../.github/workflows/wheels.yml),
   [pyproject.toml](../../pyproject.toml)

   Impact: Release jobs can flake or execute unpinned dependency install code
   before artifact upload.

   Proposed fix: Use a locked smoke environment or install only from a pinned
   constraints file.

3. **Source distribution docs are ahead of release support.**

   Refs: [Release Artifacts](../process/release-artifacts.md),
   [Build From Source](../usage/build-from-source.md)

   Impact: Unsupported platforms do not have a normal PyPI source-install path
   yet, but docs still mention installing from an sdist.

   Proposed fix: Publish tested sdists, or mark sdist install docs as future
   work.

4. **Release artifact verification checks filenames more than wheel contents.**

   Refs: [verify_release_artifacts.py](../../scripts/verify_release_artifacts.py)

   Impact: The final publish gate can miss invalid wheel ZIPs, metadata,
   license files, typing files, or native extension layout.

   Proposed fix: Open each wheel and verify `METADATA`, `RECORD`, license
   files, `py.typed`, stubs, and extension layout.

5. **Some workflow tests still use substring checks.**

   Refs: [test_workflows.py](../../tests/test_workflows.py)

   Impact: Comments or unrelated steps can satisfy tests while workflow
   behavior changes.

   Proposed fix: Parse YAML and assert job permissions, `needs`, steps,
   conditions, and action refs structurally.

6. **Dependency refresh classification can miss duplicate Cargo package names.**

   Refs: [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py),
   [deny.toml](../../deny.toml)

   Impact: If two versions of the same crate appear, one overwrites the other.
   A runtime or build dependency change can be missed.

   Proposed fix: Key Cargo lock packages by name, version, and source. Treat
   duplicate names as distinct packages.

7. **Hosted automation syncs unlocked Python dependencies in some jobs.**

   Refs: [api-matrix.yml](../../.github/workflows/api-matrix.yml),
   [dependency-health.yml](../../.github/workflows/dependency-health.yml),
   [upstream-bump.yml](../../.github/workflows/upstream-bump.yml),
   [Makefile](../../Makefile)

   Impact: Jobs can resolve a different dev environment from the committed or
   freshly updated lockfile.

   Proposed fix: Use `uv sync --locked --group dev` after lockfiles are in the
   desired state. Keep unlocked sync only where dependency refresh is intended.

8. **Docs conflict on release readiness.**

   Refs: [README.md](../../README.md),
   [Release Artifacts](../process/release-artifacts.md),
   [wheels.yml](../../.github/workflows/wheels.yml)

   Impact: Users and maintainers get mixed signals about whether PyPI publish is
   active.

   Proposed fix: Make README, release docs, and the workflow description match
   the current PyPI state.

9. **Merge policy docs conflict with automation.**

   Refs: [CONTRIBUTING.md](../../CONTRIBUTING.md),
   [Upstream Bumps](../process/upstream-bumps.md),
   [upstream-bump.yml](../../.github/workflows/upstream-bump.yml)

   Impact: Maintainers may configure branch protection or merge PRs in a way
   that fights automation.

   Proposed fix: Pick one merge policy. Update all docs and workflow tests to
   match it.

10. **Auto-merge safety depends on settings that are not checked in.**

    Refs: [dependency-health.yml](../../.github/workflows/dependency-health.yml),
    [upstream-bump.yml](../../.github/workflows/upstream-bump.yml),
    [Upstream Bumps](../process/upstream-bumps.md)

    Impact: Branch protection and required checks are part of the safety model,
    but the repo has no machine-readable policy file for them.

    Proposed fix: Document all required GitHub settings in one process doc. Add
    a `gh`-based audit script if CI must enforce those settings.

11. **Pre-commit dependency health is not automated.**

    Refs: [.pre-commit-config.yaml](../../.pre-commit-config.yaml),
    [dependabot.yml](../../.github/dependabot.yml)

    Impact: Hook revisions can age without scheduled review.

    Proposed fix: Add Dependabot or Renovate updates for pre-commit sources.

12. **Upstream bump can race GitHub releases and crates.io.**

    Refs: [bump_upstream.py](../../scripts/bump_upstream.py)

    Impact: If upstream creates a GitHub release before publishing the crate,
    the scheduled workflow fails.

    Proposed fix: Check crates.io availability before updating files. Treat a
    missing crate as a clean no-op or retryable state.

13. **`FilterStrategy.predefined()` accepts unordered collections.**

    Refs: [init.py](../../oxipng/__init__.py),
    [Options Surface](../architecture/options-surface.md)

    Impact: Sets and frozensets can change filter order. That can affect output
    size or runtime.

    Proposed fix: For stable API, accept ordered collections and general
    iterables where order is preserved. Keep exact pyoxipng behavior only in
    explicit compatibility paths.

14. **Filter type annotations allow invalid nested predefined filters.**

    Refs: [init.pyi](../../oxipng/__init__.pyi)

    Impact: `filter=[FilterStrategy.predefined(...)]` type-checks but runtime
    rejects it.

    Proposed fix: Split scalar filter types from whole-option filter types in
    the stub.

15. **pyoxipng palette compatibility is narrower than pyoxipng.**

    Refs: [lib.rs](../../src/lib.rs), [init.pyi](../../oxipng/__init__.pyi)

    Impact: pyoxipng examples that use list palette entries fail when this
    wrapper requires tuple entries.

    Proposed fix: Accept pyoxipng list entries only through the compatibility
    path. Keep stable palette rules explicit.

## Minor

1. **Memory APIs copy untrusted data before limits can help.**

   Refs: [lib.rs](../../src/lib.rs), [Untrusted Input](../usage/untrusted-input.md)

   Impact: Very large byte streams can exhaust memory before
   `max_decompressed_size` applies.

   Proposed fix: Document caller-side byte limits. Parse options before copying
   when possible.

2. **`backup=True` masks missing input as generic `OSError`.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: Caller error handling differs from normal optimize mode, which maps
   missing files to `FileNotFoundError`.

   Proposed fix: Map `NotFound` during backup to `FileNotFoundError`.

3. **`backup=True` can leave partial backup files.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: If copying fails after `create_new`, a retry may raise
   `FileExistsError` for a partial `.bak` file.

   Proposed fix: Copy to a temporary sibling file, flush it, then rename it into
   place.

4. **`max_decompressed_size` has inconsistent exception types for huge ints.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: Very large Python integers can raise `TypeError`, while smaller
   out-of-range integers raise `ValueError`.

   Proposed fix: Extract Python integers in a way that preserves integer type
   errors, then map range failures to `ValueError`.

5. **Enum `.value` extraction can accept bool-like values.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: A fake enum object with `.value = True` can be accepted as bit depth
   `1`.

   Proposed fix: Reject bools after enum `.value` extraction too.

6. **Chunk data is copied before chunk-name validation.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: Invalid chunk names can still force a large data copy first.

   Proposed fix: Validate the chunk name before copying chunk payload data.

7. **`add_icc_profile` reports success if upstream drops the profile.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: Callers cannot tell whether the ICC profile was attached.

   Proposed fix: Check whether upstream exposes success state. If not,
   document the limitation or validate enough input first to predict failure.

8. **Structured PNG chunk-name branch is effectively unreachable.**

   Refs: [lib.rs](../../src/lib.rs)

   Impact: The validation branch is misleading and gives less precise errors
   than intended.

   Proposed fix: Reorder checks or remove the dead branch.

9. **Direct filter parsing accepts sets.**

   Refs: [lib.rs](../../src/lib.rs), [init.pyi](../../oxipng/__init__.pyi)

   Impact: Set iteration can make filter order nondeterministic.

   Proposed fix: Prefer ordered inputs for sequence semantics. Reject sets if
   output stability matters.

10. **Deprecated enum warnings do not cover all lookup paths.**

    Refs: [pyoxipng compat.py](../../oxipng/_pyoxipng_compat.py),
    [init.py](../../oxipng/__init__.py)

    Impact: `RowFilter["none"]`, `RowFilter("none")`, and similar lookups can
    bypass `DeprecationWarning`.

    Proposed fix: Override enum lookup paths, or test and document which paths
    are compatibility warnings.

11. **`CompatColorType` is frozen but can contain a mutable palette.**

    Refs: [pyoxipng compat.py](../../oxipng/_pyoxipng_compat.py)

    Impact: Callers can mutate the palette after creating the descriptor.

    Proposed fix: Normalize palette values to tuples when the descriptor is
    created.

12. **Compatibility object detection trusts module and qualname strings.**

    Refs: [lib.rs](../../src/lib.rs)

    Impact: A fake object can look like a compatibility object. Values are still
    validated, so this is hardening rather than a known exploit.

    Proposed fix: Import and check real helper classes, or add a private marker
    that is hard to spoof.

13. **`classify_dependency_refresh.py` uses unresolved executables.**

    Refs: [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py)

    Impact: Local or CI `PATH` hijacking is possible in weaker environments.

    Proposed fix: Use the same executable resolver pattern as
    `bump_upstream.py`.

14. **`classify_dependency_refresh.py` does not validate GitHub output values.**

    Refs: [classify_dependency_refresh.py](../../scripts/classify_dependency_refresh.py),
    [bump_upstream.py](../../scripts/bump_upstream.py)

    Impact: Future output values with newlines could corrupt GitHub Actions
    output.

    Proposed fix: Reuse the newline guard from `bump_upstream.py`.

15. **The upstream scanner uses regex and raw brace counting.**

    Refs: [scan_upstream_surface.py](../../scripts/scan_upstream_surface.py)

    Impact: Rust comments, docs, or strings with braces can create false API
    drift reports.

    Proposed fix: Use a Rust parser or make the scanner more syntax-aware.

16. **The upstream scanner only sees plain `pub fn`.**

    Refs: [scan_upstream_surface.py](../../scripts/scan_upstream_surface.py)

    Impact: It can miss `pub const fn`, `pub async fn`, or future public forms.

    Proposed fix: Extend parsing for valid public function forms or use a Rust
    parser.

17. **`ai_filter_log.py` reads the whole log.**

    Refs: [ai_filter_log.py](../../scripts/ai_filter_log.py)

    Impact: Very large logs use avoidable memory.

    Proposed fix: Stream the tail with a bounded buffer.

18. **`cargo-deny` version is not enforced when already installed.**

    Refs: [Makefile](../../Makefile)

    Impact: Local `make dependency-audit` can use a stale policy engine.

    Proposed fix: Check the installed version. Install the pinned version when
    it differs.

19. **Retry workflow can spend extra CI minutes.**

    Refs: [retry-failed-checks.yml](../../.github/workflows/retry-failed-checks.yml)

    Impact: Failed PR checks get one extra run. The workflow does not checkout
    code or expose secrets, so token risk is low.

    Proposed fix: Keep the one-retry limit. Consider scoping retries to trusted
    branches if CI cost becomes a problem.

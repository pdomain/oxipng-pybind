# Full Code Review Report

This report tracks current findings from the Rust, Python API, security, CI,
release, and test review passes.

## Closed Findings

### Major

The original 14 major findings are complete. See
[Major Review Fixes Plan](major-review-fixes-plan.md) for the closed workstream
summary.

### Medium

The 15 medium findings are complete. See
[Medium Review Fixes Plan](medium-review-fixes-plan.md) for the interactive
review decisions and implementation summary.

Closed medium work covered:

- untrusted file-path documentation;
- pinned wheel smoke dependencies;
- tested sdist support;
- wheel and sdist content verification;
- structural workflow tests;
- duplicate Cargo package classification;
- locked hosted automation syncs;
- PyPI release readiness docs;
- rebase-only merge policy;
- GitHub settings documentation and audit helper;
- pre-commit dependency refresh automation;
- crates.io availability handling for upstream bumps;
- ordered predefined filter inputs;
- filter type annotations; and
- ordered palette-entry compatibility.

## Remaining Minor Findings

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

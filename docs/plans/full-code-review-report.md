# Full Code Review Report

This report tracks closed findings from the Rust, Python API, security, CI,
release, and test review passes. The major, medium, and minor review findings
are closed.

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

### Minor

The 19 minor findings are closed. See
[Minor Review Fixes Implementation Plan](minor-review-fixes-plan.md) for the
task-by-task implementation record.

Closed minor work covered:

- memory input option validation before buffer extraction where practical;
- missing backup input mapping to `FileNotFoundError`;
- direct backup writes preserved as upstream Rust behavior, with docs covering
  partial `.bak` risk after interruption;
- consistent `max_decompressed_size` range and type errors;
- bool rejection after enum `.value` extraction;
- PNG chunk-name validation before payload extraction;
- ICC profile attachment documented as a limitation because upstream does not
  expose a separate runtime success status;
- chunk-name validation simplification for the unreachable structured branch;
- ordered stable filter inputs, while pyoxipng compatibility still accepts sets
  with warnings;
- deprecated pyoxipng enum lookup warnings;
- immutable tuple snapshots for compatibility palettes;
- private marker checks for compatibility objects;
- resolved `git` and `cargo` executable paths in dependency classification;
- newline guards for GitHub output names and values;
- rustdoc JSON upstream API scanning instead of a custom parser;
- rustdoc JSON coverage for public `fn`, `const fn`, and `async fn`;
- bounded-memory AI log streaming;
- pinned `cargo-deny` bootstrap enforcement; and
- bounded one-time retry workflow retained with no code change because it does
  not checkout code, expose secrets, or expand permissions.

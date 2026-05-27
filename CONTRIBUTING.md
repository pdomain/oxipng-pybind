# Contributing

Thanks for improving `oxipng-pybind`.

This project is a Python wrapper around upstream Rust `oxipng`. It aims to be
a drop-in replacement for `pyoxipng`, with a stable Python API.

## Before you start

Read these files first:

- `README.md`
- `CONVENTIONS.md`
- `docs/README.md`

`CLAUDE.md` is only for AI coding agents.

When writing docs or user-facing text, also read
`docs/process/writing-style.md`.

Check `docs/plans/unfinished-work.md` before large changes.

## Setup

Install the pinned Rust toolchain, Python dependencies, editable extension, and
Git hooks:

```bash
make setup
```

`make setup` is the normal first command for local work. It checks `uv.lock`,
syncs locked Python dev dependencies, builds the editable `_oxipng` extension,
and installs Git hooks. It also installs the pinned Rust toolchain and
`cargo-deny` if they are missing.

## Common checks

Use Make targets when possible.

```bash
make test
make lint
make typecheck
make dependency-audit
make ci
```

For focused Python tests, rebuild the extension first:

```bash
make develop
uv run --no-sync --group dev pytest tests/test_api.py -q
```

Do not use bare `python -m pytest`. The tests need the project environment and
the compiled extension.

## Code changes

Keep changes small and focused.

Preserve the stable API unless the active plan says otherwise. Add tests for
new behavior. Update docs when user-facing behavior changes.

Use predictable errors:

- Caller mistakes raise standard Python exceptions.
- PNG decode and optimization failures raise `PngError`.

## Dependency changes

This repo has Rust and Python lockfiles.

Use:

```bash
make upgrade-deps
make dependency-refresh-check
```

Dependency refreshes are classified as `release-needed` or `no-release-needed`.
Runtime and published artifact changes usually need release review.

Update third-party notice tooling or `THIRD_PARTY_NOTICES.md` when shipped
dependencies change.

## Release changes

Release wheels target Python 3.11+ ABI3.

Publishing uses PyPI Trusted Publishing from GitHub Actions. Do not add PyPI
password or API-token secrets.

Before release work, read:

- `docs/process/release-artifacts.md`
- `docs/process/upstream-bumps.md`
- `docs/process/dependency-health.md`

## Pull requests

Before asking for review, run:

```bash
make ci
```

If the change touches release, wheel, or dependency automation, also run the
focused tests for that area.

Use merge commits. Do not squash unless the maintainer explicitly asks for it.

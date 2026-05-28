# Contributing

Thanks for improving `oxipng-pybind`.

This project is a Python wrapper around upstream Rust `oxipng`. It aims to be
a drop-in replacement for `pyoxipng`, with a stable Python API.

## Before you start

Read these files first:

- [README](README.md)
- [Conventions](CONVENTIONS.md)
- [Docs index](docs/README.md)

`CLAUDE.md` is only for AI coding agents.

When writing docs or user-facing text, also read
[Writing Style](docs/process/writing-style.md).

Check [Unfinished Work](docs/plans/unfinished-work.md) before large changes.

## Setup

Run the normal setup before local work:

```bash
make setup
```

See [Local Development](docs/process/local-development.md) for setup details,
editable extension rules, and focused test commands.

## Common checks

Use Make targets when possible. Run focused checks while you work, then run
the full CI gate before review:

```bash
make ci
```

Do not use bare `python -m pytest`. Python tests need the project environment
and the compiled extension.

## Code changes

Keep changes small and focused. Add tests for new behavior. Update docs when
user-facing behavior changes.

Follow [Conventions](CONVENTIONS.md) for API stability, upstream `oxipng`
boundaries, predictable errors, release artifacts, dependency refreshes, and
license rules.

## Dependency changes

This repo has Rust and Python lockfiles. For dependency work, run:

```bash
make upgrade-deps
make dependency-refresh-check
```

Follow [Dependency Health](docs/process/dependency-health.md) for refresh
classification, audit handling, and notice updates.

## Release changes

Release wheels target Python 3.10+ ABI3. Publishing uses PyPI Trusted
Publishing from GitHub Actions. Do not add PyPI password or API-token secrets.

Before release work, read [Release Artifacts](docs/process/release-artifacts.md)
and [Rust oxipng updates](docs/process/upstream-bumps.md).

## Pull requests

Before asking for review, run `make ci`. If the change touches release, wheel,
or dependency automation, also run the focused checks for that area.

For PRs, pull the branch, rebase it on current `main`, then use a rebase merge
after required checks pass. Do not squash unless the maintainer explicitly asks
for it.

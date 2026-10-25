---
kind: process
status: active
last_verified: 2026-10-25
---
# Local Development

Run setup before local work:

```bash
make setup
```

If `rustup` is missing, setup runs the official Rustup installer as a developer
convenience.

GitHub CI installs Rust before it runs `make ci`, so CI does not depend on
that local installer path.

## What make setup does

`make setup` installs the Rust and `cargo-deny` versions pinned in the
[`Makefile`](../../Makefile). It also:

- checks `uv.lock`
- syncs locked Python dependencies
- builds the editable native extension
- installs pre-commit hooks

Pre-commit tooling uses a separate Python 3.13 environment in
`.cache/pre-commit`. The project environment keeps its selected Python
version, including Python 3.10.

Hook installation is skipped in worktrees and when `core.hooksPath` is set.
Use `make pre-commit-check` to run the hooks in either case.

See the [`setup` target](../../Makefile) for the exact commands.

## Rebuilding the extension after Rust changes

Rebuild the compiled `_oxipng` extension after any Rust change, since
`oxipng-pybind` imports it:

```bash
make develop
```

Run focused Python tests with `--no-sync` after that rebuild:

```bash
uv run --no-sync --group dev pytest tests/test_optimize_memory_api.py -q
```

Keep `--no-sync` on focused pytest commands. Without it, `uv run --group dev`
can resync the environment and leave Python importing an older `_oxipng`
extension.

That stale import usually shows up as an `ImportError` for a symbol that
exists in current source.

## Choosing a test target

Use `make test-py` for the normal Python test gate. It rebuilds the extension
and runs pytest with `--no-sync`, branch coverage, `pytest-xdist`, and
`--cov-fail-under=60`.

Use `make coverage` when you need the same coverage gate plus an HTML report in
`htmlcov/`.

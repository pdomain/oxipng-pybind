# Local Development

Use `make setup` before local work.

If `rustup` is missing, setup runs the official Rustup installer as a developer
convenience.

GitHub CI installs Rust before it runs `make ci`.

That means CI does not depend on the local Rustup installer branch.

## Setup

`make setup` installs Rust `1.85.1` through `rustup`.

It installs `cargo-deny` with `cargo install --locked` if needed.

It also:

- checks `uv.lock`
- syncs locked Python dependencies
- builds the editable native extension
- installs pre-commit hooks

After Rust bootstrap, `make setup` runs:

```bash
uv lock --check
uv sync --locked --group dev --reinstall
make develop
uv run --group dev pre-commit install --install-hooks
uv run --group dev pre-commit install --hook-type commit-msg
```

## Editable Extension

`oxipng-pybind` imports a compiled `_oxipng` extension.

Rebuild it after Rust source changes:

```bash
make develop
```

Run focused Python tests with `--no-sync` after that rebuild:

```bash
uv run --no-sync --group dev pytest
```

Without `--no-sync`, `uv run --group dev` can resync the environment.

That can leave Python importing an older `_oxipng` extension.

This usually appears as an `ImportError` for a symbol that exists in current
source.

## Test Targets

`make test-py` rebuilds the extension and runs pytest with `--no-sync`.

It uses branch coverage, `pytest-xdist`, and `--cov-fail-under=80`.

`make coverage` runs the same coverage gate.

It also writes an HTML report to `htmlcov/`.

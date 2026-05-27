# Local Development

Use `make setup` before local work. If `rustup` is missing, project bootstrap
runs the official Rustup shell installer as a developer convenience. GitHub CI
installs Rust before running `make ci`, so CI does not depend on that local
bootstrap branch.

`make setup` installs Rust `1.85.1` through `rustup` and installs `cargo-deny`
through `cargo install --locked` if needed. It checks `uv.lock`, syncs locked
Python dependencies, builds the editable native extension, and installs
pre-commit hooks.

`make setup` runs:

```bash
uv lock --check
uv sync --locked --group dev --reinstall
uv run --group dev maturin develop
uv run --group dev pre-commit install --install-hooks
uv run --group dev pre-commit install --hook-type commit-msg
```

## Editable Extension

`oxipng-pybind` imports a compiled `_oxipng` extension. Rebuild it after Rust
source changes:

```bash
uv run --group dev maturin develop --quiet
```

Run Python tests with `--no-sync` after that rebuild:

```bash
uv run --no-sync --group dev pytest
```

Without `--no-sync`, `uv run --group dev` can resync the environment and leave
Python importing an older `_oxipng` extension. That usually appears as an
`ImportError` for a symbol that exists in the current source.

The `make test-py` and `make coverage` targets already rebuild the extension and
run pytest with `--no-sync`.

`make test-py` runs the Python test suite with branch coverage, `pytest-xdist`,
and `--cov-fail-under=80`.

`make coverage` runs the same coverage gate and writes an HTML report to
`htmlcov/`.

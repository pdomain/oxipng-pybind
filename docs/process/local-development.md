# Local Development

Use `make setup` before local work. It installs Python dependencies, builds the
editable native extension, and installs pre-commit hooks.

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

# Local Development

Run setup before local work:

```bash
make setup
```

If `rustup` is missing, setup runs the official Rustup installer as a developer
convenience. GitHub CI installs Rust before it runs `make ci`, so CI does not
depend on that local installer path.

## Setup

`make setup` installs Rust `1.96.0` and `cargo-deny` if needed. It also:

- checks `uv.lock`
- syncs locked Python dependencies
- builds the editable native extension
- installs pre-commit hooks

See the [`setup` target](../../Makefile) for the exact commands.

## Editable Extension

`oxipng-pybind` imports the compiled `_oxipng` extension. Rebuild it after Rust
changes:

```bash
make develop
```

Run focused Python tests with `--no-sync` after that rebuild:

```bash
uv run --no-sync --group dev pytest tests/test_optimize_memory_api.py -q
```

Keep `--no-sync` on focused pytest commands. Without it, `uv run --group dev`
can resync the environment and leave Python importing an older `_oxipng`
extension. This usually appears as an `ImportError` for a symbol that exists in
current source.

## Test Targets

Use `make test-py` for the normal Python test gate. It rebuilds the extension
and runs pytest with `--no-sync`, branch coverage, `pytest-xdist`, and
`--cov-fail-under=60`.

Use `make coverage` when you need the same coverage gate plus an HTML report in
`htmlcov/`.

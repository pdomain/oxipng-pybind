"""Tests for Makefile developer workflow guarantees."""

from pathlib import Path


def _target_body(makefile: str, target: str) -> str:
    start = makefile.index(f"\n{target}:")
    next_target = makefile.find("\n\n", start)
    return makefile[start:next_target]


def test_python_test_targets_preserve_editable_extension_after_build() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    for target in ("test-py", "coverage"):
        body = _target_body(makefile, target)

        assert "uv run --group dev maturin develop --quiet" in body
        assert "uv run --no-sync --group dev pytest" in body

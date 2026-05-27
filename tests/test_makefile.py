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


def test_bootstrap_preserves_rustup_shell_installer_for_developer_convenience() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "https://sh.rustup.rs | sh" in makefile
    assert "rustup-init" not in makefile
    assert "sha256sum -c" not in makefile


def test_github_ci_installs_rust_before_make_ci() -> None:
    workflow_dir = Path(".github/workflows")

    for workflow in workflow_dir.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        if "make ci" not in text:
            continue

        assert "dtolnay/rust-toolchain@" in text, workflow
        assert text.index("dtolnay/rust-toolchain@") < text.index("make ci"), workflow


def test_bootstrap_installs_cargo_deny_through_cargo_install() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "cargo install --locked cargo-deny" in makefile
    assert "tar -xzf" not in makefile
    assert 'find "$$tmp_dir"' not in makefile


def test_bootstrap_enforces_pinned_cargo_deny_version() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    bootstrap_body = _target_body(makefile, "bootstrap-rust")
    rust_deny_body = _target_body(makefile, "rust-deny")

    assert "CARGO_DENY_VERSION :=" in makefile
    assert 'cargo-deny --version | grep -Fqx "cargo-deny $(CARGO_DENY_VERSION)"' in bootstrap_body
    assert "cargo install --locked cargo-deny --version $(CARGO_DENY_VERSION)" in bootstrap_body
    assert "cargo-deny --version" not in rust_deny_body


def test_dependency_audit_includes_lockfile_python_audit() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "py-audit-lock:" in makefile
    assert "dependency-audit: rust-deny py-audit py-audit-lock" in makefile
    assert "uv audit --locked" in makefile
    assert "uv export --locked" not in makefile

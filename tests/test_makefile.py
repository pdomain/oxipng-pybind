"""Tests for Makefile developer workflow guarantees."""

import re
from pathlib import Path

from tests.helpers.workflows import RUST_TOOLCHAIN_VERSION

API_TEST_TARGETS = (
    "tests/test_api_surface.py",
    "tests/test_optimize_file_api.py",
    "tests/test_optimize_memory_api.py",
    "tests/test_option_validation.py",
    "tests/test_pyoxipng_compat.py",
    "tests/test_raw_image_api.py",
)
API_TEST_COMMAND = f"uv run --locked --group dev pytest {' '.join(API_TEST_TARGETS)} -v -ra"


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


def test_bootstrap_rust_version_matches_ci_toolchain() -> None:
    """Local bootstrap installs the same reviewed Rust toolchain CI uses.

    The pin must stay current with `RUST_TOOLCHAIN_VERSION`; drifting to an
    older toolchain breaks `make ci` when a pinned tool (for example
    cargo-deny) raises its minimum supported Rust version.
    """
    makefile = Path("Makefile").read_text(encoding="utf-8")
    match = re.search(r"(?m)^RUST_VERSION := (\S+)$", makefile)

    assert match is not None, "Makefile must define RUST_VERSION"
    assert match.group(1) == RUST_TOOLCHAIN_VERSION


def test_dependency_audit_includes_lockfile_python_audit() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "py-audit-lock:" in makefile
    assert "dependency-audit: rust-deny py-audit-lock" in makefile
    assert "uv audit --locked" in makefile
    assert "pip-audit" not in makefile
    assert "uv export --locked" not in makefile


def test_wheel_build_uses_locked_cargo_dependencies() -> None:
    """Wheel build commands use locked Cargo dependencies."""
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "maturin build --release --locked" in makefile


def test_refresh_actions_target_syncs_reviewed_allowlist() -> None:
    """`make refresh-actions` bumps pins and syncs the reviewed allowlist locally."""
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert (
        "refresh-actions: ## Refresh reviewed GitHub Action pins and sync the allowlist" in makefile
    )
    body = _target_body(makefile, "refresh-actions")

    assert "scripts/update_github_actions.py --sync-reviewed-refs" in body
    assert "tests/test_workflow_security.py" in body


def test_accept_refresh_pr_target_prepares_pr_but_stops_before_merge() -> None:
    """`make accept-refresh-pr` gets the PR green but leaves the merge to a human."""
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "accept-refresh-pr: ## " in makefile
    body = _target_body(makefile, "accept-refresh-pr")

    assert "git rebase origin/main" in body
    assert "scripts/update_github_actions.py --sync-reviewed-refs" in body
    # The target surfaces the merge command but never runs the merge itself.
    assert 'echo "  gh pr merge' in body
    assert "--auto" not in body


def test_makefile_has_local_api_matrix_target() -> None:
    """Local API matrix mirrors the supported Python and ABI feature lanes."""
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert (
        "api-matrix: ## Run focused public API tests on all supported Python versions" in makefile
    )
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert version in makefile
    assert "abi3-py310" in makefile
    assert "abi3-py311" in makefile
    assert "UV_PROJECT_ENV=.venv-api-{}" in makefile
    assert "uv sync --locked --group dev" in makefile
    assert API_TEST_COMMAND in makefile

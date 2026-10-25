"""Tests for Makefile developer workflow guarantees."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

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


@pytest.mark.skipif(not Path("/usr/bin/make").is_file(), reason="requires Make")
def test_pre_commit_tooling_keeps_selected_project_environment(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / ".nobackup").touch()
    uv = bin_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        + 'printf "%s|%s\\n" "$UV_PROJECT_ENVIRONMENT" "$*" >> "$UV_RECORD"\n'
        + 'if [ "$1" = "sync" ]; then mkdir -p "$UV_PROJECT_ENVIRONMENT"; fi\n',
        encoding="utf-8",
    )
    uv.chmod(0o755)
    project_env = tmp_path / "project-python310"
    record = tmp_path / "uv-record"

    subprocess.run(
        [
            "/usr/bin/make",
            "--no-print-directory",
            "md-lint",
            "pre-commit-check",
            "AI=",
        ],
        cwd=tmp_path,
        env=os.environ
        | {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "UV_PROJECT_ENVIRONMENT": str(project_env),
            "UV_RECORD": str(record),
            "MAKEFILES": str(Path("Makefile").resolve()),
        },
        check=True,
        capture_output=True,
        text=True,
    )

    calls = record.read_text(encoding="utf-8").splitlines()
    assert len(calls) == 3
    assert calls[0].startswith(f"{tmp_path / '.cache/pre-commit'}|sync --locked ")
    assert "--only-group lint" in calls[0]
    for call in calls[1:]:
        assert call.startswith(f"{project_env}|run --no-project --python ")
        assert str(tmp_path / ".cache/pre-commit/bin/pre-commit") in call
    assert calls[1].endswith("run markdownlint-cli2 --all-files")
    assert calls[2].endswith("run --all-files")


def test_wheel_build_uses_locked_cargo_dependencies() -> None:
    """Wheel build commands use locked Cargo dependencies."""
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "maturin build --release --locked" in makefile


def test_release_artifact_targets_use_uv_and_verify_both_formats() -> None:
    """Local release builds use uv and verify the wheel and sdist."""
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "build: release-artifacts" in makefile
    assert "sdist: ## Build Python source distribution" in makefile
    release_body = _target_body(makefile, "release-artifacts")
    wheel_body = _target_body(makefile, "wheel")
    sdist_body = _target_body(makefile, "sdist")
    verify_body = _target_body(makefile, "verify-release-artifacts")

    assert "$(MAKE) --no-print-directory wheel" in release_body
    assert "$(MAKE) --no-print-directory sdist" in release_body
    assert "$(MAKE) --no-print-directory verify-release-artifacts" in release_body
    assert "uv run --locked --group dev maturin build" in wheel_body
    assert "uv run --locked --group dev maturin sdist" in sdist_body
    assert "uv run --locked --group dev python scripts/verify_release_artifacts.py" in verify_body
    assert " pip " not in release_body + wheel_body + sdist_body + verify_body


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

"""Tests for dependency refresh release classification."""

import subprocess
from pathlib import Path

import pytest

from scripts import classify_dependency_refresh
from scripts.classify_dependency_refresh import CargoPackageKey, classify_refresh


def test_uv_lock_only_change_is_no_release_needed() -> None:
    """Python tooling lockfile churn does not require a package release."""
    classification = classify_refresh(
        {"uv.lock"},
        python_runtime_changed=False,
        cargo_runtime_packages=set(),
    )

    assert classification.release_needed is False
    assert classification.label == "no-release-needed"
    assert "tooling" in classification.reason


def test_runtime_cargo_lock_change_is_release_needed() -> None:
    """Cargo runtime graph changes affect built wheels."""
    package = CargoPackageKey(
        name="libdeflater",
        version="1.24.0",
        source="registry+https://github.com/rust-lang/crates.io-index",
    )

    classification = classify_refresh(
        {"Cargo.lock"},
        python_runtime_changed=False,
        cargo_runtime_packages={package},
    )

    assert classification.release_needed is True
    assert classification.label == "release-needed"
    assert "libdeflater@1.24.0" in classification.reason


def test_python_project_dependencies_change_is_release_needed() -> None:
    """Python runtime dependency metadata changes affect published installs."""
    classification = classify_refresh(
        {"pyproject.toml", "uv.lock"},
        python_runtime_changed=True,
        cargo_runtime_packages=set(),
    )

    assert classification.release_needed is True
    assert classification.label == "release-needed"
    assert "[project.dependencies]" in classification.reason


def test_cargo_toml_change_is_release_needed() -> None:
    """Cargo manifest changes are conservative release-affecting changes."""
    classification = classify_refresh(
        {"Cargo.toml"},
        python_runtime_changed=False,
        cargo_runtime_packages=set(),
    )

    assert classification.release_needed is True
    assert classification.label == "release-needed"


def test_duplicate_cargo_package_names_are_preserved_and_changed_independently() -> None:
    """Cargo.lock packages are keyed by name, version, and source."""
    old_lock = """
[[package]]
name = "windows-sys"
version = "0.52.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "old-52"

[[package]]
name = "windows-sys"
version = "0.59.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "old-59"
""".lstrip()
    new_lock = old_lock.replace('checksum = "old-52"', 'checksum = "new-52"').replace(
        'checksum = "old-59"', 'checksum = "new-59"'
    )

    packages = classify_dependency_refresh.cargo_lock_packages(new_lock)
    changed = classify_dependency_refresh.changed_cargo_lock_packages(old_lock, new_lock)

    first = CargoPackageKey(
        name="windows-sys",
        version="0.52.0",
        source="registry+https://github.com/rust-lang/crates.io-index",
    )
    second = CargoPackageKey(
        name="windows-sys",
        version="0.59.0",
        source="registry+https://github.com/rust-lang/crates.io-index",
    )
    assert set(packages) == {first, second}
    assert changed == {first, second}


def test_duplicate_cargo_package_versions_classify_independently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime classification keeps duplicate package names separate."""
    first = CargoPackageKey(
        name="windows-sys",
        version="0.52.0",
        source="registry+https://github.com/rust-lang/crates.io-index",
    )
    second = CargoPackageKey(
        name="windows-sys",
        version="0.59.0",
        source="registry+https://github.com/rust-lang/crates.io-index",
    )

    def reaches_shipped_graph(package: CargoPackageKey) -> bool:
        return package == second

    monkeypatch.setattr(
        classify_dependency_refresh,
        "cargo_package_reaches_shipped_graph",
        reaches_shipped_graph,
    )

    classification = classify_dependency_refresh.classify_refresh_from_changes(
        {"Cargo.lock"},
        python_runtime_changed=False,
        changed_cargo_packages={first, second},
    )

    assert classification.release_needed is True
    assert "windows-sys@0.59.0" in classification.reason
    assert "windows-sys@0.52.0" not in classification.reason


def test_inverse_cargo_tree_uses_precise_package_spec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inverse cargo tree calls include source, name, and version."""
    calls: list[list[str]] = []
    package = CargoPackageKey(
        name="windows-sys",
        version="0.59.0",
        source="registry+https://github.com/rust-lang/crates.io-index",
    )

    class Result:
        returncode: int = 0
        stdout: str = "oxipng-pybind v10.1.1\n"

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> Result:
        calls.append(command)
        assert cwd == classify_dependency_refresh.ROOT
        assert check is False
        assert capture_output is True
        assert text is True
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert classify_dependency_refresh.cargo_package_reaches_shipped_graph(package) is True
    assert calls == [
        [
            "cargo",
            "tree",
            "--locked",
            "--edges",
            "normal,build",
            "-i",
            "registry+https://github.com/rust-lang/crates.io-index#windows-sys@0.59.0",
        ]
    ]


@pytest.mark.parametrize(
    "files",
    [
        {".pre-commit-config.yaml"},
        {".pre-commit-config.yaml", "README.md", "docs/process/dependency-health.md"},
    ],
)
def test_pre_commit_and_formatting_only_refreshes_are_no_release_needed(
    files: set[str],
) -> None:
    """Hook and formatting-only refreshes do not affect published artifacts."""
    classification = classify_refresh(
        files,
        python_runtime_changed=False,
        cargo_runtime_packages=set(),
    )

    assert classification.release_needed is False
    assert classification.label == "no-release-needed"
    assert "No published runtime dependency changes" in classification.reason

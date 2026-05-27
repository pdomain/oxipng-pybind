#!/usr/bin/env python3
"""Classify dependency refreshes by published-artifact impact."""

from __future__ import annotations

import argparse
import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, order=True)
class CargoPackageKey:
    """Stable Cargo.lock package identity."""

    name: str
    version: str
    source: str | None = None

    @property
    def display(self) -> str:
        """Return a stable display string for reports."""
        if self.source:
            return f"{self.name}@{self.version} ({self.source})"
        return f"{self.name}@{self.version}"

    @property
    def package_spec(self) -> str:
        """Return a precise Cargo package ID spec."""
        if self.source:
            return f"{self.source}#{self.name}@{self.version}"
        return f"{self.name}@{self.version}"


@dataclass(frozen=True)
class Classification:
    """Dependency refresh release classification."""

    release_needed: bool
    label: str
    reason: str


CargoRuntimePackage = CargoPackageKey | str


def run_stdout(command: list[str], *, cwd: Path = ROOT, check: bool = True) -> str:
    """Run a command and return stdout."""
    result = subprocess.run(  # noqa: S603
        command, cwd=cwd, check=check, capture_output=True, text=True
    )
    return result.stdout


def changed_files(base_ref: str) -> set[str]:
    """Return file paths changed relative to the base ref."""
    output = run_stdout(["git", "diff", "--name-only", base_ref, "--"])
    return {line for line in output.splitlines() if line}


def git_file_at_ref(path: str, ref: str) -> str:
    """Return file contents at a git ref."""
    return run_stdout(["git", "show", f"{ref}:{path}"])


def pyproject_runtime_dependencies(pyproject_text: str) -> list[str]:
    """Return normalized project runtime dependency strings."""
    document = tomllib.loads(pyproject_text)
    project = cast("dict[str, Any]", document.get("project", {}))
    raw_dependencies = project.get("dependencies", [])
    if not isinstance(raw_dependencies, list):
        return []
    dependencies = cast("list[object]", raw_dependencies)
    return sorted(str(dependency) for dependency in dependencies if isinstance(dependency, str))


def runtime_python_dependencies_changed(base_ref: str) -> bool:
    """Return whether project runtime Python dependencies changed."""
    old_dependencies = pyproject_runtime_dependencies(git_file_at_ref("pyproject.toml", base_ref))
    new_dependencies = pyproject_runtime_dependencies(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    return old_dependencies != new_dependencies


def cargo_lock_package_key(package: dict[str, Any]) -> CargoPackageKey | None:
    """Return a Cargo package key for a parsed Cargo.lock package table."""
    name = package.get("name")
    version = package.get("version")
    source = package.get("source")
    if not isinstance(name, str) or not isinstance(version, str):
        return None
    return CargoPackageKey(
        name=name,
        version=version,
        source=source if isinstance(source, str) else None,
    )


def cargo_lock_packages(lock_text: str) -> dict[CargoPackageKey, dict[str, Any]]:
    """Return Cargo.lock package tables keyed by name, version, and source."""
    document = tomllib.loads(lock_text)
    raw_packages = document.get("package", [])
    if not isinstance(raw_packages, list):
        return {}
    packages = cast("list[object]", raw_packages)
    by_key: dict[CargoPackageKey, dict[str, Any]] = {}
    for package in packages:
        if not isinstance(package, dict):
            continue
        package_data = cast("dict[str, Any]", package)
        key = cargo_lock_package_key(package_data)
        if key is not None:
            by_key[key] = package_data
    return by_key


def changed_cargo_lock_packages(old_lock: str, new_lock: str) -> set[CargoPackageKey]:
    """Return Cargo packages whose locked metadata changed."""
    old_packages = cargo_lock_packages(old_lock)
    new_packages = cargo_lock_packages(new_lock)
    package_keys = set(old_packages) | set(new_packages)
    return {key for key in package_keys if old_packages.get(key) != new_packages.get(key)}


def changed_workspace_cargo_lock_packages(base_ref: str) -> set[CargoPackageKey]:
    """Return Cargo packages changed in the workspace relative to a base ref."""
    return changed_cargo_lock_packages(
        git_file_at_ref("Cargo.lock", base_ref),
        (ROOT / "Cargo.lock").read_text(encoding="utf-8"),
    )


def cargo_package_reaches_shipped_graph(package: CargoPackageKey) -> bool:
    """Return whether a Cargo package reaches this crate's normal/build graph."""
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "cargo",
            "tree",
            "--locked",
            "--edges",
            "normal,build",
            "-i",
            package.package_spec,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return True
    return "oxipng-pybind" in result.stdout


def cargo_package_display(package: CargoRuntimePackage) -> str:
    """Return a stable Cargo package display string."""
    if isinstance(package, CargoPackageKey):
        return package.display
    return package


def classify_refresh(
    files: set[str],
    *,
    python_runtime_changed: bool,
    cargo_runtime_packages: Iterable[CargoRuntimePackage],
) -> Classification:
    """Classify changed dependency files."""
    if python_runtime_changed:
        return Classification(
            release_needed=True,
            label="release-needed",
            reason="[project.dependencies] changed; published Python metadata changes.",
        )
    if "Cargo.toml" in files:
        return Classification(
            release_needed=True,
            label="release-needed",
            reason="Cargo.toml changed; Rust package or dependency metadata may affect wheels.",
        )
    cargo_runtime_package_displays = sorted(
        cargo_package_display(package) for package in cargo_runtime_packages
    )
    if cargo_runtime_package_displays:
        packages = ", ".join(cargo_runtime_package_displays)
        return Classification(
            release_needed=True,
            label="release-needed",
            reason=f"Cargo.lock changed runtime/build packages: {packages}.",
        )
    if files <= {"uv.lock"}:
        return Classification(
            release_needed=False,
            label="no-release-needed",
            reason="Only Python tooling lockfile dependencies changed.",
        )
    return Classification(
        release_needed=False,
        label="no-release-needed",
        reason="No published runtime dependency changes detected.",
    )


def classify_refresh_from_changes(
    files: set[str],
    *,
    python_runtime_changed: bool,
    changed_cargo_packages: set[CargoPackageKey],
) -> Classification:
    """Classify a refresh after computing changed Cargo packages."""
    cargo_runtime_packages = {
        package
        for package in changed_cargo_packages
        if cargo_package_reaches_shipped_graph(package)
    }
    return classify_refresh(
        files,
        python_runtime_changed=python_runtime_changed,
        cargo_runtime_packages=cargo_runtime_packages,
    )


def classify_workspace(base_ref: str) -> Classification:
    """Classify the current workspace relative to a base ref."""
    files = changed_files(base_ref)
    changed_cargo_packages = (
        changed_workspace_cargo_lock_packages(base_ref)
        if "Cargo.lock" in files
        else set[CargoPackageKey]()
    )
    return classify_refresh_from_changes(
        files,
        python_runtime_changed=runtime_python_dependencies_changed(base_ref),
        changed_cargo_packages=changed_cargo_packages,
    )


def emit_github_output(name: str, value: str) -> None:
    """Append a GitHub Actions output when running in Actions."""
    if "\n" in name or "\n" in value:
        raise ValueError("GitHub output names and values must not contain newlines")
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path is None:
        return
    with Path(output_path).open("a", encoding="utf-8") as output:
        print(f"{name}={value}", file=output)


def main() -> int:
    """Run dependency refresh classification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="HEAD")
    args = parser.parse_args()

    classification = classify_workspace(str(args.base_ref))
    print(classification.reason)
    emit_github_output("release-needed", str(classification.release_needed).lower())
    emit_github_output("label", classification.label)
    emit_github_output("reason", classification.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

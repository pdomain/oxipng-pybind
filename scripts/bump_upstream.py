#!/usr/bin/env python3
"""Bump oxipng-pybind to the latest upstream oxipng release."""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

import tomlkit

ROOT = Path(__file__).resolve().parents[1]
LATEST_RELEASE_URL = "https://api.github.com/repos/oxipng/oxipng/releases/latest"


def resolve_executable(name: str) -> str:
    """Resolve an executable path for subprocess calls."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def normalize_version(version: str) -> str:
    """Normalize GitHub tag names to packaging versions."""
    return version.removeprefix("v")


def latest_upstream_version() -> str:
    """Fetch the latest upstream oxipng release version."""
    with urllib.request.urlopen(LATEST_RELEASE_URL, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return normalize_version(str(payload["tag_name"]))


def update_pyproject_toml(path: Path, version: str) -> None:
    """Update the Python package version."""
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["project"]["version"] = version
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def update_cargo_toml(path: Path, version: str) -> None:
    """Update the Rust package and upstream dependency versions."""
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["package"]["version"] = version
    document["dependencies"]["oxi"]["version"] = f"={version}"
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def update_cargo_lock(version: str) -> None:
    """Refresh Cargo.lock for the requested upstream oxipng version."""
    subprocess.run(
        [resolve_executable("cargo"), "update", "-p", "oxipng", "--precise", version],
        cwd=ROOT,
        check=True,
    )


def update_uv_lock() -> None:
    """Refresh uv.lock for the updated Python package metadata."""
    subprocess.run(
        [resolve_executable("uv"), "lock"],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    """Bump all tracked version files to the latest upstream release."""
    version = latest_upstream_version()
    update_pyproject_toml(ROOT / "pyproject.toml", version)
    update_cargo_toml(ROOT / "Cargo.toml", version)
    update_cargo_lock(version)
    update_uv_lock()
    print(f"updated oxipng-pybind to oxipng {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

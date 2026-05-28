#!/usr/bin/env python3
"""Verify a release tag matches package versions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts._toml_compat import load_file

ROOT = Path(__file__).resolve().parents[1]


def read_pyproject_version(path: Path = ROOT / "pyproject.toml") -> str:
    """Read the package version from pyproject.toml."""
    document = load_file(str(path))
    return str(document["project"]["version"])


def read_cargo_version(path: Path = ROOT / "Cargo.toml") -> str:
    """Read the Rust crate version from Cargo.toml."""
    document = load_file(str(path))
    return str(document["package"]["version"])


def tag_version(tag: str) -> str:
    """Strip a leading `v` from a release tag."""
    return tag[1:] if tag.startswith("v") else tag


def release_version_errors(*, tag: str, pyproject_version: str, cargo_version: str) -> list[str]:
    """Return version mismatch errors for a release tag and package metadata."""
    version = tag_version(tag)
    errors: list[str] = []
    if version != pyproject_version:
        errors.append(f"tag version {version} does not match pyproject version {pyproject_version}")
    if cargo_version != pyproject_version:
        errors.append(
            f"cargo version {cargo_version} does not match pyproject version {pyproject_version}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    """Run release tag/version validation and return a non-zero exit on errors."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    args = parser.parse_args(argv)

    errors = release_version_errors(
        tag=args.tag,
        pyproject_version=read_pyproject_version(),
        cargo_version=read_cargo_version(),
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

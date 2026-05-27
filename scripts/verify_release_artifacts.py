#!/usr/bin/env python3
"""Verify release wheel and sdist contents before publishing."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile
from pathlib import Path

EXPECTED_DISTRIBUTION = "oxipng-pybind"
EXPECTED_PACKAGE_FILES = (
    "oxipng/__init__.py",
    "oxipng/_pyoxipng_compat.py",
    "oxipng/__init__.pyi",
    "oxipng/py.typed",
)
EXPECTED_EXTENSION_PACKAGE_FILES = ("_oxipng/__init__.py",)
EXPECTED_WHEEL_METADATA = ("METADATA", "WHEEL", "RECORD")
EXPECTED_SDIST_FILES = (
    "pyproject.toml",
    "Cargo.toml",
    "Cargo.lock",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "src/lib.rs",
    *EXPECTED_PACKAGE_FILES,
)
NATIVE_EXTENSION_BASENAME_PATTERN = re.compile(r"^_oxipng(?:[._][^/]+)?\.(?:so|pyd)$")


def check_artifacts(artifacts: list[Path]) -> list[str]:
    """Return validation errors for release artifacts."""
    if not artifacts:
        return ["no artifact paths provided"]

    errors: list[str] = []
    for artifact in artifacts:
        if not artifact.is_file():
            errors.append(f"{artifact} does not exist")
        elif artifact.suffix == ".whl":
            errors.extend(check_wheel(artifact))
        elif artifact.name.endswith(".tar.gz"):
            errors.extend(check_sdist(artifact))
        else:
            errors.append(f"{artifact.name} is not a supported release artifact")
    return errors


def check_wheel(wheel: Path) -> list[str]:
    """Return validation errors for one wheel."""
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = {name for name in archive.namelist() if not name.endswith("/")}
    except zipfile.BadZipFile:
        return [f"{wheel.name} is not a valid wheel zip"]

    errors = check_wheel_metadata(wheel.name, names)
    errors.extend(
        missing_file_errors(
            wheel.name,
            "package file",
            (*EXPECTED_PACKAGE_FILES, *EXPECTED_EXTENSION_PACKAGE_FILES),
            names,
        )
    )
    errors.extend(check_native_extensions(wheel.name, names))
    return errors


def check_wheel_metadata(wheel_name: str, names: set[str]) -> list[str]:
    """Return validation errors for wheel metadata files."""
    errors: list[str] = []
    dist_info = find_dist_info(names)
    if dist_info is None:
        errors.append(f"{wheel_name} is missing .dist-info metadata directory")
    else:
        for filename in EXPECTED_WHEEL_METADATA:
            required = f"{dist_info}/{filename}"
            if required not in names:
                errors.append(f"{wheel_name} is missing wheel metadata {required}")
        if not has_dist_info_file(names, dist_info, "LICENSE"):
            errors.append(f"{wheel_name} is missing license file LICENSE")
        if not has_dist_info_file(names, dist_info, "THIRD_PARTY_NOTICES.md"):
            errors.append(f"{wheel_name} is missing notice file THIRD_PARTY_NOTICES.md")
    return errors


def missing_file_errors(
    artifact_name: str, label: str, expected_files: tuple[str, ...], names: set[str]
) -> list[str]:
    """Return errors for expected files missing from an artifact."""
    return [
        f"{artifact_name} is missing {label} {name}" for name in expected_files if name not in names
    ]


def check_native_extensions(wheel_name: str, names: set[str]) -> list[str]:
    """Return validation errors for native extension layout."""
    errors: list[str] = []
    expected_extensions = sorted(
        name
        for name in names
        if name.startswith("_oxipng/")
        and "/" not in name.removeprefix("_oxipng/")
        and NATIVE_EXTENSION_BASENAME_PATTERN.match(Path(name).name)
    )
    misplaced_extensions = sorted(
        name
        for name in names
        if name not in expected_extensions
        and NATIVE_EXTENSION_BASENAME_PATTERN.match(Path(name).name)
    )
    if len(expected_extensions) != 1:
        errors.append(f"{wheel_name} must contain exactly one _oxipng package native extension")
    if misplaced_extensions:
        errors.append(
            f"{wheel_name} has native extension outside the expected _oxipng package layout"
        )
    return errors


def find_dist_info(names: set[str]) -> str | None:
    """Return the expected dist-info directory name when it is present."""
    dist_infos = sorted(
        name.rsplit("/", 1)[0]
        for name in names
        if any(name.endswith(f".dist-info/{filename}") for filename in EXPECTED_WHEEL_METADATA)
        and "/" in name
    )
    for dist_info in dist_infos:
        if canonicalize_distribution(dist_info.split("-", 1)[0]) == EXPECTED_DISTRIBUTION:
            return dist_info
    return dist_infos[0] if dist_infos else None


def has_dist_info_file(names: set[str], dist_info: str, filename: str) -> bool:
    """Return whether a named dist-info file exists directly or under licenses."""
    return f"{dist_info}/{filename}" in names or f"{dist_info}/licenses/{filename}" in names


def check_sdist(sdist: Path) -> list[str]:
    """Return validation errors for one source distribution."""
    try:
        with tarfile.open(sdist, "r:gz") as archive:
            names = {member.name for member in archive.getmembers() if member.isfile()}
    except tarfile.TarError:
        return [f"{sdist.name} is not a valid sdist tarball"]

    errors: list[str] = []
    root = find_sdist_root(names)
    if root is None:
        return [f"{sdist.name} does not contain a single source root directory"]

    relative_names = {
        name.removeprefix(f"{root}/") for name in names if name.startswith(f"{root}/")
    }
    errors.extend(
        missing_file_errors(sdist.name, "source file", EXPECTED_SDIST_FILES, relative_names)
    )
    return errors


def find_sdist_root(names: set[str]) -> str | None:
    """Return the single root directory used by an sdist tarball."""
    roots = {name.split("/", 1)[0] for name in names if "/" in name}
    if len(roots) != 1:
        return None
    return roots.pop()


def canonicalize_distribution(name: str) -> str:
    """Return the normalized distribution name used in package metadata."""
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> int:
    """Run release artifact validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", nargs="*")
    args = parser.parse_args()

    errors = check_artifacts([Path(artifact) for artifact in args.artifacts])
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

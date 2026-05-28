#!/usr/bin/env python3
"""Check that built wheels use expected ABI3 and platform tags."""

from __future__ import annotations

import argparse
import fnmatch
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DISTRIBUTION = "oxipng-pybind"
WHEEL_FILENAME_REGEX = (
    r"^(?P<distribution>.+)-(?P<version>[^-]+)(?:-[^-]+)?-"
    + r"(?P<python>[^-]+)-(?P<abi>[^-]+)-(?P<platform>[^-]+)\.whl$"
)
WHEEL_FILENAME_PATTERN = re.compile(WHEEL_FILENAME_REGEX)
PROJECT_VERSION_REGEX = re.compile(r'^version\s*=\s*"(?P<version>[^"]+)"$', re.MULTILINE)


def canonicalize_distribution(name: str) -> str:
    """Return the normalized distribution name used in wheel metadata."""
    return re.sub(r"[-_.]+", "-", name).lower()


def expected_version() -> str:
    """Return the package version expected in wheel filenames."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = PROJECT_VERSION_REGEX.search(pyproject)
    if match is None:
        msg = "project version not found in pyproject.toml"
        raise RuntimeError(msg)
    return match.group("version")


def check_wheels(
    wheels: list[Path], expected_platform: str, expected_python: str = "cp310"
) -> list[str]:
    """Return validation errors for wheel tags."""
    if not wheels:
        return ["no wheel paths provided"]
    if len(wheels) != 1:
        return [f"expected exactly 1 wheel, found {len(wheels)}"]

    errors: list[str] = []
    project_version = expected_version()
    for wheel in wheels:
        if not wheel.is_file():
            errors.append(f"{wheel} does not exist")
            continue

        match = WHEEL_FILENAME_PATTERN.match(wheel.name)
        if match is None:
            errors.append(f"{wheel.name} is not a valid wheel filename")
            continue

        distribution = canonicalize_distribution(match.group("distribution"))
        version = match.group("version")
        if distribution != canonicalize_distribution(EXPECTED_DISTRIBUTION):
            errors.append(
                f"{wheel.name} uses distribution {distribution}, expected {EXPECTED_DISTRIBUTION}"
            )
        if version != project_version:
            errors.append(f"{wheel.name} uses version {version}, expected {project_version}")

        python_tags = set(match.group("python").split("."))
        abi_tags = set(match.group("abi").split("."))
        platform_tags = set(match.group("platform").split("."))
        tag_label = "/".join(
            sorted(f"{python_tag}-{abi_tag}" for python_tag in python_tags for abi_tag in abi_tags)
        )
        if python_tags != {expected_python}:
            actual_python_tags = ",".join(sorted(python_tags))
            errors.append(
                f"{wheel.name} uses Python tag {actual_python_tags}, expected {expected_python}"
            )
        if abi_tags != {"abi3"}:
            errors.append(f"{wheel.name} uses non-ABI3 tag {tag_label}")
        if not any(fnmatch.fnmatchcase(platform, expected_platform) for platform in platform_tags):
            actual_platform_tags = ",".join(sorted(platform_tags))
            errors.append(
                f"{wheel.name} platform {actual_platform_tags} does not match {expected_platform}"
            )

    return errors


def main() -> int:
    """Run the wheel tag checker."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-python", default="cp310")
    parser.add_argument("--expected-platform", required=True)
    parser.add_argument("wheels", nargs="*")
    args = parser.parse_args()

    errors = check_wheels(
        [Path(wheel) for wheel in args.wheels],
        args.expected_platform,
        args.expected_python,
    )
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

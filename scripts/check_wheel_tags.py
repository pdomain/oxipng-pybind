#!/usr/bin/env python3
"""Check that built wheels use expected ABI3 and platform tags."""

from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path

import tomlkit
from packaging.utils import InvalidWheelFilename, canonicalize_name, parse_wheel_filename
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DISTRIBUTION = "oxipng-pybind"


def expected_version() -> Version:
    """Return the package version expected in wheel filenames."""
    document = tomlkit.parse((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return Version(str(document["project"]["version"]))


def check_wheels(
    wheels: list[Path], expected_platform: str, expected_python: str = "cp311"
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
        try:
            distribution, version, _build, tags = parse_wheel_filename(wheel.name)
        except InvalidWheelFilename as exc:
            errors.append(f"{wheel.name} is not a valid wheel filename: {exc}")
            continue

        if distribution != canonicalize_name(EXPECTED_DISTRIBUTION):
            errors.append(
                f"{wheel.name} uses distribution {distribution}, expected {EXPECTED_DISTRIBUTION}"
            )
        if version != project_version:
            errors.append(f"{wheel.name} uses version {version}, expected {project_version}")

        python_tags = {tag.interpreter for tag in tags}
        abi_tags = {tag.abi for tag in tags}
        platform_tags = {tag.platform for tag in tags}
        tag_label = "/".join(sorted(f"{tag.interpreter}-{tag.abi}" for tag in tags))
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
    parser.add_argument("--expected-python", default="cp311")
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

#!/usr/bin/env python3
"""Check that built wheels use expected ABI3 and platform tags."""

from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path

WHEEL_TAG_PARTS = 4


def parse_wheel_tags(path: Path) -> tuple[str, str, str]:
    """Return the Python, ABI, and platform tag components from a wheel name."""
    if path.suffix != ".whl":
        raise ValueError(f"{path} is not a wheel")
    parts = path.name.removesuffix(".whl").rsplit("-", 3)
    if len(parts) != WHEEL_TAG_PARTS:
        raise ValueError(f"{path.name} is not a valid wheel filename")
    return parts[1], parts[2], parts[3]


def check_wheels(
    wheels: list[Path], expected_platform: str, expected_python: str = "cp310"
) -> list[str]:
    """Return validation errors for wheel tags."""
    if not wheels:
        return ["no wheel paths provided"]

    errors: list[str] = []
    for wheel in wheels:
        try:
            python_tag, abi_tag, platform_tag = parse_wheel_tags(wheel)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if python_tag != expected_python:
            errors.append(f"{wheel.name} uses Python tag {python_tag}, expected {expected_python}")
        if abi_tag != "abi3":
            errors.append(f"{wheel.name} uses non-ABI3 tag {python_tag}-{abi_tag}")
        if not fnmatch.fnmatchcase(platform_tag, expected_platform):
            errors.append(
                f"{wheel.name} platform {platform_tag} does not match {expected_platform}"
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

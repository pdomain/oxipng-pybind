#!/usr/bin/env python3
"""Bump oxipng-pybind to the latest upstream oxipng release."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.request
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

ROOT = Path(__file__).resolve().parents[1]
LATEST_RELEASE_URL = "https://api.github.com/repos/oxipng/oxipng/releases/latest"
WRAPPER_VERSION_PATTERN = re.compile(r"^(?P<base>\d+\.\d+\.\d+)(?:\.post(?P<post>\d+))?$")
UPSTREAM_VERSION_PATTERN = re.compile(r"^v?(?P<version>\d+\.\d+\.\d+)$")


def resolve_executable(name: str) -> str:
    """Resolve an executable path for subprocess calls."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def normalize_version(version: str) -> str:
    """Normalize GitHub tag names to packaging versions."""
    match = UPSTREAM_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"unsupported upstream version: {version}")
    return match.group("version")


def next_post_release(version: str) -> str:
    """Return the next PEP 440 post release for a wrapper version."""
    match = WRAPPER_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"unsupported wrapper version: {version}")
    base = match.group("base")
    post = match.group("post")
    if post is None:
        return f"{base}.post1"
    return f"{base}.post{int(post) + 1}"


def latest_upstream_version() -> str:
    """Fetch the latest upstream oxipng release version."""
    with urllib.request.urlopen(LATEST_RELEASE_URL, timeout=30) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    return normalize_version(str(payload["tag_name"]))


def read_pyproject_version(path: Path) -> str:
    """Read the Python package version."""
    import tomlkit  # noqa: PLC0415  # optional automation dependency is loaded only here

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    return str(document["project"]["version"])


def update_pyproject_toml(path: Path, version: str) -> None:
    """Update the Python package version."""
    import tomlkit  # noqa: PLC0415  # optional automation dependency is loaded only here

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["project"]["version"] = version
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def read_pinned_upstream_version(path: Path) -> str:
    """Read the pinned upstream oxipng dependency version."""
    import tomlkit  # noqa: PLC0415  # optional automation dependency is loaded only here

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    return str(document["dependencies"]["oxi"]["version"]).lstrip("=")


def update_cargo_toml(path: Path, version: str) -> None:
    """Update the Rust package and upstream dependency versions."""
    import tomlkit  # noqa: PLC0415  # optional automation dependency is loaded only here

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["package"]["version"] = version
    document["dependencies"]["oxi"]["version"] = f"={version}"
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def update_cargo_lock(version: str) -> None:
    """Refresh Cargo.lock for the requested upstream oxipng version."""
    subprocess.run(  # noqa: S603
        [resolve_executable("cargo"), "update", "-p", "oxipng", "--precise", version],
        cwd=ROOT,
        check=True,
    )


def update_uv_lock() -> None:
    """Refresh uv.lock for the updated Python package metadata."""
    subprocess.run(  # noqa: S603
        [resolve_executable("uv"), "lock"],
        cwd=ROOT,
        check=True,
    )


def write_target_version(version: str, path: Path) -> None:
    """Write the target upstream version for workflow steps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(version + "\n", encoding="utf-8")


def emit_github_output(name: str, value: str) -> None:
    """Write a GitHub Actions output when running in Actions."""
    if "\n" in name or "\n" in value:
        raise ValueError("GitHub output names and values must not contain newlines")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def bump_upstream_files(
    version: str,
    *,
    pyproject_path: Path = ROOT / "pyproject.toml",
    cargo_path: Path = ROOT / "Cargo.toml",
    target_version_path: Path = ROOT / ".cache/upstream-bump/target-version.txt",
) -> bool:
    """Update tracked files for a new upstream release."""
    current_upstream = read_pinned_upstream_version(cargo_path)
    write_target_version(version, target_version_path)
    if current_upstream == version:
        return False
    update_pyproject_toml(pyproject_path, version)
    update_cargo_toml(cargo_path, version)
    update_cargo_lock(version)
    update_uv_lock()
    return True


def bump_wrapper_post_release(pyproject_path: Path = ROOT / "pyproject.toml") -> str:
    """Bump the Python package to the next wrapper-only post release."""
    version = next_post_release(read_pyproject_version(pyproject_path))
    update_pyproject_toml(pyproject_path, version)
    update_uv_lock()
    return version


def issue_body(version: str, report: str) -> str:
    """Build the upstream-surface triage issue body."""
    return f"""Upstream version: {version}

Detected surface report:

{report}

Triage checklist:

- [ ] expose now
- [ ] defer and document
- [ ] reject as intentionally unsupported
"""


def find_surface_issue(version: str) -> int | None:
    """Find an open upstream-surface issue for a specific version."""
    command = [
        resolve_executable("gh"),
        "issue",
        "list",
        "--label",
        "upstream-surface",
        "--state",
        "open",
        "--json",
        "number,title",
    ]
    result = subprocess.run(  # noqa: S603
        command, cwd=ROOT, check=True, capture_output=True, text=True
    )
    title = f"Evaluate upstream oxipng {version} surface changes"
    for issue in json.loads(result.stdout):
        if issue.get("title") == title:
            return int(issue["number"])
    return None


def upsert_surface_issue(version: str, report_path: Path) -> None:
    """Create or update the upstream-surface triage issue for a version."""
    report = report_path.read_text(encoding="utf-8")
    title = f"Evaluate upstream oxipng {version} surface changes"
    body = issue_body(version, report)
    existing = find_surface_issue(version)
    gh = resolve_executable("gh")
    if existing is None:
        subprocess.run(  # noqa: S603
            [
                gh,
                "issue",
                "create",
                "--title",
                title,
                "--label",
                "upstream-surface",
                "--body",
                body,
            ],
            cwd=ROOT,
            check=True,
        )
    else:
        subprocess.run(  # noqa: S603
            [gh, "issue", "edit", str(existing), "--body", body],
            cwd=ROOT,
            check=True,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Run upstream or wrapper-only version bumps."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wrapper-post",
        action="store_true",
        help="bump only the Python package to the next .postN release",
    )
    args = parser.parse_args(argv)

    if args.wrapper_post:
        version = bump_wrapper_post_release()
        emit_github_output("wrapper-version", version)
        print(f"updated oxipng-pybind wrapper version to {version}")
        return 0

    version = latest_upstream_version()
    changed = bump_upstream_files(version)
    emit_github_output("target-version", version)
    if changed:
        print(f"updated oxipng-pybind to oxipng {version}")
    else:
        print(f"oxipng-pybind already pins oxipng {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

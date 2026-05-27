"""Validate release tags before publishing artifacts."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

HTTP_NOT_FOUND = 404
RELEASE_TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+(?:\.post\d+)?)$")


class ReleaseTagError(RuntimeError):
    """Raised when a release tag is not eligible for publishing."""


@dataclass(frozen=True)
class WorkflowCheck:
    """A GitHub workflow conclusion required before automated tag creation."""

    workflow: str
    conclusion: str


def release_version_from_tag(tag: str) -> str:
    """Return the project version encoded by a strict release tag."""
    match = RELEASE_TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ReleaseTagError(
            f"release tag {tag!r} must match vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH.postN"
        )
    return match.group("version")


def read_project_version(pyproject: Path) -> str:
    """Read project.version from pyproject.toml."""
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    project_raw = data.get("project")
    if not isinstance(project_raw, dict):
        raise ReleaseTagError("pyproject.toml is missing [project]")
    project = cast("dict[str, Any]", project_raw)
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ReleaseTagError("pyproject.toml is missing project.version")
    return version


def validate_tag_matches_project_version(tag: str, pyproject: Path) -> str:
    """Validate that a strict release tag matches project.version."""
    tag_version = release_version_from_tag(tag)
    project_version = read_project_version(pyproject)
    if tag_version != project_version:
        message = (
            f"release tag {tag!r} resolves to {tag_version!r}, which does not match "
            f"project.version {project_version!r}"
        )
        raise ReleaseTagError(message)
    return tag_version


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the completed process."""
    git = shutil.which("git")
    if git is None:
        raise ReleaseTagError("git executable was not found")
    return subprocess.run(  # noqa: S603 - trusted git subcommands built by this script.
        [git, *args],
        check=False,
        text=True,
        capture_output=True,
    )


def ensure_ref_is_on_main(ref: str, main_ref: str) -> None:
    """Require a release ref to be reachable from the configured main ref."""
    fetch = run_git(["fetch", "--quiet", "origin", "main:refs/remotes/origin/main"])
    if fetch.returncode != 0:
        raise ReleaseTagError(fetch.stderr.strip() or "failed to fetch origin/main")
    result = run_git(["merge-base", "--is-ancestor", ref, main_ref])
    if result.returncode != 0:
        raise ReleaseTagError(f"{ref!r} is not contained in {main_ref!r}")


def pypi_version_exists(project: str, version: str, index_url: str) -> bool:
    """Return whether a project version already exists on a PyPI-compatible JSON API."""
    url = f"{index_url.rstrip('/')}/pypi/{project}/{version}/json"
    parsed_url = urllib.parse.urlsplit(url)
    if parsed_url.scheme != "https":
        raise ReleaseTagError(f"PyPI version check requires an https URL, got {index_url!r}")
    request = urllib.request.Request(  # noqa: S310 - URL scheme is validated above.
        url,
        headers={"User-Agent": "oxipng-pybind-release-check"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20):  # noqa: S310 - URL scheme is validated above.
            return True
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            return False
        raise ReleaseTagError(f"PyPI version check failed with HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise ReleaseTagError(f"PyPI version check failed: {error.reason}") from error


def ensure_pypi_version_absent(project: str, version: str, index_url: str) -> None:
    """Reject release versions that already exist on PyPI."""
    if pypi_version_exists(project, version, index_url):
        raise ReleaseTagError(f"{project} {version} already exists at {index_url}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag name, for example v10.1.1")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--project", default="oxipng-pybind")
    parser.add_argument("--pypi-url", default="https://pypi.org")
    parser.add_argument("--skip-main-check", action="store_true")
    parser.add_argument("--skip-pypi-check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run release tag validation."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        version = validate_tag_matches_project_version(args.tag, args.pyproject)
        if not args.skip_main_check:
            ensure_ref_is_on_main(args.tag, args.main_ref)
        if not args.skip_pypi_check:
            ensure_pypi_version_absent(args.project, version, args.pypi_url)
    except ReleaseTagError as error:
        print(f"release tag validation failed: {error}", file=sys.stderr)
        return 1
    print(f"release tag validation passed for {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

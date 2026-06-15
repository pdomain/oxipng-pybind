#!/usr/bin/env python3
"""Bump oxipng-pybind to the latest upstream oxipng release."""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

ROOT = Path(__file__).resolve().parents[1]
LATEST_RELEASE_URL = "https://api.github.com/repos/oxipng/oxipng/releases/latest"
CRATES_IO_VERSION_URL = "https://crates.io/api/v1/crates/oxipng/{version}"
HTTP_NOT_FOUND = 404
GITHUB_API_VERSION = "2022-11-28"
GITHUB_USER_AGENT = "oxipng-pybind-bump"
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


def _github_request_headers(token: str | None) -> dict[str, str]:
    """Build request headers for the GitHub REST API, authenticating if able."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": GITHUB_USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def latest_upstream_version() -> str:
    """Fetch the latest upstream oxipng release version.

    Authenticates with ``GITHUB_TOKEN`` (or ``GH_TOKEN``) when present so that
    scheduled CI runs use GitHub's 5000/hr authenticated rate limit instead of
    the 60/hr unauthenticated limit shared across GitHub-hosted runner egress
    IPs. Local runs without a token still work unauthenticated.
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    request = urllib.request.Request(  # noqa: S310
        LATEST_RELEASE_URL, headers=_github_request_headers(token)
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        raw_payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(raw_payload, dict):
        raise TypeError("GitHub release payload must be a JSON object")
    payload = cast("dict[str, object]", raw_payload)
    try:
        tag_name = payload["tag_name"]
    except KeyError as error:
        raise RuntimeError("GitHub release payload is missing tag_name") from error
    if not isinstance(tag_name, str):
        raise TypeError("GitHub release payload tag_name must be a string")
    return normalize_version(tag_name)


def crates_io_version_available(version: str) -> bool:
    """Return whether crates.io has indexed the target oxipng crate version."""
    url = CRATES_IO_VERSION_URL.format(version=version)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            payload = cast("dict[str, Any]", json.loads(response.read().decode("utf-8")))
    except urllib.error.HTTPError as error:
        # HTTPError is a file-like response object (urllib wraps it in a
        # tempfile-backed closer). Close it so its finalizer does not emit a
        # spurious ResourceWarning on garbage collection.
        with error:
            if error.code == HTTP_NOT_FOUND:
                return False
            raise
    crate_version = payload.get("version")
    if not isinstance(crate_version, dict):
        return False
    crate_version_data = cast("dict[str, object]", crate_version)
    return crate_version_data.get("num") == version


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


def append_upstream_release_note(version: str, *, root: Path = ROOT) -> None:
    """Append the upstream release note entry to CHANGELOG.md for automated bumps."""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    text = changelog.read_text(encoding="utf-8")
    marker = "## Release Notes\n"
    entry = (
        f"\n## {version} - Bump Version\n"
        f"\n- Rebuilt `oxipng-pybind` to track upstream `oxipng` {version}.\n"
    )
    if entry in text:
        return

    if marker in text:
        text = text.replace(marker, marker + entry + "\n", 1)
    else:
        text = text.rstrip() + "\n\n" + marker + entry + "\n"
    changelog.write_text(text, encoding="utf-8")


def emit_github_output(name: str, value: str) -> None:
    """Write a GitHub Actions output when running in Actions."""
    if "\n" in name or "\r" in name or "\n" in value or "\r" in value:
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
    changelog_root: Path | None = None,
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
    appended_version = read_pyproject_version(pyproject_path)
    append_upstream_release_note(appended_version, root=changelog_root or pyproject_path.parent)
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


UPSTREAM_SURFACE_LABEL = "upstream-surface"
UPSTREAM_SURFACE_LABEL_COLOR = "BFD4F2"
UPSTREAM_SURFACE_LABEL_DESCRIPTION = "Upstream oxipng surface change awaiting triage"


def ensure_label(name: str, *, color: str, description: str) -> None:
    """Ensure a GitHub label exists, creating it if necessary.

    Uses ``--force`` so ``gh label create`` is idempotent.  If the command
    still exits non-zero for any reason (e.g. a permissions error on a fork),
    the error is swallowed so that callers can proceed with issue creation.
    """
    with contextlib.suppress(subprocess.CalledProcessError):
        subprocess.run(  # noqa: S603
            [
                resolve_executable("gh"),
                "label",
                "create",
                name,
                "--color",
                color,
                "--description",
                description,
                "--force",
            ],
            cwd=ROOT,
            check=True,
        )


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
        ensure_label(
            UPSTREAM_SURFACE_LABEL,
            color=UPSTREAM_SURFACE_LABEL_COLOR,
            description=UPSTREAM_SURFACE_LABEL_DESCRIPTION,
        )
        subprocess.run(  # noqa: S603
            [
                gh,
                "issue",
                "create",
                "--title",
                title,
                "--label",
                UPSTREAM_SURFACE_LABEL,
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
    emit_github_output("target-version", version)
    if not crates_io_version_available(version):
        emit_github_output("upstream-crate-available", "false")
        print(f"oxipng {version} is not available on crates.io yet; retry later.")
        return 0

    changed = bump_upstream_files(version)
    if changed:
        print(f"updated oxipng-pybind to oxipng {version}")
    else:
        print(f"oxipng-pybind already pins oxipng {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

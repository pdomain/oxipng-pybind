#!/usr/bin/env python3
"""Refresh reviewed GitHub Actions refs in workflow files."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github/workflows"
MANAGED_ACTIONS = (
    "actions/checkout",
    "actions/setup-python",
    "astral-sh/setup-uv",
    "taiki-e/install-action",
    "actions/upload-artifact",
    "actions/download-artifact",
    "peter-evans/create-pull-request",
    "PyO3/maturin-action",
    "pypa/gh-action-pypi-publish",
)
MANAGED_RUST_TOOLCHAIN = "dtolnay/rust-toolchain"


@dataclass(frozen=True)
class ActionRelease:
    """Latest release tag and immutable commit SHA."""

    tag: str
    sha: str


GhRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def resolve_executable(name: str) -> str:
    """Resolve an executable path for subprocess calls."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def run_gh(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a GitHub CLI command and return captured output."""
    resolved_command = [resolve_executable(command[0]), *command[1:]]
    return subprocess.run(  # noqa: S603
        resolved_command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def gh_json(endpoint: str, *, runner: GhRunner = run_gh) -> dict[str, object]:
    """Fetch a GitHub API endpoint as JSON."""
    result = runner(["gh", "api", endpoint])
    return cast("dict[str, object]", json.loads(result.stdout))


def latest_release(action: str, *, runner: GhRunner = run_gh) -> ActionRelease:
    """Return the latest release tag and target commit SHA for an action."""
    release = gh_json(f"repos/{action}/releases/latest", runner=runner)
    tag = release.get("tag_name")
    if not isinstance(tag, str):
        raise TypeError(f"latest release for {action} did not include tag_name")
    tag_ref = gh_json(f"repos/{action}/git/ref/tags/{tag}", runner=runner)
    raw_object = tag_ref.get("object")
    if not isinstance(raw_object, dict):
        raise TypeError(f"tag ref for {action}@{tag} did not include object")
    tag_object = cast("dict[str, object]", raw_object)
    sha = tag_object.get("sha")
    if tag_object.get("type") == "tag" and isinstance(sha, str):
        tag_payload = gh_json(f"repos/{action}/git/tags/{sha}", runner=runner)
        nested_object = tag_payload.get("object")
        if not isinstance(nested_object, dict):
            raise TypeError(f"annotated tag for {action}@{tag} did not include object")
        sha = cast("dict[str, object]", nested_object).get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise TypeError(f"tag ref for {action}@{tag} did not resolve to a commit SHA")
    return ActionRelease(tag=tag, sha=sha)


def latest_stable_rust_toolchain(*, runner: GhRunner = run_gh) -> str:
    """Return latest stable Rust toolchain version from rust-lang/rust tags."""
    release = gh_json("repos/rust-lang/rust/releases/latest", runner=runner)
    tag = release.get("tag_name")
    if not isinstance(tag, str):
        raise TypeError("latest rust release did not include tag_name")
    version = tag.removeprefix("stable/")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"unexpected stable Rust release tag: {tag}")
    return version


def update_workflow_refs(
    path: Path, *, releases: dict[str, ActionRelease], rust_toolchain: str
) -> bool:
    """Update managed action refs in one workflow file."""
    text = path.read_text(encoding="utf-8")
    updated = text
    for action, release in releases.items():
        updated = re.sub(
            rf"(?m)(uses:\s+{re.escape(action)}@)[^\s]+",
            rf"\g<1>{release.sha}",
            updated,
        )
    updated = re.sub(
        rf"(?m)(uses:\s+{re.escape(MANAGED_RUST_TOOLCHAIN)}@)[^\s]+",
        rf"\g<1>{rust_toolchain}",
        updated,
    )
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def update_github_actions(
    *,
    workflow_dir: Path = WORKFLOW_DIR,
    runner: GhRunner = run_gh,
) -> list[Path]:
    """Refresh managed action refs and return changed workflow paths."""
    releases = {action: latest_release(action, runner=runner) for action in MANAGED_ACTIONS}
    rust_toolchain = latest_stable_rust_toolchain(runner=runner)
    return [
        path
        for path in sorted(workflow_dir.glob("*.yml"))
        if update_workflow_refs(path, releases=releases, rust_toolchain=rust_toolchain)
    ]


def main() -> int:
    """Run the GitHub Actions ref refresh."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    for path in update_github_actions():
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

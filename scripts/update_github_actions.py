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
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github/workflows"
HELPERS_PATH = ROOT / "tests" / "helpers" / "workflows.py"
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


@dataclass(frozen=True)
class ReviewedAllowlist:
    """Parsed reviewed action refs and Rust toolchain version from the helpers file."""

    action_refs: dict[str, str]
    rust_toolchain: str


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


def compute_managed_state(*, runner: GhRunner = run_gh) -> tuple[dict[str, ActionRelease], str]:
    """Fetch the latest managed action releases and Rust toolchain version."""
    releases = {action: latest_release(action, runner=runner) for action in MANAGED_ACTIONS}
    rust_toolchain = latest_stable_rust_toolchain(runner=runner)
    return releases, rust_toolchain


def update_workflow_refs(
    path: Path, *, releases: Mapping[str, ActionRelease], rust_toolchain: str
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


def _bump_workflow_refs(
    workflow_dir: Path, *, releases: Mapping[str, ActionRelease], rust_toolchain: str
) -> list[Path]:
    """Bump managed action refs across all workflow files; return changed paths."""
    return [
        path
        for path in sorted(workflow_dir.glob("*.yml"))
        if update_workflow_refs(path, releases=releases, rust_toolchain=rust_toolchain)
    ]


def update_github_actions(
    *,
    workflow_dir: Path = WORKFLOW_DIR,
    runner: GhRunner = run_gh,
) -> list[Path]:
    """Refresh managed action refs and return changed workflow paths."""
    releases, rust_toolchain = compute_managed_state(runner=runner)
    return _bump_workflow_refs(workflow_dir, releases=releases, rust_toolchain=rust_toolchain)


def _find_action_refs_block(text: str) -> re.Match[str]:
    """Locate the REVIEWED_ACTION_REFS dict literal within helpers file text."""
    match = re.search(r"REVIEWED_ACTION_REFS = \{.*?\n\}", text, re.DOTALL)
    if match is None:
        raise ValueError("REVIEWED_ACTION_REFS block not found in helpers file")
    return match


def parse_reviewed_allowlist(text: str) -> ReviewedAllowlist:
    """Parse the current reviewed action refs and Rust toolchain version from helpers text."""
    block = _find_action_refs_block(text)
    action_refs = dict(re.findall(r'"([^"]+)":\s*"([^"]+)",?', block.group()))
    version_match = re.search(r'RUST_TOOLCHAIN_VERSION = "([^"]+)"', text)
    if version_match is None:
        raise ValueError("RUST_TOOLCHAIN_VERSION not found in helpers file")
    return ReviewedAllowlist(action_refs=action_refs, rust_toolchain=version_match.group(1))


def render_action_refs_block(action_refs: Mapping[str, str]) -> str:
    """Render the REVIEWED_ACTION_REFS dict literal, preserving mapping order."""
    entries = "\n".join(f'    "{action}": "{sha}",' for action, sha in action_refs.items())
    return f"REVIEWED_ACTION_REFS = {{\n{entries}\n}}"


def _ordered_action_names(
    old_refs: Mapping[str, str], releases: Mapping[str, ActionRelease]
) -> list[str]:
    """Order action names as the allowlist's existing keys, then any newly managed actions."""
    ordered = list(old_refs)
    ordered.extend(action for action in releases if action not in old_refs)
    return ordered


def build_new_action_refs(
    *, old_refs: Mapping[str, str], releases: Mapping[str, ActionRelease]
) -> dict[str, str]:
    """Merge latest release SHAs into the allowlist, preserving the existing key order."""
    return {
        action: releases[action].sha if action in releases else old_refs[action]
        for action in _ordered_action_names(old_refs, releases)
    }


def sync_reviewed_refs(
    path: Path, *, releases: Mapping[str, ActionRelease], rust_toolchain: str
) -> bool:
    """Rewrite the reviewed action refs allowlist file in place.

    Returns whether the file's contents changed.
    """
    text = path.read_text(encoding="utf-8")
    old_refs = parse_reviewed_allowlist(text).action_refs
    new_refs = build_new_action_refs(old_refs=old_refs, releases=releases)
    block = _find_action_refs_block(text)
    updated = text[: block.start()] + render_action_refs_block(new_refs) + text[block.end() :]
    updated = re.sub(
        r'RUST_TOOLCHAIN_VERSION = "[^"]+"',
        f'RUST_TOOLCHAIN_VERSION = "{rust_toolchain}"',
        updated,
    )
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def _rendered_action_entry(action: str, release: ActionRelease, old_sha: str | None) -> list[str]:
    """Render review-report lines for one changed action ref."""
    old_short = old_sha[:8] if old_sha is not None else "(new)"
    return [
        f"  {action}",
        f"    repo:      https://github.com/{action}",
        f"    version:   {release.tag}",
        f"    sha:       {old_short} -> {release.sha[:8]}",
        f"    changelog: https://github.com/{action}/releases/tag/{release.tag}",
    ]


def _rendered_rust_entry(old_rust: str, new_rust: str) -> list[str]:
    """Render review-report lines for the Rust toolchain version bump."""
    return [
        f"  {MANAGED_RUST_TOOLCHAIN}",
        "    repo:      https://github.com/rust-lang/rust",
        f"    version:   {old_rust} -> {new_rust}",
        f"    changelog: https://github.com/rust-lang/rust/releases/tag/{new_rust}",
    ]


def render_review_report(
    *,
    old_refs: Mapping[str, str],
    releases: Mapping[str, ActionRelease],
    old_rust: str,
    new_rust: str,
    changed_paths: Sequence[str],
) -> str:
    """Render the human-reviewable report of reviewed action ref changes."""
    ordered_actions = _ordered_action_names(old_refs, releases)
    entries = [
        _rendered_action_entry(action, releases[action], old_refs.get(action))
        for action in ordered_actions
        if action in releases and old_refs.get(action) != releases[action].sha
    ]
    if new_rust != old_rust:
        entries.append(_rendered_rust_entry(old_rust, new_rust))

    if not entries and not changed_paths:
        return "GitHub Action pins already match the latest reviewed releases."

    lines = ["Reviewed GitHub Action pin updates:"]
    for entry in entries:
        lines.append("")
        lines.extend(entry)
    if changed_paths:
        lines.append("")
        lines.append("Updated files:")
        lines.extend(f"  {path}" for path in changed_paths)
    return "\n".join(lines)


def sync_github_actions(
    *,
    workflow_dir: Path = WORKFLOW_DIR,
    helpers_path: Path = HELPERS_PATH,
    runner: GhRunner = run_gh,
) -> str:
    """Bump workflow refs, sync the reviewed allowlist, and return the review report."""
    releases, rust_toolchain = compute_managed_state(runner=runner)
    changed_workflows = _bump_workflow_refs(
        workflow_dir, releases=releases, rust_toolchain=rust_toolchain
    )
    old_allowlist = parse_reviewed_allowlist(helpers_path.read_text(encoding="utf-8"))
    allowlist_changed = sync_reviewed_refs(
        helpers_path, releases=releases, rust_toolchain=rust_toolchain
    )
    changed_paths = [str(path.relative_to(ROOT)) for path in changed_workflows]
    if allowlist_changed:
        changed_paths.append(str(helpers_path.relative_to(ROOT)))
    return render_review_report(
        old_refs=old_allowlist.action_refs,
        releases=releases,
        old_rust=old_allowlist.rust_toolchain,
        new_rust=rust_toolchain,
        changed_paths=sorted(changed_paths),
    )


def main() -> int:
    """Run the GitHub Actions ref refresh."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sync-reviewed-refs",
        action="store_true",
        help="also rewrite the reviewed action refs allowlist and print a review report",
    )
    args = parser.parse_args()
    if args.sync_reviewed_refs:
        print(sync_github_actions())
        return 0
    for path in update_github_actions():
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

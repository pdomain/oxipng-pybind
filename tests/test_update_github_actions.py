"""Tests for GitHub Actions dependency refresh helpers."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from scripts import update_github_actions

if TYPE_CHECKING:
    from pathlib import Path


def completed(payload: object) -> subprocess.CompletedProcess[str]:
    """Return a completed gh API process with JSON stdout."""
    return subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=json.dumps(payload))


def test_latest_release_commit_sha_resolves_tag_ref() -> None:
    """Latest release lookup returns the immutable commit behind the release tag."""
    calls: list[list[str]] = []
    payloads = {
        "repos/actions/upload-artifact/releases/latest": {"tag_name": "v7.0.1"},
        "repos/actions/upload-artifact/git/ref/tags/v7.0.1": {
            "object": {"sha": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", "type": "commit"}
        },
    }

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return completed(payloads[command[-1]])

    release = update_github_actions.latest_release("actions/upload-artifact", runner=runner)

    assert release.tag == "v7.0.1"
    assert release.sha == "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    assert calls == [
        ["gh", "api", "repos/actions/upload-artifact/releases/latest"],
        ["gh", "api", "repos/actions/upload-artifact/git/ref/tags/v7.0.1"],
    ]


def test_update_workflow_refs_updates_managed_refs_only(tmp_path: Path) -> None:
    """Managed action refs are rewritten while unrelated refs stay unchanged."""
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        """
steps:
  - uses: actions/upload-artifact@v4
  - uses: actions/download-artifact@oldsha
  - uses: peter-evans/create-pull-request@oldsha
  - uses: dtolnay/rust-toolchain@1.85.1
  - uses: actions/checkout@v6
""".lstrip(),
        encoding="utf-8",
    )

    changed = update_github_actions.update_workflow_refs(
        workflow,
        releases={
            "actions/upload-artifact": update_github_actions.ActionRelease("v7.0.1", "uploadsha"),
            "actions/download-artifact": update_github_actions.ActionRelease(
                "v8.0.1", "downloadsha"
            ),
            "peter-evans/create-pull-request": update_github_actions.ActionRelease(
                "v8.1.1", "createsha"
            ),
            "actions/checkout": update_github_actions.ActionRelease("v6.0.2", "checkoutsha"),
        },
        rust_toolchain="1.95.0",
    )

    assert changed is True
    assert workflow.read_text(encoding="utf-8") == (
        "steps:\n"
        "  - uses: actions/upload-artifact@uploadsha\n"
        "  - uses: actions/download-artifact@downloadsha\n"
        "  - uses: peter-evans/create-pull-request@createsha\n"
        "  - uses: dtolnay/rust-toolchain@1.95.0\n"
        "  - uses: actions/checkout@checkoutsha\n"
    )

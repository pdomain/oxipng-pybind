"""Tests for GitHub Actions dependency refresh helpers."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import pytest

from scripts import update_github_actions
from tests.helpers.automation import completed_json

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

SAMPLE_HELPERS_TEXT = (
    '"""Shared workflow assertions for tests."""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "REVIEWED_ACTION_REFS = {\n"
    '    "actions/checkout": "df4cb1c069e1874edd31b4311f1884172cec0e10",\n'
    '    "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",\n'
    "}\n"
    'RUST_TOOLCHAIN_VERSION = "1.96.0"\n'
    "\n"
    "\n"
    "def load_workflow(relative: str) -> dict[str, object]:\n"
    "    return {}\n"
)


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
        return completed_json(payloads[command[-1]])

    release = update_github_actions.latest_release("actions/upload-artifact", runner=runner)

    assert release.tag == "v7.0.1"
    assert release.sha == "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    assert calls == [
        ["gh", "api", "repos/actions/upload-artifact/releases/latest"],
        ["gh", "api", "repos/actions/upload-artifact/git/ref/tags/v7.0.1"],
    ]


def test_latest_release_rejects_missing_release_tag_name() -> None:
    """Malformed latest release payloads fail before any workflow rewrite."""

    def runner(_command: list[str]) -> subprocess.CompletedProcess[str]:
        return completed_json({"name": "Release"})

    with pytest.raises(TypeError, match="did not include tag_name"):
        update_github_actions.latest_release("actions/upload-artifact", runner=runner)


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


def test_render_action_refs_block_preserves_order_and_indentation() -> None:
    """The rendered dict literal keeps mapping order and round-trips as valid Python."""
    mapping = {
        "actions/checkout": "sha-checkout",
        "actions/setup-python": "sha-setup-python",
    }

    block = update_github_actions.render_action_refs_block(mapping)

    assert block == (
        "REVIEWED_ACTION_REFS = {\n"
        '    "actions/checkout": "sha-checkout",\n'
        '    "actions/setup-python": "sha-setup-python",\n'
        "}"
    )
    _, _, dict_literal = block.partition(" = ")
    parsed = ast.literal_eval(dict_literal)
    assert parsed == mapping
    assert list(parsed) == list(mapping)


def test_parse_reviewed_allowlist_reads_current_refs_and_version() -> None:
    """Parsing recovers the allowlist's key order, SHAs, and Rust toolchain version."""
    allowlist = update_github_actions.parse_reviewed_allowlist(SAMPLE_HELPERS_TEXT)

    assert allowlist.action_refs == {
        "actions/checkout": "df4cb1c069e1874edd31b4311f1884172cec0e10",
        "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",
    }
    assert list(allowlist.action_refs) == ["actions/checkout", "actions/setup-python"]
    assert allowlist.rust_toolchain == "1.96.0"


def test_sync_reviewed_refs_rewrites_dict_and_version(tmp_path: Path) -> None:
    """Syncing rewrites both the SHA allowlist and the Rust version, leaving other lines alone."""
    helpers_path = tmp_path / "workflows.py"
    helpers_path.write_text(SAMPLE_HELPERS_TEXT, encoding="utf-8")

    changed = update_github_actions.sync_reviewed_refs(
        helpers_path,
        releases={
            "actions/checkout": update_github_actions.ActionRelease("v6.0.3", "newchecksha0"),
            "actions/setup-python": update_github_actions.ActionRelease("v6.1.0", "newsetuppython"),
        },
        rust_toolchain="1.97.0",
    )

    assert changed is True
    updated_text = helpers_path.read_text(encoding="utf-8")
    assert updated_text == (
        '"""Shared workflow assertions for tests."""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "REVIEWED_ACTION_REFS = {\n"
        '    "actions/checkout": "newchecksha0",\n'
        '    "actions/setup-python": "newsetuppython",\n'
        "}\n"
        'RUST_TOOLCHAIN_VERSION = "1.97.0"\n'
        "\n"
        "\n"
        "def load_workflow(relative: str) -> dict[str, object]:\n"
        "    return {}\n"
    )


def test_sync_reviewed_refs_returns_false_when_values_already_match(tmp_path: Path) -> None:
    """No file rewrite occurs, and False is returned, when the allowlist is already current."""
    helpers_path = tmp_path / "workflows.py"
    helpers_path.write_text(SAMPLE_HELPERS_TEXT, encoding="utf-8")

    changed = update_github_actions.sync_reviewed_refs(
        helpers_path,
        releases={
            "actions/checkout": update_github_actions.ActionRelease(
                "v6.0.2", "df4cb1c069e1874edd31b4311f1884172cec0e10"
            ),
            "actions/setup-python": update_github_actions.ActionRelease(
                "v6.0.1", "a309ff8b426b58ec0e2a45f0f869d46889d02405"
            ),
        },
        rust_toolchain="1.96.0",
    )

    assert changed is False
    assert helpers_path.read_text(encoding="utf-8") == SAMPLE_HELPERS_TEXT


def test_sync_makefile_rust_version_rewrites_pin(tmp_path: Path) -> None:
    """Syncing rewrites the RUST_VERSION pin while leaving other Makefile lines alone."""
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "RUST_VERSION := 1.96.0\n\nsetup:\n\trustup toolchain install $(RUST_VERSION)\n",
        encoding="utf-8",
    )

    changed = update_github_actions.sync_makefile_rust_version(makefile, rust_toolchain="1.97.0")

    assert changed is True
    assert makefile.read_text(encoding="utf-8") == (
        "RUST_VERSION := 1.97.0\n\nsetup:\n\trustup toolchain install $(RUST_VERSION)\n"
    )


def test_sync_makefile_rust_version_returns_false_when_already_current(tmp_path: Path) -> None:
    """No rewrite occurs, and False is returned, when the pin already matches."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("RUST_VERSION := 1.97.0\n", encoding="utf-8")

    changed = update_github_actions.sync_makefile_rust_version(makefile, rust_toolchain="1.97.0")

    assert changed is False
    assert makefile.read_text(encoding="utf-8") == "RUST_VERSION := 1.97.0\n"


def test_sync_makefile_rust_version_rejects_missing_pin(tmp_path: Path) -> None:
    """A Makefile without a RUST_VERSION assignment fails loudly instead of silently."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("setup:\n\techo hi\n", encoding="utf-8")

    with pytest.raises(ValueError, match="RUST_VERSION assignment not found"):
        update_github_actions.sync_makefile_rust_version(makefile, rust_toolchain="1.97.0")


def test_render_review_report_emits_changed_entries_only() -> None:
    """The report lists only actions whose SHA changed, plus a changed Rust toolchain."""
    old_refs = {
        "actions/checkout": "df4cb1c069e1874edd31b4311f1884172cec0e10",
        "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",
    }
    releases = {
        "actions/checkout": update_github_actions.ActionRelease(
            "v6.0.3", "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        ),
        "actions/setup-python": update_github_actions.ActionRelease(
            "v6.0.1", "a309ff8b426b58ec0e2a45f0f869d46889d02405"
        ),
    }

    report = update_github_actions.render_review_report(
        old_refs=old_refs,
        releases=releases,
        old_rust="1.96.0",
        new_rust="1.97.0",
        changed_paths=[".github/workflows/ci.yml", "tests/helpers/workflows.py"],
    )

    assert report == (
        "Reviewed GitHub Action pin updates:\n"
        "\n"
        "  actions/checkout\n"
        "    repo:      https://github.com/actions/checkout\n"
        "    version:   v6.0.3\n"
        "    sha:       df4cb1c0 -> a1b2c3d4\n"
        "    changelog: https://github.com/actions/checkout/releases/tag/v6.0.3\n"
        "\n"
        "  dtolnay/rust-toolchain\n"
        "    repo:      https://github.com/rust-lang/rust\n"
        "    version:   1.96.0 -> 1.97.0\n"
        "    changelog: https://github.com/rust-lang/rust/releases/tag/1.97.0\n"
        "\n"
        "Updated files:\n"
        "  .github/workflows/ci.yml\n"
        "  tests/helpers/workflows.py"
    )


def test_render_review_report_reports_already_matching_when_nothing_changed() -> None:
    """An unchanged allowlist and Rust version, with no updated files, prints one line."""
    report = update_github_actions.render_review_report(
        old_refs={"actions/checkout": "sha-checkout"},
        releases={
            "actions/checkout": update_github_actions.ActionRelease("v6.0.2", "sha-checkout"),
        },
        old_rust="1.96.0",
        new_rust="1.96.0",
        changed_paths=[],
    )

    assert report == "GitHub Action pins already match the latest reviewed releases."


def test_render_review_report_marks_new_action_without_prior_sha() -> None:
    """An action with no prior allowlist entry renders its old SHA as `(new)`."""
    report = update_github_actions.render_review_report(
        old_refs={},
        releases={
            "actions/checkout": update_github_actions.ActionRelease(
                "v6.0.2", "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
            )
        },
        old_rust="1.96.0",
        new_rust="1.96.0",
        changed_paths=[".github/workflows/ci.yml"],
    )

    assert "sha:       (new) -> a1b2c3d4" in report
    assert "Updated files:\n  .github/workflows/ci.yml" in report

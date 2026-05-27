"""Static checks for GitHub workflow security policy."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE_TOKEN_WORKFLOWS = (
    ".github/workflows/upstream-bump.yml",
    ".github/workflows/dependency-health.yml",
)


def test_write_token_workflows_pin_create_pull_request_to_sha() -> None:
    """Write-scoped PR creation actions must be pinned to immutable SHAs."""
    for relative in WRITE_TOKEN_WORKFLOWS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "peter-evans/create-pull-request@" in text
        assert "persist-credentials: false" in text
        for line in text.splitlines():
            if "peter-evans/create-pull-request@" in line:
                ref = line.rsplit("@", 1)[1].strip()
                assert len(ref) == 40
                assert all(char in "0123456789abcdef" for char in ref)


def test_upstream_bump_auto_merge_is_gated_by_ci_and_wheels() -> None:
    """Native dependency bump PRs auto-merge only after required automation gates."""
    text = (ROOT / ".github/workflows/upstream-bump.yml").read_text(encoding="utf-8")

    assert "Run CI before opening PR" in text
    assert "Wait for wheel workflow" in text
    assert "gh pr merge" in text
    assert "--auto" in text
    assert "--merge" in text
    assert "--squash" not in text
    assert text.index("Wait for wheel workflow") < text.index("Enable auto-merge")


def test_upstream_bump_docs_describe_ci_gated_auto_merge() -> None:
    """Process docs must document automation-gated auto-merge."""
    text = (ROOT / "docs/process/upstream-bumps.md").read_text(encoding="utf-8").lower()

    assert "auto-merge" in text
    assert "ci and wheel checks pass" in text
    assert "human review is required" not in text


def test_dependency_refresh_auto_merge_is_ci_gated() -> None:
    """Dependency refresh PRs auto-merge through branch protection after audits and CI."""
    text = (ROOT / ".github/workflows/dependency-health.yml").read_text(encoding="utf-8")

    assert "Run dependency audits" in text
    assert "Run CI" in text
    assert "gh pr merge" in text
    assert "--auto" in text
    assert "--merge" in text
    assert "--squash" not in text
    assert text.index("Create pull request") < text.index("Enable auto-merge")


def test_dependency_refresh_docs_describe_ci_gated_auto_merge() -> None:
    """Dependency health docs must document automation-gated auto-merge."""
    text = (ROOT / "docs/process/dependency-health.md").read_text(encoding="utf-8").lower()

    assert "auto-merge" in text
    assert "audits and ci pass" in text
    assert "review lockfile diffs before merge" not in text


def test_wheel_tag_checker_uses_only_stdlib_dependencies() -> None:
    """Wheel workflow runs the tag checker before installing project dependencies."""
    workflow = (ROOT / ".github/workflows/wheels.yml").read_text(encoding="utf-8")
    script = (ROOT / "scripts/check_wheel_tags.py").read_text(encoding="utf-8")

    assert "python scripts/check_wheel_tags.py" in workflow
    assert "import tomlkit" not in script
    assert "from packaging" not in script
    assert "import packaging" not in script


def test_failed_check_retry_is_single_attempt_and_delayed() -> None:
    """Transient CI failures get one delayed failed-job rerun without retry loops."""
    text = (ROOT / ".github/workflows/retry-failed-checks.yml").read_text(encoding="utf-8")

    for workflow in ("ci", "api-matrix", "wheels"):
        assert f"- {workflow}" in text
    assert "actions: write" in text
    assert "run_attempt == 1" in text
    assert "sleep 600" in text
    assert "gh run rerun" in text
    assert "--failed" in text

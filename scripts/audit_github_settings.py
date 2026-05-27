#!/usr/bin/env python3
"""Audit GitHub repository settings used by project automation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUIRED_CHECKS = (
    "source ci",
    "wheels-linux-x86_64",
    "wheels-linux-aarch64",
    "wheels-macos-x86_64",
    "wheels-macos-aarch64",
    "wheels-windows-x86_64",
    "sdist",
)
DEFAULT_REQUIRED_SECRETS = ("DEPENDENCY_REFRESH_TOKEN", "UPSTREAM_BUMP_TOKEN")
GITHUB_API_HEADERS = (
    "Accept: application/vnd.github+json",
    "X-GitHub-Api-Version: 2022-11-28",
)

GhRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class AuditLine:
    """One audited setting result."""

    passed: bool
    message: str


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


def gh_api(endpoint: str, runner: GhRunner) -> dict[str, object]:
    """Fetch and decode a GitHub API endpoint with gh."""
    command = ["gh", "api"]
    for header in GITHUB_API_HEADERS:
        command.extend(["-H", header])
    command.append(endpoint)
    result = runner(command)
    return cast("dict[str, object]", json.loads(result.stdout))


def current_repo(runner: GhRunner) -> str:
    """Return the current repository name as owner/name."""
    result = runner(["gh", "repo", "view", "--json", "nameWithOwner"])
    payload = cast("dict[str, object]", json.loads(result.stdout))
    return str(payload["nameWithOwner"])


def required_check_names(protection: dict[str, object]) -> set[str]:
    """Return required status and check names from a branch protection payload."""
    required_status_checks = protection.get("required_status_checks")
    if not isinstance(required_status_checks, dict):
        return set()
    status_checks = cast("dict[str, object]", required_status_checks)

    names: set[str] = set()
    contexts = status_checks.get("contexts", [])
    if isinstance(contexts, list):
        names.update(str(context) for context in cast("list[object]", contexts))

    checks = status_checks.get("checks", [])
    if isinstance(checks, list):
        for check in cast("list[object]", checks):
            if isinstance(check, dict):
                check_payload = cast("dict[str, object]", check)
                if check_payload.get("context"):
                    names.add(str(check_payload["context"]))
    return names


def available_secret_names(secrets_payload: dict[str, object]) -> set[str]:
    """Return repository secret names exposed by the GitHub Actions API."""
    secrets = secrets_payload.get("secrets", [])
    if not isinstance(secrets, list):
        return set()
    return {
        str(cast("dict[str, object]", secret)["name"])
        for secret in cast("list[object]", secrets)
        if isinstance(secret, dict)
        and isinstance(cast("dict[str, object]", secret).get("name"), str)
    }


def audit_settings(
    repo: str,
    *,
    required_checks: Sequence[str] = DEFAULT_REQUIRED_CHECKS,
    required_secrets: Sequence[str] = DEFAULT_REQUIRED_SECRETS,
    runner: GhRunner = run_gh,
) -> list[AuditLine]:
    """Audit repository settings that the GitHub API exposes reliably."""
    repo_payload = gh_api(f"repos/{repo}", runner)
    default_branch = str(repo_payload.get("default_branch", ""))
    checks: list[AuditLine] = [
        AuditLine(default_branch == "main", f"default branch is {default_branch}, expected main"),
        AuditLine(
            repo_payload.get("allow_auto_merge") is True,
            "repository auto-merge is enabled"
            if repo_payload.get("allow_auto_merge") is True
            else "repository auto-merge is disabled",
        ),
        AuditLine(
            repo_payload.get("allow_rebase_merge") is True,
            "rebase merge is enabled"
            if repo_payload.get("allow_rebase_merge") is True
            else "rebase merge is disabled",
        ),
    ]

    protection: dict[str, object]
    try:
        protection = gh_api(f"repos/{repo}/branches/{default_branch}/protection", runner)
        checks.append(AuditLine(True, f"default branch protection is enabled for {default_branch}"))
    except subprocess.CalledProcessError:
        protection = {}
        checks.append(
            AuditLine(False, f"default branch protection is missing for {default_branch}")
        )

    actual_required_checks = required_check_names(protection)
    checks.extend(
        [
            AuditLine(
                check_name in actual_required_checks,
                f"required check present: {check_name}"
                if check_name in actual_required_checks
                else f"required check missing: {check_name}",
            )
            for check_name in required_checks
        ]
    )

    secrets_payload = gh_api(f"repos/{repo}/actions/secrets", runner)
    actual_secrets = available_secret_names(secrets_payload)
    checks.extend(
        [
            AuditLine(
                secret_name in actual_secrets,
                f"required secret available: {secret_name}"
                if secret_name in actual_secrets
                else f"required secret missing: {secret_name}",
            )
            for secret_name in required_secrets
        ]
    )
    return checks


def main(argv: Sequence[str] | None = None, *, run_gh: GhRunner = run_gh) -> int:
    """Run the GitHub settings audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", help="repository to audit as owner/name; defaults to gh repo view"
    )
    parser.add_argument(
        "--required-check",
        action="append",
        dest="required_checks",
        help="required branch protection check name; repeat to override defaults",
    )
    parser.add_argument(
        "--required-secret",
        action="append",
        dest="required_secrets",
        help="required repository secret name; repeat to override defaults",
    )
    args = parser.parse_args(argv)

    repo = args.repo or current_repo(run_gh)
    checks = audit_settings(
        repo,
        required_checks=args.required_checks or DEFAULT_REQUIRED_CHECKS,
        required_secrets=args.required_secrets or DEFAULT_REQUIRED_SECRETS,
        runner=run_gh,
    )
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"{status} {check.message}")
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify required source workflows passed for a release SHA."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any

REQUIRED_WORKFLOWS = ("ci", "api-matrix")


def resolve_executable(name: str) -> str:
    """Return a full path for a required executable."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def check_required_workflows(
    runs: list[dict[str, Any]], *, sha: str, required: tuple[str, ...] = REQUIRED_WORKFLOWS
) -> list[str]:
    """Return errors for required workflows that did not complete successfully."""
    errors: list[str] = []
    for workflow in required:
        matched = [
            run
            for run in runs
            if run.get("name") == workflow
            and run.get("headSha") == sha
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
        ]
        if not matched:
            errors.append(f"{workflow} did not complete successfully for {sha}")
    return errors


def load_runs(repo: str, sha: str) -> list[dict[str, Any]]:
    """Load workflow runs for a repository commit SHA."""
    result = subprocess.run(  # noqa: S603
        [
            resolve_executable("gh"),
            "run",
            "list",
            "--repo",
            repo,
            "--commit",
            sha,
            "--json",
            "name,headSha,status,conclusion",
            "--limit",
            "100",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return list(json.loads(result.stdout))


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, validate required workflow state, and return an exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args(argv)

    errors = check_required_workflows(load_runs(args.repo, args.sha), sha=args.sha)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify required source workflows passed for a release SHA."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any, cast

WorkflowRequirement = tuple[str, str, str]
WorkflowIdByPath = dict[str, int]
REQUIRED_WORKFLOWS: tuple[WorkflowRequirement, ...] = (
    ("ci", ".github/workflows/ci.yml", "push"),
    ("api-matrix", ".github/workflows/api-matrix.yml", "push"),
)


def resolve_executable(name: str) -> str:
    """Return a full path for a required executable."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def load_workflow_ids(repo: str, required: tuple[WorkflowRequirement, ...]) -> WorkflowIdByPath:
    """Load workflow IDs for trusted workflow files."""
    required_paths = {path for _name, path, _event in required}
    result = subprocess.run(  # noqa: S603
        [
            resolve_executable("gh"),
            "workflow",
            "list",
            "--repo",
            repo,
            "--json",
            "id,path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    workflow_data = json.loads(result.stdout)
    workflow_ids: WorkflowIdByPath = {}
    if not isinstance(workflow_data, list):
        return workflow_ids

    workflow_entries = cast("list[dict[str, Any]]", workflow_data)
    for workflow in workflow_entries:
        path = workflow.get("path")
        if not isinstance(path, str) or path not in required_paths:
            continue
        workflow_id = workflow.get("id")
        if isinstance(workflow_id, int):
            workflow_ids[path] = workflow_id

    return workflow_ids


def check_required_workflows(
    runs: list[dict[str, Any]],
    *,
    sha: str,
    required: tuple[WorkflowRequirement, ...] = REQUIRED_WORKFLOWS,
    workflow_ids: WorkflowIdByPath | None = None,
) -> list[str]:
    """Return errors for required workflows that did not complete successfully."""
    workflow_ids = {} if workflow_ids is None else workflow_ids
    errors: list[str] = []
    for workflow_name, workflow_path, event in required:
        expected_workflow_id = workflow_ids.get(workflow_path)
        if expected_workflow_id is None:
            errors.append(f"{workflow_name} did not complete successfully for {sha}")
            continue
        matched = [
            run
            for run in runs
            if run.get("name") == workflow_name
            and run.get("event") == event
            and run.get("workflowDatabaseId") == expected_workflow_id
            and run.get("headSha") == sha
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
        ]
        if not matched:
            errors.append(f"{workflow_name} did not complete successfully for {sha}")
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
            "name,headSha,status,conclusion,event,workflowDatabaseId",
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

    workflow_ids = load_workflow_ids(args.repo, REQUIRED_WORKFLOWS)
    errors = check_required_workflows(
        load_runs(args.repo, args.sha),
        sha=args.sha,
        workflow_ids=workflow_ids,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

---
kind: process
status: active
last_verified: 2026-10-25
---
# Upstream Bumps

`oxipng-pybind` tracks upstream `oxipng` releases.

## How the Bump Workflow Runs

The scheduled
[`upstream-bump`](../../.github/workflows/upstream-bump.yml) workflow runs
weekly and on demand.

The prepare job uses read-only repository permissions. It:

1. Reads the latest release from upstream `oxipng`.
2. Updates `Cargo.toml`, `Cargo.lock`, `pyproject.toml`, and `uv.lock`.
3. Fetches the matching upstream source tag.
4. Copies the prior API surface manifest when the target version needs one.
5. Runs `scripts/scan_upstream_surface.py --update-docs`.
6. Prepends an upstream release note in `CHANGELOG.md` under `Release Notes`.
7. Runs the full CI gate before any pull request is published.

The publish job has write permissions. It opens or updates the bump pull
request only when files changed. The pull request body includes the upstream
surface scan summary.

The job also opens or updates one `upstream-surface` triage issue per
upstream version.

The workflow never pushes directly to `main`.

## Release Tags

[`release-tag`](../../.github/workflows/release-tag.yml) creates tags for
eligible automated upstream bump commits after they land on `main`.

It continues only when the latest `main` commit is the automated upstream bump
commit and `project.version` changed from the parent commit. For
`workflow_run` events, it also confirms that `main` still matches the completed
run.

Before tagging, the workflow runs these checks, in order:

1. `ci.yml` passes on the same commit.
2. `api-matrix.yml` passes on the same commit.
3. The strict release tag check passes.
4. No matching Git tag exists.
5. The version is absent from PyPI.

Automated tags use `v<project.version>`, such as `v10.1.1` or
`v10.1.1.post1`. See [Release Artifacts](release-artifacts.md) for tag-driven
wheel publishing.

`RELEASE_TAG_TOKEN` must be a repository secret backed by a PAT or GitHub App
token that can push tags and trigger downstream workflows. Do not use the
default `GITHUB_TOKEN` for release tags, because those tag pushes do not start
the normal wheel publishing workflow.

## How Versions Are Bumped

The Python package version is the public wrapper release version.

The Cargo package version stays SemVer-compatible. It does not need to match a
Python `.postN` release.

The `Cargo.toml` `oxi` dependency pin records the upstream `oxipng` version.

The API surface manifest records the same upstream version as the `oxi` pin.

For wrapper-only fixes, run the wrapper post bump:

```bash
uv run --group dev python scripts/bump_upstream.py --wrapper-post
```

This changes `pyproject.toml` from `10.1.1` to `10.1.1.post1`, or from
`10.1.1.post1` to `10.1.1.post2`. It also refreshes `uv.lock`.

For upstream releases, run the default bump:

```bash
uv run --group dev python scripts/bump_upstream.py
```

To pin a reviewed upstream release instead of reading the latest GitHub
release, pass its exact version:

```bash
uv run --group dev python scripts/bump_upstream.py --version 10.2.0
```

`--version` and `--wrapper-post` are mutually exclusive. Argument validation
finishes before either command edits release files.

The script checks crates.io for the target `oxipng` crate before editing
files.

If crates.io has not yet indexed the matching crate, the scheduled run exits
successfully without changing any files. It prints a message noting that the
run is retryable. The next scheduled or manual run can then pick up the same
upstream version.

If the pinned upstream version is already current, the script leaves existing
wrapper post releases unchanged.

When upstream moves from `10.1.1` to `10.2.0`, the script resets the Python
and Cargo package versions to `10.2.0` and pins `oxi` to `=10.2.0`.

Third-party GitHub Actions in write-scoped jobs must be pinned to reviewed full
commit SHAs. Review updated SHAs before merging workflow maintenance changes.

## Required Repository Settings

Use the required repository settings in [GitHub Settings](github-settings.md).

The `UPSTREAM_BUMP_TOKEN` token must be able to create pull requests so bump
PRs trigger normal PR CI checks.

## How Bump Pull Requests Merge

Upstream bump pull requests auto-merge, using a rebase merge, only after CI
and wheel checks pass. The workflow waits for wheel checks before enabling auto-merge.
The scan must also report no broken exposed mappings.

The automation command is:

```bash
gh pr merge --auto --rebase --delete-branch
```

If upstream `oxipng` changes break the wrapper, CI fails and the bump pull
request remains open for manual repair.

For manual repair, pull the PR branch, rebase it on current `main`, then merge
with the rebase merge method.

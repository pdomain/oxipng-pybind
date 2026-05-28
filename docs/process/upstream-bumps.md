# Upstream Bumps

`oxipng-pybind` tracks upstream `oxipng` releases.

## Scheduled Check

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
surface scan summary. The job also opens or updates one `upstream-surface`
triage issue per upstream version.

The workflow never pushes directly to `main`.

## Release Tags

[`release-tag`](../../.github/workflows/release-tag.yml) creates tags for
eligible automated upstream bump commits after they land on `main`.

It continues only when the latest `main` commit is the automated upstream bump
commit and `project.version` changed from the parent commit. For
`workflow_run` events, it also confirms that `main` still matches the completed
run.

Before tagging, it waits for `ci.yml` and `api-matrix.yml` to pass on the same
commit. It then checks the strict release tag, confirms that no matching Git
tag exists, and checks that the version is absent from PyPI.

Automated tags use `v<project.version>`, such as `v10.1.1` or
`v10.1.1.post1`. See [Release Artifacts](release-artifacts.md) for tag-driven
wheel publishing.

`RELEASE_TAG_TOKEN` must be a repository secret backed by a PAT or GitHub App
token that can push tags and trigger downstream workflows. Do not use the
default `GITHUB_TOKEN` for release tags, because those tag pushes do not start
the normal wheel publishing workflow.

## Version Policy

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

The script checks crates.io for the target `oxipng` crate before editing files.
If crates.io has not indexed the matching crate yet, the scheduled run exits
successfully without file changes. It prints a retryable message. The next
scheduled or manual run can pick up the same upstream version.

If the pinned upstream version is already current, the script leaves existing
wrapper post releases unchanged. When upstream moves from `10.1.1` to
`10.2.0`, the script resets the Python and Cargo package versions to `10.2.0`
and pins `oxi` to `=10.2.0`.

Third-party GitHub Actions in write-scoped jobs must be pinned to reviewed full
commit SHAs. Review updated SHAs before merging workflow maintenance changes.

## Required Repository Settings

Use the required repository settings in [GitHub Settings](github-settings.md).

The `UPSTREAM_BUMP_TOKEN` token must be able to create pull requests so bump
PRs trigger normal PR CI checks.

## Merge Policy

Upstream bump pull requests use rebase auto-merge after required checks pass.
The workflow waits for wheel checks before enabling auto-merge. The scan must
also report no broken exposed mappings.

The automation command is:

```bash
gh pr merge --auto --rebase --delete-branch
```

For manual repair, pull the PR branch, rebase it on current `main`, then merge
with the rebase merge method.

Automated upstream bump PRs are expected to auto-merge only when CI and wheel checks pass.
If upstream `oxipng` changes break the wrapper, CI fails and the bump pull request
remains open for manual repair.

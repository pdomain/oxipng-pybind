# Upstream Bumps

`oxipng-pybind` tracks upstream `oxipng` releases.

## Scheduled Check

The scheduled `.github/workflows/upstream-bump.yml` workflow:

1. Reads the latest release from `oxipng/oxipng`.
2. Updates `Cargo.toml`, `Cargo.lock`, `pyproject.toml`, and `uv.lock`.
3. Fetches the matching upstream tag into `.cache/upstream/oxipng`.
4. Copies the prior API surface manifest to the target version when needed.
5. Runs `scripts/scan_upstream_surface.py --update-docs`.
6. Runs the full repository CI.
7. Opens a pull request when files changed, including the scan summary.
8. Opens or updates one `upstream-surface` triage issue per upstream version.
9. Waits for `.github/workflows/wheels.yml` on the pull request commit.
10. Enables PR auto-merge after CI and wheel checks pass. Branch protection
    still controls the required pull request checks. The scan must also report
    no broken exposed mappings.

The workflow does not push directly to `main`.

The upstream bump workflow keeps dependency updates, source scans, and CI in a
read-only job. Only the PR and issue publication job receives write
permissions.

The prepare job uploads only the bump workspace that the publish job needs:
`Cargo.toml`, `Cargo.lock`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, API
surface docs, the target-version file, and the generated PR body section.

## Version Policy

The Python package version is the public wrapper release version.

The Cargo package version stays SemVer-compatible. It does not need to match a
Python `.postN` release.

The `Cargo.toml` `oxi` dependency pin records the upstream `oxipng` version.

The API surface manifest records the same upstream version as the `oxi` pin.

For wrapper-only fixes, run:

```bash
uv run --group dev python scripts/bump_upstream.py --wrapper-post
```

This changes `pyproject.toml` from `10.1.1` to `10.1.1.post1`, or from
`10.1.1.post1` to `10.1.1.post2`. It also refreshes `uv.lock`.

For upstream releases, run the default bump path:

```bash
uv run --group dev python scripts/bump_upstream.py
```

The script checks crates.io for the target `oxipng` crate before editing files.
If GitHub has published a release tag but crates.io has not indexed the matching
crate version yet, the scheduled run exits successfully without file changes and
prints a retryable message. The next scheduled or manual run can pick up the
same upstream version after crates.io catches up.

If the pinned upstream version is already current, the script leaves existing
wrapper post releases unchanged. If upstream moved from `10.1.1` to `10.2.0`,
the script resets the Python package version to `10.2.0`, updates the Cargo
package version to `10.2.0`, and pins `oxi` to `=10.2.0`.

Third-party GitHub Actions in write-scoped jobs must be pinned to reviewed full
commit SHAs. Review updated SHAs before merging workflow maintenance changes.

## Required Repository Settings

Use the required repository settings in
[GitHub Settings](github-settings.md). CI is continuous integration.

The `UPSTREAM_BUMP_TOKEN` token must be able to create pull requests so bump
PRs trigger normal PR CI checks.

## Merge Policy

Upstream bump pull requests use rebase auto-merge after required checks pass.
The automation command is `gh pr merge --auto --rebase`.

Native dependency bump PRs are expected to auto-merge when CI and wheel checks
pass. If upstream `oxipng` changes break the wrapper, CI fails and the bump PR
remains open for manual repair.

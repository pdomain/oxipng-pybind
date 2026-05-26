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
8. Opens or updates one `upstream-surface` triage issue per upstream version
   when the scan detects new unexposed surface.
9. Enables auto-merge only when CI passes and the scan reports no broken
   exposed mappings.

The workflow does not push directly to `main`.

The upstream bump workflow keeps dependency updates, source scans, and CI in a
read-only job. Only the PR and issue publication job receives write
permissions.

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

If the pinned upstream version is already current, the script leaves existing
wrapper post releases unchanged. If upstream moved from `10.1.1` to `10.2.0`,
the script resets the Python package version to `10.2.0`, updates the Cargo
package version to `10.2.0`, and pins `oxi` to `=10.2.0`.

Mutable action tags should be replaced with full commit SHAs during
release-hardening maintenance. Review the resolved SHAs before merge.

## Required Repository Settings

Enable these GitHub settings for CI-gated auto-merge. CI is continuous
integration.

- Add an `UPSTREAM_BUMP_TOKEN` repository secret. The token must be able to
  create pull requests and enable auto-merge so bump PRs trigger normal PR CI
  checks and can merge through protected-branch requirements.
- Allow GitHub Actions to create and approve pull requests.
- Enable auto-merge for the repository.
- Protect `main`.
- Require the `ci` workflow to pass before merging.

If upstream `oxipng` changes break the wrapper, CI fails and the bump PR remains
open for manual repair.

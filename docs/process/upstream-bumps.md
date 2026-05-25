# Upstream Bumps

`se-pyoxipng` tracks upstream `oxipng` releases.

The scheduled `upstream-bump.yml` workflow:

1. Reads the latest release from `oxipng/oxipng`.
2. Updates `Cargo.toml`, `Cargo.lock`, `pyproject.toml`, and `uv.lock`.
3. Runs the full repository CI.
4. Opens a pull request when files changed.
5. Enables auto-merge for that pull request.

The workflow does not push directly to `main`.

## Required Repository Settings

Enable these GitHub settings for CI-gated auto-merge:

- Add an `UPSTREAM_BUMP_TOKEN` repository secret. The token must be able to
  create pull requests and enable auto-merge so bump PRs trigger normal PR CI
  checks and can merge through protected-branch requirements.
- Allow GitHub Actions to create and approve pull requests.
- Enable auto-merge for the repository.
- Protect `main`.
- Require the `ci` workflow to pass before merging.

If upstream `oxipng` changes break the wrapper, CI fails and the bump PR remains
open for manual repair.

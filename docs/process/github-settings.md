# GitHub Settings

Repository automation assumes these GitHub settings are enabled.

- Protect `main`.
- Allow rebase merges and disable merge commits and squash merges.
- Enable repository auto-merge.
- Require the `ci` workflow before merging.
- Require the `wheels` workflow before merging release-relevant and upstream
  bump pull requests.
- Allow GitHub Actions to create and approve pull requests.
- Add an `UPSTREAM_BUMP_TOKEN` repository secret that can create pull requests.
- Add a `DEPENDENCY_REFRESH_TOKEN` repository secret that can write contents
  and pull requests.

Automation must use `gh pr merge --auto --rebase`. Human pull requests must
also merge by rebase after required checks pass.

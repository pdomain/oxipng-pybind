# GitHub Settings

Repository automation assumes these GitHub settings are enabled.

Maintainers can audit the API-visible settings with:
`uv run --group dev python scripts/audit_github_settings.py`.

- Protect `main`.
- Allow rebase merges and disable merge commits and squash merges.
- Enable repository auto-merge.
- Require the `source ci` check before merging.
- Require the wheel matrix checks before merging release-relevant and upstream
  bump pull requests:
  - `wheels-linux-x86_64`
  - `wheels-linux-aarch64`
  - `wheels-macos-x86_64`
  - `wheels-macos-aarch64`
  - `wheels-windows-x86_64`
  - `sdist`
- Allow GitHub Actions to create and approve pull requests.
- Add an `UPSTREAM_BUMP_TOKEN` repository secret that can create pull requests.
- Add a `DEPENDENCY_REFRESH_TOKEN` repository secret that can write contents
  and pull requests.

Automation must use `gh pr merge --auto --rebase`. Human pull requests must
also merge by rebase after required checks pass.

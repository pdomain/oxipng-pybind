# GitHub Settings

Repository automation assumes these GitHub settings are enabled.

Maintainers can audit API-visible settings with:

```bash
uv run --group dev python scripts/audit_github_settings.py
```

## Required Settings

- Protect `main`.
- Allow only rebase merges. Disable merge commits and squash merges.
- Enable repository auto-merge.
- Require the split source checks before merging:
  - `pre-commit checks`
  - `python tests`
  - `rust tests`
  - `dependency audit`
  - `release file checks`
  - `public api py3.10`
  - `public api py3.11`
  - `public api py3.12`
  - `public api py3.13`
  - `public api py3.14`
- Allow GitHub Actions to create and approve pull requests.

## Wheel Checks

Do not globally require path-filtered wheel checks, because dependency refresh
PRs may not trigger them.

Upstream bump automation waits for `.github/workflows/wheels.yml` before
enabling auto-merge.

Review these wheel checks when configuring release-relevant branch rules:

- `wheels-linux-x86_64`
- `wheels-linux-x86_64-py311`
- `wheels-linux-aarch64`
- `wheels-linux-aarch64-py311`
- `wheels-macos-x86_64`
- `wheels-macos-x86_64-py311`
- `wheels-macos-aarch64`
- `wheels-macos-aarch64-py311`
- `wheels-windows-x86_64`
- `wheels-windows-x86_64-py311`
- `sdist`

## Secrets

- Add `UPSTREAM_BUMP_TOKEN`. It must create pull requests. See
  [Upstream Bumps](upstream-bumps.md#required-repository-settings).
- Add `DEPENDENCY_REFRESH_TOKEN`. It must write contents and pull requests.
  See [Dependency Health](dependency-health.md#scheduled-refresh).

## Merge Method

Automation must use `gh pr merge --auto --rebase`. Human pull requests must
also use rebase merges after required checks pass.

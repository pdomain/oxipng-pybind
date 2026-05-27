# Dependency Health

Dependency security is checked by scheduled automation and by manual commands.

`cargo deny check` audits Rust dependencies with the RustSec advisory database.
`pip-audit --local` audits the installed Python development environment.
`make py-audit-lock` runs `uv audit --locked` against the locked Python project
dependency set.

## Manual Checks

Run the normal audit gate before dependency work:

```bash
make dependency-audit
```

Run a full lockfile refresh before opening dependency update PRs:

```bash
make dependency-refresh-check
```

For CVE-driven updates, prefer the smallest lockfile change that clears the
advisory. A CVE is a public security advisory.

If the vulnerable dependency is transitive, update the direct parent dependency
first. If no fixed version exists, document the advisory ID, affected path,
exploitability for this project, and temporary mitigation in the PR body.

Do not ignore advisories in `deny.toml` without a dated comment and an issue.

## Scheduled Refresh

`.github/workflows/dependency-health.yml` runs weekly and on demand.

The prepare job has read-only repository permissions. It refreshes `uv.lock` and
`Cargo.lock`, then runs dependency audits and full CI.

A separate write-scoped publish job opens or updates the dependency refresh PR
only if lockfiles changed.

Set the `DEPENDENCY_REFRESH_TOKEN` repository secret to a fine-grained PAT or
GitHub App token that can write contents and pull requests. The workflow
requires this explicit token so dependency refresh PRs trigger normal CI
workflows. PRs created with the default `GITHUB_TOKEN` do not trigger those
downstream workflow events.

The publish job limits committed paths to `Cargo.lock` and `uv.lock`.

Dependency refresh PRs enable auto-merge after audits and CI pass. Branch
protection remains the merge gate, so failed checks leave the PR open for
manual repair.

Third-party GitHub Actions in write-scoped dependency refresh jobs must be
pinned to reviewed full commit SHAs.

# Dependency Health

Dependency security is checked in two layers:

- `cargo deny check` audits Rust dependencies with the RustSec advisory database.
- `pip-audit --local` audits the installed Python development environment.

Run the normal audit gate locally with:

```bash
make dependency-audit
```

Run a full lockfile refresh before opening dependency update PRs with:

```bash
make dependency-refresh-check
```

For CVE-driven updates, prefer the smallest lockfile change that clears the
advisory. If the vulnerable dependency is transitive, update the direct parent
dependency first. If no fixed version exists, document the advisory ID, affected
path, exploitability for this project, and temporary mitigation in the PR body.
Do not ignore advisories in `deny.toml` without a dated comment and an issue.

## Scheduled Refresh

`.github/workflows/dependency-health.yml` runs weekly and on demand. The prepare
job has read-only repository permissions, refreshes `uv.lock` and `Cargo.lock`,
then runs dependency audits and full CI. A separate write-scoped publish job
opens or updates the dependency refresh PR only if lockfiles changed.

Do not enable auto-merge for dependency refresh PRs by default. Review lockfile
diffs before merge, especially when CVE remediation pulls major transitive
updates.

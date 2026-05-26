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

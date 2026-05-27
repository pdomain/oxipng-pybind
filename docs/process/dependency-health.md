# Dependency Health

Dependency security is checked by automation and by local commands.

Rust dependencies are checked with `cargo deny check`.

Python lockfile dependencies are checked with `uv audit --locked`.

## Manual Checks

Run the normal audit gate before dependency work:

```bash
make dependency-audit
```

Run a full lockfile refresh before dependency update work:

```bash
make dependency-refresh-check
```

For audit-only checks, run `make dependency-audit`.

For third-party notice drift only, run:

```bash
make third-party-notices-check
```

For CVE (Common Vulnerabilities and Exposures) updates, prefer the smallest
lockfile change that clears the advisory.

If the vulnerable dependency is transitive, update the direct parent dependency
first.

If no fixed version exists, document these items in the PR body:

- advisory ID
- affected path
- project exploitability
- temporary mitigation

Do not ignore advisories in `deny.toml` without a dated comment and an issue.

## Scheduled Refresh

`.github/workflows/dependency-health.yml` runs weekly and on demand.

The prepare job has read-only repository permissions. It refreshes `uv.lock` and
`Cargo.lock`, refreshes pre-commit hook revisions, applies lint fixes, then
runs dependency audits and full CI.

A separate write-scoped publish job opens or updates the dependency refresh PR
only if dependency refresh, hook refresh, or generated-file fix steps changed
files.

The publish job commits the changed files detected by the prepare job. This
keeps `Cargo.lock`, `uv.lock`, `.pre-commit-config.yaml`, and lint-generated
fixes together when refresh automation changes them.

Dependency refresh PRs enable auto-merge after audits and CI pass. Branch
protection remains the merge gate, so failed checks leave the PR open for
manual repair.

Use the required repository settings in
[GitHub Settings](github-settings.md). Dependency refresh PRs use rebase
auto-merge. The automation command is `gh pr merge --auto --rebase`.

Set the `DEPENDENCY_REFRESH_TOKEN` repository secret.

Use a fine-grained PAT or GitHub App token that can write contents and pull
requests.

The workflow uses this explicit token so refresh PRs trigger normal PR CI.

PRs created with the default `GITHUB_TOKEN` do not trigger those downstream
workflow events.

## Release Classification

Dependency refresh PRs are classified before publication.

`no-release-needed` means only tooling or non-runtime dependency state changed.

These PRs enable auto-merge after audits and CI pass.

`release-needed` means the refresh may affect published artifacts.

Examples include:

- a runtime Cargo dependency change
- a Python `[project.dependencies]` change

These PRs stay open for an explicit wrapper version bump before merge.

Branch protection remains the merge gate.

Failed checks leave the PR open for repair.

Third-party GitHub Actions in write-scoped dependency refresh jobs must be
pinned to reviewed full commit SHAs.

## Third-Party Notices

`THIRD_PARTY_NOTICES.md` is generated from locked Cargo metadata. Regenerate it
after shipped Rust dependencies change:

```bash
make third-party-notices
```

Python runtime notices stay empty while `[project.dependencies]` is empty.

# Dependency Health

Automation and local commands check dependency health.

Rust dependencies are checked with `cargo deny check`.
Python lockfile dependencies are checked with `uv audit --locked`.

## Manual Checks

Run the audit gate before dependency work:

```bash
make dependency-audit
```

Run a full refresh before dependency update work:

```bash
make dependency-refresh-check
```

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

`.github/workflows/dependency-health.yml` runs weekly and on demand. It owns
scheduled dependency refreshes.

The prepare job has read-only repository permissions. It refreshes `uv.lock` and
`Cargo.lock`, pre-commit hook revisions, reviewed GitHub Action pins, and
third-party notices. It then applies lint fixes, runs dependency audits, and
runs full CI.

The "Run CI" step records its result as the `ci-passed` job output and does not
abort the job on failure. This matters because a GitHub Action pin bump produces
an unreviewed SHA, which the reviewed-action-ref security gate rejects by design,
so `make ci` fails. The prepare job therefore continues, detects changes
regardless of CI outcome, and lets the publish job open a PR for human review.

A separate write-scoped publish job opens or updates a dependency refresh PR
only when the prepare job changed files. It labels the PR `ci-passed` when local
CI was green and `ci-failed` when it was red, and threads the `ci-passed` value
into the PR body. A `ci-failed` PR opens as a normal PR awaiting human review and
never auto-merges; review the new pins (or other changes) before merge.

The prepare job runs `scripts/classify_dependency_refresh.py --base-ref origin/main`
after it detects changed files. The publish job adds the classifier label and
reason to the PR.

The publish job commits only the changed files from the prepare job. This keeps
lockfiles, `.pre-commit-config.yaml`, workflow action pins, generated notices,
and lint fixes in one PR.

`no-release-needed` PRs with a green prepare-job CI (`ci-passed`) may auto-merge
after required checks pass. `release-needed` PRs are opened but not auto-merged;
they stay open for wrapper version review. Any `ci-failed` PR also stays open for
human review and never auto-merges, regardless of release classification.

Branch protection remains the merge gate, so failed checks leave the PR open
for manual repair.

Use the required settings and token from
[GitHub Settings](github-settings.md). Dependency refresh PRs use rebase
auto-merge.

Third-party GitHub Actions in write-scoped workflows must be pinned to reviewed
full commit SHAs. `scripts/update_github_actions.py` updates only the reviewed
allowlist of workflow actions. It also updates the `dtolnay/rust-toolchain`
selector from the latest stable Rust release tag.

## Local Action Pin Sign-Off

The scheduled refresh PR fails on purpose when a pin bump introduces an
unreviewed SHA: CI bumps the workflow YAML but not the reviewed allowlist in
`tests/helpers/workflows.py`, so the security gate rejects the mismatch. Turning
that PR green is the human sign-off.

Do it locally:

```bash
make refresh-actions
```

This bumps the workflow pins, syncs `REVIEWED_ACTION_REFS` and
`RUST_TOOLCHAIN_VERSION` to match, and prints a review report with each action's
repository and changelog link. Review the diff and the linked release notes,
then commit. The sync mode is local only; CI still runs the script without
`--sync-reviewed-refs` so the gate keeps its meaning.

To carry the sign-off onto the open refresh PR:

```bash
make accept-refresh-pr
```

This rebases `automation/dependency-refresh` on `main`, syncs the allowlist,
runs full CI, pushes the fix, and prints the `gh pr merge` command. It stops
before merging; run the printed command yourself after checks pass.

## Release Classification

Dependency refresh PRs are classified before publication.

`no-release-needed` means only tooling or non-runtime dependency state changed.

`release-needed` means the refresh may affect published artifacts.
Examples include:

- a runtime Cargo dependency change
- a Python `[project.dependencies]` change

## Third-Party Notices

`THIRD_PARTY_NOTICES.md` is generated from locked Cargo metadata. Regenerate it
after shipped Rust dependencies change:

```bash
make third-party-notices
```

Python runtime notices stay empty while `[project.dependencies]` is empty.

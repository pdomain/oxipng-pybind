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

## Dependency Overrides

`[tool.uv] override-dependencies` in `pyproject.toml` forces a transitive
dependency to a version its parent does not request. Each override needs a
comment naming the advisory or reason it exists.

Re-audit every override after each dependency upgrade. An override can outlive
its reason: the parent may ship a fix, or the forced version may drift far
enough to break the parent. For each override, confirm three things:

- the advisory or reason still applies
- the parent still works with the forced version
- the floor still clears the advisory

`make override-audit` automates the first check. It re-resolves the project
without its overrides in an isolated virtual project, then fails if any
override's floor is already met by the natural resolution — meaning the
override is removable. The weekly refresh runs it as a dedicated step, so a
parent that ships a fix surfaces the override for removal. It stays out of
`make ci` to avoid blocking unrelated pull requests.

Remove the override once the parent requests a safe version on its own.

Current overrides:

- `click>=8.3.3` — `gitlint-core[trusted-deps]` pins the vulnerable
  `click==8.1.3` (PYSEC-2026-2132, command injection in `click.edit()`).
  `click` is a dev-only transitive dependency, and commit-msg linting runs in
  pre-commit's own environment, so the override only affects the audited
  lockfile. Remove it if `gitlint` ships a release that drops the pin.

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

This bumps the workflow pins, syncs `REVIEWED_ACTION_REFS`,
`RUST_TOOLCHAIN_VERSION`, and the `Makefile` `RUST_VERSION` bootstrap pin to
match, and prints a review report with each action's repository and changelog
link. Review the diff and the linked release notes,
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

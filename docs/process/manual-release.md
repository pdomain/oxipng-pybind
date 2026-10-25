---
kind: runbook
status: active
last_verified: 2026-10-25
---
# Manual Release Process

Use this process to publish a release by hand.

For artifact rules, supported wheel tags, and Trusted Publishing setup, see
[Release Artifacts](release-artifacts.md).

## Agent Index

- **Kind:** runbook
- **Status:** active
- **Read when:** rehearsing a release on TestPyPI, pushing a release tag, or
  monitoring a production PyPI publish.
- **Search terms:** manual release, TestPyPI rehearsal, production PyPI,
  release tag, wheels workflow, publish monitoring.

## Trigger

Run this procedure after a prepared release passes its exact-commit source
checks and TestPyPI rehearsal. Pushing the final `v*` tag starts the production
`wheels` workflow.

## Preconditions

The operator needs permission to dispatch Actions workflows, push repository
tags, and approve the `testpypi` and `pypi` GitHub environments when required.
Trusted Publishing must match the settings in
[Release Artifacts](release-artifacts.md).

The release commit must be on `origin/main`, and the worktree must be clean.
Its version, changelog, lockfiles, dependency notices, and documentation must
already be committed.

## Steps

Use this path after the release commit and TestPyPI rehearsal pass. Run every
command from a clean `main` checkout.

1. Record the version, tag, and exact release commit.

   ```bash
   release_version=$(uv run --no-sync --group dev python -c \
     'from scripts._toml_compat import load_file; print(load_file("pyproject.toml")["project"]["version"])')
   release_tag="v${release_version}"
   release_sha=$(git rev-parse HEAD)
   ```

2. Confirm that local `main`, remote `main`, and the release commit match.
   Confirm that the worktree is clean and that the version is unused on PyPI.

   ```bash
   test "$(git branch --show-current)" = main
   test -z "$(git status --porcelain)"
   git fetch origin main --tags
   test "$release_sha" = "$(git rev-parse origin/main)"
   test "$(curl -sS -o /dev/null -w '%{http_code}' \
     "https://pypi.org/pypi/oxipng-pybind/${release_version}/json")" = 404
   ```

3. Find the exact-commit `ci`, `api-matrix`, and TestPyPI rehearsal runs.
   Confirm that all three passed on `release_sha`.

   ```bash
   ci_run_id=$(gh run list --workflow ci.yml --commit "$release_sha" --limit 1 \
     --json databaseId --jq '.[0].databaseId')
   api_matrix_run_id=$(gh run list --workflow api-matrix.yml \
     --commit "$release_sha" --limit 1 --json databaseId \
     --jq '.[0].databaseId')
   testpypi_run_id=$(gh run list --workflow wheels.yml \
     --event workflow_dispatch --commit "$release_sha" --limit 1 \
     --json databaseId --jq '.[0].databaseId')
   test -n "$ci_run_id"
   test -n "$api_matrix_run_id"
   test -n "$testpypi_run_id"
   gh run view "$ci_run_id" --json headSha,conclusion,url
   gh run view "$api_matrix_run_id" --json headSha,conclusion,url
   gh run view "$testpypi_run_id" --json headSha,conclusion,url
   test "$(gh run view "$ci_run_id" --json headSha --jq .headSha)" = "$release_sha"
   test "$(gh run view "$api_matrix_run_id" --json headSha --jq .headSha)" = "$release_sha"
   test "$(gh run view "$testpypi_run_id" --json headSha --jq .headSha)" = "$release_sha"
   test "$(gh run view "$ci_run_id" --json conclusion --jq .conclusion)" = success
   test "$(gh run view "$api_matrix_run_id" --json conclusion --jq .conclusion)" = success
   test "$(gh run view "$testpypi_run_id" --json conclusion --jq .conclusion)" = success
   test "$(gh run view "$testpypi_run_id" --json jobs --jq \
     '.jobs[] | select(.name == "publish-testpypi") | .conclusion')" = success
   ```

4. Create the tag locally before running the validator. The validator resolves
   the tag and proves that its commit is contained in `origin/main`.

   ```bash
   test -z "$(git ls-remote --tags origin "refs/tags/${release_tag}")"
   if git show-ref --verify --quiet "refs/tags/${release_tag}"; then
     test "$(git rev-list -n1 "$release_tag")" = "$release_sha"
   else
     git tag "$release_tag" "$release_sha"
   fi
   uv run --no-sync --group dev python scripts/validate_release_tag.py \
     --tag "$release_tag"
   ```

5. Push only the verified tag. The push starts the production `wheels`
   workflow.

   ```bash
   git push origin "refs/tags/${release_tag}"
   ```

6. Find the tag-triggered run. GitHub may take a few seconds to return it.
   Repeat the list command until it returns a URL.

   ```bash
   production_run_url=
   for attempt in {1..30}; do
     production_run_url=$(gh run list --workflow wheels.yml --event push \
       --branch "$release_tag" --limit 1 --json url --jq '.[0].url')
     test -n "$production_run_url" && break
     sleep 2
   done
   test -n "$production_run_url"
   production_run_id=${production_run_url##*/}
   test "$(gh run view "$production_run_id" --json headSha --jq .headSha)" = \
     "$release_sha"
   ```

7. Monitor that exact run. Inspect every job conclusion.

   ```bash
   echo "$production_run_url"
   gh run watch "$production_run_id" --exit-status
   gh run view "$production_run_id" --json jobs \
     --jq '.jobs[] | [.name, .status, .conclusion] | @tsv'
   ```

   The production run must pass `wait for release checks`,
   `validate release tag`, `sdist`, every wheel job, and `publish`.
   It must skip `publish-testpypi`.

8. Verify the final registry state. A complete release has one source
   distribution and ten wheels.

   ```bash
   curl -fsSL \
     "https://pypi.org/pypi/oxipng-pybind/${release_version}/json" |
     jq '{version: .info.version, file_count: (.urls | length), files: [.urls[].filename]}'
   ```

   Confirm `version` equals `release_version`, `file_count` is `11`, and files
   cover both ABI3 wheel sets and all supported platforms.

Stop if any commit, version, run conclusion, or artifact check differs from the
expected value. Do not move the tag after PyPI accepts any file. Prepare a new
post release instead.

## Verification

The release is complete only when the exact tag-triggered workflow succeeds and
the PyPI JSON endpoint returns all 11 files. Confirm that production PyPI shows
the final version without the TestPyPI `.devNNN` suffix.

Keep the workflow URL, tag, release commit, and PyPI version in the release
record or handoff. These values identify the publication without relying on the
newest workflow in the repository.

## Rollback

Stop the workflow before publication if a check or artifact is wrong. Fix
`main`, prepare a new commit, and rerun the TestPyPI rehearsal.

You may move a bad tag only when the production workflow has not published any
file. Follow [If the Tag Points at the Wrong Commit](#if-the-tag-points-at-the-wrong-commit).
Never move or reuse a tag after PyPI accepts a file. Publish a new post release
because PyPI files are immutable.

## Prepare and Rehearse a Release on TestPyPI

Use this checklist for every release rehearsal. Complete the steps in order so
the TestPyPI artifacts match the commit that will become the real release.

1. Start from a clean `main` branch that matches `origin/main`.

   ```bash
   test "$(git branch --show-current)" = main
   test -z "$(git status --porcelain)"
   git fetch origin main
   test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
   ```

2. Finish dependency work before release work. For a dependency refresh, follow
   [Dependency Health](dependency-health.md). When dependencies change, check
   upstream `oxipng` and run the override audit.

   ```bash
   make override-audit AI=1
   ```

3. Add the release entry under `Release Notes` in
   [`CHANGELOG.md`](../../CHANGELOG.md). Include dependency or security fixes,
   tooling changes, user-visible changes, and the upstream `oxipng` version.
   State when the public API and optimization behavior did not change.

4. Set the next Python package version and refresh `uv.lock`. For a wrapper
   post release, use the version bump script.

   ```bash
   uv run --group dev python scripts/bump_upstream.py --wrapper-post
   ```

5. Confirm that the new version is absent from PyPI. Replace the example
   version with the version from `pyproject.toml`. A `404` response means that
   the version is available.

   ```bash
   curl -sS -o /dev/null -w '%{http_code}\n' \
     https://pypi.org/pypi/oxipng-pybind/10.1.1.post4/json
   ```

6. Before committing, run the full local gate and validate the planned tag.
   Skip the `main` check only because the version change is not committed yet.

   ```bash
   make ci AI=1
   uv run --no-sync --group dev python scripts/validate_release_tag.py \
     --tag v10.1.1.post4 --skip-main-check
   ```

7. Commit and push the changelog, `pyproject.toml`, and `uv.lock` together.
   Do not create the release tag yet.

8. Wait for `ci` and `api-matrix` to pass on the exact pushed commit. Confirm
   that local `HEAD`, `origin/main`, and each workflow run use that commit.

9. Start the TestPyPI rehearsal from `main`. Then find the new dispatch run by
   its event and exact commit.

   ```bash
   release_sha=$(git rev-parse HEAD)
   gh workflow run wheels.yml --ref main -f publish-target=testpypi
   run_url=
   for attempt in {1..30}; do
     run_url=$(gh run list --workflow wheels.yml --event workflow_dispatch \
       --branch main --commit "$release_sha" --limit 1 --json url \
       --jq '.[0].url')
     test -n "$run_url" && break
     sleep 2
   done
   test -n "$run_url"
   run_id=${run_url##*/}
   test "$(gh run view "$run_id" --json headSha --jq .headSha)" = \
     "$release_sha"
   ```

10. Monitor that exact run until completion.

    ```bash
    echo "$run_url"
    gh run watch "$run_id" --exit-status
    ```

11. Confirm that the sdist, all wheel and smoke-test jobs, and
    `publish-testpypi` passed. The manual workflow adds a unique `.devNNN`
    suffix, so repeated rehearsals do not collide on TestPyPI.

12. Create and push the final tag only after the rehearsal passes and the
    release commit still matches `origin/main`. Follow
    [Steps](#steps) from the beginning for the real PyPI release.

## Set the Version Before Tagging

Choose the exact PyPI version first. The release tag must match
`project.version` in `pyproject.toml`.

Use a Python post release, such as `10.1.1.post1`, for wrapper-only
corrections.

Keep the Cargo package version on the upstream semver base, such as
`10.1.1`. Cargo does not use Python `.postN` versions.

Before tagging, update the Python package version and lockfile:

```bash
uv lock
```

Commit and push the version change.

Then wait for these required source checks on `main`:

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

Do not push the release tag until these checks pass on the commit you plan to
tag.

## Rehearse on TestPyPI

Run the wheels workflow by hand with `publish-target` set to `testpypi`.

The TestPyPI run builds the same artifacts as a real release. It publishes them
to TestPyPI with a `.devNNN` suffix to avoid collisions during repeated
rehearsals.

Confirm the run passes:

- source distribution build;
- all `cp310-abi3` wheel lanes;
- all `cp311-abi3` wheel lanes;
- wheel smoke tests;
- `publish-testpypi`.

Ignore non-blocking GitHub runner notices unless a job fails.

## Push the Release Tag

Tag the checked commit with the exact project version:

```bash
git tag v10.1.1.post1
git push origin v10.1.1.post1
```

The tag starts the real PyPI publish workflow. The workflow validates that:

- the tag is a strict final release tag;
- the tag version matches `pyproject.toml`;
- the tag commit is contained in `origin/main`;
- the version is not already on PyPI;
- required release checks passed on the tagged commit.

If validation fails, the workflow stops before publishing.

## Monitor the Publish Workflow

Watch the tag-triggered `wheels` workflow.

The real publish is complete only when these jobs pass:

- `validate release tag`
- `sdist`
- every wheel job
- `publish`

The `publish-testpypi` job should be skipped for a tag release.

After the workflow passes, verify that the PyPI project page has the expected
version, sdist, and wheels.

## If the Tag Points at the Wrong Commit

If the tag was pushed before the version commit, release validation should fail
before publish.

Fix the version on `main` and wait for checks. Then move the tag, but only if
no artifacts were published:

```bash
git tag -f v10.1.1.post1 <fixed-commit>
git push --force origin v10.1.1.post1
```

Do not move a tag after PyPI publishing succeeds. PyPI files are immutable.
Publish a new post release instead.

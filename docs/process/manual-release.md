# Manual Release

Use this process when publishing a release by hand.

For artifact rules, supported wheel tags, and Trusted Publishing setup, see
[Release Artifacts](release-artifacts.md).

## Before You Tag

Choose the exact PyPI version first. The release tag must match
`project.version` in `pyproject.toml`.

For wrapper-only corrections, use a Python post release such as
`10.1.1.post1`. Keep the Cargo package version on the upstream semver base,
such as `10.1.1`. Cargo does not use Python `.postN` versions.

Update the Python package version and lockfile before tagging:

```bash
uv lock
```

Commit and push the version change. Wait for the required source checks on
`main`:

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

The TestPyPI run builds the same artifacts as a real release, then publishes
them to TestPyPI with a `.devNNN` suffix. This avoids collisions during repeated
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

## Monitor Publish

Watch the tag-triggered `wheels` workflow.

The real publish is complete only when these jobs pass:

- `validate release tag`
- `sdist`
- every wheel job
- `publish`

The `publish-testpypi` job should be skipped for a tag release.

After the workflow passes, verify the PyPI project page has the expected
version, sdist, and wheels.

## If the Tag Points at the Wrong Commit

If the tag was pushed before the version commit, the release validation should
fail before publish.

Fix the version on `main`, wait for checks, then move the tag only if no
artifacts were published:

```bash
git tag -f v10.1.1.post1 <fixed-commit>
git push --force origin v10.1.1.post1
```

Do not move a tag after PyPI publishing succeeds. PyPI files are immutable;
publish a new post release instead.

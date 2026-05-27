# Unfinished Work

This file tracks current unfinished work only. Completed review findings and
implementation notes live in the related docs under `docs/`.

## Required

1. **Validate dependency refresh automation on hosted CI.**
   Run `dependency-health.yml` on `main`. Confirm a tooling-only lockfile
   change gets `no-release-needed`, notice drift is included in the pull
   request, and the pull request auto-merges after required checks pass.

2. **Configure PyPI Trusted Publishing.**
   Configure a pending trusted publisher for project `oxipng-pybind`, owner
   `pdomain`, repository `oxipng-pybind`, workflow `wheels.yml`, and
   environment `pypi`. Do this before creating the first release tag.

3. **Prove the upstream bump workflow.**
   Run the first real `upstream-bump.yml` after upstream `oxipng` releases a
   version newer than 10.1.1. Verify release discovery, manifest copying,
   scanner output, third-party notice generation, docs updates, issue upsert,
   wheel waiting, and auto-merge.

## Optional Future Work

- Add Windows ARM64 wheels if there is user demand.
- Add musllinux x86_64/aarch64 wheels if Alpine users need native wheels.
- Decide whether to publish an sdist. Source installs require Rust and a
  compatible build environment.

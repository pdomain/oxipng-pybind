# Documentation

Use this map to find the right project doc.

| Folder | Purpose | Use when |
| --- | --- | --- |
| `architecture/` | Durable reference for how the system works today. | You need current contracts or diagrams. |
| `api-surface/` | Package-specific upstream API manifests. | You need tracked Rust `oxipng` API snapshots. |
| `plans/` | Current project plans. | You need open work. |
| `process/` | Workflow conventions and release process. | You need team workflow rules. |
| `usage/` | Downstream reference. | You need to use or integrate the package. |

This repo keeps only current docs folders. Use Git history for old plans,
specs, and reports.

## Usage

- [Optimize PNG files](usage/file-optimization.md)
- [Optimize PNG data in memory](usage/memory-optimization.md)
- [Create PNGs from raw pixels](usage/raw-image.md)
- [Handle untrusted input](usage/untrusted-input.md)
- [Build from source](usage/build-from-source.md)
- [Move from pyoxipng](usage/pyoxipng-migration.md)

## Architecture

- [Architecture overview](architecture/overview.md)
- [API compatibility](architecture/api-compatibility.md)
- [Options surface](architecture/options-surface.md)
- [Upstream API surface scan](api-surface/oxipng-10.1.1.toml)

## Process

- [Dependency health](process/dependency-health.md)
- [GitHub settings](process/github-settings.md)
- [Local development](process/local-development.md)
- [Manual release](process/manual-release.md)
- [Release artifacts](process/release-artifacts.md)
- [Rust oxipng updates](process/upstream-bumps.md)
- [Writing style](process/writing-style.md)
- [Lint deviations](process/lint-deviations.md)

## Project state

- [Unfinished work](plans/unfinished-work.md)

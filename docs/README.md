# docs/

How documentation is organized in this repo.

| Folder | Purpose | Use when |
| --- | --- | --- |
| `architecture/` | Durable reference: how the system works today. | Capturing current shape, contracts, and current-state diagrams. |
| `api-surface/` | Package-specific upstream API manifests. | Tracking Rust `oxipng` API surface snapshots. |
| `plans/` | Project state, retained review records, and active plans. | Checking open work or in-tree review history. |
| `process/` | Workflow conventions and release process. | Capturing how the team works. |
| `usage/` | Downstream reference. | A user or integrator needs to know how to use it. |

This repo keeps only docs folders that contain current files. It follows the
workspace folder meanings when those folders exist. `api-surface/` is
package-specific. Use Git history for old plans, specs, and reports.

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
- [Local development](process/local-development.md)
- [Release artifacts](process/release-artifacts.md)
- [Rust oxipng updates](process/upstream-bumps.md)
- [Writing style](process/writing-style.md)
- [Lint deviations](process/lint-deviations.md)

## Project State

- [Unfinished work](plans/unfinished-work.md)

## Review Records

- [Full code review report](plans/full-code-review-report.md)
- [Major review fixes implementation plan](plans/major-review-fixes-plan.md)

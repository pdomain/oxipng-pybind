---
kind: process
status: active
last_verified: 2026-10-25
---
# Documentation Map

This map shows where to find each project doc.

## Agent Index

- **Kind:** process
- **Status:** active
- **Read when:** locating a project doc by topic — usage, architecture, process,
  plans, issues, or API surface.
- **Search terms:** documentation map, docs index, folder guide, where are the
  docs.

| Folder | Purpose | Use when |
| --- | --- | --- |
| `architecture/` | Durable reference for how the system works today. | You need current contracts or diagrams. |
| `api-surface/` | Package-specific upstream API manifests. | You need tracked Rust `oxipng` API snapshots. |
| `issues/` | Governed, evidence-bearing issue reports. | You file or look up a bug, regression, or investigation. |
| `plans/` | Current project plans. | You need open work. |
| `process/` | Workflow conventions and release process. | You need team workflow rules. |
| `usage/` | Downstream reference. | You need to use or integrate the package. |

This repo keeps only current docs folders. Use Git history for old plans,
specs, and reports.

## Agent context

- [Agent guidance (AGENTS.md)](../AGENTS.md)
- [Docgraph rules (DOCGRAPH.md)](../DOCGRAPH.md)
- [Codex-specific context (CODEX.md)](../CODEX.md)

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
- [Test architecture](architecture/test-architecture.md)
- [Upstream API surface scan](api-surface/oxipng-10.2.1.toml)

## Process

- [Dependency health](process/dependency-health.md)
- [GitHub settings](process/github-settings.md)
- [Local development](process/local-development.md)
- [Manual release](process/manual-release.md)
- [Release artifacts](process/release-artifacts.md)
- [Rust oxipng updates](process/upstream-bumps.md)
- [Writing style](process/writing-style.md)
- [Lint deviations](process/lint-deviations.md)

## Issues

- [Issue reports and template](issues/README.md)

## Project state

- [Unfinished work](plans/unfinished-work.md)

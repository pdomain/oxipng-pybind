# Strict CI And Dependency Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `oxipng-pybind` up to the workspace's strict CI standard and add a repeatable dependency/CVE update workflow.

**Architecture:** Keep checks centralized in `make ci` so local and CI behavior match. Use pre-commit for fast local guardrails, keep the existing basedpyright configuration as a required type gate, add Python and Rust dependency auditing as first-class Make targets, and add a scheduled dependency refresh workflow that opens a PR only after the refreshed locks pass audits and CI.

**Tech Stack:** uv, pytest-cov, ruff, basedpyright, pre-commit, gitlint, gitleaks, cargo-deny, GitHub Actions, maturin, Rust 1.85.1.

---

## File Structure

- `pyproject.toml`: Python lint/type/test/audit dependency groups, basedpyright settings, and strict pytest defaults.
- `.pre-commit-config.yaml`: local hooks for formatting, linting, basedpyright type checking, lock sync, secret scan, and commit message linting.
- `Makefile`: canonical local and CI targets for lint, typecheck, tests, coverage, audits, dependency refresh, and AI-filtered runs.
- `deny.toml`: Rust dependency advisory/license/source policy.
- `.github/workflows/ci.yml`: regular CI entry point.
- `.github/workflows/dependency-health.yml`: scheduled/manual dependency refresh and CVE audit workflow.
- `docs/process/dependency-health.md`: operational process for dependency/CVE updates.
- `docs/README.md`: link to dependency health process docs.

---

### Task 1: Align Python Lint, Type, And Coverage Baseline

**Files:**

- Modify: `pyproject.toml`
- Modify: `Makefile`

- [x] **Step 1: Update Ruff target to Python 3.11**

In `pyproject.toml`, change:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
```

to:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
```

- [x] **Step 2: Keep focused pytest runs usable and enforce coverage through Make**

In `pyproject.toml`, keep the default pytest `addopts` focused on strict test
configuration only:

```toml
[tool.pytest.ini_options]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
]
testpaths = ["tests"]
filterwarnings = ["error"]
```

Then update `Makefile` so `test-py`, and therefore `make ci`, enforces branch
coverage on the full Python test suite:

```make
test-py: ## Run Python tests against editable extension
    uv run --group dev maturin develop --quiet
    uv run --group dev pytest -v -ra -n auto --cov=oxipng --cov=scripts --cov-branch --cov-report=term-missing:skip-covered --cov-fail-under=80
```

Do not add coverage fail-under to default pytest options. That makes focused
commands such as `pytest tests/test_scan_upstream_surface.py -q` fail after
their selected tests pass because project-wide coverage is measured from a
partial run.

- [x] **Step 3: Add an explicit coverage Make target**

In `Makefile`, add `coverage` to the `.PHONY` list:

```make
.PHONY: help bootstrap-rust setup develop test test-rust test-py coverage lint lint-fix py-lint py-lint-fix \
```

Add this target after `test-py`:

```make
coverage: ## Run pytest with branch coverage and HTML report
    uv run --group dev maturin develop --quiet
    uv run --group dev pytest --cov=oxipng --cov=scripts --cov-branch --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

- [x] **Step 4: Run focused validation**

Run:

```bash
uv run --no-sync --group dev ruff check .
uv run --no-sync --group dev ruff format --check .
uv run --no-sync --group dev basedpyright
uv run --no-sync --group dev maturin develop --quiet
uv run --no-sync --group dev pytest -q
```

Expected: all commands pass. Plain focused pytest runs do not enforce coverage;
`make test-py` and `make coverage` enforce coverage at or above 80%.

- [x] **Step 5: Commit**

Run:

```bash
git add pyproject.toml Makefile
git commit -m "ci: tighten python lint and coverage"
git push origin main
```

---

### Task 2: Add Workspace-Strict Pre-Commit Hooks

**Files:**

- Modify: `.pre-commit-config.yaml`
- Modify: `Makefile`
- Create: `.gitlint`
- Modify: `docs/conventions/lint-deviations.md`

- [x] **Step 1: Update pre-commit hook versions and install types**

Replace the top of `.pre-commit-config.yaml` with:

```yaml
default_install_hook_types: [pre-commit, commit-msg]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: debug-statements
      - id: check-merge-conflict
```

- [x] **Step 2: Add gitleaks**

Add this repo block after `pre-commit-hooks`:

```yaml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

- [x] **Step 3: Update Ruff hook revision**

Replace the Ruff repo block with:

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.14
    hooks:
      - id: ruff-check
        args: ["--select", "I", "--fix"]
      - id: ruff-check
        args: ["--fix"]
      - id: ruff-format
```

- [x] **Step 4: Keep markdownlint and add manual markdown fix**

Replace the markdownlint block with:

```yaml
  - repo: https://github.com/DavidAnson/markdownlint-cli2
    rev: v0.22.1
    hooks:
      - id: markdownlint-cli2
      - id: markdownlint-cli2
        alias: markdownlint-cli2-fix
        args: ["--fix"]
        stages: [manual]
```

- [x] **Step 5: Add local lock, Rust, and basedpyright hooks**

Replace the local hook block with:

```yaml
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt --check
        entry: bash -c 'PATH="$HOME/.cargo/bin:$PATH" cargo fmt --all -- --check'
        language: system
        pass_filenames: false
        files: ^(Cargo\.(toml|lock)|rust-toolchain\.toml|src/.*\.rs)$
      - id: cargo-clippy
        name: cargo clippy -D warnings
        entry: bash -c 'PATH="$HOME/.cargo/bin:$PATH" cargo clippy --workspace --all-targets -- -D warnings'
        language: system
        pass_filenames: false
        files: ^(Cargo\.(toml|lock)|rust-toolchain\.toml|src/.*\.rs)$
      - id: uv-lock-check
        name: uv.lock is in sync with pyproject.toml
        entry: uv lock --check
        language: system
        pass_filenames: false
        files: ^(pyproject\.toml|uv\.lock)$
      - id: basedpyright
        name: basedpyright type check
        entry: uv run --group dev basedpyright
        language: system
        pass_filenames: false
        files: ^((oxipng|scripts|tests)/.*\.pyi?|pyproject\.toml|uv\.lock)$
```

- [x] **Step 6: Add gitlint commit-msg hook**

Add this block at the end:

```yaml
  - repo: https://github.com/jorisroovers/gitlint
    rev: v0.19.1
    hooks:
      - id: gitlint
        stages: [commit-msg]
```

- [x] **Step 6a: Add workspace gitlint configuration**

Create `.gitlint` so the commit-msg hook follows the workspace convention:

```ini
[general]
ignore=body-is-missing
# Match the workspace 100-char convention while keeping subjects compact.
[title-max-length]
line-length=72
[title-must-not-contain-word]
words=WIP
[body-max-line-length]
line-length=100
```

Document the `body-is-missing` deviation in
`docs/conventions/lint-deviations.md`.

- [x] **Step 7: Ensure setup installs commit-msg hooks**

In `Makefile`, change:

```make
uv run --group dev pre-commit install
```

to:

```make
uv lock --check
uv sync --locked --group dev --reinstall
uv run --group dev pre-commit install --install-hooks
uv run --group dev pre-commit install --hook-type commit-msg
```

- [x] **Step 7a: Run pre-commit in CI**

In `Makefile`, update `ci` so CI runs the same repository hygiene hooks that
developers run locally:

```make
ci: ## Run full CI
    @$(MAKE) --no-print-directory setup
    @$(MAKE) --no-print-directory pre-commit-check
    @$(MAKE) --no-print-directory lint
    @$(MAKE) --no-print-directory rust-deny
    @$(MAKE) --no-print-directory typecheck
    @$(MAKE) --no-print-directory test
    @$(MAKE) --no-print-directory build
```

- [x] **Step 7b: Document markdownlint deviations**

Add `MD013` and `MD033` entries to
`docs/conventions/lint-deviations.md`, matching the existing disables in
`.markdownlint-cli2.jsonc`.

- [x] **Step 8: Run pre-commit validation**

Run:

```bash
uv run --group dev pre-commit run --all-files
uv run --group dev pre-commit run gitlint --hook-stage commit-msg --commit-msg-filename .git/COMMIT_EDITMSG
```

If `.git/COMMIT_EDITMSG` does not exist, create a temporary file:

```bash
printf "ci: test gitlint hook\n" > .cache/gitlint-message.txt
uv run --group dev pre-commit run gitlint --hook-stage commit-msg --commit-msg-filename .cache/gitlint-message.txt
rm -f .cache/gitlint-message.txt
```

Expected: all hooks pass.

- [x] **Step 9: Commit**

Run:

```bash
git add .pre-commit-config.yaml .gitlint Makefile docs/conventions/lint-deviations.md
git commit -m "ci: add strict pre-commit hooks"
git push origin main
```

---

### Task 3: Add Python And Rust CVE Audit Targets

**Files:**

- Modify: `pyproject.toml`
- Modify: `Makefile`
- Modify: `deny.toml`
- Create: `docs/process/dependency-health.md`
- Modify: `docs/README.md`

- [x] **Step 1: Add `pip-audit` to lint dependencies**

In `pyproject.toml`, add `pip-audit` to the `lint` dependency group:

```toml
lint = [
    "basedpyright>=1.39.4",
    "gitlint>=0.19.1",
    "pip-audit>=2.9",
    "pre-commit>=4.3",
    "ruff>=0.13",
]
```

- [x] **Step 2: Tighten cargo-deny advisories and sources**

Replace `deny.toml` with:

```toml
[advisories]
db-path = "~/.cargo/advisory-db"
db-urls = ["https://github.com/rustsec/advisory-db"]
yanked = "deny"
ignore = []

[licenses]
allow = [
    "Apache-2.0",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "MIT",
    "Unlicense",
    "Unicode-3.0",
    "Zlib",
]
confidence-threshold = 0.93

[bans]
multiple-versions = "warn"
wildcards = "deny"

[sources]
unknown-registry = "deny"
unknown-git = "deny"
allow-registry = ["https://github.com/rust-lang/crates.io-index"]
allow-git = []
```

- [x] **Step 3: Add audit Make targets**

In `Makefile`, add `py-audit dependency-audit dependency-refresh-check` to the `.PHONY` list:

```make
    rust-deny py-audit dependency-audit dependency-refresh-check pre-commit-check build wheel clean clean-cache reset remove-venv \
```

Add these targets after `rust-deny`:

```make
py-audit: ## Audit installed Python environment for known vulnerabilities
    uv run --group dev pip-audit --local

dependency-audit: rust-deny py-audit ## Run Rust and Python dependency vulnerability checks

dependency-refresh-check: ## Refresh lockfiles, then run audits and full CI
    uv lock --upgrade
    cargo update
    uv sync --locked --group dev
    uv run --group dev maturin develop
    @$(MAKE) --no-print-directory dependency-audit
    @$(MAKE) --no-print-directory ci
```

- [x] **Step 4: Add dependency audit to CI**

In `Makefile`, update `ci`:

```make
ci: ## Run full CI
    @$(MAKE) --no-print-directory setup
    @$(MAKE) --no-print-directory pre-commit-check
    @$(MAKE) --no-print-directory lint
    @$(MAKE) --no-print-directory rust-deny
    @$(MAKE) --no-print-directory py-audit
    @$(MAKE) --no-print-directory typecheck
    @$(MAKE) --no-print-directory test
    @$(MAKE) --no-print-directory build
```

- [x] **Step 5: Document dependency health process**

Create `docs/process/dependency-health.md`:

````markdown
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
```
````

- [x] **Step 6: Link dependency health docs**

In `docs/README.md`, add this bullet to the process/docs list:

```markdown
- [Dependency Health](process/dependency-health.md)
```

- [x] **Step 7: Run audit validation**

Run:

```bash
uv lock
uv sync --locked --group dev
cargo deny check
uv run --group dev pip-audit --local
make md-lint
make dependency-audit
```

Expected: all commands pass. If `pip-audit` reports a vulnerability, update the affected dependency and rerun the commands before committing.

- [x] **Step 8: Commit**

Run:

```bash
git add pyproject.toml uv.lock Makefile deny.toml docs/process/dependency-health.md docs/README.md
git commit -m "ci: add dependency vulnerability audits"
git push origin main
```

---

### Task 4: Add Scheduled Dependency Refresh PR Workflow

**Files:**

- Create: `.github/workflows/dependency-health.yml`
- Modify: `docs/process/dependency-health.md`

- [ ] **Step 1: Create read-only prepare job**

Create `.github/workflows/dependency-health.yml`:

```yaml
name: dependency-health

on:
  workflow_dispatch:
  schedule:
    - cron: "31 10 * * 2"

permissions:
  contents: read

jobs:
  prepare:
    name: refresh and verify dependencies
    runs-on: ubuntu-latest
    outputs:
      changed: ${{ steps.changes.outputs.changed }}
    env:
      UV_PYTHON: "3.13"
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          version: 0.11.12
      - uses: dtolnay/rust-toolchain@1.85.1
        with:
          components: clippy
      - name: Install cargo-deny
        uses: taiki-e/install-action@v2
        with:
          tool: cargo-deny@0.19.7
      - name: Refresh lockfiles
        run: |
          uv lock --upgrade
          cargo update
      - name: Sync refreshed dependencies
        run: uv sync --group dev
      - name: Build editable extension
        run: uv run --group dev maturin develop
      - name: Run dependency audits
        run: make dependency-audit
      - name: Run CI
        run: make ci
      - name: Check for changes
        id: changes
        run: |
          if git diff --quiet; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi
      - name: Upload refreshed lockfiles
        if: steps.changes.outputs.changed == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: dependency-refresh
          path: |
            Cargo.lock
            uv.lock
```

- [ ] **Step 2: Add write-scoped publish job**

Append this job to `.github/workflows/dependency-health.yml`:

```yaml
  publish:
    name: open dependency refresh PR
    needs: prepare
    if: needs.prepare.outputs.changed == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v6
      - uses: actions/download-artifact@v4
        with:
          name: dependency-refresh
          path: .
      - name: Create pull request
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "chore: refresh dependency lockfiles"
          title: "chore: refresh dependency lockfiles"
          body: |
            Automated dependency refresh.

            Verification run in the prepare job:

            - `make dependency-audit`
            - `make ci`

            Review the lockfile diff for security-relevant updates before merge.
          branch: automation/dependency-refresh
          delete-branch: true
          labels: dependencies, automated
```

- [ ] **Step 3: Document the scheduled workflow**

Append this section to `docs/process/dependency-health.md`:

```markdown
## Scheduled Refresh

`.github/workflows/dependency-health.yml` runs weekly and on demand. The prepare
job has read-only repository permissions, refreshes `uv.lock` and `Cargo.lock`,
then runs dependency audits and full CI. A separate write-scoped publish job
opens or updates the dependency refresh PR only if lockfiles changed.

Do not enable auto-merge for dependency refresh PRs by default. Review lockfile
diffs before merge, especially when CVE remediation pulls major transitive
updates.
```

- [ ] **Step 4: Validate workflow syntax**

Run:

```bash
uv run --group dev pre-commit run check-yaml --files .github/workflows/dependency-health.yml
make md-lint
```

Expected: both commands pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add .github/workflows/dependency-health.yml docs/process/dependency-health.md
git commit -m "ci: schedule dependency health refresh"
git push origin main
```

---

### Task 5: Final Verification

**Files:**

- Verify all files changed by Tasks 1-4.

- [ ] **Step 1: Run full local verification**

Run:

```bash
make setup
make ci
make pre-commit-check
make format-check
make dependency-audit
```

Expected: all commands pass.

- [ ] **Step 2: Verify wheel tag and smoke test still pass**

Run:

```bash
rm -f target/wheels/*.whl
make wheel
python scripts/check_wheel_tags.py --expected-python cp311 --expected-platform manylinux_2_34_x86_64 target/wheels/*.whl
tmpdir="$(mktemp -d)"
uv run --group dev python -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/pip" install target/wheels/*.whl pillow
"$tmpdir/venv/bin/python" scripts/smoke_wheel.py
rm -rf "$tmpdir"
```

Expected: fresh wheel is `cp311-abi3`, tag check passes, and smoke exits 0.

- [ ] **Step 3: Check final worktree**

Run:

```bash
git status --short
```

Expected: clean.

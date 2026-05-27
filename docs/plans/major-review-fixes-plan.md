# Major Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the major findings from
[Full Code Review Report](full-code-review-report.md).

**Architecture:** Keep release hardening, RawImage safety, option validation,
and pyoxipng compatibility as separate workstreams. Stable API behavior stays
strict and user-friendly. pyoxipng behavior is allowed only in explicit
compatibility paths, and must warn.

**Tech Stack:** Rust, PyO3, Python, pytest, basedpyright, Ruff, GitHub Actions,
Dependabot, maturin, uv.

---

## Decisions

- Major 1: fix now. Pin release-path action SHAs and automate action SHA bump
  pull requests with Dependabot.
- Major 2: fix now. Require source `ci` and `api-matrix` success for the tag
  SHA before publishing.
- Major 3: fix now. Require the release tag version to match Python and Cargo
  package versions.
- Major 4: fix now. Build wheels with Cargo `--locked`.
- Major 5: fix now. Scope `DEPENDENCY_REFRESH_TOKEN` only to steps that need it.
- Major 6: fix now. Research upstream zero-dimension behavior first. Pass
  through a good upstream error if it exists. Add wrapper validation if it does
  not.
- Major 7: fix now. Research upstream raw-data length arithmetic first. Pass
  through a good upstream error if it exists. Add wrapper checked validation if
  it does not.
- Major 8: fix now with Major 6 and Major 7. Validate dimensions before indexed
  pixel validation.
- Major 9: fix now. Reject bool for stable `level`. If pyoxipng 9.1.1 accepted
  bool, allow it only through an explicit compatibility path with
  `DeprecationWarning`.
- Major 10: fix now. Research pyoxipng 9.1.1 deflater bool behavior. Reject
  bool in stable behavior. Allow it only with `DeprecationWarning` if pyoxipng
  accepted it.
- Major 11: fix soon. Add pyoxipng `RawImage(data, width, height)` default
  compatibility after RawImage safety fixes.
- Major 12: fix soon with Major 11. Add pyoxipng `RawImage(..., bit_depth=...)`
  compatibility with warning.
- Major 13: fix soon. Add old pyoxipng `RowFilter` aliases with
  `DeprecationWarning`.
- Major 14: fix soon. Support old pyoxipng `StripChunks.none()`,
  `StripChunks.safe()`, and `StripChunks.all()` callable factories with
  `DeprecationWarning`.

## Parallel Execution Map

These task groups can run in parallel because they have separate file
ownership:

- Group A: Tasks 1 through 5. Release and dependency automation.
- Group B: Tasks 6 through 8. Rust RawImage safety.
- Group C: Tasks 9 and 10. Bool validation and pyoxipng behavior research.
- Group D: Tasks 11 through 14. pyoxipng compatibility surface.

Run final full CI after all groups are merged.

## Task 1: Pin Release Actions And Add Dependabot

**Recommendation:** Fix now.

**Behavior change:** Release actions stop following mutable tags. Dependabot
opens pull requests for future action updates.

**Files:**

- Modify: `.github/workflows/wheels.yml`
- Create: `.github/dependabot.yml`
- Modify or create tests in `tests/test_workflows.py`

- [ ] **Step 1: Record current action SHAs**

Run:

```bash
gh api repos/PyO3/maturin-action/git/ref/tags/v1 --jq .object.sha
gh api repos/pypa/gh-action-pypi-publish/git/ref/tags/release/v1 --jq .object.sha
```

Expected:

- Two full commit SHAs.
- If the API returns an annotated tag object, resolve the tag object to the
  commit before pinning.

- [ ] **Step 2: Write failing workflow tests**

Add tests to `tests/test_workflows.py`:

```python
def test_release_actions_are_sha_pinned() -> None:
    workflow = load_workflow(".github/workflows/wheels.yml")
    action_refs = workflow_action_refs(workflow)

    assert action_refs["PyO3/maturin-action"].matches_full_sha
    assert action_refs["pypa/gh-action-pypi-publish"].matches_full_sha


def test_dependabot_updates_github_actions() -> None:
    config = load_yaml(".github/dependabot.yml")

    updates = config["updates"]
    assert {
        "package-ecosystem": "github-actions",
        "directory": "/",
    } in [
        {key: item[key] for key in ("package-ecosystem", "directory")}
        for item in updates
    ]
```

If helper functions do not exist, add small YAML parsing helpers in the same
test file:

```python
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class ActionRef:
    def __init__(self, value: str) -> None:
        self.owner_repo, self.ref = value.split("@", 1)

    @property
    def matches_full_sha(self) -> bool:
        return FULL_SHA.fullmatch(self.ref) is not None


def load_yaml(path: str) -> dict[str, object]:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def load_workflow(path: str) -> dict[str, object]:
    return load_yaml(path)


def workflow_action_refs(workflow: dict[str, object]) -> dict[str, ActionRef]:
    refs: dict[str, ActionRef] = {}
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    for job in jobs.values():
        assert isinstance(job, dict)
        for step in job.get("steps", []):
            if isinstance(step, dict) and isinstance(step.get("uses"), str):
                action = ActionRef(step["uses"])
                refs[action.owner_repo] = action
    return refs
```

- [ ] **Step 3: Run test and verify it fails**

Run:

```bash
uv run --group dev pytest tests/test_workflows.py -q
```

Expected:

- Fails because release actions are still tag-pinned or Dependabot config is
  missing.

- [ ] **Step 4: Pin action refs**

Edit `.github/workflows/wheels.yml`:

```yaml
      - name: Build wheel
        uses: PyO3/maturin-action@0123456789abcdef0123456789abcdef01234567
```

```yaml
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@89abcdef0123456789abcdef0123456789abcdef
```

Replace the sample SHAs above with the real SHAs from Step 1.

- [ ] **Step 5: Add Dependabot config**

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      github-actions:
        patterns:
          - "*"
```

- [ ] **Step 6: Verify**

Run:

```bash
uv run --group dev pytest tests/test_workflows.py -q
uv run --group dev pre-commit run check-yaml --files .github/dependabot.yml .github/workflows/wheels.yml
```

Expected:

- Workflow tests pass.
- YAML check passes.

## Task 2: Gate Tag Publishing On Source CI

**Recommendation:** Fix now.

**Behavior change:** Tag publishing fails unless required source workflows passed
for the tag SHA.

**Files:**

- Create: `scripts/verify_release_checks.py`
- Create or modify: `tests/test_release_checks.py`
- Modify: `.github/workflows/wheels.yml`
- Modify: `tests/test_workflows.py`

- [ ] **Step 1: Write failing unit tests**

Create `tests/test_release_checks.py`:

```python
from scripts.verify_release_checks import check_required_workflows


def test_required_workflows_pass_when_all_successful() -> None:
    runs = [
        {"name": "ci", "headSha": "abc", "status": "completed", "conclusion": "success"},
        {
            "name": "api-matrix",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
        },
    ]

    errors = check_required_workflows(runs, sha="abc", required=("ci", "api-matrix"))

    assert errors == []


def test_required_workflows_fail_when_missing() -> None:
    runs = [
        {"name": "ci", "headSha": "abc", "status": "completed", "conclusion": "success"},
    ]

    errors = check_required_workflows(runs, sha="abc", required=("ci", "api-matrix"))

    assert errors == ["api-matrix did not complete successfully for abc"]


def test_required_workflows_fail_when_not_successful() -> None:
    runs = [
        {"name": "ci", "headSha": "abc", "status": "completed", "conclusion": "failure"},
        {
            "name": "api-matrix",
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
        },
    ]

    errors = check_required_workflows(runs, sha="abc", required=("ci", "api-matrix"))

    assert errors == ["ci did not complete successfully for abc"]
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run --group dev pytest tests/test_release_checks.py -q
```

Expected:

- Fails because `scripts.verify_release_checks` does not exist.

- [ ] **Step 3: Add verification script**

Create `scripts/verify_release_checks.py`:

```python
#!/usr/bin/env python3
"""Verify required source workflows passed for a release SHA."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any

REQUIRED_WORKFLOWS = ("ci", "api-matrix")


def resolve_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def check_required_workflows(
    runs: list[dict[str, Any]], *, sha: str, required: tuple[str, ...] = REQUIRED_WORKFLOWS
) -> list[str]:
    errors: list[str] = []
    for workflow in required:
        matched = [
            run
            for run in runs
            if run.get("name") == workflow
            and run.get("headSha") == sha
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
        ]
        if not matched:
            errors.append(f"{workflow} did not complete successfully for {sha}")
    return errors


def load_runs(repo: str, sha: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        [
            resolve_executable("gh"),
            "run",
            "list",
            "--repo",
            repo,
            "--commit",
            sha,
            "--json",
            "name,headSha,status,conclusion",
            "--limit",
            "100",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return list(json.loads(result.stdout))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args(argv)

    errors = check_required_workflows(load_runs(args.repo, args.sha), sha=args.sha)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add release gate job**

Modify `.github/workflows/wheels.yml`:

```yaml
  verify-source-checks:
    name: verify source checks
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - name: Verify source workflows passed
        env:
          GH_TOKEN: ${{ github.token }}
        run: python scripts/verify_release_checks.py --repo "${{ github.repository }}" --sha "${{ github.sha }}"
```

Update publish dependencies:

```yaml
  publish:
    name: publish to pypi
    needs:
      - verify-release-artifacts
      - verify-source-checks
```

- [ ] **Step 5: Verify**

Run:

```bash
uv run --group dev pytest tests/test_release_checks.py tests/test_workflows.py -q
uv run --group dev ruff check scripts/verify_release_checks.py tests/test_release_checks.py tests/test_workflows.py
uv run --group dev basedpyright scripts/verify_release_checks.py tests/test_release_checks.py tests/test_workflows.py
```

Expected:

- Tests pass.
- Ruff passes.
- basedpyright passes.

## Task 3: Verify Release Tag Version

**Recommendation:** Fix now.

**Behavior change:** A tag can publish only when the tag version matches
`pyproject.toml` and `Cargo.toml`.

**Files:**

- Create: `scripts/verify_release_version.py`
- Create: `tests/test_release_version.py`
- Modify: `.github/workflows/wheels.yml`

- [ ] **Step 1: Write failing tests**

Create `tests/test_release_version.py`:

```python
from scripts.verify_release_version import release_version_errors


def test_release_version_matches_python_and_cargo() -> None:
    errors = release_version_errors(
        tag="v10.1.1",
        pyproject_version="10.1.1",
        cargo_version="10.1.1",
    )

    assert errors == []


def test_release_version_rejects_tag_mismatch() -> None:
    errors = release_version_errors(
        tag="v10.1.0",
        pyproject_version="10.1.1",
        cargo_version="10.1.1",
    )

    assert errors == ["tag version 10.1.0 does not match pyproject version 10.1.1"]


def test_release_version_rejects_cargo_mismatch() -> None:
    errors = release_version_errors(
        tag="v10.1.1",
        pyproject_version="10.1.1",
        cargo_version="10.1.0",
    )

    assert errors == ["cargo version 10.1.0 does not match pyproject version 10.1.1"]
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run --group dev pytest tests/test_release_version.py -q
```

Expected:

- Fails because `scripts.verify_release_version` does not exist.

- [ ] **Step 3: Add version verification script**

Create `scripts/verify_release_version.py`:

```python
#!/usr/bin/env python3
"""Verify a release tag matches package versions."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_pyproject_version(path: Path = ROOT / "pyproject.toml") -> str:
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    return str(document["project"]["version"])


def read_cargo_version(path: Path = ROOT / "Cargo.toml") -> str:
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    return str(document["package"]["version"])


def tag_version(tag: str) -> str:
    return tag[1:] if tag.startswith("v") else tag


def release_version_errors(tag: str, pyproject_version: str, cargo_version: str) -> list[str]:
    version = tag_version(tag)
    errors: list[str] = []
    if version != pyproject_version:
        errors.append(
            f"tag version {version} does not match pyproject version {pyproject_version}"
        )
    if cargo_version != pyproject_version:
        errors.append(
            f"cargo version {cargo_version} does not match pyproject version {pyproject_version}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    args = parser.parse_args(argv)

    errors = release_version_errors(
        args.tag,
        pyproject_version=read_pyproject_version(),
        cargo_version=read_cargo_version(),
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add workflow step**

In `.github/workflows/wheels.yml`, add this to `verify-release-artifacts`
before artifact verification:

```yaml
      - name: Verify release version
        run: python scripts/verify_release_version.py --tag "${{ github.ref_name }}"
```

Also add the same step in `publish` before publishing.

- [ ] **Step 5: Verify**

Run:

```bash
uv run --group dev pytest tests/test_release_version.py -q
uv run --group dev ruff check scripts/verify_release_version.py tests/test_release_version.py
uv run --group dev basedpyright scripts/verify_release_version.py tests/test_release_version.py
```

Expected:

- Tests pass.
- Ruff passes.
- basedpyright passes.

## Task 4: Build Wheels With Locked Cargo Dependencies

**Recommendation:** Fix now.

**Behavior change:** Wheel builds fail when `Cargo.lock` is stale.

**Files:**

- Modify: `Makefile`
- Modify: `.github/workflows/wheels.yml`
- Modify: `tests/test_makefile.py`
- Modify: `tests/test_workflows.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_makefile.py`:

```python
def test_wheel_build_uses_locked_cargo_dependencies() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "maturin build --release --locked" in makefile
```

Add to `tests/test_workflows.py`:

```python
def test_wheel_workflow_uses_locked_cargo_dependencies() -> None:
    workflow_text = (ROOT / ".github/workflows/wheels.yml").read_text(encoding="utf-8")

    assert "--release --locked --out dist --interpreter python3.11" in workflow_text
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
uv run --group dev pytest tests/test_makefile.py tests/test_workflows.py -q
```

Expected:

- Fails because `--locked` is not present.

- [ ] **Step 3: Add `--locked`**

In `Makefile`, change:

```make
uv run --group dev maturin build --release
```

to:

```make
uv run --group dev maturin build --release --locked
```

In `.github/workflows/wheels.yml`, change:

```yaml
args: --release --out dist --interpreter python3.11
```

to:

```yaml
args: --release --locked --out dist --interpreter python3.11
```

- [ ] **Step 4: Verify**

Run:

```bash
uv run --group dev pytest tests/test_makefile.py tests/test_workflows.py -q
uv run --group dev maturin build --release --locked
```

Expected:

- Tests pass.
- Local locked wheel build succeeds.

## Task 5: Scope Dependency Refresh Token

**Recommendation:** Fix now.

**Behavior change:** The dependency refresh token is visible only to steps that
need it.

**Files:**

- Modify: `.github/workflows/dependency-health.yml`
- Modify: `tests/test_workflows.py`

- [ ] **Step 1: Write failing workflow test**

Add to `tests/test_workflows.py`:

```python
def test_dependency_refresh_token_is_step_scoped() -> None:
    workflow = load_workflow(".github/workflows/dependency-health.yml")
    publish = workflow["jobs"]["publish"]

    assert "env" not in publish or "DEPENDENCY_REFRESH_TOKEN" not in publish["env"]

    steps = publish["steps"]
    token_steps = [
        step
        for step in steps
        if isinstance(step, dict)
        and "DEPENDENCY_REFRESH_TOKEN" in step.get("env", {})
    ]
    assert [step["name"] for step in token_steps] == [
        "Require dependency refresh token",
        "Enable auto-merge",
    ]

    create_pr = next(step for step in steps if step.get("name") == "Create pull request")
    assert create_pr["with"]["token"] == "${{ secrets.DEPENDENCY_REFRESH_TOKEN }}"
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run --group dev pytest tests/test_workflows.py -q
```

Expected:

- Fails because token is currently job-scoped.

- [ ] **Step 3: Scope token to steps**

In `.github/workflows/dependency-health.yml`, remove job-level env:

```yaml
    env:
      DEPENDENCY_REFRESH_TOKEN: ${{ secrets.DEPENDENCY_REFRESH_TOKEN }}
```

Change token uses:

```yaml
      - name: Require dependency refresh token
        env:
          DEPENDENCY_REFRESH_TOKEN: ${{ secrets.DEPENDENCY_REFRESH_TOKEN }}
        run: |
          if [ -z "$DEPENDENCY_REFRESH_TOKEN" ]; then
            echo "DEPENDENCY_REFRESH_TOKEN is required so refresh PRs trigger normal CI." >&2
            exit 1
          fi
```

```yaml
      - name: Create pull request
        id: cpr
        uses: peter-evans/create-pull-request@c5a7806660adbe173f04e3e038b0ccdcd758773c
        with:
          token: ${{ secrets.DEPENDENCY_REFRESH_TOKEN }}
```

```yaml
      - name: Enable auto-merge
        env:
          GH_TOKEN: ${{ secrets.DEPENDENCY_REFRESH_TOKEN }}
        run: |
          gh pr merge "${{ steps.cpr.outputs.pull-request-number }}" --auto --rebase --delete-branch
```

- [ ] **Step 4: Verify**

Run:

```bash
uv run --group dev pytest tests/test_workflows.py -q
uv run --group dev pre-commit run check-yaml --files .github/workflows/dependency-health.yml
```

Expected:

- Tests pass.
- YAML check passes.

## Task 6: Research RawImage Upstream Validation

**Recommendation:** Fix now.

**Behavior change:** None. This task records facts needed for Tasks 7 and 8.

**Files:**

- Modify: `docs/plans/major-review-fixes-plan.md`

- [ ] **Step 1: Inspect pinned upstream source**

Run:

```bash
rg -n "pub struct RawImage|impl RawImage|fn new|row_bytes|width|height|checked" \
  ~/.cargo/registry/src -g 'raw.rs' -g 'colors.rs'
```

Expected:

- Locate `oxipng-10.1.1` raw image construction code.

- [ ] **Step 2: Run behavior probes**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --group dev python - <<'PY'
from oxipng import BitDepth, ColorType, RawImage

cases = [
    ("zero width", lambda: RawImage(0, 1, ColorType.rgba, BitDepth.eight, b"")),
    ("zero height", lambda: RawImage(1, 0, ColorType.rgba, BitDepth.eight, b"")),
    ("huge dimensions", lambda: RawImage(2**32 - 1, 2**32 - 1, ColorType.rgba, BitDepth.eight, b"")),
]

for name, call in cases:
    try:
        image = call()
        print(name, "constructed", type(image).__name__)
    except Exception as error:
        print(name, type(error).__name__, str(error))
PY
```

Expected:

- Clear output for zero dimensions and huge dimensions.

- [ ] **Step 3: Record research result**

Append a short note under this task:

```markdown
### RawImage Upstream Research Result

- `oxipng` version checked: 10.1.1.
- Zero width result: paste the exact exception type and message from Step 2.
- Zero height result: paste the exact exception type and message from Step 2.
- Huge dimension result: paste the exact exception type and message from Step 2.
- Decision: choose one sentence. Use `pass through upstream error` when
  upstream already raises a clear error. Use `add wrapper validation` when
  upstream constructs invalid data, panics, loops, or returns a poor error.
```

## Task 7: Add RawImage Dimension And Length Validation

**Recommendation:** Fix now after Task 6.

**Behavior change:** Invalid RawImage dimensions and impossible data lengths
raise predictable Python errors before optimization.

**Files:**

- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_api.py`:

```python
@pytest.mark.parametrize(("width", "height"), [(0, 1), (1, 0)])
def test_raw_image_rejects_zero_dimensions(width: int, height: int) -> None:
    with pytest.raises(ValueError, match="must be greater than 0|invalid image dimensions"):
        RawImage(width, height, ColorType.rgba, BitDepth.eight, b"")


def test_raw_image_rejects_huge_dimensions_without_panic() -> None:
    with pytest.raises(ValueError, match="raw image data length|image dimensions|too large"):
        RawImage(2**32 - 1, 2**32 - 1, ColorType.rgba, BitDepth.eight, b"")
```

- [ ] **Step 2: Run tests and verify they fail or expose upstream behavior**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest \
  tests/test_api.py::test_raw_image_rejects_zero_dimensions \
  tests/test_api.py::test_raw_image_rejects_huge_dimensions_without_panic -q
```

Expected:

- Fails if wrapper does not reject yet.
- If upstream already returns a different good error, adjust expected message
  to match the mapped Python error.

- [ ] **Step 3: Add wrapper validation only if Task 6 showed upstream is unsafe**

Add helpers in `src/lib.rs` near raw image helpers:

```rust
fn validate_raw_dimensions(width: u32, height: u32) -> PyResult<()> {
    if width == 0 || height == 0 {
        return Err(PyValueError::new_err(
            "raw image dimensions must be greater than 0",
        ));
    }
    Ok(())
}
```

In `PyRawImage::from_parts`, after parsing `bit_depth` and before
`validate_indexed_pixels`, add:

```rust
validate_raw_dimensions(width, height)?;
```

If Task 6 shows upstream length math is unsafe, add checked length validation
with code that matches upstream format rules. Keep this helper private to
`src/lib.rs`.

- [ ] **Step 4: Verify**

Run:

```bash
cargo fmt
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest \
  tests/test_api.py::test_raw_image_rejects_zero_dimensions \
  tests/test_api.py::test_raw_image_rejects_huge_dimensions_without_panic -q
cargo clippy --workspace --all-targets -- -D warnings
```

Expected:

- Tests pass.
- Clippy passes.

## Task 8: Prove Indexed Zero-Width Fails Fast

**Recommendation:** Fix now with Task 7.

**Behavior change:** Invalid indexed zero-width input fails before any indexed
pixel loop.

**Files:**

- Modify: `tests/test_api.py`
- Modify: `src/lib.rs` only if Task 7 did not already fix this

- [ ] **Step 1: Add focused test**

Add to `tests/test_api.py`:

```python
def test_indexed_raw_image_rejects_zero_width_before_pixel_scan() -> None:
    palette = [(0, 0, 0, 255)]

    with pytest.raises(ValueError, match="raw image dimensions must be greater than 0|invalid image dimensions"):
        RawImage(
            0,
            2**32 - 1,
            ColorType.indexed,
            BitDepth.eight,
            b"",
            palette=palette,
        )
```

- [ ] **Step 2: Run test**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py::test_indexed_raw_image_rejects_zero_width_before_pixel_scan -q
```

Expected:

- Passes quickly.

## Task 9: Reject Bool For Stable `level`

**Recommendation:** Fix now.

**Behavior change:** Stable `level=True` and `level=False` raise `TypeError`.
Allow only in a pyoxipng compatibility path if Task 10 research proves
pyoxipng accepted bool.

**Files:**

- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Research pyoxipng behavior**

Run in the pyoxipng venv or install pyoxipng 9.1.1 in `/tmp`:

```bash
/tmp/pyoxipng-venv/bin/python - <<'PY'
from io import BytesIO
from PIL import Image
import oxipng

buf = BytesIO()
Image.new("RGBA", (1, 1), (255, 0, 0, 255)).save(buf, format="PNG")
data = buf.getvalue()

for value in [True, False]:
    try:
        oxipng.optimize_from_memory(data, level=value)
        print(value, "accepted")
    except Exception as error:
        print(value, type(error).__name__, str(error))
PY
```

Record whether pyoxipng accepted bool.

- [ ] **Step 2: Write failing stable tests**

Add to `tests/test_api.py`:

```python
@pytest.mark.parametrize("value", [True, False])
def test_level_rejects_bool(png_bytes: bytes, value: bool) -> None:
    with pytest.raises(TypeError, match="level must be an integer"):
        optimize_from_memory(png_bytes, level=value)
```

- [ ] **Step 3: Run test and verify it fails**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py::test_level_rejects_bool -q
```

Expected:

- Fails because bool is accepted today.

- [ ] **Step 4: Reject bool in stable parser**

In `src/lib.rs`, update `parse_level`:

```rust
fn parse_level(value: &Bound<'_, PyAny>) -> PyResult<u8> {
    reject_bool(value, "level")?;
    let parsed: i64 = value
        .extract()
        .map_err(|_| PyValueError::new_err("level must be an integer from 0 to 6"))?;
```

- [ ] **Step 5: Verify**

Run:

```bash
cargo fmt
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py::test_level_rejects_bool -q
```

Expected:

- Tests pass.

## Task 10: Deflater Bool Compatibility Policy

**Recommendation:** Fix now.

**Behavior change:** Stable behavior rejects bool. If pyoxipng accepted bool,
compat behavior may allow it with `DeprecationWarning`.

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/_pyoxipng_compat.py`
- Modify: `src/lib.rs`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Research pyoxipng behavior**

Run:

```bash
/tmp/pyoxipng-venv/bin/python - <<'PY'
import oxipng

for factory in [oxipng.Deflaters.libdeflater, oxipng.Deflaters.zopfli]:
    for value in [True, False]:
        try:
            factory(value)
            print(factory.__name__, value, "accepted")
        except Exception as error:
            print(factory.__name__, value, type(error).__name__, str(error))
PY
```

Record whether pyoxipng accepted bool.

- [ ] **Step 2: Write tests for target behavior**

If pyoxipng rejected bool, add:

```python
@pytest.mark.parametrize("factory", [Deflaters.libdeflater, Deflaters.zopfli])
@pytest.mark.parametrize("value", [True, False])
def test_deflater_factories_reject_bool(factory: Any, value: bool) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        factory(value)
```

If pyoxipng accepted bool, add:

```python
@pytest.mark.parametrize("factory", [Deflaters.libdeflater, Deflaters.zopfli])
@pytest.mark.parametrize("value", [True, False])
def test_deflater_bool_compatibility_warns(factory: Any, value: bool) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        factory(value)
```

- [ ] **Step 3: Implement target behavior**

If rejecting bool, add a bool check in `Deflaters` Python factory methods:

```python
if isinstance(compression, bool):
    raise TypeError("deflate libdeflater compression must be an integer")
```

and:

```python
if isinstance(iterations, bool):
    raise TypeError("deflate zopfli iterations must be an integer")
```

If allowing pyoxipng bool compatibility, emit:

```python
_compat.warn_pyoxipng_compat()
```

before returning the compatibility object for bool values.

- [ ] **Step 4: Verify**

Run:

```bash
uv run --group dev ruff check oxipng/__init__.py oxipng/_pyoxipng_compat.py tests/test_api.py
uv run --group dev basedpyright oxipng tests/test_api.py
uv run --no-sync --group dev pytest tests/test_api.py -q -k 'deflater and bool'
```

Expected:

- New tests pass.

## Task 11: Add pyoxipng RawImage Default Constructor Compatibility

**Recommendation:** Fix soon after Tasks 7 and 8.

**Behavior change:** `RawImage(data, width, height)` works as a warning-emitting
compatibility path.

**Files:**

- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`
- Modify: `docs/usage/pyoxipng-migration.md`

- [ ] **Step 1: Research pyoxipng defaults**

Run:

```bash
/tmp/pyoxipng-venv/bin/python - <<'PY'
import inspect
import oxipng

print(inspect.signature(oxipng.RawImage))
PY
```

Confirm:

- default `color_type`
- default `bit_depth`
- accepted keyword names

- [ ] **Step 2: Write failing tests**

Add to `tests/test_api.py`:

```python
def test_pyoxipng_raw_image_default_constructor_warns() -> None:
    data = bytes([255, 0, 0, 255])

    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(data, 1, 1)

    assert_readable_png_bytes(raw.create_optimized_png())
```

- [ ] **Step 3: Implement compatibility branch**

In `PyRawImage::new`, route `args.len() == 3` to the compatibility constructor.
In `new_pyoxipng_compat`, default the missing `color_type` to the pyoxipng
default found in Step 1.

- [ ] **Step 4: Update stub**

Add overload in `oxipng/__init__.pyi`:

```python
    @overload
    def __init__(
        self,
        data: BytesLike,
        width: int,
        height: int,
    ) -> None: ...
```

- [ ] **Step 5: Verify**

Run:

```bash
cargo fmt
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py::test_pyoxipng_raw_image_default_constructor_warns -q
uv run --group dev basedpyright oxipng tests/test_api.py
```

Expected:

- Test passes.
- Type check passes.

## Task 12: Add pyoxipng RawImage `bit_depth` Compatibility

**Recommendation:** Fix soon with Task 11.

**Behavior change:** `RawImage(data, width, height, color_type=..., bit_depth=...)`
works as a warning-emitting compatibility path.

**Files:**

- Modify: `src/lib.rs`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`
- Modify: `docs/usage/pyoxipng-migration.md`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_api.py`:

```python
def test_pyoxipng_raw_image_constructor_accepts_bit_depth_kwarg() -> None:
    data = bytes([255, 0, 0, 255])

    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(data, 1, 1, color_type=ColorType.rgba(), bit_depth=8)

    assert_readable_png_bytes(raw.create_optimized_png())
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py::test_pyoxipng_raw_image_constructor_accepts_bit_depth_kwarg -q
```

Expected:

- Fails because `bit_depth` is currently rejected.

- [ ] **Step 3: Implement `bit_depth` compatibility**

In `new_pyoxipng_compat`, allow kwargs:

```rust
Self::reject_extra_kwargs(Some(kwargs), &["color_type", "bit_depth"])?;
```

Read optional `bit_depth`:

```rust
let bit_depth = Self::raw_image_kwarg(Some(kwargs), "bit_depth")?;
```

Use it when present. Otherwise use the descriptor bit depth or pyoxipng
default found in Task 11 research.

- [ ] **Step 4: Update stub**

Update the compatibility overload:

```python
    @overload
    def __init__(
        self,
        data: BytesLike,
        width: int,
        height: int,
        *,
        color_type: _CompatColorType | None = None,
        bit_depth: BitDepth | int = BitDepth.eight,
    ) -> None: ...
```

- [ ] **Step 5: Verify**

Run:

```bash
cargo fmt
uv run --group dev maturin develop --quiet
uv run --no-sync --group dev pytest tests/test_api.py -q -k 'pyoxipng_raw_image_constructor'
uv run --group dev basedpyright oxipng tests/test_api.py
```

Expected:

- Relevant tests pass.
- Type check passes.

## Task 13: Add Old pyoxipng RowFilter Aliases

**Recommendation:** Fix soon.

**Behavior change:** Old `RowFilter.NoOp` style names work with
`DeprecationWarning`.

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`
- Modify: `docs/usage/pyoxipng-migration.md`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_api.py`:

```python
@pytest.mark.parametrize(
    ("old_name", "stable"),
    [
        ("NoOp", FilterStrategy.none),
        ("Sub", FilterStrategy.sub),
        ("Up", FilterStrategy.up),
        ("Average", FilterStrategy.average),
        ("Paeth", FilterStrategy.paeth),
        ("MinSum", FilterStrategy.minsum),
        ("Entropy", FilterStrategy.entropy),
        ("Bigrams", FilterStrategy.bigrams),
        ("BigEnt", FilterStrategy.bigent),
        ("Brute", FilterStrategy.brute),
    ],
)
def test_pyoxipng_rowfilter_old_names_warn(old_name: str, stable: FilterStrategy) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        value = getattr(RowFilter, old_name)

    assert value.value == stable.value
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py::test_pyoxipng_rowfilter_old_names_warn -q
```

Expected:

- Fails because old aliases are missing.

- [ ] **Step 3: Add aliases**

In `RowFilter`, add old names:

```python
    NoOp = "none"
    Sub = "sub"
    Up = "up"
    Average = "average"
    Paeth = "paeth"
    MinSum = "minsum"
    Entropy = "entropy"
    Bigrams = "bigrams"
    BigEnt = "bigent"
    Brute = "brute"
```

Add those names to `__pyoxipng_deprecated_names__`.

- [ ] **Step 4: Update stub and docs**

Add the same aliases to `oxipng/__init__.pyi`.

In `docs/usage/pyoxipng-migration.md`, update the row filter migration table
to include old pyoxipng names such as `RowFilter.NoOp`.

- [ ] **Step 5: Verify**

Run:

```bash
uv run --group dev ruff check oxipng/__init__.py oxipng/__init__.pyi tests/test_api.py
uv run --group dev basedpyright oxipng tests/test_api.py
uv run --no-sync --group dev pytest tests/test_api.py::test_pyoxipng_rowfilter_old_names_warn -q
```

Expected:

- Tests pass.
- Static checks pass.

## Task 14: Add Callable pyoxipng StripChunks Factories

**Recommendation:** Fix soon.

**Behavior change:** Old calls such as `StripChunks.safe()` work with
`DeprecationWarning`. Stable `StripChunks.safe` still works without warning.

**Files:**

- Modify: `oxipng/__init__.py`
- Modify: `oxipng/__init__.pyi`
- Modify: `tests/test_api.py`
- Modify: `docs/usage/pyoxipng-migration.md`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_api.py`:

```python
@pytest.mark.parametrize(
    ("member_name", "member"),
    [
        ("none", StripChunks.none),
        ("safe", StripChunks.safe),
        ("all", StripChunks.all),
    ],
)
def test_pyoxipng_strip_chunk_enum_members_are_callable(
    member_name: str,
    member: StripChunks,
) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        value = getattr(StripChunks, member_name)()

    assert value is member
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_api.py::test_pyoxipng_strip_chunk_enum_members_are_callable -q
```

Expected:

- Fails because enum members are not callable.

- [ ] **Step 3: Make `StripChunks` enum members callable**

Add to `StripChunks`:

```python
    def __call__(self) -> "StripChunks":
        """Return this enum member for pyoxipng callable factory compatibility."""
        _compat.warn_pyoxipng_compat()
        return self
```

- [ ] **Step 4: Update stub**

Add to `StripChunks` in `oxipng/__init__.pyi`:

```python
    def __call__(self) -> StripChunks:
        """Return this enum member for pyoxipng callable factory compatibility."""
```

- [ ] **Step 5: Update docs**

In `docs/usage/pyoxipng-migration.md`, add a short table:

```markdown
| Old pyoxipng shape | Stable oxipng-pybind shape |
| --- | --- |
| `StripChunks.safe()` | `StripChunks.safe` |
| `StripChunks.none()` | `StripChunks.none` |
| `StripChunks.all()` | `StripChunks.all` |
```

- [ ] **Step 6: Verify**

Run:

```bash
uv run --group dev ruff check oxipng/__init__.py oxipng/__init__.pyi tests/test_api.py
uv run --group dev basedpyright oxipng tests/test_api.py
uv run --no-sync --group dev pytest tests/test_api.py::test_pyoxipng_strip_chunk_enum_members_are_callable -q
```

Expected:

- Tests pass.
- Static checks pass.

## Final Verification

Run after all tasks are integrated:

```bash
make ci AI=1
```

Expected:

- `ci passed (log: .ci-ai.log)`

Then update [Full Code Review Report](full-code-review-report.md) status notes
for every fixed major finding.

## Self-Review Notes

- All 14 major findings from the review report are covered.
- The plan separates workflow/release, RawImage safety, bool validation, and
  pyoxipng compatibility so subagents can work in parallel.
- Final CI is required after integration because several groups touch shared
  tests and workflows.

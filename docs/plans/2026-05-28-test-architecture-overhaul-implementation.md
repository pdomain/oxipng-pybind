# Test Architecture Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the test suite into clear behavior-contract domains with shared verified helpers and stronger high-value negative coverage.

**Architecture:** Build a small `tests/helpers/` layer first, then split large mixed test files by public contract area. Keep production behavior unchanged; each task either moves tests, strengthens assertions, or adds focused negative coverage from the approved design.

**Tech Stack:** Python 3.10+, pytest, PyO3/maturin extension via Make targets, basedpyright, Ruff, GitHub Actions YAML fixtures, project helper scripts under `scripts/`.

---

## Ground Rules

- Work only on local branch(es). Do not push to origin.
- Preserve package behavior unless a test exposes a real defect.
- Do not revert edits made by another agent. If a parallel task changed a file
  you need, re-read it and adapt.
- Keep commits local and task-scoped.
- Prefer `make` targets. Run `make develop AI=1` before focused tests that
  import `oxipng` or `_oxipng`.
- Use `uv run --no-sync --group dev pytest <specific test files> -v` for
  focused test runs after the editable extension is built.

## Target File Structure

Create:

- `tests/helpers/__init__.py`: mark helper package.
- `tests/helpers/png.py`: PNG fixture, parsing, structural assertion, and pixel helpers.
- `tests/helpers/warnings.py`: deprecation-warning assertion helpers.
- `tests/helpers/automation.py`: fake HTTP and subprocess helpers.
- `tests/helpers/artifacts.py`: fake wheel, sdist, wheel-name, and workflow-run factories.
- `tests/helpers/workflows.py`: workflow YAML, step lookup, action ref, and allowlist helpers.
- `tests/test_helpers_png.py`: direct tests for PNG helper failure modes.
- `tests/test_helpers_warnings.py`: direct tests for warning helpers.
- `tests/test_helpers_workflows.py`: direct tests for workflow helper failure modes.
- `tests/test_api_surface.py`: imports, signatures, names, and runtime docs.
- `tests/test_optimize_file_api.py`: file optimize and analyze behavior.
- `tests/test_optimize_memory_api.py`: memory optimize input and error behavior.
- `tests/test_option_validation.py`: cross-entry-point option normalization and validation.
- `tests/test_pyoxipng_compat.py`: pyoxipng compatibility and warning behavior.
- `tests/test_raw_image_api.py`: `RawImage` construction, output, chunk, palette, and validation.
- `tests/test_workflow_security.py`: action pinning, reviewed allowlist, permissions, and token policy.
- `tests/test_workflow_release_policy.py`: wheels, PyPI/TestPyPI, release-tag, and release checks.
- `tests/test_workflow_automation_policy.py`: upstream bump, dependency refresh, retry, and CI gates.
- `tests/test_packaging_metadata.py`: packaging metadata static policy moved out of `test_scripts.py`.
- `tests/test_ai_filter_log.py`: `scripts/ai_filter_log.py` CLI behavior.
- `tests/test_smoke_wheel.py`: `scripts/smoke_wheel.py` behavior and CLI smoke checks.
- `tests/typecheck/typing_filter_options.py`: basedpyright-only fixture moved from `tests/typing_filter_options.py`.

Modify:

- `tests/conftest.py`: use shared PNG fixture helpers.
- `tests/test_api.py`: delete after its tests are moved.
- `tests/test_docs_examples.py`: use PNG and warning helpers; keep docs-scope tests.
- `tests/test_real_pngs.py`: use PNG helpers; add selected image-fidelity cases.
- `tests/test_bump_upstream.py`: use automation helpers and add selected negative cases.
- `tests/test_dependency_refresh_classification.py`: use automation helpers.
- `tests/test_scan_upstream_surface.py`: use automation helpers where useful.
- `tests/test_update_github_actions.py`: use fake HTTP/subprocess helpers and add selected negative cases.
- `tests/test_validate_release_tag.py`: use fake HTTP helpers and add selected project-version negatives.
- `tests/test_github_settings_audit.py`: use workflow-run/subprocess helpers where useful.
- `tests/test_third_party_notices.py`: use automation helpers.
- `tests/test_workflows.py`: delete after workflow tests are split.
- `tests/test_makefile.py`: keep Makefile-only checks and move local API matrix target check here.
- `tests/test_release_artifacts.py`: use artifact helpers and add selected negatives.
- `tests/test_release_checks.py`: use workflow-run helper and add selected negatives.
- `tests/test_release_version.py`: add selected version consistency negatives if not covered elsewhere.
- `tests/test_scripts.py`: delete after tests are moved to focused files.
- `pyproject.toml`: update basedpyright include/exclude only if moving the typecheck fixture requires it.

## Task 1: Shared PNG And Warning Helpers

**Files:**

- Create: `tests/helpers/__init__.py`
- Create: `tests/helpers/png.py`
- Create: `tests/helpers/warnings.py`
- Create: `tests/test_helpers_png.py`
- Create: `tests/test_helpers_warnings.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Create failing helper tests for PNG structural checks**

Add `tests/test_helpers_png.py` with these tests first:

```python
"""Tests for shared PNG test helpers."""

from __future__ import annotations

import pytest

from tests.helpers.png import (
    PNG_SIGNATURE,
    assert_png_structure,
    make_png_bytes,
    png_chunk_names,
    png_text_chunks,
)


def test_assert_png_structure_accepts_generated_png() -> None:
    data = make_png_bytes()

    assert_png_structure(data)
    assert png_chunk_names(data)[:1] == [b"IHDR"]
    assert png_chunk_names(data)[-1:] == [b"IEND"]
    assert png_text_chunks(data)["Comment"] == "metadata makes this fixture less optimized"


def test_assert_png_structure_rejects_bad_signature() -> None:
    with pytest.raises(AssertionError, match="PNG signature"):
        assert_png_structure(b"not a png")


def test_assert_png_structure_rejects_trailing_bytes_after_iend() -> None:
    data = make_png_bytes() + b"trailing"

    with pytest.raises(AssertionError, match="trailing data"):
        assert_png_structure(data)


def test_assert_png_structure_rejects_crc_mismatch() -> None:
    data = bytearray(make_png_bytes())
    data[len(PNG_SIGNATURE) + 8] ^= 0x01

    with pytest.raises(AssertionError, match="invalid .* CRC"):
        assert_png_structure(bytes(data))
```

- [ ] **Step 2: Create failing helper tests for warning checks**

Add `tests/test_helpers_warnings.py`:

```python
"""Tests for shared warning assertion helpers."""

from __future__ import annotations

import warnings

import pytest

from tests.helpers.warnings import (
    PYOXIPNG_WARNING,
    assert_no_deprecation_warning,
    assert_pyoxipng_warning,
)


def test_assert_no_deprecation_warning_accepts_clean_call() -> None:
    result = assert_no_deprecation_warning(lambda: "ok")

    assert result == "ok"


def test_assert_no_deprecation_warning_rejects_deprecation() -> None:
    def warn() -> None:
        warnings.warn("deprecated", DeprecationWarning, stacklevel=2)

    with pytest.raises(AssertionError, match="unexpected DeprecationWarning"):
        assert_no_deprecation_warning(warn)


def test_assert_pyoxipng_warning_returns_value() -> None:
    def warn() -> str:
        warnings.warn(PYOXIPNG_WARNING, DeprecationWarning, stacklevel=2)
        return "compat"

    assert assert_pyoxipng_warning(warn) == "compat"
```

- [ ] **Step 3: Run helper tests and verify they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_helpers_png.py tests/test_helpers_warnings.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tests.helpers'`.

- [ ] **Step 4: Implement `tests/helpers/png.py`**

Create `tests/helpers/__init__.py` as an empty file.

Create `tests/helpers/png.py`:

```python
"""Shared PNG fixtures and assertions for tests."""

from __future__ import annotations

import binascii
import struct
import zlib
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(name: bytes, data: bytes) -> bytes:
    return (
        len(data).to_bytes(4, "big")
        + name
        + data
        + binascii.crc32(name + data).to_bytes(4, "big")
    )


def make_png_bytes() -> bytes:
    try:
        from PIL import Image, PngImagePlugin  # noqa: PLC0415 - optional on Python 3.10 lane.
    except ModuleNotFoundError:
        return make_stdlib_png_bytes()

    buffer = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "metadata makes this fixture less optimized")
    image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    image.save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def make_stdlib_png_bytes() -> bytes:
    width = 32
    height = 32
    pixel = bytes([255, 255, 255, 255])
    rows = b"".join(b"\x00" + pixel * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"".join(
        (
            PNG_SIGNATURE,
            png_chunk(b"IHDR", ihdr),
            png_chunk(b"tEXt", b"Comment\x00metadata makes this fixture less optimized"),
            png_chunk(b"IDAT", zlib.compress(rows)),
            png_chunk(b"IEND", b""),
        )
    )


def assert_png_path(path: Path) -> None:
    assert_png_structure(path.read_bytes())


def assert_png_structure(data: bytes) -> None:
    if not data.startswith(PNG_SIGNATURE):
        raise AssertionError("PNG output is missing the PNG signature")

    chunks: list[bytes] = []
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise AssertionError("PNG output has a truncated chunk")
        expected_crc = int.from_bytes(data[payload_end:crc_end], "big")
        actual_crc = binascii.crc32(name + data[payload_start:payload_end])
        if actual_crc != expected_crc:
            raise AssertionError(f"PNG output has an invalid {name.decode('ascii')} CRC")
        chunks.append(name)
        offset = crc_end
        if name == b"IEND":
            break

    if chunks[:1] != [b"IHDR"] or chunks[-1:] != [b"IEND"] or b"IDAT" not in chunks:
        raise AssertionError("PNG output is missing required chunks")
    if offset != len(data):
        raise AssertionError("PNG output has trailing data after IEND")


def png_chunk_names(data: bytes) -> list[bytes]:
    chunks: list[bytes] = []
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        chunks.append(name)
        offset += 12 + length
        if name == b"IEND":
            break
    return chunks


def png_text_chunks(data: bytes) -> dict[str, str]:
    chunks: dict[str, str] = {}
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if name == b"tEXt":
            key, _, value = payload.partition(b"\x00")
            chunks[key.decode("latin-1")] = value.decode("latin-1")
        offset += 12 + length
        if name == b"IEND":
            break
    return chunks


def decoded_rgba(data: bytes) -> tuple[tuple[int, int], bytes]:
    from PIL import Image  # noqa: PLC0415 - real pixel tests require Pillow.

    with Image.open(BytesIO(data)) as image:
        rgba = image.convert("RGBA")
        return rgba.size, rgba.tobytes()


def assert_same_pixels(left: bytes, right: bytes) -> None:
    assert decoded_rgba(right) == decoded_rgba(left)


def write_png(path: Path, data: bytes | None = None) -> Path:
    path.write_bytes(make_png_bytes() if data is None else data)
    return path
```

- [ ] **Step 5: Implement `tests/helpers/warnings.py`**

Create `tests/helpers/warnings.py`:

```python
"""Shared warning assertions for tests."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import TypeVar

PYOXIPNG_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)

T = TypeVar("T")


def assert_no_deprecation_warning(callback: Callable[[], T]) -> T:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = callback()

    matches = [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
    if matches:
        raise AssertionError(f"unexpected DeprecationWarning: {matches[0].message}")
    return result


def assert_pyoxipng_warning(callback: Callable[[], T]) -> T:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = callback()

    matches = [
        warning
        for warning in caught
        if issubclass(warning.category, DeprecationWarning)
        and PYOXIPNG_WARNING in str(warning.message)
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one pyoxipng compatibility warning, got {len(matches)}")
    return result
```

- [ ] **Step 6: Update `tests/conftest.py` to use PNG helper**

Replace the PNG-building helpers in `tests/conftest.py` with imports:

```python
"""Shared test fixtures."""

from pathlib import Path

import pytest

from tests.helpers.png import make_png_bytes


@pytest.fixture
def png_bytes() -> bytes:
    """Return generated PNG bytes."""
    return make_png_bytes()


@pytest.fixture
def png_path(tmp_path: Path, png_bytes: bytes) -> Path:
    """Create a small PNG that oxipng can optimize."""
    path = tmp_path / "cover.png"
    path.write_bytes(png_bytes)
    return path


@pytest.fixture
def corrupt_png_path(tmp_path: Path) -> Path:
    """Create a file that is not a PNG."""
    path = tmp_path / "not-a-png.png"
    path.write_bytes(b"not a png")
    return path
```

- [ ] **Step 7: Run helper tests and conftest smoke**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_helpers_png.py tests/test_helpers_warnings.py -v
```

Expected: PASS.

Run:

```bash
make develop AI=1
uv run --no-sync --group dev pytest tests/test_api.py::test_optimize_from_memory_bytes_returns_readable_bytes -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 1**

```bash
git add tests/conftest.py tests/helpers tests/test_helpers_png.py tests/test_helpers_warnings.py
git commit -m "test: add shared PNG and warning helpers"
```

## Task 2: Shared Automation, Artifact, And Workflow Helpers

**Files:**

- Create: `tests/helpers/automation.py`
- Create: `tests/helpers/artifacts.py`
- Create: `tests/helpers/workflows.py`
- Create: `tests/test_helpers_workflows.py`
- Modify: `tests/test_release_checks.py`
- Modify: `tests/test_wheel_tags.py`

- [ ] **Step 1: Add workflow helper tests first**

Create `tests/test_helpers_workflows.py`:

```python
"""Tests for shared workflow test helpers."""

from __future__ import annotations

import pytest

from tests.helpers.workflows import (
    assert_action_ref_is_reviewed,
    assert_ordered_steps,
    step_by_name,
    workflow_trigger,
)


def test_workflow_trigger_accepts_yaml_boolean_on_key() -> None:
    workflow = {True: {"push": None}}

    assert workflow_trigger(workflow) == {"push": None}


def test_step_by_name_rejects_duplicate_step_names() -> None:
    steps = [{"name": "Build"}, {"name": "Build"}]

    with pytest.raises(AssertionError, match="expected exactly one step named Build"):
        step_by_name(steps, "Build")


def test_assert_ordered_steps_rejects_reordered_steps() -> None:
    steps = [{"name": "Test"}, {"name": "Build"}]

    with pytest.raises(AssertionError, match="expected step order"):
        assert_ordered_steps(steps, ["Build", "Test"])


def test_assert_action_ref_is_reviewed_rejects_unreviewed_sha() -> None:
    with pytest.raises(AssertionError, match="unreviewed action ref"):
        assert_action_ref_is_reviewed("example/action@0123456789abcdef0123456789abcdef01234567")
```

- [ ] **Step 2: Run workflow helper tests and verify they fail**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_helpers_workflows.py -v
```

Expected: FAIL with import errors for missing workflow helpers.

- [ ] **Step 3: Implement `tests/helpers/automation.py`**

Create:

```python
"""Shared fake automation boundaries for tests."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class FakeResponse:
    """Small context-manager response for urlopen-style tests."""

    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


@dataclass
class RecordedRun:
    command: list[str]
    cwd: Path | None
    check: bool | None
    capture_output: bool | None = None
    text: bool | None = None


@dataclass
class RunRecorder:
    stdout: str = ""
    returncode: int = 0
    calls: list[RecordedRun] = field(default_factory=list)

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(
            RecordedRun(
                command=command,
                cwd=kwargs.get("cwd") if isinstance(kwargs.get("cwd"), Path) else None,
                check=kwargs.get("check") if isinstance(kwargs.get("check"), bool) else None,
                capture_output=(
                    kwargs.get("capture_output")
                    if isinstance(kwargs.get("capture_output"), bool)
                    else None
                ),
                text=kwargs.get("text") if isinstance(kwargs.get("text"), bool) else None,
            )
        )
        return subprocess.CompletedProcess(command, self.returncode, stdout=self.stdout)


def fake_which(prefix: str = "/fake/bin"):
    def resolve(name: str) -> str:
        return f"{prefix}/{name}"

    return resolve


def completed_json(payload: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], 0, stdout=json.dumps(payload))
```

- [ ] **Step 4: Implement `tests/helpers/artifacts.py`**

Create:

```python
"""Shared artifact factories for release tests."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_VERSION = "10.1.1.post1"


def wheel_name(
    *,
    distribution: str = "oxipng_pybind",
    version: str = DEFAULT_VERSION,
    python_tag: str = "cp310",
    abi_tag: str = "abi3",
    platform: str = "manylinux_2_34_x86_64",
) -> str:
    return f"{distribution}-{version}-{python_tag}-{abi_tag}-{platform}.whl"


def touch_wheel(directory: Path, **kwargs: str) -> Path:
    wheel = directory / wheel_name(**kwargs)
    wheel.write_text("", encoding="utf-8")
    return wheel


def workflow_run(
    *,
    name: str = "ci",
    head_sha: str = "abc",
    status: str = "completed",
    conclusion: str = "success",
    event: str = "push",
    workflow_database_id: int = 1,
) -> dict[str, object]:
    return {
        "name": name,
        "headSha": head_sha,
        "status": status,
        "conclusion": conclusion,
        "event": event,
        "workflowDatabaseId": workflow_database_id,
    }


def write_zip(path: Path, entries: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in entries.items():
            archive.writestr(name, value)
    return path


def write_targz(path: Path, root: str, entries: dict[str, str]) -> Path:
    with tarfile.open(path, "w:gz") as archive:
        for name, value in entries.items():
            payload = value.encode()
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(payload)
            archive.addfile(info, fileobj=io.BytesIO(payload))
    return path
```

- [ ] **Step 5: Implement `tests/helpers/workflows.py`**

Create:

```python
"""Shared workflow assertions for tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[2]
Workflow = dict[Any, Any]
Step = dict[str, Any]

REVIEWED_ACTION_REFS = {
    "actions/checkout": "de0fac2e4500dabe0009e67214ff5f5447ce83dd",
    "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",
    "actions/upload-artifact": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    "actions/download-artifact": "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
    "peter-evans/create-pull-request": "5f6978faf089d4d20b00c7766989d076bb2fc7f1",
    "PyO3/maturin-action": "e83996d129638aa358a18fbd1dfb82f0b0fb5d3b",
    "pypa/gh-action-pypi-publish": "cef221092ed1bacb1cc03d23a2d87d1d172e277b",
}
RUST_TOOLCHAIN_VERSION = "1.95.0"


def load_workflow(relative: str) -> Workflow:
    data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast("Workflow", data)


def workflow_trigger(workflow: Workflow) -> Workflow:
    trigger = workflow.get("on", workflow[True])
    assert isinstance(trigger, dict)
    return cast("Workflow", trigger)


def step_by_name(steps: list[Step], name: str) -> Step:
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name}, found {len(matches)}"
    return matches[0]


def step_index(steps: list[Step], name: str) -> int:
    return steps.index(step_by_name(steps, name))


def assert_ordered_steps(steps: list[Step], names: list[str]) -> None:
    indexes = [step_index(steps, name) for name in names]
    assert indexes == sorted(indexes), f"expected step order {names}, got indexes {indexes}"


def parse_action_ref(uses: str) -> tuple[str, str]:
    action, ref = uses.rsplit("@", 1)
    return action, ref


def assert_action_ref_is_reviewed(uses: str) -> None:
    if uses.startswith("dtolnay/rust-toolchain@"):
        assert uses == f"dtolnay/rust-toolchain@{RUST_TOOLCHAIN_VERSION}"
        return

    action, ref = parse_action_ref(uses)
    expected = REVIEWED_ACTION_REFS.get(action)
    assert expected is not None, f"unreviewed action ref: {uses}"
    assert ref == expected, f"{action} uses {ref}, expected reviewed ref {expected}"
```

- [ ] **Step 6: Update `tests/test_release_checks.py` to use `workflow_run`**

Replace repeated run dictionaries with `workflow_run` calls from
`tests.helpers.artifacts`. Add these two negative tests:

```python
def test_required_workflows_fail_for_wrong_head_sha() -> None:
    runs = [
        workflow_run(
            name="ci",
            head_sha="other",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"],
        ),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]


def test_required_workflows_fail_when_status_is_not_completed() -> None:
    runs = [
        workflow_run(
            name="ci",
            status="in_progress",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/ci.yml"],
        ),
        workflow_run(
            name="api-matrix",
            workflow_database_id=WORKFLOW_IDS[".github/workflows/api-matrix.yml"],
        ),
    ]

    errors = check_required_workflows(
        runs,
        sha="abc",
        required=REQUIRED_WORKFLOWS,
        workflow_ids=WORKFLOW_IDS,
    )

    assert errors == ["ci did not complete successfully for abc"]
```

- [ ] **Step 7: Update `tests/test_wheel_tags.py` to use `touch_wheel`**

Import `touch_wheel` and replace repeated literal wheel filename setup with
`touch_wheel` calls. Add this negative test:

```python
def test_rejects_invalid_wheel_filename_format(tmp_path: Path) -> None:
    wheel = tmp_path / "not-a-wheel.whl"
    wheel.write_text("", encoding="utf-8")

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel.name} is not a valid wheel filename"]
```

This expected message matches `scripts/check_wheel_tags.py`. Keep the test as
a clean returned-error contract, not an exception contract.

- [ ] **Step 8: Run helper and changed release tests**

Run:

```bash
uv run --no-sync --group dev pytest \
  tests/test_helpers_workflows.py \
  tests/test_release_checks.py \
  tests/test_wheel_tags.py \
  -v
```

Expected: PASS.

- [ ] **Step 9: Commit Task 2**

```bash
git add tests/helpers/automation.py tests/helpers/artifacts.py tests/helpers/workflows.py tests/test_helpers_workflows.py tests/test_release_checks.py tests/test_wheel_tags.py
git commit -m "test: add shared automation and workflow helpers"
```

## Task 3: Split Public API And Compatibility Tests

**Files:**

- Create: `tests/test_api_surface.py`
- Create: `tests/test_optimize_file_api.py`
- Create: `tests/test_optimize_memory_api.py`
- Create: `tests/test_option_validation.py`
- Create: `tests/test_pyoxipng_compat.py`
- Create: `tests/test_raw_image_api.py`
- Modify: `tests/test_api.py`
- Use: `tests/helpers/png.py`
- Use: `tests/helpers/warnings.py`

- [ ] **Step 1: Establish baseline for current API suite**

Run:

```bash
make develop AI=1
uv run --no-sync --group dev pytest tests/test_api.py -v
```

Expected: PASS before moving tests. If it fails, stop and fix the baseline
before reorganizing.

- [ ] **Step 2: Move imports and small local classes to the new files**

Each new file should import only what it needs. Start from these imports and
trim unused names before committing:

```python
from pathlib import Path
from typing import Any, cast

import pytest

from tests.helpers.png import (
    assert_png_path,
    assert_png_structure,
    png_chunk_names,
    png_text_chunks,
)
from tests.helpers.warnings import PYOXIPNG_WARNING, assert_no_deprecation_warning
```

Keep local classes where used:

- `CustomPathLike` belongs in `tests/test_optimize_file_api.py`.
- `BytesMethodOnly` belongs in `tests/test_optimize_memory_api.py`.
- `ExplodingValue` belongs in `tests/test_option_validation.py`.
- `Palette` belongs in `tests/test_raw_image_api.py`.

- [ ] **Step 3: Move API surface tests**

Move these tests from `tests/test_api.py` to `tests/test_api_surface.py`:

- `test_import_supported_api`
- `test_optimize_signature_matches_supported_api`
- `test_optimize_from_memory_signature_matches_supported_api`
- `test_analyze_signature_matches_supported_api`
- `test_public_callables_expose_runtime_docstrings`
- `test_pyoxipng_compatibility_exports_and_docstrings`

After moving, run:

```bash
uv run --no-sync --group dev pytest tests/test_api_surface.py -v
```

Expected: PASS.

- [ ] **Step 4: Move file optimize and analyze tests**

Move file-path and analyze tests into `tests/test_optimize_file_api.py`:

- `test_optimize_in_place_with_high_compression_level`
- `test_optimize_to_output_path`
- `test_analyze_returns_optimization_result_without_writing`
- `test_analyze_accepts_stable_options_without_warning`
- `test_analyze_rejects_file_write_options`
- `test_optimize_accepts_string_paths`
- `test_optimize_accepts_custom_pathlike`
- `test_optimize_interlace_keep_is_accepted`
- `test_enum_and_string_aliases_for_file_options`
- `test_invalid_level_raises_value_error`
- `test_optimize_level_rejects_bool`
- `test_analyze_level_rejects_bool`
- `test_unsupported_keyword_raises_type_error`
- `test_invalid_enum_string_raises_value_error`
- `test_empty_filter_sequence_raises_value_error`
- `test_non_bool_file_flags_raise_type_error`
- `test_backup_with_explicit_output_raises_value_error`
- `test_backup_refuses_to_overwrite_existing_backup`
- `test_backup_refuses_existing_symlink_backup`
- `test_backup_creates_copy_for_in_place_optimization`
- `test_missing_input_raises_file_not_found`
- `test_missing_output_parent_raises_os_error`
- `test_preserve_attrs_copies_permissions_and_mtime`
- `test_corrupt_input_raises_png_error`
- `test_analyze_advanced_bool_options_without_warning`
- `test_analyze_timeout_without_warning`
- `test_analyze_rejects_negative_timeout`

Strengthen `test_optimize_to_output_path` by asserting the input bytes are
unchanged:

```python
def test_optimize_to_output_path_does_not_modify_input(png_path: Path, tmp_path: Path) -> None:
    original = png_path.read_bytes()
    output = tmp_path / "optimized.png"

    optimize(png_path, output, level=6)

    assert output.exists()
    assert_png_path(output)
    assert png_path.read_bytes() == original
```

Run:

```bash
uv run --no-sync --group dev pytest tests/test_optimize_file_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Move memory optimize tests**

Move memory tests into `tests/test_optimize_memory_api.py`:

- `test_filter_enum_and_string_aliases_for_memory`
- `test_filter_sequence_is_accepted`
- `test_predefined_filter_optimizes_memory`
- `test_pyoxipng_rowfilter_values_optimize_memory`
- `test_pyoxipng_strip_member_factories_warn_and_work`
- `test_pyoxipng_deflaters_optimize_memory`
- `test_advanced_bool_options_optimize_memory_without_warning`
- `test_timeout_optimizes_memory_without_warning`
- `test_timeout_none_optimizes_memory_without_warning`
- `test_advanced_bool_none_optimizes_memory_without_warning`
- `test_max_decompressed_size_optimizes_memory_without_warning`
- `test_pyoxipng_timeout_rejects_out_of_range_values`
- `test_pyoxipng_timeout_rejects_bool`
- `test_pyoxipng_advanced_options_reject_invalid_values`
- `test_stable_option_paths_do_not_emit_deprecation_warnings`
- `test_optimize_from_memory_level_rejects_bool`
- `test_non_bool_memory_flags_raise_type_error`
- `test_optimize_from_memory_bytes_returns_readable_bytes`
- `test_optimize_from_memory_bytearray_returns_readable_bytes`
- `test_optimize_from_memory_memoryview_returns_readable_bytes`
- `test_optimize_from_memory_rejects_generic_buffers`
- `test_optimize_from_memory_rejects_tobytes_only_objects`
- `test_optimize_from_memory_rejects_file_only_options`
- `test_max_decompressed_size_limit_is_enforced`
- `test_corrupt_memory_input_raises_png_error`
- `test_optimize_from_memory_rejects_negative_timeout`
- `test_enum_value_property_errors_are_propagated`

Parametrize accepted buffer types:

```python
@pytest.mark.parametrize("buffer_factory", [bytes, bytearray, memoryview])
def test_optimize_from_memory_accepts_supported_buffers(
    png_bytes: bytes,
    buffer_factory: Any,
) -> None:
    output = optimize_from_memory(buffer_factory(png_bytes))

    assert isinstance(output, bytes)
    assert_png_structure(output)
```

Run:

```bash
uv run --no-sync --group dev pytest tests/test_optimize_memory_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Move option validation tests**

Move cross-cutting option/factory validation into `tests/test_option_validation.py`:

- `test_predefined_filter_factory_uses_basic_filters_without_warning`
- `test_predefined_filter_rejects_empty_sequence`
- `test_predefined_filter_rejects_non_basic_filters`
- `test_strip_factories_reject_invalid_chunk_names`
- `test_strip_factories_accept_iterables`
- `test_predefined_filter_accepts_iterables`
- `test_predefined_filter_rejects_mapping`
- `test_strip_factories_reject_scalar_and_mapping_outer_containers`
- `test_strip_factories_reject_byte_chunk_names`
- `test_predefined_filter_rejects_scalar_and_mapping_outer_containers`
- `test_pyoxipng_deflaters_reject_invalid_values`
- `test_max_decompressed_size_rejects_invalid_values`
- `test_bit_depth_value_property_errors_are_propagated`

Add missing range tests:

```python
@pytest.mark.parametrize("level", [-1, 7])
def test_optimize_from_memory_level_rejects_out_of_range_values(
    png_bytes: bytes,
    level: int,
) -> None:
    with pytest.raises(ValueError, match="level must be between 0 and 6"):
        optimize_from_memory(png_bytes, level=level)


@pytest.mark.parametrize("value", [0, -1])
def test_max_decompressed_size_rejects_non_positive_values(
    png_bytes: bytes,
    value: int,
) -> None:
    with pytest.raises(ValueError, match="max_decompressed_size"):
        optimize_from_memory(png_bytes, max_decompressed_size=value)
```

Run:

```bash
uv run --no-sync --group dev pytest tests/test_option_validation.py -v
```

Expected: PASS.

- [ ] **Step 7: Move pyoxipng compatibility tests**

Move compatibility warning and factory tests into `tests/test_pyoxipng_compat.py`:

- `test_deprecated_enum_aliases_warn_on_access`
- `test_pyoxipng_rowfilter_aliases_warn_on_access`
- `test_stable_enum_members_do_not_warn_on_access`
- `test_pyoxipng_color_factories_warn_and_stable_factories_do_not_warn`
- `test_pyoxipng_predefined_filter_rejects_non_string_entries`
- `test_pyoxipng_indexed_color_requires_palette`
- `test_pyoxipng_alpha_color_rejects_transparent`
- `test_pyoxipng_non_indexed_color_rejects_palette`
- `test_pyoxipng_strip_factories_optimize_file`
- `test_pyoxipng_keep_factories_optimize_file`
- `test_deflater_libdeflater_bool_is_compatibility_path`
- `test_deflater_zopfli_bool_is_compatibility_path`

Use `assert_no_deprecation_warning` for stable paths.

Run:

```bash
uv run --no-sync --group dev pytest tests/test_pyoxipng_compat.py -v
```

Expected: PASS.

- [ ] **Step 8: Move RawImage tests**

Move all `RawImage` constructor, output, chunk, palette, transparency, and
create-option tests into `tests/test_raw_image_api.py`, including:

- `test_pyoxipng_raw_image_constructor_accepts_rgb_descriptor`
- through
- `test_raw_image_rejects_negative_timeout`
- plus `test_max_decompressed_size_optimizes_raw_image_without_warning`
- plus `test_raw_image_advanced_bool_options_without_warning`
- plus `test_raw_image_timeout_without_warning`

Use shared `assert_png_structure`, `png_chunk_names`, and `png_text_chunks`.

Add this focused negative case:

```python
def test_raw_image_stable_constructor_rejects_zero_dimensions() -> None:
    with pytest.raises(ValueError, match="raw image dimensions"):
        RawImage(0, 1, ColorType.rgb, BitDepth.eight, b"")
```

Run:

```bash
uv run --no-sync --group dev pytest tests/test_raw_image_api.py -v
```

Expected: PASS.

- [ ] **Step 9: Delete `tests/test_api.py` after all moved tests pass**

Run:

```bash
uv run --no-sync --group dev pytest \
  tests/test_api_surface.py \
  tests/test_optimize_file_api.py \
  tests/test_optimize_memory_api.py \
  tests/test_option_validation.py \
  tests/test_pyoxipng_compat.py \
  tests/test_raw_image_api.py \
  -v
```

Expected: PASS.

Then remove `tests/test_api.py`.

- [ ] **Step 10: Commit Task 3**

```bash
git add tests/test_api_surface.py tests/test_optimize_file_api.py tests/test_optimize_memory_api.py tests/test_option_validation.py tests/test_pyoxipng_compat.py tests/test_raw_image_api.py tests/test_api.py
git commit -m "test: split public API contract tests"
```

## Task 4: PNG Behavior And Docs Examples

**Files:**

- Modify: `tests/test_real_pngs.py`
- Modify: `tests/test_docs_examples.py`
- Use: `tests/helpers/png.py`
- Use: `tests/helpers/warnings.py`

- [ ] **Step 1: Baseline docs and real PNG tests**

Run:

```bash
make develop AI=1
uv run --no-sync --group dev pytest tests/test_docs_examples.py tests/test_real_pngs.py -v
```

Expected: PASS.

- [ ] **Step 2: Refactor `tests/test_real_pngs.py` to use shared helpers**

Remove local `decoded_rgba` and replace local assertions with:

```python
from tests.helpers.png import assert_same_pixels, decoded_rgba
```

Keep the local `make_real_png(mode: str)` only if it still contains mode-specific
Pillow setup not suited to `tests/helpers/png.py`. If multiple files need it,
move it into `tests/helpers/png.py`.

Use:

```python
assert_same_pixels(original, optimized)
```

for file and memory preservation tests.

- [ ] **Step 3: Add selected image-fidelity cases**

Add one grayscale-alpha real PNG case if Pillow supports mode `LA`:

```python
def test_optimize_real_png_memory_preserves_grayscale_alpha_pixels() -> None:
    original = make_real_png("LA")

    optimized = optimize_from_memory(original, level=1)

    assert_same_pixels(original, optimized)
```

If `make_real_png("LA")` needs mode support, extend its branch table with a
small 8-bit grayscale-alpha image:

```python
elif mode == "LA":
    image = Image.new("LA", (4, 4), (128, 192))
```

- [ ] **Step 4: Strengthen docs example PNG assertions**

In `tests/test_docs_examples.py`, replace weak PNG output assertions:

```python
assert output_path.read_bytes()
assert optimized
assert b"tEXt" in png_bytes
assert b"iCCP" in png_bytes
```

with:

```python
assert_png_path(output_path)
assert_png_structure(optimized)
assert png_text_chunks(png_bytes)["Comment"] == "Created by example"
assert b"iCCP" in png_chunk_names(png_bytes)
```

Use the actual text key/value from the current example body when replacing
the `tEXt` assertion.

- [ ] **Step 5: Keep docs tests scoped to executable examples**

Do not duplicate every API negative in docs tests. Keep these docs negatives:

- corrupt file example raises `PngError`
- corrupt memory example raises `PngError`
- raw image invalid data length raises `PngError`
- migration guide rejected raw image shape raises `TypeError`

Move any added API-contract negative back to the API files from Task 3.

- [ ] **Step 6: Run docs and real PNG tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_docs_examples.py tests/test_real_pngs.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 4**

```bash
git add tests/test_docs_examples.py tests/test_real_pngs.py tests/helpers/png.py
git commit -m "test: strengthen PNG behavior assertions"
```

## Task 5: Automation Script Test Reorganization

**Files:**

- Modify: `tests/test_bump_upstream.py`
- Modify: `tests/test_dependency_refresh_classification.py`
- Modify: `tests/test_scan_upstream_surface.py`
- Modify: `tests/test_update_github_actions.py`
- Modify: `tests/test_validate_release_tag.py`
- Modify: `tests/test_github_settings_audit.py`
- Modify: `tests/test_third_party_notices.py`
- Use: `tests/helpers/automation.py`

- [ ] **Step 1: Baseline automation script tests**

Run:

```bash
uv run --no-sync --group dev pytest \
  tests/test_bump_upstream.py \
  tests/test_dependency_refresh_classification.py \
  tests/test_scan_upstream_surface.py \
  tests/test_update_github_actions.py \
  tests/test_validate_release_tag.py \
  tests/test_github_settings_audit.py \
  tests/test_third_party_notices.py \
  -v
```

Expected: PASS.

- [ ] **Step 2: Replace repeated fake HTTP responses**

Use `FakeResponse` from `tests.helpers.automation` in:

- `tests/test_bump_upstream.py`
- `tests/test_validate_release_tag.py`
- `tests/test_update_github_actions.py`

Keep each test's URL and timeout assertions. Do not weaken public boundary
checks for official API endpoints.

- [ ] **Step 3: Replace repeated fake subprocess runners**

Use `RunRecorder` and `fake_which` in:

- `tests/test_bump_upstream.py`
- `tests/test_dependency_refresh_classification.py`
- `tests/test_scan_upstream_surface.py`
- `tests/test_third_party_notices.py`

Keep exact command-list assertions where the command is a security or release
contract. Prefer partial semantic assertions when the exact order is not the
contract.

- [ ] **Step 4: Add GitHub output carriage-return negative in bump tests**

Update the existing parametrization in `tests/test_bump_upstream.py`:

```python
@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("bad\nname", "10.2.0"),
        ("bad\rname", "10.2.0"),
        ("version", "10.2.0\nbad"),
        ("version", "10.2.0\rbad"),
    ],
)
def test_emit_github_output_rejects_newlines(name: str, value: str) -> None:
    with pytest.raises(ValueError, match="must not contain newlines"):
        bump_upstream.emit_github_output(name, value)
```

If this fails for carriage returns, update the production helper to reject both
`\n` and `\r` because GitHub output injection is a CI safety boundary.

- [ ] **Step 5: Add malformed release payload negatives**

In `tests/test_bump_upstream.py`, add:

```python
def test_latest_upstream_version_rejects_missing_tag_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda url, *, timeout: FakeResponse({"name": "release"}),
    )

    with pytest.raises(KeyError, match="tag_name"):
        bump_upstream.latest_upstream_version()
```

If the current script raises a different exception, update the script to raise
a clear `RuntimeError("GitHub release payload is missing tag_name")` and update
the test to match that message.

- [ ] **Step 6: Add release-tag project-version negatives**

In `tests/test_validate_release_tag.py`, add:

```python
def test_read_project_version_rejects_missing_project_table(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text("[tool.example]\nname = 'x'\n", encoding="utf-8")

    with pytest.raises(ReleaseTagError, match="project.version"):
        read_project_version(path)


def test_read_project_version_rejects_missing_version(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text("[project]\nname = 'oxipng-pybind'\n", encoding="utf-8")

    with pytest.raises(ReleaseTagError, match="project.version"):
        read_project_version(path)
```

If `read_project_version` currently raises `KeyError`, update the script to
raise the user-facing `ReleaseTagError`.

- [ ] **Step 7: Run automation tests**

Run:

```bash
uv run --no-sync --group dev pytest \
  tests/test_bump_upstream.py \
  tests/test_dependency_refresh_classification.py \
  tests/test_scan_upstream_surface.py \
  tests/test_update_github_actions.py \
  tests/test_validate_release_tag.py \
  tests/test_github_settings_audit.py \
  tests/test_third_party_notices.py \
  -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 5**

```bash
git add tests/helpers/automation.py tests/test_bump_upstream.py tests/test_dependency_refresh_classification.py tests/test_scan_upstream_surface.py tests/test_update_github_actions.py tests/test_validate_release_tag.py tests/test_github_settings_audit.py tests/test_third_party_notices.py scripts/bump_upstream.py scripts/validate_release_tag.py
git commit -m "test: consolidate automation script fixtures"
```

## Task 6: Workflow And Makefile Policy Split

**Files:**

- Create: `tests/test_workflow_security.py`
- Create: `tests/test_workflow_release_policy.py`
- Create: `tests/test_workflow_automation_policy.py`
- Modify: `tests/test_workflows.py`
- Modify: `tests/test_makefile.py`
- Use: `tests/helpers/workflows.py`

- [ ] **Step 1: Baseline workflow and Makefile tests**

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflows.py tests/test_makefile.py -v
```

Expected: PASS.

- [ ] **Step 2: Move security tests to `tests/test_workflow_security.py`**

Move these tests and helper assertions:

- `test_write_token_workflows_pin_create_pull_request_to_sha`
- `test_workflow_actions_are_pinned_to_commit_shas`
- `test_release_actions_are_pinned_to_reviewed_shas`
- `assert_release_tag_checkout_uses_ephemeral_credentials`
- token containment assertions from `test_release_tag_workflow_creates_tags_only_after_main_checks`

Add reviewed action allowlist coverage:

```python
def test_workflow_actions_use_reviewed_refs() -> None:
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        workflow = load_workflow(str(path.relative_to(ROOT)))
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if isinstance(uses, str):
                    assert_action_ref_is_reviewed(uses)
```

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflow_security.py -v
```

Expected: PASS.

- [ ] **Step 3: Move release policy tests**

Move to `tests/test_workflow_release_policy.py`:

- `test_wheel_tag_checker_uses_only_stdlib_dependencies`
- `test_wheel_smoke_installs_local_wheel_with_pinned_test_dependency`
- `test_wheel_workflow_can_publish_to_testpypi_manually`
- `test_pypi_publish_requires_strict_release_tag_validation`
- `test_wheel_workflow_waits_on_tag_commit_checks`
- `test_release_tag_workflow_creates_tags_only_after_main_checks`
- `test_release_docs_describe_tag_gates_and_automation`

Keep exact shell snippets only where they prove release safety. Use helpers for
step order and reviewed action refs.

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflow_release_policy.py -v
```

Expected: PASS.

- [ ] **Step 4: Move automation workflow tests**

Move to `tests/test_workflow_automation_policy.py`:

- `test_dependabot_version_updates_are_not_configured`
- `test_workflows_use_current_rust_toolchain`
- `test_upstream_bump_auto_merge_is_gated_by_ci_and_wheels`
- `test_upstream_bump_docs_describe_ci_gated_auto_merge`
- `test_dependency_refresh_auto_merge_is_ci_gated`
- `test_dependency_refresh_docs_describe_ci_gated_auto_merge`
- `test_api_matrix_uses_locked_dev_dependencies`
- `test_ci_workflow_splits_independent_checks`
- `test_failed_check_retry_is_single_attempt_and_delayed`

Run:

```bash
uv run --no-sync --group dev pytest tests/test_workflow_automation_policy.py -v
```

Expected: PASS.

- [ ] **Step 5: Move Makefile-only API matrix check**

Move `test_makefile_has_local_api_matrix_target` from workflow tests into
`tests/test_makefile.py`.

Replace `test_github_ci_installs_rust_before_make_ci` with a YAML-aware check
or move it to workflow automation policy. The check must inspect the same job's
steps, not global source text order.

Use this pattern:

```python
def test_github_ci_installs_rust_before_make_ci() -> None:
    workflow = load_workflow(".github/workflows/ci.yml")
    rust_tests = workflow["jobs"]["rust-tests"]["steps"]

    assert step_index(rust_tests, "Install Rust") < step_index(rust_tests, "Run Rust tests")
```

Use the actual step names from `.github/workflows/ci.yml`.

- [ ] **Step 6: Delete `tests/test_workflows.py` after split passes**

Run:

```bash
uv run --no-sync --group dev pytest \
  tests/test_workflow_security.py \
  tests/test_workflow_release_policy.py \
  tests/test_workflow_automation_policy.py \
  tests/test_makefile.py \
  -v
```

Expected: PASS.

Then remove `tests/test_workflows.py`.

- [ ] **Step 7: Commit Task 6**

```bash
git add tests/helpers/workflows.py tests/test_workflow_security.py tests/test_workflow_release_policy.py tests/test_workflow_automation_policy.py tests/test_workflows.py tests/test_makefile.py
git commit -m "test: split workflow policy tests"
```

## Task 7: Release, Build, CLI, And Static Policy Cleanup

**Files:**

- Create: `tests/test_packaging_metadata.py`
- Create: `tests/test_ai_filter_log.py`
- Create: `tests/test_smoke_wheel.py`
- Modify: `tests/test_release_artifacts.py`
- Modify: `tests/test_wheel_tags.py`
- Modify: `tests/test_release_version.py`
- Modify: `tests/test_scripts.py`
- Use: `tests/helpers/artifacts.py`

- [ ] **Step 1: Baseline release/build/script tests**

Run:

```bash
make develop AI=1
uv run --no-sync --group dev pytest \
  tests/test_release_artifacts.py \
  tests/test_wheel_tags.py \
  tests/test_release_version.py \
  tests/test_scripts.py \
  -v
```

Expected: PASS.

- [ ] **Step 2: Move packaging metadata checks**

Move these tests from `tests/test_scripts.py` to `tests/test_packaging_metadata.py`:

- `test_script_security_ignores_are_line_scoped`
- `test_third_party_notices_are_packaged`
- `test_pillow_dependency_keeps_python_310_wheel_compatibility`
- `test_python_314_classifier_matches_api_matrix`
- `test_api_surface_records_python_rowfilter_compatibility`

Run:

```bash
uv run --no-sync --group dev pytest tests/test_packaging_metadata.py -v
```

Expected: PASS.

- [ ] **Step 3: Move AI log tests**

Move these tests from `tests/test_scripts.py` to `tests/test_ai_filter_log.py`:

- `test_ai_filter_log_prints_tail`
- `test_ai_filter_log_streams_large_logs_without_early_noise`
- `test_ai_filter_log_reports_missing_file`

Add wrong-argument-count coverage:

```python
def test_ai_filter_log_reports_wrong_argument_count(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["ai_filter_log.py"])

    assert ai_filter_log.main() == 1
    assert "usage:" in capsys.readouterr().err.lower()
```

Run:

```bash
uv run --no-sync --group dev pytest tests/test_ai_filter_log.py -v
```

Expected: PASS.

- [ ] **Step 4: Move smoke wheel tests**

Move these tests from `tests/test_scripts.py` to `tests/test_smoke_wheel.py`:

- `test_smoke_wheel_main_exercises_installed_package`
- `test_smoke_wheel_release_mode_has_no_editable_typing_fallback`

Make the local smoke test stdlib-safe:

```python
def test_smoke_wheel_main_exercises_installed_package_with_stdlib_png() -> None:
    assert smoke_wheel.main(["--allow-editable", "--stdlib-png"]) == 0
```

Replace source-string fallback coverage with a behavior test around the helper
that checks typing files. If `scripts/smoke_wheel.py` does not expose a helper,
extract a small function named `verify_packaged_typing_files(package_path, *,
allow_editable: bool)`.

- [ ] **Step 5: Move wheel tag CLI tests**

Keep pure `check_wheels` tests in `tests/test_wheel_tags.py`.

Move only these CLI/direct-execution tests from `tests/test_scripts.py` to
`tests/test_wheel_tags.py`:

- `test_check_wheel_tags_main_success`
- `test_check_wheel_tags_main_reports_errors`
- `test_check_wheel_tags_runs_as_script_before_install`

Remove duplicate pure-function cases from `tests/test_scripts.py` because
`tests/test_wheel_tags.py` owns them.

- [ ] **Step 6: Move bump and surface overlap tests**

Move these from `tests/test_scripts.py`:

- `test_normalize_version_removes_leading_v` to `tests/test_bump_upstream.py`
- `test_issue_body_mentions_manual_surface_triage` to `tests/test_bump_upstream.py`
- `test_scan_upstream_surface_tracks_color_type_and_bit_depth` to `tests/test_scan_upstream_surface.py`

- [ ] **Step 7: Add release artifact negative cases**

In `tests/test_release_artifacts.py`, add:

```python
def test_rejects_missing_artifact_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.whl"

    errors = verify_release_artifacts.check_artifacts([missing])

    assert errors == [f"{missing} does not exist"]


def test_rejects_unsupported_artifact_suffix(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("not a release artifact", encoding="utf-8")

    errors = verify_release_artifacts.check_artifacts([artifact])

    assert errors == [f"{artifact.name} is not a supported release artifact"]


def test_rejects_invalid_sdist_tarball(tmp_path: Path) -> None:
    sdist = tmp_path / SDIST_NAME
    sdist.write_text("not a tarball", encoding="utf-8")

    errors = verify_release_artifacts.check_artifacts([sdist])

    assert errors == [f"{sdist.name} is not a valid sdist tarball"]
```

These expected messages match `scripts/verify_release_artifacts.py`. If a new
script crash appears here, change the script to return one of these clear error
strings.

- [ ] **Step 8: Delete `tests/test_scripts.py` after all moves pass**

Run:

```bash
uv run --no-sync --group dev pytest \
  tests/test_packaging_metadata.py \
  tests/test_ai_filter_log.py \
  tests/test_smoke_wheel.py \
  tests/test_release_artifacts.py \
  tests/test_wheel_tags.py \
  tests/test_bump_upstream.py \
  tests/test_scan_upstream_surface.py \
  -v
```

Expected: PASS.

Then remove `tests/test_scripts.py`.

- [ ] **Step 9: Commit Task 7**

```bash
git add tests/test_packaging_metadata.py tests/test_ai_filter_log.py tests/test_smoke_wheel.py tests/test_release_artifacts.py tests/test_wheel_tags.py tests/test_release_version.py tests/test_scripts.py tests/test_bump_upstream.py tests/test_scan_upstream_surface.py scripts/smoke_wheel.py scripts/verify_release_artifacts.py scripts/ai_filter_log.py
git commit -m "test: separate release and CLI policy tests"
```

## Task 8: Typecheck Fixture Move

**Files:**

- Create: `tests/typecheck/typing_filter_options.py`
- Delete: `tests/typing_filter_options.py`
- Modify: `pyproject.toml` only if needed

- [ ] **Step 1: Move typecheck fixture**

Run:

```bash
mkdir -p tests/typecheck
git mv tests/typing_filter_options.py tests/typecheck/typing_filter_options.py
```

- [ ] **Step 2: Verify basedpyright still includes the fixture**

Run:

```bash
make typecheck AI=1
```

Expected: PASS.

If basedpyright stops checking the moved file, update `[tool.basedpyright]`
in `pyproject.toml`:

```toml
include = ["oxipng", "tests", "scripts"]
```

This value already includes `tests`; only change it if the project config
changed before this task runs.

- [ ] **Step 3: Commit Task 8**

```bash
git add tests/typecheck/typing_filter_options.py tests/typing_filter_options.py pyproject.toml
git commit -m "test: move typecheck fixtures under tests typecheck"
```

## Task 9: Integration Verification And Cleanup

**Files:**

- Review: `tests/helpers/*.py`
- Review: `tests/test_*.py`
- Review: `tests/typecheck/typing_filter_options.py`
- Review: `scripts/bump_upstream.py`
- Review: `scripts/validate_release_tag.py`
- Review: `scripts/smoke_wheel.py`
- Review: `scripts/verify_release_artifacts.py`
- Review: `scripts/ai_filter_log.py`
- Review: `pyproject.toml`
- Review: `docs/plans/2026-05-28-test-architecture-overhaul-design.md`

- [ ] **Step 1: Check for stale imports and deleted files**

Run:

```bash
rg -n "test_api|test_workflows|test_scripts|typing_filter_options|assert_readable_png|PYOXIPNG_WARNING" tests pyproject.toml
```

Expected:

- No references to deleted test modules except in Git history.
- No local duplicate `assert_readable_png_*` helpers outside `tests/helpers/png.py`.
- `PYOXIPNG_WARNING` imported from `tests.helpers.warnings` where shared.

- [ ] **Step 2: Run full Python test suite**

Run:

```bash
make test-py AI=1
```

Expected: PASS.

- [ ] **Step 3: Run lint and typecheck**

Run:

```bash
make lint AI=1
make typecheck AI=1
```

Expected: PASS.

- [ ] **Step 4: Run full CI gate**

Run:

```bash
make ci AI=1
```

Expected: PASS. If the environment blocks part of CI, record the exact failing
target and the reason in the final handoff.

- [ ] **Step 5: Review diff shape**

Run:

```bash
git status --short
git diff --stat main HEAD
```

Expected:

- Changes are grouped by helper extraction and test-domain split.
- No origin push occurred.
- No unrelated source or docs files changed except scripts that needed clearer
  user-facing errors for new negative tests.

- [ ] **Step 6: Commit integration cleanup if needed**

If the integration pass changed files after the domain commits, commit them:

```bash
git add tests scripts pyproject.toml
git commit -m "test: integrate test architecture overhaul"
```

If there are no remaining changes, skip this commit.

## Self-Review Checklist For Implementers

Before asking for review, confirm:

- Each new test has a clear good state or a meaningful bad state.
- Helpers are directly tested when they enforce important assertions.
- Exact source-string checks remain only where the exact string is the contract.
- `tests/test_api.py`, `tests/test_workflows.py`, and `tests/test_scripts.py`
  were deleted only after their tests were moved and passing.
- No test imports from optional Pillow unless that test is allowed to require
  Pillow.
- `make test-py AI=1`, `make lint AI=1`, and `make typecheck AI=1` pass.
- `make ci AI=1` was run or a concrete blocker was recorded.

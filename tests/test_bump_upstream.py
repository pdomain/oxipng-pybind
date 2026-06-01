"""Tests for upstream bump helpers."""
# pyright: reportUnannotatedClassAttribute=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportUnusedParameter=false

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path

import pytest
import tomlkit

from scripts import bump_upstream
from tests.helpers.automation import FakeResponse, RecordedRun, RunRecorder, fake_which


def test_normalize_version_strips_v_prefix() -> None:
    assert bump_upstream.normalize_version("v10.1.1") == "10.1.1"
    assert bump_upstream.normalize_version("10.1.1") == "10.1.1"


def test_normalize_version_removes_leading_v() -> None:
    assert bump_upstream.normalize_version("v10.1.2") == "10.1.2"


@pytest.mark.parametrize("version", ["release-10.1.1", "v10.1", "10.1.1\nbad", "10.1.1.post1"])
def test_normalize_version_rejects_unexpected_upstream_tags(version: str) -> None:
    with pytest.raises(ValueError, match="unsupported upstream version"):
        bump_upstream.normalize_version(version)


def test_next_post_release_adds_or_increments_post_segment() -> None:
    assert bump_upstream.next_post_release("10.1.1") == "10.1.1.post1"
    assert bump_upstream.next_post_release("10.1.1.post1") == "10.1.1.post2"


@pytest.mark.parametrize("version", ["v10.1.1", "10.1", "10.1.1.dev1"])
def test_next_post_release_rejects_unsupported_versions(version: str) -> None:
    with pytest.raises(ValueError, match="unsupported wrapper version"):
        bump_upstream.next_post_release(version)


def test_latest_upstream_version_reads_github_release_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int]] = []

    def fake_urlopen(url: str, *, timeout: int) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse({"tag_name": "v10.2.0"})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    assert bump_upstream.latest_upstream_version() == "10.2.0"
    assert calls == [(bump_upstream.LATEST_RELEASE_URL, 30)]


def test_latest_upstream_version_rejects_missing_tag_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda url, *, timeout: FakeResponse({"name": "release"}),
    )

    with pytest.raises(RuntimeError, match="missing tag_name"):
        bump_upstream.latest_upstream_version()


def test_crates_io_version_available_checks_exact_crate_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int]] = []

    def fake_urlopen(url: str, *, timeout: int) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse({"version": {"num": "10.2.0"}})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    assert bump_upstream.crates_io_version_available("10.2.0") is True
    assert calls == [(bump_upstream.CRATES_IO_VERSION_URL.format(version="10.2.0"), 30)]


def test_crates_io_version_available_treats_missing_version_as_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(url: str, *, timeout: int) -> object:
        raise urllib.error.HTTPError(url, 404, "not found", hdrs=Message(), fp=None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    assert bump_upstream.crates_io_version_available("10.2.0") is False


def test_update_pyproject_toml(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        """
[project]
name = "oxipng-pybind"
version = "10.1.0"
""".lstrip(),
        encoding="utf-8",
    )

    bump_upstream.update_pyproject_toml(path, "10.1.1")

    data = tomlkit.parse(path.read_text(encoding="utf-8"))
    assert data["project"]["version"] == "10.1.1"


def test_read_pyproject_version(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        """
[project]
name = "oxipng-pybind"
version = "10.1.1.post1"
""".lstrip(),
        encoding="utf-8",
    )

    assert bump_upstream.read_pyproject_version(path) == "10.1.1.post1"


def test_update_cargo_toml(tmp_path: Path) -> None:
    path = tmp_path / "Cargo.toml"
    path.write_text(
        """
[package]
name = "oxipng-pybind"
version = "10.1.0"

[dependencies]
oxi = { package = "oxipng", version = "=10.1.0", default-features = false, features = ["parallel", "zopfli"] }
""".lstrip(),
        encoding="utf-8",
    )

    bump_upstream.update_cargo_toml(path, "10.1.1")

    data = tomlkit.parse(path.read_text(encoding="utf-8"))
    assert data["package"]["version"] == "10.1.1"
    assert data["dependencies"]["oxi"]["version"] == "=10.1.1"


def test_read_pinned_upstream_version(tmp_path: Path) -> None:
    path = tmp_path / "Cargo.toml"
    path.write_text(
        """
[package]
name = "oxipng-pybind"
version = "10.1.1"

[dependencies]
oxi = { package = "oxipng", version = "=10.1.1" }
""".lstrip(),
        encoding="utf-8",
    )

    assert bump_upstream.read_pinned_upstream_version(path) == "10.1.1"


def test_bump_upstream_leaves_post_release_when_upstream_is_current(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    cargo = tmp_path / "Cargo.toml"
    target = tmp_path / "target-version.txt"
    pyproject.write_text(
        """
[project]
name = "oxipng-pybind"
version = "10.1.1.post1"
""".lstrip(),
        encoding="utf-8",
    )
    cargo.write_text(
        """
[package]
name = "oxipng-pybind"
version = "10.1.1"

[dependencies]
oxi = { package = "oxipng", version = "=10.1.1" }
""".lstrip(),
        encoding="utf-8",
    )
    cargo_lock_calls: list[str] = []
    uv_lock_calls: list[None] = []

    monkeypatch.setattr(bump_upstream, "update_cargo_lock", cargo_lock_calls.append)
    monkeypatch.setattr(bump_upstream, "update_uv_lock", lambda: uv_lock_calls.append(None))

    changed = bump_upstream.bump_upstream_files(
        "10.1.1",
        pyproject_path=pyproject,
        cargo_path=cargo,
        target_version_path=target,
    )

    assert changed is False
    assert bump_upstream.read_pyproject_version(pyproject) == "10.1.1.post1"
    assert bump_upstream.read_pinned_upstream_version(cargo) == "10.1.1"
    assert target.read_text(encoding="utf-8") == "10.1.1\n"
    assert cargo_lock_calls == []
    assert uv_lock_calls == []


def test_bump_upstream_resets_wrapper_version_for_new_upstream(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    cargo = tmp_path / "Cargo.toml"
    target = tmp_path / "target-version.txt"
    pyproject.write_text(
        """
[project]
name = "oxipng-pybind"
version = "10.1.1.post2"
""".lstrip(),
        encoding="utf-8",
    )
    cargo.write_text(
        """
[package]
name = "oxipng-pybind"
version = "10.1.1"

[dependencies]
oxi = { package = "oxipng", version = "=10.1.1" }
""".lstrip(),
        encoding="utf-8",
    )
    cargo_lock_calls: list[str] = []
    uv_lock_calls: list[None] = []

    monkeypatch.setattr(bump_upstream, "update_cargo_lock", cargo_lock_calls.append)
    monkeypatch.setattr(bump_upstream, "update_uv_lock", lambda: uv_lock_calls.append(None))

    changed = bump_upstream.bump_upstream_files(
        "10.2.0",
        pyproject_path=pyproject,
        cargo_path=cargo,
        target_version_path=target,
    )

    assert changed is True
    assert bump_upstream.read_pyproject_version(pyproject) == "10.2.0"
    assert bump_upstream.read_pinned_upstream_version(cargo) == "10.2.0"
    assert target.read_text(encoding="utf-8") == "10.2.0\n"
    assert cargo_lock_calls == ["10.2.0"]
    assert uv_lock_calls == [None]


def test_bump_wrapper_post_release_updates_only_pyproject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "oxipng-pybind"
version = "10.1.1.post1"
""".lstrip(),
        encoding="utf-8",
    )
    uv_lock_calls: list[None] = []

    monkeypatch.setattr(bump_upstream, "update_uv_lock", lambda: uv_lock_calls.append(None))

    version = bump_upstream.bump_wrapper_post_release(pyproject)

    assert version == "10.1.1.post2"
    assert bump_upstream.read_pyproject_version(pyproject) == "10.1.1.post2"
    assert uv_lock_calls == [None]


def test_main_wrapper_post_mode_updates_wrapper_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    outputs: list[tuple[str, str]] = []

    monkeypatch.setattr(bump_upstream, "bump_wrapper_post_release", lambda: "10.1.1.post1")
    monkeypatch.setattr(
        bump_upstream, "emit_github_output", lambda name, value: outputs.append((name, value))
    )

    assert bump_upstream.main(["--wrapper-post"]) == 0

    assert outputs == [("wrapper-version", "10.1.1.post1")]
    assert capsys.readouterr().out == "updated oxipng-pybind wrapper version to 10.1.1.post1\n"


def test_main_upstream_mode_reports_current_pin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    outputs: list[tuple[str, str]] = []

    monkeypatch.setattr(bump_upstream, "latest_upstream_version", lambda: "10.1.1")
    monkeypatch.setattr(bump_upstream, "crates_io_version_available", lambda version: True)
    monkeypatch.setattr(bump_upstream, "bump_upstream_files", lambda version: False)
    monkeypatch.setattr(
        bump_upstream, "emit_github_output", lambda name, value: outputs.append((name, value))
    )

    assert bump_upstream.main([]) == 0

    assert outputs == [("target-version", "10.1.1")]
    assert capsys.readouterr().out == "oxipng-pybind already pins oxipng 10.1.1\n"


def test_main_upstream_mode_exits_cleanly_when_crate_is_not_indexed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    outputs: list[tuple[str, str]] = []
    bump_calls: list[str] = []

    monkeypatch.setattr(bump_upstream, "latest_upstream_version", lambda: "10.2.0")
    monkeypatch.setattr(bump_upstream, "crates_io_version_available", lambda version: False)
    monkeypatch.setattr(bump_upstream, "bump_upstream_files", bump_calls.append)
    monkeypatch.setattr(
        bump_upstream, "emit_github_output", lambda name, value: outputs.append((name, value))
    )

    assert bump_upstream.main([]) == 0

    assert bump_calls == []
    assert outputs == [("target-version", "10.2.0"), ("upstream-crate-available", "false")]
    assert (
        capsys.readouterr().out == "oxipng 10.2.0 is not available on crates.io yet; retry later.\n"
    )


def test_update_cargo_lock_runs_precise_cargo_update(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RunRecorder()

    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", recorder)

    bump_upstream.update_cargo_lock("10.2.0")

    assert recorder.calls == [
        RecordedRun(
            ["/usr/bin/cargo", "update", "-p", "oxipng", "--precise", "10.2.0"],
            cwd=bump_upstream.ROOT,
            check=True,
        )
    ]


def test_append_upstream_release_note_adds_to_release_notes_section(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Release Notes\n", encoding="utf-8")

    bump_upstream.append_upstream_release_note("10.2.0", root=tmp_path)

    text = changelog.read_text(encoding="utf-8")
    assert (
        "## Release Notes\n\n## 10.2.0 - Bump Version\n\n- Rebuilt `oxipng-pybind` to track upstream `oxipng` 10.2.0."
        in text
    )


def test_append_upstream_release_note_is_idempotent(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Release Notes\n", encoding="utf-8")

    bump_upstream.append_upstream_release_note("10.2.0", root=tmp_path)
    bump_upstream.append_upstream_release_note("10.2.0", root=tmp_path)

    assert (
        changelog.read_text(encoding="utf-8").count(
            "## 10.2.0 - Bump Version\n\n- Rebuilt `oxipng-pybind` to track upstream `oxipng` 10.2.0."
        )
        == 1
    )


def test_bump_upstream_files_adds_upstream_release_note(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    cargo = tmp_path / "Cargo.toml"
    target = tmp_path / "target-version.txt"
    changelog = tmp_path / "CHANGELOG.md"
    pyproject.write_text(
        """
[project]
name = "oxipng-pybind"
version = "10.1.1.post2"
""".lstrip(),
        encoding="utf-8",
    )
    cargo.write_text(
        """
[package]
name = "oxipng-pybind"
version = "10.1.1"

[dependencies]
oxi = { package = "oxipng", version = "=10.1.1" }
""".lstrip(),
        encoding="utf-8",
    )
    changelog.write_text("# Changelog\n\n## Release Notes\n", encoding="utf-8")
    cargo_lock_calls: list[str] = []
    uv_lock_calls: list[None] = []

    monkeypatch.setattr(bump_upstream, "update_cargo_lock", cargo_lock_calls.append)
    monkeypatch.setattr(bump_upstream, "update_uv_lock", lambda: uv_lock_calls.append(None))

    changed = bump_upstream.bump_upstream_files(
        "10.2.0",
        pyproject_path=pyproject,
        cargo_path=cargo,
        target_version_path=target,
        changelog_root=tmp_path,
    )

    assert changed is True
    assert (
        "## 10.2.0 - Bump Version\n\n- Rebuilt `oxipng-pybind` to track upstream `oxipng` 10.2.0."
        in changelog.read_text(encoding="utf-8")
    )
    assert cargo_lock_calls == ["10.2.0"]
    assert uv_lock_calls == [None]


def test_update_uv_lock_runs_uv_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RunRecorder()

    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", recorder)

    bump_upstream.update_uv_lock()

    assert recorder.calls == [
        RecordedRun(["/usr/bin/uv", "lock"], cwd=bump_upstream.ROOT, check=True)
    ]


def test_write_target_version(tmp_path: Path) -> None:
    path = tmp_path / "out" / "version.txt"

    bump_upstream.write_target_version("10.2.0", path)

    assert path.read_text(encoding="utf-8") == "10.2.0\n"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("bad\nname", "10.2.0"),
        ("bad\rname", "10.2.0"),
        ("version", "10.2.0\nbad"),
        ("version", "10.2.0\rbad"),
    ],
)
def test_emit_github_output_rejects_newlines(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, value: str
) -> None:
    output = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    with pytest.raises(ValueError, match="must not contain newlines"):
        bump_upstream.emit_github_output(name, value)

    assert not output.exists()


def test_find_surface_issue_returns_matching_version(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RunRecorder(
        stdout=json.dumps(
            [
                {
                    "number": 12,
                    "title": "Evaluate upstream oxipng 10.2.0 surface changes",
                }
            ]
        )
    )

    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", recorder)

    assert bump_upstream.find_surface_issue("10.2.0") == 12
    assert recorder.calls == [
        RecordedRun(
            [
                "/usr/bin/gh",
                "issue",
                "list",
                "--label",
                "upstream-surface",
                "--state",
                "open",
                "--json",
                "number,title",
            ],
            cwd=bump_upstream.ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    ]


def test_find_surface_issue_ignores_different_version(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RunRecorder(
        stdout=json.dumps(
            [
                {
                    "number": 12,
                    "title": "Evaluate upstream oxipng 10.3.0 surface changes",
                }
            ]
        )
    )

    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", recorder)

    assert bump_upstream.find_surface_issue("10.2.0") is None
    assert recorder.calls == [
        RecordedRun(
            [
                "/usr/bin/gh",
                "issue",
                "list",
                "--label",
                "upstream-surface",
                "--state",
                "open",
                "--json",
                "number,title",
            ],
            cwd=bump_upstream.ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    ]


def test_upsert_surface_issue_creates_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report = tmp_path / "pr-body-section.md"
    report.write_text("report", encoding="utf-8")
    recorder = RunRecorder()

    monkeypatch.setattr(bump_upstream, "find_surface_issue", lambda version: None)
    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", recorder)

    bump_upstream.upsert_surface_issue("10.2.0", report)

    assert recorder.calls == [
        RecordedRun(
            [
                "/usr/bin/gh",
                "label",
                "create",
                "upstream-surface",
                "--color",
                "BFD4F2",
                "--description",
                "Upstream oxipng surface change awaiting triage",
                "--force",
            ],
            cwd=bump_upstream.ROOT,
            check=True,
        ),
        RecordedRun(
            [
                "/usr/bin/gh",
                "issue",
                "create",
                "--title",
                "Evaluate upstream oxipng 10.2.0 surface changes",
                "--label",
                "upstream-surface",
                "--body",
                bump_upstream.issue_body("10.2.0", "report"),
            ],
            cwd=bump_upstream.ROOT,
            check=True,
        ),
    ]


def test_upsert_surface_issue_ensure_label_called_before_issue_create(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ensure_label must be called before gh issue create so a missing label never hard-fails."""
    report = tmp_path / "pr-body-section.md"
    report.write_text("report", encoding="utf-8")
    call_order: list[str] = []
    recorder = RunRecorder()

    original_call = recorder.__call__

    def ordered_call(command: list[str], **kwargs: object) -> object:
        if "label" in command and "create" in command:
            call_order.append("label_create")
        elif "issue" in command and "create" in command:
            call_order.append("issue_create")
        return original_call(command, **kwargs)

    monkeypatch.setattr(bump_upstream, "find_surface_issue", lambda version: None)
    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", ordered_call)

    bump_upstream.upsert_surface_issue("10.2.0", report)

    assert call_order == ["label_create", "issue_create"]


def test_upsert_surface_issue_ensure_label_tolerates_already_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A non-zero exit from gh label create --force must not abort issue creation."""
    report = tmp_path / "pr-body-section.md"
    report.write_text("report", encoding="utf-8")
    issue_create_called: list[bool] = []

    def run_with_label_failure(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if "label" in command and "create" in command:
            raise subprocess.CalledProcessError(1, command, output="")
        if "issue" in command and "create" in command:
            issue_create_called.append(True)
        return subprocess.CompletedProcess(command, 0, stdout="")

    monkeypatch.setattr(bump_upstream, "find_surface_issue", lambda version: None)
    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", run_with_label_failure)

    # Must not raise even when label create exits non-zero
    bump_upstream.upsert_surface_issue("10.2.0", report)

    assert issue_create_called == [True]


def test_issue_body_mentions_manual_surface_triage() -> None:
    body = bump_upstream.issue_body("10.1.2", "## report")

    assert "Upstream version: 10.1.2" in body
    assert "- [ ] expose now" in body
    assert "- [ ] defer and document" in body
    assert "- [ ] reject as intentionally unsupported" in body


def test_upsert_surface_issue_updates_existing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report = tmp_path / "pr-body-section.md"
    report.write_text("report", encoding="utf-8")
    recorder = RunRecorder()

    monkeypatch.setattr(bump_upstream, "find_surface_issue", lambda version: 12)
    monkeypatch.setattr(shutil, "which", fake_which("/usr/bin"))
    monkeypatch.setattr(subprocess, "run", recorder)

    bump_upstream.upsert_surface_issue("10.2.0", report)

    assert recorder.calls == [
        RecordedRun(
            [
                "/usr/bin/gh",
                "issue",
                "edit",
                "12",
                "--body",
                bump_upstream.issue_body("10.2.0", "report"),
            ],
            cwd=bump_upstream.ROOT,
            check=True,
        )
    ]

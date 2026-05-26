"""Tests for upstream bump helpers."""
# pyright: reportUnannotatedClassAttribute=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportUnusedParameter=false

import json
import shutil
import subprocess
import urllib.request
from pathlib import Path
from types import TracebackType

import pytest
import tomlkit

from scripts import bump_upstream


def test_normalize_version_strips_v_prefix() -> None:
    assert bump_upstream.normalize_version("v10.1.1") == "10.1.1"
    assert bump_upstream.normalize_version("10.1.1") == "10.1.1"


def test_latest_upstream_version_reads_github_release_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            pass

        def read(self) -> bytes:
            return b'{"tag_name": "v10.2.0"}'

    calls: list[tuple[str, int]] = []

    def fake_urlopen(url: str, *, timeout: int) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    assert bump_upstream.latest_upstream_version() == "10.2.0"
    assert calls == [(bump_upstream.LATEST_RELEASE_URL, 30)]


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


def test_update_cargo_lock_runs_precise_cargo_update(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path, bool]] = []

    def fake_which(executable: str) -> str | None:
        assert executable == "cargo"
        return "/usr/bin/cargo"

    def fake_run(command: list[str], *, cwd: Path, check: bool) -> object:
        calls.append((command, cwd, check))
        return object()

    monkeypatch.setattr(shutil, "which", fake_which)
    monkeypatch.setattr(subprocess, "run", fake_run)

    bump_upstream.update_cargo_lock("10.2.0")

    assert calls == [
        (
            ["/usr/bin/cargo", "update", "-p", "oxipng", "--precise", "10.2.0"],
            bump_upstream.ROOT,
            True,
        ),
    ]


def test_update_uv_lock_runs_uv_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path, bool]] = []

    def fake_which(executable: str) -> str | None:
        assert executable == "uv"
        return "/usr/bin/uv"

    def fake_run(command: list[str], *, cwd: Path, check: bool) -> object:
        calls.append((command, cwd, check))
        return object()

    monkeypatch.setattr(shutil, "which", fake_which)
    monkeypatch.setattr(subprocess, "run", fake_run)

    bump_upstream.update_uv_lock()

    assert calls == [(["/usr/bin/uv", "lock"], bump_upstream.ROOT, True)]


def test_write_target_version(tmp_path: Path) -> None:
    path = tmp_path / "out" / "version.txt"

    bump_upstream.write_target_version("10.2.0", path)

    assert path.read_text(encoding="utf-8") == "10.2.0\n"


def test_find_surface_issue_returns_matching_version(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(executable: str) -> str | None:
        assert executable == "gh"
        return "/usr/bin/gh"

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> object:
        assert command[:3] == ["/usr/bin/gh", "issue", "list"]
        assert cwd == bump_upstream.ROOT
        assert check is True
        assert capture_output is True
        assert text is True

        class Result:
            stdout = json.dumps(
                [
                    {
                        "number": 12,
                        "title": "Evaluate upstream oxipng 10.2.0 surface changes",
                    }
                ]
            )

        return Result()

    monkeypatch.setattr(shutil, "which", fake_which)
    monkeypatch.setattr(subprocess, "run", fake_run)

    assert bump_upstream.find_surface_issue("10.2.0") == 12


def test_find_surface_issue_ignores_different_version(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(executable: str) -> str | None:
        return f"/usr/bin/{executable}"

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> object:
        class Result:
            stdout = json.dumps(
                [
                    {
                        "number": 12,
                        "title": "Evaluate upstream oxipng 10.3.0 surface changes",
                    }
                ]
            )

        return Result()

    monkeypatch.setattr(shutil, "which", fake_which)
    monkeypatch.setattr(subprocess, "run", fake_run)

    assert bump_upstream.find_surface_issue("10.2.0") is None


def test_upsert_surface_issue_creates_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report = tmp_path / "pr-body-section.md"
    report.write_text("report", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(bump_upstream, "find_surface_issue", lambda version: None)
    monkeypatch.setattr(shutil, "which", lambda executable: f"/usr/bin/{executable}")

    def fake_run(command: list[str], *, cwd: Path, check: bool) -> object:
        calls.append(command)
        return object()

    monkeypatch.setattr(subprocess, "run", fake_run)

    bump_upstream.upsert_surface_issue("10.2.0", report)

    assert calls[0][:3] == ["/usr/bin/gh", "issue", "create"]


def test_upsert_surface_issue_updates_existing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report = tmp_path / "pr-body-section.md"
    report.write_text("report", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(bump_upstream, "find_surface_issue", lambda version: 12)
    monkeypatch.setattr(shutil, "which", lambda executable: f"/usr/bin/{executable}")

    def fake_run(command: list[str], *, cwd: Path, check: bool) -> object:
        calls.append(command)
        return object()

    monkeypatch.setattr(subprocess, "run", fake_run)

    bump_upstream.upsert_surface_issue("10.2.0", report)

    assert calls[0][:4] == ["/usr/bin/gh", "issue", "edit", "12"]

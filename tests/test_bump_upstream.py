"""Tests for upstream bump helpers."""

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
name = "se-pyoxipng"
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
name = "se-pyoxipng"
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

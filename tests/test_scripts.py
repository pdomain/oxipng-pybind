"""Tests for small command-line helper entry points."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts import ai_filter_log, check_wheel_tags, smoke_wheel

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_smoke_wheel_main_exercises_installed_package() -> None:
    assert smoke_wheel.main() == 0


def test_check_wheel_tags_main_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_wheel_tags.py",
            "--expected-platform",
            "manylinux_2_34_x86_64",
            "oxipng_pybind-10.1.1-cp310-abi3-manylinux_2_34_x86_64.whl",
        ],
    )

    assert check_wheel_tags.main() == 0


def test_check_wheel_tags_main_reports_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_wheel_tags.py",
            "--expected-platform",
            "manylinux_2_34_x86_64",
        ],
    )

    assert check_wheel_tags.main() == 1
    assert "no wheel paths provided" in capsys.readouterr().out


def test_ai_filter_log_prints_tail(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    log = tmp_path / "command.log"
    log.write_text("\n".join(f"line {index}" for index in range(130)), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["ai_filter_log.py", str(log)])

    assert ai_filter_log.main() == 0
    output = capsys.readouterr().out
    assert "line 9\n" not in output
    assert "line 10\n" in output
    assert "line 129\n" in output


def test_ai_filter_log_reports_missing_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    missing = tmp_path / "missing.log"
    monkeypatch.setattr("sys.argv", ["ai_filter_log.py", str(missing)])

    assert ai_filter_log.main() == 1
    assert "log file not found" in capsys.readouterr().err

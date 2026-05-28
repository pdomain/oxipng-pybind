"""Tests for the AI log filter CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts import ai_filter_log

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


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


def test_ai_filter_log_streams_large_logs_without_early_noise(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    log = tmp_path / "command.log"
    log.write_text(
        "\n".join([*(f"info line {index}" for index in range(10_000)), "ERROR: final failure"]),
        encoding="utf-8",
    )

    def fail_read_text(self: Path, *_args: object, **_kwargs: object) -> str:
        raise AssertionError(f"whole-file read attempted for {self}")

    monkeypatch.setattr(type(log), "read_text", fail_read_text)
    monkeypatch.setattr("sys.argv", ["ai_filter_log.py", str(log)])

    assert ai_filter_log.main() == 0
    output = capsys.readouterr().out
    assert "ERROR: final failure" in output
    assert "info line 0\n" not in output
    assert len(output.splitlines()) <= 160


def test_ai_filter_log_reports_missing_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    missing = tmp_path / "missing.log"
    monkeypatch.setattr("sys.argv", ["ai_filter_log.py", str(missing)])

    assert ai_filter_log.main() == 1
    assert "log file not found" in capsys.readouterr().err


def test_ai_filter_log_reports_wrong_argument_count(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["ai_filter_log.py"])

    assert ai_filter_log.main() == 2
    assert "usage:" in capsys.readouterr().err.lower()

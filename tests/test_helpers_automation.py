"""Tests for shared automation test helpers."""

from __future__ import annotations

import subprocess

import pytest

from tests.helpers.automation import RunRecorder


def test_run_recorder_raises_for_check_true_failure() -> None:
    recorder = RunRecorder(stdout="failed\n", returncode=2)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        recorder(["tool", "arg"], check=True)

    assert exc_info.value.returncode == 2
    assert exc_info.value.cmd == ["tool", "arg"]
    assert exc_info.value.stdout == "failed\n"
    assert recorder.calls[0].command == ["tool", "arg"]
    assert recorder.calls[0].check is True


def test_run_recorder_returns_for_check_false_failure() -> None:
    recorder = RunRecorder(stdout="failed\n", returncode=2)

    result = recorder(["tool", "arg"], check=False)

    assert result.returncode == 2
    assert result.stdout == "failed\n"
    assert recorder.calls[0].check is False

"""Shared fake automation boundaries for tests."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class FakeResponse:
    """Small context-manager response for urlopen-style tests."""

    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.payload: object = payload
        self.status: int = status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


@dataclass
class RecordedRun:
    command: list[str]
    cwd: Path | str | None
    check: bool | None
    capture_output: bool | None = None
    text: bool | None = None


@dataclass
class RunRecorder:
    stdout: str = ""
    returncode: int = 0
    allowed_kwargs: tuple[str, ...] = ("cwd", "check", "capture_output", "text")
    calls: list[RecordedRun] = field(default_factory=list)

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        unexpected = sorted(set(kwargs) - set(self.allowed_kwargs))
        if unexpected:
            joined = ", ".join(unexpected)
            raise AssertionError(f"unexpected subprocess kwargs: {joined}")
        cwd = kwargs.get("cwd")
        check = _optional_bool(kwargs.get("check"))
        self.calls.append(
            RecordedRun(
                command=command,
                cwd=cwd if isinstance(cwd, (Path, str)) else None,
                check=check,
                capture_output=_optional_bool(kwargs.get("capture_output")),
                text=_optional_bool(kwargs.get("text")),
            )
        )
        completed = subprocess.CompletedProcess(command, self.returncode, stdout=self.stdout)
        if check is True and self.returncode != 0:
            raise subprocess.CalledProcessError(
                self.returncode,
                command,
                output=self.stdout,
            )
        return completed


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def fake_which(prefix: str = "/fake/bin") -> Callable[[str], str]:
    def resolve(name: str) -> str:
        return f"{prefix}/{name}"

    return resolve


def completed_json(payload: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], 0, stdout=json.dumps(payload))

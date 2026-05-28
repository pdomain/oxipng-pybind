"""Shared artifact factories for release tests."""

from __future__ import annotations

import io
import tarfile
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_VERSION = "10.1.1.post1"


def wheel_name(
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


def workflow_run(  # noqa: PLR0913 - Factory mirrors GitHub workflow run fields.
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

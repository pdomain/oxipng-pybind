"""Tests for release artifact content validation."""

from __future__ import annotations

import io
import tarfile
import zipfile
from typing import TYPE_CHECKING

from scripts import verify_release_artifacts

if TYPE_CHECKING:
    from pathlib import Path

WHEEL_NAME = "oxipng_pybind-10.1.1-cp310-abi3-manylinux_2_28_x86_64.whl"
SDIST_NAME = "oxipng_pybind-10.1.1.tar.gz"
DIST_INFO = "oxipng_pybind-10.1.1.dist-info"
SDIST_ROOT = "oxipng_pybind-10.1.1"

BASE_WHEEL_ENTRIES = {
    f"{DIST_INFO}/METADATA": "Name: oxipng-pybind\nVersion: 10.1.1\n",
    f"{DIST_INFO}/WHEEL": "Wheel-Version: 1.0\n",
    f"{DIST_INFO}/RECORD": "",
    f"{DIST_INFO}/licenses/LICENSE": "license\n",
    f"{DIST_INFO}/licenses/THIRD_PARTY_NOTICES.md": "notices\n",
    "oxipng/__init__.py": "",
    "oxipng/_pyoxipng_compat.py": "",
    "oxipng/__init__.pyi": "",
    "oxipng/py.typed": "",
    "_oxipng/__init__.py": "",
    "_oxipng/_oxipng.abi3.so": "",
}

BASE_SDIST_ENTRIES = {
    "pyproject.toml": "[project]\nname = 'oxipng-pybind'\nversion = '10.1.1'\n",
    "Cargo.toml": "[package]\nname = 'oxipng-pybind'\n",
    "Cargo.lock": "",
    "README.md": "# oxipng-pybind\n",
    "LICENSE": "license\n",
    "THIRD_PARTY_NOTICES.md": "notices\n",
    "src/lib.rs": "",
    "oxipng/__init__.py": "",
    "oxipng/_pyoxipng_compat.py": "",
    "oxipng/__init__.pyi": "",
    "oxipng/py.typed": "",
}


def write_wheel(
    directory: Path,
    *,
    omit: set[str] | None = None,
    extra: dict[str, str] | None = None,
) -> Path:
    wheel = directory / WHEEL_NAME
    omitted = omit or set()
    entries = {name: value for name, value in BASE_WHEEL_ENTRIES.items() if name not in omitted}
    entries.update(extra or {})
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, value in entries.items():
            archive.writestr(name, value)
    return wheel


def write_sdist(
    directory: Path,
    *,
    omit: set[str] | None = None,
) -> Path:
    sdist = directory / SDIST_NAME
    omitted = omit or set()
    with tarfile.open(sdist, "w:gz") as archive:
        for name, value in BASE_SDIST_ENTRIES.items():
            if name in omitted:
                continue
            payload = value.encode()
            info = tarfile.TarInfo(f"{SDIST_ROOT}/{name}")
            info.size = len(payload)
            archive.addfile(info, fileobj=io.BytesIO(payload))
    return sdist


def test_accepts_valid_wheel_and_sdist(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path)
    sdist = write_sdist(tmp_path)

    assert verify_release_artifacts.check_artifacts([wheel, sdist]) == []


def test_rejects_invalid_wheel_zip(tmp_path: Path) -> None:
    wheel = tmp_path / WHEEL_NAME
    wheel.write_text("not a zip", encoding="utf-8")

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert errors == [f"{wheel.name} is not a valid wheel zip"]


def test_rejects_missing_wheel_metadata(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path, omit={f"{DIST_INFO}/METADATA"})

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert f"{wheel.name} is missing wheel metadata {DIST_INFO}/METADATA" in errors


def test_rejects_missing_wheel_typing_files(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path, omit={"oxipng/__init__.pyi", "oxipng/py.typed"})

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert f"{wheel.name} is missing package file oxipng/__init__.pyi" in errors
    assert f"{wheel.name} is missing package file oxipng/py.typed" in errors


def test_rejects_missing_wheel_license_file(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path, omit={f"{DIST_INFO}/licenses/LICENSE"})

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert f"{wheel.name} is missing license file LICENSE" in errors


def test_rejects_missing_wheel_notice_file(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path, omit={f"{DIST_INFO}/licenses/THIRD_PARTY_NOTICES.md"})

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert f"{wheel.name} is missing notice file THIRD_PARTY_NOTICES.md" in errors


def test_rejects_missing_wheel_native_extension(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path, omit={"_oxipng/_oxipng.abi3.so"})

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert f"{wheel.name} must contain exactly one _oxipng package native extension" in errors


def test_rejects_duplicate_wheel_native_extensions(tmp_path: Path) -> None:
    wheel = write_wheel(tmp_path, extra={"_oxipng/_oxipng.cpython-313-x86_64-linux-gnu.so": ""})

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert f"{wheel.name} must contain exactly one _oxipng package native extension" in errors


def test_rejects_unexpected_wheel_extension_layout(tmp_path: Path) -> None:
    wheel = write_wheel(
        tmp_path,
        omit={"_oxipng/_oxipng.abi3.so"},
        extra={"oxipng/_oxipng.abi3.so": ""},
    )

    errors = verify_release_artifacts.check_artifacts([wheel])

    assert (
        f"{wheel.name} has native extension outside the expected _oxipng package layout" in errors
    )


def test_rejects_missing_sdist_project_file(tmp_path: Path) -> None:
    sdist = write_sdist(tmp_path, omit={"pyproject.toml"})

    errors = verify_release_artifacts.check_artifacts([sdist])

    assert f"{sdist.name} is missing source file pyproject.toml" in errors


def test_rejects_missing_sdist_typing_file(tmp_path: Path) -> None:
    sdist = write_sdist(tmp_path, omit={"oxipng/py.typed"})

    errors = verify_release_artifacts.check_artifacts([sdist])

    assert f"{sdist.name} is missing source file oxipng/py.typed" in errors

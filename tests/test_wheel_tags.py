"""Tests for wheel tag validation."""

from pathlib import Path

from scripts.check_wheel_tags import check_wheels
from tests.helpers.artifacts import touch_wheel


def test_valid_abi3_linux_tag(tmp_path: Path) -> None:
    wheel = touch_wheel(tmp_path)
    errors = check_wheels(
        [wheel],
        "manylinux_2_34_x86_64",
    )

    assert errors == []


def test_valid_abi3_macos_wildcard_tag(tmp_path: Path) -> None:
    wheel = touch_wheel(tmp_path, platform="macosx_14_0_arm64")
    errors = check_wheels(
        [wheel],
        "macosx_*_arm64",
    )

    assert errors == []


def test_invalid_cpython_specific_abi_tag(tmp_path: Path) -> None:
    wheel = touch_wheel(tmp_path, python_tag="cp313", abi_tag="cp313")
    errors = check_wheels(
        [wheel],
        "manylinux_2_34_x86_64",
    )

    assert any("uses Python tag cp313, expected cp310" in error for error in errors)
    assert any("non-ABI3 tag cp313-cp313" in error for error in errors)


def test_missing_expected_platform(tmp_path: Path) -> None:
    wheel = touch_wheel(tmp_path)
    errors = check_wheels(
        [wheel],
        "manylinux_2_28_x86_64",
    )

    assert "does not match manylinux_2_28_x86_64" in errors[0]


def test_no_wheel_paths() -> None:
    assert check_wheels([], "manylinux_2_34_x86_64") == ["no wheel paths provided"]


def test_rejects_wrong_distribution_name(tmp_path: Path) -> None:
    wheel = touch_wheel(tmp_path, distribution="other_project")

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel.name} uses distribution other-project, expected oxipng-pybind"]


def test_rejects_wrong_version(tmp_path: Path) -> None:
    wheel = touch_wheel(tmp_path, version="10.1.0")

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel.name} uses version 10.1.0, expected 10.1.1.post1"]


def test_rejects_invalid_wheel_filename_format(tmp_path: Path) -> None:
    wheel = tmp_path / "not-a-wheel.whl"
    wheel.write_text("", encoding="utf-8")

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel.name} is not a valid wheel filename"]


def test_rejects_missing_wheel_file(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1.post1-cp310-abi3-manylinux_2_34_x86_64.whl"

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel} does not exist"]


def test_rejects_extra_wheel_artifacts(tmp_path: Path) -> None:
    wheel_a = touch_wheel(tmp_path)
    wheel_b = touch_wheel(tmp_path, platform="manylinux_2_34_aarch64")

    errors = check_wheels([wheel_a, wheel_b], "manylinux_2_34_*")

    assert errors == ["expected exactly 1 wheel, found 2"]

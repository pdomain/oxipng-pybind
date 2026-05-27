"""Tests for wheel tag validation."""

from pathlib import Path

from scripts.check_wheel_tags import check_wheels


def test_valid_abi3_linux_tag(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl"
    wheel.write_text("", encoding="utf-8")
    errors = check_wheels(
        [wheel],
        "manylinux_2_34_x86_64",
    )

    assert errors == []


def test_valid_abi3_macos_wildcard_tag(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-macosx_14_0_arm64.whl"
    wheel.write_text("", encoding="utf-8")
    errors = check_wheels(
        [wheel],
        "macosx_*_arm64",
    )

    assert errors == []


def test_invalid_cpython_specific_abi_tag(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp313-cp313-manylinux_2_34_x86_64.whl"
    wheel.write_text("", encoding="utf-8")
    errors = check_wheels(
        [wheel],
        "manylinux_2_34_x86_64",
    )

    assert any("uses Python tag cp313, expected cp311" in error for error in errors)
    assert any("non-ABI3 tag cp313-cp313" in error for error in errors)


def test_missing_expected_platform(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl"
    wheel.write_text("", encoding="utf-8")
    errors = check_wheels(
        [wheel],
        "manylinux_2_28_x86_64",
    )

    assert "does not match manylinux_2_28_x86_64" in errors[0]


def test_no_wheel_paths() -> None:
    assert check_wheels([], "manylinux_2_34_x86_64") == ["no wheel paths provided"]


def test_rejects_wrong_distribution_name(tmp_path: Path) -> None:
    wheel = tmp_path / "other_project-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl"
    wheel.write_text("", encoding="utf-8")

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel.name} uses distribution other-project, expected oxipng-pybind"]


def test_rejects_wrong_version(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.0-cp311-abi3-manylinux_2_34_x86_64.whl"
    wheel.write_text("", encoding="utf-8")

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel.name} uses version 10.1.0, expected 10.1.1"]


def test_rejects_missing_wheel_file(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl"

    errors = check_wheels([wheel], "manylinux_2_34_x86_64")

    assert errors == [f"{wheel} does not exist"]


def test_rejects_extra_wheel_artifacts(tmp_path: Path) -> None:
    wheel_a = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl"
    wheel_b = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_aarch64.whl"
    wheel_a.write_text("", encoding="utf-8")
    wheel_b.write_text("", encoding="utf-8")

    errors = check_wheels([wheel_a, wheel_b], "manylinux_2_34_*")

    assert errors == ["expected exactly 1 wheel, found 2"]

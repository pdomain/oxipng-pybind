"""Tests for wheel tag validation."""

from pathlib import Path

from scripts.check_wheel_tags import check_wheels


def test_valid_abi3_linux_tag() -> None:
    errors = check_wheels(
        [Path("oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl")],
        "manylinux_2_34_x86_64",
    )

    assert errors == []


def test_valid_abi3_macos_wildcard_tag() -> None:
    errors = check_wheels(
        [Path("oxipng_pybind-10.1.1-cp311-abi3-macosx_14_0_arm64.whl")],
        "macosx_*_arm64",
    )

    assert errors == []


def test_invalid_cpython_specific_abi_tag() -> None:
    errors = check_wheels(
        [Path("oxipng_pybind-10.1.1-cp313-cp313-manylinux_2_34_x86_64.whl")],
        "manylinux_2_34_x86_64",
    )

    assert any("uses Python tag cp313, expected cp311" in error for error in errors)
    assert any("non-ABI3 tag cp313-cp313" in error for error in errors)


def test_missing_expected_platform() -> None:
    errors = check_wheels(
        [Path("oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl")],
        "manylinux_2_28_x86_64",
    )

    assert "does not match manylinux_2_28_x86_64" in errors[0]


def test_no_wheel_paths() -> None:
    assert check_wheels([], "manylinux_2_34_x86_64") == ["no wheel paths provided"]

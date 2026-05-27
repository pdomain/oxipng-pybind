"""Tests for small command-line helper entry points."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts import (
    ai_filter_log,
    bump_upstream,
    check_wheel_tags,
    scan_upstream_surface,
    smoke_wheel,
)

if TYPE_CHECKING:
    import pytest


def test_smoke_wheel_main_exercises_installed_package() -> None:
    assert smoke_wheel.main(["--allow-editable"]) == 0


def test_check_wheel_tags_main_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_34_x86_64.whl"
    wheel.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_wheel_tags.py",
            "--expected-platform",
            "manylinux_2_34_x86_64",
            str(wheel),
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


def test_check_wheel_tags_rejects_wrong_python_tag(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp310-abi3-manylinux_2_28_x86_64.whl"
    wheel.write_text("", encoding="utf-8")

    errors = check_wheel_tags.check_wheels([wheel], "manylinux_2_28_x86_64", "cp311")

    assert errors == [f"{wheel.name} uses Python tag cp310, expected cp311"]


def test_check_wheel_tags_accepts_cp311_abi3(tmp_path: Path) -> None:
    wheel = tmp_path / "oxipng_pybind-10.1.1-cp311-abi3-manylinux_2_28_x86_64.whl"
    wheel.write_text("", encoding="utf-8")

    assert check_wheel_tags.check_wheels([wheel], "manylinux_2_28_x86_64", "cp311") == []


def test_script_security_ignores_are_line_scoped() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    bump_script = Path("scripts/bump_upstream.py").read_text(encoding="utf-8")

    assert '"scripts/*.py" = ["S310", "S603", "T201"]' not in pyproject
    assert "# noqa: S310" in bump_script
    assert "# noqa: S603" in bump_script


def test_third_party_notices_are_packaged() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    notices = Path("THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert 'license-files = ["LICENSE", "THIRD_PARTY_NOTICES.md"]' in pyproject
    for dependency in ("PyO3", "indexmap", "libdeflater", "zopfli", "rayon"):
        assert dependency in notices


def test_smoke_wheel_release_mode_has_no_editable_typing_fallback() -> None:
    source = Path("scripts/smoke_wheel.py").read_text(encoding="utf-8")

    assert "allow_editable" in source
    assert "oxipng_pybind.pth" in source
    assert 'if allow_editable and "oxipng_pybind.pth" in names:' in source


def test_python_314_classifier_matches_api_matrix() -> None:
    matrix = Path(".github/workflows/api-matrix.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    if '"3.14"' in matrix:
        assert '"Programming Language :: Python :: 3.14"' in pyproject


def test_api_surface_records_python_rowfilter_compatibility() -> None:
    manifest = Path("docs/api-surface/oxipng-10.1.1.toml").read_text(encoding="utf-8")

    assert "[python_compat.RowFilter.aliases]" in manifest
    assert (
        'brute = "Python facade compatibility alias; maps through FilterStrategy, not upstream RowFilter"'
        in manifest
    )


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


def test_normalize_version_removes_leading_v() -> None:
    assert bump_upstream.normalize_version("v10.1.2") == "10.1.2"


def test_issue_body_mentions_manual_surface_triage() -> None:
    body = bump_upstream.issue_body("10.1.2", "## report")

    assert "Upstream version: 10.1.2" in body
    assert "- [ ] expose now" in body
    assert "- [ ] defer and document" in body
    assert "- [ ] reject as intentionally unsupported" in body


def test_scan_upstream_surface_tracks_color_type_and_bit_depth(tmp_path: Path) -> None:
    upstream = tmp_path / "upstream"
    src = upstream / "src"
    (src / "deflate").mkdir(parents=True)
    (src / "options.rs").write_text("pub struct Options { pub force: bool }\n", encoding="utf-8")
    (src / "filters.rs").write_text(
        "pub enum FilterStrategy { MinSum }\npub enum RowFilter { None }\n",
        encoding="utf-8",
    )
    (src / "headers.rs").write_text("pub enum StripChunks { None }\n", encoding="utf-8")
    (src / "deflate/mod.rs").write_text("pub enum Deflater { Libdeflater }\n", encoding="utf-8")
    (src / "lib.rs").write_text(
        "pub fn optimize() {}\npub fn optimize_from_memory() {}\n",
        encoding="utf-8",
    )
    (src / "colors.rs").write_text(
        (
            "pub enum ColorType { Grayscale, RGB, NewColor }\n"
            "pub enum BitDepth { One = 1, Eight = 8, ThirtyTwo = 32 }\n"
        ),
        encoding="utf-8",
    )
    manifest = {
        "upstream_version": "test",
        "options": {"exposed": {"force": "Options.force"}},
        "functions": {"exposed": ["optimize", "optimize_from_memory"]},
        "enums": {
            "FilterStrategy": {"unexposed": {"MinSum": "known"}},
            "RowFilter": {"unexposed": {"None": "known"}},
            "StripChunks": {"unexposed": {"None": "known"}},
            "Deflater": {"unexposed": {"Libdeflater": "known"}},
            "ColorType": {"unexposed": {"Grayscale": "known", "RGB": "known"}},
            "BitDepth": {"unexposed": {"One": "known", "Eight": "known"}},
        },
    }

    surface = scan_upstream_surface.parse_upstream_surface(upstream)
    report = scan_upstream_surface.compare_surface(surface, manifest)

    assert report["enums"]["ColorType"]["new_upstream_variants"] == ["NewColor"]
    assert report["enums"]["BitDepth"]["new_upstream_variants"] == ["ThirtyTwo"]

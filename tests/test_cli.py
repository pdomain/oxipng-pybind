"""Command-line entry point tests."""

from pathlib import Path

import pytest

from oxipng.cli import main
from tests.helpers.png import assert_png_path, png_chunk_names


def test_cli_optimizes_files_in_place(png_path: Path) -> None:
    assert main(["-o", "max", "--strip", "all", str(png_path)]) == 0

    assert_png_path(png_path)
    assert b"tEXt" not in png_chunk_names(png_path.read_bytes())


def test_cli_writes_out_without_modifying_input(png_path: Path, tmp_path: Path) -> None:
    original = png_path.read_bytes()
    output = tmp_path / "out.png"

    assert main(["-Z", "-i", "0", "--out", str(output), str(png_path)]) == 0

    assert_png_path(output)
    assert png_path.read_bytes() == original


def test_cli_reports_failures_and_keeps_going(
    png_path: Path,
    corrupt_png_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([str(corrupt_png_path), str(png_path)]) == 1

    assert str(corrupt_png_path) in capsys.readouterr().err
    assert_png_path(png_path)


@pytest.mark.parametrize("args", [["-o", "7", "a.png"], ["--out", "o.png", "a.png", "b.png"]])
def test_cli_rejects_invalid_arguments(args: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 2

"""Tests for upstream surface scanning."""

import json
from pathlib import Path

from scripts.scan_upstream_surface import (
    compare_surface,
    parse_enum_variants,
    parse_public_functions,
    parse_struct_fields,
    parse_upstream_surface,
    write_outputs,
)


def test_parse_struct_fields() -> None:
    source = """
pub struct Options {
    pub fix_errors: bool,
    pub force: bool,
}
"""

    assert parse_struct_fields(source, "Options") == ["fix_errors", "force"]


def test_parse_multiline_enum_variants() -> None:
    source = """
pub enum FilterStrategy {
    Basic(RowFilter),
    Brute {
        num_lines: usize,
        level: u8,
    },
    Predefined(Vec<RowFilter>),
}
"""

    assert parse_enum_variants(source, "FilterStrategy") == [
        "Basic",
        "Brute",
        "Predefined",
    ]


def test_parse_enum_with_attributes() -> None:
    source = """
#[cfg(feature = "zopfli")]
pub enum Deflater {
    Libdeflater { compression: u8 },
    #[cfg(feature = "zopfli")]
    Zopfli(ZopfliOptions),
}
"""

    assert parse_enum_variants(source, "Deflater") == ["Libdeflater", "Zopfli"]


def test_parse_public_functions() -> None:
    source = """
pub fn optimize_from_memory(data: &[u8], opts: &Options) -> PngResult<Vec<u8>> {
    todo!()
}
"""

    assert parse_public_functions(source) == ["optimize_from_memory"]


def test_parse_upstream_surface_from_fixture_tree(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "deflate").mkdir(parents=True)
    (src / "options.rs").write_text(
        "pub struct Options { pub fix_errors: bool, pub force: bool, }",
        encoding="utf-8",
    )
    (src / "filters.rs").write_text(
        "\n".join(
            [
                "pub enum FilterStrategy { Basic(RowFilter), Predefined(Vec<RowFilter>), }",
                "pub enum RowFilter { None, Sub, }",
            ]
        ),
        encoding="utf-8",
    )
    (src / "headers.rs").write_text(
        "pub enum StripChunks { None, Strip(IndexSet<[u8; 4]>), Safe, Keep(IndexSet<[u8; 4]>), All, }",
        encoding="utf-8",
    )
    (src / "colors.rs").write_text(
        "pub enum ColorType { Grayscale, RGB, Indexed, GrayscaleAlpha, RGBA }\n"
        "pub enum BitDepth { One = 1, Two = 2, Four = 4, Eight = 8, Sixteen = 16 }\n",
        encoding="utf-8",
    )
    (src / "deflate/mod.rs").write_text(
        "pub enum Deflater { Libdeflater { compression: u8 }, Zopfli(ZopfliOptions), }",
        encoding="utf-8",
    )
    (src / "lib.rs").write_text(
        """
pub fn optimize() {}

pub fn optimize_from_memory(data: &[u8], opts: &Options) -> PngResult<Vec<u8>> {
    todo!()
}
""".lstrip(),
        encoding="utf-8",
    )

    surface = parse_upstream_surface(tmp_path)

    assert surface.options_fields == ["fix_errors"]
    assert surface.enums["ColorType"] == ["Grayscale", "RGB", "Indexed", "GrayscaleAlpha", "RGBA"]
    assert surface.enums["BitDepth"] == ["One", "Two", "Four", "Eight", "Sixteen"]
    assert "optimize_from_memory" in surface.functions


def test_compare_surface_reports_new_and_removed_items() -> None:
    manifest = {
        "upstream_version": "10.1.1",
        "functions": {"exposed": ["optimize", "optimize_from_memory"]},
        "options": {
            "exposed": {"fix_errors": "Options.fix_errors", "missing": "Options.missing"},
            "unexposed": {},
        },
        "enums": {"Deflater": {"exposed": {"Libdeflater": "Deflater::Libdeflater"}}},
    }
    surface = parse_upstream_surface(Path(".cache/upstream/oxipng"))
    report = compare_surface(surface, manifest)

    assert "missing" in report["removed_exposed_options"]
    assert report["blocking"] is True


def test_write_outputs_are_deterministic(tmp_path: Path) -> None:
    report: dict[str, object] = {
        "upstream_version": "10.1.1",
        "new_upstream_options": [],
        "removed_exposed_options": [],
        "missing_expected_functions": [],
        "manifest_options_not_found": [],
        "enums": {},
        "blocking": False,
    }

    write_outputs(report, tmp_path)

    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))["blocking"] is False
    assert "No upstream surface changes" in (tmp_path / "pr-body-section.md").read_text(
        encoding="utf-8"
    )

"""Tests for upstream surface scanning."""

import json
from pathlib import Path

import pytest

from scripts.scan_upstream_surface import (
    UpstreamSurface,
    append_generated_docs,
    compare_surface,
    current_manifest_path,
    extract_block,
    has_new_unexposed,
    parse_enum_variants,
    parse_public_functions,
    parse_struct_fields,
    parse_upstream_surface,
    pr_body,
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


def test_parse_struct_fields_finds_multiple_fields_on_one_line() -> None:
    source = "pub struct Options { pub fix_errors: bool, pub force: bool, }"

    assert parse_struct_fields(source, "Options") == ["fix_errors", "force"]


def test_parse_struct_fields_requires_public_fields() -> None:
    source = "pub struct Options { force: bool }"

    with pytest.raises(ValueError, match="no public fields found for Options"):
        parse_struct_fields(source, "Options")


def test_extract_block_reports_missing_and_unterminated_declarations() -> None:
    with pytest.raises(ValueError, match=r"required declaration not found"):
        extract_block("pub struct Other {}", r"pub\s+struct\s+Options")

    with pytest.raises(ValueError, match=r"unterminated declaration"):
        extract_block("pub struct Options { pub force: bool", r"pub\s+struct\s+Options")


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


def test_parse_enum_variants_requires_variants() -> None:
    source = "pub enum Deflater { value, another_value }"

    with pytest.raises(ValueError, match="no variants found for Deflater"):
        parse_enum_variants(source, "Deflater")


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
        "\n".join(
            [
                "pub enum ColorType { Grayscale, RGB, Indexed, GrayscaleAlpha, RGBA }",
                "pub enum BitDepth { One = 1, Two = 2, Four = 4, Eight = 8, Sixteen = 16 }",
            ]
        ),
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

    assert surface.options_fields == ["fix_errors", "force"]
    assert surface.enums["ColorType"] == ["Grayscale", "RGB", "Indexed", "GrayscaleAlpha", "RGBA"]
    assert surface.enums["BitDepth"] == ["One", "Two", "Four", "Eight", "Sixteen"]
    assert "optimize_from_memory" in surface.functions


def test_parse_upstream_surface_requires_checkout_and_public_api(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="upstream checkout not found"):
        parse_upstream_surface(tmp_path / "missing")

    src = tmp_path / "src"
    (src / "deflate").mkdir(parents=True)
    (src / "options.rs").write_text("pub struct Options { pub force: bool }", encoding="utf-8")
    (src / "filters.rs").write_text(
        "pub enum FilterStrategy { MinSum }\npub enum RowFilter { None }\n",
        encoding="utf-8",
    )
    (src / "headers.rs").write_text("pub enum StripChunks { None }\n", encoding="utf-8")
    (src / "colors.rs").write_text(
        "pub enum ColorType { RGB }\npub enum BitDepth { Eight = 8 }\n",
        encoding="utf-8",
    )
    (src / "deflate/mod.rs").write_text("pub enum Deflater { Libdeflater }\n", encoding="utf-8")
    (src / "lib.rs").write_text("pub fn optimize() {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="required function not found: optimize_from_memory"):
        parse_upstream_surface(tmp_path)


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
    surface = UpstreamSurface(
        options_fields=["fix_errors"],
        enums={"Deflater": ["Libdeflater"]},
        functions=["optimize", "optimize_from_memory"],
    )
    report = compare_surface(surface, manifest)

    assert "missing" in report["removed_exposed_options"]
    assert report["blocking"] is True


def test_compare_surface_handles_malformed_manifest_tables() -> None:
    surface = UpstreamSurface(
        options_fields=["force"],
        enums={"Deflater": ["Libdeflater"]},
        functions=["optimize"],
    )
    manifest: dict[str, object] = {
        "upstream_version": "test",
        "functions": {"exposed": ["optimize", "missing"]},
        "options": {"exposed": [], "unexposed": []},
        "enums": {"Deflater": {"exposed": [], "unexposed": []}},
    }

    report = compare_surface(surface, manifest)

    assert report["new_upstream_options"] == ["force"]
    assert report["missing_expected_functions"] == ["missing"]
    assert report["enums"]["Deflater"]["new_upstream_variants"] == ["Libdeflater"]
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


def test_pr_body_distinguishes_blocking_and_new_unexposed_surface() -> None:
    blocking_report: dict[str, object] = {
        "upstream_version": "10.1.1",
        "new_upstream_options": [],
        "enums": {},
        "blocking": True,
    }
    new_unexposed_report: dict[str, object] = {
        "upstream_version": "10.1.1",
        "new_upstream_options": ["force"],
        "enums": {"Deflater": {"new_upstream_variants": []}},
        "blocking": False,
    }

    assert has_new_unexposed(blocking_report) is False
    assert "Blocking exposed-surface changes" in pr_body(blocking_report)
    assert has_new_unexposed(new_unexposed_report) is True
    assert "documented as unexposed" in pr_body(new_unexposed_report)


def test_append_generated_docs_updates_docs_once(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "architecture"
    docs.mkdir(parents=True)
    for name in ("api-compatibility.md", "options-surface.md"):
        (docs / name).write_text(f"# {name}\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Unreleased\n", encoding="utf-8")
    report: dict[str, object] = {
        "upstream_version": "10.2.0",
        "new_upstream_options": ["force"],
        "enums": {"Deflater": {"new_upstream_variants": ["Zopfli"]}},
        "blocking": False,
    }

    append_generated_docs(report, tmp_path)
    append_generated_docs(report, tmp_path)

    api_text = (docs / "api-compatibility.md").read_text(encoding="utf-8")
    options_text = (docs / "options-surface.md").read_text(encoding="utf-8")
    changelog_text = changelog.read_text(encoding="utf-8")
    assert api_text.count("### oxipng 10.2.0") == 1
    assert options_text.count("`Deflater::Zopfli`") == 1
    assert changelog_text.count("Documented new unexposed upstream surface") == 1


def test_append_generated_docs_skips_when_report_has_no_new_surface(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "architecture"
    docs.mkdir(parents=True)
    api = docs / "api-compatibility.md"
    api.write_text("# API\n", encoding="utf-8")
    options = docs / "options-surface.md"
    options.write_text("# Options\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Unreleased\n", encoding="utf-8")
    report: dict[str, object] = {
        "upstream_version": "10.2.0",
        "new_upstream_options": [],
        "enums": {},
        "blocking": False,
    }

    append_generated_docs(report, tmp_path)

    assert api.read_text(encoding="utf-8") == "# API\n"
    assert options.read_text(encoding="utf-8") == "# Options\n"
    assert changelog.read_text(encoding="utf-8") == "# Changelog\n\n## Unreleased\n"


def test_current_manifest_path_uses_pinned_oxipng_version(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text(
        '[dependencies]\noxi = { package = "oxipng", version = "=10.1.1" }\n',
        encoding="utf-8",
    )

    assert current_manifest_path(tmp_path) == tmp_path / "docs/api-surface/oxipng-10.1.1.toml"

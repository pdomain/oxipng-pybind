"""Tests for upstream surface scanning."""

import json
import subprocess
from pathlib import Path
from typing import cast

import pytest

from scripts.scan_upstream_surface import (
    UpstreamSurface,
    append_generated_docs,
    compare_surface,
    current_manifest_path,
    has_new_unexposed,
    load_rustdoc_json,
    parse_upstream_surface,
    pr_body,
    public_items_from_rustdoc_json,
    rustdoc_json_command,
    write_outputs,
)


def rustdoc_fixture() -> dict[str, object]:
    return {
        "root": 0,
        "index": {
            "0": {
                "name": "oxipng",
                "visibility": "public",
                "inner": {"module": {"items": [1, 2, 3, 4, 5, 6, 18]}},
            },
            "1": {
                "name": "optimize",
                "visibility": "public",
                "inner": {"function": {"header": {"is_const": False, "is_async": False}}},
            },
            "2": {
                "name": "default_options",
                "visibility": "public",
                "inner": {"function": {"header": {"is_const": True, "is_async": False}}},
            },
            "3": {
                "name": "optimize_async",
                "visibility": "public",
                "inner": {"function": {"header": {"is_const": False, "is_async": True}}},
            },
            "4": {
                "name": "private_fn",
                "visibility": "default",
                "inner": {"function": {"header": {"is_const": False, "is_async": False}}},
            },
            "5": {
                "name": "crate_fn",
                "visibility": {"restricted": {"parent": 0, "path": "crate"}},
                "inner": {"function": {"header": {"is_const": False, "is_async": False}}},
            },
            "6": {
                "name": "Options",
                "visibility": "public",
                "inner": {"struct": {"kind": {"plain": {"fields": [7, 8]}}}},
            },
            "7": {"name": "fix_errors", "visibility": "public", "inner": {"struct_field": []}},
            "8": {
                "name": "private_field",
                "visibility": "default",
                "inner": {"struct_field": []},
            },
            "9": {
                "name": "FilterStrategy",
                "visibility": "public",
                "inner": {"enum": {"variants": [10, 11]}},
            },
            "10": {
                "name": "Basic",
                "visibility": "public",
                "inner": {"variant": {"kind": "plain"}},
            },
            "11": {
                "name": "Predefined",
                "visibility": "public",
                "inner": {"variant": {"kind": "tuple"}},
            },
            "12": {
                "name": "ColorType",
                "visibility": "public",
                "inner": {"enum": {"variants": [13]}},
            },
            "13": {
                "name": "RGB",
                "visibility": "public",
                "inner": {"variant": {"kind": "plain"}},
            },
            "14": {
                "name": "MAX_IDAT_SIZE",
                "visibility": "public",
                "inner": {"constant": {"type": "usize"}},
            },
            "15": {
                "name": "VERSION",
                "visibility": "public",
                "inner": {"static": {"type": "&'static str"}},
            },
            "16": {
                "name": "Optimizer",
                "visibility": "public",
                "inner": {"type_alias": {"type": "Options"}},
            },
            "17": {"name": "RowLike", "visibility": "public", "inner": {"trait": {}}},
            "18": {
                "name": "optimize_from_memory",
                "visibility": "public",
                "inner": {"function": {"header": {"is_const": False, "is_async": False}}},
            },
        },
    }


def test_public_items_from_rustdoc_json_classifies_public_surface() -> None:
    surface = public_items_from_rustdoc_json(rustdoc_fixture())

    assert surface.options_fields == ["fix_errors"]
    assert surface.enums["FilterStrategy"] == ["Basic", "Predefined"]
    assert surface.enums["ColorType"] == ["RGB"]
    assert surface.functions == [
        "default_options",
        "optimize",
        "optimize_async",
        "optimize_from_memory",
    ]
    assert surface.types == ["ColorType", "FilterStrategy", "Optimizer", "Options", "RowLike"]
    assert surface.constants == ["MAX_IDAT_SIZE", "VERSION"]
    assert "private_fn" not in surface.functions
    assert "crate_fn" not in surface.functions


def test_rustdoc_json_command_uses_nightly_rustdoc_json_flags(tmp_path: Path) -> None:
    command = rustdoc_json_command(tmp_path)

    assert command[:4] == ["rustup", "run", "nightly", "cargo"]
    assert command[4:6] == ["rustdoc", "--lib"]
    assert "--no-deps" not in command
    assert command[-4:] == ["--", "-Z", "unstable-options", "--output-format=json"]
    assert command[command.index("--manifest-path") + 1] == str(tmp_path / "Cargo.toml")


def test_load_rustdoc_json_runs_command_and_loads_crate_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "oxipng"\n', encoding="utf-8")
    doc_dir = tmp_path / "target" / "doc"
    doc_dir.mkdir(parents=True)
    expected: dict[str, object] = {"index": {}}
    (doc_dir / "oxipng.json").write_text(json.dumps(expected), encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path, check: bool) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert cwd == tmp_path
        assert check is True
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert load_rustdoc_json(tmp_path) == expected
    assert calls == [rustdoc_json_command(tmp_path)]


def test_parse_upstream_surface_uses_rustdoc_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_load(crate_dir: Path) -> dict[str, object]:
        assert crate_dir == tmp_path
        return rustdoc_fixture()

    monkeypatch.setattr("scripts.scan_upstream_surface.load_rustdoc_json", fake_load)

    surface = parse_upstream_surface(tmp_path)

    assert surface.options_fields == ["fix_errors"]
    assert "optimize" in surface.functions


def test_parse_upstream_surface_requires_checkout_and_public_api(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(FileNotFoundError, match="upstream checkout not found"):
        parse_upstream_surface(tmp_path / "missing")

    tmp_path.mkdir(exist_ok=True)

    def fake_load(_crate_dir: Path) -> dict[str, object]:
        fixture = rustdoc_fixture()
        index = cast("dict[str, object]", fixture["index"])
        del index["1"]
        return fixture

    monkeypatch.setattr("scripts.scan_upstream_surface.load_rustdoc_json", fake_load)

    with pytest.raises(ValueError, match="required function not found: optimize"):
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
    assert api_text.count("### oxipng 10.2.0") == 1
    assert options_text.count("`Deflater::Zopfli`") == 1
    assert not (tmp_path / "CHANGELOG.md").exists()


def test_append_generated_docs_updates_existing_changelog_once(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "architecture"
    docs.mkdir(parents=True)
    for name in ("api-compatibility.md", "options-surface.md"):
        (docs / name).write_text(f"# {name}\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Unreleased\n", encoding="utf-8")
    report: dict[str, object] = {
        "upstream_version": "10.2.0",
        "new_upstream_options": ["force"],
        "enums": {"Deflater": {"new_upstream_variants": []}},
        "blocking": False,
    }

    append_generated_docs(report, tmp_path)
    append_generated_docs(report, tmp_path)

    changelog_text = changelog.read_text(encoding="utf-8")
    assert changelog_text.count("Documented new unexposed upstream surface") == 1


def test_append_generated_docs_skips_when_report_has_no_new_surface(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "architecture"
    docs.mkdir(parents=True)
    api = docs / "api-compatibility.md"
    api.write_text("# API\n", encoding="utf-8")
    options = docs / "options-surface.md"
    options.write_text("# Options\n", encoding="utf-8")
    report: dict[str, object] = {
        "upstream_version": "10.2.0",
        "new_upstream_options": [],
        "enums": {},
        "blocking": False,
    }

    append_generated_docs(report, tmp_path)

    assert api.read_text(encoding="utf-8") == "# API\n"
    assert options.read_text(encoding="utf-8") == "# Options\n"
    assert not (tmp_path / "CHANGELOG.md").exists()


def test_current_manifest_path_uses_pinned_oxipng_version(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text(
        '[dependencies]\noxi = { package = "oxipng", version = "=10.1.1" }\n',
        encoding="utf-8",
    )

    assert current_manifest_path(tmp_path) == tmp_path / "docs/api-surface/oxipng-10.1.1.toml"

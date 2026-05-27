#!/usr/bin/env python3
# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false
"""Scan upstream oxipng Rust surface against the wrapper manifest."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import tomlkit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPSTREAM = ROOT / ".cache/upstream/oxipng"
OUTPUT_DIR = ROOT / ".cache/upstream-surface"


@dataclass(frozen=True)
class UpstreamSurface:
    """Relevant upstream declarations."""

    options_fields: list[str]
    enums: dict[str, list[str]]
    functions: list[str]


def _strip_attributes(lines: list[str]) -> list[str]:
    return [line for line in lines if not line.strip().startswith("#[")]


def extract_block(source: str, declaration: str) -> str:
    """Extract a braced Rust declaration body."""
    match = re.search(declaration + r"\s*\{", source)
    if match is None:
        raise ValueError(f"required declaration not found: {declaration}")
    start = match.end()
    depth = 1
    index = start
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    if depth:
        raise ValueError(f"unterminated declaration: {declaration}")
    return source[start : index - 1]


def parse_struct_fields(source: str, name: str) -> list[str]:
    """Parse public field names from a Rust struct."""
    block = extract_block(source, rf"pub\s+struct\s+{name}")
    fields: list[str] = []
    for line in _strip_attributes(block.splitlines()):
        fields.extend(re.findall(r"\bpub\s+([A-Za-z_][A-Za-z0-9_]*)\s*:", line))
    if not fields:
        raise ValueError(f"no public fields found for {name}")
    return fields


def parse_enum_variants(source: str, name: str) -> list[str]:
    """Parse public enum variant names from a Rust enum."""
    block = extract_block(source, rf"pub\s+enum\s+{name}")
    text = "\n".join(
        line.split("//", 1)[0].strip()
        for line in _strip_attributes(block.splitlines())
        if line.split("//", 1)[0].strip() and not line.split("//", 1)[0].strip().startswith("///")
    )
    chunks: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "{(<[":
            depth += 1
        elif char in "})>]":
            depth -= 1
        elif char == "," and depth == 0:
            chunks.append(text[start:index])
            start = index + 1
    chunks.append(text[start:])

    variants: list[str] = []
    for chunk in chunks:
        match = re.match(r"\s*([A-Z][A-Za-z0-9_]*)", chunk)
        if match:
            variants.append(match.group(1))
    if not variants:
        raise ValueError(f"no variants found for {name}")
    return variants


def parse_public_functions(source: str) -> list[str]:
    """Parse public function names."""
    return re.findall(r"(?m)^\s*pub\s+fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source)


def parse_upstream_surface(upstream: Path) -> UpstreamSurface:
    """Parse relevant upstream files."""
    if not upstream.exists():
        raise FileNotFoundError(f"upstream checkout not found: {upstream}")
    src = upstream / "src"
    options_rs = (src / "options.rs").read_text(encoding="utf-8")
    filters_rs = (src / "filters.rs").read_text(encoding="utf-8")
    headers_rs = (src / "headers.rs").read_text(encoding="utf-8")
    colors_rs = (src / "colors.rs").read_text(encoding="utf-8")
    deflater_rs = (src / "deflate/mod.rs").read_text(encoding="utf-8")
    lib_rs = (src / "lib.rs").read_text(encoding="utf-8")

    functions = parse_public_functions(lib_rs)
    for required in ("optimize", "optimize_from_memory"):
        if required not in functions:
            raise ValueError(f"required function not found: {required}")

    return UpstreamSurface(
        options_fields=parse_struct_fields(options_rs, "Options"),
        enums={
            "FilterStrategy": parse_enum_variants(filters_rs, "FilterStrategy"),
            "RowFilter": parse_enum_variants(filters_rs, "RowFilter"),
            "StripChunks": parse_enum_variants(headers_rs, "StripChunks"),
            "Deflater": parse_enum_variants(deflater_rs, "Deflater"),
            "ColorType": parse_enum_variants(colors_rs, "ColorType"),
            "BitDepth": parse_enum_variants(colors_rs, "BitDepth"),
        },
        functions=functions,
    )


def _table_keys(table: object) -> set[str]:
    return set(table.keys()) if isinstance(table, dict) else set()


def _mapped_upstream_variants(table: object) -> set[str]:
    if not isinstance(table, dict):
        return set()
    variants: set[str] = set()
    for value in table.values():
        text = str(value)
        match = re.search(r"::([A-Z][A-Za-z0-9_]*)", text)
        if match:
            variants.add(match.group(1))
    return variants


def _mapped_option_fields(table: object) -> set[str]:
    if not isinstance(table, dict):
        return set()
    fields: set[str] = set()
    for value in table.values():
        match = re.search(r"Options\.([A-Za-z_][A-Za-z0-9_]*)", str(value))
        if match:
            fields.add(match.group(1))
    return fields


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a TOML manifest."""
    return cast("dict[str, Any]", tomlkit.parse(path.read_text(encoding="utf-8")))


def compare_surface(surface: UpstreamSurface, manifest: dict[str, Any]) -> dict[str, Any]:
    """Compare parsed upstream surface with the wrapper manifest."""
    exposed_options = _mapped_option_fields(manifest.get("options", {}).get("exposed", {}))
    unexposed_options = _table_keys(manifest.get("options", {}).get("unexposed", {}))
    known_options = exposed_options | unexposed_options

    enum_report: dict[str, dict[str, list[str]]] = {}
    manifest_enums = manifest.get("enums", {})
    for enum_name, upstream_variants in surface.enums.items():
        manifest_enum = manifest_enums.get(enum_name, {})
        exposed = _mapped_upstream_variants(manifest_enum.get("exposed", {}))
        unexposed = _table_keys(manifest_enum.get("unexposed", {}))
        known = exposed | unexposed
        enum_report[enum_name] = {
            "new_upstream_variants": sorted(set(upstream_variants) - known),
            "removed_exposed_variants": sorted(exposed - set(upstream_variants)),
            "manifest_entries_not_found": sorted(known - set(upstream_variants)),
        }

    exposed_functions = set(manifest.get("functions", {}).get("exposed", []))

    return {
        "upstream_version": manifest.get("upstream_version"),
        "new_upstream_options": sorted(set(surface.options_fields) - known_options),
        "removed_exposed_options": sorted(exposed_options - set(surface.options_fields)),
        "missing_expected_functions": sorted(exposed_functions - set(surface.functions)),
        "manifest_options_not_found": sorted(known_options - set(surface.options_fields)),
        "enums": enum_report,
        "blocking": bool(
            exposed_options - set(surface.options_fields)
            or exposed_functions - set(surface.functions)
            or any(item["removed_exposed_variants"] for item in enum_report.values())
        ),
    }


def current_manifest_path(root: Path = ROOT) -> Path:
    """Return the manifest path for the pinned upstream version."""
    cargo = cast("dict[str, Any]", tomlkit.parse((root / "Cargo.toml").read_text(encoding="utf-8")))
    version = str(cargo["dependencies"]["oxi"]["version"]).lstrip("=")
    return root / "docs/api-surface" / f"oxipng-{version}.toml"


def pr_body(report: dict[str, Any]) -> str:
    """Render a concise PR body section."""
    lines = ["## Upstream Surface Scan", ""]
    if report["blocking"]:
        lines.append("Blocking exposed-surface changes were detected.")
    elif has_new_unexposed(report):
        lines.append("New upstream surface is documented as unexposed for triage.")
    else:
        lines.append("No upstream surface changes were detected.")
    lines.append("")
    lines.append(f"Upstream version: {report['upstream_version']}")
    return "\n".join(lines) + "\n"


def has_new_unexposed(report: dict[str, Any]) -> bool:
    """Return whether the report has new upstream items."""
    return bool(report["new_upstream_options"]) or any(
        values["new_upstream_variants"] for values in report["enums"].values()
    )


def append_generated_docs(report: dict[str, Any], root: Path = ROOT) -> None:
    """Append generated unexposed-surface notes to docs and changelog."""
    if not has_new_unexposed(report):
        return

    version = report["upstream_version"]
    lines = [f"\n### oxipng {version}\n"]
    lines.extend(f"- `Options.{option}`\n" for option in report["new_upstream_options"])
    for enum_name, enum_report in report["enums"].items():
        lines.extend(
            f"- `{enum_name}::{variant}`\n" for variant in enum_report["new_upstream_variants"]
        )
    addition = "".join(lines)

    for relative in (
        "docs/architecture/api-compatibility.md",
        "docs/architecture/options-surface.md",
    ):
        path = root / relative
        text = path.read_text(encoding="utf-8")
        if f"### oxipng {version}" not in text:
            path.write_text(text.rstrip() + "\n" + addition, encoding="utf-8")

    changelog = root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    marker = "## Unreleased\n"
    note = f"- Documented new unexposed upstream surface for oxipng {version}.\n"
    if note not in text:
        text = text.replace(marker, marker + "\n" + note, 1)
        changelog.write_text(text, encoding="utf-8")


def write_outputs(report: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> None:
    """Write deterministic scan outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "pr-body-section.md").write_text(pr_body(report), encoding="utf-8")


def main() -> int:
    """Run the upstream surface scanner."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--update-docs", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest or current_manifest_path()
    surface = parse_upstream_surface(args.upstream)
    report = compare_surface(surface, load_manifest(manifest_path))
    write_outputs(report)
    if args.update_docs:
        append_generated_docs(report)
    return 1 if report["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

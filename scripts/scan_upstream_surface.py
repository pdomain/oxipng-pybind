#!/usr/bin/env python3
# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false
"""Scan upstream oxipng Rust surface against the wrapper manifest."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
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
    types: list[str] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)


def _crate_name(crate_dir: Path) -> str:
    cargo = cast(
        "dict[str, Any]", tomlkit.parse((crate_dir / "Cargo.toml").read_text(encoding="utf-8"))
    )
    package = cargo.get("package", {})
    if not isinstance(package, dict):
        raise TypeError(f"package metadata not found: {crate_dir / 'Cargo.toml'}")
    return str(package["name"]).replace("-", "_")


def rustdoc_json_command(crate_dir: Path) -> list[str]:
    """Build the rustdoc JSON command for an upstream crate."""
    return [
        "rustup",
        "run",
        "nightly",
        "cargo",
        "rustdoc",
        "--lib",
        "--manifest-path",
        str(crate_dir / "Cargo.toml"),
        "--",
        "-Z",
        "unstable-options",
        "--output-format=json",
    ]


def load_rustdoc_json(crate_dir: Path) -> dict[str, object]:
    """Generate and load upstream rustdoc JSON."""
    subprocess.run(rustdoc_json_command(crate_dir), cwd=crate_dir, check=True)  # noqa: S603 - fixed rustdoc command with crate path argument.
    path = crate_dir / "target" / "doc" / f"{_crate_name(crate_dir)}.json"
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


def _index(document: Mapping[str, object]) -> Mapping[str, object]:
    index = document.get("index")
    if not isinstance(index, Mapping):
        raise TypeError("rustdoc JSON index not found")
    return cast("Mapping[str, object]", index)


def _item_mapping(index: Mapping[str, object], item_id: object) -> Mapping[str, object] | None:
    item = index.get(str(item_id))
    return cast("Mapping[str, object]", item) if isinstance(item, Mapping) else None


def _inner(item: Mapping[str, object]) -> Mapping[str, object]:
    inner = item.get("inner")
    return cast("Mapping[str, object]", inner) if isinstance(inner, Mapping) else {}


def _name(item: Mapping[str, object]) -> str | None:
    name = item.get("name")
    return name if isinstance(name, str) else None


def _is_public(item: Mapping[str, object]) -> bool:
    return item.get("visibility") == "public"


def _item_id_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str | int)]


def _public_struct_fields(
    index: Mapping[str, object], struct_item: Mapping[str, object]
) -> list[str]:
    struct = _inner(struct_item).get("struct")
    if not isinstance(struct, Mapping):
        return []
    struct = cast("Mapping[str, object]", struct)
    kind = struct.get("kind")
    if not isinstance(kind, Mapping):
        return []
    kind = cast("Mapping[str, object]", kind)
    plain = kind.get("plain")
    if not isinstance(plain, Mapping):
        return []
    plain = cast("Mapping[str, object]", plain)
    fields = _item_id_list(plain.get("fields"))
    names: list[str] = []
    for field_id in fields:
        field_item = _item_mapping(index, field_id)
        if field_item is None or not _is_public(field_item):
            continue
        name = _name(field_item)
        if name is not None:
            names.append(name)
    return sorted(names)


def _enum_variants(index: Mapping[str, object], enum_item: Mapping[str, object]) -> list[str]:
    enum = _inner(enum_item).get("enum")
    if not isinstance(enum, Mapping):
        return []
    enum = cast("Mapping[str, object]", enum)
    names: list[str] = []
    for variant_id in _item_id_list(enum.get("variants")):
        variant_item = _item_mapping(index, variant_id)
        if variant_item is None:
            continue
        name = _name(variant_item)
        if name is not None:
            names.append(name)
    return names


def public_items_from_rustdoc_json(document: Mapping[str, object]) -> UpstreamSurface:
    """Extract public surface from rustdoc JSON metadata."""
    index = _index(document)
    functions: list[str] = []
    types: list[str] = []
    constants: list[str] = []
    enums: dict[str, list[str]] = {}
    options_fields: list[str] = []

    for item in index.values():
        if not isinstance(item, Mapping) or not _is_public(item):
            continue
        name = _name(item)
        if name is None:
            continue
        inner = _inner(item)
        if "function" in inner:
            functions.append(name)
        elif "struct" in inner:
            types.append(name)
            if name == "Options":
                options_fields = _public_struct_fields(index, item)
        elif "enum" in inner:
            types.append(name)
            enums[name] = _enum_variants(index, item)
        elif "union" in inner or "trait" in inner or "type_alias" in inner:
            types.append(name)
        elif "constant" in inner or "static" in inner:
            constants.append(name)

    return UpstreamSurface(
        options_fields=sorted(options_fields),
        enums={name: enums[name] for name in sorted(enums)},
        functions=sorted(functions),
        types=sorted(types),
        constants=sorted(constants),
    )


def parse_upstream_surface(upstream: Path) -> UpstreamSurface:
    """Load relevant upstream surface from rustdoc JSON."""
    if not upstream.exists():
        raise FileNotFoundError(f"upstream checkout not found: {upstream}")
    surface = public_items_from_rustdoc_json(load_rustdoc_json(upstream))
    for required in ("optimize", "optimize_from_memory"):
        if required not in surface.functions:
            raise ValueError(f"required function not found: {required}")
    return surface


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
    """Append generated unexposed-surface notes to active docs."""
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
    if changelog.exists():
        text = changelog.read_text(encoding="utf-8")
        marker = "## Unreleased\n"
        note = f"- Documented new unexposed upstream surface for oxipng {version}.\n"
        if marker in text and note not in text:
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

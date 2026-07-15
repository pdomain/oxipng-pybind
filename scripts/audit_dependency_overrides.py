#!/usr/bin/env python3
"""Flag dependency overrides that are no longer required.

`[tool.uv] override-dependencies` in `pyproject.toml` forces a transitive
dependency past the version its parents request, usually to clear an advisory.
An override can outlive its reason: once the natural resolution already meets
the override's floor, the override is dead weight and should be removed.

This audit re-resolves the project *without* its overrides in an isolated
virtual project, then compares each override against that natural resolution.
It exits non-zero when any override is removable so the weekly dependency
refresh surfaces it for cleanup. See `docs/process/dependency-health.md`.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import tomlkit
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
sys_path = os.fspath(ROOT)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from scripts._toml_compat import loads  # noqa: E402 - direct script execution needs repo root.

if TYPE_CHECKING:
    from collections.abc import Mapping

PYPROJECT_PATH = ROOT / "pyproject.toml"

# Resolve a probe project's lockfile from its pyproject text. Injected in tests.
ProbeResolver = Callable[[str], str]


@dataclass(frozen=True)
class Override:
    """One parsed `override-dependencies` entry."""

    name: str
    requirement: Requirement

    @property
    def canonical_name(self) -> str:
        """Return the PEP 503 normalized distribution name."""
        return canonicalize_name(self.name)


@dataclass(frozen=True)
class Finding:
    """A removable override and the reason it is no longer required."""

    name: str
    reason: str


def parse_overrides(pyproject_text: str) -> list[Override]:
    """Parse `[tool.uv] override-dependencies` requirement strings."""
    tool = loads(pyproject_text).get("tool")
    if not isinstance(tool, dict):
        return []
    uv_section = cast("dict[str, Any]", tool).get("uv")
    if not isinstance(uv_section, dict):
        return []
    raw = cast("dict[str, Any]", uv_section).get("override-dependencies")
    if not isinstance(raw, list):
        return []
    overrides: list[Override] = []
    for entry in cast("list[Any]", raw):
        if isinstance(entry, str):
            requirement = Requirement(entry)
            overrides.append(Override(name=requirement.name, requirement=requirement))
    return overrides


def build_probe_pyproject(pyproject_text: str) -> str:
    """Return probe `pyproject.toml` text: overrides stripped, root un-packaged.

    Dropping `override-dependencies` shows the natural resolution, and marking
    the root a virtual (non-packaged) project avoids a native build just to
    resolve dependencies.
    """
    document = tomlkit.parse(pyproject_text)
    tool = document.setdefault("tool", tomlkit.table())
    uv_table = tool.setdefault("uv", tomlkit.table())
    uv_table.pop("override-dependencies", None)
    uv_table["package"] = False
    return tomlkit.dumps(document)


def resolved_versions(lock_text: str) -> dict[str, str]:
    """Map canonical package names to versions from a `uv.lock` document."""
    packages = loads(lock_text).get("package")
    if not isinstance(packages, list):
        return {}
    versions: dict[str, str] = {}
    for package in cast("list[Any]", packages):
        if not isinstance(package, dict):
            continue
        package_map = cast("dict[str, Any]", package)
        name = package_map.get("name")
        version = package_map.get("version")
        if isinstance(name, str) and isinstance(version, str):
            versions[canonicalize_name(name)] = version
    return versions


def _redundancy_reason(override: Override, natural: Mapping[str, str]) -> str | None:
    """Return why an override is removable, or None when it is still required."""
    version = natural.get(override.canonical_name)
    if version is None:
        return "not resolved without the override; the dependency is gone"
    specifier = override.requirement.specifier
    if not specifier:
        return None
    try:
        parsed = Version(version)
    except InvalidVersion:
        return None
    if parsed in specifier:
        return f"natural resolution {version} already satisfies {specifier}"
    return None


def evaluate_overrides(overrides: list[Override], natural: Mapping[str, str]) -> list[Finding]:
    """Return findings for every override the natural resolution makes redundant."""
    findings: list[Finding] = []
    for override in overrides:
        reason = _redundancy_reason(override, natural)
        if reason is not None:
            findings.append(Finding(name=override.name, reason=reason))
    return findings


def _resolve_executable(name: str) -> str:
    """Resolve an executable path for subprocess calls."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} executable not found on PATH")
    return executable


def resolve_probe_lock(probe_pyproject: str) -> str:
    """Lock an isolated probe project and return its `uv.lock` text."""
    uv = _resolve_executable("uv")
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        (project / "pyproject.toml").write_text(probe_pyproject, encoding="utf-8")
        subprocess.run(  # noqa: S603
            [uv, "lock"],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        )
        return (project / "uv.lock").read_text(encoding="utf-8")


def audit_overrides(
    pyproject_text: str, *, resolver: ProbeResolver = resolve_probe_lock
) -> list[Finding]:
    """Audit overrides against the natural resolution and return findings."""
    overrides = parse_overrides(pyproject_text)
    if not overrides:
        return []
    natural = resolved_versions(resolver(build_probe_pyproject(pyproject_text)))
    return evaluate_overrides(overrides, natural)


def render_report(overrides: list[Override], findings: list[Finding]) -> str:
    """Render the human-readable audit result."""
    if not overrides:
        return "No dependency overrides configured."
    if not findings:
        count = len(overrides)
        noun = "override" if count == 1 else "overrides"
        return f"All {count} dependency {noun} still required."
    lines = ["Removable dependency overrides:", ""]
    lines.extend(f"  {finding.name}: {finding.reason}" for finding in findings)
    lines.append("")
    lines.append(
        "Remove each from `[tool.uv] override-dependencies` in pyproject.toml, "
        + "re-lock, and confirm audits stay green."
    )
    return "\n".join(lines)


def main() -> int:
    """Run the dependency override audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=PYPROJECT_PATH,
        help="path to pyproject.toml (default: repository root)",
    )
    args = parser.parse_args()
    pyproject_text = args.pyproject.read_text(encoding="utf-8")
    overrides = parse_overrides(pyproject_text)
    findings = audit_overrides(pyproject_text)
    print(render_report(overrides, findings))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

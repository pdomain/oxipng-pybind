"""Tests for the dependency override audit."""

from __future__ import annotations

from scripts import audit_dependency_overrides as audit

SAMPLE_PYPROJECT = (
    "[project]\n"
    'name = "demo"\n'
    'version = "0"\n'
    'requires-python = ">=3.10"\n'
    "dependencies = []\n"
    "\n"
    "[tool.uv]\n"
    'override-dependencies = ["click>=8.3.3"]\n'
    "\n"
    "[tool.maturin]\n"
    'module-name = "_demo"\n'
    "\n"
    "[dependency-groups]\n"
    'lint = ["gitlint>=0.19.1"]\n'
)

SAMPLE_LOCK = (
    "version = 1\n"
    "\n"
    "[[package]]\n"
    'name = "click"\n'
    'version = "8.1.3"\n'
    "\n"
    "[[package]]\n"
    'name = "gitlint"\n'
    'version = "0.19.1"\n'
)


def test_parse_overrides_reads_tool_uv_entries() -> None:
    """Override entries parse into distribution names and requirements."""
    overrides = audit.parse_overrides(SAMPLE_PYPROJECT)

    assert [override.name for override in overrides] == ["click"]
    assert str(overrides[0].requirement.specifier) == ">=8.3.3"
    assert overrides[0].canonical_name == "click"


def test_parse_overrides_returns_empty_without_tool_uv() -> None:
    """A project without `[tool.uv]` overrides yields no entries."""
    assert audit.parse_overrides('[project]\nname = "demo"\n') == []


def test_build_probe_pyproject_strips_overrides_and_unpackages_root() -> None:
    """The probe drops overrides and marks the root a virtual project."""
    probe = audit.build_probe_pyproject(SAMPLE_PYPROJECT)

    assert "override-dependencies" not in probe
    assert "package = false" in probe
    # The dependency graph that decides the natural resolution is preserved.
    assert 'lint = ["gitlint>=0.19.1"]' in probe


def test_resolved_versions_maps_canonical_names() -> None:
    """Lock parsing returns canonical-name to version mappings."""
    versions = audit.resolved_versions(SAMPLE_LOCK)

    assert versions == {"click": "8.1.3", "gitlint": "0.19.1"}


def test_evaluate_overrides_keeps_binding_override() -> None:
    """An override whose floor exceeds the natural version is still required."""
    overrides = audit.parse_overrides(SAMPLE_PYPROJECT)

    assert audit.evaluate_overrides(overrides, {"click": "8.1.3"}) == []


def test_evaluate_overrides_flags_satisfied_floor() -> None:
    """An override is removable once the natural resolution meets its floor."""
    overrides = audit.parse_overrides(SAMPLE_PYPROJECT)

    findings = audit.evaluate_overrides(overrides, {"click": "8.4.2"})

    assert len(findings) == 1
    assert findings[0].name == "click"
    assert "8.4.2" in findings[0].reason


def test_evaluate_overrides_flags_dropped_dependency() -> None:
    """An override for a package no longer resolved is removable."""
    overrides = audit.parse_overrides(SAMPLE_PYPROJECT)

    findings = audit.evaluate_overrides(overrides, {})

    assert len(findings) == 1
    assert "gone" in findings[0].reason


def test_audit_overrides_uses_probe_resolver() -> None:
    """The audit resolves the probe pyproject and evaluates the result."""
    seen: list[str] = []

    def resolver(probe_pyproject: str) -> str:
        seen.append(probe_pyproject)
        return SAMPLE_LOCK

    findings = audit.audit_overrides(SAMPLE_PYPROJECT, resolver=resolver)

    assert findings == []
    assert "override-dependencies" not in seen[0]


def test_audit_overrides_skips_resolution_without_overrides() -> None:
    """With no overrides the audit never invokes the resolver."""

    def resolver(_probe_pyproject: str) -> str:  # pragma: no cover - must not run.
        raise AssertionError("resolver should not be called")

    assert audit.audit_overrides('[project]\nname = "demo"\n', resolver=resolver) == []


def test_render_report_reports_no_overrides() -> None:
    """The report states when no overrides are configured."""
    assert audit.render_report([], []) == "No dependency overrides configured."


def test_render_report_reports_all_required() -> None:
    """The report confirms when every override is still required."""
    overrides = audit.parse_overrides(SAMPLE_PYPROJECT)

    assert audit.render_report(overrides, []) == "All 1 dependency override still required."


def test_render_report_lists_removable_overrides() -> None:
    """The report lists each removable override with its reason and next steps."""
    overrides = audit.parse_overrides(SAMPLE_PYPROJECT)
    findings = [
        audit.Finding(name="click", reason="natural resolution 8.4.2 already satisfies >=8.3.3")
    ]

    report = audit.render_report(overrides, findings)

    assert "Removable dependency overrides:" in report
    assert "click: natural resolution 8.4.2 already satisfies >=8.3.3" in report
    assert "override-dependencies" in report

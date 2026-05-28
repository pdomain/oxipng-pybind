"""Unit tests for release tag version consistency checks."""

from __future__ import annotations

from scripts.verify_release_version import release_version_errors


def test_release_version_matches_python_and_cargo() -> None:
    """Matching tag, Cargo, and pyproject versions produce no errors."""
    errors = release_version_errors(
        tag="v10.1.1",
        pyproject_version="10.1.1",
        cargo_version="10.1.1",
    )

    assert errors == []


def test_release_version_allows_python_post_release_with_cargo_base() -> None:
    """Python post releases keep Cargo on the upstream semver base."""
    errors = release_version_errors(
        tag="v10.1.1.post1",
        pyproject_version="10.1.1.post1",
        cargo_version="10.1.1",
    )

    assert errors == []


def test_release_version_rejects_tag_mismatch() -> None:
    """Mismatched tag versions are rejected with a stable error message."""
    errors = release_version_errors(
        tag="v10.1.0",
        pyproject_version="10.1.1",
        cargo_version="10.1.1",
    )

    assert errors == ["tag version 10.1.0 does not match pyproject version 10.1.1"]


def test_release_version_rejects_cargo_mismatch() -> None:
    """Mismatched Cargo versions are rejected with a stable error message."""
    errors = release_version_errors(
        tag="v10.1.1",
        pyproject_version="10.1.1",
        cargo_version="10.1.0",
    )

    assert errors == ["cargo version 10.1.0 does not match pyproject base version 10.1.1"]

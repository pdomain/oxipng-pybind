"""Tests for shared workflow test helpers."""

from __future__ import annotations

import pytest

from tests.helpers.workflows import (
    assert_action_ref_is_reviewed,
    assert_ordered_steps,
    step_by_name,
    workflow_trigger,
)


def test_workflow_trigger_accepts_yaml_boolean_on_key() -> None:
    workflow = {True: {"push": None}}

    assert workflow_trigger(workflow) == {"push": None}


def test_step_by_name_rejects_duplicate_step_names() -> None:
    steps = [{"name": "Build"}, {"name": "Build"}]

    with pytest.raises(AssertionError, match="expected exactly one step named Build"):
        step_by_name(steps, "Build")


def test_assert_ordered_steps_rejects_reordered_steps() -> None:
    steps = [{"name": "Test"}, {"name": "Build"}]

    with pytest.raises(AssertionError, match="expected step order"):
        assert_ordered_steps(steps, ["Build", "Test"])


def test_assert_action_ref_is_reviewed_rejects_unreviewed_sha() -> None:
    with pytest.raises(AssertionError, match="unreviewed action ref"):
        assert_action_ref_is_reviewed("example/action@0123456789abcdef0123456789abcdef01234567")

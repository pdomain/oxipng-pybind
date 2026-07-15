"""Shared workflow assertions for tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[2]
Workflow = dict[Any, Any]
Step = dict[str, Any]

REVIEWED_ACTION_REFS = {
    "actions/checkout": "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/upload-artifact": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    "actions/download-artifact": "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
    "astral-sh/setup-uv": "11f9893b081a58869d3b5fccaea48c9e9e46f990",
    "taiki-e/install-action": "43aecc8d72668fbcfe75c31400bc4f890f1c5853",
    "peter-evans/create-pull-request": "5f6978faf089d4d20b00c7766989d076bb2fc7f1",
    "PyO3/maturin-action": "e83996d129638aa358a18fbd1dfb82f0b0fb5d3b",
    "pypa/gh-action-pypi-publish": "cef221092ed1bacb1cc03d23a2d87d1d172e277b",
}
RUST_TOOLCHAIN_VERSION = "1.97.0"


def load_workflow(relative: str) -> Workflow:
    data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast("Workflow", data)


def workflow_trigger(workflow: Workflow) -> Workflow:
    trigger = workflow["on"] if "on" in workflow else workflow[True]
    assert isinstance(trigger, dict)
    return cast("Workflow", trigger)


def step_by_name(steps: list[Step], name: str) -> Step:
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name}, found {len(matches)}"
    return matches[0]


def step_index(steps: list[Step], name: str) -> int:
    return steps.index(step_by_name(steps, name))


def assert_ordered_steps(steps: list[Step], names: list[str]) -> None:
    indexes = [step_index(steps, name) for name in names]
    assert indexes == sorted(indexes), f"expected step order {names}, got indexes {indexes}"


def parse_action_ref(uses: str) -> tuple[str, str]:
    action, ref = uses.rsplit("@", 1)
    return action, ref


def assert_action_ref_is_reviewed(uses: str) -> None:
    if uses.startswith("dtolnay/rust-toolchain@"):
        assert uses == f"dtolnay/rust-toolchain@{RUST_TOOLCHAIN_VERSION}"
        return

    action, ref = parse_action_ref(uses)
    expected = REVIEWED_ACTION_REFS.get(action)
    assert expected is not None, f"unreviewed action ref: {uses}"
    assert ref == expected, f"{action} uses {ref}, expected reviewed ref {expected}"

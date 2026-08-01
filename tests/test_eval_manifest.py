from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.manifest import load_questions  # noqa: E402


def test_manifest_loads_and_ids_are_unique() -> None:
    questions = load_questions()
    assert len(questions) >= 12
    ids = [q.id for q in questions]
    assert len(ids) == len(set(ids))


def test_pinned_questions_carry_expected_values() -> None:
    pinned = [q for q in load_questions() if q.answer_type == "pinned"]
    assert pinned, "manifest must contain pinned questions"
    for q in pinned:
        assert q.expected_value is not None, q.id
        assert q.expected_period, q.id
        assert q.tolerance >= 0.0, q.id
        assert q.note.strip(), f"{q.id} must explain why the value never revises"


def test_live_questions_resolve_to_known_concepts() -> None:
    from ausecon_mcp.catalogue.resolver import CURATED_SHORTCUTS
    from ausecon_mcp.derived import DERIVED_CONCEPTS

    live = [q for q in load_questions() if q.answer_type == "live"]
    assert live, "manifest must contain live questions"
    for q in live:
        assert q.resolver is not None, q.id
        kind = q.resolver["kind"]
        concept = q.resolver["concept"]
        if kind == "economic":
            assert concept in CURATED_SHORTCUTS, f"{q.id}: unknown concept {concept}"
        elif kind == "derived":
            assert concept in DERIVED_CONCEPTS, f"{q.id}: unknown derived concept {concept}"
        else:
            pytest.fail(f"{q.id}: unknown resolver kind {kind}")


def test_question_text_does_not_leak_tool_identifiers() -> None:
    for q in load_questions():
        lowered = q.question.lower()
        for banned in ("get_economic_series", "get_derived_series", "concept=", "ausecon"):
            assert banned not in lowered, f"{q.id} leaks identifier {banned!r}"

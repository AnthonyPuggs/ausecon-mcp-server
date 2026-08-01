from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.grading import GroundTruth, Verdict  # noqa: E402
from evals.loop import CellResult  # noqa: E402
from evals.manifest import EvalQuestion  # noqa: E402
from evals.results import (  # noqa: E402
    aggregate,
    build_cell_record,
    build_results_document,
    estimate_cost_usd,
)


def _cell(arm, outcome, fresh=False, live=True, tool_calls=1, error=None):
    return {
        "question_id": "q",
        "arm": arm,
        "outcome": outcome,
        "value_ok": outcome == "correct",
        "fresh": fresh,
        "unit_flag": False,
        "submitted": {},
        "tool_calls": tool_calls,
        "input_tokens": 1000,
        "output_tokens": 100,
        "latency_s": 2.0,
        "error": error,
        "answer_type": "live" if live else "pinned",
    }


def test_aggregate_accuracy_excludes_error_cells() -> None:
    cells = [
        _cell("bare", "correct"),
        _cell("bare", "incorrect"),
        _cell("bare", "no_answer", error="RuntimeError: boom"),
    ]
    agg = aggregate(cells)["bare"]
    assert agg["accuracy"] == 0.5  # 1 correct of 2 graded
    assert agg["error_count"] == 1


def test_aggregate_freshness_only_over_live_graded_cells() -> None:
    cells = [
        _cell("ausecon", "correct", fresh=True, live=True),
        _cell("ausecon", "correct", fresh=False, live=False),  # pinned: ignored for freshness
        _cell("ausecon", "incorrect", fresh=False, live=True),
    ]
    agg = aggregate(cells)["ausecon"]
    assert agg["freshness"] == 0.5


def test_aggregate_abstain_rate() -> None:
    cells = [_cell("web", "abstain"), _cell("web", "correct")]
    assert aggregate(cells)["web"]["abstain_rate"] == 0.5


def test_estimate_cost() -> None:
    # 1M input at $3 + 1M output at $15
    assert estimate_cost_usd(1_000_000, 1_000_000) == 18.0


def test_aggregate_empty_cell_list_returns_empty_dict() -> None:
    assert aggregate([]) == {}


def test_aggregate_all_error_cells_zero_denominators() -> None:
    cells = [
        _cell("bare", "no_answer", error="RuntimeError: boom"),
        _cell("bare", "no_answer", error="TimeoutError: slow"),
    ]
    agg = aggregate(cells)["bare"]
    assert agg["error_count"] == 2
    assert agg["accuracy"] == 0.0
    assert agg["abstain_rate"] == 0.0
    assert agg["freshness"] == 0.0  # live_graded also empty since graded is empty


def test_aggregate_no_answer_without_error_counts_as_graded() -> None:
    # outcome == "no_answer" alone (error=None) must not be excluded as an error cell;
    # only outcome == "no_answer" AND a truthy error string is an error cell.
    cells = [_cell("bare", "no_answer", error=None), _cell("bare", "correct")]
    agg = aggregate(cells)["bare"]
    assert agg["error_count"] == 0
    assert agg["accuracy"] == 0.5  # 1 correct of 2 graded


def test_aggregate_pinned_only_arm_has_zero_freshness() -> None:
    # graded cells exist but none are live -> freshness denominator (live_graded) is empty.
    cells = [_cell("bare", "correct", live=False), _cell("bare", "incorrect", live=False)]
    agg = aggregate(cells)["bare"]
    assert agg["freshness"] == 0.0


def test_build_cell_record_maps_fields() -> None:
    question = EvalQuestion(
        id="q1",
        question="What is X?",
        answer_type="pinned",
        category="test",
        source="abs",
        tolerance=0.1,
        unit="per cent",
        note="fixed",
        expected_value=1.0,
        expected_period="2020-Q1",
    )
    truth = GroundTruth(value=1.0, period="2020-Q1", unit="per cent")
    cell = CellResult(
        submitted={"value": 1.0, "unit": "per cent", "period": "2020-Q1", "not_found": False},
        tool_calls=2,
        input_tokens=500,
        output_tokens=50,
        latency_s=1.2345,
        error=None,
    )
    verdict = Verdict(outcome="correct", value_ok=True, fresh=True, unit_flag=False)

    record = build_cell_record(question, "bare", truth, cell, verdict)

    assert record["question_id"] == "q1"
    assert record["arm"] == "bare"
    assert record["answer_type"] == "pinned"
    assert record["outcome"] == "correct"
    assert record["value_ok"] is True
    assert record["fresh"] is True
    assert record["unit_flag"] is False
    assert record["submitted"] == cell.submitted
    assert record["expected_value"] == 1.0
    assert record["expected_period"] == "2020-Q1"
    assert record["tool_calls"] == 2
    assert record["input_tokens"] == 500
    assert record["output_tokens"] == 50
    assert record["latency_s"] == 1.23  # rounded to 2dp
    assert record["error"] is None


def test_build_results_document_shape() -> None:
    cells = [_cell("bare", "correct"), _cell("web", "abstain")]
    ground_truth = {"q": {"value": 1.0, "period": "2020-Q1", "unit": "per cent"}}

    document = build_results_document(
        model="claude-sonnet-5",
        package_version="1.0.0",
        timestamp_iso="2026-08-02T00:00:00+00:00",
        ground_truth=ground_truth,
        cell_records=cells,
    )

    assert document["run"]["model"] == "claude-sonnet-5"
    assert document["run"]["package_version"] == "1.0.0"
    assert document["run"]["question_count"] == 1
    assert document["run"]["input_tokens"] == 2000
    assert document["run"]["output_tokens"] == 200
    assert document["run"]["est_cost_usd"] == round(estimate_cost_usd(2000, 200), 2)
    assert document["ground_truth"] == ground_truth
    assert document["cells"] == cells
    assert set(document["aggregates"]) == {"bare", "web"}

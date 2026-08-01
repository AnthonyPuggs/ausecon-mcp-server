from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.results import build_results_document  # noqa: E402

RESULTS = ROOT / "evals" / "results" / "latest.json"
PAGE = ROOT / "docs-site" / "src" / "content" / "docs" / "user-guide" / "evaluation.md"


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


def _synthetic_document(arms=("bare", "web", "ausecon")):
    cells = []
    for arm in arms:
        cells.append(_cell(arm, "correct", fresh=True, live=True))
        cells.append(_cell(arm, "incorrect", fresh=False, live=True))
    ground_truth = {"q": {"value": 1.0, "period": "2020-Q1", "unit": "per cent"}}
    return build_results_document(
        model="claude-sonnet-5",
        package_version="1.14.1",
        timestamp_iso="2026-08-02T00:00:00+00:00",
        ground_truth=ground_truth,
        cell_records=cells,
    )


@pytest.mark.skipif(not RESULTS.exists(), reason="no eval results committed yet")
def test_eval_docs_page_matches_latest_results() -> None:
    from scripts.update_docs_eval import render

    document = json.loads(RESULTS.read_text(encoding="utf-8"))
    assert PAGE.exists(), "run scripts/update_docs_eval.py after each eval run"
    assert PAGE.read_text(encoding="utf-8") == render(document)


def test_render_produces_expected_frontmatter_and_tables() -> None:
    from scripts.update_docs_eval import render

    document = _synthetic_document()
    text = render(document)

    assert text.startswith(
        "---\ntitle: Evaluation\ndescription: Measured impact of the ausecon MCP server on "
        "Claude's Australian-economics answers.\n---\n"
    )
    assert "claude-sonnet-5" in text
    assert "1.14.1" in text
    assert "## Results" in text
    assert "| Arm | Accuracy | Freshness (live questions) | Abstained | Errors |" in text
    assert "| Claude alone | 50% | 50% | 0% | 0 |" in text
    assert "| Claude + web search | 50% | 50% | 0% | 0 |" in text
    assert "| Claude + ausecon MCP | 50% | 50% | 0% | 0 |" in text
    assert "| Arm | Avg tool calls | Avg latency (s) | Tokens (in / out) |" in text
    assert "## Methodology" in text
    assert "## Limitations" in text


def test_render_skips_arms_missing_from_aggregates() -> None:
    from scripts.update_docs_eval import render

    document = _synthetic_document(arms=("bare", "ausecon"))
    text = render(document)

    assert "Claude alone" in text
    assert "Claude + ausecon MCP" in text
    assert "Claude + web search" not in text


def test_render_handles_empty_aggregates() -> None:
    from scripts.update_docs_eval import render

    document = build_results_document(
        model="claude-sonnet-5",
        package_version="1.14.1",
        timestamp_iso="2026-08-02T00:00:00+00:00",
        ground_truth={},
        cell_records=[],
    )
    text = render(document)

    assert "## Results" in text
    assert "| Claude alone |" not in text
    assert "| Claude + web search |" not in text
    assert "| Claude + ausecon MCP |" not in text
    assert "## Methodology" in text

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.manifest import EvalQuestion  # noqa: E402
from evals.resolve import resolve_ground_truth  # noqa: E402


class FakeService:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str, dict]] = []

    async def get_economic_series(self, concept: str, **kwargs) -> dict:
        self.calls.append(("economic", concept, kwargs))
        return self.payload

    async def get_derived_series(self, concept: str, **kwargs) -> dict:
        self.calls.append(("derived", concept, kwargs))
        return self.payload


PAYLOAD = {
    "metadata": {},
    "series": [{"series_id": "X", "label": "X", "unit": "Percent"}],
    "observations": [{"date": "2026-Q1", "series_id": "X", "value": 4.35}],
}


def _question(answer_type: str, resolver: dict | None = None, **overrides) -> EvalQuestion:
    base = dict(
        id="q1",
        question="What?",
        answer_type=answer_type,
        category="c",
        source="rba",
        tolerance=0.0,
        unit="per cent",
        note="n",
        expected_value=1.5 if answer_type == "pinned" else None,
        expected_period="2016-08-03" if answer_type == "pinned" else None,
        resolver=resolver,
    )
    base.update(overrides)
    return EvalQuestion(**base)


async def test_pinned_resolution_skips_service() -> None:
    service = FakeService(PAYLOAD)
    truth = await resolve_ground_truth(service, _question("pinned"))
    assert truth.value == 1.5
    assert truth.period == "2016-08-03"
    assert truth.unit == "per cent"
    assert service.calls == []


async def test_live_economic_resolution_uses_last_observation() -> None:
    service = FakeService(PAYLOAD)
    truth = await resolve_ground_truth(
        service, _question("live", resolver={"kind": "economic", "concept": "cash_rate_target"})
    )
    assert truth.value == 4.35
    assert truth.period == "2026-Q1"
    assert truth.unit == "Percent"
    method, concept, kwargs = service.calls[0]
    assert method == "economic"
    assert concept == "cash_rate_target"
    assert kwargs.get("last_n") == 1


async def test_live_resolution_rejects_empty_observations() -> None:
    service = FakeService({"metadata": {}, "series": [], "observations": []})
    with pytest.raises(ValueError, match="no observations"):
        await resolve_ground_truth(
            service, _question("live", resolver={"kind": "economic", "concept": "cash_rate_target"})
        )


async def test_live_derived_resolution_calls_get_derived_series() -> None:
    service = FakeService(PAYLOAD)
    truth = await resolve_ground_truth(
        service, _question("live", resolver={"kind": "derived", "concept": "real_cash_rate"})
    )
    assert truth.value == 4.35
    assert truth.period == "2026-Q1"
    assert truth.unit == "Percent"
    method, concept, kwargs = service.calls[0]
    assert method == "derived"
    assert concept == "real_cash_rate"
    assert kwargs.get("last_n") == 1


async def test_live_resolution_filters_none_values() -> None:
    payload = {
        "metadata": {},
        "series": [{"series_id": "X", "label": "X", "unit": "Percent"}],
        "observations": [
            {"date": "2025-Q4", "series_id": "X", "value": 4.1},
            {"date": "2026-Q1", "series_id": "X", "value": None},
        ],
    }
    service = FakeService(payload)
    truth = await resolve_ground_truth(
        service, _question("live", resolver={"kind": "economic", "concept": "cash_rate_target"})
    )
    assert truth.value == 4.1
    assert truth.period == "2025-Q4"
    assert truth.unit == "Percent"


async def test_live_resolution_falls_back_to_question_unit() -> None:
    payload = {
        "metadata": {},
        "series": [],
        "observations": [{"date": "2026-Q1", "series_id": "X", "value": 4.35}],
    }
    service = FakeService(payload)
    truth = await resolve_ground_truth(
        service, _question("live", resolver={"kind": "economic", "concept": "cash_rate_target"})
    )
    assert truth.value == 4.35
    assert truth.period == "2026-Q1"
    assert truth.unit == "per cent"

from __future__ import annotations

from evals.grading import GroundTruth
from evals.manifest import EvalQuestion


async def resolve_ground_truth(service, question: EvalQuestion) -> GroundTruth:
    if question.answer_type == "pinned":
        assert question.expected_value is not None and question.expected_period is not None
        return GroundTruth(
            value=question.expected_value,
            period=question.expected_period,
            unit=question.unit,
        )

    resolver = question.resolver or {}
    concept = resolver["concept"]
    if resolver["kind"] == "derived":
        payload = await service.get_derived_series(concept, last_n=1)
    else:
        payload = await service.get_economic_series(
            concept,
            variant=resolver.get("variant"),
            geography=resolver.get("geography"),
            frequency=resolver.get("frequency"),
            last_n=1,
        )

    observations = [o for o in payload.get("observations", []) if o.get("value") is not None]
    if not observations:
        raise ValueError(f"{question.id}: resolver returned no observations")
    latest = observations[-1]
    series = payload.get("series") or [{}]
    unit = series[0].get("unit") or question.unit
    return GroundTruth(value=float(latest["value"]), period=str(latest["date"]), unit=str(unit))

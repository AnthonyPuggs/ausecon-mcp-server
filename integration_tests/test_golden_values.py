from __future__ import annotations

import pytest

from ausecon_mcp.server import AuseconService

from .golden import GoldenEntry, load_golden_values

pytestmark = pytest.mark.asyncio

GOLDEN = load_golden_values()


async def _fetch(service: AuseconService, entry: GoldenEntry) -> dict:
    if entry.source == "abs":
        return await service.get_abs_data(
            entry.identifier, key=entry.key, start_period=entry.start, end_period=entry.end
        )
    if entry.source == "rba":
        return await service.get_rba_table(
            entry.identifier, series_ids=[entry.key], start_date=entry.start, end_date=entry.end
        )
    if entry.source == "apra":
        return await service.get_apra_data(
            entry.identifier,
            table_id=entry.table_id,
            series_ids=[entry.key],
            start_date=entry.start,
            end_date=entry.end,
        )
    raise AssertionError(f"unknown source {entry.source!r}")


@pytest.mark.parametrize("entry", GOLDEN, ids=[e.id for e in GOLDEN])
async def test_golden_value_matches_live_source(entry: GoldenEntry) -> None:
    service = AuseconService()
    result = await _fetch(service, entry)
    url = result["metadata"].get("retrieval_url")

    matches = [obs for obs in result["observations"] if obs["date"] == entry.match_date]
    assert matches, f"{entry.id}: no observation dated {entry.match_date} (url={url})"

    actual = matches[0]["value"]
    assert actual is not None, f"{entry.id}: observation value is None (url={url})"
    assert abs(actual - entry.expected_value) <= entry.tolerance, (
        f"{entry.id}: expected {entry.expected_value} +/- {entry.tolerance}, "
        f"got {actual} (url={url})"
    )

from __future__ import annotations

import pytest

from ausecon_mcp.providers.apra import APRAProvider

pytestmark = pytest.mark.asyncio


async def test_apra_quarterly_performance_live_returns_key_stats() -> None:
    provider = APRAProvider()

    result = await provider.get_data(
        "ADI_QUARTERLY_PERFORMANCE",
        table_id="key_stats",
        last_n=1,
    )

    assert result["metadata"]["source"] == "apra"
    assert result["metadata"]["dataset_id"] == "ADI_QUARTERLY_PERFORMANCE"
    assert result["series"]
    assert result["observations"]


async def test_apra_property_exposures_live_returns_residential_property_table() -> None:
    provider = APRAProvider()

    result = await provider.get_data(
        "ADI_PROPERTY_EXPOSURES",
        table_id="tab_1b",
        last_n=1,
    )

    assert result["metadata"]["source"] == "apra"
    assert result["metadata"]["dataset_id"] == "ADI_PROPERTY_EXPOSURES"
    assert any(
        "total_credit_outstanding" in series["series_id"]
        or "total_credit_oustanding" in series["series_id"]
        for series in result["series"]
    )
    assert result["observations"]


# Every curated APRA concept, end to end through the semantic layer. Added after APRA
# renamed the PHI performance data sheet ("Database" -> "Database ") and the nightly
# suite kept passing for weeks because no APRA concept was exercised here.
_APRA_CONCEPT_MAX_AGE_DAYS = 200


def _apra_concepts() -> list[str]:
    from ausecon_mcp.catalogue.resolver import list_economic_concepts

    return sorted(entry["concept"] for entry in list_economic_concepts(source="apra"))


@pytest.mark.parametrize("concept", _apra_concepts())
async def test_live_every_apra_concept_resolves_with_recent_data(concept: str) -> None:
    from datetime import date, timedelta

    from ausecon_mcp.server import AuseconService

    result = await AuseconService().get_economic_series(concept, last_n=1)

    assert result["metadata"]["source"] == "apra"
    assert result["observations"], f"expected observations for {concept}"
    latest = date.fromisoformat(result["observations"][-1]["date"])
    assert date.today() - latest <= timedelta(days=_APRA_CONCEPT_MAX_AGE_DAYS), (
        f"{concept} latest observation {latest} is stale"
    )

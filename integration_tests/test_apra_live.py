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

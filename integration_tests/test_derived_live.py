from __future__ import annotations

import pytest

from ausecon_mcp.server import AuseconService

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    ("concept", "frequency"),
    [
        ("yield_curve_slope", "Daily"),
        ("real_cash_rate", "Monthly"),
        ("gdp_per_capita", "Quarterly"),
        ("misery_index", "Monthly"),
        ("real_10y_bond_yield", "Monthly"),
        ("real_business_lending_rate", "Monthly"),
        ("broad_money_growth", "Monthly"),
        ("terms_of_trade", "Quarterly"),
    ],
)
async def test_live_derived_series_foundation_concepts(concept: str, frequency: str) -> None:
    service = AuseconService()
    result = await service.get_derived_series(concept, last_n=3)

    assert result["metadata"]["source"] == "derived"
    assert result["metadata"]["dataset_id"] == concept
    assert result["metadata"]["derived"]["concept"] == concept
    assert result["metadata"]["derived"]["alignment_frequency"] == frequency
    assert result["observations"], f"expected derived observations for {concept}"
    assert {series["series_id"] for series in result["series"]} == {concept}

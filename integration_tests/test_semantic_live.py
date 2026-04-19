from __future__ import annotations

import pytest

from ausecon_mcp.server import AuseconService

pytestmark = pytest.mark.asyncio


async def _call(concept: str) -> dict:
    service = AuseconService()
    return await service.get_economic_series(concept, last_n=4)


# Tranche A live coverage


async def test_live_semantic_unemployment_rate() -> None:
    result = await _call("unemployment_rate")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "LF"
    assert result["observations"], "expected observations for unemployment_rate"


async def test_live_semantic_wage_growth() -> None:
    result = await _call("wage_growth")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "WPI"
    assert result["observations"]


async def test_live_semantic_monthly_inflation() -> None:
    result = await _call("monthly_inflation")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "g4"
    series_ids = {s["series_id"] for s in result["series"]}
    assert "GCPIAGSAMP" in series_ids


async def test_live_semantic_government_bond_yield_10y() -> None:
    result = await _call("government_bond_yield_10y")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "f17"
    series_ids = {s["series_id"] for s in result["series"]}
    assert "FZCY1000D" in series_ids


async def test_live_semantic_housing_credit() -> None:
    result = await _call("housing_credit")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "d2"
    series_ids = {s["series_id"] for s in result["series"]}
    assert {"DLCACOHS", "DLCACIHS"} <= series_ids


# Tranche B live coverage


async def test_live_semantic_current_account_balance() -> None:
    result = await _call("current_account_balance")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "BOP"
    assert result["observations"]


async def test_live_semantic_underemployment_rate() -> None:
    result = await _call("underemployment_rate")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "LF_UNDER"
    assert result["observations"]


async def test_live_semantic_mortgage_rate() -> None:
    result = await _call("mortgage_rate")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "f6"
    series_ids = {s["series_id"] for s in result["series"]}
    assert "FLRHOOVA" in series_ids


async def test_live_semantic_population() -> None:
    result = await _call("population")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "ERP_Q"
    assert result["observations"]


async def test_live_semantic_commodity_prices() -> None:
    result = await _call("commodity_prices")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "i2"
    series_ids = {s["series_id"] for s in result["series"]}
    assert "GRCPAISDR" in series_ids

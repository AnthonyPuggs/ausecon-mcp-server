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

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "CPI"
    series_ids = {s["series_id"] for s in result["series"]}
    assert "MEASURE=3|INDEX=10001|TSEST=10|REGION=50|FREQ=M" in series_ids


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


async def test_live_semantic_dwelling_approvals() -> None:
    result = await _call("dwelling_approvals")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "BA_GCCSA"
    assert result["observations"]


# Tranche C live coverage


@pytest.mark.parametrize(
    ("concept", "source", "dataset_id"),
    [
        ("real_gdp", "abs", "ANA_AGG"),
        ("nominal_gdp", "abs", "ANA_AGG"),
        ("household_consumption", "abs", "ANA_EXP"),
        ("private_investment", "abs", "ANA_EXP"),
        ("retail_turnover", "abs", "RT"),
    ],
)
async def test_live_semantic_tranche_c_abs_concepts(
    concept: str,
    source: str,
    dataset_id: str,
) -> None:
    result = await _call(concept)

    assert result["metadata"]["source"] == source
    assert result["metadata"]["dataset_id"] == dataset_id
    assert result["observations"]


@pytest.mark.parametrize(
    ("concept", "table_id", "series_id"),
    [
        ("broad_money", "d3", "DMABMS"),
        ("bank_bill_rate", "f1", "FIRMMBAB90D"),
    ],
)
async def test_live_semantic_tranche_c_rba_concepts(
    concept: str,
    table_id: str,
    series_id: str,
) -> None:
    result = await _call(concept)

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == table_id
    series_ids = {s["series_id"] for s in result["series"]}
    assert series_id in series_ids


# Tranche D live coverage


@pytest.mark.parametrize(
    ("concept", "table_id", "series_id"),
    [
        ("total_credit", "d2", "DLCACS"),
        ("total_credit_growth", "d1", "DGFAC12"),
        ("housing_credit_growth", "d1", "DGFACH12"),
        ("business_credit_growth", "d1", "DGFACB12"),
        ("m3", "d3", "DMAM3S"),
        ("money_base", "d3", "DMAMMB"),
        ("currency_in_circulation", "d3", "DMACS"),
        ("aud_cny", "f11", "FXRCR"),
        ("aud_jpy", "f11", "FXRJY"),
        ("aud_eur", "f11", "FXREUR"),
        ("aud_gbp", "f11", "FXRUKPS"),
        ("aud_nzd", "f11", "FXRNZD"),
    ],
)
async def test_live_semantic_tranche_d_rba_concepts(
    concept: str,
    table_id: str,
    series_id: str,
) -> None:
    result = await _call(concept)

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == table_id
    series_ids = {s["series_id"] for s in result["series"]}
    assert series_id in series_ids


# Tranche E live coverage


@pytest.mark.parametrize(
    ("concept", "series_id"),
    [
        ("monthly_cpi_index", "MEASURE=1|INDEX=10001|TSEST=10|REGION=50|FREQ=M"),
        ("monthly_cpi_change", "MEASURE=2|INDEX=10001|TSEST=10|REGION=50|FREQ=M"),
        (
            "monthly_trimmed_mean_inflation",
            "MEASURE=3|INDEX=999902|TSEST=20|REGION=50|FREQ=M",
        ),
        (
            "monthly_weighted_median_inflation",
            "MEASURE=3|INDEX=999903|TSEST=20|REGION=50|FREQ=M",
        ),
    ],
)
async def test_live_semantic_tranche_e_monthly_cpi_concepts(
    concept: str,
    series_id: str,
) -> None:
    result = await _call(concept)

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "CPI"
    series_ids = {s["series_id"] for s in result["series"]}
    assert series_id in series_ids


@pytest.mark.parametrize(
    ("concept", "series_id"),
    [
        (
            "new_housing_lending",
            "MEASURE=FIN_VAL|DATA_ITEM=NEWCOMMITS|LOAN_TYPE=DV8368|"
            "LOAN_PURPOSE=TOTDWELL|LENDER_TYPE=TOT|HOUSING_PURPOSE=TOT|"
            "TSEST=20|REGION=AUS|FREQ=Q",
        ),
        (
            "owner_occupier_housing_lending",
            "MEASURE=FIN_VAL|DATA_ITEM=NEWCOMMITS|LOAN_TYPE=DV8368|"
            "LOAN_PURPOSE=TOTDWELL|LENDER_TYPE=TOT|HOUSING_PURPOSE=DV5167|"
            "TSEST=20|REGION=AUS|FREQ=Q",
        ),
        (
            "investor_housing_lending",
            "MEASURE=FIN_VAL|DATA_ITEM=NEWCOMMITS|LOAN_TYPE=DV8368|"
            "LOAN_PURPOSE=TOTDWELL|LENDER_TYPE=TOT|HOUSING_PURPOSE=DV5168|"
            "TSEST=20|REGION=AUS|FREQ=Q",
        ),
    ],
)
async def test_live_semantic_tranche_e_housing_lending_concepts(
    concept: str,
    series_id: str,
) -> None:
    result = await _call(concept)

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "LEND_HOUSING"
    series_ids = {s["series_id"] for s in result["series"]}
    assert series_id in series_ids

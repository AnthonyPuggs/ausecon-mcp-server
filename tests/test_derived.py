from __future__ import annotations

import pytest

from ausecon_mcp.derived import DERIVED_CONCEPTS, derive_series, list_derived_concepts


def _payload(
    *,
    concept: str,
    source: str,
    dataset_id: str,
    series_id: str,
    observations: list[tuple[str, float | None]],
    frequency: str,
    unit: str | None = None,
    abs_key: str | None = None,
    rba_series_ids: list[str] | None = None,
) -> dict:
    return {
        "metadata": {
            "source": source,
            "dataset_id": dataset_id,
            "server_version": "test",
            "truncated": False,
            "semantic": {
                "concept": concept,
                "variant": None,
                "geography": None,
                "frequency": frequency,
                "requested_bounds": {"start": None, "end": None},
                "resolved_bounds": {"start": None, "end": None},
                "target": {
                    "source": source,
                    "dataset_id": dataset_id,
                    "upstream_id": dataset_id,
                    "abs_key": abs_key,
                    "rba_series_ids": rba_series_ids,
                },
            },
        },
        "series": [
            {
                "series_id": series_id,
                "label": concept,
                "unit": unit,
                "frequency": frequency,
                "dimensions": {},
                "source_key": series_id,
                "unit_multiplier": None,
                "decimals": None,
                "base_period": None,
            }
        ],
        "observations": [
            {"date": date, "series_id": series_id, "value": value, "dimensions": {}}
            for date, value in observations
        ],
    }


def test_list_derived_concepts_exposes_expected_concepts() -> None:
    assert list_derived_concepts() == [
        "broad_money_growth",
        "credit_growth",
        "credit_to_gdp",
        "employment_growth",
        "gdp_per_capita",
        "household_spending_growth",
        "misery_index",
        "mortgage_rate_spread",
        "real_10y_bond_yield",
        "real_bank_bill_rate",
        "real_business_lending_rate",
        "real_cash_rate",
        "real_mortgage_rate",
        "real_wage_growth",
        "terms_of_trade",
        "yield_curve_slope",
    ]


def test_yield_curve_slope_aligns_daily_yields_and_records_dropped_observations() -> None:
    payload = derive_series(
        "yield_curve_slope",
        {
            "long_yield": _payload(
                concept="government_bond_yield_10y",
                source="rba",
                dataset_id="f17",
                series_id="FZCY1000D",
                observations=[("2024-01-01", 4.2), ("2024-01-02", 4.1)],
                frequency="Daily",
                unit="Percent per annum",
                rba_series_ids=["FZCY1000D"],
            ),
            "short_yield": _payload(
                concept="government_bond_yield_3y",
                source="rba",
                dataset_id="f17",
                series_id="FZCY3D",
                observations=[("2024-01-01", 3.7), ("2024-01-03", 3.8)],
                frequency="Daily",
                unit="Percent per annum",
                rba_series_ids=["FZCY3D"],
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert payload["observations"] == [
        {
            "date": "2024-01-01",
            "series_id": "yield_curve_slope",
            "value": pytest.approx(0.5),
            "dimensions": {
                "DERIVED_CONCEPT": {
                    "code": "yield_curve_slope",
                    "label": "Yield curve slope",
                }
            },
            "status": None,
            "comment": None,
        }
    ]
    assert payload["metadata"]["source"] == "derived"
    assert payload["metadata"]["derived"]["formula"] == (
        "government_bond_yield_10y - government_bond_yield_3y"
    )
    assert payload["metadata"]["derived"]["dropped_observations"]["dropped"] == 3
    assert payload["metadata"]["derived"]["operands"][0]["rba_series_ids"] == ["FZCY1000D"]


def test_real_cash_rate_carries_cash_rate_forward_to_monthly_cpi_periods() -> None:
    payload = derive_series(
        "real_cash_rate",
        {
            "cash_rate": _payload(
                concept="cash_rate_target",
                source="rba",
                dataset_id="a2",
                series_id="ARBAMPCNCRT",
                observations=[("2024-01-03", 4.35), ("2024-03-20", 4.1)],
                frequency="Daily",
                unit="Percent per annum",
                rba_series_ids=["ARBAMPCNCRT"],
            ),
            "inflation": _payload(
                concept="monthly_inflation",
                source="abs",
                dataset_id="CPI",
                series_id="MEASURE=3|INDEX=10001|TSEST=10|REGION=50|FREQ=M",
                observations=[("2024-01", 4.1), ("2024-02", 3.8), ("2024-03", 3.5)],
                frequency="Monthly",
                unit="Percent",
                abs_key="3.10001.10.50.M",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    values = [(obs["date"], obs["value"]) for obs in payload["observations"]]
    assert values == [
        ("2024-01", pytest.approx(0.25)),
        ("2024-02", pytest.approx(0.55)),
        ("2024-03", pytest.approx(0.6)),
    ]
    assert payload["metadata"]["derived"]["alignment_frequency"] == "Monthly"


def test_real_wage_growth_subtracts_quarterly_cpi_year_ended_growth() -> None:
    payload = derive_series(
        "real_wage_growth",
        {
            "wage_growth": _payload(
                concept="wage_growth",
                source="abs",
                dataset_id="WPI",
                series_id="MEASURE=3|WPI_TYPE=THRPEB|SECTOR=7|INDUSTRY=TOT|TSEST=20|REGION=AUS|FREQ=Q",
                observations=[("2024-Q1", 4.2), ("2024-Q2", 3.8)],
                frequency="Quarterly",
                unit="Percent",
                abs_key="3.THRPEB.7.TOT.20.AUS.Q",
            ),
            "cpi_index": _payload(
                concept="headline_cpi",
                source="abs",
                dataset_id="CPI",
                series_id="MEASURE=1|INDEX=10001|TSEST=10|REGION=50|FREQ=Q",
                observations=[
                    ("2023-Q1", 100.0),
                    ("2023-Q2", 101.0),
                    ("2024-Q1", 104.0),
                    ("2024-Q2", 105.04),
                ],
                frequency="Quarterly",
                unit="Index",
                abs_key="1.10001.10.50.Q",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    values = [(obs["date"], obs["value"]) for obs in payload["observations"]]
    assert values == [("2024-Q1", pytest.approx(0.2)), ("2024-Q2", pytest.approx(-0.2))]
    assert "headline_cpi_yoy" in payload["metadata"]["derived"]["formula"]


def test_credit_growth_derives_year_ended_growth_and_applies_last_n() -> None:
    payload = derive_series(
        "credit_growth",
        {
            "total_credit": _payload(
                concept="total_credit",
                source="rba",
                dataset_id="d2",
                series_id="DLCACS",
                observations=[
                    ("2023-01", 100.0),
                    ("2023-02", 110.0),
                    ("2024-01", 115.0),
                    ("2024-02", 121.0),
                ],
                frequency="Monthly",
                unit="$ million",
                rba_series_ids=["DLCACS"],
            )
        },
        requested_start="2024-01",
        requested_end=None,
        last_n=1,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-02", pytest.approx(10.0))
    ]
    assert payload["metadata"]["truncated"] is True
    assert (
        payload["metadata"]["derived"]["formula"]
        == "100 * (total_credit_t / total_credit_t-12 - 1)"
    )


def test_gdp_per_capita_scales_real_gdp_millions_to_aud_per_person() -> None:
    payload = derive_series(
        "gdp_per_capita",
        {
            "real_gdp": _payload(
                concept="real_gdp",
                source="abs",
                dataset_id="ANA_AGG",
                series_id="MEASURE=M1|DATA_ITEM=GPM|TSEST=20|REGION=AUS|FREQ=Q",
                observations=[("2024-Q1", 700000.0)],
                frequency="Quarterly",
                unit="AUD",
                abs_key="M1.GPM.20.AUS.Q",
            ),
            "population": _payload(
                concept="population",
                source="abs",
                dataset_id="ERP_Q",
                series_id="MEASURE=1|SEX=3|AGE=TOT|REGION=AUS|FREQ=Q",
                observations=[("2024-Q1", 28000000.0)],
                frequency="Quarterly",
                unit="Persons",
                abs_key="1.3.TOT.AUS.Q",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert payload["observations"][0]["value"] == pytest.approx(25000.0)
    assert payload["series"][0]["unit"] == "real AUD per person"


def test_mortgage_rate_spread_carries_daily_bank_bill_rate_to_monthly_mortgage_periods() -> None:
    payload = derive_series(
        "mortgage_rate_spread",
        {
            "mortgage_rate": _payload(
                concept="mortgage_rate",
                source="rba",
                dataset_id="f6",
                series_id="FLRHOOVA",
                observations=[("2024-01", 6.2), ("2024-02", 6.3)],
                frequency="Monthly",
                rba_series_ids=["FLRHOOVA"],
            ),
            "bank_bill_rate": _payload(
                concept="bank_bill_rate",
                source="rba",
                dataset_id="f1",
                series_id="FIRMMBAB90D",
                observations=[("2024-01-15", 4.3), ("2024-02-20", 4.4)],
                frequency="Daily",
                rba_series_ids=["FIRMMBAB90D"],
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-01", pytest.approx(1.9)),
        ("2024-02", pytest.approx(1.9)),
    ]
    assert payload["series"][0]["unit"] == "percentage points"


def test_real_mortgage_rate_subtracts_monthly_inflation() -> None:
    payload = derive_series(
        "real_mortgage_rate",
        {
            "mortgage_rate": _payload(
                concept="mortgage_rate",
                source="rba",
                dataset_id="f6",
                series_id="FLRHOOVA",
                observations=[("2024-01", 6.2)],
                frequency="Monthly",
                rba_series_ids=["FLRHOOVA"],
            ),
            "inflation": _payload(
                concept="monthly_inflation",
                source="abs",
                dataset_id="CPI",
                series_id="cpi",
                observations=[("2024-01", 4.1)],
                frequency="Monthly",
                abs_key="3.10001.10.50.M",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert payload["observations"][0]["value"] == pytest.approx(2.1)


def test_credit_to_gdp_aligns_latest_monthly_credit_to_quarterly_nominal_gdp() -> None:
    payload = derive_series(
        "credit_to_gdp",
        {
            "total_credit": _payload(
                concept="total_credit",
                source="rba",
                dataset_id="d2",
                series_id="DLCACS",
                observations=[("2024-02", 3900.0), ("2024-03", 4000.0)],
                frequency="Monthly",
                rba_series_ids=["DLCACS"],
            ),
            "nominal_gdp": _payload(
                concept="nominal_gdp",
                source="abs",
                dataset_id="ANA_AGG",
                series_id="gdp",
                observations=[("2024-Q1", 2000.0)],
                frequency="Quarterly",
                abs_key="M3.GPM.20.AUS.Q",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert payload["observations"][0]["date"] == "2024-Q1"
    assert payload["observations"][0]["value"] == pytest.approx(200.0)


def test_household_spending_growth_derives_year_ended_growth() -> None:
    payload = derive_series(
        "household_spending_growth",
        {
            "household_spending": _payload(
                concept="quarterly_household_spending_volume",
                source="abs",
                dataset_id="HSI_Q",
                series_id="spending",
                observations=[("2023-Q1", 100.0), ("2024-Q1", 106.0)],
                frequency="Quarterly",
                abs_key="7.TOT.CVM.20.AUS.Q",
            )
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert payload["observations"][0]["date"] == "2024-Q1"
    assert payload["observations"][0]["value"] == pytest.approx(6.0)


def test_real_10y_bond_yield_carries_daily_yield_forward_to_monthly_inflation() -> None:
    payload = derive_series(
        "real_10y_bond_yield",
        {
            "bond_yield": _payload(
                concept="government_bond_yield_10y",
                source="rba",
                dataset_id="f17",
                series_id="FZCY1000D",
                observations=[("2024-01-10", 4.2), ("2024-03-15", 4.0)],
                frequency="Daily",
                unit="Percent per annum",
                rba_series_ids=["FZCY1000D"],
            ),
            "inflation": _payload(
                concept="monthly_inflation",
                source="abs",
                dataset_id="CPI",
                series_id="cpi",
                observations=[("2024-01", 4.1), ("2024-02", 3.8), ("2024-03", 3.5)],
                frequency="Monthly",
                unit="Percent",
                abs_key="3.10001.10.50.M",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    values = [(obs["date"], obs["value"]) for obs in payload["observations"]]
    assert values == [
        ("2024-01", pytest.approx(0.1)),
        ("2024-02", pytest.approx(0.4)),
        ("2024-03", pytest.approx(0.5)),
    ]
    assert payload["metadata"]["derived"]["alignment_frequency"] == "Monthly"
    assert payload["series"][0]["unit"] == "percentage points"


def test_real_bank_bill_rate_subtracts_inflation_from_carried_rate() -> None:
    payload = derive_series(
        "real_bank_bill_rate",
        {
            "bank_bill_rate": _payload(
                concept="bank_bill_rate",
                source="rba",
                dataset_id="f1",
                series_id="FIRMMBAB90D",
                observations=[("2024-01-15", 4.35)],
                frequency="Daily",
                rba_series_ids=["FIRMMBAB90D"],
            ),
            "inflation": _payload(
                concept="monthly_inflation",
                source="abs",
                dataset_id="CPI",
                series_id="cpi",
                observations=[("2024-01", 4.1), ("2024-02", 3.8)],
                frequency="Monthly",
                abs_key="3.10001.10.50.M",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-01", pytest.approx(0.25)),
        ("2024-02", pytest.approx(0.55)),
    ]


def test_real_business_lending_rate_intersects_monthly_periods() -> None:
    payload = derive_series(
        "real_business_lending_rate",
        {
            "lending_rate": _payload(
                concept="business_lending_rate",
                source="rba",
                dataset_id="f7",
                series_id="FLRMBSV",
                # RBA monthly series arrive as end-of-month ISO dates, not YYYY-MM,
                # so this must align with ABS YYYY-MM inflation by (year, month).
                observations=[("2024-01-31", 8.5), ("2024-02-29", 8.6)],
                frequency="Monthly",
                rba_series_ids=["FLRMBSV"],
            ),
            "inflation": _payload(
                concept="monthly_inflation",
                source="abs",
                dataset_id="CPI",
                series_id="cpi",
                observations=[("2024-01", 4.1), ("2024-03", 3.5)],
                frequency="Monthly",
                abs_key="3.10001.10.50.M",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-01-31", pytest.approx(4.4)),
    ]


def test_broad_money_growth_derives_year_ended_growth() -> None:
    payload = derive_series(
        "broad_money_growth",
        {
            "broad_money": _payload(
                concept="broad_money",
                source="rba",
                dataset_id="d3",
                series_id="DMABMS",
                # RBA monthly series arrive as end-of-month ISO dates, not YYYY-MM.
                observations=[("2023-01-31", 100.0), ("2024-01-31", 106.0)],
                frequency="Monthly",
                rba_series_ids=["DMABMS"],
            )
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-01-31", pytest.approx(6.0)),
    ]
    assert payload["metadata"]["derived"]["formula"] == (
        "100 * (broad_money_t / broad_money_t-12 - 1)"
    )


def test_employment_growth_derives_year_ended_growth() -> None:
    payload = derive_series(
        "employment_growth",
        {
            "employment": _payload(
                concept="employment",
                source="abs",
                dataset_id="LF",
                series_id="employment",
                observations=[("2023-05", 13000.0), ("2024-05", 13390.0)],
                frequency="Monthly",
                abs_key="employment-key",
            )
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-05", pytest.approx(3.0)),
    ]


def test_misery_index_sums_unemployment_and_inflation() -> None:
    payload = derive_series(
        "misery_index",
        {
            "unemployment_rate": _payload(
                concept="unemployment_rate",
                source="abs",
                dataset_id="LF",
                series_id="unemployment_rate",
                observations=[("2024-01", 4.1), ("2024-02", 4.0)],
                frequency="Monthly",
                abs_key="unemp-key",
            ),
            "inflation": _payload(
                concept="monthly_inflation",
                source="abs",
                dataset_id="CPI",
                series_id="cpi",
                observations=[("2024-01", 3.4), ("2024-03", 3.5)],
                frequency="Monthly",
                abs_key="3.10001.10.50.M",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert [(obs["date"], obs["value"]) for obs in payload["observations"]] == [
        ("2024-01", pytest.approx(7.5)),
    ]
    assert payload["series"][0]["unit"] == "percentage points"


def test_terms_of_trade_ratios_export_to_import_prices() -> None:
    payload = derive_series(
        "terms_of_trade",
        {
            "export_prices": _payload(
                concept="export_price_index",
                source="abs",
                dataset_id="ITPI_EXP",
                series_id="MEASURE=1|INDEX=8093697|FREQ=Q",
                observations=[("2025-Q4", 157.8), ("2026-Q1", 158.6)],
                frequency="Quarterly",
                unit="Index Numbers",
                abs_key="1.8093697.Q",
            ),
            "import_prices": _payload(
                concept="import_price_index",
                source="abs",
                dataset_id="ITPI_IMP",
                series_id="MEASURE=1|INDEX=6011001|FREQ=Q",
                observations=[("2025-Q4", 135.4), ("2026-Q1", 135.5)],
                frequency="Quarterly",
                unit="Index Numbers",
                abs_key="1.6011001.Q",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    values = [(obs["date"], obs["value"]) for obs in payload["observations"]]
    assert values == [
        ("2025-Q4", pytest.approx(116.543574)),
        ("2026-Q1", pytest.approx(117.047970)),
    ]
    assert payload["metadata"]["derived"]["formula"] == (
        "100 * export_price_index / import_price_index"
    )
    assert payload["series"][0]["unit"] == "index"


_VALID_ALIGNMENT_METHODS = {
    "locf",
    "exact_month",
    "period_intersection",
    "year_ended_lag",
}


def test_every_derived_concept_declares_a_valid_alignment_method() -> None:
    for name, spec in DERIVED_CONCEPTS.items():
        assert spec.alignment_method in _VALID_ALIGNMENT_METHODS, name


def test_terms_of_trade_metadata_carries_alignment_method() -> None:
    payload = derive_series(
        "terms_of_trade",
        {
            "export_prices": _payload(
                concept="export_price_index",
                source="abs",
                dataset_id="ITPI_EXP",
                series_id="MEASURE=1|INDEX=8093697|FREQ=Q",
                observations=[("2025-Q4", 157.8), ("2026-Q1", 158.6)],
                frequency="Quarterly",
                unit="Index Numbers",
                abs_key="1.8093697.Q",
            ),
            "import_prices": _payload(
                concept="import_price_index",
                source="abs",
                dataset_id="ITPI_IMP",
                series_id="MEASURE=1|INDEX=6011001|FREQ=Q",
                observations=[("2025-Q4", 135.4), ("2026-Q1", 135.5)],
                frequency="Quarterly",
                unit="Index Numbers",
                abs_key="1.6011001.Q",
            ),
        },
        requested_start=None,
        requested_end=None,
        last_n=None,
        server_version="test",
    )

    assert payload["metadata"]["derived"]["alignment_method"] == "period_intersection"


def test_derive_series_rejects_start_after_end() -> None:
    with pytest.raises(ValueError, match="start must be before or equal to end"):
        derive_series(
            "credit_growth",
            {
                "total_credit": _payload(
                    concept="total_credit",
                    source="rba",
                    dataset_id="d2",
                    series_id="DLCACS",
                    observations=[],
                    frequency="Monthly",
                    rba_series_ids=["DLCACS"],
                )
            },
            requested_start="2024-02",
            requested_end="2024-01",
            last_n=None,
            server_version="test",
        )

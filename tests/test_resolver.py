from pathlib import Path

import pytest

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.resolver import (
    CURATED_SHORTCUTS,
    build_abs_key,
    resolve,
    resolve_abs_dataflow_id,
    resolve_abs_structure_id,
    resolve_rba_csv_path,
)
from ausecon_mcp.parsers.abs_structure import parse_abs_structure

FIXTURES = Path(__file__).parent / "fixtures"


def _load_cpi_structure() -> dict:
    return parse_abs_structure((FIXTURES / "abs_cpi_structure.xml").read_text(encoding="utf-8"))


async def _cpi_fetcher(_dataflow_id: str) -> dict:
    return _load_cpi_structure()


@pytest.mark.asyncio
async def test_resolve_rejects_empty_concept() -> None:
    with pytest.raises(ValueError, match="concept"):
        await resolve("   ")


@pytest.mark.asyncio
async def test_resolve_rejects_unknown_concept() -> None:
    with pytest.raises(ValueError, match="Unknown concept"):
        await resolve("not_a_real_concept_xyz")


@pytest.mark.asyncio
async def test_resolve_rejects_ambiguous_alias() -> None:
    # "cpi" is an alias on both ABS CPI and RBA g1.
    with pytest.raises(ValueError, match="ambiguous"):
        await resolve("cpi")


@pytest.mark.asyncio
async def test_resolve_cash_rate_target_defaults_to_target_series() -> None:
    result = await resolve("cash_rate_target")

    assert result.source == "rba"
    assert result.dataset_id == "a2"
    assert result.rba_series_ids == ["ARBAMPCNCRT"]
    assert result.abs_key is None
    assert result.variant == "target"


@pytest.mark.asyncio
async def test_resolve_trimmed_mean_inflation_defaults_to_year_ended_series() -> None:
    result = await resolve("trimmed_mean_inflation")

    assert result.source == "rba"
    assert result.dataset_id == "g1"
    assert result.rba_series_ids == ["GCPIOCPMTMYP"]
    assert result.variant == "trimmed_mean"


@pytest.mark.asyncio
async def test_resolve_rba_variant_returns_populated_series_ids() -> None:
    result = await resolve("trimmed_mean_inflation", variant="headline")

    assert result.source == "rba"
    assert result.dataset_id == "g1"
    assert result.rba_series_ids == ["GCPIAG"]
    assert result.variant == "headline"


@pytest.mark.asyncio
async def test_resolve_removed_runtime_variant_is_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown variant"):
        await resolve("g3", variant="market")


@pytest.mark.asyncio
async def test_resolve_unknown_variant_raises_with_known_list() -> None:
    with pytest.raises(ValueError, match="Unknown variant"):
        await resolve("trimmed_mean_inflation", variant="monthly")


@pytest.mark.asyncio
async def test_resolve_frequency_validated_against_catalogue() -> None:
    with pytest.raises(ValueError, match="Frequency"):
        await resolve("trimmed_mean_inflation", frequency="D")


@pytest.mark.asyncio
async def test_resolve_geography_validated_against_catalogue() -> None:
    with pytest.raises(ValueError, match="Geography"):
        await resolve("trimmed_mean_inflation", geography="sydney")


@pytest.mark.asyncio
async def test_resolve_direct_dataset_id_matches_abs_entry() -> None:
    result = await resolve("ANA_AGG")

    assert result.source == "abs"
    assert result.dataset_id == "ANA_AGG"


@pytest.mark.asyncio
async def test_resolve_abs_without_key_inputs_returns_none_key() -> None:
    result = await resolve("headline_cpi")

    assert result.source == "abs"
    assert result.dataset_id == "CPI"
    assert result.abs_key == "1.10001.10.50.Q"
    assert result.variant == "headline"


@pytest.mark.asyncio
async def test_resolve_gdp_growth_defaults_to_real_gdp_qoq_key() -> None:
    result = await resolve("gdp_growth")

    assert result.source == "abs"
    assert result.dataset_id == "ANA_AGG"
    assert result.abs_key == "M2.GPM.20.AUS.Q"
    assert result.variant == "gdp_growth"


@pytest.mark.asyncio
async def test_resolve_abs_frequency_only_composes_against_structure() -> None:
    result = await resolve(
        "headline_cpi",
        frequency="Q",
        abs_structure_fetcher=_cpi_fetcher,
    )

    # Live CPI fixture order: MEASURE(1), INDEX(2), TSEST(3), REGION(4), FREQ(5).
    # The default headline variant already pins the intended semantic series.
    assert result.abs_key == "1.10001.10.50.Q"


@pytest.mark.asyncio
async def test_resolve_abs_structure_fetcher_required_for_composition() -> None:
    with pytest.raises(ValueError, match="abs_structure_fetcher"):
        await resolve("headline_cpi", frequency="Q")


def test_build_abs_key_orders_parts_by_dimension_position() -> None:
    structure = _load_cpi_structure()

    key = build_abs_key(
        structure,
        variant_fragment={"MEASURE": "1", "INDEX": "10001", "TSEST": "10"},
        frequency="Q",
        geography="national",
        geography_codes={"national": "50"},
    )

    assert key == "1.10001.10.50.Q"


def test_build_abs_key_strips_trailing_empty_slots() -> None:
    structure = _load_cpi_structure()

    key = build_abs_key(
        structure,
        variant_fragment={"MEASURE": "3"},
        frequency=None,
        geography=None,
        geography_codes={},
    )

    assert key == "3"


def test_build_abs_key_rejects_unknown_codelist_value() -> None:
    structure = _load_cpi_structure()

    with pytest.raises(ValueError, match="codelist"):
        build_abs_key(
            structure,
            variant_fragment={"MEASURE": "99"},
            frequency=None,
            geography=None,
            geography_codes={},
        )


def test_build_abs_key_maps_geography_through_entry_codes() -> None:
    structure = _load_cpi_structure()

    key = build_abs_key(
        structure,
        variant_fragment={"MEASURE": "1", "INDEX": "10001", "TSEST": "10"},
        frequency="Q",
        geography="national",
        geography_codes={"national": "50"},
    )

    assert key == "1.10001.10.50.Q"


def test_build_abs_key_rejects_unmapped_geography() -> None:
    structure = _load_cpi_structure()

    with pytest.raises(ValueError, match="No geography code"):
        build_abs_key(
            structure,
            variant_fragment={"MEASURE": "1", "INDEX": "10001", "TSEST": "10"},
            frequency=None,
            geography="darwin",
            geography_codes={"national": "50"},
        )


def test_resolve_abs_dataflow_id_passes_through_unknown_keys() -> None:
    assert resolve_abs_dataflow_id("NOT_IN_CATALOGUE") == "NOT_IN_CATALOGUE"


def test_resolve_abs_dataflow_id_returns_catalogue_key_when_no_upstream_id() -> None:
    key = next(iter(ABS_CATALOGUE))
    assert "upstream_id" not in ABS_CATALOGUE[key] or ABS_CATALOGUE[key].get("upstream_id") == key
    assert resolve_abs_dataflow_id(key) == ABS_CATALOGUE[key].get("upstream_id", key)


def test_resolve_abs_dataflow_id_returns_upstream_id_when_declared() -> None:
    ABS_CATALOGUE["__TEST__"] = {"upstream_id": "REAL_ID"}
    try:
        assert resolve_abs_dataflow_id("__TEST__") == "REAL_ID"
    finally:
        del ABS_CATALOGUE["__TEST__"]


def test_resolve_abs_structure_id_passes_through_unknown_keys() -> None:
    assert resolve_abs_structure_id("NOT_IN_CATALOGUE") == "NOT_IN_CATALOGUE"


def test_resolve_abs_structure_id_falls_back_to_dataflow_id_when_not_declared() -> None:
    assert resolve_abs_structure_id("CPI") == "CPI"


def test_resolve_abs_structure_id_returns_structure_id_for_lf_under() -> None:
    assert resolve_abs_structure_id("LF_UNDER") == "DS_LF_UNDER"


@pytest.mark.asyncio
async def test_resolve_lf_under_uses_mapped_structure_id_for_fetch() -> None:
    captured: list[str] = []

    async def fetcher(dataflow_id: str) -> dict:
        captured.append(dataflow_id)
        return {
            "id": dataflow_id,
            "dimensions": [
                {
                    "id": "MEASURE",
                    "position": 1,
                    "values": [{"code": "M23"}],
                },
                {"id": "FREQ", "position": 2, "values": [{"code": "M"}]},
            ],
        }

    await resolve("LF_UNDER", frequency="M", abs_structure_fetcher=fetcher)

    assert captured == ["DS_LF_UNDER"]


def test_resolve_rba_csv_path_defaults_to_id_pattern() -> None:
    assert resolve_rba_csv_path("unknown_id") == "unknown_id-data.csv"


def test_resolve_rba_csv_path_uses_explicit_csv_path_when_declared() -> None:
    RBA_CATALOGUE["__test__"] = {"csv_path": "custom-file.csv"}
    try:
        assert resolve_rba_csv_path("__test__") == "custom-file.csv"
    finally:
        del RBA_CATALOGUE["__test__"]


def test_curated_shortcuts_cover_current_semantic_concepts() -> None:
    assert set(CURATED_SHORTCUTS) == {
        "cash_rate_target",
        "headline_cpi",
        "trimmed_mean_inflation",
        "gdp_growth",
        "dwelling_approvals",
        # Tranche A
        "employment",
        "unemployment_rate",
        "participation_rate",
        "wage_growth",
        "trade_balance",
        "weighted_median_inflation",
        "monthly_inflation",
        "aud_usd",
        "trade_weighted_index",
        "government_bond_yield_3y",
        "government_bond_yield_10y",
        "housing_credit",
        # Tranche B
        "business_credit",
        "current_account_balance",
        "underemployment_rate",
        "hours_worked",
        "job_vacancies",
        "mortgage_rate",
        "business_lending_rate",
        "population",
        "inflation_expectations",
        "producer_price_inflation",
        "household_spending",
        "commodity_prices",
        # Tranche C
        "real_gdp",
        "nominal_gdp",
        "household_consumption",
        "private_investment",
        "retail_turnover",
        "broad_money",
        "bank_bill_rate",
    }


@pytest.mark.asyncio
async def test_resolve_dwelling_approvals_defaults_to_live_abs_key() -> None:
    result = await resolve("dwelling_approvals")

    assert result.source == "abs"
    assert result.dataset_id == "BUILDING_APPROVALS"
    assert result.variant == "headline_approvals"
    assert result.abs_key == "1.1.9.TOT.100.10.AUS.M"


TRANCHE_B_ABS = [
    ("current_account_balance", "BOP", "current_account", "1.100.20.Q"),
    ("underemployment_rate", "LF_UNDER", "headline_underemployment", "M23.3.1599.20.AUS.M"),
    ("hours_worked", "LF_HOURS", "headline_hours", "M18.3.1599.TOT.20.AUS.M"),
    ("job_vacancies", "JV", "headline_vacancies", "M1.7.TOT.20.AUS.Q"),
    ("population", "ERP_Q", "headline_population", "1.3.TOT.AUS.Q"),
    ("producer_price_inflation", "PPI_FD", "producer", "3.TOT.TOT.TOTXE.Q"),
    ("household_spending", "HSI_M", "headline_spending", "7.TOT.CUR.20.AUS.M"),
]

TRANCHE_B_RBA = [
    ("business_credit", "d2", "business", ["DLCACBS"]),
    ("mortgage_rate", "f6", "owner_occupier_variable", ["FLRHOOVA"]),
    ("business_lending_rate", "f7", "small_business_indicator", ["FLRBFOSBT"]),
    ("inflation_expectations", "g3", "consumer", ["GCONEXP"]),
    ("commodity_prices", "i2", "rba_commodity_index", ["GRCPAISDR"]),
]

TRANCHE_C_ABS = [
    ("real_gdp", "ANA_AGG", "real_gdp", "M1.GPM.20.AUS.Q"),
    ("nominal_gdp", "ANA_AGG", "nominal_gdp", "M3.GPM.20.AUS.Q"),
    ("household_consumption", "ANA_EXP", "household_consumption", "VCH.FCE.PHS.20.AUS.Q"),
    ("private_investment", "ANA_EXP", "private_investment", "VCH.GFC_PBI.PSS.20.AUS.Q"),
    ("retail_turnover", "RT", "headline_turnover", "M1.20.20.AUS.M"),
]

TRANCHE_C_RBA = [
    ("broad_money", "d3", "broad_money", ["DMABMS"]),
    ("bank_bill_rate", "f1", "bank_bills_3m", ["FIRMMBAB90D"]),
]


@pytest.mark.parametrize(("concept", "dataset_id", "variant", "abs_key"), TRANCHE_B_ABS)
@pytest.mark.asyncio
async def test_resolve_tranche_b_abs_concepts(
    concept: str, dataset_id: str, variant: str, abs_key: str
) -> None:
    result = await resolve(concept)
    assert result.source == "abs"
    assert result.dataset_id == dataset_id
    assert result.variant == variant
    assert result.abs_key == abs_key


@pytest.mark.parametrize(("concept", "dataset_id", "variant", "series_ids"), TRANCHE_B_RBA)
@pytest.mark.asyncio
async def test_resolve_tranche_b_rba_concepts(
    concept: str, dataset_id: str, variant: str, series_ids: list[str]
) -> None:
    result = await resolve(concept)
    assert result.source == "rba"
    assert result.dataset_id == dataset_id
    assert result.variant == variant
    assert result.rba_series_ids == series_ids


@pytest.mark.parametrize(("concept", "dataset_id", "variant", "abs_key"), TRANCHE_C_ABS)
@pytest.mark.asyncio
async def test_resolve_tranche_c_abs_concepts(
    concept: str, dataset_id: str, variant: str, abs_key: str
) -> None:
    result = await resolve(concept)
    assert result.source == "abs"
    assert result.dataset_id == dataset_id
    assert result.variant == variant
    assert result.abs_key == abs_key


@pytest.mark.parametrize(("concept", "dataset_id", "variant", "series_ids"), TRANCHE_C_RBA)
@pytest.mark.asyncio
async def test_resolve_tranche_c_rba_concepts(
    concept: str, dataset_id: str, variant: str, series_ids: list[str]
) -> None:
    result = await resolve(concept)
    assert result.source == "rba"
    assert result.dataset_id == dataset_id
    assert result.variant == variant
    assert result.rba_series_ids == series_ids


TRANCHE_A_ABS = [
    ("employment", "LF", "employment", "M3.3.1599.20.AUS.M"),
    ("unemployment_rate", "LF", "unemployment_rate", "M13.3.1599.20.AUS.M"),
    ("participation_rate", "LF", "participation_rate", "M12.3.1599.20.AUS.M"),
    ("wage_growth", "WPI", "headline_wpi", "3.THRPEB.7.TOT.20.AUS.Q"),
    ("trade_balance", "ITGS", "trade_balance", "M1.170.20.AUS.M"),
]

TRANCHE_A_RBA = [
    ("weighted_median_inflation", "g1", "weighted_median", ["GCPIOCPMWMYP"]),
    ("monthly_inflation", "g4", "headline_monthly", ["GCPIAGSAMP"]),
    ("aud_usd", "f11", "aud_usd", ["FXRUSD"]),
    ("trade_weighted_index", "f11", "twi", ["FXRTWI"]),
    ("government_bond_yield_3y", "f17", "ags_3y", ["FZCY300D"]),
    ("government_bond_yield_10y", "f17", "ags_10y", ["FZCY1000D"]),
    ("housing_credit", "d2", "housing", ["DLCACOHS", "DLCACIHS"]),
]


@pytest.mark.parametrize(("concept", "dataset_id", "variant", "abs_key"), TRANCHE_A_ABS)
@pytest.mark.asyncio
async def test_resolve_tranche_a_abs_concepts(
    concept: str, dataset_id: str, variant: str, abs_key: str
) -> None:
    result = await resolve(concept)
    assert result.source == "abs"
    assert result.dataset_id == dataset_id
    assert result.variant == variant
    assert result.abs_key == abs_key


@pytest.mark.parametrize(("concept", "dataset_id", "variant", "series_ids"), TRANCHE_A_RBA)
@pytest.mark.asyncio
async def test_resolve_tranche_a_rba_concepts(
    concept: str, dataset_id: str, variant: str, series_ids: list[str]
) -> None:
    result = await resolve(concept)
    assert result.source == "rba"
    assert result.dataset_id == dataset_id
    assert result.variant == variant
    assert result.rba_series_ids == series_ids

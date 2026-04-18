from pathlib import Path

import pytest

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.resolver import (
    CURATED_SHORTCUTS,
    build_abs_key,
    resolve,
    resolve_abs_dataflow_id,
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
async def test_resolve_rba_unpopulated_variant_raises() -> None:
    with pytest.raises(ValueError, match="rba_series_ids populated"):
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


def test_resolve_rba_csv_path_defaults_to_id_pattern() -> None:
    assert resolve_rba_csv_path("unknown_id") == "unknown_id-data.csv"


def test_resolve_rba_csv_path_uses_explicit_csv_path_when_declared() -> None:
    RBA_CATALOGUE["__test__"] = {"csv_path": "custom-file.csv"}
    try:
        assert resolve_rba_csv_path("__test__") == "custom-file.csv"
    finally:
        del RBA_CATALOGUE["__test__"]


def test_curated_shortcuts_cover_v0110_tranche_a_concepts() -> None:
    assert set(CURATED_SHORTCUTS) == {
        "cash_rate_target",
        "headline_cpi",
        "trimmed_mean_inflation",
        "gdp_growth",
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
    }


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

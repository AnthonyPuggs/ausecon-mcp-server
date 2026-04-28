import re

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.search import search_catalogue

VALID_FREQUENCY_CODES = {"D", "M", "Q", "A", "E"}
SDMX_LITERAL_KEY_PATTERN = re.compile(r"^[0-9A-Z_+]+(\.[0-9A-Z_+]+)*$")
SDMX_FRAGMENT_PATTERN = re.compile(
    r"^[A-Z_][A-Z0-9_]*=[0-9A-Z_+]+(;[A-Z_][A-Z0-9_]*=[0-9A-Z_+]+)*$"
)
SDMX_KEY_PATTERN = re.compile(
    f"(?:{SDMX_LITERAL_KEY_PATTERN.pattern})|(?:{SDMX_FRAGMENT_PATTERN.pattern})"
)


def test_abs_catalogue_covers_core_discovery_domains() -> None:
    assert len(ABS_CATALOGUE) >= 30
    assert {
        "prices_inflation",
        "labour",
        "national_accounts",
        "activity",
        "housing_construction",
        "external_sector",
        "credit_finance",
        "demographics",
    } <= {entry["category"] for entry in ABS_CATALOGUE.values()}
    assert all(entry["tags"] for entry in ABS_CATALOGUE.values())


def test_rba_catalogue_covers_active_tables_and_tracks_discontinued_state() -> None:
    active_tables = [
        entry for entry in RBA_CATALOGUE.values() if not entry.get("discontinued", False)
    ]

    assert len(active_tables) >= 30
    assert {
        "monetary_policy",
        "payments",
        "money_credit",
        "interest_rates",
        "exchange_rates",
        "inflation",
        "output_labour",
        "external_sector",
        "household_finance",
    } <= {entry["category"] for entry in RBA_CATALOGUE.values()}
    assert all(entry["tags"] for entry in RBA_CATALOGUE.values())


def test_search_catalogue_prefers_high_value_alias_matches() -> None:
    results = search_catalogue("trimmed mean inflation")

    assert results
    assert results[0]["source"] == "rba"
    assert results[0]["id"] == "g1"


def test_search_catalogue_respects_source_filter() -> None:
    results = search_catalogue("cash rate", source="abs")

    assert results == []


def test_search_catalogue_prioritises_exact_table_id_matches() -> None:
    results = search_catalogue("f6")

    assert results
    assert results[0]["source"] == "rba"
    assert results[0]["id"] == "f6"


def test_search_catalogue_prefers_full_economist_query_matches() -> None:
    results = search_catalogue("unemployment rate")

    assert results
    assert results[0]["source"] == "abs"
    assert results[0]["id"] == "LF"


def test_search_catalogue_handles_common_real_gdp_phrase() -> None:
    results = search_catalogue("real gdp")

    assert results
    assert results[0]["source"] == "abs"
    assert results[0]["id"] == "ANA_AGG"


def test_search_catalogue_excludes_ceased_abs_dataflows() -> None:
    for ceased_id in ("BUSINESS_TURNOVER", "CPI_M", "RPPI"):
        results = search_catalogue(ceased_id, source="abs")
        assert all(item["id"] != ceased_id for item in results), (
            f"{ceased_id} is marked ceased but still appeared in search results"
        )


def test_search_catalogue_returns_reactivated_retail_trade() -> None:
    results = search_catalogue("retail trade", source="abs")

    assert results
    assert results[0]["id"] == "RT"


def test_slci_resolves_to_selected_living_cost_indexes() -> None:
    entry = ABS_CATALOGUE["SLCI"]

    assert entry["name"] == "Selected Living Cost Indexes"
    assert "selected living cost indexes" in entry["aliases"]
    assert entry["category"] == "prices_inflation"


def test_every_catalogue_entry_declares_resolver_schema_fields() -> None:
    for entry in (*ABS_CATALOGUE.values(), *RBA_CATALOGUE.values()):
        assert isinstance(entry.get("frequencies"), list), entry["id"]
        assert entry["frequencies"], f"{entry['id']}: frequencies must not be empty"
        assert set(entry["frequencies"]) <= VALID_FREQUENCY_CODES, entry["id"]

        assert isinstance(entry.get("geographies"), list), entry["id"]
        assert entry["geographies"], f"{entry['id']}: geographies must not be empty"

        assert isinstance(entry.get("variants"), list), entry["id"]


def test_abs_variants_carry_name_aliases_and_wired_sdmx_key() -> None:
    for entry in ABS_CATALOGUE.values():
        for variant in entry["variants"]:
            assert isinstance(variant.get("name"), str) and variant["name"], entry["id"]
            assert isinstance(variant.get("aliases"), list), entry["id"]
            assert "abs_key" in variant, f"{entry['id']}/{variant['name']}"
            key = variant["abs_key"]
            assert isinstance(key, str) and SDMX_KEY_PATTERN.match(key), (
                f"{entry['id']}/{variant['name']}: {key!r} is not a valid wired SDMX key"
            )


def test_rba_variants_carry_name_aliases_and_wired_series_ids() -> None:
    for entry in RBA_CATALOGUE.values():
        for variant in entry["variants"]:
            assert isinstance(variant.get("name"), str) and variant["name"], entry["id"]
            assert isinstance(variant.get("aliases"), list), entry["id"]
            assert "rba_series_ids" in variant, f"{entry['id']}/{variant['name']}"
            series_ids = variant["rba_series_ids"]
            assert isinstance(series_ids, list) and series_ids, (
                f"{entry['id']}/{variant['name']}: rba_series_ids must be wired and non-empty"
            )
            assert all(isinstance(s, str) and s for s in series_ids), (
                f"{entry['id']}/{variant['name']}: all series ids must be non-empty strings"
            )


def test_building_approvals_entry_has_wired_default_variant() -> None:
    entry = ABS_CATALOGUE["BUILDING_APPROVALS"]

    assert entry["name"] == "Building Approvals"
    assert entry["frequency"] == "Monthly"
    assert entry["category"] == "housing_construction"
    assert entry["variants"] == [
        {
            "name": "headline_approvals",
            "aliases": ["dwelling approvals", "residential approvals"],
            "abs_key": "1.1.9.TOT.100.10.AUS.M",
        }
    ]

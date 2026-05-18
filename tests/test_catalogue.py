import re

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.search import list_catalogue

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


def test_apra_catalogue_covers_v14_source_native_publications() -> None:
    assert set(APRA_CATALOGUE) == {
        "ADI_MONTHLY",
        "ADI_QUARTERLY_PERFORMANCE",
        "ADI_QUARTERLY_CENTRALISED",
        "ADI_PROPERTY_EXPOSURES",
        "APRA_SUPER_INDUSTRY",
        "APRA_SUPER_FUND_LEVEL",
        "APRA_GENERAL_INSURANCE_PERFORMANCE",
        "APRA_LIFE_INSURANCE_PERFORMANCE",
        "APRA_PHI_PERFORMANCE",
        "APRA_PHI_MEMBERSHIP",
    }
    assert all(
        entry["landing_url"].startswith("https://www.apra.gov.au/")
        for entry in APRA_CATALOGUE.values()
    )
    assert all(entry["link_patterns"] for entry in APRA_CATALOGUE.values())
    assert all(entry["tables"] for entry in APRA_CATALOGUE.values())


def test_list_catalogue_returns_apra_entries_when_source_filtered() -> None:
    results = list_catalogue(source="apra")

    assert [item["source"] for item in results] == ["apra"] * len(APRA_CATALOGUE)
    assert {item["id"] for item in results} == set(APRA_CATALOGUE)


def test_slci_resolves_to_selected_living_cost_indexes() -> None:
    entry = ABS_CATALOGUE["SLCI"]

    assert entry["name"] == "Selected Living Cost Indexes"
    assert "selected living cost indexes" in entry["aliases"]
    assert entry["category"] == "prices_inflation"


def test_every_catalogue_entry_declares_resolver_schema_fields() -> None:
    for entry in (*ABS_CATALOGUE.values(), *RBA_CATALOGUE.values(), *APRA_CATALOGUE.values()):
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


def test_apra_variants_carry_table_and_series_ids() -> None:
    for entry in APRA_CATALOGUE.values():
        for variant in entry["variants"]:
            assert isinstance(variant.get("name"), str) and variant["name"], entry["id"]
            assert isinstance(variant.get("aliases"), list), entry["id"]
            assert variant.get("apra_table_id") in entry["tables"], (
                f"{entry['id']}/{variant['name']}: apra_table_id must reference a table"
            )
            series_ids = variant.get("apra_series_ids")
            assert isinstance(series_ids, list) and series_ids, (
                f"{entry['id']}/{variant['name']}: apra_series_ids must be wired"
            )
            assert all(isinstance(s, str) and s for s in series_ids), (
                f"{entry['id']}/{variant['name']}: all APRA series ids must be non-empty"
            )


def test_hsi_q_entry_exposes_current_and_volume_variants() -> None:
    entry = ABS_CATALOGUE["HSI_Q"]

    assert entry["name"] == "Quarterly Household Spending Indicator"
    assert entry["frequency"] == "Quarterly"
    assert entry["category"] == "activity"
    assert entry["variants"] == [
        {
            "name": "current_price_total",
            "aliases": ["quarterly household spending", "current price household spending"],
            "abs_key": "7.TOT.CUR.20.AUS.Q",
        },
        {
            "name": "chain_volume_total",
            "aliases": ["real household spending", "volume household spending"],
            "abs_key": "7.TOT.CVM.20.AUS.Q",
        },
    ]


def test_selected_rba_expansion_tables_are_catalogued_with_csv_paths() -> None:
    expected = {
        "f1.1": "f1.1-data.csv",
        "f2.1": "f2.1-data.csv",
        "a4": "a4-data.csv",
        "i5": "i5-data.csv",
        "j1": "j1-gdp-growth.csv",
        "d14.1": "d14.1-data.csv",
        "c1.1": "c1.1-aggregate.csv",
        "c2.1": "c2.1-aggregate.csv",
        "c4.1": "c4.1-data.csv",
    }

    for table_id, csv_path in expected.items():
        assert RBA_CATALOGUE[table_id]["csv_path"] == csv_path


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

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.search import search_catalogue


def test_abs_catalogue_covers_core_discovery_domains() -> None:
    assert len(ABS_CATALOGUE) >= 12
    assert {
        "prices_inflation",
        "labour",
        "national_accounts",
        "activity",
        "housing_construction",
        "external_sector",
        "credit_finance",
    } <= {entry["category"] for entry in ABS_CATALOGUE.values()}
    assert all(entry["tags"] for entry in ABS_CATALOGUE.values())


def test_rba_catalogue_covers_active_tables_and_tracks_discontinued_state() -> None:
    active_tables = [
        entry for entry in RBA_CATALOGUE.values() if not entry.get("discontinued", False)
    ]

    assert len(active_tables) >= 12
    assert any(entry.get("discontinued", False) for entry in RBA_CATALOGUE.values())
    assert {
        "monetary_policy",
        "payments",
        "money_credit",
        "interest_rates",
        "exchange_rates",
        "inflation",
        "output_labour",
        "external_sector",
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


def test_search_catalogue_excludes_discontinued_rba_tables() -> None:
    results = search_catalogue("producer price indicators", source="rba")

    assert results == []

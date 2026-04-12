from ausecon_mcp.catalogue.search import search_catalogue


def test_search_catalogue_prefers_high_value_alias_matches() -> None:
    results = search_catalogue("trimmed mean inflation")

    assert results
    assert results[0]["source"] == "rba"
    assert results[0]["id"] == "g1"


def test_search_catalogue_respects_source_filter() -> None:
    results = search_catalogue("cash rate", source="abs")

    assert results == []

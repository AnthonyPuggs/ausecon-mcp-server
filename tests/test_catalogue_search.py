from ausecon_mcp.catalogue.search import search_catalogue


def test_search_catalogue_prefers_high_value_alias_matches() -> None:
    results = search_catalogue("trimmed mean inflation")

    assert results
    assert results[0]["source"] == "rba"
    assert results[0]["id"] == "g1"


def test_search_catalogue_respects_source_filter() -> None:
    results = search_catalogue("cash rate", source="abs")

    assert results == []


def test_search_catalogue_returns_apra_entries_when_source_filtered() -> None:
    results = search_catalogue("property exposures", source="apra")

    assert results
    assert results[0]["source"] == "apra"
    assert results[0]["id"] == "ADI_PROPERTY_EXPOSURES"


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


def test_search_catalogue_excludes_ceased_retail_trade() -> None:
    # The ABS discontinued Retail Trade after the June 2025 reference month; the
    # entry stays retrievable via the retail_turnover concept but is hidden from
    # default discovery like other ceased dataflows.
    results = search_catalogue("retail trade", source="abs")

    assert all(item["id"] != "RT" for item in results)


def test_list_catalogue_surfaces_ceased_retail_trade_on_request() -> None:
    from ausecon_mcp.catalogue.search import list_catalogue

    default_ids = {item["id"] for item in list_catalogue(source="abs")}
    ceased_ids = {item["id"] for item in list_catalogue(source="abs", include_ceased=True)}

    assert "RT" not in default_ids
    assert "RT" in ceased_ids

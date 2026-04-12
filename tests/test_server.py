import pytest

from ausecon_mcp.server import AuseconService


class StubABSProvider:
    async def get_dataset_structure(self, dataflow_id: str) -> dict:
        return {"id": dataflow_id, "dimensions": [{"id": "MEASURE"}]}

    async def get_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict:
        return {
            "metadata": {"source": "abs", "dataset_id": dataflow_id},
            "series": [{"series_id": "abs-series"}],
            "observations": [{"date": "2024-Q1", "series_id": "abs-series", "value": 4.1}],
        }


class StubRBAProvider:
    def list_tables(
        self,
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        del include_discontinued
        tables = [
            {
                "id": "a2",
                "name": "Changes in Monetary Policy and Administered Rates",
                "category": "monetary_policy",
            },
            {"id": "g1", "name": "Consumer Price Inflation", "category": "inflation"},
        ]
        if category is None:
            return tables
        return [table for table in tables if table["category"] == category]

    async def get_table(
        self,
        table_id: str,
        series_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        last_n: int | None = None,
    ) -> dict:
        return {
            "metadata": {"source": "rba", "dataset_id": table_id},
            "series": [{"series_id": "rba-series"}],
            "observations": [{"date": "2024-01-01", "series_id": "rba-series", "value": 4.35}],
        }


@pytest.mark.asyncio
async def test_service_searches_curated_catalogue() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    results = await service.search_datasets("cash rate")

    assert results[0]["id"] == "a2"


@pytest.mark.asyncio
async def test_service_lists_rba_tables() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    results = await service.list_rba_tables(category="inflation")

    assert results == [{"id": "g1", "name": "Consumer Price Inflation", "category": "inflation"}]


@pytest.mark.asyncio
async def test_service_resolves_curated_economic_series() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    result = await service.get_economic_series("cash_rate_target")

    assert result["metadata"]["dataset_id"] == "a2"


@pytest.mark.asyncio
async def test_service_fetches_abs_data() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    result = await service.get_abs_data("CPI", start_period="2024-Q1")

    assert result["metadata"]["dataset_id"] == "CPI"


@pytest.mark.asyncio
async def test_service_rejects_unknown_economic_series_concept() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unsupported concept"):
        await service.get_economic_series("unknown_series")


@pytest.mark.asyncio
async def test_service_rejects_unsupported_economic_series_options() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unsupported semantic options"):
        await service.get_economic_series("cash_rate_target", variant="monthly")


@pytest.mark.asyncio
async def test_service_rejects_empty_search_query() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="query"):
        await service.search_datasets("   ")


@pytest.mark.asyncio
async def test_service_rejects_unknown_search_source() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="source"):
        await service.search_datasets("cash rate", source="fred")


@pytest.mark.asyncio
async def test_service_rejects_empty_abs_key() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="key"):
        await service.get_abs_data("CPI", key=" ")


@pytest.mark.asyncio
async def test_service_rejects_non_positive_abs_last_n() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="last_n"):
        await service.get_abs_data("CPI", last_n=0)


@pytest.mark.asyncio
async def test_service_rejects_invalid_abs_period_format() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="start_period"):
        await service.get_abs_data("CPI", start_period="2024-13")


@pytest.mark.asyncio
async def test_service_rejects_mixed_abs_period_bounds() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="same frequency"):
        await service.get_abs_data("CPI", start_period="2024-Q1", end_period="2024-06")


@pytest.mark.asyncio
async def test_service_rejects_non_positive_rba_last_n() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="last_n"):
        await service.get_rba_table("g1", last_n=0)


@pytest.mark.asyncio
async def test_service_rejects_empty_rba_series_ids() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="series_ids"):
        await service.get_rba_table("g1", series_ids=["GCPIAGYP", " "])


@pytest.mark.asyncio
async def test_service_rejects_invalid_rba_iso_dates() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="start_date"):
        await service.get_rba_table("g1", start_date="2024/01/01")


@pytest.mark.asyncio
async def test_service_rejects_invalid_semantic_rba_dates_after_resolution() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="ISO"):
        await service.get_economic_series("cash_rate_target", start="2024-Q1")


@pytest.mark.asyncio
async def test_service_rejects_invalid_semantic_abs_periods_after_resolution() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="ABS period"):
        await service.get_economic_series("headline_cpi", start="2024/01")


@pytest.mark.asyncio
async def test_service_rejects_empty_abs_dataset_structure_id() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="dataflow_id"):
        await service.get_abs_dataset_structure(" ")


@pytest.mark.asyncio
async def test_service_rejects_unknown_rba_category() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="category"):
        await service.list_rba_tables(category="housing")

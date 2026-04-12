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

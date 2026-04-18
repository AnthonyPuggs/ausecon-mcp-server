import pytest
from fastmcp import Client

from ausecon_mcp.server import AuseconService, build_server


class StubABSProvider:
    def __init__(self) -> None:
        self.last_get_data_kwargs: dict | None = None

    async def get_dataset_structure(self, dataflow_id: str) -> dict:
        return {
            "id": dataflow_id,
            "dimensions": [
                {"id": "MEASURE", "position": 1, "values": [{"code": "1"}, {"code": "3"}]},
                {"id": "INDEX", "position": 2, "values": [{"code": "10001"}, {"code": "999902"}]},
                {"id": "TSEST", "position": 3, "values": [{"code": "10"}, {"code": "20"}]},
                {"id": "REGION", "position": 4, "values": [{"code": "50"}, {"code": "AUS"}]},
                {"id": "FREQ", "position": 5, "values": [{"code": "Q"}, {"code": "M"}]},
            ],
        }

    async def get_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict:
        self.last_get_data_kwargs = {
            "dataflow_id": dataflow_id,
            "key": key,
            "start_period": start_period,
            "end_period": end_period,
            "last_n": last_n,
            "updated_after": updated_after,
        }
        return {
            "metadata": {"source": "abs", "dataset_id": dataflow_id},
            "series": [{"series_id": "abs-series"}],
            "observations": [{"date": "2024-Q1", "series_id": "abs-series", "value": 4.1}],
        }


class StubRBAProvider:
    def __init__(self) -> None:
        self.last_get_table_kwargs: dict | None = None

    def list_tables(
        self,
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        tables = [
            {
                "id": "a2",
                "name": "Changes in Monetary Policy and Administered Rates",
                "category": "monetary_policy",
                "frequency": "Event-driven",
                "discontinued": False,
            },
            {
                "id": "g1",
                "name": "Consumer Price Inflation",
                "category": "inflation",
                "frequency": "Quarterly",
                "discontinued": False,
            },
            {
                "id": "g3",
                "name": "Producer and Import Prices",
                "category": "inflation",
                "frequency": "Quarterly",
                "discontinued": True,
            },
        ]
        if not include_discontinued:
            tables = [table for table in tables if not table["discontinued"]]
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
        csv_path: str | None = None,
    ) -> dict:
        self.last_get_table_kwargs = {
            "table_id": table_id,
            "series_ids": series_ids,
            "start_date": start_date,
            "end_date": end_date,
            "last_n": last_n,
            "csv_path": csv_path,
        }
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

    assert results == [
        {
            "id": "g1",
            "name": "Consumer Price Inflation",
            "category": "inflation",
            "frequency": "Quarterly",
            "discontinued": False,
        }
    ]


@pytest.mark.asyncio
async def test_service_lists_rba_tables_with_discontinued_entries() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    results = await service.list_rba_tables(category="inflation", include_discontinued=True)

    assert [item["id"] for item in results] == ["g1", "g3"]
    assert results[-1]["discontinued"] is True


@pytest.mark.asyncio
async def test_service_resolves_curated_economic_series() -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    result = await service.get_economic_series("cash_rate_target")

    assert result["metadata"]["dataset_id"] == "a2"
    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["series_ids"] == ["ARBAMPCNCRT"]


@pytest.mark.asyncio
async def test_service_fetches_abs_data() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    result = await service.get_abs_data("CPI", start_period="2024-Q1")

    assert result["metadata"]["dataset_id"] == "CPI"


@pytest.mark.asyncio
async def test_service_rejects_unknown_economic_series_concept() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unknown concept"):
        await service.get_economic_series("unknown_series")


@pytest.mark.asyncio
async def test_service_rejects_unknown_variant_for_concept() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unknown variant"):
        await service.get_economic_series("trimmed_mean_inflation", variant="monthly")


@pytest.mark.asyncio
async def test_service_forwards_rba_series_ids_for_resolved_variant() -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series("trimmed_mean_inflation", variant="headline")

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == "g1"
    assert rba.last_get_table_kwargs["series_ids"] == ["GCPIAG"]


@pytest.mark.asyncio
async def test_service_forwards_default_rba_series_ids_for_trimmed_mean() -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series("trimmed_mean_inflation")

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == "g1"
    assert rba.last_get_table_kwargs["series_ids"] == ["GCPIOCPMTMYP"]


@pytest.mark.asyncio
async def test_service_forwards_abs_key_composed_from_frequency() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series("headline_cpi", frequency="Q")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "CPI"
    assert abs_provider.last_get_data_kwargs["key"] == "1.10001.10.50.Q"


@pytest.mark.asyncio
async def test_service_forwards_default_abs_key_for_headline_cpi() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series("headline_cpi")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "CPI"
    assert abs_provider.last_get_data_kwargs["key"] == "1.10001.10.50.Q"


@pytest.mark.asyncio
async def test_service_forwards_default_abs_key_for_gdp_growth() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series("gdp_growth")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "ANA_AGG"
    assert abs_provider.last_get_data_kwargs["key"] == "M2.GPM.20.AUS.Q"


@pytest.mark.asyncio
async def test_service_rejects_unpopulated_rba_variant() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="rba_series_ids populated"):
        await service.get_economic_series("trimmed_mean_inflation", variant="weighted_median")


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


async def test_service_resolves_rba_csv_path_before_calling_provider() -> None:
    rba_provider = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba_provider)

    await service.get_rba_table("f17")

    assert rba_provider.last_get_table_kwargs is not None
    assert rba_provider.last_get_table_kwargs["csv_path"] == "f17-yields.csv"


async def test_service_defaults_rba_csv_path_when_not_declared() -> None:
    rba_provider = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba_provider)

    await service.get_rba_table("f16")

    assert rba_provider.last_get_table_kwargs is not None
    assert rba_provider.last_get_table_kwargs["csv_path"] == "f16-data.csv"


async def test_service_resolves_abs_upstream_id_before_calling_provider() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_abs_data("LABOUR_ACCT_A", start_period="2023")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "ABS_LABOUR_ACCT"


async def test_service_passes_through_dataflow_id_when_no_upstream_id_declared() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_abs_data("CPI")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "CPI"


async def test_registered_tools_carry_readonly_and_openworld_annotations() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = await client.list_tools()

    assert tools, "expected at least one tool registered"
    for tool in tools:
        annotations = tool.annotations
        assert annotations is not None, f"{tool.name} has no annotations"
        assert annotations.readOnlyHint is True, f"{tool.name} missing readOnlyHint"
        assert annotations.openWorldHint is True, f"{tool.name} missing openWorldHint"

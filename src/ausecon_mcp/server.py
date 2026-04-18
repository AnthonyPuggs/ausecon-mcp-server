from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ausecon_mcp.catalogue.resolver import (
    resolve,
    resolve_abs_dataflow_id,
    resolve_rba_csv_path,
)
from ausecon_mcp.catalogue.search import search_catalogue
from ausecon_mcp.logging import configure_logging, get_logger
from ausecon_mcp.prompts import register_prompts
from ausecon_mcp.providers.abs import ABSProvider
from ausecon_mcp.providers.rba import RBAProvider
from ausecon_mcp.resources import register_resources
from ausecon_mcp.validation import (
    require_non_empty,
    validate_abs_period_range,
    validate_iso_date_range,
    validate_iso_datetime,
    validate_positive_int,
    validate_rba_category,
    validate_search_query,
    validate_series_ids,
    validate_source,
)


class AuseconService:
    def __init__(
        self,
        abs_provider: ABSProvider | Any | None = None,
        rba_provider: RBAProvider | Any | None = None,
    ) -> None:
        self.abs_provider = abs_provider or ABSProvider()
        self.rba_provider = rba_provider or RBAProvider()

    async def search_datasets(self, query: str, source: str | None = None) -> list[dict]:
        validated_query = validate_search_query(query)
        validated_source = validate_source(source)
        return search_catalogue(validated_query, source=validated_source)

    async def get_abs_dataset_structure(self, dataflow_id: str) -> dict:
        validated_dataflow_id = require_non_empty("dataflow_id", dataflow_id)
        upstream_id = resolve_abs_dataflow_id(validated_dataflow_id)
        return await self.abs_provider.get_dataset_structure(upstream_id)

    async def get_abs_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict:
        validated_dataflow_id = require_non_empty("dataflow_id", dataflow_id)
        validated_key = require_non_empty("key", key)
        validated_start_period, validated_end_period = validate_abs_period_range(
            start_period,
            end_period,
            start_name="start_period",
            end_name="end_period",
        )
        validated_last_n = validate_positive_int("last_n", last_n)
        validated_updated_after = validate_iso_datetime("updated_after", updated_after)
        upstream_id = resolve_abs_dataflow_id(validated_dataflow_id)
        return await self.abs_provider.get_data(
            dataflow_id=upstream_id,
            key=validated_key,
            start_period=validated_start_period,
            end_period=validated_end_period,
            last_n=validated_last_n,
            updated_after=validated_updated_after,
        )

    async def list_rba_tables(
        self,
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        validated_category = validate_rba_category(category)
        return self.rba_provider.list_tables(
            category=validated_category,
            include_discontinued=include_discontinued,
        )

    async def get_rba_table(
        self,
        table_id: str,
        series_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        last_n: int | None = None,
    ) -> dict:
        validated_table_id = require_non_empty("table_id", table_id)
        validated_series_ids = validate_series_ids(series_ids)
        validated_start_date, validated_end_date = validate_iso_date_range(
            start_date,
            end_date,
            start_name="start_date",
            end_name="end_date",
        )
        validated_last_n = validate_positive_int("last_n", last_n)
        csv_path = resolve_rba_csv_path(validated_table_id)
        return await self.rba_provider.get_table(
            table_id=validated_table_id,
            series_ids=validated_series_ids,
            start_date=validated_start_date,
            end_date=validated_end_date,
            last_n=validated_last_n,
            csv_path=csv_path,
        )

    async def get_economic_series(
        self,
        concept: str,
        variant: str | None = None,
        geography: str | None = None,
        frequency: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict:
        validated_concept = require_non_empty("concept", concept)
        resolved = await resolve(
            validated_concept,
            variant=variant,
            geography=geography,
            frequency=frequency,
            abs_structure_fetcher=self.abs_provider.get_dataset_structure,
        )

        if resolved.source == "rba":
            validated_start, validated_end = validate_iso_date_range(
                start,
                end,
                start_name="start",
                end_name="end",
            )
            return await self.get_rba_table(
                resolved.dataset_id,
                series_ids=resolved.rba_series_ids,
                start_date=validated_start,
                end_date=validated_end,
                last_n=None,
            )

        validated_start, validated_end = validate_abs_period_range(
            start,
            end,
            start_name="start",
            end_name="end",
        )
        return await self.get_abs_data(
            resolved.dataset_id,
            key=resolved.abs_key or "all",
            start_period=validated_start,
            end_period=validated_end,
        )


def build_server(service: AuseconService | None = None) -> FastMCP:
    app_service = service or AuseconService()
    mcp = FastMCP(
        "ausecon",
        instructions=(
            "Australian economic data tools for ABS and RBA datasets. "
            "Use search_datasets first when the user does not know the exact dataset or table."
        ),
    )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def search_datasets(query: str, source: str | None = None) -> list[dict]:
        """Search curated ABS and RBA economic datasets."""
        return await app_service.search_datasets(query=query, source=source)

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_abs_dataset_structure(dataflow_id: str) -> dict:
        """Get ABS SDMX dataset dimensions and codelists."""
        return await app_service.get_abs_dataset_structure(dataflow_id=dataflow_id)

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_abs_data(
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict:
        """Fetch ABS data in a normalised response shape."""
        return await app_service.get_abs_data(
            dataflow_id=dataflow_id,
            key=key,
            start_period=start_period,
            end_period=end_period,
            last_n=last_n,
            updated_after=updated_after,
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_rba_tables(
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        """List curated RBA statistical tables."""
        return await app_service.list_rba_tables(
            category=category,
            include_discontinued=include_discontinued,
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_rba_table(
        table_id: str,
        series_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        last_n: int | None = None,
    ) -> dict:
        """Fetch an RBA statistical table in a normalised response shape."""
        return await app_service.get_rba_table(
            table_id=table_id,
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_economic_series(
        concept: str,
        variant: str | None = None,
        geography: str | None = None,
        frequency: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict:
        """Resolve an economic concept to an ABS or RBA retrieval, optionally narrowing by
        variant, geography, and frequency."""
        return await app_service.get_economic_series(
            concept=concept,
            variant=variant,
            geography=geography,
            frequency=frequency,
            start=start,
            end=end,
        )

    register_resources(mcp)
    register_prompts(mcp)

    return mcp


mcp = build_server()


def main() -> None:
    configure_logging()
    get_logger("server").info("server.start")
    mcp.run()

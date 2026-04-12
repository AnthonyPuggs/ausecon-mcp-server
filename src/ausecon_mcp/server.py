from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ausecon_mcp.catalogue.search import search_catalogue
from ausecon_mcp.providers.abs import ABSProvider
from ausecon_mcp.providers.rba import RBAProvider

CURATED_SERIES = {
    "cash_rate_target": {"source": "rba", "dataset_id": "a2"},
    "headline_cpi": {"source": "abs", "dataset_id": "CPI"},
    "trimmed_mean_inflation": {"source": "rba", "dataset_id": "g1"},
    "gdp_growth": {"source": "abs", "dataset_id": "NAQ"},
}


class AuseconService:
    def __init__(
        self,
        abs_provider: ABSProvider | Any | None = None,
        rba_provider: RBAProvider | Any | None = None,
    ) -> None:
        self.abs_provider = abs_provider or ABSProvider()
        self.rba_provider = rba_provider or RBAProvider()

    async def search_datasets(self, query: str, source: str | None = None) -> list[dict]:
        return search_catalogue(query, source=source)

    async def get_abs_dataset_structure(self, dataflow_id: str) -> dict:
        return await self.abs_provider.get_dataset_structure(dataflow_id)

    async def get_abs_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict:
        return await self.abs_provider.get_data(
            dataflow_id=dataflow_id,
            key=key,
            start_period=start_period,
            end_period=end_period,
            last_n=last_n,
            updated_after=updated_after,
        )

    async def list_rba_tables(
        self,
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        return self.rba_provider.list_tables(
            category=category,
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
        return await self.rba_provider.get_table(
            table_id=table_id,
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
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
        del variant, geography, frequency
        mapping = CURATED_SERIES[concept]
        if mapping["source"] == "rba":
            return await self.get_rba_table(
                mapping["dataset_id"],
                start_date=start,
                end_date=end,
                last_n=None,
            )
        return await self.get_abs_data(
            mapping["dataset_id"],
            start_period=start,
            end_period=end,
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

    @mcp.tool
    async def search_datasets(query: str, source: str | None = None) -> list[dict]:
        """Search curated ABS and RBA economic datasets."""
        return await app_service.search_datasets(query=query, source=source)

    @mcp.tool
    async def get_abs_dataset_structure(dataflow_id: str) -> dict:
        """Get ABS SDMX dataset dimensions and codelists."""
        return await app_service.get_abs_dataset_structure(dataflow_id=dataflow_id)

    @mcp.tool
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

    @mcp.tool
    async def list_rba_tables(
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        """List curated RBA statistical tables."""
        return await app_service.list_rba_tables(
            category=category,
            include_discontinued=include_discontinued,
        )

    @mcp.tool
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

    @mcp.tool
    async def get_economic_series(
        concept: str,
        variant: str | None = None,
        geography: str | None = None,
        frequency: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict:
        """Resolve a small curated set of high-value economic concepts to ABS or RBA retrievals."""
        return await app_service.get_economic_series(
            concept=concept,
            variant=variant,
            geography=geography,
            frequency=frequency,
            start=start,
            end=end,
        )

    return mcp


def main() -> None:
    build_server().run()

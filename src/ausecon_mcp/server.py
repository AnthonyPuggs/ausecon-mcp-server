from __future__ import annotations

import os
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from ausecon_mcp.bounds import NormalisedSemanticBounds, normalise_semantic_bounds
from ausecon_mcp.catalogue.resolver import (
    list_economic_concepts as _list_economic_concepts,
)
from ausecon_mcp.catalogue.resolver import (
    resolve,
    resolve_abs_dataflow_id,
    resolve_abs_structure_id,
    resolve_rba_csv_path,
)
from ausecon_mcp.catalogue.search import list_catalogue as _list_catalogue
from ausecon_mcp.catalogue.search import search_catalogue
from ausecon_mcp.contracts import response_output_schema
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
    validate_source_token,
)

ABS_PERIOD_PATTERN = r"^(\d{4}|\d{4}-Q[1-4]|\d{4}-(0[1-9]|1[0-2])|\d{4}-S[1-2])$"
SourceFilter = Annotated[
    Literal["abs", "rba"],
    Field(description="Optional source filter: abs or rba."),
]
RbaCategoryFilter = Annotated[
    Literal[
        "exchange_rates",
        "external_sector",
        "household_finance",
        "inflation",
        "interest_rates",
        "monetary_policy",
        "money_credit",
        "output_labour",
        "payments",
    ],
    Field(description="Optional RBA catalogue category filter."),
]
SearchQuery = Annotated[str, Field(min_length=1, description="Discovery query text.")]
ConceptQuery = Annotated[
    str,
    Field(min_length=1, description="Optional semantic concept discovery query."),
]
Identifier = Annotated[str, Field(min_length=1, description="Non-empty dataset or table id.")]
AbsKey = Annotated[
    str,
    Field(min_length=1, description='ABS SDMX key, or "all" for all series.'),
]
AbsPeriod = Annotated[
    str,
    Field(
        pattern=ABS_PERIOD_PATTERN,
        description="ABS period in YYYY, YYYY-QN, YYYY-MM, or YYYY-SN format.",
    ),
]
IsoDate = Annotated[
    str,
    Field(json_schema_extra={"format": "date"}, description="ISO date in YYYY-MM-DD format."),
]
IsoDateTime = Annotated[
    str,
    Field(description="ISO date or datetime accepted by the ABS updatedAfter API."),
]
PositiveInt = Annotated[
    int,
    Field(ge=1, description="Positive observation count limit."),
]
SeriesId = Annotated[str, Field(min_length=1)]
SeriesIdList = Annotated[
    list[SeriesId],
    Field(description="Optional list of non-empty RBA series IDs to keep."),
]
SemanticStartEnd = Annotated[
    str,
    Field(
        description=(
            "Analyst-friendly date bound: YYYY, YYYY-QN, YYYY-SN, YYYY-MM, or YYYY-MM-DD. "
            "Semantic retrieval normalises this to the resolved source frequency."
        ),
    ),
]


def _tool_annotations(title: str) -> dict[str, bool | str]:
    return {"title": title, "readOnlyHint": True, "openWorldHint": True}


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

    async def list_catalogue(
        self,
        source: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        include_ceased: bool = False,
        include_discontinued: bool = False,
    ) -> list[dict]:
        validated_source = validate_source(source)
        return _list_catalogue(
            source=validated_source,
            category=category,
            tag=tag,
            include_ceased=include_ceased,
            include_discontinued=include_discontinued,
        )

    async def list_economic_concepts(
        self,
        query: str | None = None,
        source: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        validated_query = None if query is None else validate_search_query(query)
        validated_source = validate_source(source)
        validated_category = None if category is None else require_non_empty("category", category)
        return _list_economic_concepts(
            query=validated_query,
            source=validated_source,
            category=validated_category,
        )

    async def get_abs_dataset_structure(self, dataflow_id: str) -> dict:
        validated_dataflow_id = validate_source_token("dataflow_id", dataflow_id)
        structure_id = resolve_abs_structure_id(validated_dataflow_id)
        if structure_id == validated_dataflow_id:
            structure_id = resolve_abs_dataflow_id(validated_dataflow_id)
        return await self.abs_provider.get_dataset_structure(structure_id)

    async def get_abs_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict:
        validated_dataflow_id = validate_source_token("dataflow_id", dataflow_id)
        validated_key = validate_source_token("key", key)
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
        validated_table_id = validate_source_token("table_id", table_id)
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
        last_n: int | None = None,
    ) -> dict:
        validated_concept = require_non_empty("concept", concept)
        validated_last_n = validate_positive_int("last_n", last_n)
        resolved = await resolve(
            validated_concept,
            variant=variant,
            geography=geography,
            frequency=frequency,
            abs_structure_fetcher=self.abs_provider.get_dataset_structure,
        )
        bounds = normalise_semantic_bounds(resolved, start=start, end=end)

        if resolved.source == "rba":
            validated_start, validated_end = validate_iso_date_range(
                bounds.start,
                bounds.end,
                start_name="start",
                end_name="end",
            )
            payload = await self.get_rba_table(
                resolved.dataset_id,
                series_ids=resolved.rba_series_ids,
                start_date=validated_start,
                end_date=validated_end,
                last_n=validated_last_n,
            )
            _stamp_semantic_metadata(payload, validated_concept, resolved, bounds)
            return payload

        validated_start, validated_end = validate_abs_period_range(
            bounds.start,
            bounds.end,
            start_name="start",
            end_name="end",
        )
        payload = await self.get_abs_data(
            resolved.dataset_id,
            key=resolved.abs_key or "all",
            start_period=validated_start,
            end_period=validated_end,
            last_n=validated_last_n,
        )
        _stamp_semantic_metadata(payload, validated_concept, resolved, bounds)
        return payload

    async def aclose(self) -> None:
        for provider in (self.abs_provider, self.rba_provider):
            close = getattr(provider, "aclose", None)
            if close is not None:
                await close()


def build_server(service: AuseconService | None = None) -> FastMCP:
    app_service = service or AuseconService()
    mcp = FastMCP(
        "ausecon",
        instructions=(
            "Australian economic data tools for official ABS and RBA datasets. "
            "Use list_economic_concepts before get_economic_series for ordinary analyst "
            "requests such as GDP, CPI, unemployment, cash rate, credit, or yields. "
            "Use search_datasets and list_catalogue for source-native ABS/RBA discovery, "
            "then get_abs_data or get_rba_table when exact dataset/table control is needed."
        ),
    )

    @mcp.tool(annotations=_tool_annotations("Search Datasets"))
    async def search_datasets(query: SearchQuery, source: SourceFilter | None = None) -> list[dict]:
        """Search curated ABS and RBA economic datasets."""
        return await app_service.search_datasets(query=query, source=source)

    @mcp.tool(annotations=_tool_annotations("List Catalogue"))
    async def list_catalogue(
        source: SourceFilter | None = None,
        category: str | None = None,
        tag: str | None = None,
        include_ceased: bool = False,
        include_discontinued: bool = False,
    ) -> list[dict]:
        """List curated ABS and RBA catalogue entries, optionally filtered by source,
        category, or tag. Unranked complement to ``search_datasets``."""
        return await app_service.list_catalogue(
            source=source,
            category=category,
            tag=tag,
            include_ceased=include_ceased,
            include_discontinued=include_discontinued,
        )

    @mcp.tool(annotations=_tool_annotations("List Economic Concepts"))
    async def list_economic_concepts(
        query: ConceptQuery | None = None,
        source: SourceFilter | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """List analyst-friendly semantic economic concepts accepted by get_economic_series."""
        return await app_service.list_economic_concepts(
            query=query,
            source=source,
            category=category,
        )

    @mcp.tool(annotations=_tool_annotations("Get ABS Dataset Structure"))
    async def get_abs_dataset_structure(dataflow_id: Identifier) -> dict:
        """Get ABS SDMX dataset dimensions and codelists."""
        return await app_service.get_abs_dataset_structure(dataflow_id=dataflow_id)

    @mcp.tool(
        annotations=_tool_annotations("Get ABS Data"),
        output_schema=response_output_schema(),
    )
    async def get_abs_data(
        dataflow_id: Identifier,
        key: AbsKey = "all",
        start_period: AbsPeriod | None = None,
        end_period: AbsPeriod | None = None,
        last_n: PositiveInt | None = None,
        updated_after: IsoDateTime | None = None,
    ) -> dict:
        """Expert/source-native ABS SDMX retrieval in a normalised response shape."""
        return await app_service.get_abs_data(
            dataflow_id=dataflow_id,
            key=key,
            start_period=start_period,
            end_period=end_period,
            last_n=last_n,
            updated_after=updated_after,
        )

    @mcp.tool(annotations=_tool_annotations("List RBA Tables"))
    async def list_rba_tables(
        category: RbaCategoryFilter | None = None,
        include_discontinued: bool = False,
    ) -> list[dict]:
        """Deprecated compatibility alias. Prefer list_catalogue(source="rba")."""
        return await app_service.list_rba_tables(
            category=category,
            include_discontinued=include_discontinued,
        )

    @mcp.tool(
        annotations=_tool_annotations("Get RBA Table"),
        output_schema=response_output_schema(),
    )
    async def get_rba_table(
        table_id: Identifier,
        series_ids: SeriesIdList | None = None,
        start_date: IsoDate | None = None,
        end_date: IsoDate | None = None,
        last_n: PositiveInt | None = None,
    ) -> dict:
        """Expert/source-native RBA statistical table retrieval in a normalised response shape."""
        return await app_service.get_rba_table(
            table_id=table_id,
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )

    @mcp.tool(
        annotations=_tool_annotations("Get Economic Series"),
        output_schema=response_output_schema(),
    )
    async def get_economic_series(
        concept: Annotated[str, Field(min_length=1, description="Curated semantic concept name.")],
        variant: str | None = None,
        geography: str | None = None,
        frequency: str | None = None,
        start: SemanticStartEnd | None = None,
        end: SemanticStartEnd | None = None,
        last_n: PositiveInt | None = None,
    ) -> dict:
        """Preferred analyst-facing retrieval tool for curated ABS/RBA economic concepts.

        Use list_economic_concepts for discovery. Date bounds accept YYYY, YYYY-QN,
        YYYY-SN, YYYY-MM, or YYYY-MM-DD and are normalised to the resolved source.
        """
        return await app_service.get_economic_series(
            concept=concept,
            variant=variant,
            geography=geography,
            frequency=frequency,
            start=start,
            end=end,
            last_n=last_n,
        )

    register_resources(mcp)
    register_prompts(mcp)

    return mcp


def _stamp_semantic_metadata(
    payload: dict,
    concept: str,
    resolved: Any,
    bounds: NormalisedSemanticBounds,
) -> None:
    target = {
        "source": resolved.source,
        "dataset_id": resolved.dataset_id,
        "upstream_id": (
            resolve_abs_dataflow_id(resolved.dataset_id)
            if resolved.source == "abs"
            else resolved.dataset_id
        ),
        "abs_key": resolved.abs_key,
        "rba_series_ids": resolved.rba_series_ids,
    }
    payload.setdefault("metadata", {})["semantic"] = {
        "concept": concept,
        "variant": resolved.variant,
        "geography": resolved.geography,
        "frequency": resolved.frequency or resolved.entry.get("frequency"),
        "requested_bounds": {
            "start": bounds.requested_start,
            "end": bounds.requested_end,
        },
        "resolved_bounds": {
            "start": bounds.start,
            "end": bounds.end,
        },
        "target": target,
    }


mcp = build_server()


def resolve_http_port() -> int:
    raw_port = os.environ.get("PORT", "8081")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("PORT must be an integer between 1 and 65535.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535.")
    return port


def build_http_middleware() -> list[Middleware]:
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )
    ]


def main() -> None:
    configure_logging()
    get_logger("server").info("server.start")
    mcp.run()


def main_http() -> None:
    configure_logging()
    get_logger("server").info("server.start", extra={"transport": "streamable-http"})
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=resolve_http_port(),
        path="/mcp",
        middleware=build_http_middleware(),
        show_banner=False,
        uvicorn_config={"access_log": False},
    )

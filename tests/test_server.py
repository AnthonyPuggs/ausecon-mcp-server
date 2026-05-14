import pytest
from fastmcp import Client
from starlette.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

import ausecon_mcp.server as server_module
from ausecon_mcp.server import AuseconService, build_server

EXPECTED_TOOL_TITLES = {
    "search_datasets": "Search Datasets",
    "list_catalogue": "List Catalogue",
    "list_economic_concepts": "List Economic Concepts",
    "get_abs_dataset_structure": "Get ABS Dataset Structure",
    "get_abs_data": "Get ABS Data",
    "list_rba_tables": "List RBA Tables",
    "get_rba_table": "Get RBA Table",
    "get_apra_data": "Get APRA Data",
    "get_economic_series": "Get Economic Series",
    "get_derived_series": "Get Derived Series",
}


def _walk_schema(schema):
    if isinstance(schema, dict):
        yield schema
        for value in schema.values():
            yield from _walk_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            yield from _walk_schema(value)


def _has_schema_description(schema: dict) -> bool:
    return any(node.get("description") for node in _walk_schema(schema))


def _has_string_enum(schema: dict, values: list[str]) -> bool:
    return any(
        node.get("type") == "string" and node.get("enum") == values
        for node in _walk_schema(schema)
    )


def _has_integer_minimum(schema: dict, minimum: int) -> bool:
    return any(
        node.get("type") == "integer" and node.get("minimum") == minimum
        for node in _walk_schema(schema)
    )


def _has_schema_property(schema: dict, key: str, value: object | None = None) -> bool:
    for node in _walk_schema(schema):
        if key not in node:
            continue
        if value is None or node[key] == value:
            return True
    return False


def test_schema_description_normaliser_promotes_python310_optional_union_shape() -> None:
    schema = {
        "type": "object",
        "properties": {
            "source": {
                "anyOf": [
                    {
                        "anyOf": [
                            {"enum": ["abs", "rba", "apra"], "type": "string"},
                            {"type": "null"},
                        ],
                        "description": "Optional source filter.",
                    },
                    {"type": "null"},
                ],
                "default": None,
            },
        },
    }

    server_module._promote_nested_parameter_descriptions(schema)

    assert schema["properties"]["source"]["description"] == "Optional source filter."


class FakeMCP:
    def __init__(self) -> None:
        self.run_kwargs: dict | None = None

    def run(self, **kwargs) -> None:
        self.run_kwargs = kwargs


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


class StubAPRAProvider:
    def __init__(self) -> None:
        self.last_get_data_kwargs: dict | None = None

    async def get_data(
        self,
        publication_id: str,
        table_id: str | None = None,
        series_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        last_n: int | None = None,
    ) -> dict:
        self.last_get_data_kwargs = {
            "publication_id": publication_id,
            "table_id": table_id,
            "series_ids": series_ids,
            "start_date": start_date,
            "end_date": end_date,
            "last_n": last_n,
        }
        return {
            "metadata": {"source": "apra", "dataset_id": publication_id},
            "series": [{"series_id": "apra-series"}],
            "observations": [{"date": "2024-03-31", "series_id": "apra-series", "value": 1.0}],
        }


class RecordingDerivedService(AuseconService):
    def __init__(self, payloads: dict[str, dict]) -> None:
        super().__init__(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())
        self.payloads = payloads
        self.economic_series_calls: list[dict] = []

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
        self.economic_series_calls.append(
            {
                "concept": concept,
                "variant": variant,
                "geography": geography,
                "frequency": frequency,
                "start": start,
                "end": end,
                "last_n": last_n,
            }
        )
        return self.payloads[concept]


def _semantic_payload(
    *,
    concept: str,
    source: str,
    dataset_id: str,
    series_id: str,
    observations: list[tuple[str, float | None]],
    frequency: str,
    abs_key: str | None = None,
    rba_series_ids: list[str] | None = None,
) -> dict:
    return {
        "metadata": {
            "source": source,
            "dataset_id": dataset_id,
            "server_version": "test",
            "truncated": False,
            "semantic": {
                "concept": concept,
                "variant": None,
                "geography": None,
                "frequency": frequency,
                "requested_bounds": {"start": None, "end": None},
                "resolved_bounds": {"start": None, "end": None},
                "target": {
                    "source": source,
                    "dataset_id": dataset_id,
                    "upstream_id": dataset_id,
                    "abs_key": abs_key,
                    "rba_series_ids": rba_series_ids,
                },
            },
        },
        "series": [
            {
                "series_id": series_id,
                "label": concept,
                "unit": None,
                "frequency": frequency,
                "dimensions": {},
                "source_key": series_id,
                "unit_multiplier": None,
                "decimals": None,
                "base_period": None,
            }
        ],
        "observations": [
            {"date": date, "series_id": series_id, "value": value, "dimensions": {}}
            for date, value in observations
        ],
    }


def test_http_port_defaults_to_smithery_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PORT", raising=False)

    assert server_module.resolve_http_port() == 8081


def test_http_port_accepts_valid_environment_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "9090")

    assert server_module.resolve_http_port() == 9090


@pytest.mark.parametrize("port", ["abc", "0", "65536", "-1"])
def test_http_port_rejects_invalid_environment_port(
    monkeypatch: pytest.MonkeyPatch,
    port: str,
) -> None:
    monkeypatch.setenv("PORT", port)

    with pytest.raises(ValueError, match="PORT must be an integer between 1 and 65535"):
        server_module.resolve_http_port()


def test_http_middleware_configures_non_credentialed_cors() -> None:
    middleware = server_module.build_http_middleware()

    cors = next(item for item in middleware if item.cls is CORSMiddleware)
    assert cors.kwargs["allow_origins"] == ["*"]
    assert cors.kwargs["allow_credentials"] is False
    assert cors.kwargs["allow_methods"] == ["GET", "POST", "DELETE", "OPTIONS"]
    assert cors.kwargs["allow_headers"] == ["*"]
    assert cors.kwargs["expose_headers"] == ["mcp-session-id", "mcp-protocol-version"]


def test_main_http_runs_streamable_http_on_smithery_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {}

    def fake_run(app, **kwargs):
        calls["app"] = app
        calls["kwargs"] = kwargs

    monkeypatch.setattr(server_module, "build_http_app", lambda: "http-app")
    monkeypatch.setattr(server_module.uvicorn, "run", fake_run)
    monkeypatch.setenv("PORT", "9090")

    server_module.main_http()

    assert calls["app"] == "http-app"
    assert calls["kwargs"]["host"] == "0.0.0.0"
    assert calls["kwargs"]["port"] == 9090
    assert calls["kwargs"]["access_log"] is False
    assert calls["kwargs"]["lifespan"] == "on"


def test_http_app_uses_smithery_mcp_path() -> None:
    app = server_module.build_http_app(build_server())

    assert app.state.path == "/mcp"
    assert app.state.transport_type == "streamable-http"


def test_http_app_exposes_status_endpoints_for_hosted_publish_flow() -> None:
    app = server_module.build_http_app(build_server())

    with TestClient(app) as client:
        root = client.get("/")
        health = client.get("/healthz")

    assert root.status_code == 200
    assert root.json()["mcp_endpoint"] == "/mcp"
    assert root.json()["server_card"] == "/.well-known/mcp/server-card.json"
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_http_app_exposes_smithery_static_server_card() -> None:
    app = server_module.build_http_app(build_server())

    with TestClient(app) as client:
        response = client.get("/.well-known/mcp/server-card.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["serverInfo"]["name"] == "ausecon-mcp-server"
    assert payload["serverInfo"]["version"]
    assert payload["displayName"] == "AusEcon MCP Server"
    assert "Australian economic data" in payload["description"]
    assert payload["homepage"] == server_module.HOMEPAGE_URL
    assert payload["iconUrl"] == server_module.SERVER_ICON_URL
    assert payload["icons"][0]["src"] == server_module.SERVER_ICON_URL
    assert payload["license"] == "MIT"
    assert payload["authentication"] == {"required": False}
    tools = {tool["name"]: tool for tool in payload["tools"]}
    assert set(tools) == set(EXPECTED_TOOL_TITLES)

    for name, title in EXPECTED_TOOL_TITLES.items():
        tool = tools[name]
        assert tool["title"] == title
        assert tool["description"], f"{name} missing description"
        assert tool["inputSchema"]["type"] == "object"
        assert tool["outputSchema"]["type"] == "object"
        assert tool["annotations"]["title"] == title
        assert tool["annotations"]["readOnlyHint"] is True
        assert tool["annotations"]["destructiveHint"] is False
        assert tool["annotations"]["idempotentHint"] is True
        assert tool["annotations"]["openWorldHint"] is True

        for parameter, schema in tool["inputSchema"].get("properties", {}).items():
            assert schema.get("description"), f"{name}.{parameter} missing description"


@pytest.mark.asyncio
async def test_service_searches_curated_catalogue() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    results = await service.search_datasets("cash rate")

    assert results[0]["id"] == "a2"


@pytest.mark.parametrize(
    "query",
    [
        "https://example.com",
        "cash/rate",
        "cash?rate",
        "cash#rate",
        "cash\\rate",
        "cash\nrate",
        "x" * 201,
    ],
)
@pytest.mark.asyncio
async def test_service_rejects_unsafe_search_queries(query: str) -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="query"):
        await service.search_datasets(query)


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
async def test_service_fetches_apra_data() -> None:
    apra = StubAPRAProvider()
    service = AuseconService(
        abs_provider=StubABSProvider(),
        rba_provider=StubRBAProvider(),
        apra_provider=apra,
    )

    result = await service.get_apra_data(
        "ADI_PROPERTY_EXPOSURES",
        table_id="tab_1b",
        series_ids=["ADI_PROPERTY_EXPOSURES:tab_1b:credit_outstanding:total_credit_outstanding"],
        start_date="2024-01-01",
        end_date="2024-12-31",
        last_n=1,
    )

    assert result["metadata"]["source"] == "apra"
    assert apra.last_get_data_kwargs == {
        "publication_id": "ADI_PROPERTY_EXPOSURES",
        "table_id": "tab_1b",
        "series_ids": [
            "ADI_PROPERTY_EXPOSURES:tab_1b:credit_outstanding:total_credit_outstanding"
        ],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "last_n": 1,
    }


@pytest.mark.asyncio
async def test_service_rejects_unsafe_apra_publication_ids_before_provider_call() -> None:
    apra = StubAPRAProvider()
    service = AuseconService(
        abs_provider=StubABSProvider(),
        rba_provider=StubRBAProvider(),
        apra_provider=apra,
    )

    with pytest.raises(ValueError, match="publication_id"):
        await service.get_apra_data("https://example.com")

    assert apra.last_get_data_kwargs is None


@pytest.mark.asyncio
async def test_service_allows_apra_source_filter_without_semantic_concepts() -> None:
    service = AuseconService(
        abs_provider=StubABSProvider(),
        rba_provider=StubRBAProvider(),
        apra_provider=StubAPRAProvider(),
    )

    assert await service.list_economic_concepts(source="apra") == []
    catalogue = await service.list_catalogue(source="apra")
    assert {item["id"] for item in catalogue} == {
        "ADI_MONTHLY",
        "ADI_QUARTERLY_PERFORMANCE",
        "ADI_QUARTERLY_CENTRALISED",
        "ADI_PROPERTY_EXPOSURES",
    }


@pytest.mark.parametrize(
    "dataflow_id",
    [
        "https://example.com",
        "../CPI",
        "CPI?x=1",
        "CPI#frag",
        "CPI\\path",
        "CPI\n",
        "x" * 129,
    ],
)
@pytest.mark.asyncio
async def test_service_rejects_unsafe_abs_identifiers_before_provider_call(
    dataflow_id: str,
) -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="dataflow_id"):
        await service.get_abs_data(dataflow_id)

    assert abs_provider.last_get_data_kwargs is None


@pytest.mark.asyncio
async def test_service_allows_source_native_abs_identifiers_and_keys() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_abs_data("ANA_AGG", key="M2.GPM.20.AUS.Q")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "ANA_AGG"
    assert abs_provider.last_get_data_kwargs["key"] == "M2.GPM.20.AUS.Q"


@pytest.mark.parametrize(
    "table_id",
    [
        "https://example.com",
        "../g1",
        "g1?x=1",
        "g1#frag",
        "g1\\path",
        "g1\n",
        "x" * 129,
    ],
)
@pytest.mark.asyncio
async def test_service_rejects_unsafe_rba_table_ids_before_provider_call(table_id: str) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    with pytest.raises(ValueError, match="table_id"):
        await service.get_rba_table(table_id)

    assert rba.last_get_table_kwargs is None


@pytest.mark.parametrize("series_id", ["https://example.com", "../GCPIAG", "GCPIAG?x=1"])
@pytest.mark.asyncio
async def test_service_rejects_unsafe_rba_series_ids_before_provider_call(series_id: str) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    with pytest.raises(ValueError, match="series_ids"):
        await service.get_rba_table("g1", series_ids=[series_id])

    assert rba.last_get_table_kwargs is None


@pytest.mark.asyncio
async def test_service_allows_source_native_rba_table_and_series_ids() -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_rba_table("c1.2", series_ids=["GCPIAG"])

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == "c1.2"
    assert rba.last_get_table_kwargs["series_ids"] == ["GCPIAG"]


@pytest.mark.asyncio
async def test_service_rejects_unknown_economic_series_concept() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unknown concept"):
        await service.get_economic_series("unknown_series")


@pytest.mark.asyncio
async def test_service_rejects_unknown_derived_series_concept() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unknown derived concept"):
        await service.get_derived_series("unknown_series")


@pytest.mark.asyncio
async def test_service_rejects_invalid_derived_date_range_before_fetching_operands() -> None:
    service = RecordingDerivedService({})

    with pytest.raises(ValueError, match="start must be before or equal to end"):
        await service.get_derived_series("credit_growth", start="2024-02", end="2024-01")

    assert service.economic_series_calls == []


@pytest.mark.asyncio
async def test_service_get_derived_series_fetches_operands_and_applies_final_last_n() -> None:
    service = RecordingDerivedService(
        {
            "total_credit": _semantic_payload(
                concept="total_credit",
                source="rba",
                dataset_id="d2",
                series_id="DLCACS",
                observations=[
                    ("2023-01", 100.0),
                    ("2023-02", 110.0),
                    ("2024-01", 115.0),
                    ("2024-02", 121.0),
                ],
                frequency="Monthly",
                rba_series_ids=["DLCACS"],
            )
        }
    )

    result = await service.get_derived_series(
        "credit_growth",
        start="2024-01",
        end="2024-02",
        last_n=1,
    )

    assert service.economic_series_calls == [
        {
            "concept": "total_credit",
            "variant": None,
            "geography": None,
            "frequency": None,
            "start": "2023-01",
            "end": "2024-02",
            "last_n": None,
        }
    ]
    assert [(obs["date"], obs["value"]) for obs in result["observations"]] == [
        ("2024-02", pytest.approx(10.0))
    ]
    assert result["metadata"]["source"] == "derived"
    assert result["metadata"]["dataset_id"] == "credit_growth"
    assert result["metadata"]["derived"]["operands"][0]["concept"] == "total_credit"


@pytest.mark.asyncio
async def test_service_expands_quarterly_cpi_operand_for_real_wage_growth() -> None:
    service = RecordingDerivedService(
        {
            "wage_growth": _semantic_payload(
                concept="wage_growth",
                source="abs",
                dataset_id="WPI",
                series_id="wpi",
                observations=[("2024-Q1", 4.2)],
                frequency="Quarterly",
                abs_key="3.THRPEB.7.TOT.20.AUS.Q",
            ),
            "headline_cpi": _semantic_payload(
                concept="headline_cpi",
                source="abs",
                dataset_id="CPI",
                series_id="cpi",
                observations=[("2023-Q1", 100.0), ("2024-Q1", 104.0)],
                frequency="Quarterly",
                abs_key="1.10001.10.50.Q",
            ),
        }
    )

    await service.get_derived_series("real_wage_growth", start="2024-Q1", end="2024-Q1")

    assert service.economic_series_calls == [
        {
            "concept": "wage_growth",
            "variant": None,
            "geography": None,
            "frequency": None,
            "start": "2024-Q1",
            "end": "2024-Q1",
            "last_n": None,
        },
        {
            "concept": "headline_cpi",
            "variant": None,
            "geography": None,
            "frequency": None,
            "start": "2023-Q1",
            "end": "2024-Q1",
            "last_n": None,
        },
    ]


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
async def test_service_normalises_semantic_abs_iso_bounds_for_quarterly_concept() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    result = await service.get_economic_series(
        "gdp_growth",
        start="2020-01-01",
        end="2024-06-30",
    )

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["start_period"] == "2020-Q1"
    assert abs_provider.last_get_data_kwargs["end_period"] == "2024-Q2"
    assert result["metadata"]["semantic"]["concept"] == "gdp_growth"
    assert result["metadata"]["semantic"]["requested_bounds"] == {
        "start": "2020-01-01",
        "end": "2024-06-30",
    }
    assert result["metadata"]["semantic"]["resolved_bounds"] == {
        "start": "2020-Q1",
        "end": "2024-Q2",
    }


@pytest.mark.asyncio
async def test_service_normalises_semantic_abs_quarter_bounds_for_monthly_concept() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series("trade_balance", start="2020-Q1", end="2020-Q2")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["start_period"] == "2020-01"
    assert abs_provider.last_get_data_kwargs["end_period"] == "2020-06"


@pytest.mark.asyncio
async def test_service_normalises_semantic_rba_coarse_bounds_to_iso_dates() -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    result = await service.get_economic_series(
        "cash_rate_target",
        start="2020-Q1",
        end="2020-02",
    )

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["start_date"] == "2020-01-01"
    assert rba.last_get_table_kwargs["end_date"] == "2020-02-29"
    assert result["metadata"]["semantic"]["resolved_bounds"] == {
        "start": "2020-01-01",
        "end": "2020-02-29",
    }


@pytest.mark.asyncio
async def test_service_rejects_removed_runtime_rba_variant() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="Unknown variant"):
        await service.get_economic_series("g3", variant="market")


@pytest.mark.asyncio
async def test_service_forwards_default_abs_key_for_dwelling_approvals() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series("dwelling_approvals")

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == "BA_GCCSA"
    assert abs_provider.last_get_data_kwargs["key"] == "1.1.9.TOT.100.10.AUS.M"


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
async def test_service_rejects_invalid_semantic_bounds_after_resolution() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="YYYY"):
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


TRANCHE_A_ABS_SERVICE = [
    ("employment", "LF", "M3.3.1599.20.AUS.M"),
    ("unemployment_rate", "LF", "M13.3.1599.20.AUS.M"),
    ("participation_rate", "LF", "M12.3.1599.20.AUS.M"),
    ("wage_growth", "WPI", "3.THRPEB.7.TOT.20.AUS.Q"),
    ("trade_balance", "ITGS", "M1.170.20.AUS.M"),
]

TRANCHE_A_RBA_SERVICE = [
    ("weighted_median_inflation", "g1", ["GCPIOCPMWMYP"]),
    ("aud_usd", "f11", ["FXRUSD"]),
    ("trade_weighted_index", "f11", ["FXRTWI"]),
    ("government_bond_yield_3y", "f17", ["FZCY300D"]),
    ("government_bond_yield_10y", "f17", ["FZCY1000D"]),
    ("housing_credit", "d2", ["DLCACOHS", "DLCACIHS"]),
]


@pytest.mark.parametrize(("concept", "dataflow_id", "abs_key"), TRANCHE_A_ABS_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_a_abs_concepts(
    concept: str, dataflow_id: str, abs_key: str
) -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series(concept)

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == dataflow_id
    assert abs_provider.last_get_data_kwargs["key"] == abs_key


@pytest.mark.parametrize(("concept", "table_id", "series_ids"), TRANCHE_A_RBA_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_a_rba_concepts(
    concept: str, table_id: str, series_ids: list[str]
) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series(concept)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == table_id
    assert rba.last_get_table_kwargs["series_ids"] == series_ids


@pytest.mark.asyncio
async def test_list_catalogue_unfiltered_returns_abs_rba_and_apra_entries() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_catalogue()

    sources = {row["source"] for row in rows}
    assert sources == {"abs", "rba", "apra"}
    expected_keys = {"id", "source", "name", "category", "frequency", "tags"}
    assert all(row.keys() == expected_keys for row in rows)


@pytest.mark.asyncio
async def test_list_catalogue_filters_by_source() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_catalogue(source="rba")

    assert rows
    assert {row["source"] for row in rows} == {"rba"}


@pytest.mark.asyncio
async def test_list_catalogue_filters_by_category() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_catalogue(category="inflation")

    assert rows
    assert {row["category"] for row in rows} == {"inflation"}


@pytest.mark.asyncio
async def test_list_catalogue_filters_by_tag_case_insensitive() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_catalogue(tag="Yield Curve")

    assert rows
    assert any("yield curve" in [t.lower() for t in row["tags"]] for row in rows)


@pytest.mark.asyncio
async def test_list_catalogue_excludes_ceased_and_discontinued_by_default() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_catalogue()
    ids = {row["id"] for row in rows}

    # BUSINESS_TURNOVER is ceased; a5 was un-discontinued but check no ceased/discontinued.
    from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
    from ausecon_mcp.catalogue.rba import RBA_CATALOGUE

    for entry in list(ABS_CATALOGUE.values()) + list(RBA_CATALOGUE.values()):
        if entry.get("ceased") or entry.get("discontinued"):
            assert entry["id"] not in ids


@pytest.mark.asyncio
async def test_list_catalogue_includes_ceased_when_opted_in() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_catalogue(include_ceased=True)
    ids = {row["id"] for row in rows}

    assert "BUSINESS_TURNOVER" in ids


@pytest.mark.asyncio
async def test_list_catalogue_rejects_unknown_source() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="source"):
        await service.list_catalogue(source="fred")


@pytest.mark.asyncio
async def test_list_economic_concepts_filters_and_recommends_calls() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    rows = await service.list_economic_concepts(
        query="cash",
        source="rba",
        category="monetary_policy",
    )

    assert rows
    assert rows[0]["concept"] == "cash_rate_target"
    assert rows[0]["source"] == "rba"
    assert rows[0]["dataset_id"] == "a2"
    assert rows[0]["variant"] == "target"
    assert rows[0]["recommended_call"] == {
        "tool": "get_economic_series",
        "arguments": {"concept": "cash_rate_target"},
    }


@pytest.mark.asyncio
async def test_service_forwards_last_n_to_abs_provider_for_semantic_call() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series("headline_cpi", last_n=4)

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["last_n"] == 4


@pytest.mark.asyncio
async def test_service_forwards_last_n_to_rba_provider_for_semantic_call() -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series("cash_rate_target", last_n=12)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["last_n"] == 12


@pytest.mark.asyncio
async def test_service_rejects_non_positive_semantic_last_n() -> None:
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=StubRBAProvider())

    with pytest.raises(ValueError, match="last_n"):
        await service.get_economic_series("cash_rate_target", last_n=0)


TRANCHE_B_ABS_SERVICE = [
    ("current_account_balance", "BOP", "1.100.20.Q"),
    ("underemployment_rate", "LF_UNDER", "M23.3.1599.20.AUS.M"),
    ("hours_worked", "LF_HOURS", "M18.3.1599.TOT.20.AUS.M"),
    ("job_vacancies", "JV", "M1.7.TOT.20.AUS.Q"),
    ("population", "ERP_Q", "1.3.TOT.AUS.Q"),
    ("producer_price_inflation", "PPI_FD", "3.TOT.TOT.TOTXE.Q"),
    ("household_spending", "HSI_M", "7.TOT.CUR.20.AUS.M"),
]

TRANCHE_B_RBA_SERVICE = [
    ("business_credit", "d2", ["DLCACBS"]),
    ("mortgage_rate", "f6", ["FLRHOOVA"]),
    ("business_lending_rate", "f7", ["FLRBFOSBT"]),
    ("inflation_expectations", "g3", ["GCONEXP"]),
    ("commodity_prices", "i2", ["GRCPAISDR"]),
]

TRANCHE_C_ABS_SERVICE = [
    ("real_gdp", "ANA_AGG", "M1.GPM.20.AUS.Q"),
    ("nominal_gdp", "ANA_AGG", "M3.GPM.20.AUS.Q"),
    ("household_consumption", "ANA_EXP", "VCH.FCE.PHS.20.AUS.Q"),
    ("private_investment", "ANA_EXP", "VCH.GFC_PBI.PSS.20.AUS.Q"),
    ("retail_turnover", "RT", "M1.20.20.AUS.M"),
]

TRANCHE_C_RBA_SERVICE = [
    ("broad_money", "d3", ["DMABMS"]),
    ("bank_bill_rate", "f1", ["FIRMMBAB90D"]),
]

TRANCHE_D_RBA_SERVICE = [
    ("total_credit", "d2", ["DLCACS"]),
    ("total_credit_growth", "d1", ["DGFAC12"]),
    ("housing_credit_growth", "d1", ["DGFACH12"]),
    ("business_credit_growth", "d1", ["DGFACB12"]),
    ("m3", "d3", ["DMAM3S"]),
    ("money_base", "d3", ["DMAMMB"]),
    ("currency_in_circulation", "d3", ["DMACS"]),
    ("aud_cny", "f11", ["FXRCR"]),
    ("aud_jpy", "f11", ["FXRJY"]),
    ("aud_eur", "f11", ["FXREUR"]),
    ("aud_gbp", "f11", ["FXRUKPS"]),
    ("aud_nzd", "f11", ["FXRNZD"]),
]

TRANCHE_E_ABS_SERVICE = [
    ("monthly_inflation", "CPI", "3.10001.10.50.M"),
    ("monthly_cpi_index", "CPI", "1.10001.10.50.M"),
    ("monthly_cpi_change", "CPI", "2.10001.10.50.M"),
    ("monthly_trimmed_mean_inflation", "CPI", "3.999902.20.50.M"),
    ("monthly_weighted_median_inflation", "CPI", "3.999903.20.50.M"),
    (
        "new_housing_lending",
        "LEND_HOUSING",
        "FIN_VAL.NEWCOMMITS.DV8368.TOTDWELL.TOT.TOT.20.AUS.Q",
    ),
    (
        "owner_occupier_housing_lending",
        "LEND_HOUSING",
        "FIN_VAL.NEWCOMMITS.DV8368.TOTDWELL.TOT.DV5167.20.AUS.Q",
    ),
    (
        "investor_housing_lending",
        "LEND_HOUSING",
        "FIN_VAL.NEWCOMMITS.DV8368.TOTDWELL.TOT.DV5168.20.AUS.Q",
    ),
]


@pytest.mark.parametrize(("concept", "dataflow_id", "abs_key"), TRANCHE_B_ABS_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_b_abs_concepts(
    concept: str, dataflow_id: str, abs_key: str
) -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series(concept)

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == dataflow_id
    assert abs_provider.last_get_data_kwargs["key"] == abs_key


@pytest.mark.parametrize(("concept", "table_id", "series_ids"), TRANCHE_B_RBA_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_b_rba_concepts(
    concept: str, table_id: str, series_ids: list[str]
) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series(concept)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == table_id
    assert rba.last_get_table_kwargs["series_ids"] == series_ids


@pytest.mark.parametrize(("concept", "dataflow_id", "abs_key"), TRANCHE_C_ABS_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_c_abs_concepts(
    concept: str, dataflow_id: str, abs_key: str
) -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series(concept)

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == dataflow_id
    assert abs_provider.last_get_data_kwargs["key"] == abs_key


@pytest.mark.parametrize(("concept", "table_id", "series_ids"), TRANCHE_C_RBA_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_c_rba_concepts(
    concept: str, table_id: str, series_ids: list[str]
) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series(concept)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == table_id
    assert rba.last_get_table_kwargs["series_ids"] == series_ids


@pytest.mark.parametrize(("concept", "table_id", "series_ids"), TRANCHE_D_RBA_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_d_rba_concepts(
    concept: str, table_id: str, series_ids: list[str]
) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series(concept)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == table_id
    assert rba.last_get_table_kwargs["series_ids"] == series_ids


@pytest.mark.parametrize(("concept", "dataflow_id", "abs_key"), TRANCHE_E_ABS_SERVICE)
@pytest.mark.asyncio
async def test_service_forwards_tranche_e_abs_concepts(
    concept: str, dataflow_id: str, abs_key: str
) -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series(concept)

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == dataflow_id
    assert abs_provider.last_get_data_kwargs["key"] == abs_key


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


async def test_service_uses_abs_structure_id_for_structure_tool() -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    result = await service.get_abs_dataset_structure("LF_UNDER")

    assert result["id"] == "DS_LF_UNDER"


async def test_registered_tools_carry_readonly_and_openworld_annotations() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = await client.list_tools()

    assert tools, "expected at least one tool registered"
    for tool in tools:
        annotations = tool.annotations
        assert annotations is not None, f"{tool.name} has no annotations"
        assert annotations.title, f"{tool.name} missing human-readable title"
        assert annotations.readOnlyHint is True, f"{tool.name} missing readOnlyHint"
        assert annotations.destructiveHint is False, f"{tool.name} missing destructiveHint"
        assert annotations.idempotentHint is True, f"{tool.name} missing idempotentHint"
        assert annotations.openWorldHint is True, f"{tool.name} missing openWorldHint"


async def test_registered_tools_expose_top_level_titles_for_hosted_registries() -> None:
    mcp = build_server()

    tools = {tool.name: tool for tool in await mcp.list_tools(run_middleware=False)}

    assert set(tools) == set(EXPECTED_TOOL_TITLES)
    for name, title in EXPECTED_TOOL_TITLES.items():
        assert tools[name].title == title


def test_server_metadata_is_complete_for_hosted_registries() -> None:
    mcp = build_server()

    assert mcp.name == "ausecon-mcp-server"
    assert mcp.version
    assert mcp.website_url == server_module.HOMEPAGE_URL
    assert mcp.icons
    assert mcp.icons[0].src == server_module.SERVER_ICON_URL
    assert mcp.icons[0].mimeType == "image/svg+xml"


async def test_registered_tools_expose_input_schema_constraints_and_descriptions() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    source_schema = tools["search_datasets"].inputSchema["properties"]["source"]
    assert _has_string_enum(source_schema, ["abs", "rba", "apra"])
    assert _has_schema_description(source_schema)

    concepts_source_schema = tools["list_economic_concepts"].inputSchema["properties"]["source"]
    assert _has_string_enum(concepts_source_schema, ["abs", "rba", "apra"])
    assert "economic concepts" in tools["list_economic_concepts"].description

    last_n_schema = tools["get_abs_data"].inputSchema["properties"]["last_n"]
    assert _has_integer_minimum(last_n_schema, 1)
    assert _has_schema_description(last_n_schema)

    start_period_schema = tools["get_abs_data"].inputSchema["properties"]["start_period"]
    assert _has_schema_property(start_period_schema, "pattern")
    assert "ABS period" in str(start_period_schema)

    start_date_schema = tools["get_rba_table"].inputSchema["properties"]["start_date"]
    assert _has_schema_property(start_date_schema, "format", "date")
    assert "ISO date" in str(start_date_schema)

    apra_start_date_schema = tools["get_apra_data"].inputSchema["properties"]["start_date"]
    assert _has_schema_property(apra_start_date_schema, "format", "date")
    assert "ISO date" in str(apra_start_date_schema)

    category_schema = tools["list_rba_tables"].inputSchema["properties"]["category"]
    expected_categories = [
        "exchange_rates",
        "external_sector",
        "household_finance",
        "inflation",
        "interest_rates",
        "monetary_policy",
        "money_credit",
        "output_labour",
        "payments",
    ]
    assert _has_string_enum(category_schema, expected_categories)

    semantic_start_schema = tools["get_economic_series"].inputSchema["properties"]["start"]
    assert "YYYY-QN" in str(semantic_start_schema)
    assert "YYYY-MM-DD" in str(semantic_start_schema)

    derived_start_schema = tools["get_derived_series"].inputSchema["properties"]["start"]
    assert "derived series" in tools["get_derived_series"].description
    assert "YYYY-QN" in str(derived_start_schema)
    assert _has_integer_minimum(tools["get_derived_series"].inputSchema["properties"]["last_n"], 1)


async def test_all_registered_tool_parameters_have_top_level_descriptions() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = await client.list_tools()

    for tool in tools:
        properties = tool.inputSchema.get("properties", {})
        for parameter, schema in properties.items():
            assert schema.get("description"), f"{tool.name}.{parameter} missing description"


async def test_retrieval_tools_expose_response_output_schema() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    for name in (
        "get_abs_data",
        "get_rba_table",
        "get_apra_data",
        "get_economic_series",
        "get_derived_series",
    ):
        output_schema = tools[name].outputSchema
        assert output_schema["type"] == "object"
        assert output_schema["additionalProperties"] is False
        assert output_schema["required"] == ["metadata", "series", "observations"]


async def test_all_registered_tools_expose_output_schema() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = await client.list_tools()

    for tool in tools:
        output_schema = tool.outputSchema
        assert output_schema["type"] == "object", f"{tool.name} missing object output schema"
        assert output_schema.get("description") or output_schema.get("title")

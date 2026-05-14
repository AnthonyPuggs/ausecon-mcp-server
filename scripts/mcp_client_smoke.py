from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.client import UvStdioTransport

ROOT = Path(__file__).resolve().parents[1]


def _as_dict(data):
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, list):
        return [_as_dict(item) for item in data]
    if isinstance(data, dict):
        return {key: _as_dict(value) for key, value in data.items()}
    if hasattr(data, "__dict__"):
        return {key: _as_dict(value) for key, value in vars(data).items()}
    return data


async def main() -> None:
    transport = UvStdioTransport(
        "ausecon-mcp-server",
        project_directory=ROOT,
        python_version="3.12",
        env_vars={
            "UV_CACHE_DIR": str(ROOT / ".uv-cache"),
            "FASTMCP_SHOW_SERVER_BANNER": "false",
            "FASTMCP_LOG_LEVEL": "ERROR",
            "AUSECON_CACHE_DISABLED": "1",
            "AUSECON_LOG_LEVEL": "ERROR",
        },
    )

    async with Client(transport, name="ausecon-smoke") as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        assert {
            "list_economic_concepts",
            "search_datasets",
            "list_catalogue",
            "get_abs_data",
            "get_economic_series",
            "get_derived_series",
        } <= tool_names

        concepts = await client.call_tool("list_economic_concepts", {"query": "dwelling approvals"})
        assert concepts.data and concepts.data[0]["concept"] == "dwelling_approvals"

        search = await client.call_tool("search_datasets", {"query": "cash rate"})
        assert search.data and search.data[0]["id"] == "a2"

        catalogue = await client.call_tool(
            "list_catalogue",
            {"source": "abs", "category": "housing_construction"},
        )
        ids = {row["id"] for row in catalogue.data}
        assert "BUILDING_APPROVALS" in ids

        abs_data = await client.call_tool(
            "get_abs_data",
            {
                "dataflow_id": "BUILDING_APPROVALS",
                "key": "1.1.9.TOT.100.10.AUS.M",
                "last_n": 3,
            },
        )
        abs_payload = _as_dict(abs_data.data)
        assert abs_payload["metadata"]["source"] == "abs"
        assert abs_payload["observations"]

        semantic = await client.call_tool(
            "get_economic_series",
            {"concept": "dwelling_approvals", "last_n": 3},
        )
        semantic_payload = _as_dict(semantic.data)
        assert semantic_payload["metadata"]["source"] == "abs"
        assert semantic_payload["observations"]

        derived = await client.call_tool(
            "get_derived_series",
            {"concept": "yield_curve_slope", "last_n": 1},
        )
        derived_payload = _as_dict(derived.data)
        assert derived_payload["metadata"]["source"] == "derived"
        assert derived_payload["metadata"]["derived"]["concept"] == "yield_curve_slope"
        assert derived_payload["observations"]

    print("mcp-smoke-ok")


if __name__ == "__main__":
    asyncio.run(main())

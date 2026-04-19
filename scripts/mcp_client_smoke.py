from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.client import UvStdioTransport

ROOT = Path(__file__).resolve().parents[1]


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
            "search_datasets",
            "list_catalogue",
            "get_abs_data",
            "get_economic_series",
        } <= tool_names

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
        assert abs_data.data["metadata"]["source"] == "abs"
        assert abs_data.data["observations"]

        semantic = await client.call_tool(
            "get_economic_series",
            {"concept": "dwelling_approvals", "last_n": 3},
        )
        assert semantic.data["metadata"]["source"] == "abs"
        assert semantic.data["observations"]

    print("mcp-smoke-ok")


if __name__ == "__main__":
    asyncio.run(main())

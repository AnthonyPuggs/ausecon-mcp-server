"""Both MCP protocol eras fastmcp 4 negotiates: the legacy handshake and 2026-07-28.

Every call here is catalogue-local, so no test touches the network.
"""

import asyncio
import socket
import threading
import time
from collections.abc import Callable, Iterator

import pytest
import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from mcp.server import _streamable_http_modern

from ausecon_mcp.server import AuseconService, build_http_app, build_server

ERAS = ["legacy", "2026-07-28"]
LARGE_TABLE_OBSERVATIONS = 20_000


class _SlowLargeRBAProvider:
    """Answers one RBA table after a short delay with a payload well over 1 MiB."""

    def list_tables(self, category: str | None = None, include_discontinued: bool = False):
        return []

    async def get_table(self, table_id: str, **_kwargs) -> dict:
        await asyncio.sleep(0.5)
        return {
            "metadata": {
                "source": "rba",
                "dataset_id": table_id,
                "server_version": "test",
                "truncated": False,
            },
            "series": [{"series_id": "rba-series", "label": "Large series", "dimensions": {}}],
            "observations": [
                {"date": f"{1900 + i // 365}-01-01", "series_id": "rba-series", "value": i + 0.25}
                for i in range(LARGE_TABLE_OBSERVATIONS)
            ],
        }


class _HttpServer:
    """The streamable-HTTP app on a local port, in a thread, restartable on the same port."""

    def __init__(self, server_factory: Callable[[], FastMCP] = build_server) -> None:
        self._server_factory = server_factory
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}/mcp"
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        config = uvicorn.Config(
            build_http_app(self._server_factory()),
            host="127.0.0.1",
            port=self.port,
            log_level="error",
            lifespan="on",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        deadline = time.monotonic() + 10
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("HTTP test server did not start within 10 s")
            time.sleep(0.05)

    def stop(self) -> None:
        if self._server is not None and self._thread is not None:
            self._server.should_exit = True
            self._thread.join(timeout=10)
        self._server = None
        self._thread = None

    def restart(self) -> None:
        # A fresh server instance stands in for a redeploy: no session state survives.
        self.stop()
        self.start()


@pytest.fixture
def http_server() -> Iterator[_HttpServer]:
    server = _HttpServer()
    server.start()
    try:
        yield server
    finally:
        server.stop()


@pytest.mark.parametrize("mode", ERAS)
async def test_in_memory_client_works_in_each_protocol_era(mode: str) -> None:
    async with Client(build_server(), mode=mode) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert {"list_economic_concepts", "get_economic_series"} <= set(tools)
        assert all(tool.annotations.read_only_hint is True for tool in tools.values())

        result = await client.call_tool("list_economic_concepts", {"query": "cash rate"})
        rows = result.structured_content["result"]
        assert any(row["concept"] == "cash_rate_target" for row in rows)

        assert (await client.read_resource("ausecon://concepts"))[0].text
        assert await client.list_prompts()


@pytest.mark.parametrize("mode", ERAS)
async def test_tool_errors_surface_in_each_protocol_era(mode: str) -> None:
    async with Client(build_server(), mode=mode) as client:
        with pytest.raises(ToolError, match="Unknown concept 'not_a_concept'"):
            await client.call_tool("get_economic_series", {"concept": "not_a_concept"})


@pytest.mark.parametrize("mode", ERAS)
async def test_http_app_serves_each_protocol_era(mode: str, http_server: _HttpServer) -> None:
    async with Client(http_server.url, mode=mode) as client:
        assert len(await client.list_tools()) == 14
        await client.call_tool("list_economic_concepts", {"query": "cash rate"})


async def test_modern_protocol_client_survives_server_restart(http_server: _HttpServer) -> None:
    async with Client(http_server.url, mode="2026-07-28") as client:
        await client.call_tool("list_economic_concepts", {})
        http_server.restart()
        await client.call_tool("list_economic_concepts", {})


@pytest.mark.parametrize("mode", ERAS)
async def test_http_large_slow_result_reaches_a_default_capped_client(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # MCP SDK v2 clients refuse any single SSE event over 1 MiB by default. Legacy replies are
    # SSE unless the server answers in JSON, and 2026-07-28 replies switch to SSE once a handler
    # runs past the SDK's ping interval (15 s; shortened here so a cold fetch fits in a test).
    monkeypatch.setattr(_streamable_http_modern, "_SSE_PING_INTERVAL", 0.1)
    service = AuseconService(rba_provider=_SlowLargeRBAProvider())
    http_server = _HttpServer(lambda: build_server(service))
    http_server.start()
    try:
        async with Client(http_server.url, mode=mode, timeout=60) as client:
            result = await client.call_tool("get_rba_table", {"table_id": "a2"})
    finally:
        http_server.stop()
    assert len(result.structured_content["observations"]) == LARGE_TABLE_OBSERVATIONS

import re

from fastmcp import Client

from ausecon_mcp.server import build_server
from ausecon_mcp.ui import CHART_RESOURCE_URI, CHART_TOOLS, load_chart_html

UI_MIME_TYPE = "text/html;profile=mcp-app"


async def test_chart_resource_is_listed_as_an_mcp_app() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        resources = {str(resource.uri): resource for resource in await client.list_resources()}

    assert CHART_RESOURCE_URI in resources
    assert resources[CHART_RESOURCE_URI].mime_type == UI_MIME_TYPE


async def test_chart_resource_serves_the_packaged_html() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        contents = await client.read_resource(CHART_RESOURCE_URI)

    assert len(contents) == 1
    assert contents[0].mime_type == UI_MIME_TYPE
    assert contents[0].text == load_chart_html()


async def test_only_chart_tools_point_at_the_chart_resource() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    assert CHART_TOOLS <= set(tools)
    for name, tool in tools.items():
        ui_meta = (tool.meta or {}).get("ui") or {}
        if name in CHART_TOOLS:
            assert ui_meta.get("resourceUri") == CHART_RESOURCE_URI, name
            # Visible to the model as well as the app: the tool stays an ordinary data tool.
            assert ui_meta.get("visibility") in (None, ["model", "app"], ["app", "model"]), name
        else:
            assert "resourceUri" not in ui_meta, name


async def test_chart_tools_still_return_plain_json_for_non_ui_clients() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    for name in CHART_TOOLS:
        assert tools[name].output_schema is not None, name


def test_chart_html_is_self_contained() -> None:
    html = load_chart_html()

    assert html.lstrip().lower().startswith("<!doctype html>")
    assert not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", html), "stray control character"
    # The sandboxed iframe gets a default-deny CSP; nothing may load from the network.
    assert not re.search(r"<script[^>]+src=", html, re.IGNORECASE)
    assert not re.search(r"<link[^>]+href=", html, re.IGNORECASE)
    assert not re.search(r"@import", html)
    assert "fetch(" not in html
    # Speaks the MCP Apps handshake and consumes tool results.
    for method in (
        "ui/initialize",
        "ui/notifications/initialized",
        "ui/notifications/tool-result",
        "ui/notifications/size-changed",
        "ui/notifications/host-context-changed",
    ):
        assert method in html, method


def test_chart_html_never_uses_inner_html_for_data() -> None:
    # Series labels come from upstream sources; they must be inserted as text.
    html = load_chart_html()

    assert "innerHTML" not in html
    assert "insertAdjacentHTML" not in html
    assert "document.write" not in html

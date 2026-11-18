import json
import re
import shutil
import subprocess

import pytest
from fastmcp import Client
from fastmcp.apps import UI_EXTENSION_ID
from mcp.client import advertise

from ausecon_mcp.server import build_server
from ausecon_mcp.ui import CHART_RESOURCE_URI, CHART_SHOWN_NOTE, CHART_TOOLS, load_chart_html

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


def test_chart_html_script_parses() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    # Slice between the tags (no HTML regex): the view has exactly one inline script.
    html = load_chart_html()
    start = html.index("<script>") + len("<script>")
    script = html[start : html.index("</script>", start)]
    assert script.strip(), "inline script missing"

    result = subprocess.run(
        [node, "--check", "-"],
        input=script,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_chart_view_can_shrink_after_content_collapses() -> None:
    # scrollHeight never drops below the iframe's current height, so a view sized from it
    # grows but never shrinks (collapsing the data table left blank space in claude.ai).
    html = load_chart_html()

    assert "scrollHeight" not in html
    assert 'html.style.height = "max-content"' in html


async def test_chart_tool_descriptions_discourage_redrawing_the_chart() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    for name in CHART_TOOLS:
        assert "Do not create another chart" in tools[name].description, name
        assert "annotation" not in tools[name].description, name


_PAYLOAD = {
    "metadata": {
        "source": "rba",
        "dataset_id": "g1",
        "server_version": "test",
        "truncated": False,
    },
    "series": [{"series_id": "GCPIOCPMTMYP", "label": "Trimmed mean", "dimensions": {}}],
    "observations": [{"date": "2026-09-30", "series_id": "GCPIOCPMTMYP", "value": 3.7}],
}


class _FakeService:
    async def get_economic_series(self, **_: object) -> dict:
        return json.loads(json.dumps(_PAYLOAD))

    async def get_derived_series(self, **_: object) -> dict:
        return json.loads(json.dumps(_PAYLOAD))

    async def list_economic_concepts(self, **_: object) -> list[dict]:
        return [{"concept": "trimmed_mean_inflation"}]


def _ui_client(mcp) -> Client:
    return Client(mcp, extensions=[advertise(UI_EXTENSION_ID, {"mimeTypes": [UI_MIME_TYPE]})])


def _texts(result) -> list[str]:
    return [block.text for block in result.content if getattr(block, "type", None) == "text"]


@pytest.mark.parametrize("tool", sorted(CHART_TOOLS))
async def test_ui_clients_are_told_the_chart_is_already_shown(tool: str) -> None:
    mcp = build_server(service=_FakeService())

    async with _ui_client(mcp) as client:
        result = await client.call_tool(tool, {"concept": "trimmed_mean_inflation"})

    texts = _texts(result)
    assert len(texts) == 2
    assert json.loads(texts[0]) == _PAYLOAD
    assert texts[1] == CHART_SHOWN_NOTE
    assert result.structured_content == _PAYLOAD


@pytest.mark.parametrize("tool", sorted(CHART_TOOLS))
async def test_text_only_clients_get_the_unchanged_json(tool: str) -> None:
    mcp = build_server(service=_FakeService())

    async with Client(mcp) as client:
        result = await client.call_tool(tool, {"concept": "trimmed_mean_inflation"})

    texts = _texts(result)
    assert len(texts) == 1
    assert json.loads(texts[0]) == _PAYLOAD


async def test_non_chart_tools_never_get_the_chart_note() -> None:
    mcp = build_server(service=_FakeService())

    async with _ui_client(mcp) as client:
        result = await client.call_tool("list_economic_concepts", {})

    assert CHART_SHOWN_NOTE not in _texts(result)


def test_chart_note_leaves_no_room_for_a_second_chart() -> None:
    assert "Do not create another chart" in CHART_SHOWN_NOTE
    assert "annotation" not in CHART_SHOWN_NOTE

import json
import re
import shutil
import subprocess

import pytest
from fastmcp import Client
from fastmcp.apps import UI_EXTENSION_ID
from mcp.client import advertise

from ausecon_mcp.server import build_server
from ausecon_mcp.ui import (
    CHART_RESOURCE_URI,
    CHART_SHOWN_NOTE,
    CHART_TOOLS,
    MAX_CHART_SERIES,
    load_chart_html,
)

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
        description = " ".join(tools[name].description.split())
        assert "Do not create another chart" in description, name
        assert "up to eight series" in description, name
        assert "annotation" not in description, name


def _payload(series_count: int = 1, numeric: bool = True) -> dict:
    series = [
        {"series_id": f"S{i}", "label": f"Series {i}", "dimensions": {}}
        for i in range(series_count)
    ]
    observations = [
        {"date": date, "series_id": f"S{i}", "value": 3.7 if numeric else None}
        for i in range(series_count)
        for date in ("2026-08-31", "2026-09-30")
    ]
    return {
        "metadata": {
            "source": "rba",
            "dataset_id": "g1",
            "server_version": "test",
            "truncated": False,
        },
        "series": series,
        "observations": observations,
    }


class _FakeService:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or _payload()

    async def _respond(self, **_: object) -> dict:
        return json.loads(json.dumps(self.payload))

    get_economic_series = _respond
    get_derived_series = _respond
    get_rba_table = _respond
    get_abs_data = _respond
    get_apra_data = _respond

    async def list_economic_concepts(self, **_: object) -> list[dict]:
        return [{"concept": "trimmed_mean_inflation"}]


_ARGS = {
    "get_economic_series": {"concept": "trimmed_mean_inflation"},
    "get_derived_series": {"concept": "real_cash_rate"},
    "get_rba_table": {"table_id": "g1"},
    "get_abs_data": {"dataflow_id": "CPI"},
    "get_apra_data": {"publication_id": "ADI_MONTHLY"},
}


def _ui_client(mcp) -> Client:
    return Client(mcp, extensions=[advertise(UI_EXTENSION_ID, {"mimeTypes": [UI_MIME_TYPE]})])


def _texts(result) -> list[str]:
    return [block.text for block in result.content if getattr(block, "type", None) == "text"]


def test_every_normalised_retrieval_tool_has_the_chart() -> None:
    assert CHART_TOOLS == set(_ARGS)


@pytest.mark.parametrize("tool", sorted(CHART_TOOLS))
async def test_ui_clients_are_told_the_chart_is_already_shown(tool: str) -> None:
    payload = _payload()
    mcp = build_server(service=_FakeService(payload))

    async with _ui_client(mcp) as client:
        result = await client.call_tool(tool, _ARGS[tool])

    (text,) = _texts(result)
    body = json.loads(text)
    assert body["metadata"]["chart_note"] == CHART_SHOWN_NOTE
    # Placed first so the model reads it before the data, even in a truncated preview.
    assert next(iter(body)) == "metadata"
    assert next(iter(body["metadata"])) == "chart_note"
    del body["metadata"]["chart_note"]
    assert body == payload
    assert result.structured_content["metadata"]["chart_note"] == CHART_SHOWN_NOTE


@pytest.mark.parametrize("tool", sorted(CHART_TOOLS))
async def test_text_only_clients_get_the_unchanged_json(tool: str) -> None:
    payload = _payload()
    mcp = build_server(service=_FakeService(payload))

    async with Client(mcp) as client:
        result = await client.call_tool(tool, _ARGS[tool])

    texts = _texts(result)
    assert len(texts) == 1
    assert json.loads(texts[0]) == payload


async def test_results_too_wide_to_chart_get_no_note() -> None:
    # The view charts at most MAX_CHART_SERIES series; beyond that it shows a short
    # "ask for specific series" line, so the model must stay free to present the data.
    mcp = build_server(service=_FakeService(_payload(MAX_CHART_SERIES + 1)))

    async with _ui_client(mcp) as client:
        result = await client.call_tool("get_rba_table", _ARGS["get_rba_table"])

    assert "chart_note" not in json.loads(_texts(result)[0])["metadata"]


async def test_results_with_nothing_numeric_get_no_note() -> None:
    mcp = build_server(service=_FakeService(_payload(2, numeric=False)))

    async with _ui_client(mcp) as client:
        result = await client.call_tool("get_rba_table", _ARGS["get_rba_table"])

    assert "chart_note" not in json.loads(_texts(result)[0])["metadata"]


async def test_series_without_numeric_values_do_not_count_towards_the_limit() -> None:
    payload = _payload(MAX_CHART_SERIES)
    payload["series"].append({"series_id": "EMPTY", "label": "Empty", "dimensions": {}})
    payload["observations"].append({"date": "2026-09-30", "series_id": "EMPTY", "value": None})
    mcp = build_server(service=_FakeService(payload))

    async with _ui_client(mcp) as client:
        result = await client.call_tool("get_rba_table", _ARGS["get_rba_table"])

    assert json.loads(_texts(result)[0])["metadata"]["chart_note"] == CHART_SHOWN_NOTE


def test_view_and_server_agree_on_the_series_limit() -> None:
    assert f"const MAX_SERIES = {MAX_CHART_SERIES};" in load_chart_html()


async def test_non_chart_tools_never_get_the_chart_note() -> None:
    mcp = build_server(service=_FakeService())

    async with _ui_client(mcp) as client:
        result = await client.call_tool("list_economic_concepts", {})

    assert all(CHART_SHOWN_NOTE not in text for text in _texts(result))


def test_chart_note_leaves_no_room_for_a_second_chart() -> None:
    assert "Do not create another chart" in CHART_SHOWN_NOTE
    assert "annotation" not in CHART_SHOWN_NOTE
    # The view's own context summary (ui/update-model-context) must say the same thing.
    html = load_chart_html()
    assert "Do not create another chart of this data" in html
    assert "annotation" not in html.lower()


async def test_single_date_results_get_no_note() -> None:
    # A last_n=1 lookup (often a model finding series codes) is a list of values, not a chart.
    payload = _payload(5)
    payload["observations"] = [o for o in payload["observations"] if o["date"] == "2026-09-30"]
    mcp = build_server(service=_FakeService(payload))

    async with _ui_client(mcp) as client:
        result = await client.call_tool("get_rba_table", _ARGS["get_rba_table"])

    assert "chart_note" not in json.loads(_texts(result)[0])["metadata"]


def test_view_shows_single_date_results_as_a_list_of_values() -> None:
    html = load_chart_html()

    assert "model.snapshot" in html
    assert 'el("ul", "snapshot")' in html


def test_chart_note_says_the_chart_is_visible_on_mobile_too() -> None:
    # On the claude.ai iPhone app the model doubted the chart had rendered and offered to
    # draw its own; the client only gets the note after declaring it renders MCP Apps.
    assert "mobile" in CHART_SHOWN_NOTE
    assert "Do not create another chart" in CHART_SHOWN_NOTE


async def test_charted_results_stay_a_single_json_document() -> None:
    # claude.ai saves a tool result's text blocks to one file for code execution. A separate
    # note block after the JSON made json.load fail with "Extra data: line 2 column 1".
    mcp = build_server(service=_FakeService(_payload(2)))

    async with _ui_client(mcp) as client:
        result = await client.call_tool("get_rba_table", _ARGS["get_rba_table"])

    joined = "\n".join(_texts(result))
    assert json.loads(joined)["series"] == _payload(2)["series"]


async def test_text_only_clients_never_see_a_chart_note() -> None:
    mcp = build_server(service=_FakeService(_payload(2)))

    async with Client(mcp) as client:
        result = await client.call_tool("get_rba_table", _ARGS["get_rba_table"])

    assert "chart_note" not in result.structured_content["metadata"]

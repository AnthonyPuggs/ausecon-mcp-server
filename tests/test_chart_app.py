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


def _y_domain(min_value: float, max_value: float, target_ticks: int = 5) -> dict:
    """Run the view's own yScaleDomain in node and return {lo, hi, ticks, step}."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    html = load_chart_html()
    start = html.index("  function niceStep(")
    source = html[start : html.index("  function timeTicks(", start)]
    script = (
        f"{source}\nprocess.stdout.write(JSON.stringify("
        f"yScaleDomain({min_value}, {max_value}, {target_ticks})));"
    )
    result = subprocess.run(
        [node, "-"], input=script, capture_output=True, text=True, encoding="utf-8", check=False
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_y_axis_does_not_add_a_whole_step_for_a_tiny_overshoot() -> None:
    # RBA F2's 2-year yield touched -0.001% on 2021-06-11; the axis ran down to -2%.
    domain = _y_domain(-0.001, 5.413)

    assert domain["ticks"][0] == 0
    assert -0.1 < domain["lo"] <= -0.001
    assert domain["hi"] >= 5.413


def test_y_axis_still_extends_a_step_for_a_real_overshoot() -> None:
    domain = _y_domain(-0.5, 5.413)

    assert domain["ticks"][0] == -2
    assert domain["lo"] == -2


def test_y_axis_ticks_stay_inside_the_domain() -> None:
    for low, high in ((-0.001, 5.413), (0.02, 6.001), (3.7, 3.7), (-12.5, 40.0)):
        domain = _y_domain(low, high)
        assert domain["lo"] <= low and domain["hi"] >= high, (low, high)
        assert all(domain["lo"] <= t <= domain["hi"] for t in domain["ticks"]), (low, high)
        assert len(domain["ticks"]) >= 2, (low, high)


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
        assert "would duplicate it" in description, name
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


def test_chart_note_says_a_second_chart_would_duplicate_it() -> None:
    assert "would duplicate what is already on screen" in CHART_SHOWN_NOTE
    assert "annotation" not in CHART_SHOWN_NOTE
    # The view's own context summary (ui/update-model-context) must say the same thing.
    html = load_chart_html()
    assert "Another chart of this data would duplicate" in html
    assert "annotation" not in html.lower()


# Anthropic's connector directory rejects tool text that tells Claude how to behave or
# interferes with its other tools, so the chart wording states facts, never commands.
_IMPERATIVES = ("do not", "don't", "never ", "no need to check", "instead.", "only draw")


async def test_chart_wording_has_no_instructions_to_the_model() -> None:
    mcp = build_server()
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    html = load_chart_html()
    start = html.index("function shareViewWithModel")
    view_summary = html[start : html.index("];", start)]
    texts = {"chart_note": CHART_SHOWN_NOTE, "view_summary": view_summary}
    texts.update({name: tools[name].description for name in CHART_TOOLS})

    for where, text in texts.items():
        lowered = " ".join(text.lower().split())
        for phrase in _IMPERATIVES:
            assert phrase not in lowered, f"{where} contains {phrase!r}"


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
    assert "already on screen" in CHART_SHOWN_NOTE


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


def _run_view(expression: str) -> object:
    """Evaluate an expression against the view's constants, helpers, and model code in node."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    html = load_chart_html()
    constants = html[html.index("  const MAX_SERIES") : html.index("  const app =")]
    start = html.index("  function el(")
    code = html[start : html.index("  function render()")]
    script = f"{constants}\n{code}\nprocess.stdout.write(JSON.stringify({expression}));"
    result = subprocess.run(
        [node, "-"], input=script, capture_output=True, text=True, encoding="utf-8", check=False
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


ABS_UNEMPLOYMENT_LABEL = (
    "Unemployment rate / Persons / Total (age) / Seasonally Adjusted / Australia / Monthly"
)


def test_abs_labels_split_into_a_measure_title_and_a_detail_line() -> None:
    parts = _run_view(f"splitLabel({json.dumps(ABS_UNEMPLOYMENT_LABEL)}, 'Monthly')")

    assert parts == {
        "title": "Unemployment rate",
        # The frequency is already in the eyebrow, so it is not repeated.
        "detail": "Persons · Total (age) · Seasonally Adjusted · Australia",
    }


def test_labels_without_dimension_separators_are_left_alone() -> None:
    parts = _run_view("splitLabel('New Cash Rate Target', 'As announced')")

    assert parts == {"title": "New Cash Rate Target", "detail": ""}


@pytest.mark.parametrize(
    ("raw", "tidy"),
    [
        (
            "A2 RESERVE BANK OF AUSTRALIA – CHANGES IN MONETARY POLICY AND ADMINISTERED RATES",
            "A2 Reserve Bank of Australia – Changes in Monetary Policy and Administered Rates",
        ),
        ("F11 EXCHANGE RATES", "F11 Exchange Rates"),
        ("G1 CONSUMER PRICE INFLATION", "G1 Consumer Price Inflation"),
        (
            "F3 NON-FINANCIAL CORPORATE (NFC) BOND SPREADS – US DOLLAR",
            "F3 Non-financial Corporate (NFC) Bond Spreads – US Dollar",
        ),
        # Titles that already use mixed case are the source's own styling.
        ("Labour Force", "Labour Force"),
    ],
)
def test_all_caps_source_titles_are_shown_in_title_case(raw: str, tidy: str) -> None:
    assert _run_view(f"tidyTitle({json.dumps(raw)})") == tidy


def test_abs_percent_and_rba_per_cent_share_one_unit() -> None:
    units = _run_view(
        "[unitLabel({unit: 'Percent'}), unitLabel({unit: 'Per cent'}),"
        " unitLabel({unit: 'Per cent per annum'})]"
    )

    assert units == ["Per cent", "Per cent", "Per cent per annum"]


def _policy_rate_result(date_window: dict | None) -> dict:
    metadata = {"source": "rba", "retrieved_at": "2026-11-19T00:00:00Z"}
    if date_window is not None:
        metadata["date_window"] = date_window
    return {
        "metadata": metadata,
        "series": [{"series_id": "R", "label": "Cash rate", "frequency": "As announced"}],
        "observations": [
            {"date": "2016-08-03", "series_id": "R", "value": 1.5},
            {"date": "2019-06-05", "series_id": "R", "value": 1.25},
        ],
    }


def test_a_carried_in_value_starts_the_chart_at_the_window_start() -> None:
    window = {"start": "2019-01-01", "end": None, "carried_in": ["R"]}
    model = _run_view(f"buildModel({json.dumps(_policy_rate_result(window))})")

    assert model["t0"] == 1546300800000  # 2019-01-01, not the 2016 announcement
    assert model["t1"] == 1795046400000  # held to the 2026-11-19 retrieval date


def test_an_end_bound_stops_the_step_line_at_the_window_end() -> None:
    window = {"start": None, "end": "2019-12-31", "carried_in": []}
    model = _run_view(f"buildModel({json.dumps(_policy_rate_result(window))})")

    # Not carried on to the 2026 retrieval date: the rate changed after the window.
    assert model["t1"] == 1577750400000  # 2019-12-31


class _RecordingService(_FakeService):
    def __init__(self, payload: dict | None = None) -> None:
        super().__init__(payload)
        self.calls: list[tuple[str, dict]] = []

    async def get_economic_series(self, **kwargs: object) -> dict:
        self.calls.append(("single", kwargs))
        return await self._respond()

    async def get_economic_series_many(self, concepts: list[str], **kwargs: object) -> dict:
        self.calls.append(("many", {"concepts": concepts, **kwargs}))
        return await self._respond()


async def test_economic_series_tool_accepts_a_list_of_concepts() -> None:
    service = _RecordingService()

    async with Client(build_server(service=service)) as client:
        await client.call_tool(
            "get_economic_series",
            {"concept": ["unemployment_rate", "cash_rate_target"], "start": "2019"},
        )

    ((kind, kwargs),) = service.calls
    assert kind == "many"
    assert kwargs["concepts"] == ["unemployment_rate", "cash_rate_target"]
    assert kwargs["start"] == "2019"


async def test_economic_series_tool_reads_a_json_encoded_list() -> None:
    # Some clients send an array argument as its JSON text.
    service = _RecordingService()

    async with Client(build_server(service=service)) as client:
        await client.call_tool(
            "get_economic_series", {"concept": '["unemployment_rate", "cash_rate_target"]'}
        )

    ((kind, kwargs),) = service.calls
    assert kind == "many"
    assert kwargs["concepts"] == ["unemployment_rate", "cash_rate_target"]


async def test_economic_series_tool_still_takes_a_plain_concept() -> None:
    service = _RecordingService()

    async with Client(build_server(service=service)) as client:
        await client.call_tool("get_economic_series", {"concept": "cash_rate_target"})

    ((kind, kwargs),) = service.calls
    assert kind == "single"
    assert kwargs["concept"] == "cash_rate_target"


async def test_economic_series_schema_allows_a_list() -> None:
    async with Client(build_server()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    concept = tools["get_economic_series"].input_schema["properties"]["concept"]
    variants = concept["anyOf"]
    assert {"type": "string", "minLength": 1} in variants
    (array,) = [v for v in variants if v.get("type") == "array"]
    assert array["items"]["type"] == "string"
    assert array["maxItems"] == 8
    assert array["minItems"] == 1


async def test_combined_results_over_eight_series_get_no_note() -> None:
    mcp = build_server(service=_RecordingService(_payload(MAX_CHART_SERIES + 1)))

    async with _ui_client(mcp) as client:
        result = await client.call_tool(
            "get_economic_series", {"concept": ["unemployment_rate", "cash_rate_target"]}
        )

    assert "chart_note" not in json.loads(_texts(result)[0])["metadata"]


def _combined(
    rba_unit: str = "Per cent", rba_frequency: str = "As announced", snapshot: bool = False
) -> dict:
    from ausecon_mcp.combine import merge_concept_payloads

    abs_part = {
        "metadata": {
            "source": "abs",
            "dataset_id": "LF",
            "title": "Labour Force",
            "frequency": "Monthly",
            "retrieval_url": "https://data.api.abs.gov.au/rest/data/LF/M13.3.1599.20.AUS.M",
            "retrieved_at": "2026-11-19T01:00:00Z",
            "server_version": "test",
            "truncated": False,
        },
        "series": [
            {
                "series_id": "U",
                "label": ABS_UNEMPLOYMENT_LABEL,
                "unit": "Percent",
                "frequency": "Monthly",
                "dimensions": {},
            }
        ],
        "observations": (
            [{"date": "2026-09", "series_id": "U", "value": 4.7}]
            if snapshot
            else [
                {"date": "2019-01", "series_id": "U", "value": 5.1},
                {"date": "2019-02", "series_id": "U", "value": 5.0},
            ]
        ),
    }
    rba_metadata = {
        "source": "rba",
        "dataset_id": "a2",
        "title": "A2 RESERVE BANK OF AUSTRALIA – CHANGES IN MONETARY POLICY AND ADMINISTERED RATES",
        "publication_date": "03-Nov-2026",
        "retrieval_url": "https://www.rba.gov.au/statistics/tables/csv/a2-data.csv",
        "retrieved_at": "2026-11-19T00:30:00Z",
        "server_version": "test",
        "truncated": False,
    }
    if not snapshot:
        rba_metadata["date_window"] = {"start": "2019-01-01", "end": None, "carried_in": ["R"]}
    rba_part = {
        "metadata": rba_metadata,
        "series": [
            {
                "series_id": "R",
                "label": "New Cash Rate Target",
                "unit": rba_unit,
                "frequency": rba_frequency,
                "dimensions": {},
            }
        ],
        "observations": (
            [{"date": "2026-11-04", "series_id": "R", "value": 4.85}]
            if snapshot
            else [
                {"date": "2016-08-03", "series_id": "R", "value": 1.5},
                {"date": "2019-06-05", "series_id": "R", "value": 1.25},
            ]
        ),
    }
    return merge_concept_payloads([("unemployment_rate", abs_part), ("cash_rate_target", rba_part)])


def test_combined_result_shares_one_percent_axis() -> None:
    assert _run_view(f"buildModel({json.dumps(_combined())}).panels.length") == 1


def test_combined_result_starts_at_the_window_despite_a_carried_value() -> None:
    assert _run_view(f"buildModel({json.dumps(_combined())}).t0") == 1546300800000


def test_combined_header_names_both_sources_and_short_titles() -> None:
    payload = json.dumps(_combined())
    header = _run_view(f"headerText({payload}.metadata, buildModel({payload}).plotted)")

    assert header == {
        "eyebrow": "ABS · RBA",
        "title": "Unemployment rate and New Cash Rate Target",
        "detail": "",
    }


def test_combined_legend_uses_short_titles() -> None:
    labels = _run_view(f"displayLabels(buildModel({json.dumps(_combined())}).plotted)")

    assert labels == ["Unemployment rate", "New Cash Rate Target"]


def test_combined_footer_has_a_line_per_source() -> None:
    lines = _run_view(f"footerLines({json.dumps(_combined())}.metadata)")

    assert len(lines) == 2
    assert lines[0]["text"].startswith("ABS Labour Force")
    assert "A2 Reserve Bank of Australia" in lines[1]["text"]
    assert "Published" in lines[1]["text"]
    assert lines[0]["url"].startswith("https://data.api.abs.gov.au/")
    assert lines[1]["url"] == "https://www.rba.gov.au/statistics/tables/csv/a2-data.csv"


def test_single_source_footer_is_one_line_without_a_source_prefix() -> None:
    payload = _policy_rate_result({"start": None, "end": None, "carried_in": []})
    payload["metadata"]["retrieval_url"] = "https://www.rba.gov.au/x.csv"

    lines = _run_view(f"footerLines({json.dumps(payload)}.metadata)")

    assert len(lines) == 1
    assert lines[0]["text"].startswith("Retrieved")
    assert lines[0]["url"] == "https://www.rba.gov.au/x.csv"


def test_mixed_units_get_stacked_panels() -> None:
    payload = json.dumps(_combined(rba_unit="Number", rba_frequency="Monthly"))

    assert _run_view(f"buildModel({payload}).panels.length") == 2


def test_combined_snapshot_lists_both_values() -> None:
    payload = json.dumps(_combined(snapshot=True))

    assert _run_view(f"buildModel({payload}).snapshot") is True
    assert _run_view(f"displayLabels(buildModel({payload}).plotted)") == [
        "Unemployment rate",
        "New Cash Rate Target",
    ]


def test_single_source_header_is_unchanged() -> None:
    single = _combined()["metadata"]["components"][0]["metadata"]
    payload = {
        "metadata": single,
        "series": [
            {
                "series_id": "U",
                "label": ABS_UNEMPLOYMENT_LABEL,
                "unit": "Percent",
                "frequency": "Monthly",
                "dimensions": {},
            }
        ],
        "observations": [
            {"date": "2019-01", "series_id": "U", "value": 5.1},
            {"date": "2019-02", "series_id": "U", "value": 5.0},
        ],
    }
    text = json.dumps(payload)

    header = _run_view(f"headerText({text}.metadata, buildModel({text}).plotted)")

    assert header == {
        "eyebrow": "ABS · Labour Force · Monthly",
        "title": "Unemployment rate",
        "detail": "Persons · Total (age) · Seasonally Adjusted · Australia",
    }


def test_two_series_with_the_same_short_title_keep_their_full_labels() -> None:
    model = "{plotted: [{label: 'Rate / Persons', desc: {}}, {label: 'Rate / Females', desc: {}}]}"

    assert _run_view(f"displayLabels({model}.plotted)") == ["Rate / Persons", "Rate / Females"]

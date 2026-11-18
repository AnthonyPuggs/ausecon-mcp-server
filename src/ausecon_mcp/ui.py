"""MCP Apps UI: an inline time-series chart for retrieval tool results.

Hosts that support the MCP Apps extension (claude.ai, Claude Desktop, and other
``io.modelcontextprotocol/ui`` clients) render ``CHART_RESOURCE_URI`` in a sandboxed
iframe next to a chart tool's result. Every other client ignores the metadata and
keeps receiving the same JSON payload, so the tools' contract is unchanged.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import pydantic_core
from fastmcp import FastMCP
from fastmcp.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools import ToolResult
from mcp.types import CallToolRequestParams, TextContent

from ausecon_mcp.logging import get_logger

CHART_RESOURCE_URI = "ui://ausecon/series-chart.html"
# Every tool that returns the normalised metadata/series/observations response.
CHART_TOOLS = frozenset(
    {
        "get_economic_series",
        "get_derived_series",
        "get_rba_table",
        "get_abs_data",
        "get_apra_data",
    }
)
# The view charts at most this many series (one per categorical colour). Wider results, such as
# an unkeyed ABS dataflow with thousands of series, get a one-line "ask for specific series"
# message instead of a chart. Keep in step with MAX_SERIES in static/series_chart.html.
MAX_CHART_SERIES = 8

# Added as metadata.chart_note to chart tool results for clients that render MCP Apps. The
# tool description alone did not stop claude.ai's Claude drawing its own chart of the same
# series; the result is what the model is reading when it decides.
#
# Kept descriptive on purpose: Anthropic's connector directory rejects tool text that tells
# Claude how to behave or interferes with its other tools, so this states what is on screen
# and leaves the decision to the model. Don't add imperatives ("Do not ...") back.
CHART_SHOWN_NOTE = (
    "This result is already displayed to the user as an interactive inline chart with a "
    "data table, on mobile as well as desktop: the user's app told this server that it "
    "displays these charts. Another chart of the same data would duplicate what is "
    "already on screen."
)

_STATIC_DIR = "static"
_CHART_FILE = "series_chart.html"


@lru_cache(maxsize=1)
def load_chart_html() -> str:
    """Return the self-contained chart view shipped with the package."""
    try:
        resource = resources.files("ausecon_mcp").joinpath(_STATIC_DIR).joinpath(_CHART_FILE)
        if resource.is_file():
            return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        pass
    return (Path(__file__).resolve().parent / _STATIC_DIR / _CHART_FILE).read_text(encoding="utf-8")


def numeric_points_by_series(payload: Any) -> dict[Any, int]:
    """Count each series' numeric observations in a retrieval payload."""
    counts: dict[Any, int] = {}
    if not isinstance(payload, dict):
        return counts
    for observation in payload.get("observations") or ():
        value = observation.get("value") if isinstance(observation, dict) else None
        if isinstance(value, int | float) and not isinstance(value, bool):
            series_id = observation.get("series_id")
            counts[series_id] = counts.get(series_id, 0) + 1
    return counts


def is_charted(payload: Any) -> bool:
    """Whether the view draws a line chart of this payload.

    It does for 1 to MAX_CHART_SERIES numeric series with at least one of them spanning two or
    more observations. A single-date result (a last_n=1 lookup) is shown as a list of values
    instead, and a wider result as a one-line "ask for fewer series" message.
    """
    counts = numeric_points_by_series(payload)
    return 0 < len(counts) <= MAX_CHART_SERIES and max(counts.values()) > 1


def chart_app_config() -> AppConfig:
    """Tool-side app metadata pointing a retrieval tool at the chart view."""
    return AppConfig(resource_uri=CHART_RESOURCE_URI)


def register_chart_resource(mcp: FastMCP) -> None:
    @mcp.resource(
        CHART_RESOURCE_URI,
        name="ausecon series chart",
        description=(
            "Interactive line chart that MCP Apps hosts render alongside results from "
            "get_economic_series, get_derived_series, get_rba_table, get_abs_data and "
            "get_apra_data."
        ),
        # No CSP domains: the view is fully inline and makes no network requests.
        app=AppConfig(prefers_border=False),
    )
    def series_chart() -> str:
        return load_chart_html()


class ChartShownNoteMiddleware(Middleware):
    """Tell UI-rendering clients that a chart tool's result is already on screen.

    Only added when the view will actually draw a chart of the result (see ``is_charted``).
    Text-only clients (Claude Code, most IDEs) get the tool's JSON unchanged.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        result = await call_next(context)
        tool = context.message.name
        if tool not in CHART_TOOLS or result.is_error:
            return result

        fastmcp_context = context.fastmcp_context
        renders_ui = bool(
            fastmcp_context is not None
            and fastmcp_context.client_supports_extension(UI_EXTENSION_ID)
        )
        charted = renders_ui and is_charted(result.structured_content)
        get_logger("ui").info(
            "chart_tool.result",
            extra={"tool": tool, "renders_ui": renders_ui, "charted": charted},
        )
        if not charted:
            return result

        structured = result.structured_content
        if not isinstance(structured, dict) or not isinstance(structured.get("metadata"), dict):
            return result
        # The note goes inside the JSON, not in a text block of its own: claude.ai saves a
        # result's text blocks to one file for code execution, and a second block after the
        # JSON broke json.load there. Metadata (with the note first) leads, so the model reads
        # the note before the data.
        annotated = {
            "metadata": {"chart_note": CHART_SHOWN_NOTE, **structured["metadata"]},
            **{key: value for key, value in structured.items() if key != "metadata"},
        }
        text = pydantic_core.to_json(annotated, fallback=str).decode()
        others = [block for block in result.content if getattr(block, "type", None) != "text"]
        return ToolResult(
            content=[TextContent(type="text", text=text), *others],
            structured_content=annotated,
            meta=result.meta,
        )

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

from fastmcp import FastMCP
from fastmcp.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools import ToolResult
from mcp.types import CallToolRequestParams, TextContent

from ausecon_mcp.logging import get_logger

CHART_RESOURCE_URI = "ui://ausecon/series-chart.html"
CHART_TOOLS = frozenset({"get_economic_series", "get_derived_series"})

# Appended to chart tool results for clients that render MCP Apps. The tool description
# alone did not stop claude.ai's Claude drawing its own chart of the same series; the
# result is what the model is reading when it decides.
CHART_SHOWN_NOTE = (
    "This result is already displayed to the user as an interactive inline chart with a "
    "data table. Do not create another chart of this data; summarise it in prose instead. "
    "Only draw a chart yourself if the user explicitly asks for a different chart."
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


def chart_app_config() -> AppConfig:
    """Tool-side app metadata pointing a retrieval tool at the chart view."""
    return AppConfig(resource_uri=CHART_RESOURCE_URI)


def register_chart_resource(mcp: FastMCP) -> None:
    @mcp.resource(
        CHART_RESOURCE_URI,
        name="Ausecon series chart",
        description=(
            "Interactive line chart that MCP Apps hosts render alongside "
            "get_economic_series and get_derived_series results."
        ),
        # No CSP domains: the view is fully inline and makes no network requests.
        app=AppConfig(prefers_border=False),
    )
    def series_chart() -> str:
        return load_chart_html()


class ChartShownNoteMiddleware(Middleware):
    """Tell UI-rendering clients that a chart tool's result is already on screen.

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
        get_logger("ui").info("chart_tool.result", extra={"tool": tool, "renders_ui": renders_ui})
        if not renders_ui:
            return result

        content: list[Any] = [*result.content, TextContent(type="text", text=CHART_SHOWN_NOTE)]
        return ToolResult(
            content=content,
            structured_content=result.structured_content,
            meta=result.meta,
        )

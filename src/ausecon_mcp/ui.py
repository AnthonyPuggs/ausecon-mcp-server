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

from fastmcp import FastMCP
from fastmcp.apps import AppConfig

CHART_RESOURCE_URI = "ui://ausecon/series-chart.html"
CHART_TOOLS = frozenset({"get_economic_series", "get_derived_series"})

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

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.resolver import CURATED_SHORTCUTS

_CATALOGUE_SUMMARY_FIELDS = (
    "id",
    "source",
    "name",
    "description",
    "category",
    "frequency",
    "tags",
)


def _summarise(entry: dict) -> dict:
    return {field: entry.get(field) for field in _CATALOGUE_SUMMARY_FIELDS}


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "ausecon://catalogue",
        name="Ausecon catalogue index",
        description=(
            "Flat index of every curated ABS and RBA dataset the server exposes. "
            "Use this to browse what is available before calling search_datasets."
        ),
        mime_type="application/json",
        annotations={"readOnlyHint": True},
    )
    def catalogue_index() -> list[dict]:
        return [
            _summarise(entry)
            for entry in list(ABS_CATALOGUE.values()) + list(RBA_CATALOGUE.values())
        ]

    @mcp.resource(
        "ausecon://concepts",
        name="Ausecon semantic concepts",
        description=(
            "Every curated semantic shortcut accepted by get_economic_series, with its "
            "resolved target dataset, variant, supported frequencies, and geographies."
        ),
        mime_type="application/json",
        annotations={"readOnlyHint": True},
    )
    def concepts_index() -> list[dict]:
        rows: list[dict] = []
        for concept, shortcut in CURATED_SHORTCUTS.items():
            source = shortcut["source"]
            dataset_id = shortcut["dataset_id"]
            catalogue = ABS_CATALOGUE if source == "abs" else RBA_CATALOGUE
            entry = catalogue.get(dataset_id, {})
            rows.append(
                {
                    "concept": concept,
                    "source": source,
                    "dataset_id": dataset_id,
                    "variant": shortcut.get("variant"),
                    "frequencies": list(entry.get("frequencies", [])),
                    "geographies": list(entry.get("geographies", [])),
                }
            )
        return rows

    @mcp.resource(
        "ausecon://abs/{dataflow_id}",
        name="ABS catalogue entry",
        description="Curated metadata for a single ABS dataflow.",
        mime_type="application/json",
        annotations={"readOnlyHint": True},
    )
    def abs_entry(dataflow_id: str) -> dict:
        entry = ABS_CATALOGUE.get(dataflow_id)
        if entry is None:
            raise ResourceError(f"Unknown ABS dataflow_id: {dataflow_id!r}")
        return entry

    @mcp.resource(
        "ausecon://rba/{table_id}",
        name="RBA catalogue entry",
        description="Curated metadata for a single RBA statistical table.",
        mime_type="application/json",
        annotations={"readOnlyHint": True},
    )
    def rba_entry(table_id: str) -> dict:
        entry = RBA_CATALOGUE.get(table_id)
        if entry is None:
            raise ResourceError(f"Unknown RBA table_id: {table_id!r}")
        return entry

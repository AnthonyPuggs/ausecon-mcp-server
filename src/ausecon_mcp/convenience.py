from __future__ import annotations

from copy import deepcopy
from typing import Any

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.resolver import resolve_abs_dataflow_id, resolve_rba_csv_path
from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.identity import geography_alias_rows


def select_top_observations(payload: dict[str, Any], *, n: int, direction: str) -> dict[str, Any]:
    result = deepcopy(payload)
    observations = list(result.get("observations", []))
    numeric = [row for row in observations if isinstance(row.get("value"), int | float)]
    reverse = direction == "highest"
    ranked = sorted(
        numeric,
        key=lambda row: (
            row["value"],
            str(row.get("date", "")),
            str(row.get("series_id", "")),
        ),
        reverse=reverse,
    )
    selected = ranked[:n]
    selected_series_ids = {row["series_id"] for row in selected}
    result["observations"] = selected
    result["series"] = [
        row for row in result.get("series", []) if row.get("series_id") in selected_series_ids
    ]
    result.setdefault("metadata", {})["selection"] = {
        "type": "top_n",
        "n": n,
        "direction": direction,
        "numeric_observation_count": len(numeric),
        "returned_observation_count": len(selected),
        "dropped_non_numeric_count": len(observations) - len(numeric),
    }
    return result


def describe_dataset(
    source: str,
    identifier: str,
    *,
    table_id: str | None = None,
    structure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = _entry(source, identifier)
    description = {
        "source": source,
        "id": entry["id"],
        "name": entry["name"],
        "plain_english_summary": entry.get("description", ""),
        "category": entry.get("category"),
        "frequency": entry.get("frequency"),
        "frequencies": list(entry.get("frequencies", [])),
        "geographies": list(entry.get("geographies", [])),
        "geography_aliases": geography_alias_rows(),
        "tags": list(entry.get("tags", [])),
        "aliases": list(entry.get("aliases", [])),
        "native_ids": _native_ids(source, entry, table_id=table_id),
        "variants": _variant_rows(source, entry),
        "tables": _table_rows(source, entry, table_id=table_id),
        "warnings": _warning_rows(entry),
        "framework_breaks": list(entry.get("framework_breaks", [])),
        "recommended_call": _recommended_call(source, entry, table_id=table_id),
    }
    if structure is not None:
        description["structure"] = {
            "id": structure.get("id"),
            "dimensions": structure.get("dimensions", []),
        }
    return description


def _entry(source: str, identifier: str) -> dict[str, Any]:
    catalogue = {"abs": ABS_CATALOGUE, "rba": RBA_CATALOGUE, "apra": APRA_CATALOGUE}[source]
    entry = catalogue.get(identifier)
    if entry is None:
        raise AuseconValidationError(f"Unknown {source.upper()} dataset {identifier!r}.")
    return entry


def _native_ids(source: str, entry: dict[str, Any], *, table_id: str | None) -> dict[str, Any]:
    if source == "abs":
        return {
            "dataflow_id": entry["id"],
            "upstream_id": resolve_abs_dataflow_id(entry["id"]),
            "structure_id": entry.get("structure_id", entry["id"]),
        }
    if source == "rba":
        return {
            "table_id": entry["id"],
            "csv_path": resolve_rba_csv_path(entry["id"]),
        }
    native = {
        "publication_id": entry["id"],
        "landing_url": entry["landing_url"],
        "link_patterns": list(entry.get("link_patterns", [])),
    }
    if table_id is not None:
        if table_id not in entry.get("tables", {}):
            known = ", ".join(sorted(entry.get("tables", {})))
            raise AuseconValidationError(
                f"Unknown APRA table {table_id!r} for {entry['id']!r}. Known tables: {known}."
            )
        native["table_id"] = table_id
    return native


def _variant_rows(source: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for variant in entry.get("variants", []):
        row = {
            "name": variant["name"],
            "aliases": list(variant.get("aliases", [])),
            "frequency": variant.get("frequency", entry.get("frequency")),
        }
        if source == "abs":
            row["abs_key"] = variant.get("abs_key")
        elif source == "rba":
            row["rba_series_ids"] = list(variant.get("rba_series_ids", []))
        else:
            row["apra_table_id"] = variant.get("apra_table_id")
            row["apra_series_ids"] = list(variant.get("apra_series_ids", []))
        rows.append(row)
    return rows


def _table_rows(
    source: str,
    entry: dict[str, Any],
    *,
    table_id: str | None,
) -> list[dict[str, Any]]:
    if source != "apra":
        return []
    tables = entry.get("tables", {})
    selected = {table_id: tables[table_id]} if table_id is not None else tables
    return [
        {
            "id": key,
            "title": table.get("title"),
            "sheet": table.get("sheet"),
            "layout": table.get("layout"),
            "frequency": table.get("frequency", entry.get("frequency")),
            "unit": table.get("unit"),
        }
        for key, table in selected.items()
    ]


def _warning_rows(entry: dict[str, Any]) -> list[str]:
    return [_format_framework_break_warning(item) for item in entry.get("framework_breaks", [])]


def _format_framework_break_warning(item: dict[str, Any]) -> str:
    label = item.get("label", "Framework break")
    date = item.get("date", "unknown date")
    description = item.get("description", "")
    if description:
        return f"{label} on {date}: {description}"
    return f"{label} on {date}."


def _recommended_call(
    source: str,
    entry: dict[str, Any],
    *,
    table_id: str | None,
) -> dict[str, Any]:
    if source == "abs":
        return {"tool": "get_abs_data", "arguments": {"dataflow_id": entry["id"], "key": "all"}}
    if source == "rba":
        return {"tool": "get_rba_table", "arguments": {"table_id": entry["id"]}}
    arguments = {"publication_id": entry["id"]}
    if table_id is not None:
        arguments["table_id"] = table_id
    return {"tool": "get_apra_data", "arguments": arguments}


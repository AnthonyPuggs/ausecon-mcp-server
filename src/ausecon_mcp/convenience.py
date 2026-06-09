from __future__ import annotations

from copy import deepcopy
from typing import Any

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.resolver import resolve_abs_dataflow_id, resolve_rba_csv_path
from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.governance.apra import audit_apra_governance, load_apra_seed_manifest
from ausecon_mcp.identity import geography_alias_rows


def select_latest_observations(payload: dict[str, Any], *, count: int) -> dict[str, Any]:
    result = deepcopy(payload)
    result.setdefault("metadata", {})["selection"] = {
        "type": "latest",
        "n": count,
        "series_count": len(result.get("series", [])),
        "returned_observation_count": len(result.get("observations", [])),
    }
    return result


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
        "ceased": bool(entry.get("ceased", False)),
        "successor": entry.get("successor"),
        "recommended_call": _recommended_call(source, entry, table_id=table_id),
        "source_controls": _source_controls(source, entry, table_id=table_id),
        "convenience_calls": _convenience_calls(source, entry, table_id=table_id),
        "governance": _governance_summary(source, entry),
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
        row["recommended_call"] = _variant_recommended_call(source, entry, variant)
        row["convenience_calls"] = _variant_convenience_calls(source, entry, variant)
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


def _variant_recommended_call(
    source: str,
    entry: dict[str, Any],
    variant: dict[str, Any],
) -> dict[str, Any]:
    if source == "abs":
        return {
            "tool": "get_abs_data",
            "arguments": {
                "dataflow_id": entry["id"],
                "key": variant.get("abs_key", "all"),
            },
        }
    if source == "rba":
        return {
            "tool": "get_rba_table",
            "arguments": {
                "table_id": entry["id"],
                "series_ids": list(variant.get("rba_series_ids", [])),
            },
        }
    return {
        "tool": "get_apra_data",
        "arguments": {
            "publication_id": entry["id"],
            "table_id": variant.get("apra_table_id"),
            "series_ids": list(variant.get("apra_series_ids", [])),
        },
    }


def _convenience_calls(
    source: str,
    entry: dict[str, Any],
    *,
    table_id: str | None,
) -> dict[str, dict[str, Any]]:
    latest_args: dict[str, Any] = {
        "source": source,
        "identifier": entry["id"],
        "count": 1,
    }
    top_args: dict[str, Any] = {
        "source": source,
        "identifier": entry["id"],
        "n": 10,
        "direction": "highest",
    }
    if source == "apra" and table_id is not None:
        latest_args["table_id"] = table_id
        top_args["table_id"] = table_id
    return {
        "latest": {"tool": "get_latest_observations", "arguments": latest_args},
        "top": {"tool": "get_top_observations", "arguments": top_args},
    }


def _variant_convenience_calls(
    source: str,
    entry: dict[str, Any],
    variant: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    calls = _convenience_calls(source, entry, table_id=variant.get("apra_table_id"))
    if source == "abs":
        calls["latest"]["arguments"]["key"] = variant.get("abs_key", "all")
        calls["top"]["arguments"]["key"] = variant.get("abs_key", "all")
    elif source == "rba":
        series_ids = list(variant.get("rba_series_ids", []))
        calls["latest"]["arguments"]["series_ids"] = series_ids
        calls["top"]["arguments"]["series_ids"] = series_ids
    elif source == "apra":
        series_ids = list(variant.get("apra_series_ids", []))
        calls["latest"]["arguments"]["series_ids"] = series_ids
        calls["top"]["arguments"]["series_ids"] = series_ids
    return calls


def _source_controls(
    source: str,
    entry: dict[str, Any],
    *,
    table_id: str | None,
) -> dict[str, Any]:
    if source == "abs":
        return {
            "identifier_field": "dataflow_id",
            "identifier": entry["id"],
            "native_ids": _native_ids(source, entry, table_id=None),
            "date_bounds": {"start": "start_period", "end": "end_period"},
            "supported_filters": ["key", "start_period", "end_period", "last_n", "updated_after"],
            "unsupported_arguments": ["table_id", "series_ids", "start_date", "end_date"],
        }
    if source == "rba":
        return {
            "identifier_field": "table_id",
            "identifier": entry["id"],
            "native_ids": _native_ids(source, entry, table_id=None),
            "date_bounds": {"start": "start_date", "end": "end_date"},
            "supported_filters": ["series_ids", "start_date", "end_date", "last_n"],
            "unsupported_arguments": ["key", "table_id", "start_period", "end_period"],
        }
    return {
        "identifier_field": "publication_id",
        "identifier": entry["id"],
        "native_ids": _native_ids(source, entry, table_id=table_id),
        "date_bounds": {"start": "start_date", "end": "end_date"},
        "supported_filters": ["table_id", "series_ids", "start_date", "end_date", "last_n"],
        "unsupported_arguments": ["key", "start_period", "end_period"],
    }


def _governance_summary(source: str, entry: dict[str, Any]) -> dict[str, Any]:
    audit = entry.get("audit", {})
    if source != "apra":
        return {
            "audit": audit,
            "audit_last_audited": audit.get("last_audited"),
            "warnings": [],
            "framework_breaks": [],
        }

    seed_manifest = load_apra_seed_manifest()
    row = audit_apra_governance(
        {entry["id"]: entry},
        seed_manifest={entry["id"]: seed_manifest.get(entry["id"], [])},
    )[0]
    return {
        "audit": audit,
        "audit_last_audited": row["audit_last_audited"],
        "governance_status": row["status"],
        "governance_issues": row["issues"],
        "resolved_url": row["resolved_url"],
        "resolution_strategy": row["resolution_strategy"],
        "seed_checked_at": row["seed_checked_at"],
        "accepts_arbitrary_urls": False,
        "trusted_url_hosts": ["apra.gov.au", "www.apra.gov.au"],
        "framework_breaks": list(entry.get("framework_breaks", [])),
        "warnings": _warning_rows(entry),
    }

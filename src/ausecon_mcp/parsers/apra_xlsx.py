from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.models import Observation, SeriesDescriptor, parse_float

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_apra_xlsx(
    content: bytes,
    *,
    publication_id: str,
    title: str,
    frequency: str,
    table_maps: dict[str, dict[str, Any]],
    table_id: str | None = None,
) -> dict[str, Any]:
    """Parse a curated APRA XLSX workbook into the normal retrieval response shape."""
    selected_maps = _select_table_maps(table_maps, table_id)
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    series_by_id: dict[str, dict[str, Any]] = {}
    observations: list[dict[str, Any]] = []

    for selected_table_id, table_map in selected_maps.items():
        sheet_name = str(table_map["sheet"])
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"APRA workbook did not contain sheet {sheet_name!r}.")
        sheet = workbook[sheet_name]
        layout = table_map["layout"]
        if layout == "row_records":
            table_series, table_observations = _parse_row_records(
                sheet,
                publication_id=publication_id,
                table_id=selected_table_id,
                table_map=table_map,
            )
        elif layout == "matrix":
            table_series, table_observations = _parse_matrix(
                sheet,
                publication_id=publication_id,
                table_id=selected_table_id,
                table_map=table_map,
            )
        else:
            raise ValueError(f"Unsupported APRA table layout: {layout!r}.")

        for item in table_series:
            series_by_id.setdefault(item["series_id"], item)
        observations.extend(table_observations)

    series_order = {series_id: index for index, series_id in enumerate(series_by_id)}
    return {
        "metadata": {
            "source": "apra",
            "dataset_id": publication_id,
            "frequency": frequency,
            "title": title,
        },
        "series": list(series_by_id.values()),
        "observations": sorted(
            observations,
            key=lambda item: (
                str(item["date"]),
                series_order.get(str(item["series_id"]), 0),
                str(item.get("dimensions", {})),
            ),
        ),
    }


def _select_table_maps(
    table_maps: dict[str, dict[str, Any]],
    table_id: str | None,
) -> dict[str, dict[str, Any]]:
    if table_id is None:
        return table_maps
    if table_id not in table_maps:
        known = ", ".join(sorted(table_maps))
        raise AuseconValidationError(
            f"Unknown APRA table {table_id!r}. Known tables: {known or '(none)'}."
        )
    return {table_id: table_maps[table_id]}


def _parse_row_records(
    sheet: Any,
    *,
    publication_id: str,
    table_id: str,
    table_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    header_row = int(table_map["header_row"])
    data_start_row = int(table_map["data_start_row"])
    date_column = int(table_map["date_column"])
    dimension_columns: dict[str, int] = dict(table_map.get("dimension_columns", {}))
    identity_columns: list[str] = list(table_map.get("identity_columns", []))
    series_start_column = int(table_map["series_start_column"])
    max_column = sheet.max_column or series_start_column

    metric_headers = {
        column: _clean_label(sheet.cell(header_row, column).value)
        for column in range(series_start_column, max_column + 1)
    }
    metric_headers = {column: label for column, label in metric_headers.items() if label}

    series_by_id: dict[str, dict[str, Any]] = {}
    observations: list[dict[str, Any]] = []

    for row_index in range(data_start_row, (sheet.max_row or data_start_row) + 1):
        parsed_date = _parse_date(sheet.cell(row_index, date_column).value)
        if parsed_date is None:
            continue
        dimension_values = {
            name: _clean_label(sheet.cell(row_index, column).value)
            for name, column in dimension_columns.items()
        }
        dimension_values = {name: value for name, value in dimension_values.items() if value}
        identity = _identity_slug(dimension_values, identity_columns)
        if not identity:
            identity = f"row_{row_index}"

        for column, metric_label in metric_headers.items():
            value, raw_value = _parse_observation_value(sheet.cell(row_index, column).value)
            if value is None and raw_value is None:
                continue
            metric_slug = _slug(metric_label)
            series_id = f"{publication_id}:{table_id}:{identity}:{metric_slug}"
            dimensions = _row_dimensions(table_id, table_map, dimension_values)
            if series_id not in series_by_id:
                entity_label = _entity_label(dimension_values)
                label = f"{entity_label} - {metric_label}" if entity_label else metric_label
                series_by_id[series_id] = SeriesDescriptor(
                    series_id=series_id,
                    label=label,
                    unit=table_map.get("unit"),
                    frequency=table_map.get("frequency"),
                    dimensions=dimensions,
                    source_key=metric_label,
                ).to_dict()
            observations.append(
                Observation(
                    date=parsed_date,
                    series_id=series_id,
                    value=value,
                    raw_value=raw_value,
                    dimensions=dimensions,
                ).to_dict()
            )

    return list(series_by_id.values()), observations


def _parse_matrix(
    sheet: Any,
    *,
    publication_id: str,
    table_id: str,
    table_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    date_row = int(table_map["date_row"])
    date_start_column = int(table_map["date_start_column"])
    data_start_row = int(table_map["data_start_row"])
    label_column = int(table_map["label_column"])

    date_columns: list[tuple[int, str]] = []
    for column in range(date_start_column, (sheet.max_column or date_start_column) + 1):
        parsed_date = _parse_date(sheet.cell(date_row, column).value)
        if parsed_date is not None:
            date_columns.append((column, parsed_date))
    if not date_columns:
        raise ValueError(f"APRA matrix table {table_id!r} did not contain date columns.")

    series_by_id: dict[str, dict[str, Any]] = {}
    observations: list[dict[str, Any]] = []
    section_label: str | None = None

    for row_index in range(data_start_row, (sheet.max_row or data_start_row) + 1):
        row_label = _clean_label(sheet.cell(row_index, label_column).value)
        if not row_label:
            continue
        values = [
            _parse_observation_value(sheet.cell(row_index, column).value)
            for column, _ in date_columns
        ]
        has_observations = any(value is not None or raw is not None for value, raw in values)
        if not has_observations:
            if not row_label.lower().endswith(":"):
                section_label = row_label
            continue

        metric_slug = _slug(row_label)
        section_slug = _slug(section_label) if section_label else None
        series_id = (
            f"{publication_id}:{table_id}:{section_slug}:{metric_slug}"
            if section_slug
            else f"{publication_id}:{table_id}:{metric_slug}"
        )
        dimensions = _matrix_dimensions(table_id, table_map, section_label)
        if series_id not in series_by_id:
            label = f"{section_label}: {row_label}" if section_label else row_label
            series_by_id[series_id] = SeriesDescriptor(
                series_id=series_id,
                label=label,
                unit=table_map.get("unit"),
                frequency=table_map.get("frequency"),
                dimensions=dimensions,
                source_key=row_label,
            ).to_dict()

        for (_column, parsed_date), (value, raw_value) in zip(date_columns, values, strict=False):
            if value is None and raw_value is None:
                continue
            observations.append(
                Observation(
                    date=parsed_date,
                    series_id=series_id,
                    value=value,
                    raw_value=raw_value,
                    dimensions=dimensions,
                ).to_dict()
            )

    return list(series_by_id.values()), observations


def _row_dimensions(
    table_id: str,
    table_map: dict[str, Any],
    dimension_values: dict[str, str],
) -> dict[str, dict[str, str]]:
    dimensions = {
        "table": {
            "code": table_id,
            "label": str(table_map.get("title") or table_id),
        }
    }
    for name, value in dimension_values.items():
        dimensions[name] = {"code": value, "label": value}
    return dimensions


def _matrix_dimensions(
    table_id: str,
    table_map: dict[str, Any],
    section_label: str | None,
) -> dict[str, dict[str, str]]:
    dimensions = {
        "table": {
            "code": table_id,
            "label": str(table_map.get("title") or table_id),
        }
    }
    if section_label:
        dimensions["section"] = {"code": _slug(section_label), "label": section_label}
    return dimensions


def _parse_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for fmt in ("%b %Y", "%B %Y"):
            try:
                parsed = datetime.strptime(text, fmt)
            except ValueError:
                continue
            day = calendar.monthrange(parsed.year, parsed.month)[1]
            return date(parsed.year, parsed.month, day).isoformat()
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return None
    return None


def _parse_observation_value(value: Any) -> tuple[float | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, str(value)
    if isinstance(value, int | float):
        return float(value), None
    text = str(value).strip()
    if not text:
        return None, None
    try:
        return parse_float(text), None
    except ValueError:
        return None, text


def _identity_slug(
    dimension_values: dict[str, str],
    identity_columns: list[str],
) -> str:
    values = [dimension_values.get(name, "") for name in identity_columns]
    return ":".join(_slug(value) for value in values if value)


def _entity_label(dimension_values: dict[str, str]) -> str | None:
    for key in ("institution", "entity", "abn"):
        value = dimension_values.get(key)
        if value:
            return value
    return None


def _clean_label(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def _slug(value: str) -> str:
    slug = _SLUG_RE.sub("_", value.strip().lower()).strip("_")
    return slug or "unknown"

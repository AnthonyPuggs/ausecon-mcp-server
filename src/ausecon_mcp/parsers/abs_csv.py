from __future__ import annotations

import csv
import re
from io import StringIO

from ausecon_mcp.models import Observation, SeriesDescriptor, parse_float, split_code_and_label

# Non-dimension SDMX fields across the supported ABS CSV layouts: code-only
# ``csvfile``, the legacy "CODE: Label" merged-header variant, and
# ``csvfilewithlabels``, which pairs every code column with an adjacent
# human-readable label column and replaces DATAFLOW with the
# STRUCTURE/STRUCTURE_ID/STRUCTURE_NAME/ACTION quartet.
_RESERVED_IDS = {
    "ACTION",
    "BASE_PERIOD",
    "DATAFLOW",
    "DECIMALS",
    "OBS_COMMENT",
    "OBS_STATUS",
    "OBS_VALUE",
    "STRUCTURE",
    "STRUCTURE_ID",
    "STRUCTURE_NAME",
    "TIME_PERIOD",
    "UNIT_MEASURE",
    "UNIT_MULT",
}

_SDMX_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")


def parse_abs_csv(csv_text: str) -> dict:
    reader = csv.DictReader(StringIO(csv_text))
    fieldnames = [name for name in (reader.fieldnames or []) if name is not None]
    label_columns = _pair_label_columns(fieldnames)
    label_column_names = set(label_columns.values())
    series_index: dict[str, SeriesDescriptor] = {}
    observations: list[dict] = []
    rows = list(reader)
    if not rows:
        raise ValueError("ABS CSV payload was empty")

    dataset_id = _parse_dataset_id(_row_value(rows[0], "DATAFLOW", "STRUCTURE_ID"))
    title = _none_if_empty(_row_value(rows[0], "STRUCTURE_NAME"))
    frequency = None
    for row in rows:
        dimension_values = _extract_dimensions(row, label_columns, label_column_names)
        series_id = "|".join(f"{key}={value['code']}" for key, value in dimension_values.items())
        if series_id not in series_index:
            frequency = frequency or dimension_values.get("FREQ", {}).get("label")
            unit = _labelled_value(
                row, label_columns, "UNIT_MEASURE", "UNIT_MEASURE: Unit of Measure"
            )
            series_index[series_id] = SeriesDescriptor(
                series_id=series_id,
                label=" / ".join(value["label"] for value in dimension_values.values()),
                unit=unit,
                frequency=dimension_values.get("FREQ", {}).get("label"),
                dimensions=dimension_values,
                source_key=_row_value(row, "DATAFLOW", "STRUCTURE_ID"),
                unit_multiplier=_parse_int(
                    _row_value(row, "UNIT_MULT", "UNIT_MULT: Unit Multiplier")
                ),
                decimals=_parse_int(_row_value(row, "DECIMALS", "DECIMALS: Decimals")),
                base_period=_none_if_empty(
                    _labelled_value(
                        row, label_columns, "BASE_PERIOD", "BASE_PERIOD: Reference Base Period"
                    )
                ),
            )

        observations.append(
            Observation(
                date=_row_value(row, "TIME_PERIOD", "TIME_PERIOD: Time Period"),
                series_id=series_id,
                value=parse_float(row["OBS_VALUE"]),
                dimensions=dimension_values,
                status=split_code_and_label(
                    _row_value(row, "OBS_STATUS", "OBS_STATUS: Observation Status")
                )[0]
                or None,
                comment=_none_if_empty(
                    _row_value(row, "OBS_COMMENT", "OBS_COMMENT: Observation Comment")
                ),
            ).to_dict()
        )

    metadata = {
        "source": "abs",
        "dataset_id": dataset_id,
        "frequency": frequency,
    }
    if title is not None:
        metadata["title"] = title
    return {
        "metadata": metadata,
        "series": [descriptor.to_dict() for descriptor in series_index.values()],
        "observations": observations,
    }


def _parse_dataset_id(dataflow: str) -> str:
    payload = dataflow.split(":", 1)[-1]
    return payload.split("(", 1)[0]


def _pair_label_columns(fieldnames: list[str]) -> dict[str, str]:
    """Map each code column to the adjacent label column from csvfilewithlabels.

    In that layout every SDMX field is followed by a human-readable label column
    (e.g. ``REGION`` then ``Region``). Code-only and merged "CODE: Label" headers
    produce no pairs, so those layouts are unaffected.
    """
    pairs: dict[str, str] = {}
    for index, column in enumerate(fieldnames[:-1]):
        next_column = fieldnames[index + 1]
        if _SDMX_ID.match(column) and not _SDMX_ID.match(next_column) and ":" not in next_column:
            pairs[column] = next_column
    return pairs


def _extract_dimensions(
    row: dict[str, str],
    label_columns: dict[str, str],
    label_column_names: set[str],
) -> dict[str, dict[str, str]]:
    dimensions: dict[str, dict[str, str]] = {}
    for column, value in row.items():
        if column is None or column in label_column_names or value is None:
            continue
        dimension_id = column.split(":", 1)[0]
        if dimension_id in _RESERVED_IDS:
            continue
        code, label = split_code_and_label(value)
        paired_label = (row.get(label_columns.get(column, "")) or "").strip()
        if paired_label:
            label = paired_label
        dimensions[dimension_id] = {"code": code, "label": label}
    return dimensions


def _labelled_value(
    row: dict[str, str],
    label_columns: dict[str, str],
    column: str,
    *candidates: str,
) -> str:
    paired_label = (row.get(label_columns.get(column, "")) or "").strip()
    if paired_label:
        return paired_label
    return split_code_and_label(_row_value(row, column, *candidates))[1]


def _row_value(row: dict[str, str], *candidates: str) -> str:
    for key in candidates:
        value = row.get(key)
        if value is not None:
            return value
    return ""


def _none_if_empty(value: str) -> str | None:
    text = (value or "").strip()
    return text or None


def _parse_int(value: str) -> int | None:
    text = (value or "").strip()
    if not text:
        return None
    return int(text)

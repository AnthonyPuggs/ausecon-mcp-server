from __future__ import annotations

import csv
from io import StringIO

from ausecon_mcp.models import Observation, SeriesDescriptor, parse_float, split_code_and_label

_RESERVED_COLUMNS = {
    "DATAFLOW",
    "TIME_PERIOD",
    "TIME_PERIOD: Time Period",
    "OBS_VALUE",
    "UNIT_MEASURE",
    "UNIT_MEASURE: Unit of Measure",
    "UNIT_MULT",
    "UNIT_MULT: Unit Multiplier",
    "OBS_STATUS",
    "OBS_STATUS: Observation Status",
    "DECIMALS",
    "DECIMALS: Decimals",
    "OBS_COMMENT",
    "OBS_COMMENT: Observation Comment",
    "BASE_PERIOD",
    "BASE_PERIOD: Reference Base Period",
}


def parse_abs_csv(csv_text: str) -> dict:
    reader = csv.DictReader(StringIO(csv_text))
    series_index: dict[str, SeriesDescriptor] = {}
    observations: list[dict] = []
    rows = list(reader)
    if not rows:
        raise ValueError("ABS CSV payload was empty")

    dataset_id = _parse_dataset_id(rows[0]["DATAFLOW"])
    frequency = None
    for row in rows:
        dimension_values = _extract_dimensions(row)
        series_id = "|".join(f"{key}={value['code']}" for key, value in dimension_values.items())
        if series_id not in series_index:
            frequency = frequency or dimension_values.get("FREQ", {}).get("label")
            unit = split_code_and_label(
                _row_value(row, "UNIT_MEASURE", "UNIT_MEASURE: Unit of Measure")
            )[1]
            series_index[series_id] = SeriesDescriptor(
                series_id=series_id,
                label=" / ".join(value["label"] for value in dimension_values.values()),
                unit=unit,
                frequency=dimension_values.get("FREQ", {}).get("label"),
                dimensions=dimension_values,
                source_key=row["DATAFLOW"],
                unit_multiplier=_parse_int(
                    _row_value(row, "UNIT_MULT", "UNIT_MULT: Unit Multiplier")
                ),
                decimals=_parse_int(_row_value(row, "DECIMALS", "DECIMALS: Decimals")),
                base_period=_none_if_empty(
                    _row_value(row, "BASE_PERIOD", "BASE_PERIOD: Reference Base Period")
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

    return {
        "metadata": {
            "source": "abs",
            "dataset_id": dataset_id,
            "frequency": frequency,
        },
        "series": [descriptor.to_dict() for descriptor in series_index.values()],
        "observations": observations,
    }


def _parse_dataset_id(dataflow: str) -> str:
    payload = dataflow.split(":", 1)[-1]
    return payload.split("(", 1)[0]


def _extract_dimensions(row: dict[str, str]) -> dict[str, dict[str, str]]:
    dimensions: dict[str, dict[str, str]] = {}
    for column, value in row.items():
        if column is None or column in _RESERVED_COLUMNS or value is None:
            continue
        dimension_id = column.split(":", 1)[0]
        code, label = split_code_and_label(value)
        dimensions[dimension_id] = {"code": code, "label": label}
    return dimensions


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

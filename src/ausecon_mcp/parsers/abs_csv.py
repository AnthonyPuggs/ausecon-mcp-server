from __future__ import annotations

import csv
from io import StringIO

from ausecon_mcp.models import Observation, SeriesDescriptor, parse_float, split_code_and_label

_RESERVED_COLUMNS = {
    "DATAFLOW",
    "TIME_PERIOD: Time Period",
    "OBS_VALUE",
    "UNIT_MEASURE: Unit of Measure",
    "OBS_STATUS: Observation Status",
    "DECIMALS: Decimals",
    "OBS_COMMENT: Observation Comment",
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
            series_index[series_id] = SeriesDescriptor(
                series_id=series_id,
                label=" / ".join(value["label"] for value in dimension_values.values()),
                unit=split_code_and_label(row["UNIT_MEASURE: Unit of Measure"])[1],
                frequency=dimension_values.get("FREQ", {}).get("label"),
                dimensions=dimension_values,
                source_key=row["DATAFLOW"],
            )

        observations.append(
            Observation(
                date=row["TIME_PERIOD: Time Period"],
                series_id=series_id,
                value=parse_float(row["OBS_VALUE"]),
                dimensions=dimension_values,
                status=split_code_and_label(row["OBS_STATUS: Observation Status"])[0] or None,
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
        if column in _RESERVED_COLUMNS or value is None:
            continue
        dimension_id = column.split(":", 1)[0]
        code, label = split_code_and_label(value)
        dimensions[dimension_id] = {"code": code, "label": label}
    return dimensions

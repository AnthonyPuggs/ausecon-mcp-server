from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO

from ausecon_mcp.models import Observation, SeriesDescriptor, parse_float

_METADATA_KEYS = {
    "Title",
    "Description",
    "Frequency",
    "Type",
    "Units",
    "Source",
    "Publication date",
    "Series ID",
}


def parse_rba_csv(csv_text: str, table_id: str) -> dict:
    rows = list(csv.reader(StringIO(csv_text.lstrip("\ufeff"))))
    if not rows:
        raise ValueError("RBA CSV payload was empty")

    table_title = rows[0][0].strip()
    metadata_rows = {}
    data_start = None
    for index, row in enumerate(rows[1:], start=1):
        if not row or not row[0].strip():
            continue
        label = row[0].strip()
        if label in _METADATA_KEYS:
            metadata_rows[label] = [cell.strip() for cell in row[1:]]
            continue
        if _looks_like_date(label):
            data_start = index
            break

    if "Series ID" not in metadata_rows or data_start is None:
        raise ValueError("RBA CSV payload did not contain the expected header rows")

    series_ids = metadata_rows["Series ID"]
    titles = metadata_rows.get("Title", [])
    descriptions = metadata_rows.get("Description", [])
    frequencies = metadata_rows.get("Frequency", [])
    kinds = metadata_rows.get("Type", [])
    units = metadata_rows.get("Units", [])
    sources = metadata_rows.get("Source", [])
    publication_dates = metadata_rows.get("Publication date", [])

    series = []
    for idx, series_id in enumerate(series_ids):
        series.append(
            SeriesDescriptor(
                series_id=series_id,
                label=_at(titles, idx) or series_id,
                unit=_at(units, idx),
                frequency=_at(frequencies, idx),
                dimensions={
                    "description": {"code": "", "label": _at(descriptions, idx) or ""},
                    "type": {"code": "", "label": _at(kinds, idx) or ""},
                    "source": {"code": "", "label": _at(sources, idx) or ""},
                },
                source_key=series_id,
            ).to_dict()
        )

    observations = []
    for row in rows[data_start:]:
        if not row or not row[0].strip():
            continue
        date = _parse_rba_date(row[0].strip())
        for idx, raw_value in enumerate(row[1:]):
            value, non_numeric_value = _parse_rba_observation_value(raw_value)
            if value is None and non_numeric_value is None:
                continue
            observations.append(
                Observation(
                    date=date,
                    series_id=series_ids[idx],
                    value=value,
                    raw_value=non_numeric_value,
                ).to_dict()
            )

    return {
        "metadata": {
            "source": "rba",
            "dataset_id": table_id,
            "title": table_title,
            "publication_date": publication_dates[0] if publication_dates else None,
        },
        "series": series,
        "observations": observations,
    }


def _looks_like_date(value: str) -> bool:
    try:
        _parse_rba_date(value)
    except ValueError:
        return False
    return True


def _parse_rba_date(value: str) -> str:
    for fmt in ("%d/%m/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported RBA date format: {value}")


def _parse_rba_observation_value(value: str) -> tuple[float | None, str | None]:
    text = (value or "").strip()
    if not text:
        return None, None

    try:
        return parse_float(text), None
    except ValueError:
        return None, text


def _at(values: list[str], index: int) -> str | None:
    if index >= len(values):
        return None
    value = values[index].strip()
    return value or None

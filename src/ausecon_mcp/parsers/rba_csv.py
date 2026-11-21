from __future__ import annotations

import calendar
import csv
from datetime import date, datetime, timedelta
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
    "Mnemonic",
}
# Most tables label the series-ID row "Series ID"; a few older layouts (A5, D10) use "Mnemonic".
_SERIES_ID_KEYS = ("Series ID", "Mnemonic")
# Excel's day zero: D9 writes its dates as serial day numbers counted from here.
_EXCEL_EPOCH = date(1899, 12, 30)


def parse_rba_csv(csv_text: str, table_id: str) -> dict:
    rows = list(csv.reader(StringIO(csv_text.lstrip("\ufeff"))))
    if not rows:
        raise ValueError("RBA CSV payload was empty")

    table_title = rows[0][0].strip()
    metadata_rows = {}
    label_fragments: list[list[str]] = []
    data_start = None
    for index, row in enumerate(rows[1:], start=1):
        if not row or not row[0].strip():
            if any(cell.strip() for cell in row[1:]):
                label_fragments.append([cell.strip() for cell in row[1:]])
            continue
        label = row[0].strip()
        if label in _METADATA_KEYS:
            metadata_rows[label] = [cell.strip() for cell in row[1:]]
            continue
        if _looks_like_date(label):
            data_start = index
            break

    series_id_key = next((key for key in _SERIES_ID_KEYS if key in metadata_rows), None)
    if series_id_key is None or data_start is None:
        raise ValueError("RBA CSV payload did not contain the expected header rows")

    series_ids = list(metadata_rows[series_id_key])
    while series_ids and not series_ids[-1]:
        series_ids.pop()  # trailing empty columns (C8 pads every row with commas)
    titles = metadata_rows.get("Title") or _join_label_fragments(label_fragments)
    descriptions = metadata_rows.get("Description", [])
    frequencies = metadata_rows.get("Frequency", [])
    kinds = metadata_rows.get("Type", [])
    units = metadata_rows.get("Units") or _unit_under_title(rows, len(series_ids))
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
        for idx, raw_value in enumerate(row[1 : len(series_ids) + 1]):
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
    try:
        parsed = datetime.strptime(value, "%d-%b-%y").date()  # C9: "30-Jun-21"
    except ValueError:
        pass
    else:
        # strptime reads 00-68 as 2000-2068; an observation is never years in the future.
        if parsed.year > date.today().year + 1:
            parsed = parsed.replace(year=parsed.year - 100)
        return parsed.isoformat()
    try:
        month = datetime.strptime(value, "%b %Y").date()
    except ValueError:
        pass
    else:
        # A month label ("Jun 1990") marks the month-end, like the rest of the RBA tables.
        last_day = calendar.monthrange(month.year, month.month)[1]
        return month.replace(day=last_day).isoformat()
    if len(value) == 5 and value.isdigit():
        return (_EXCEL_EPOCH + timedelta(days=int(value))).isoformat()
    raise ValueError(f"Unsupported RBA date format: {value}")


def _join_label_fragments(fragments: list[list[str]]) -> list[str]:
    """Series labels from the untitled layout (A5), split across rows with a blank first cell."""
    width = max((len(row) for row in fragments), default=0)
    return [
        " ".join(row[idx] for row in fragments if idx < len(row) and row[idx])
        for idx in range(width)
    ]


def _unit_under_title(rows: list[list[str]], series_count: int) -> list[str]:
    """The untitled layout (A5) puts one unit for every series on the row under the title."""
    if len(rows) < 2 or not rows[1] or any(cell.strip() for cell in rows[1][1:]):
        return []
    unit = rows[1][0].strip()
    if not unit or unit in _METADATA_KEYS or _looks_like_date(unit):
        return []
    return [unit] * series_count


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

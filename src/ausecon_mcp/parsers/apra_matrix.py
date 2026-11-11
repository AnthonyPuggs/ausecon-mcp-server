"""The APRA ``matrix`` worksheet layout: one row per series, one column per date.

APRA lays these sheets out for people, so what a row means depends on what sits above it:

* a **block heading** is written in the first date column of a row with no label
  (``Assets ($m)``, ``Number of entities``, ``Banks``);
* a **section heading** is a labelled row with nothing under the dates
  (``Banks``, ``Credit outstanding``), sometimes carrying a unit or a repeat of the dates;
* a repeated **date header** starts a new panel of the same sheet;
* indentation of the label cell shows which rows belong to which heading or parent row.

A series id is ``PUBLICATION:table[:block][:section]:metric``, with block and section in
the order they appear on the sheet, so two rows with the same label under different
headings are different series.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ausecon_mcp.models import Observation, SeriesDescriptor
from ausecon_mcp.parsers.apra_xlsx import (
    Grid,
    _apply_number_format,
    _clean_label,
    _parse_date,
    _parse_observation_value,
    _series_decimals,
    _series_unit,
    _slug,
)

# Footnote markers APRA types as characters rather than superscript formatting:
# modifier and phonetic-extension letters such as U+1D47 (modifier small b).
_SUPERSCRIPT_CLASS = "\u1d2c-\u1dbf\u02b0-\u02ff"
_FOOTNOTE_ROW_RE = re.compile(rf"^(?:[a-z]|[{_SUPERSCRIPT_CLASS}]|\*)\s+\S")
_TRAILING_MARK_RE = re.compile(rf"[\s*{_SUPERSCRIPT_CLASS}]+$")
_TRAILING_PARENTHESES_RE = re.compile(r"\s*\(([^()]*)\)\s*$")
_IGNORED_COLUMN_TEXT = frozenset({"quarter end"})
_UNIT_TEXTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\$\s*m(?:illions?)?", re.IGNORECASE), "$ million"),
    (re.compile(r"\$\s*billions?", re.IGNORECASE), "$ billion"),
    (re.compile(r"\$\s*'000", re.IGNORECASE), "$ thousand"),
    (re.compile(r"'000", re.IGNORECASE), "thousand"),
    (re.compile(r"per cent|%", re.IGNORECASE), "Per cent"),
)


@dataclass
class _Heading:
    kind: str  # "block" or "section"
    slug: str
    label: str
    row: int
    level: float = 0.0
    # Level of the first data row under a section; rows shallower than it end the section.
    child_level: float | None = None


@dataclass
class _DataRow:
    index: int
    label: str
    metric: str
    level: float
    values: list[tuple[float | None, str | None]]
    formats: list[str | None]
    headings: tuple[_Heading, ...]

    def series_id(self, publication_id: str, table_id: str) -> str:
        parts = [publication_id, table_id, *(heading.slug for heading in self.headings)]
        return ":".join([*parts, self.metric])


def parse_matrix(
    grid: Grid,
    *,
    publication_id: str,
    table_id: str,
    table_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Return ``(series, observations, warnings)`` for one matrix worksheet."""
    date_row = int(table_map["date_row"])
    date_start_column = int(table_map["date_start_column"])

    date_columns: list[tuple[int, str]] = []
    for column in range(date_start_column, (grid.max_column or date_start_column) + 1):
        parsed_date = _parse_date(grid.value(date_row, column))
        if parsed_date is not None:
            date_columns.append((column, parsed_date))
    if not date_columns:
        raise ValueError(f"APRA matrix table {table_id!r} did not contain date columns.")

    rows = _collect_rows(grid, table_map, [column for column, _ in date_columns])
    warnings: list[str] = []

    series: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for row in rows:
        series_id = row.series_id(publication_id, table_id)
        dimensions = _dimensions(table_id, table_map, row)
        number_format = next(
            (
                fmt
                for (value, _raw), fmt in zip(row.values, row.formats, strict=True)
                if value is not None
            ),
            None,
        )
        series.append(
            SeriesDescriptor(
                series_id=series_id,
                label=" / ".join([*(heading.label for heading in row.headings), row.label]),
                unit=_series_unit(table_map.get("unit"), row.label, number_format),
                frequency=table_map.get("frequency"),
                dimensions=dimensions,
                source_key=row.label,
                decimals=_series_decimals(number_format),
            ).to_dict()
        )
        for (_column, parsed_date), (value, raw_value), cell_format in zip(
            date_columns, row.values, row.formats, strict=True
        ):
            if value is None and raw_value is None:
                continue
            observations.append(
                Observation(
                    date=parsed_date,
                    series_id=series_id,
                    value=_apply_number_format(value, cell_format),
                    raw_value=raw_value,
                    dimensions=dimensions,
                ).to_dict()
            )

    return series, observations, warnings


def _collect_rows(grid: Grid, table_map: dict[str, Any], date_columns: list[int]) -> list[_DataRow]:
    """Walk the sheet top to bottom and return its data rows with their headings."""
    date_row = int(table_map["date_row"])
    data_start_row = int(table_map["data_start_row"])
    label_column = int(table_map["label_column"])
    date_header_threshold = max(2, len(date_columns) // 2)

    headings: list[_Heading] = []
    rows: list[_DataRow] = []
    last_data_row = 0

    def drop_from(kind: str) -> None:
        for position, heading in enumerate(headings):
            if heading.kind == kind:
                del headings[position:]
                return

    def open_heading(heading: _Heading) -> None:
        # A new heading replaces the previous one of its kind and anything written after it.
        drop_from(heading.kind)
        headings.append(heading)

    # The row above the first date header may carry the first block heading.
    for row_index in range(max(1, date_row - 1), grid.max_row + 1):
        marked_label = _clean_label(grid.value(row_index, label_column))
        raw_label = grid.unmarked_text(row_index, label_column)
        label = _strip_marks(_clean_label(raw_label))
        level = grid.indent(row_index) + (len(raw_label) - len(raw_label.lstrip(" "))) / 4

        cells = [grid.value(row_index, column) for column in date_columns]
        values = [_parse_observation_value(cell) for cell in cells]
        has_numbers = any(value is not None for value, _raw in values)
        is_date = [
            value is None and raw is not None and _parse_date(cell) is not None
            for cell, (value, raw) in zip(cells, values, strict=True)
        ]
        texts = [
            (column, raw)
            for column, (value, raw), dated in zip(date_columns, values, is_date, strict=True)
            if value is None and raw is not None and not dated
        ]
        filled = sum(1 for value, raw in values if value is not None or raw is not None)
        labelled = bool(label) and row_index >= data_start_row
        is_footnote = not has_numbers and bool(_FOOTNOTE_ROW_RE.match(marked_label))

        if row_index == date_row or (not has_numbers and sum(is_date) >= date_header_threshold):
            # A date header starts a new panel: only headings written since the last data
            # row (the new panel's own) carry over.
            headings[:] = [heading for heading in headings if heading.row > last_data_row]
            if labelled and not is_footnote:
                open_heading(_Heading("section", _slug(label), label, row_index, level))
            continue

        if not label:
            if has_numbers or filled != 1 or not texts:
                continue
            column, _raw = texts[0]
            text = _strip_marks(_clean_label(grid.unmarked_text(row_index, column)))
            if text.lower() in _IGNORED_COLUMN_TEXT:
                continue
            name, _unit = _split_unit(text)
            if name:
                open_heading(_Heading("block", _slug(name), text, row_index))
            continue

        if not labelled or is_footnote:
            continue

        if not has_numbers:
            states_unit = filled == 1 and bool(texts) and not _split_unit(texts[0][1])[0]
            if not texts or states_unit:
                if not texts and label.lower().startswith("of which"):
                    continue
                open_heading(_Heading("section", _slug(label), label, row_index, level))
                continue

        section = next((heading for heading in headings if heading.kind == "section"), None)
        if section is not None:
            is_section_total = label.lower().startswith("total") and level >= section.level
            if section.child_level is None:
                if level < section.level:
                    drop_from("section")
                else:
                    section.child_level = level
            elif level < section.child_level and not is_section_total:
                drop_from("section")

        rows.append(
            _DataRow(
                index=row_index,
                label=label,
                metric=_slug(label),
                level=level,
                values=values,
                formats=[grid.number_format(row_index, column) for column in date_columns],
                headings=tuple(headings),
            )
        )
        last_data_row = row_index

    return rows


def _strip_marks(text: str) -> str:
    """Drop trailing footnote markers (``*`` or superscript letters) from a label."""
    return _TRAILING_MARK_RE.sub("", text)


def _unit_from_text(text: str) -> str | None:
    """Return the unit a bare text such as ``($ millions)`` or ``per cent`` names."""
    candidate = text.strip()
    if candidate.startswith("(") and candidate.endswith(")"):
        candidate = candidate[1:-1].strip()
    for pattern, unit in _UNIT_TEXTS:
        if pattern.fullmatch(candidate):
            return unit
    return None


def _split_unit(text: str) -> tuple[str, str | None]:
    """Split a heading into its name and the unit it states, if any.

    ``Assets ($m)`` -> ``("Assets", "$ million")``; ``('000)`` -> ``("", "thousand")``;
    ``ADIs (excludes 'other ADIs')`` -> unchanged with no unit.
    """
    bare = _unit_from_text(text)
    if bare is not None:
        return "", bare
    match = _TRAILING_PARENTHESES_RE.search(text)
    if match is not None:
        unit = _unit_from_text(match.group(1))
        if unit is not None:
            return text[: match.start()].strip(), unit
    return text.strip(), None


def _dimensions(
    table_id: str,
    table_map: dict[str, Any],
    row: _DataRow,
) -> dict[str, dict[str, str]]:
    dimensions = {
        "table": {
            "code": table_id,
            "label": str(table_map.get("title") or table_id),
        }
    }
    for heading in row.headings:
        dimensions[heading.kind] = {"code": heading.slug, "label": heading.label}
    return dimensions

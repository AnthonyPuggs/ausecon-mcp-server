from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment

from ausecon_mcp.parsers.apra_xlsx import Grid, parse_apra_xlsx

D1, D2 = datetime(2026, 3, 31), datetime(2026, 6, 30)
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _share_rich_strings(content: bytes) -> bytes:
    """Move rich-text cells from inline strings to a shared-string table.

    openpyxl writes rich text inline, but Excel (and so APRA's workbooks) stores it as
    shared strings, the only form openpyxl's read-only reader returns as rich text.
    """
    ET.register_namespace("", _NS)
    source = zipfile.ZipFile(BytesIO(content))
    sheet = ET.fromstring(source.read("xl/worksheets/sheet1.xml"))
    strings = ET.Element(f"{{{_NS}}}sst")
    for cell in sheet.iter(f"{{{_NS}}}c"):
        inline = cell.find(f"{{{_NS}}}is")
        if inline is None or inline.find(f"{{{_NS}}}r") is None:
            continue
        ET.SubElement(strings, f"{{{_NS}}}si").extend(list(inline))
        cell.remove(inline)
        cell.set("t", "s")
        ET.SubElement(cell, f"{{{_NS}}}v").text = str(len(strings) - 1)
    content_types = source.read("[Content_Types].xml").decode("utf-8")
    override = (
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.spreadsheetml.sharedStrings+xml" />'
    )
    replaced = {
        "xl/worksheets/sheet1.xml": ET.tostring(sheet),
        "[Content_Types].xml": content_types.replace("</Types>", f"{override}</Types>").encode(),
    }
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            target.writestr(info, replaced.get(info.filename, source.read(info.filename)))
        target.writestr("xl/sharedStrings.xml", ET.tostring(strings))
    return buffer.getvalue()


def _matrix_xlsx(
    rows: list[list[object]],
    *,
    levels: dict[int, int] | None = None,
    formats: dict[tuple[int, int], str] | None = None,
) -> bytes:
    """Build a one-sheet workbook. A cell given as ("text", "a") gets a superscript "a".

    ``levels`` maps a 1-based sheet row to the Excel indent of its first cell;
    ``formats`` maps (row, column) to a number format.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet"
    for row in rows:
        sheet.append(
            [
                CellRichText(cell[0], TextBlock(InlineFont(vertAlign="superscript"), cell[1]))
                if isinstance(cell, tuple)
                else cell
                for cell in row
            ]
        )
    for row_index, indent in (levels or {}).items():
        sheet.cell(row_index, 1).alignment = Alignment(indent=indent)
    for (row_index, column), number_format in (formats or {}).items():
        sheet.cell(row_index, column).number_format = number_format
    buffer = BytesIO()
    workbook.save(buffer)
    if any(isinstance(cell, tuple) for row in rows for cell in row):
        return _share_rich_strings(buffer.getvalue())
    return buffer.getvalue()


def _parse(rows, *, levels=None, formats=None, **map_overrides) -> dict[str, Any]:
    table_map = {
        "sheet": "Sheet",
        "layout": "matrix",
        "title": "Test table",
        "unit": None,
        "frequency": "Quarterly",
        "date_row": 2,
        "date_start_column": 2,
        "data_start_row": 3,
        "label_column": 1,
        **map_overrides,
    }
    return parse_apra_xlsx(
        _matrix_xlsx(rows, levels=levels, formats=formats),
        publication_id="P",
        title="T",
        frequency="Quarterly",
        table_maps={"t": table_map},
    )


def _units(payload: dict[str, Any]) -> dict[str, str | None]:
    """Series id (without the "P:t:" prefix) -> unit, asserting the unique-id guarantee."""
    ids = [series["series_id"] for series in payload["series"]]
    assert len(ids) == len(set(ids))
    keys = [(obs["series_id"], obs["date"]) for obs in payload["observations"]]
    assert len(keys) == len(set(keys))
    return {item["series_id"].removeprefix("P:t:"): item["unit"] for item in payload["series"]}


def test_grid_reports_indent_and_label_text_without_superscript_markers() -> None:
    content = _matrix_xlsx(
        [
            ["Title", None],
            [None, D1],
            [("Net profit (loss) after tax", "a"), 1.5],
            ["    Owner-occupied", 2.0],
            [None, 3.0],
        ],
        levels={3: 2},
    )
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True, rich_text=True)
    grid = Grid(workbook["Sheet"], style_column=1)

    assert grid.value(3, 1) == "Net profit (loss) after taxa"
    assert type(grid.value(3, 1)) is str
    assert grid.unmarked_text(3, 1) == "Net profit (loss) after tax"
    assert grid.unmarked_text(4, 1) == "    Owner-occupied"
    assert grid.unmarked_text(5, 1) == ""
    assert grid.unmarked_text(3, 2) == "1.5"
    assert (grid.indent(3), grid.indent(4), grid.indent(5)) == (2.0, 0.0, 0.0)
    assert Grid(workbook["Sheet"]).indent(3) == 0.0

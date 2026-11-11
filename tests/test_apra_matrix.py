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


def test_stacked_blocks_qualify_repeated_rows_and_sections_end_by_indent() -> None:
    payload = _parse(
        [
            [None, "Assets ($m)", None],
            [None, D1, D2],
            ["ADIs", None, None],
            ["Banks", None, None],
            ["Major banks", 100.0, 110.0],
            ["All banks", 150.0, 160.0],
            ["Other ADIs", 5.0, 6.0],
            [None, "Number of entities", None],
            [None, "Mar 2026", "Jun 2026"],
            ["ADIs", None, None],
            ["Banks", None, None],
            ["Major banks", 4, 4],
            ["Other ADIs", 7, 7],
        ],
        levels={4: 1, 5: 2, 6: 2, 7: 1, 11: 1, 12: 2, 13: 1},
    )

    assert list(_units(payload)) == [
        "assets:banks:major_banks",
        "assets:banks:all_banks",
        "assets:other_adis",
        "number_of_entities:banks:major_banks",
        "number_of_entities:other_adis",
    ]
    first = payload["series"][0]
    assert first["label"] == "Assets ($m) / Banks / Major banks"
    assert first["source_key"] == "Major banks"
    assert first["dimensions"]["block"] == {"code": "assets", "label": "Assets ($m)"}
    assert first["dimensions"]["section"] == {"code": "banks", "label": "Banks"}
    assert "section" not in payload["series"][2]["dimensions"]
    assert "warnings" not in payload["metadata"]


def test_block_under_a_section_keeps_the_section_when_the_block_changes() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Net interest income ($m)", 1.0, 2.0],
            ["Key figures", None, None],
            [None, "Quarter end", None],
            [None, D1, D2],
            [None, ("ADIs (excludes 'other ADIs')", "a"), None],
            ["Total capital ratio", 0.2, 0.21],
            ["Key figures (banks and CUBS)", None, None],
            [None, D1, D2],
            [None, "Banks", None],
            ["Total capital ratio", 0.2, 0.2],
            [None, "Credit unions", None],
            ["Total capital ratio", 0.17, 0.17],
        ]
    )

    assert list(_units(payload)) == [
        "net_interest_income_m",
        "key_figures:adis_excludes_other_adis:total_capital_ratio",
        "key_figures_banks_and_cubs:banks:total_capital_ratio",
        "key_figures_banks_and_cubs:credit_unions:total_capital_ratio",
    ]


def test_total_row_at_heading_level_stays_and_a_later_shallow_row_ends_the_section() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Exposure limits", None, None],
            ["Office", 1, 2],
            ["Retail", 3, 4],
            ["Total limits", 4, 6],
            ["of which: In Australia", 3, 5],
            ["Number of entities", 10, 10],
        ],
        levels={4: 1, 5: 1, 7: 1},
    )

    assert list(_units(payload)) == [
        "exposure_limits:office",
        "exposure_limits:retail",
        "exposure_limits:total_limits",
        "exposure_limits:of_which_in_australia",
        "number_of_entities",
    ]


def test_heading_whose_first_row_is_at_its_own_level_keeps_those_rows() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Loan performance", None, None],
            ["Past due", 1, 1],
            ["Non-performing", 2, 2],
            ["Term loans", 1.5, 1.5],
            ["By LVR", None, None],
            ["LVR < 60%", 1, 1],
            ["Number of entities", 5, 5],
        ],
        levels={3: 1, 4: 1, 5: 1, 6: 2, 7: 1, 8: 2, 9: 1},
    )

    assert list(_units(payload)) == [
        "loan_performance:past_due",
        "loan_performance:non_performing",
        "loan_performance:term_loans",
        "by_lvr:lvr_60",
        "number_of_entities",
    ]


def test_headings_with_units_or_dates_are_not_series_and_text_marks_still_are() -> None:
    payload = _parse(
        [
            [None, "MySuper products", None],
            [None, D1, D2],
            ["New loans funded - total", "($ millions)", None],
            ["New loans funded", 100, 110],
            ["Interest rates", "per cent", None],
            [None, "Mar 2026", "Jun 2026"],
            ["Variable rate", 6.1, 6.2],
            ["Suppressed row", "*", "*"],
            [None, "Number of member accounts ('000)", None],
            ["Members with 100 per cent MySuper interest", D1, D2],
            ["MySuper products - generic", 13322.4, 13400.0],
            [None, "*", "*"],
            ["of which: empty row", None, None],
            ["MySuper products - large employer", 100.9, 101.0],
        ],
        levels={3: 1, 4: 1, 5: 1, 7: 2, 8: 2, 11: 1, 14: 1},
    )

    assert list(_units(payload)) == [
        "mysuper_products:new_loans_funded_total:new_loans_funded",
        "interest_rates:variable_rate",
        "interest_rates:suppressed_row",
        "number_of_member_accounts:members_with_100_per_cent_mysuper_interest"
        ":mysuper_products_generic",
        "number_of_member_accounts:members_with_100_per_cent_mysuper_interest"
        ":mysuper_products_large_employer",
    ]
    suppressed = [o for o in payload["observations"] if o["series_id"].endswith("suppressed_row")]
    assert [(o["value"], o["raw_value"]) for o in suppressed] == [(None, "*"), (None, "*")]


def test_footnote_markers_and_footnote_rows_do_not_reach_ids() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Section", None, None],
            [("Net profit (loss) after tax", "a"), 1, 1],
            ["Liquidity coverage ratio (LCR) ᵇ", 1.3, 1.3],
            ["Corporate funds*", 3, 3],
            ["a Profit or loss after goodwill amortisation.", None, None],
            ["ᵇ For those ADIs subject to LCR requirements.", None, None],
            ["* From the June 2026 quarter.", None, None],
            ["Small funds", 9, 9],
        ],
        levels={4: 1, 5: 1, 6: 1, 10: 1},
    )

    assert list(_units(payload)) == [
        "section:net_profit_loss_after_tax",
        "section:liquidity_coverage_ratio_lcr",
        "section:corporate_funds",
        "section:small_funds",
    ]
    assert payload["series"][0]["source_key"] == "Net profit (loss) after tax"


def test_repeated_labels_take_their_parent_rows() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Interest income", 10, 11],
            ["of which:", None, None],
            ["Loans and advances", 8, 9],
            ["Housing loans", 5, 6],
            ["Other", 3, 3],
            ["Other operating income", 4, 4],
            ["Other", 1, 1],
        ],
        levels={5: 1, 6: 2, 7: 2, 9: 1},
    )

    assert list(_units(payload)) == [
        "interest_income",
        "loans_and_advances",
        "housing_loans",
        "interest_income:loans_and_advances:other",
        "other_operating_income",
        "other_operating_income:other",
    ]
    other = payload["series"][3]
    assert other["label"] == "Interest income / Loans and advances / Other"
    assert other["dimensions"]["parent"] == {
        "code": "interest_income:loans_and_advances",
        "label": "Interest income / Loans and advances",
    }
    assert "parent" not in payload["series"][2]["dimensions"]


def test_leading_spaces_count_as_a_level() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Owner-occupied and investor loans", None, None],
            ["Debt-to-income ≥ 4x < 6x", 9, 9],
            ["    Owner-occupied", 5, 5],
            ["Debt-to-income ≥ 6x", 2, 2],
            ["    Owner-occupied", 1, 1],
        ],
        levels={3: 2, 4: 3, 5: 3, 6: 3, 7: 3},
    )

    assert list(_units(payload)) == [
        "owner_occupied_and_investor_loans:debt_to_income_4x_6x",
        "owner_occupied_and_investor_loans:debt_to_income_4x_6x:owner_occupied",
        "owner_occupied_and_investor_loans:debt_to_income_6x",
        "owner_occupied_and_investor_loans:debt_to_income_6x:owner_occupied",
    ]


def test_rows_parents_cannot_separate_take_the_closest_unique_row_above() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Impaired exposures", 5, 5],
            ["of which: In Australia", 4, 4],
            ["Specific provisions", 2, 2],
            ["of which: In Australia", 1, 1],
            ["Non-performing exposures", 7, 7],
            ["of which: In Australia", 6, 6],
            ["Specific provisions", 3, 3],
            ["of which: In Australia", 2, 2],
        ],
        levels={4: 1, 6: 1, 8: 1, 10: 1},
    )

    assert list(_units(payload)) == [
        "impaired_exposures",
        "impaired_exposures:of_which_in_australia",
        "impaired_exposures:specific_provisions",
        "impaired_exposures:specific_provisions:of_which_in_australia",
        "non_performing_exposures",
        "non_performing_exposures:of_which_in_australia",
        "non_performing_exposures:specific_provisions",
        "non_performing_exposures:specific_provisions:of_which_in_australia",
    ]
    assert "warnings" not in payload["metadata"]


def test_rows_nothing_can_separate_are_numbered_with_a_warning() -> None:
    payload = _parse(
        [
            ["Title", None, None],
            [None, D1, D2],
            ["Other", 1, 1],
            ["Other", 2, 2],
            ["—", 3, 3],
            ["…", 4, 4],
        ]
    )

    assert list(_units(payload)) == ["other", "other_2", "unknown", "unknown_2"]
    numbered = "later rows are numbered _2, _3."
    assert payload["metadata"]["warnings"] == [
        f"APRA table 't': 2 rows resolve to series id 'P:t:other'; {numbered}",
        f"APRA table 't': 2 rows resolve to series id 'P:t:unknown'; {numbered}",
    ]

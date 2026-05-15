from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO

import pytest
from openpyxl import Workbook

import ausecon_mcp.parsers.apra_xlsx as apra_parser
from ausecon_mcp.parsers.apra_xlsx import parse_apra_xlsx


def _xlsx_bytes(rows_by_sheet: dict[str, list[list[object]]]) -> bytes:
    workbook = Workbook()
    first = True
    for title, rows in rows_by_sheet.items():
        sheet = workbook.active if first else workbook.create_sheet()
        first = False
        sheet.title = title
        for row in rows:
            sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _row_record_table_map() -> dict:
    return {
        "table_1": {
            "sheet": "Table 1",
            "layout": "row_records",
            "title": "Table 1",
            "unit": "$ million",
            "frequency": "Monthly",
            "header_row": 2,
            "data_start_row": 3,
            "date_column": 1,
            "dimension_columns": {"abn": 2, "institution": 3},
            "series_start_column": 4,
            "identity_columns": ["abn"],
        }
    }


def test_parse_apra_xlsx_rejects_oversized_compressed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(apra_parser, "MAX_APRA_XLSX_BYTES", 8, raising=False)

    with pytest.raises(ValueError, match="exceeds maximum APRA XLSX size"):
        parse_apra_xlsx(
            b"not-an-xlsx",
            publication_id="TEST_PUBLICATION",
            title="Test APRA publication",
            frequency="Monthly",
            table_maps=_row_record_table_map(),
        )


def test_parse_apra_xlsx_rejects_excessive_uncompressed_zip_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", "x" * 32)
    monkeypatch.setattr(apra_parser, "MAX_APRA_XLSX_UNCOMPRESSED_BYTES", 16, raising=False)

    with pytest.raises(ValueError, match="uncompressed APRA XLSX payload"):
        parse_apra_xlsx(
            buffer.getvalue(),
            publication_id="TEST_PUBLICATION",
            title="Test APRA publication",
            frequency="Monthly",
            table_maps=_row_record_table_map(),
        )


def test_parse_apra_xlsx_rejects_excessive_table_dimensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workbook = _xlsx_bytes(
        {
            "Table 1": [
                ["($million)"],
                ["Period", "ABN", "Institution Name", "Total residents assets"],
                [datetime(2024, 1, 31), 11111111111, "Example Bank", 100.5],
                [datetime(2024, 2, 29), 11111111111, "Example Bank", 110.0],
            ]
        }
    )
    monkeypatch.setattr(apra_parser, "MAX_APRA_TABLE_ROWS", 3, raising=False)

    with pytest.raises(ValueError, match="exceeds maximum APRA table rows"):
        parse_apra_xlsx(
            workbook,
            publication_id="TEST_PUBLICATION",
            title="Test APRA publication",
            frequency="Monthly",
            table_maps=_row_record_table_map(),
        )


def test_parse_apra_xlsx_normalises_row_record_tables() -> None:
    workbook = _xlsx_bytes(
        {
            "Table 1": [
                ["($million)"],
                [
                    "Period",
                    "ABN",
                    "Institution Name",
                    "Total residents assets",
                    "Deposits by households",
                ],
                [datetime(2024, 1, 31), 11111111111, "Example Bank", 100.5, "*"],
                [datetime(2024, 2, 29), 11111111111, "Example Bank", 110.0, 55.5],
                [None, None, None, None, None],
            ]
        }
    )

    payload = parse_apra_xlsx(
        workbook,
        publication_id="TEST_PUBLICATION",
        title="Test APRA publication",
        frequency="Monthly",
        table_maps={
            "table_1": {
                "sheet": "Table 1",
                "layout": "row_records",
                "title": "Table 1",
                "unit": "$ million",
                "frequency": "Monthly",
                "header_row": 2,
                "data_start_row": 3,
                "date_column": 1,
                "dimension_columns": {
                    "abn": 2,
                    "institution": 3,
                },
                "series_start_column": 4,
                "identity_columns": ["abn"],
            }
        },
    )

    assert payload["metadata"]["source"] == "apra"
    assert payload["metadata"]["dataset_id"] == "TEST_PUBLICATION"
    assert payload["metadata"]["title"] == "Test APRA publication"
    assert payload["series"][0]["series_id"] == (
        "TEST_PUBLICATION:table_1:11111111111:total_residents_assets"
    )
    assert payload["series"][0]["label"] == "Example Bank - Total residents assets"
    assert payload["series"][0]["unit"] == "$ million"
    assert payload["observations"][0] == {
        "date": "2024-01-31",
        "series_id": "TEST_PUBLICATION:table_1:11111111111:total_residents_assets",
        "value": 100.5,
        "dimensions": {
            "table": {"code": "table_1", "label": "Table 1"},
            "abn": {"code": "11111111111", "label": "11111111111"},
            "institution": {"code": "Example Bank", "label": "Example Bank"},
        },
        "status": None,
        "comment": None,
    }
    assert payload["observations"][1]["raw_value"] == "*"
    assert payload["observations"][1]["value"] is None


def test_parse_apra_xlsx_normalises_matrix_tables_with_section_labels() -> None:
    workbook = _xlsx_bytes(
        {
            "Tab 1b": [
                ["Table 1b  Residential property exposures"],
                ["($ million, Level 2)"],
                [None, None, "Quarter end", None],
                [None, None, datetime(2024, 3, 31), datetime(2024, 6, 30)],
                [None, None, None, None],
                ["Credit outstanding", None, None, None],
                ["Total credit outstanding", None, 1000.0, 1050.5],
                ["Owner-occupied", None, 700.0, 725.0],
                [None, None, None, None],
                ["Memo row with no observations", None, None, None],
            ]
        }
    )

    payload = parse_apra_xlsx(
        workbook,
        publication_id="TEST_PUBLICATION",
        title="Test APRA publication",
        frequency="Quarterly",
        table_maps={
            "tab_1b": {
                "sheet": "Tab 1b",
                "layout": "matrix",
                "title": "Residential property exposures",
                "unit": "$ million",
                "frequency": "Quarterly",
                "date_row": 4,
                "date_start_column": 3,
                "data_start_row": 6,
                "label_column": 1,
            }
        },
    )

    assert payload["series"][0]["series_id"] == (
        "TEST_PUBLICATION:tab_1b:credit_outstanding:total_credit_outstanding"
    )
    assert payload["series"][0]["label"] == "Credit outstanding: Total credit outstanding"
    assert payload["series"][0]["dimensions"]["section"]["label"] == "Credit outstanding"
    assert payload["observations"][0] == {
        "date": "2024-03-31",
        "series_id": "TEST_PUBLICATION:tab_1b:credit_outstanding:total_credit_outstanding",
        "value": 1000.0,
        "dimensions": {
            "table": {"code": "tab_1b", "label": "Residential property exposures"},
            "section": {"code": "credit_outstanding", "label": "Credit outstanding"},
        },
        "status": None,
        "comment": None,
    }
    target_observations = [
        item
        for item in payload["observations"]
        if item["series_id"]
        == "TEST_PUBLICATION:tab_1b:credit_outstanding:total_credit_outstanding"
    ]
    assert [item["date"] for item in target_observations] == [
        "2024-03-31",
        "2024-06-30",
    ]


def test_parse_apra_xlsx_can_limit_to_one_declared_table() -> None:
    workbook = _xlsx_bytes(
        {
            "A": [
                [None],
                ["Period", "Entity", "Metric"],
                [datetime(2024, 1, 31), "Entity A", 1.0],
            ],
            "B": [
                [None],
                ["Period", "Entity", "Metric"],
                [datetime(2024, 1, 31), "Entity B", 2.0],
            ],
        }
    )
    table_maps = {
        "a": {
            "sheet": "A",
            "layout": "row_records",
            "title": "A",
            "unit": "count",
            "frequency": "Monthly",
            "header_row": 2,
            "data_start_row": 3,
            "date_column": 1,
            "dimension_columns": {"entity": 2},
            "series_start_column": 3,
            "identity_columns": ["entity"],
        },
        "b": {
            "sheet": "B",
            "layout": "row_records",
            "title": "B",
            "unit": "count",
            "frequency": "Monthly",
            "header_row": 2,
            "data_start_row": 3,
            "date_column": 1,
            "dimension_columns": {"entity": 2},
            "series_start_column": 3,
            "identity_columns": ["entity"],
        },
    }

    payload = parse_apra_xlsx(
        workbook,
        publication_id="TEST_PUBLICATION",
        title="Test APRA publication",
        frequency="Monthly",
        table_maps=table_maps,
        table_id="b",
    )

    assert {series["dimensions"]["table"]["code"] for series in payload["series"]} == {"b"}
    assert payload["observations"][0]["series_id"] == "TEST_PUBLICATION:b:entity_b:metric"


def test_parse_apra_xlsx_selected_table_requires_matching_sheet() -> None:
    workbook = _xlsx_bytes(
        {
            "A": [
                [None],
                ["Period", "Entity", "Metric"],
                [datetime(2024, 1, 31), "Entity A", 1.0],
            ],
        }
    )
    table_maps = {
        "missing": {
            "sheet": "Missing",
            "layout": "row_records",
            "title": "Missing",
            "unit": "count",
            "frequency": "Monthly",
            "header_row": 2,
            "data_start_row": 3,
            "date_column": 1,
            "dimension_columns": {"entity": 2},
            "series_start_column": 3,
            "identity_columns": ["entity"],
        }
    }

    with pytest.raises(ValueError, match="did not contain sheet 'Missing'"):
        parse_apra_xlsx(
            workbook,
            publication_id="TEST_PUBLICATION",
            title="Test APRA publication",
            frequency="Monthly",
            table_maps=table_maps,
            table_id="missing",
        )

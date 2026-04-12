from pathlib import Path

from ausecon_mcp.parsers.abs_csv import parse_abs_csv
from ausecon_mcp.parsers.abs_structure import parse_abs_structure
from ausecon_mcp.parsers.rba_csv import parse_rba_csv

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_abs_structure_extracts_dimensions_and_codelists() -> None:
    structure = parse_abs_structure((FIXTURES / "abs_cpi_structure.xml").read_text())

    assert structure["id"] == "CPI"
    assert structure["name"] == "Consumer Price Index"
    assert [dimension["id"] for dimension in structure["dimensions"]] == [
        "MEASURE",
        "REGION",
        "FREQ",
    ]
    assert structure["dimensions"][0]["values"][0] == {
        "code": "1",
        "label": "Index numbers",
    }
    assert structure["dimensions"][1]["values"][-1]["label"] == "Australia"


def test_parse_abs_csv_normalises_series_and_observations() -> None:
    parsed = parse_abs_csv((FIXTURES / "abs_cpi_sample.csv").read_text())

    assert parsed["metadata"]["source"] == "abs"
    assert parsed["metadata"]["dataset_id"] == "CPI"
    assert parsed["metadata"]["frequency"] == "Monthly"
    assert len(parsed["series"]) == 2
    assert parsed["series"][0]["unit"] == "Percent"
    assert parsed["observations"][0]["date"] == "2024-01"
    assert parsed["observations"][0]["value"] == 7.4
    assert parsed["observations"][0]["dimensions"]["REGION"]["label"] == "Australia"


def test_parse_rba_csv_extracts_metadata_and_long_observations() -> None:
    parsed = parse_rba_csv((FIXTURES / "rba_g1_sample.csv").read_text(), table_id="g1")

    assert parsed["metadata"]["source"] == "rba"
    assert parsed["metadata"]["dataset_id"] == "g1"
    assert parsed["metadata"]["title"] == "G1 CONSUMER PRICE INFLATION"
    assert len(parsed["series"]) == 3
    assert parsed["series"][1]["series_id"] == "GCPIAGYP"
    assert parsed["series"][1]["unit"] == "Per cent"
    assert parsed["observations"][0]["date"] == "1922-06-30"
    assert parsed["observations"][-1]["series_id"] == "GCPIAGSAQP"
    assert parsed["observations"][-1]["value"] == 3.1

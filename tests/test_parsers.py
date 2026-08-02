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
        "INDEX",
        "TSEST",
        "REGION",
        "FREQ",
    ]
    assert structure["dimensions"][0]["values"][0] == {
        "code": "1",
        "label": "Index numbers",
    }
    assert structure["dimensions"][1]["values"][-1]["label"] == "Weighted Median"
    assert structure["dimensions"][3]["values"][-1]["label"] == "Australia"


def test_parse_abs_csv_normalises_labelled_series_and_observations() -> None:
    # abs_cpi_sample.csv mirrors the live csvfilewithlabels layout: paired
    # code/label columns and STRUCTURE_ID/STRUCTURE_NAME instead of DATAFLOW.
    parsed = parse_abs_csv((FIXTURES / "abs_cpi_sample.csv").read_text())

    assert parsed["metadata"]["source"] == "abs"
    assert parsed["metadata"]["dataset_id"] == "CPI"
    assert parsed["metadata"]["frequency"] == "Quarterly"
    assert parsed["metadata"]["title"] == "Consumer Price Index (CPI)"
    assert len(parsed["series"]) == 1
    assert parsed["series"][0]["unit"] == "Index Numbers"
    assert parsed["series"][0]["series_id"] == "MEASURE=1|INDEX=10001|TSEST=10|REGION=50|FREQ=Q"
    assert parsed["series"][0]["label"] == (
        "Index numbers / All groups CPI / Original / Australia / Quarterly"
    )
    assert parsed["series"][0]["source_key"] == "ABS:CPI(2.0.0)"
    assert parsed["series"][0]["base_period"] == "Sep 2025 = 100.0"
    assert parsed["observations"][0]["date"] == "2025-Q2"
    assert parsed["observations"][0]["value"] == 140.2
    assert parsed["observations"][0]["dimensions"]["REGION"] == {
        "code": "50",
        "label": "Australia",
    }
    assert parsed["observations"][0]["dimensions"]["INDEX"]["code"] == "10001"


def test_parse_abs_csv_preserves_unit_multiplier_and_status_metadata() -> None:
    # abs_ana_agg_sample.csv stays in the code-only csvfile layout to prove the
    # parser still handles the legacy variant (no paired label columns).
    parsed = parse_abs_csv((FIXTURES / "abs_ana_agg_sample.csv").read_text())

    assert parsed["metadata"]["dataset_id"] == "ANA_AGG"
    assert parsed["metadata"]["frequency"] == "Q"
    assert len(parsed["series"]) == 1
    assert parsed["series"][0]["unit"] == "PCT"
    assert parsed["series"][0]["unit_multiplier"] == 0
    assert "UNIT_MULT" not in parsed["series"][0]["dimensions"]
    assert parsed["observations"][0]["value"] is None
    assert parsed["observations"][0]["status"] == "m"
    assert parsed["observations"][1]["value"] == 0.9


def test_parse_abs_csv_composes_multiplier_word_into_unit() -> None:
    # Mirrors the live ANA_AGG GDP series: UNIT_MEASURE "Australian Dollars" with
    # UNIT_MULT 6 should read as "Australian Dollars, millions" while the raw
    # OBS_VALUE and the numeric unit_multiplier field stay untouched.
    csv_text = "\n".join(
        [
            "DATAFLOW,MEASURE,DATA_ITEM,TSEST,REGION,FREQ,TIME_PERIOD,OBS_VALUE,"
            "UNIT_MEASURE,UNIT_MULT,OBS_STATUS,OBS_COMMENT",
            "ABS:ANA_AGG(1.0.0),M2,GNI,20,AUS,Q,2025-Q2,736601.0,Australian Dollars,6,,",
        ]
    )
    parsed = parse_abs_csv(csv_text)

    assert parsed["series"][0]["unit"] == "Australian Dollars, millions"
    assert parsed["series"][0]["unit_multiplier"] == 6
    assert parsed["observations"][0]["value"] == 736601.0


def test_parse_abs_csv_zero_multiplier_leaves_unit_unchanged() -> None:
    # abs_ana_agg_sample.csv fixture already carries UNIT_MULT=0 (PCT); confirm
    # no ", x10^0" or similar suffix gets appended.
    parsed = parse_abs_csv((FIXTURES / "abs_ana_agg_sample.csv").read_text())

    assert parsed["series"][0]["unit"] == "PCT"
    assert parsed["series"][0]["unit_multiplier"] == 0


def test_parse_abs_csv_missing_multiplier_leaves_unit_unchanged() -> None:
    # abs_cpi_sample.csv has no UNIT_MULT column at all (unit_multiplier is None).
    parsed = parse_abs_csv((FIXTURES / "abs_cpi_sample.csv").read_text())

    assert parsed["series"][0]["unit"] == "Index Numbers"
    assert parsed["series"][0]["unit_multiplier"] is None


def _abs_csv_row(unit_measure: str, unit_mult: str) -> str:
    return "\n".join(
        [
            "DATAFLOW,MEASURE,DATA_ITEM,TSEST,REGION,FREQ,TIME_PERIOD,OBS_VALUE,"
            "UNIT_MEASURE,UNIT_MULT,OBS_STATUS,OBS_COMMENT",
            f"ABS:ANA_AGG(1.0.0),M2,GNI,20,AUS,Q,2025-Q2,736601.0,{unit_measure},{unit_mult},,",
        ]
    )


def test_parse_abs_csv_does_not_double_append_already_scaled_unit() -> None:
    # Some ABS units ship pre-scaled labels (e.g. "$ Millions"); the composer
    # must not append ", millions" a second time in that case.
    parsed = parse_abs_csv(_abs_csv_row("$ Millions", "6"))

    assert parsed["series"][0]["unit"] == "$ Millions"


def test_parse_abs_csv_does_not_double_append_dollar_letter_abbreviation() -> None:
    # "$m"-style abbreviations already encode the scale even though they don't
    # contain the word "million"; the multiplier word must not be appended.
    parsed = parse_abs_csv(_abs_csv_row("$m", "6"))

    assert parsed["series"][0]["unit"] == "$m"


def test_parse_abs_csv_does_not_double_append_mismatched_scale_word() -> None:
    # A unit already carrying a scale word (even one that doesn't match the
    # current multiplier) must not get a second, contradictory scale appended.
    parsed = parse_abs_csv(_abs_csv_row("$ Millions", "3"))

    assert parsed["series"][0]["unit"] == "$ Millions"


def test_parse_abs_csv_does_not_double_append_thousands_convention() -> None:
    # "'000" is a common pre-scaled convention in published tables.
    parsed = parse_abs_csv(_abs_csv_row("'000", "3"))

    assert parsed["series"][0]["unit"] == "'000"


def test_parse_abs_csv_composes_when_unit_has_no_scale_indicator() -> None:
    parsed = parse_abs_csv(_abs_csv_row("Number", "3"))

    assert parsed["series"][0]["unit"] == "Number, thousands"


def test_parse_abs_csv_composes_for_unit_ending_in_letter_m_but_not_dollar_abbreviation() -> None:
    # "per annum" ends in the letter "m" but is not a "$m"-style abbreviation,
    # so the double-append guard must not false-positive on it.
    parsed = parse_abs_csv(_abs_csv_row("Percent per annum", "3"))

    assert parsed["series"][0]["unit"] == "Percent per annum, thousands"


def test_parse_abs_csv_unusual_exponent_uses_power_of_ten_notation() -> None:
    csv_text = "\n".join(
        [
            "DATAFLOW,MEASURE,DATA_ITEM,TSEST,REGION,FREQ,TIME_PERIOD,OBS_VALUE,"
            "UNIT_MEASURE,UNIT_MULT,OBS_STATUS,OBS_COMMENT",
            "ABS:ANA_AGG(1.0.0),M2,GNI,20,AUS,Q,2025-Q2,1.0,Australian Dollars,2,,",
        ]
    )
    parsed = parse_abs_csv(csv_text)

    assert parsed["series"][0]["unit"] == "Australian Dollars, x10^2"


def test_parse_abs_csv_preserves_decimals_base_period_and_comments() -> None:
    csv_text = "\n".join(
        [
            "DATAFLOW,MEASURE,INDEX,TSEST,REGION,FREQ,TIME_PERIOD,OBS_VALUE,"
            "UNIT_MEASURE,OBS_STATUS,DECIMALS,OBS_COMMENT,BASE_PERIOD",
            "ABS:CPI(2.0.0),1,10001,10,50,Q,2025-Q2,140.2,IN,,1,sample comment,2011-12",
        ]
    )
    parsed = parse_abs_csv(csv_text)

    assert parsed["series"][0]["decimals"] == 1
    assert parsed["series"][0]["base_period"] == "2011-12"
    assert parsed["observations"][0]["comment"] == "sample comment"


def test_parse_rba_csv_extracts_metadata_and_long_observations() -> None:
    parsed = parse_rba_csv(
        (FIXTURES / "rba_g1_sample.csv").read_text(encoding="utf-8"), table_id="g1"
    )

    assert parsed["metadata"]["source"] == "rba"
    assert parsed["metadata"]["dataset_id"] == "g1"
    assert parsed["metadata"]["title"] == "G1 CONSUMER PRICE INFLATION"
    assert len(parsed["series"]) == 3
    assert parsed["series"][1]["series_id"] == "GCPIAGYP"
    assert parsed["series"][1]["unit"] == "Per cent"
    assert parsed["observations"][0]["date"] == "1922-06-30"
    assert parsed["observations"][-1]["series_id"] == "GCPIAGSAQP"
    assert parsed["observations"][-1]["value"] == 3.1


def test_parse_rba_csv_supports_a2_event_format_and_range_cells() -> None:
    parsed = parse_rba_csv(
        (FIXTURES / "rba_a2_sample.csv").read_text(encoding="utf-8"), table_id="a2"
    )

    assert parsed["metadata"]["source"] == "rba"
    assert parsed["metadata"]["dataset_id"] == "a2"
    assert parsed["metadata"]["title"] == (
        "A2 RESERVE BANK OF AUSTRALIA – CHANGES IN MONETARY POLICY AND ADMINISTERED RATES"
    )
    assert len(parsed["series"]) == 6
    assert parsed["observations"][0]["date"] == "1990-01-23"
    assert parsed["observations"][0]["series_id"] == "ARBAMPCCCR"
    assert parsed["observations"][0]["value"] is None
    assert parsed["observations"][0]["raw_value"] == "-0.50 to -1.00"
    assert parsed["observations"][1]["series_id"] == "ARBAMPCNCRT"
    assert parsed["observations"][1]["raw_value"] == "17.00 to 17.50"
    assert parsed["observations"][-1]["series_id"] == "ARBAMPNORR"
    assert parsed["observations"][-1]["value"] == 7.25

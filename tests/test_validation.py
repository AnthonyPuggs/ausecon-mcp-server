import pytest

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.validation import (
    validate_abs_period_range,
    validate_apra_series_ids,
    validate_iso_date_range,
    validate_iso_datetime,
    validate_search_query,
    validate_source_token,
)


def test_validate_search_query_accepts_trimmed_plain_text() -> None:
    assert validate_search_query("  wages cafe au lait  ") == "wages cafe au lait"


@pytest.mark.parametrize(
    "query",
    [
        "https:abs.gov.au",
        "labour/force",
        "cash?rate",
        "cash#rate",
        "cash\x00rate",
    ],
)
def test_validate_search_query_rejects_url_path_and_control_text(query: str) -> None:
    with pytest.raises(AuseconValidationError, match="plain search text"):
        validate_search_query(query)


def test_validate_search_query_enforces_length_after_trimming() -> None:
    with pytest.raises(AuseconValidationError, match="no more than 200"):
        validate_search_query(f"  {'x' * 201}  ")


def test_validate_source_token_accepts_trimmed_source_native_identifiers() -> None:
    assert validate_source_token("key", "  1.10001.10.50.Q  ") == "1.10001.10.50.Q"


@pytest.mark.parametrize(
    "value",
    [
        "http:example",
        "CPI/all",
        "CPI?format=csv",
        "CPI#fragment",
        "ABS:CPI",
        "CPI\x1f",
    ],
)
def test_validate_source_token_rejects_url_path_and_control_characters(value: str) -> None:
    with pytest.raises(AuseconValidationError, match="unsupported URL or path"):
        validate_source_token("dataflow_id", value)


def test_validate_apra_series_ids_permits_colon_delimited_source_native_ids() -> None:
    assert validate_apra_series_ids(["ADI_MONTHLY:table_1:11111111111:total_residents_assets"]) == [
        "ADI_MONTHLY:table_1:11111111111:total_residents_assets"
    ]


@pytest.mark.parametrize(
    "series_id",
    [
        "ADI_MONTHLY/table_1",
        "ADI_MONTHLY?table=1",
        "ADI_MONTHLY#table_1",
        "ADI_MONTHLY\x00table_1",
    ],
)
def test_validate_apra_series_ids_rejects_url_path_and_control_characters(
    series_id: str,
) -> None:
    with pytest.raises(AuseconValidationError, match="APRA series identifiers"):
        validate_apra_series_ids([series_id])


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2020", "2024"),
        ("2020-Q1", "2024-Q4"),
        ("2020-01", "2024-12"),
        ("2020-S1", "2024-S2"),
    ],
)
def test_validate_abs_period_range_accepts_supported_matching_frequencies(
    start: str,
    end: str,
) -> None:
    assert validate_abs_period_range(
        start,
        end,
        start_name="start_period",
        end_name="end_period",
    ) == (start, end)


def test_validate_abs_period_range_rejects_reversed_bounds() -> None:
    with pytest.raises(AuseconValidationError, match="earlier than or equal"):
        validate_abs_period_range(
            "2024-Q2",
            "2024-Q1",
            start_name="start_period",
            end_name="end_period",
        )


def test_validate_iso_date_range_rejects_reversed_bounds() -> None:
    with pytest.raises(AuseconValidationError, match="earlier than or equal"):
        validate_iso_date_range(
            "2024-02-01",
            "2024-01-31",
            start_name="start_date",
            end_name="end_date",
        )


@pytest.mark.parametrize(
    "value",
    [
        "2024-01-31",
        "2024-01-31T10:30:00",
        "2024-01-31T10:30:00Z",
        "2024-01-31T10:30:00+10:00",
    ],
)
def test_validate_iso_datetime_accepts_dates_and_datetimes(value: str) -> None:
    assert validate_iso_datetime("updated_after", value) == value

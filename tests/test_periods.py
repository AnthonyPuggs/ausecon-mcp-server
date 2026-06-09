from datetime import date

import pytest

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.periods import (
    period_end_date,
    period_sort_key,
    period_start_date,
    try_period_sort_key,
)


def test_period_start_and_end_dates_for_all_formats() -> None:
    assert period_start_date("2025") == date(2025, 1, 1)
    assert period_end_date("2025") == date(2025, 12, 31)
    assert period_start_date("2025-Q2") == date(2025, 4, 1)
    assert period_end_date("2025-Q2") == date(2025, 6, 30)
    assert period_start_date("2025-S1") == date(2025, 1, 1)
    assert period_end_date("2025-S1") == date(2025, 6, 30)
    assert period_start_date("2025-S2") == date(2025, 7, 1)
    assert period_end_date("2025-S2") == date(2025, 12, 31)
    assert period_start_date("2025-02") == date(2025, 2, 1)
    assert period_end_date("2025-02") == date(2025, 2, 28)
    assert period_start_date("2025-02-14") == date(2025, 2, 14)
    assert period_end_date("2025-02-14") == date(2025, 2, 14)


def test_period_end_date_handles_leap_years() -> None:
    assert period_end_date("2024-02") == date(2024, 2, 29)
    assert period_end_date("2024-Q1") == date(2024, 3, 31)


def test_period_sort_key_orders_mixed_granularities() -> None:
    periods = ["2026-Q1", "2025-12-31", "2025-S1", "2025", "2025-07"]
    ordered = sorted(periods, key=period_sort_key)
    assert ordered == ["2025-S1", "2025-07", "2025-12-31", "2025", "2026-Q1"]


def test_period_helpers_reject_unknown_formats() -> None:
    with pytest.raises(AuseconValidationError, match="Unsupported observation period"):
        period_end_date("13/05/2025")
    with pytest.raises(AuseconValidationError):
        period_start_date("not-a-period")


def test_period_helpers_accept_iso_week_periods() -> None:
    # Parsed explicitly (not via date.fromisoformat, which only accepts ISO week
    # strings on Python 3.11+) so behaviour is identical across supported Pythons.
    assert period_start_date("2025-W01") == date(2024, 12, 30)
    assert period_end_date("2025-W01") == date(2025, 1, 5)
    assert try_period_sort_key("2025-W01") == (2025, 1, 5)
    # 2020 had 53 ISO weeks; 2025 does not.
    assert period_end_date("2020-W53") == date(2021, 1, 3)
    with pytest.raises(AuseconValidationError, match="Unsupported observation period"):
        period_end_date("2025-W53")


def test_try_period_sort_key_returns_none_for_unknown_formats() -> None:
    assert try_period_sort_key("not-a-period") is None
    assert try_period_sort_key("2025-Q4") == (2025, 12, 31)

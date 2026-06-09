"""Shared parsing and ordering helpers for observation periods and date bounds.

Observation dates arrive in any of five formats depending on the source and
frequency: YYYY, YYYY-QN, YYYY-SN, YYYY-MM, or YYYY-MM-DD. Comparisons across
granularities must use parsed calendar dates rather than string order.
"""

from __future__ import annotations

import calendar
import re
from datetime import date

from ausecon_mcp.errors import AuseconValidationError

YEAR_RE = re.compile(r"^(?P<year>\d{4})$")
QUARTER_RE = re.compile(r"^(?P<year>\d{4})-Q(?P<quarter>[1-4])$")
SEMESTER_RE = re.compile(r"^(?P<year>\d{4})-S(?P<semester>[1-2])$")
MONTH_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])$")

ACCEPTED_PERIOD_FORMATS = "YYYY, YYYY-QN, YYYY-SN, YYYY-MM, or YYYY-MM-DD"


def period_start_date(period: str) -> date:
    """Return the first calendar day covered by a period string."""
    if match := QUARTER_RE.fullmatch(period):
        year = int(match.group("year"))
        month = int(match.group("quarter")) * 3 - 2
        return date(year, month, 1)
    if match := SEMESTER_RE.fullmatch(period):
        year = int(match.group("year"))
        return date(year, 1 if match.group("semester") == "1" else 7, 1)
    if match := MONTH_RE.fullmatch(period):
        return date(int(match.group("year")), int(match.group("month")), 1)
    if match := YEAR_RE.fullmatch(period):
        return date(int(match.group("year")), 1, 1)
    return _parse_iso(period)


def period_end_date(period: str) -> date:
    """Return the last calendar day covered by a period string."""
    if match := QUARTER_RE.fullmatch(period):
        year = int(match.group("year"))
        month = int(match.group("quarter")) * 3
        return date(year, month, calendar.monthrange(year, month)[1])
    if match := SEMESTER_RE.fullmatch(period):
        year = int(match.group("year"))
        month = 6 if match.group("semester") == "1" else 12
        return date(year, month, calendar.monthrange(year, month)[1])
    if match := MONTH_RE.fullmatch(period):
        year = int(match.group("year"))
        month = int(match.group("month"))
        return date(year, month, calendar.monthrange(year, month)[1])
    if match := YEAR_RE.fullmatch(period):
        return date(int(match.group("year")), 12, 31)
    return _parse_iso(period)


def period_sort_key(period: str) -> tuple[int, int, int]:
    """Chronological sort key for a period string, based on its end date."""
    parsed = period_end_date(period)
    return parsed.year, parsed.month, parsed.day


def try_period_sort_key(period: str) -> tuple[int, int, int] | None:
    """Like period_sort_key, but returns None for unrecognised formats."""
    try:
        return period_sort_key(period)
    except AuseconValidationError:
        return None


def _parse_iso(period: str) -> date:
    try:
        return date.fromisoformat(period)
    except (TypeError, ValueError) as exc:
        raise AuseconValidationError(
            f"Unsupported observation period {period!r}; expected {ACCEPTED_PERIOD_FORMATS}."
        ) from exc

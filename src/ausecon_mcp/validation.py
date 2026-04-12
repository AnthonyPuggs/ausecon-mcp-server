from __future__ import annotations

import re
from datetime import date, datetime

from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.errors import AuseconValidationError

_ABS_PERIOD_PATTERNS = {
    "annual": re.compile(r"^\d{4}$"),
    "quarterly": re.compile(r"^\d{4}-Q[1-4]$"),
    "monthly": re.compile(r"^\d{4}-(0[1-9]|1[0-2])$"),
    "half_yearly": re.compile(r"^\d{4}-S[1-2]$"),
}

_RBA_CATEGORIES = {entry["category"] for entry in RBA_CATALOGUE.values()}
_ALLOWED_SOURCES = {"abs", "rba"}


def validate_search_query(query: str) -> str:
    return require_non_empty("query", query)


def validate_source(source: str | None) -> str | None:
    if source is None:
        return None

    normalised = require_non_empty("source", source).lower()
    if normalised not in _ALLOWED_SOURCES:
        allowed = ", ".join(sorted(_ALLOWED_SOURCES))
        raise AuseconValidationError(f"source must be one of: {allowed}.")
    return normalised


def validate_rba_category(category: str | None) -> str | None:
    if category is None:
        return None

    normalised = require_non_empty("category", category)
    if normalised not in _RBA_CATEGORIES:
        allowed = ", ".join(sorted(_RBA_CATEGORIES))
        raise AuseconValidationError(f"category must be one of: {allowed}.")
    return normalised


def require_non_empty(field_name: str, value: str) -> str:
    normalised = (value or "").strip()
    if not normalised:
        raise AuseconValidationError(f"{field_name} must not be empty.")
    return normalised


def validate_positive_int(field_name: str, value: int | None) -> int | None:
    if value is None:
        return None
    if value <= 0:
        raise AuseconValidationError(f"{field_name} must be a positive integer.")
    return value


def validate_series_ids(series_ids: list[str] | None) -> list[str] | None:
    if series_ids is None:
        return None

    normalised = [series_id.strip() for series_id in series_ids]
    if any(not series_id for series_id in normalised):
        raise AuseconValidationError("series_ids must contain only non-empty values.")
    return normalised


def validate_iso_date(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None

    normalised = require_non_empty(field_name, value)
    try:
        date.fromisoformat(normalised)
    except ValueError as exc:
        raise AuseconValidationError(
            f"{field_name} must be an ISO date in YYYY-MM-DD format."
        ) from exc
    return normalised


def validate_iso_datetime(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None

    normalised = require_non_empty(field_name, value)
    try:
        datetime.fromisoformat(normalised.replace("Z", "+00:00"))
    except ValueError:
        try:
            date.fromisoformat(normalised)
        except ValueError as exc:
            raise AuseconValidationError(
                f"{field_name} must be an ISO date or datetime."
            ) from exc
    return normalised


def validate_iso_date_range(
    start: str | None,
    end: str | None,
    *,
    start_name: str,
    end_name: str,
) -> tuple[str | None, str | None]:
    normalised_start = validate_iso_date(start_name, start)
    normalised_end = validate_iso_date(end_name, end)
    if normalised_start and normalised_end and normalised_start > normalised_end:
        raise AuseconValidationError(f"{start_name} must be earlier than or equal to {end_name}.")
    return normalised_start, normalised_end


def validate_abs_period_range(
    start: str | None,
    end: str | None,
    *,
    start_name: str,
    end_name: str,
) -> tuple[str | None, str | None]:
    start_kind, normalised_start = _validate_abs_period(start_name, start)
    end_kind, normalised_end = _validate_abs_period(end_name, end)

    if start_kind and end_kind:
        if start_kind != end_kind:
            raise AuseconValidationError(
                f"{start_name} and {end_name} must use the same frequency."
            )
        if normalised_start > normalised_end:
            raise AuseconValidationError(
                f"{start_name} must be earlier than or equal to {end_name}."
            )

    return normalised_start, normalised_end


def _validate_abs_period(field_name: str, value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None

    normalised = require_non_empty(field_name, value)
    for period_kind, pattern in _ABS_PERIOD_PATTERNS.items():
        if pattern.fullmatch(normalised):
            return period_kind, normalised

    raise AuseconValidationError(
        f"{field_name} must be a valid ABS period in YYYY, YYYY-QN, YYYY-MM, or YYYY-SN format."
    )

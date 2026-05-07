from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from ausecon_mcp.errors import AuseconValidationError

_YEAR_RE = re.compile(r"^(?P<year>\d{4})$")
_QUARTER_RE = re.compile(r"^(?P<year>\d{4})-Q(?P<quarter>[1-4])$")
_SEMESTER_RE = re.compile(r"^(?P<year>\d{4})-S(?P<semester>[1-2])$")
_MONTH_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])$")
_ACCEPTED_BOUND_FORMATS = "YYYY, YYYY-QN, YYYY-SN, YYYY-MM, or YYYY-MM-DD"


@dataclass(frozen=True)
class NormalisedSemanticBounds:
    start: str | None
    end: str | None
    requested_start: str | None
    requested_end: str | None


@dataclass(frozen=True)
class _ParsedBound:
    kind: str
    year: int
    month: int | None = None
    day: int | None = None
    quarter: int | None = None
    semester: int | None = None


def normalise_semantic_bounds(
    resolved: Any,
    *,
    start: str | None,
    end: str | None,
) -> NormalisedSemanticBounds:
    """Normalise analyst-friendly semantic bounds to source-native provider bounds."""
    if resolved.source == "rba":
        return NormalisedSemanticBounds(
            start=_normalise_rba_bound("start", start, side="start"),
            end=_normalise_rba_bound("end", end, side="end"),
            requested_start=start,
            requested_end=end,
        )

    frequency = _infer_abs_frequency(resolved)
    return NormalisedSemanticBounds(
        start=_normalise_abs_bound("start", start, frequency=frequency, side="start"),
        end=_normalise_abs_bound("end", end, frequency=frequency, side="end"),
        requested_start=start,
        requested_end=end,
    )


def _infer_abs_frequency(resolved: Any) -> str:
    if resolved.frequency:
        return resolved.frequency

    if resolved.abs_key:
        candidate = resolved.abs_key.split(".")[-1]
        if candidate in {"A", "Q", "M", "S"}:
            return candidate

    frequencies = list(resolved.entry.get("frequencies", []))
    if len(frequencies) == 1 and frequencies[0] in {"A", "Q", "M", "S"}:
        return frequencies[0]

    raise AuseconValidationError(
        f"Could not infer an ABS frequency for {resolved.dataset_id!r}; pass frequency explicitly."
    )


def _normalise_abs_bound(
    field_name: str,
    value: str | None,
    *,
    frequency: str,
    side: Literal["start", "end"],
) -> str | None:
    parsed = _parse_bound(field_name, value)
    if parsed is None:
        return None

    if frequency == "A":
        return f"{parsed.year:04d}"
    if frequency == "Q":
        quarter = _quarter_for(parsed, side)
        return f"{parsed.year:04d}-Q{quarter}"
    if frequency == "M":
        month = _month_for(parsed, side)
        return f"{parsed.year:04d}-{month:02d}"
    if frequency == "S":
        semester = _semester_for(parsed, side)
        return f"{parsed.year:04d}-S{semester}"

    raise AuseconValidationError(
        f"Unsupported ABS frequency {frequency!r} for semantic date normalisation."
    )


def _normalise_rba_bound(
    field_name: str,
    value: str | None,
    *,
    side: Literal["start", "end"],
) -> str | None:
    parsed = _parse_bound(field_name, value)
    if parsed is None:
        return None

    if parsed.kind == "date":
        month = parsed.month
        day = parsed.day
        assert month is not None and day is not None
        return f"{parsed.year:04d}-{month:02d}-{day:02d}"

    month = _month_for(parsed, side)
    day = 1 if side == "start" else calendar.monthrange(parsed.year, month)[1]
    return f"{parsed.year:04d}-{month:02d}-{day:02d}"


def _parse_bound(field_name: str, value: str | None) -> _ParsedBound | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        raise AuseconValidationError(f"{field_name} must not be empty.")

    if match := _YEAR_RE.fullmatch(text):
        return _ParsedBound(kind="year", year=int(match.group("year")))
    if match := _QUARTER_RE.fullmatch(text):
        return _ParsedBound(
            kind="quarter",
            year=int(match.group("year")),
            quarter=int(match.group("quarter")),
        )
    if match := _SEMESTER_RE.fullmatch(text):
        return _ParsedBound(
            kind="semester",
            year=int(match.group("year")),
            semester=int(match.group("semester")),
        )
    if match := _MONTH_RE.fullmatch(text):
        return _ParsedBound(
            kind="month",
            year=int(match.group("year")),
            month=int(match.group("month")),
        )
    try:
        parsed_date = date.fromisoformat(text)
    except ValueError as exc:
        raise AuseconValidationError(
            f"{field_name} must be a semantic date bound in {_ACCEPTED_BOUND_FORMATS} format."
        ) from exc

    return _ParsedBound(
        kind="date",
        year=parsed_date.year,
        month=parsed_date.month,
        day=parsed_date.day,
    )


def _month_for(parsed: _ParsedBound, side: Literal["start", "end"]) -> int:
    if parsed.kind in {"month", "date"}:
        assert parsed.month is not None
        return parsed.month
    if parsed.kind == "quarter":
        assert parsed.quarter is not None
        return (parsed.quarter - 1) * 3 + (1 if side == "start" else 3)
    if parsed.kind == "semester":
        assert parsed.semester is not None
        return 1 if parsed.semester == 1 and side == "start" else (
            6 if parsed.semester == 1 else 7 if side == "start" else 12
        )
    return 1 if side == "start" else 12


def _quarter_for(parsed: _ParsedBound, side: Literal["start", "end"]) -> int:
    if parsed.kind == "quarter":
        assert parsed.quarter is not None
        return parsed.quarter
    if parsed.kind == "semester":
        assert parsed.semester is not None
        return 1 if parsed.semester == 1 and side == "start" else (
            2 if parsed.semester == 1 else 3 if side == "start" else 4
        )
    month = _month_for(parsed, side)
    return ((month - 1) // 3) + 1


def _semester_for(parsed: _ParsedBound, side: Literal["start", "end"]) -> int:
    if parsed.kind == "semester":
        assert parsed.semester is not None
        return parsed.semester
    if parsed.kind == "quarter":
        assert parsed.quarter is not None
        if parsed.quarter in {1, 2}:
            return 1
        return 2
    month = _month_for(parsed, side)
    return 1 if month <= 6 else 2

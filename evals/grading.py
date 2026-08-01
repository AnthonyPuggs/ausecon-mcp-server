from __future__ import annotations

import re
from dataclasses import dataclass

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_QUARTER_MONTHS = {"march": 1, "june": 2, "september": 3, "december": 4}

_UNIT_ALIASES = {
    "per cent": "per cent",
    "percent": "per cent",
    "%": "per cent",
    "pct": "per cent",
    "percentage points": "percentage points",
    "pp": "percentage points",
    "ppt": "percentage points",
    "ppts": "percentage points",
    "index points": "index points",
    "index": "index points",
    "aud millions": "aud millions",
    "$ millions": "aud millions",
    "millions of dollars": "aud millions",
    "a$ millions": "aud millions",
    "aud billions": "aud billions",
    "$ billions": "aud billions",
    "usd per aud": "usd per aud",
    "usd": "usd per aud",
}


@dataclass(frozen=True)
class GroundTruth:
    value: float
    period: str
    unit: str


@dataclass(frozen=True)
class Verdict:
    outcome: str
    value_ok: bool
    fresh: bool
    unit_flag: bool


def normalize_period(text: str) -> str | None:
    cleaned = text.strip().lower()
    if not cleaned:
        return None
    if match := re.fullmatch(r"(\d{4})-q([1-4])", cleaned):
        return f"{match.group(1)}-Q{match.group(2)}"
    if match := re.fullmatch(r"q([1-4])[ ,]+(\d{4})", cleaned):
        return f"{match.group(2)}-Q{match.group(1)}"
    if match := re.fullmatch(r"(\w+) quarter[ ,]+(\d{4})", cleaned):
        quarter = _QUARTER_MONTHS.get(match.group(1))
        return f"{match.group(2)}-Q{quarter}" if quarter else None
    if match := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", cleaned):
        return cleaned
    if match := re.fullmatch(r"(\d{1,2})[ ]+(\w+)[ ,]+(\d{4})", cleaned):
        month = _MONTHS.get(match.group(2))
        return f"{match.group(3)}-{month:02d}-{int(match.group(1)):02d}" if month else None
    if match := re.fullmatch(r"(\d{4})-(\d{2})", cleaned):
        return cleaned
    if match := re.fullmatch(r"(\w+)[ ,]+(\d{4})", cleaned):
        month = _MONTHS.get(match.group(1))
        return f"{match.group(2)}-{month:02d}" if month else None
    if re.fullmatch(r"\d{4}", cleaned):
        return cleaned
    return None


def _normalize_unit(unit: str) -> str:
    return _UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())


def grade(submitted: dict | None, truth: GroundTruth, tolerance: float) -> Verdict:
    if submitted is None:
        return Verdict(outcome="no_answer", value_ok=False, fresh=False, unit_flag=False)
    if submitted.get("not_found"):
        return Verdict(outcome="abstain", value_ok=False, fresh=False, unit_flag=False)

    try:
        value = float(submitted["value"])
    except (KeyError, TypeError, ValueError):
        return Verdict(outcome="no_answer", value_ok=False, fresh=False, unit_flag=False)

    value_ok = abs(value - truth.value) <= tolerance + 1e-10
    submitted_period = normalize_period(str(submitted.get("period", "")))
    truth_period = normalize_period(truth.period)
    fresh = submitted_period is not None and submitted_period == truth_period
    unit_flag = _normalize_unit(str(submitted.get("unit", ""))) != _normalize_unit(truth.unit)

    outcome = "correct" if value_ok else "incorrect"
    return Verdict(outcome=outcome, value_ok=value_ok, fresh=fresh, unit_flag=unit_flag)

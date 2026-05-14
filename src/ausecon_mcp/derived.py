from __future__ import annotations

import calendar
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Literal

from ausecon_mcp.errors import AuseconValidationError

_YEAR_RE = re.compile(r"^(?P<year>\d{4})$")
_QUARTER_RE = re.compile(r"^(?P<year>\d{4})-Q(?P<quarter>[1-4])$")
_SEMESTER_RE = re.compile(r"^(?P<year>\d{4})-S(?P<semester>[1-2])$")
_MONTH_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class OperandSpec:
    name: str
    concept: str


@dataclass(frozen=True)
class DerivedSpec:
    concept: str
    label: str
    description: str
    frequency: Literal["Daily", "Monthly", "Quarterly"]
    unit: str
    formula: str
    operands: tuple[OperandSpec, ...]
    compute: Callable[[dict[str, dict[str, float]]], list[tuple[str, float]]]


def _compute_yield_curve_slope(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    long_yield = values["long_yield"]
    short_yield = values["short_yield"]
    dates = sorted(set(long_yield) & set(short_yield), key=_period_sort_key)
    return [(period, _round(long_yield[period] - short_yield[period])) for period in dates]


def _compute_real_cash_rate(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    cash_rate = values["cash_rate"]
    inflation = values["inflation"]
    cash_items = sorted(cash_rate.items(), key=lambda item: _period_end_date(item[0]))
    results: list[tuple[str, float]] = []
    cash_index = 0
    latest_cash: float | None = None

    sorted_inflation = sorted(
        inflation.items(),
        key=lambda item: _period_sort_key(item[0]),
    )
    for period, inflation_value in sorted_inflation:
        period_end = _period_end_date(period)
        while (
            cash_index < len(cash_items)
            and _period_end_date(cash_items[cash_index][0]) <= period_end
        ):
            latest_cash = cash_items[cash_index][1]
            cash_index += 1
        if latest_cash is None:
            continue
        results.append((period, _round(latest_cash - inflation_value)))

    return results


def _compute_real_wage_growth(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    wage_growth = values["wage_growth"]
    cpi_index = values["cpi_index"]
    cpi_yoy: dict[str, float] = {}
    for period, index_value in cpi_index.items():
        lag_period = shift_quarter(period, -4)
        lag_value = cpi_index.get(lag_period)
        if lag_value in (None, 0):
            continue
        cpi_yoy[period] = _round(100 * (index_value / lag_value - 1))

    dates = sorted(set(wage_growth) & set(cpi_yoy), key=_period_sort_key)
    return [(period, _round(wage_growth[period] - cpi_yoy[period])) for period in dates]


def _compute_credit_growth(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    total_credit = values["total_credit"]
    results: list[tuple[str, float]] = []
    for period in sorted(total_credit, key=_period_sort_key):
        lag_period = shift_month(period, -12)
        lag_value = total_credit.get(lag_period)
        if lag_value in (None, 0):
            continue
        results.append((period, _round(100 * (total_credit[period] / lag_value - 1))))
    return results


def _compute_gdp_per_capita(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    real_gdp = values["real_gdp"]
    population = values["population"]
    dates = sorted(set(real_gdp) & set(population), key=_period_sort_key)
    results: list[tuple[str, float]] = []
    for period in dates:
        population_value = population[period]
        if population_value == 0:
            continue
        results.append((period, _round(real_gdp[period] * 1_000_000 / population_value)))
    return results


DERIVED_CONCEPTS: dict[str, DerivedSpec] = {
    "yield_curve_slope": DerivedSpec(
        concept="yield_curve_slope",
        label="Yield curve slope",
        description="Ten-year Australian government bond yield less three-year yield.",
        frequency="Daily",
        unit="percentage points",
        formula="government_bond_yield_10y - government_bond_yield_3y",
        operands=(
            OperandSpec("long_yield", "government_bond_yield_10y"),
            OperandSpec("short_yield", "government_bond_yield_3y"),
        ),
        compute=_compute_yield_curve_slope,
    ),
    "real_cash_rate": DerivedSpec(
        concept="real_cash_rate",
        label="Real cash rate",
        description="RBA cash-rate target less complete monthly CPI year-ended inflation.",
        frequency="Monthly",
        unit="percentage points",
        formula="cash_rate_target - monthly_inflation",
        operands=(
            OperandSpec("cash_rate", "cash_rate_target"),
            OperandSpec("inflation", "monthly_inflation"),
        ),
        compute=_compute_real_cash_rate,
    ),
    "real_wage_growth": DerivedSpec(
        concept="real_wage_growth",
        label="Real wage growth",
        description=(
            "Wage Price Index year-ended growth less derived headline CPI year-ended growth."
        ),
        frequency="Quarterly",
        unit="percentage points",
        formula="wage_growth - headline_cpi_yoy",
        operands=(
            OperandSpec("wage_growth", "wage_growth"),
            OperandSpec("cpi_index", "headline_cpi"),
        ),
        compute=_compute_real_wage_growth,
    ),
    "credit_growth": DerivedSpec(
        concept="credit_growth",
        label="Credit growth",
        description="Year-ended growth in total credit derived from RBA total-credit levels.",
        frequency="Monthly",
        unit="percent year-ended",
        formula="100 * (total_credit_t / total_credit_t-12 - 1)",
        operands=(OperandSpec("total_credit", "total_credit"),),
        compute=_compute_credit_growth,
    ),
    "gdp_per_capita": DerivedSpec(
        concept="gdp_per_capita",
        label="Real GDP per capita",
        description="Quarterly real GDP in chained-volume dollars per resident person.",
        frequency="Quarterly",
        unit="real AUD per person",
        formula="real_gdp * 1_000_000 / population",
        operands=(
            OperandSpec("real_gdp", "real_gdp"),
            OperandSpec("population", "population"),
        ),
        compute=_compute_gdp_per_capita,
    ),
}


def list_derived_concepts() -> list[str]:
    return sorted(DERIVED_CONCEPTS)


def get_derived_spec(concept: str) -> DerivedSpec:
    spec = DERIVED_CONCEPTS.get(concept)
    if spec is None:
        supported = ", ".join(list_derived_concepts())
        raise AuseconValidationError(
            f"Unknown derived concept {concept!r}. Supported derived concepts: {supported}."
        )
    return spec


def get_operand_specs(concept: str) -> tuple[OperandSpec, ...]:
    return get_derived_spec(concept).operands


def validate_derived_bounds(
    concept: str,
    *,
    start: str | None,
    end: str | None,
) -> tuple[str | None, str | None]:
    spec = get_derived_spec(concept)
    normalised_start = normalise_bound(start, frequency=spec.frequency, side="start")
    normalised_end = normalise_bound(end, frequency=spec.frequency, side="end")
    if (
        normalised_start is not None
        and normalised_end is not None
        and _comparison_key(normalised_start, frequency=spec.frequency)
        > _comparison_key(normalised_end, frequency=spec.frequency)
    ):
        raise AuseconValidationError("start must be before or equal to end.")
    return normalised_start, normalised_end


def operand_request_bounds(
    concept: str,
    operand_name: str,
    *,
    start: str | None,
    end: str | None,
) -> tuple[str | None, str | None]:
    normalised_start, normalised_end = validate_derived_bounds(concept, start=start, end=end)

    if concept == "credit_growth" and operand_name == "total_credit" and normalised_start:
        normalised_start = shift_month(normalised_start, -12)
    elif concept == "real_wage_growth" and operand_name == "cpi_index" and normalised_start:
        normalised_start = shift_quarter(normalised_start, -4)
    elif concept == "real_cash_rate" and operand_name == "cash_rate":
        normalised_start = None

    return normalised_start, normalised_end


def derive_series(
    concept: str,
    operands: dict[str, dict],
    *,
    requested_start: str | None,
    requested_end: str | None,
    last_n: int | None,
    server_version: str,
) -> dict[str, Any]:
    spec = get_derived_spec(concept)
    missing_operands = [operand.name for operand in spec.operands if operand.name not in operands]
    if missing_operands:
        missing = ", ".join(missing_operands)
        raise AuseconValidationError(f"Missing operand payloads for {concept!r}: {missing}.")

    operand_values = {
        operand.name: _values_by_period(operands[operand.name]) for operand in spec.operands
    }
    derived_values = spec.compute(operand_values)
    input_observation_count = sum(len(values) for values in operand_values.values())
    unfiltered_count = len(derived_values)

    resolved_start, resolved_end = validate_derived_bounds(
        concept,
        start=requested_start,
        end=requested_end,
    )
    derived_values = _filter_values(
        derived_values,
        start=resolved_start,
        end=resolved_end,
        frequency=spec.frequency,
    )

    truncated = False
    if last_n is not None and len(derived_values) > last_n:
        derived_values = derived_values[-last_n:]
        truncated = True

    dimensions = {"DERIVED_CONCEPT": {"code": spec.concept, "label": spec.label}}
    observations = [
        {
            "date": period,
            "series_id": spec.concept,
            "value": value,
            "dimensions": dimensions,
            "status": None,
            "comment": None,
        }
        for period, value in derived_values
    ]

    return {
        "metadata": {
            "source": "derived",
            "dataset_id": spec.concept,
            "frequency": spec.frequency,
            "title": spec.label,
            "publication_date": None,
            "retrieval_url": f"derived:{spec.concept}",
            "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "server_version": server_version,
            "truncated": truncated,
            "derived": {
                "concept": spec.concept,
                "formula": spec.formula,
                "operands": [
                    _operand_metadata(operand.name, operand.concept, operands[operand.name])
                    for operand in spec.operands
                ],
                "source_concepts": [operand.concept for operand in spec.operands],
                "alignment_frequency": spec.frequency,
                "units": spec.unit,
                "requested_bounds": {"start": requested_start, "end": requested_end},
                "resolved_bounds": {"start": resolved_start, "end": resolved_end},
                "dropped_observations": {
                    "input": input_observation_count,
                    "derived": unfiltered_count,
                    "returned": len(observations),
                    "dropped": max(input_observation_count - unfiltered_count, 0),
                },
            },
        },
        "series": [
            {
                "series_id": spec.concept,
                "label": spec.label,
                "unit": spec.unit,
                "frequency": spec.frequency,
                "dimensions": dimensions,
                "source_key": spec.concept,
                "unit_multiplier": None,
                "decimals": None,
                "base_period": None,
            }
        ]
        if observations
        else [],
        "observations": observations,
    }


def _values_by_period(payload: dict) -> dict[str, float]:
    values: dict[str, float] = {}
    series_ids = {series.get("series_id") for series in payload.get("series", [])}
    for observation in payload.get("observations", []):
        series_id = observation.get("series_id")
        if series_ids and series_id not in series_ids:
            continue
        value = observation.get("value")
        if value is None:
            continue
        values[str(observation["date"])] = float(value)
    return values


def _operand_metadata(name: str, concept: str, payload: dict) -> dict[str, Any]:
    metadata = payload.get("metadata", {})
    semantic = metadata.get("semantic", {})
    target = semantic.get("target", {})
    series_ids = [
        series.get("series_id") for series in payload.get("series", []) if series.get("series_id")
    ]

    return {
        "name": name,
        "concept": semantic.get("concept") or concept,
        "source": target.get("source") or metadata.get("source"),
        "dataset_id": target.get("dataset_id") or metadata.get("dataset_id"),
        "upstream_id": target.get("upstream_id") or metadata.get("dataset_id"),
        "abs_key": target.get("abs_key"),
        "rba_series_ids": target.get("rba_series_ids"),
        "series_ids": series_ids,
    }


def _filter_values(
    values: list[tuple[str, float]],
    *,
    start: str | None,
    end: str | None,
    frequency: Literal["Daily", "Monthly", "Quarterly"],
) -> list[tuple[str, float]]:
    filtered = values
    if start is not None:
        start_key = _comparison_key(start, frequency=frequency)
        filtered = [
            (period, value)
            for period, value in filtered
            if _comparison_key(period, frequency=frequency) >= start_key
        ]
    if end is not None:
        end_key = _comparison_key(end, frequency=frequency)
        filtered = [
            (period, value)
            for period, value in filtered
            if _comparison_key(period, frequency=frequency) <= end_key
        ]
    return filtered


def normalise_bound(
    value: str | None,
    *,
    frequency: Literal["Daily", "Monthly", "Quarterly"],
    side: Literal["start", "end"],
) -> str | None:
    parsed = _parse_bound(value)
    if parsed is None:
        return None

    if frequency == "Daily":
        return _bound_date(parsed, side=side).isoformat()
    if frequency == "Monthly":
        year, month = _bound_month(parsed, side=side)
        return f"{year:04d}-{month:02d}"
    if frequency == "Quarterly":
        year, quarter = _bound_quarter(parsed, side=side)
        return f"{year:04d}-Q{quarter}"

    raise AuseconValidationError(f"Unsupported derived frequency {frequency!r}.")


def shift_month(period: str, months: int) -> str:
    match = _MONTH_RE.fullmatch(period)
    if match is None:
        raise AuseconValidationError(f"Expected monthly period YYYY-MM, got {period!r}.")
    year = int(match.group("year"))
    month = int(match.group("month"))
    index = year * 12 + (month - 1) + months
    shifted_year, shifted_month_index = divmod(index, 12)
    return f"{shifted_year:04d}-{shifted_month_index + 1:02d}"


def shift_quarter(period: str, quarters: int) -> str:
    match = _QUARTER_RE.fullmatch(period)
    if match is None:
        raise AuseconValidationError(f"Expected quarterly period YYYY-QN, got {period!r}.")
    year = int(match.group("year"))
    quarter = int(match.group("quarter"))
    index = year * 4 + (quarter - 1) + quarters
    shifted_year, shifted_quarter_index = divmod(index, 4)
    return f"{shifted_year:04d}-Q{shifted_quarter_index + 1}"


@dataclass(frozen=True)
class _ParsedBound:
    kind: str
    year: int
    month: int | None = None
    day: int | None = None
    quarter: int | None = None
    semester: int | None = None


def _parse_bound(value: str | None) -> _ParsedBound | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        raise AuseconValidationError("start and end must not be empty.")

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
            "Derived date bounds must use YYYY, YYYY-QN, YYYY-SN, YYYY-MM, or YYYY-MM-DD."
        ) from exc
    return _ParsedBound(
        kind="date",
        year=parsed_date.year,
        month=parsed_date.month,
        day=parsed_date.day,
    )


def _bound_date(parsed: _ParsedBound, *, side: Literal["start", "end"]) -> date:
    year, month = _bound_month(parsed, side=side)
    if parsed.kind == "date":
        assert parsed.day is not None
        return date(parsed.year, month, parsed.day)
    day = 1 if side == "start" else calendar.monthrange(year, month)[1]
    return date(year, month, day)


def _bound_month(parsed: _ParsedBound, *, side: Literal["start", "end"]) -> tuple[int, int]:
    if parsed.kind in {"date", "month"}:
        assert parsed.month is not None
        return parsed.year, parsed.month
    if parsed.kind == "quarter":
        assert parsed.quarter is not None
        month = (parsed.quarter - 1) * 3 + (1 if side == "start" else 3)
        return parsed.year, month
    if parsed.kind == "semester":
        assert parsed.semester is not None
        if parsed.semester == 1:
            return parsed.year, 1 if side == "start" else 6
        return parsed.year, 7 if side == "start" else 12
    return parsed.year, 1 if side == "start" else 12


def _bound_quarter(parsed: _ParsedBound, *, side: Literal["start", "end"]) -> tuple[int, int]:
    if parsed.kind == "quarter":
        assert parsed.quarter is not None
        return parsed.year, parsed.quarter
    if parsed.kind == "semester":
        assert parsed.semester is not None
        if parsed.semester == 1:
            return parsed.year, 1 if side == "start" else 2
        return parsed.year, 3 if side == "start" else 4
    _, month = _bound_month(parsed, side=side)
    return parsed.year, ((month - 1) // 3) + 1


def _comparison_key(
    period: str,
    *,
    frequency: Literal["Daily", "Monthly", "Quarterly"],
) -> tuple[int, int, int]:
    if frequency == "Daily":
        parsed_date = _period_end_date(period)
        return parsed_date.year, parsed_date.month, parsed_date.day
    if frequency == "Monthly":
        match = _MONTH_RE.fullmatch(period)
        if match is None:
            parsed_date = _period_end_date(period)
            return parsed_date.year, parsed_date.month, 1
        return int(match.group("year")), int(match.group("month")), 1
    if frequency == "Quarterly":
        match = _QUARTER_RE.fullmatch(period)
        if match is None:
            parsed_date = _period_end_date(period)
            return parsed_date.year, ((parsed_date.month - 1) // 3) + 1, 1
        return int(match.group("year")), int(match.group("quarter")), 1
    raise AuseconValidationError(f"Unsupported derived frequency {frequency!r}.")


def _period_sort_key(period: str) -> tuple[int, int, int]:
    parsed_date = _period_end_date(period)
    return parsed_date.year, parsed_date.month, parsed_date.day


def _period_end_date(period: str) -> date:
    if match := _QUARTER_RE.fullmatch(period):
        year = int(match.group("year"))
        month = int(match.group("quarter")) * 3
        return date(year, month, calendar.monthrange(year, month)[1])
    if match := _MONTH_RE.fullmatch(period):
        year = int(match.group("year"))
        month = int(match.group("month"))
        return date(year, month, calendar.monthrange(year, month)[1])
    if match := _YEAR_RE.fullmatch(period):
        return date(int(match.group("year")), 12, 31)
    try:
        return date.fromisoformat(period)
    except ValueError as exc:
        raise AuseconValidationError(f"Unsupported derived observation period {period!r}.") from exc


def _round(value: float) -> float:
    return round(value, 10)

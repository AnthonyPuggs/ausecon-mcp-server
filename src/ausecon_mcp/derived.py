from __future__ import annotations

import calendar
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Literal

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.periods import (
    MONTH_RE as _MONTH_RE,
)
from ausecon_mcp.periods import (
    QUARTER_RE as _QUARTER_RE,
)
from ausecon_mcp.periods import (
    SEMESTER_RE as _SEMESTER_RE,
)
from ausecon_mcp.periods import (
    YEAR_RE as _YEAR_RE,
)
from ausecon_mcp.periods import (
    period_end_date as _period_end_date,
)
from ausecon_mcp.periods import (
    period_sort_key as _period_sort_key,
)


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
    alignment_method: Literal["locf", "exact_month", "period_intersection", "year_ended_lag"]
    operands: tuple[OperandSpec, ...]
    compute: Callable[[dict[str, dict[str, float]]], list[tuple[str, float]]]


def _compute_yield_curve_slope(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    long_yield = values["long_yield"]
    short_yield = values["short_yield"]
    dates = sorted(set(long_yield) & set(short_yield), key=_period_sort_key)
    return [(period, _round(long_yield[period] - short_yield[period])) for period in dates]


def _real_rate_minus_inflation(
    rate: dict[str, float],
    inflation: dict[str, float],
) -> list[tuple[str, float]]:
    """Carry a higher-frequency rate forward to each inflation period, then subtract.

    Shared by the real-rate family. ``rate`` may be daily (cash rate, bond yield,
    bank bill rate); the latest rate observed on or before each inflation period
    end is used.
    """
    rate_items = sorted(rate.items(), key=lambda item: _period_end_date(item[0]))
    results: list[tuple[str, float]] = []
    rate_index = 0
    latest_rate: float | None = None

    sorted_inflation = sorted(inflation.items(), key=lambda item: _period_sort_key(item[0]))
    for period, inflation_value in sorted_inflation:
        period_end = _period_end_date(period)
        while (
            rate_index < len(rate_items)
            and _period_end_date(rate_items[rate_index][0]) <= period_end
        ):
            latest_rate = rate_items[rate_index][1]
            rate_index += 1
        if latest_rate is None:
            continue
        results.append((period, _round(latest_rate - inflation_value)))

    return results


def _monthly_year_ended_growth(levels: dict[str, float]) -> list[tuple[str, float]]:
    """Year-ended percentage growth of a monthly level series (current vs 12 months prior).

    Robust to both ``YYYY-MM`` (ABS) and ``YYYY-MM-DD`` end-of-month (RBA) period
    formats by indexing observations on their (year, month) rather than reconstructing
    a string key.
    """
    by_month: dict[tuple[int, int], float] = {}
    for period, value in levels.items():
        year, month, _ = _period_sort_key(period)
        by_month[(year, month)] = value

    results: list[tuple[str, float]] = []
    for period in sorted(levels, key=_period_sort_key):
        year, month, _ = _period_sort_key(period)
        lag_value = by_month.get((year - 1, month))
        if lag_value in (None, 0):
            continue
        results.append((period, _round(100 * (levels[period] / lag_value - 1))))
    return results


def _compute_real_cash_rate(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    return _real_rate_minus_inflation(values["cash_rate"], values["inflation"])


def _compute_real_10y_bond_yield(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    return _real_rate_minus_inflation(values["bond_yield"], values["inflation"])


def _compute_real_bank_bill_rate(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    return _real_rate_minus_inflation(values["bank_bill_rate"], values["inflation"])


def _compute_real_business_lending_rate(
    values: dict[str, dict[str, float]],
) -> list[tuple[str, float]]:
    lending_rate = values["lending_rate"]
    inflation = values["inflation"]
    # Align by (year, month): the lending rate is RBA monthly (YYYY-MM-DD
    # end-of-month) while inflation is ABS monthly (YYYY-MM), so the raw
    # period strings never intersect.
    inflation_by_month = {
        _period_sort_key(period)[:2]: value for period, value in inflation.items()
    }
    results: list[tuple[str, float]] = []
    for period in sorted(lending_rate, key=_period_sort_key):
        inflation_value = inflation_by_month.get(_period_sort_key(period)[:2])
        if inflation_value is None:
            continue
        results.append((period, _round(lending_rate[period] - inflation_value)))
    return results


def _compute_broad_money_growth(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    return _monthly_year_ended_growth(values["broad_money"])


def _compute_employment_growth(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    return _monthly_year_ended_growth(values["employment"])


def _compute_misery_index(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    unemployment = values["unemployment_rate"]
    inflation = values["inflation"]
    dates = sorted(set(unemployment) & set(inflation), key=_period_sort_key)
    return [(period, _round(unemployment[period] + inflation[period])) for period in dates]


def _compute_terms_of_trade(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    export_prices = values["export_prices"]
    import_prices = values["import_prices"]
    dates = sorted(set(export_prices) & set(import_prices), key=_period_sort_key)
    results: list[tuple[str, float]] = []
    for period in dates:
        import_value = import_prices[period]
        if import_value in (None, 0):
            continue
        results.append((period, _round(100 * export_prices[period] / import_value)))
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
    return _monthly_year_ended_growth(values["total_credit"])


def _compute_gdp_per_capita(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    real_gdp = values["real_gdp"]
    population = values["population"]
    dates = sorted(set(real_gdp) & set(population), key=_period_sort_key)
    results: list[tuple[str, float]] = []
    for period in dates:
        population_value = population[period]
        if population_value in (None, 0):
            continue
        results.append((period, _round(real_gdp[period] * 1_000_000 / population_value)))
    return results


def _compute_mortgage_rate_spread(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    mortgage_rate = values["mortgage_rate"]
    bank_bill_rate = values["bank_bill_rate"]
    carried_bank_bill = _carry_forward_to_periods(bank_bill_rate, sorted(mortgage_rate))
    return [
        (period, _round(mortgage_rate[period] - carried_bank_bill[period]))
        for period in sorted(mortgage_rate, key=_period_sort_key)
        if period in carried_bank_bill
    ]


def _compute_real_mortgage_rate(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    mortgage_rate = values["mortgage_rate"]
    inflation = values["inflation"]
    dates = sorted(set(mortgage_rate) & set(inflation), key=_period_sort_key)
    return [(period, _round(mortgage_rate[period] - inflation[period])) for period in dates]


def _compute_credit_to_gdp(values: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    total_credit = values["total_credit"]
    nominal_gdp = values["nominal_gdp"]
    carried_credit = _carry_forward_to_periods(total_credit, sorted(nominal_gdp))
    results: list[tuple[str, float]] = []
    for period in sorted(nominal_gdp, key=_period_sort_key):
        gdp_value = nominal_gdp[period]
        credit_value = carried_credit.get(period)
        if credit_value is None or gdp_value in (None, 0):
            continue
        results.append((period, _round(100 * credit_value / gdp_value)))
    return results


def _compute_household_spending_growth(
    values: dict[str, dict[str, float]],
) -> list[tuple[str, float]]:
    household_spending = values["household_spending"]
    results: list[tuple[str, float]] = []
    for period in sorted(household_spending, key=_period_sort_key):
        lag_period = shift_quarter(period, -4)
        lag_value = household_spending.get(lag_period)
        if lag_value in (None, 0):
            continue
        results.append((period, _round(100 * (household_spending[period] / lag_value - 1))))
    return results


def _carry_forward_to_periods(
    source_values: dict[str, float],
    target_periods: list[str],
) -> dict[str, float]:
    source_items = sorted(source_values.items(), key=lambda item: _period_end_date(item[0]))
    carried: dict[str, float] = {}
    source_index = 0
    latest_value: float | None = None
    for period in sorted(target_periods, key=_period_sort_key):
        target_end = _period_end_date(period)
        while (
            source_index < len(source_items)
            and _period_end_date(source_items[source_index][0]) <= target_end
        ):
            latest_value = source_items[source_index][1]
            source_index += 1
        if latest_value is not None:
            carried[period] = latest_value
    return carried


DERIVED_CONCEPTS: dict[str, DerivedSpec] = {
    "yield_curve_slope": DerivedSpec(
        concept="yield_curve_slope",
        label="Yield curve slope",
        description="Ten-year Australian government bond yield less three-year yield.",
        frequency="Daily",
        unit="percentage points",
        formula="government_bond_yield_10y - government_bond_yield_3y",
        alignment_method="period_intersection",
        operands=(
            OperandSpec("long_yield", "government_bond_yield_10y"),
            OperandSpec("short_yield", "government_bond_yield_3y"),
        ),
        compute=_compute_yield_curve_slope,
    ),
    "real_cash_rate": DerivedSpec(
        concept="real_cash_rate",
        label="Real cash rate",
        description=(
            "RBA cash-rate target less complete monthly CPI year-ended inflation. "
            "This is an ex-post real rate (the nominal rate less realised year-ended "
            "CPI inflation), not the ex-ante Fisher rate (less expected inflation)."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="cash_rate_target - monthly_inflation",
        alignment_method="locf",
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
        alignment_method="period_intersection",
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
        alignment_method="year_ended_lag",
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
        alignment_method="period_intersection",
        operands=(
            OperandSpec("real_gdp", "real_gdp"),
            OperandSpec("population", "population"),
        ),
        compute=_compute_gdp_per_capita,
    ),
    "mortgage_rate_spread": DerivedSpec(
        concept="mortgage_rate_spread",
        label="Mortgage rate spread",
        description=(
            "Owner-occupier variable mortgage rate less the carried-forward bank bill rate."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="mortgage_rate - bank_bill_rate",
        alignment_method="locf",
        operands=(
            OperandSpec("mortgage_rate", "mortgage_rate"),
            OperandSpec("bank_bill_rate", "bank_bill_rate"),
        ),
        compute=_compute_mortgage_rate_spread,
    ),
    "real_mortgage_rate": DerivedSpec(
        concept="real_mortgage_rate",
        label="Real mortgage rate",
        description=(
            "Owner-occupier variable mortgage rate less complete monthly CPI inflation. "
            "This is an ex-post real rate (the nominal rate less realised year-ended "
            "CPI inflation), not the ex-ante Fisher rate (less expected inflation)."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="mortgage_rate - monthly_inflation",
        alignment_method="period_intersection",
        operands=(
            OperandSpec("mortgage_rate", "mortgage_rate"),
            OperandSpec("inflation", "monthly_inflation"),
        ),
        compute=_compute_real_mortgage_rate,
    ),
    "credit_to_gdp": DerivedSpec(
        concept="credit_to_gdp",
        label="Credit-to-GDP ratio",
        description="Total credit as a percentage of quarterly nominal GDP.",
        frequency="Quarterly",
        unit="percent",
        formula="100 * total_credit / nominal_gdp",
        alignment_method="locf",
        operands=(
            OperandSpec("total_credit", "total_credit"),
            OperandSpec("nominal_gdp", "nominal_gdp"),
        ),
        compute=_compute_credit_to_gdp,
    ),
    "household_spending_growth": DerivedSpec(
        concept="household_spending_growth",
        label="Household spending growth",
        description=("Year-ended growth in quarterly chain-volume household spending."),
        frequency="Quarterly",
        unit="percent year-ended",
        formula="100 * (household_spending_t / household_spending_t-4 - 1)",
        alignment_method="year_ended_lag",
        operands=(OperandSpec("household_spending", "quarterly_household_spending_volume"),),
        compute=_compute_household_spending_growth,
    ),
    "real_10y_bond_yield": DerivedSpec(
        concept="real_10y_bond_yield",
        label="Real 10-year bond yield",
        description=(
            "Ten-year Australian government bond yield less complete monthly CPI "
            "year-ended inflation. This is an ex-post real rate (the nominal rate "
            "less realised year-ended CPI inflation), not the ex-ante Fisher rate "
            "(less expected inflation)."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="government_bond_yield_10y - monthly_inflation",
        alignment_method="locf",
        operands=(
            OperandSpec("bond_yield", "government_bond_yield_10y"),
            OperandSpec("inflation", "monthly_inflation"),
        ),
        compute=_compute_real_10y_bond_yield,
    ),
    "real_bank_bill_rate": DerivedSpec(
        concept="real_bank_bill_rate",
        label="Real bank bill rate",
        description=(
            "Three-month bank bill swap rate less complete monthly CPI year-ended inflation. "
            "This is an ex-post real rate (the nominal rate less realised year-ended "
            "CPI inflation), not the ex-ante Fisher rate (less expected inflation)."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="bank_bill_rate - monthly_inflation",
        alignment_method="locf",
        operands=(
            OperandSpec("bank_bill_rate", "bank_bill_rate"),
            OperandSpec("inflation", "monthly_inflation"),
        ),
        compute=_compute_real_bank_bill_rate,
    ),
    "real_business_lending_rate": DerivedSpec(
        concept="real_business_lending_rate",
        label="Real business lending rate",
        description=(
            "Small-business indicator lending rate less complete monthly CPI year-ended inflation. "
            "This is an ex-post real rate (the nominal rate less realised year-ended "
            "CPI inflation), not the ex-ante Fisher rate (less expected inflation)."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="business_lending_rate - monthly_inflation",
        alignment_method="exact_month",
        operands=(
            OperandSpec("lending_rate", "business_lending_rate"),
            OperandSpec("inflation", "monthly_inflation"),
        ),
        compute=_compute_real_business_lending_rate,
    ),
    "broad_money_growth": DerivedSpec(
        concept="broad_money_growth",
        label="Broad money growth",
        description="Year-ended growth in broad money derived from RBA broad-money levels.",
        frequency="Monthly",
        unit="percent year-ended",
        formula="100 * (broad_money_t / broad_money_t-12 - 1)",
        alignment_method="year_ended_lag",
        operands=(OperandSpec("broad_money", "broad_money"),),
        compute=_compute_broad_money_growth,
    ),
    "employment_growth": DerivedSpec(
        concept="employment_growth",
        label="Employment growth",
        description="Year-ended growth in total employment derived from ABS Labour Force levels.",
        frequency="Monthly",
        unit="percent year-ended",
        formula="100 * (employment_t / employment_t-12 - 1)",
        alignment_method="year_ended_lag",
        operands=(OperandSpec("employment", "employment"),),
        compute=_compute_employment_growth,
    ),
    "misery_index": DerivedSpec(
        concept="misery_index",
        label="Misery index",
        description=(
            "Unemployment rate plus complete monthly CPI year-ended inflation (Okun misery index)."
        ),
        frequency="Monthly",
        unit="percentage points",
        formula="unemployment_rate + monthly_inflation",
        alignment_method="period_intersection",
        operands=(
            OperandSpec("unemployment_rate", "unemployment_rate"),
            OperandSpec("inflation", "monthly_inflation"),
        ),
        compute=_compute_misery_index,
    ),
    "terms_of_trade": DerivedSpec(
        concept="terms_of_trade",
        label="Terms of trade",
        description=(
            "All-groups export price index relative to the all-groups import price "
            "index, expressed as an index (×100)."
        ),
        frequency="Quarterly",
        unit="index",
        formula="100 * export_price_index / import_price_index",
        alignment_method="period_intersection",
        operands=(
            OperandSpec("export_prices", "export_price_index"),
            OperandSpec("import_prices", "import_price_index"),
        ),
        compute=_compute_terms_of_trade,
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
    elif concept == "broad_money_growth" and operand_name == "broad_money" and normalised_start:
        normalised_start = shift_month(normalised_start, -12)
    elif concept == "employment_growth" and operand_name == "employment" and normalised_start:
        normalised_start = shift_month(normalised_start, -12)
    elif concept == "real_wage_growth" and operand_name == "cpi_index" and normalised_start:
        normalised_start = shift_quarter(normalised_start, -4)
    elif (
        concept == "household_spending_growth"
        and operand_name == "household_spending"
        and normalised_start
    ):
        normalised_start = shift_quarter(normalised_start, -4)
    elif concept == "real_cash_rate" and operand_name == "cash_rate":
        normalised_start = None
    elif concept == "real_10y_bond_yield" and operand_name == "bond_yield":
        normalised_start = None
    elif concept == "real_bank_bill_rate" and operand_name == "bank_bill_rate":
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
                "alignment_method": spec.alignment_method,
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


def _round(value: float) -> float:
    return round(value, 10)

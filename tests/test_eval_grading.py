from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.grading import GroundTruth, grade, normalize_period  # noqa: E402

TRUTH = GroundTruth(value=4.35, period="2026-Q1", unit="per cent")


def test_normalize_period_canonical_forms() -> None:
    assert normalize_period("2026-Q1") == "2026-Q1"
    assert normalize_period("Q1 2026") == "2026-Q1"
    assert normalize_period("March quarter 2026") == "2026-Q1"
    assert normalize_period("2026-05") == "2026-05"
    assert normalize_period("May 2026") == "2026-05"
    assert normalize_period("2026-05-05") == "2026-05-05"
    assert normalize_period("5 May 2026") == "2026-05-05"
    assert normalize_period("2026") == "2026"
    assert normalize_period("sometime recently") is None


def test_grade_correct_within_tolerance_and_fresh() -> None:
    verdict = grade(
        {"value": 4.36, "unit": "per cent", "period": "Q1 2026", "not_found": False},
        TRUTH,
        tolerance=0.05,
    )
    assert verdict.outcome == "correct"
    assert verdict.value_ok is True
    assert verdict.fresh is True
    assert verdict.unit_flag is False


def test_grade_tolerance_boundary_is_inclusive() -> None:
    verdict = grade(
        {"value": 4.40, "unit": "per cent", "period": "2026-Q1", "not_found": False},
        TRUTH,
        tolerance=0.05,
    )
    assert verdict.outcome == "correct"


def test_grade_wrong_value() -> None:
    verdict = grade(
        {"value": 3.0, "unit": "per cent", "period": "2026-Q1", "not_found": False},
        TRUTH,
        tolerance=0.05,
    )
    assert verdict.outcome == "incorrect"
    assert verdict.fresh is True  # freshness independent of value


def test_grade_stale_period() -> None:
    verdict = grade(
        {"value": 4.35, "unit": "per cent", "period": "2025-Q4", "not_found": False},
        TRUTH,
        tolerance=0.05,
    )
    assert verdict.outcome == "correct"
    assert verdict.fresh is False


def test_grade_abstain_and_no_answer() -> None:
    abstain = grade({"value": 0, "unit": "", "period": "", "not_found": True}, TRUTH, 0.05)
    assert abstain.outcome == "abstain"
    none_at_all = grade(None, TRUTH, 0.05)
    assert none_at_all.outcome == "no_answer"


def test_unit_mismatch_flags_but_does_not_fail() -> None:
    verdict = grade(
        {"value": 4.35, "unit": "basis points", "period": "2026-Q1", "not_found": False},
        TRUTH,
        tolerance=0.05,
    )
    assert verdict.outcome == "correct"
    assert verdict.unit_flag is True


def test_percent_unit_aliases_do_not_flag() -> None:
    for alias in ("%", "percent", "Per cent", "pct"):
        verdict = grade(
            {"value": 4.35, "unit": alias, "period": "2026-Q1", "not_found": False},
            TRUTH,
            tolerance=0.05,
        )
        assert verdict.unit_flag is False, alias


def test_composed_abs_dollar_unit_aliases_do_not_flag() -> None:
    # After the ABS parser folds UNIT_MULT into `unit` (e.g. "Australian
    # Dollars, millions"), that live-resolved ground-truth unit must still
    # normalize alongside submitted answers phrased as "AUD millions" /
    # "$ millions" per the eval manifest's own unit wording.
    millions_truth = GroundTruth(
        value=736601.0, period="2026-Q1", unit="Australian Dollars, millions"
    )
    for alias in ("AUD millions", "$ millions", "millions of dollars", "aud millions"):
        verdict = grade(
            {"value": 736601.0, "unit": alias, "period": "2026-Q1", "not_found": False},
            millions_truth,
            tolerance=1.0,
        )
        assert verdict.unit_flag is False, alias

    thousands_truth = GroundTruth(
        value=1111.1, period="2026-Q1", unit="Australian Dollars, thousands"
    )
    for alias in ("AUD thousands", "thousands of dollars", "aud thousands"):
        verdict = grade(
            {"value": 1111.1, "unit": alias, "period": "2026-Q1", "not_found": False},
            thousands_truth,
            tolerance=1.0,
        )
        assert verdict.unit_flag is False, alias

    count_truth = GroundTruth(value=329.5, period="2026-Q1", unit="Number, thousands")
    for alias in ("thousands", "Number, thousands"):
        verdict = grade(
            {"value": 329.5, "unit": alias, "period": "2026-Q1", "not_found": False},
            count_truth,
            tolerance=1.0,
        )
        assert verdict.unit_flag is False, alias


def test_grade_missing_value_key() -> None:
    verdict = grade({"unit": "per cent", "period": "2026-Q1", "not_found": False}, TRUTH, 0.05)
    assert verdict.outcome == "no_answer"


def test_grade_none_value() -> None:
    verdict = grade({"value": None, "unit": "", "period": "", "not_found": False}, TRUTH, 0.05)
    assert verdict.outcome == "no_answer"


def test_grade_non_numeric_value() -> None:
    verdict = grade({"value": "unknown", "unit": "", "period": "", "not_found": False}, TRUTH, 0.05)
    assert verdict.outcome == "no_answer"

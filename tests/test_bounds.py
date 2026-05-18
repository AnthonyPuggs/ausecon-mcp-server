from types import SimpleNamespace

import pytest

from ausecon_mcp.bounds import NormalisedSemanticBounds, normalise_semantic_bounds
from ausecon_mcp.errors import AuseconValidationError


def _resolved(
    *,
    source: str,
    frequency: str | None = None,
    abs_key: str | None = None,
    entry: dict | None = None,
    dataset_id: str = "TEST",
) -> SimpleNamespace:
    return SimpleNamespace(
        source=source,
        frequency=frequency,
        abs_key=abs_key,
        entry=entry or {},
        dataset_id=dataset_id,
    )


@pytest.mark.parametrize(
    ("start", "end", "expected_start", "expected_end"),
    [
        ("2024", "2024", "2024-01-01", "2024-12-31"),
        ("2024-Q1", "2024-Q2", "2024-01-01", "2024-06-30"),
        ("2024-S1", "2024-S2", "2024-01-01", "2024-12-31"),
        ("2024-02", "2024-02", "2024-02-01", "2024-02-29"),
        ("2024-02-15", "2024-02-20", "2024-02-15", "2024-02-20"),
    ],
)
def test_normalise_semantic_bounds_converts_rba_bounds_to_iso_dates(
    start: str,
    end: str,
    expected_start: str,
    expected_end: str,
) -> None:
    result = normalise_semantic_bounds(
        _resolved(source="rba"),
        start=start,
        end=end,
    )

    assert result == NormalisedSemanticBounds(
        start=expected_start,
        end=expected_end,
        requested_start=start,
        requested_end=end,
    )


@pytest.mark.parametrize(
    ("frequency", "start", "end", "expected_start", "expected_end"),
    [
        ("A", "2024-Q2", "2024-12-31", "2024", "2024"),
        ("Q", "2024-02-01", "2024-S2", "2024-Q1", "2024-Q4"),
        ("M", "2024-Q2", "2024-Q2", "2024-04", "2024-06"),
        ("S", "2024-Q2", "2024-12-31", "2024-S1", "2024-S2"),
    ],
)
def test_normalise_semantic_bounds_converts_abs_bounds_to_requested_frequency(
    frequency: str,
    start: str,
    end: str,
    expected_start: str,
    expected_end: str,
) -> None:
    result = normalise_semantic_bounds(
        _resolved(source="abs", frequency=frequency),
        start=start,
        end=end,
    )

    assert result == NormalisedSemanticBounds(
        start=expected_start,
        end=expected_end,
        requested_start=start,
        requested_end=end,
    )


def test_normalise_semantic_bounds_infers_abs_frequency_from_sdmx_key() -> None:
    result = normalise_semantic_bounds(
        _resolved(source="abs", abs_key="1.10001.10.50.M"),
        start="2024-Q1",
        end="2024-Q2",
    )

    assert result.start == "2024-01"
    assert result.end == "2024-06"


def test_normalise_semantic_bounds_infers_abs_frequency_from_single_entry_frequency() -> None:
    result = normalise_semantic_bounds(
        _resolved(source="abs", entry={"frequencies": ["Q"]}),
        start="2024-S1",
        end="2024-S2",
    )

    assert result.start == "2024-Q1"
    assert result.end == "2024-Q4"


def test_normalise_semantic_bounds_rejects_ambiguous_abs_frequency() -> None:
    with pytest.raises(AuseconValidationError, match="Could not infer"):
        normalise_semantic_bounds(
            _resolved(source="abs", entry={"frequencies": ["M", "Q"]}),
            start="2024",
            end="2024",
        )


def test_normalise_semantic_bounds_rejects_unsupported_abs_frequency() -> None:
    with pytest.raises(AuseconValidationError, match="Unsupported ABS frequency"):
        normalise_semantic_bounds(
            _resolved(source="abs", frequency="D"),
            start="2024-01-01",
            end="2024-01-31",
        )


@pytest.mark.parametrize("value", ["today", "2024/01/01", "2024-q1", "2024-13"])
def test_normalise_semantic_bounds_rejects_invalid_bound_formats(value: str) -> None:
    with pytest.raises(AuseconValidationError, match="semantic date bound"):
        normalise_semantic_bounds(
            _resolved(source="rba"),
            start=value,
            end=None,
        )

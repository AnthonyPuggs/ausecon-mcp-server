from copy import deepcopy

from ausecon_mcp.filters import filter_payload


def _sample_payload() -> dict:
    return {
        "metadata": {"source": "rba", "dataset_id": "g1"},
        "series": [
            {"series_id": "A", "label": "Series A", "dimensions": {}},
            {"series_id": "B", "label": "Series B", "dimensions": {}},
        ],
        "observations": [
            {"date": "2024-01-01", "series_id": "A", "value": 1.0, "dimensions": {}},
            {"date": "2024-02-01", "series_id": "B", "value": 2.0, "dimensions": {}},
            {"date": "2024-03-01", "series_id": "A", "value": 3.0, "dimensions": {}},
        ],
    }


def test_filter_payload_truncates_latest_observations_per_series_and_prunes_series() -> None:
    payload = filter_payload(deepcopy(_sample_payload()), last_n=2)

    assert payload["metadata"]["truncated"] is False
    assert [item["date"] for item in payload["observations"]] == [
        "2024-01-01",
        "2024-02-01",
        "2024-03-01",
    ]
    assert {item["series_id"] for item in payload["series"]} == {"A", "B"}


def test_filter_payload_last_n_applies_per_series_not_globally() -> None:
    payload = filter_payload(deepcopy(_sample_payload()), last_n=1)

    assert payload["metadata"]["truncated"] is True
    assert payload["observations"] == [
        {"date": "2024-02-01", "series_id": "B", "value": 2.0, "dimensions": {}},
        {"date": "2024-03-01", "series_id": "A", "value": 3.0, "dimensions": {}},
    ]
    assert {item["series_id"] for item in payload["series"]} == {"A", "B"}


def test_filter_payload_filters_by_series_ids_and_date_range() -> None:
    payload = filter_payload(
        deepcopy(_sample_payload()),
        series_ids=["A"],
        start_date="2024-02-01",
        end_date="2024-03-31",
    )

    assert payload["metadata"]["truncated"] is False
    assert payload["observations"] == [
        {"date": "2024-03-01", "series_id": "A", "value": 3.0, "dimensions": {}}
    ]
    assert payload["series"] == [{"series_id": "A", "label": "Series A", "dimensions": {}}]


def test_filter_payload_leaves_metadata_untruncated_when_last_n_does_not_bind() -> None:
    payload = filter_payload(deepcopy(_sample_payload()), last_n=5)

    assert payload["metadata"]["truncated"] is False
    assert len(payload["observations"]) == 3


def _shuffled_payload() -> dict:
    # Mirrors live ABS SDMX behaviour: CSV rows arrive in arbitrary, non-chronological order.
    return {
        "metadata": {"source": "abs", "dataset_id": "CPI"},
        "series": [
            {"series_id": "A", "label": "Series A", "dimensions": {}},
            {"series_id": "B", "label": "Series B", "dimensions": {}},
        ],
        "observations": [
            {"date": "2025-Q1", "series_id": "A", "value": 97.7, "dimensions": {}},
            {"date": "2026-Q1", "series_id": "A", "value": 101.7, "dimensions": {}},
            {"date": "2025-Q4", "series_id": "A", "value": 100.3, "dimensions": {}},
            {"date": "1986-Q3", "series_id": "A", "value": 30.0, "dimensions": {}},
            {"date": "2025-Q3", "series_id": "B", "value": 99.7, "dimensions": {}},
            {"date": "1986-Q2", "series_id": "B", "value": 29.2, "dimensions": {}},
            {"date": "2025-Q2", "series_id": "B", "value": 98.4, "dimensions": {}},
        ],
    }


def test_filter_payload_last_n_returns_true_latest_per_series_when_unordered() -> None:
    payload = filter_payload(deepcopy(_shuffled_payload()), last_n=2)

    assert payload["metadata"]["truncated"] is True
    assert payload["metadata"]["observations_dropped"] == 3
    assert [(item["date"], item["series_id"]) for item in payload["observations"]] == [
        ("2025-Q2", "B"),
        ("2025-Q3", "B"),
        ("2025-Q4", "A"),
        ("2026-Q1", "A"),
    ]


def test_filter_payload_output_is_chronological_for_shuffled_input() -> None:
    payload = filter_payload(deepcopy(_shuffled_payload()))

    assert [item["date"] for item in payload["observations"]] == [
        "1986-Q2",
        "1986-Q3",
        "2025-Q1",
        "2025-Q2",
        "2025-Q3",
        "2025-Q4",
        "2026-Q1",
    ]
    assert payload["metadata"]["truncated"] is False
    assert payload["metadata"]["observations_dropped"] == 0


def test_filter_payload_date_bounds_compare_parsed_periods_not_strings() -> None:
    # Lexicographically "2026-Q1" <= "2026-03-31" is false; parsed-period comparison keeps
    # the quarter that overlaps the requested window.
    payload = filter_payload(
        deepcopy(_shuffled_payload()),
        start_date="2025-11-15",
        end_date="2026-03-31",
    )

    assert [item["date"] for item in payload["observations"]] == ["2025-Q4", "2026-Q1"]


def test_filter_payload_handles_semester_periods() -> None:
    payload = {
        "metadata": {"source": "abs", "dataset_id": "X"},
        "series": [{"series_id": "S", "label": "S", "dimensions": {}}],
        "observations": [
            {"date": "2025-S2", "series_id": "S", "value": 2.0, "dimensions": {}},
            {"date": "2024-S2", "series_id": "S", "value": 1.0, "dimensions": {}},
            {"date": "2025-S1", "series_id": "S", "value": 1.5, "dimensions": {}},
        ],
    }
    result = filter_payload(payload, last_n=2)

    assert [item["date"] for item in result["observations"]] == ["2025-S1", "2025-S2"]
    assert result["metadata"]["observations_dropped"] == 1


def test_filter_payload_preserves_source_order_for_unrecognised_period_formats() -> None:
    payload = {
        "metadata": {"source": "abs", "dataset_id": "X"},
        "series": [{"series_id": "S", "label": "S", "dimensions": {}}],
        "observations": [
            {"date": "Jun-2025", "series_id": "S", "value": 2.0, "dimensions": {}},
            {"date": "May-2025", "series_id": "S", "value": 1.0, "dimensions": {}},
        ],
    }
    result = filter_payload(payload)

    assert [item["date"] for item in result["observations"]] == ["Jun-2025", "May-2025"]

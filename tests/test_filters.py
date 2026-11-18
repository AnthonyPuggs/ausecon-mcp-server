from copy import deepcopy

import pytest

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.filters import filter_payload, strip_observation_dimensions


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


def test_strip_observation_dimensions_keeps_series_dimensions() -> None:
    region = {"REGION": {"code": "50", "label": "Australia"}}
    payload = {
        "metadata": {"source": "abs", "dataset_id": "CPI"},
        "series": [{"series_id": "A", "label": "Series A", "dimensions": region}],
        "observations": [
            {"date": "2024-Q1", "series_id": "A", "value": 1.0, "dimensions": dict(region)},
            {"date": "2024-Q2", "series_id": "A", "value": 2.0, "dimensions": dict(region)},
        ],
    }

    result = strip_observation_dimensions(payload)

    assert result is payload
    assert all("dimensions" not in item for item in result["observations"])
    assert result["series"][0]["dimensions"] == region


def test_strip_observation_dimensions_is_idempotent_on_slim_payloads() -> None:
    payload = {
        "metadata": {"source": "rba", "dataset_id": "g1"},
        "series": [{"series_id": "A", "label": "Series A", "dimensions": {}}],
        "observations": [{"date": "2024-01-01", "series_id": "A", "value": 1.0}],
    }

    result = strip_observation_dimensions(strip_observation_dimensions(payload))

    assert result["observations"] == [{"date": "2024-01-01", "series_id": "A", "value": 1.0}]


def _bond_payload() -> dict:
    labels = {"FCMYGBAG2D": "2 year bond", "FCMYGBAG10D": "10 year bond"}
    return {
        "metadata": {"source": "rba", "dataset_id": "f2"},
        "series": [
            {"series_id": series_id, "label": label, "dimensions": {}}
            for series_id, label in labels.items()
        ],
        "observations": [
            {"date": "2026-11-11", "series_id": series_id, "value": 4.8} for series_id in labels
        ],
    }


def test_filter_payload_rejects_series_ids_that_match_nothing() -> None:
    # A guessed ID used to return an empty result, which gave the caller nothing to correct.
    with pytest.raises(AuseconValidationError) as excinfo:
        filter_payload(_bond_payload(), series_ids=["FCMYGBAG2", "FCMYGBAG10"])

    message = str(excinfo.value)
    assert "'FCMYGBAG2'" in message and "'FCMYGBAG10'" in message
    assert "RBA f2" in message
    assert "Did you mean FCMYGBAG2D, FCMYGBAG10D?" in message
    assert "FCMYGBAG2D (2 year bond)" in message
    assert "FCMYGBAG10D (10 year bond)" in message


def test_filter_payload_warns_about_unknown_series_ids_alongside_known_ones() -> None:
    payload = filter_payload(_bond_payload(), series_ids=["FCMYGBAG2D", "FCMYGBAG10"])

    assert [item["series_id"] for item in payload["series"]] == ["FCMYGBAG2D"]
    (warning,) = payload["metadata"]["warnings"]
    assert "'FCMYGBAG10'" in warning
    assert "FCMYGBAG10D" in warning


def test_unknown_series_message_lists_a_bounded_number_of_series() -> None:
    payload = _bond_payload()
    payload["series"] = [
        {"series_id": f"S{i:03d}", "label": f"Series {i}", "dimensions": {}} for i in range(500)
    ]

    with pytest.raises(AuseconValidationError) as excinfo:
        filter_payload(payload, series_ids=["NOPE"])

    message = str(excinfo.value)
    assert "S000 (Series 0)" in message
    assert "S499" not in message
    assert "and 470 more" in message


def test_unknown_series_message_bounds_the_work_for_long_lists_of_unknown_ids() -> None:
    unknown = [f"BOGUS{i:04d}" for i in range(2_000)]

    with pytest.raises(AuseconValidationError) as excinfo:
        filter_payload(_bond_payload(), series_ids=unknown)

    message = str(excinfo.value)
    assert "'BOGUS0009'" in message
    assert "'BOGUS0010'" not in message
    assert "and 1990 more" in message


def _policy_rate_payload() -> dict:
    return {
        "metadata": {"source": "rba", "dataset_id": "a2"},
        "series": [
            {"series_id": "RATE", "label": "Cash rate target", "frequency": "As announced"},
            {"series_id": "FLOW", "label": "Monthly flow", "frequency": "Monthly"},
        ],
        "observations": [
            {"date": "2016-08-03", "series_id": "RATE", "value": 1.5},
            {"date": "2019-06-05", "series_id": "RATE", "value": 1.25},
            {"date": "2019-07-03", "series_id": "RATE", "value": 1.0},
            {"date": "2018-12-01", "series_id": "FLOW", "value": 7.0},
            {"date": "2019-01-01", "series_id": "FLOW", "value": 8.0},
        ],
    }


def test_event_driven_series_keep_the_value_in_effect_at_the_window_start() -> None:
    # "Cash rate since 2019" used to start at the June 2019 cut, hiding the 1.50% in effect
    # from August 2016 until then.
    payload = filter_payload(_policy_rate_payload(), start_date="2019-01-01")

    rate = [o["date"] for o in payload["observations"] if o["series_id"] == "RATE"]
    assert rate == ["2016-08-03", "2019-06-05", "2019-07-03"]
    assert payload["metadata"]["date_window"] == {
        "start": "2019-01-01",
        "end": None,
        "carried_in": ["RATE"],
    }


def test_periodic_series_are_not_carried_into_the_window() -> None:
    payload = filter_payload(_policy_rate_payload(), start_date="2019-01-01")

    flow = [o["date"] for o in payload["observations"] if o["series_id"] == "FLOW"]
    assert flow == ["2019-01-01"]


def test_event_driven_series_with_no_change_inside_the_window_still_have_a_value() -> None:
    # No decision between June 2017 and June 2019: the series used to vanish entirely.
    payload = filter_payload(_policy_rate_payload(), start_date="2017-06-01", end_date="2018-12-31")

    rate = [o for o in payload["observations"] if o["series_id"] == "RATE"]
    assert [(o["date"], o["value"]) for o in rate] == [("2016-08-03", 1.5)]
    assert payload["metadata"]["date_window"]["end"] == "2018-12-31"
    assert "RATE" in {s["series_id"] for s in payload["series"]}


def test_no_carry_in_when_a_change_falls_on_the_window_start() -> None:
    payload = filter_payload(_policy_rate_payload(), start_date="2019-06-05")

    rate = [o["date"] for o in payload["observations"] if o["series_id"] == "RATE"]
    assert rate == ["2019-06-05", "2019-07-03"]
    assert payload["metadata"]["date_window"]["carried_in"] == []


def test_unbounded_requests_get_no_date_window() -> None:
    payload = filter_payload(_policy_rate_payload(), last_n=1)

    assert "date_window" not in payload["metadata"]

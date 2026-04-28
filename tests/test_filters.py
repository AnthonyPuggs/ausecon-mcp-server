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

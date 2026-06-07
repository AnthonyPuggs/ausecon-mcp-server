from __future__ import annotations

from ausecon_mcp.convenience import (
    describe_dataset,
    select_latest_observations,
    select_top_observations,
)


def _payload() -> dict:
    return {
        "metadata": {
            "source": "rba",
            "dataset_id": "g1",
            "server_version": "test",
            "truncated": False,
        },
        "series": [
            {"series_id": "a", "label": "A", "dimensions": {}},
            {"series_id": "b", "label": "B", "dimensions": {}},
            {"series_id": "c", "label": "C", "dimensions": {}},
        ],
        "observations": [
            {"date": "2024-01-01", "series_id": "a", "value": 1.0, "dimensions": {}},
            {"date": "2024-01-02", "series_id": "b", "value": None, "dimensions": {}},
            {"date": "2024-01-03", "series_id": "c", "value": 3.5, "dimensions": {}},
            {"date": "2024-01-04", "series_id": "a", "value": 2.0, "dimensions": {}},
        ],
    }


def test_select_top_observations_keeps_highest_numeric_rows_and_matching_series() -> None:
    result = select_top_observations(_payload(), n=2, direction="highest")

    assert [(row["series_id"], row["value"]) for row in result["observations"]] == [
        ("c", 3.5),
        ("a", 2.0),
    ]
    assert {row["series_id"] for row in result["series"]} == {"a", "c"}
    assert result["metadata"]["selection"] == {
        "type": "top_n",
        "n": 2,
        "direction": "highest",
        "numeric_observation_count": 3,
        "returned_observation_count": 2,
        "dropped_non_numeric_count": 1,
    }


def test_select_top_observations_keeps_lowest_numeric_rows() -> None:
    result = select_top_observations(_payload(), n=2, direction="lowest")

    assert [(row["series_id"], row["value"]) for row in result["observations"]] == [
        ("a", 1.0),
        ("a", 2.0),
    ]


def test_select_latest_observations_records_selection_provenance() -> None:
    result = select_latest_observations(_payload(), count=2)

    assert result["metadata"]["selection"] == {
        "type": "latest",
        "n": 2,
        "series_count": 3,
        "returned_observation_count": 4,
    }


def test_describe_dataset_exposes_source_controls_convenience_calls_and_governance() -> None:
    result = describe_dataset(
        "apra",
        "APRA_GENERAL_INSURANCE_PERFORMANCE",
        table_id="database",
    )

    assert result["source_controls"]["identifier_field"] == "publication_id"
    assert result["source_controls"]["identifier"] == "APRA_GENERAL_INSURANCE_PERFORMANCE"
    assert result["source_controls"]["date_bounds"] == {
        "start": "start_date",
        "end": "end_date",
    }
    assert "series_ids" in result["source_controls"]["supported_filters"]
    assert "key" in result["source_controls"]["unsupported_arguments"]
    assert result["convenience_calls"]["latest"] == {
        "tool": "get_latest_observations",
        "arguments": {
            "source": "apra",
            "identifier": "APRA_GENERAL_INSURANCE_PERFORMANCE",
            "table_id": "database",
            "count": 1,
        },
    }
    assert result["governance"]["accepts_arbitrary_urls"] is False
    assert result["governance"]["audit_last_audited"] == "2026-05-18"
    assert result["governance"]["seed_checked_at"]
    assert result["governance"]["governance_status"] in {"ok", "stale"}

    variant = result["variants"][0]
    assert variant["recommended_call"]["tool"] == "get_apra_data"
    assert variant["convenience_calls"]["latest"]["tool"] == "get_latest_observations"
    assert variant["convenience_calls"]["latest"]["arguments"]["series_ids"] == (
        variant["apra_series_ids"]
    )

from __future__ import annotations

from ausecon_mcp.convenience import select_top_observations


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


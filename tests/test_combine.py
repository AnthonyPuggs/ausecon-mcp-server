from copy import deepcopy

import pytest

from ausecon_mcp.combine import MAX_CONCEPTS, merge_concept_payloads
from ausecon_mcp.errors import AuseconValidationError


def _semantic(concept: str, source: str, dataset_id: str, start: str) -> dict:
    return {
        "concept": concept,
        "variant": None,
        "geography": None,
        "frequency": None,
        "requested_bounds": {"start": "2019", "end": None},
        "resolved_bounds": {"start": start, "end": None},
        "target": {
            "source": source,
            "dataset_id": dataset_id,
            "upstream_id": dataset_id,
            "abs_key": None,
            "rba_series_ids": None,
            "apra_table_id": None,
            "apra_series_ids": None,
        },
    }


def abs_unemployment() -> dict:
    return {
        "metadata": {
            "chart_note": "shown",
            "source": "abs",
            "dataset_id": "LF",
            "frequency": "Monthly",
            "title": "Labour Force",
            "retrieval_url": "https://data.api.abs.gov.au/rest/data/LF/M13.3.1599.20.AUS.M",
            "retrieved_at": "2026-11-19T01:00:00Z",
            "server_version": "1.20.1",
            "truncated": False,
            "observations_dropped": 0,
            "semantic": _semantic("unemployment_rate", "abs", "LF", "2019-01"),
            "warnings": ["w1"],
        },
        "series": [
            {"series_id": "U", "label": "Unemployment rate", "unit": "Percent", "dimensions": {}}
        ],
        "observations": [
            {"date": "2019-02", "series_id": "U", "value": 5.0},
            {"date": "2019-01", "series_id": "U", "value": 5.1},
        ],
    }


def rba_cash_rate() -> dict:
    return {
        "metadata": {
            "source": "rba",
            "dataset_id": "a2",
            "title": "A2 RESERVE BANK OF AUSTRALIA",
            "publication_date": "03-Nov-2026",
            "retrieval_url": "https://www.rba.gov.au/statistics/tables/csv/a2-data.csv",
            "retrieved_at": "2026-11-19T00:30:00Z",
            "server_version": "1.20.1",
            "truncated": True,
            "observations_dropped": 3,
            "stale": True,
            "semantic": _semantic("cash_rate_target", "rba", "a2", "2019-01-01"),
            "date_window": {"start": "2019-01-01", "end": None, "carried_in": ["R"]},
        },
        "series": [
            {
                "series_id": "R",
                "label": "New Cash Rate Target",
                "unit": "Per cent",
                "dimensions": {},
            }
        ],
        "observations": [
            {"date": "2016-08-03", "series_id": "R", "value": 1.5},
            {"date": "2019-06-05", "series_id": "R", "value": 1.25},
        ],
    }


def merged() -> dict:
    return merge_concept_payloads(
        [("unemployment_rate", abs_unemployment()), ("cash_rate_target", rba_cash_rate())]
    )


def test_concept_limit_matches_the_chart_series_limit() -> None:
    assert MAX_CONCEPTS == 8


def test_merge_marks_the_result_as_multiple_sources() -> None:
    metadata = merged()["metadata"]

    assert metadata["source"] == "multiple"
    assert metadata["dataset_id"] == "LF+a2"
    assert metadata["title"] == "unemployment_rate, cash_rate_target"
    assert metadata["server_version"] == "1.20.1"


def test_merge_keeps_each_concepts_metadata_in_components() -> None:
    components = merged()["metadata"]["components"]

    assert [c["series_ids"] for c in components] == [["U"], ["R"]]
    assert components[1]["metadata"]["date_window"] == rba_cash_rate()["metadata"]["date_window"]
    assert (
        components[0]["metadata"]["retrieval_url"]
        == abs_unemployment()["metadata"]["retrieval_url"]
    )
    for component in components:
        assert "chart_note" not in component["metadata"]
        assert component["metadata"]["server_version"] == "1.20.1"


def test_merge_orders_observations_chronologically_across_sources() -> None:
    dates = [o["date"] for o in merged()["observations"]]

    assert dates == ["2016-08-03", "2019-01", "2019-02", "2019-06-05"]


def test_merge_reports_the_oldest_retrieval_and_aggregates_flags() -> None:
    metadata = merged()["metadata"]

    assert metadata["retrieved_at"] == "2026-11-19T00:30:00Z"
    assert metadata["truncated"] is True
    assert metadata["observations_dropped"] == 3
    # A component served from stale cache makes the whole result stale (the view's notice).
    assert metadata["stale"] is True


def test_merge_prefixes_component_warnings() -> None:
    assert merged()["metadata"]["warnings"] == ["unemployment_rate: w1"]


def test_merge_drops_single_source_fields_from_the_top_level() -> None:
    metadata = merged()["metadata"]

    for field in ("semantic", "retrieval_url", "publication_date", "date_window", "frequency"):
        assert field not in metadata, field
    assert "chart_note" not in metadata


def test_merge_keeps_a_frequency_every_component_shares() -> None:
    other = abs_unemployment()
    other["metadata"]["dataset_id"] = "LF_UNDER"
    other["series"][0]["series_id"] = "UU"
    for observation in other["observations"]:
        observation["series_id"] = "UU"

    result = merge_concept_payloads([("a", abs_unemployment()), ("b", other)])

    assert result["metadata"]["frequency"] == "Monthly"


def test_merge_keeps_one_copy_of_a_series_shared_within_a_dataset() -> None:
    result = merge_concept_payloads([("a", abs_unemployment()), ("b", abs_unemployment())])

    assert [s["series_id"] for s in result["series"]] == ["U"]
    assert [o["date"] for o in result["observations"]] == ["2019-01", "2019-02"]


def test_merge_rejects_a_series_id_shared_across_datasets() -> None:
    retail = abs_unemployment()
    retail["metadata"]["dataset_id"] = "RT"

    with pytest.raises(AuseconValidationError, match="U"):
        merge_concept_payloads([("a", abs_unemployment()), ("b", retail)])


def test_merge_does_not_mutate_its_inputs() -> None:
    parts = [("unemployment_rate", abs_unemployment()), ("cash_rate_target", rba_cash_rate())]
    before = deepcopy(parts)

    merge_concept_payloads(parts)

    assert parts == before

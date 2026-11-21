from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastmcp import Client
from jsonschema import Draft202012Validator

from ausecon_mcp.response_limits import (
    MAX_RESPONSE_OBSERVATIONS,
    MAX_RESPONSE_SERIES,
    limit_response,
)
from ausecon_mcp.server import AuseconService, build_server


def _payload(series_count: int, per_series: int, *, dropped: int = 0) -> dict:
    series = [
        {"series_id": f"S{index}", "label": f"Series {index}"} for index in range(series_count)
    ]
    observations = [
        {"date": f"{2000 + year}-01-01", "series_id": f"S{index}", "value": float(year)}
        for year in range(per_series)
        for index in range(series_count)
    ]
    return {
        "metadata": {
            "source": "rba",
            "dataset_id": "x",
            "truncated": dropped > 0,
            "observations_dropped": dropped,
        },
        "series": series,
        "observations": observations,
    }


def test_response_within_limits_is_unchanged() -> None:
    payload = _payload(3, 4)
    before = {**payload["metadata"]}

    result = limit_response(payload, max_series=5, max_observations=100)

    assert len(result["observations"]) == 12
    assert result["metadata"] == before


def test_series_over_the_limit_keep_the_first_ones_in_source_order() -> None:
    result = limit_response(_payload(10, 2), max_series=4, max_observations=100)

    assert [item["series_id"] for item in result["series"]] == ["S0", "S1", "S2", "S3"]
    assert {item["series_id"] for item in result["observations"]} == {"S0", "S1", "S2", "S3"}
    assert result["metadata"]["series_dropped"] == 6
    assert any("series_ids" in warning for warning in result["metadata"]["warnings"])


def test_observations_over_the_limit_keep_the_most_recent_of_each_series() -> None:
    result = limit_response(_payload(2, 10, dropped=3), max_series=5, max_observations=8)

    observations = result["observations"]
    assert len(observations) == 8
    assert {item["date"] for item in observations} == {
        "2006-01-01",
        "2007-01-01",
        "2008-01-01",
        "2009-01-01",
    }
    assert [item["date"] for item in observations] == sorted(item["date"] for item in observations)
    assert result["metadata"]["truncated"] is True
    assert result["metadata"]["observations_dropped"] == 3 + 12
    assert any("start_date" in warning for warning in result["metadata"]["warnings"])


def test_every_kept_series_keeps_at_least_one_observation() -> None:
    result = limit_response(_payload(6, 3), max_series=10, max_observations=4)

    assert {item["series_id"] for item in result["observations"]} == {
        f"S{index}" for index in range(6)
    }
    assert len(result["observations"]) == 6


class _HugeRBAProvider:
    """A daily table far over the observation limit: 4 series x 3,000 days."""

    def list_tables(self, category=None, include_discontinued=False) -> list[dict]:
        return []

    async def get_table(self, table_id: str, **kwargs) -> dict:
        start = date(2010, 1, 1)
        days = [(start + timedelta(days=offset)).isoformat() for offset in range(3000)]
        return {
            "metadata": {
                "source": "rba",
                "dataset_id": table_id,
                "server_version": "test",
                "truncated": False,
                "observations_dropped": 0,
            },
            "series": [
                {"series_id": f"S{index}", "label": f"S{index}", "dimensions": {}}
                for index in range(4)
            ],
            "observations": [
                {"date": day, "series_id": f"S{index}", "value": 1.0}
                for day in days
                for index in range(4)
            ],
        }


class _WideAPRAProvider:
    """One publication with far more series than one response holds."""

    async def get_data(self, publication_id: str, **kwargs) -> dict:
        return {
            "metadata": {
                "source": "apra",
                "dataset_id": publication_id,
                "server_version": "test",
                "truncated": False,
                "observations_dropped": 0,
            },
            "series": [
                {"series_id": f"S{index}", "label": f"S{index}", "dimensions": {}}
                for index in range(500)
            ],
            "observations": [
                {"date": "2026-09-30", "series_id": f"S{index}", "value": 1.0}
                for index in range(500)
            ],
        }


def _schema_validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "response.schema.json"
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))


async def test_rba_table_tool_bounds_an_unfiltered_daily_table() -> None:
    service = AuseconService(rba_provider=_HugeRBAProvider())

    async with Client(build_server(service)) as client:
        result = await client.call_tool("get_rba_table", {"table_id": "f16"})

    payload = result.structured_content
    assert len(payload["observations"]) <= MAX_RESPONSE_OBSERVATIONS
    assert (
        payload["observations"][-1]["date"] == (date(2010, 1, 1) + timedelta(days=2999)).isoformat()
    )
    assert payload["metadata"]["truncated"] is True
    _schema_validator().validate(payload)


async def test_apra_tool_bounds_a_publication_with_thousands_of_series() -> None:
    service = AuseconService(apra_provider=_WideAPRAProvider())

    async with Client(build_server(service)) as client:
        result = await client.call_tool("get_apra_data", {"publication_id": "ADI_MONTHLY"})

    payload = result.structured_content
    assert len(payload["series"]) == MAX_RESPONSE_SERIES
    assert payload["metadata"]["series_dropped"] == 500 - MAX_RESPONSE_SERIES
    _schema_validator().validate(payload)


async def test_service_calls_used_by_derived_indicators_stay_complete() -> None:
    service = AuseconService(rba_provider=_HugeRBAProvider())

    payload = await service.get_rba_table("f16")

    assert len(payload["observations"]) == 12_000


async def test_caller_errors_reach_the_client_and_log_one_line_without_a_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    async with Client(build_server(AuseconService())) as client:
        result = await client.call_tool(
            "get_economic_series", {"concept": "not_a_concept"}, raise_on_error=False
        )

    assert result.is_error
    message = result.content[0].text
    assert message.startswith("Unknown concept 'not_a_concept'.")
    logged = [
        record
        for record in caplog.records
        if record.getMessage() == "tool.caller_error"
        and "not_a_concept" in getattr(record, "error", "")
    ]
    assert logged, "expected the caller error to be logged"
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.levelno <= logging.WARNING for record in caplog.records)


async def test_latest_observations_tool_bounds_a_publication_with_thousands_of_series() -> None:
    service = AuseconService(apra_provider=_WideAPRAProvider())

    async with Client(build_server(service)) as client:
        result = await client.call_tool(
            "get_latest_observations", {"source": "apra", "identifier": "ADI_MONTHLY"}
        )

    payload = result.structured_content
    assert len(payload["series"]) == MAX_RESPONSE_SERIES
    assert payload["metadata"]["series_dropped"] == 500 - MAX_RESPONSE_SERIES

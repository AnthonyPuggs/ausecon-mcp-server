"""Caller-side tool errors reach the client as a plain message that names a next step."""

from __future__ import annotations

import logging

import pytest
import respx
from fastmcp import Client
from httpx import Response

from ausecon_mcp.server import AuseconService, build_server


async def _error_text(tool: str, arguments: dict) -> str:
    async with Client(build_server(AuseconService())) as client:
        result = await client.call_tool(tool, arguments, raise_on_error=False)
    assert result.is_error, f"expected {tool} to fail"
    return result.content[0].text


@pytest.mark.parametrize(
    ("tool", "arguments", "expected"),
    [
        (
            "get_latest_observations",
            {"source": "abs", "identifier": "CPI", "series_ids": ["x"]},
            "series_ids is not supported for source 'abs'.",
        ),
        (
            "get_latest_observations",
            {"source": "rba", "identifier": "g1", "key": "1.2"},
            "key is only supported for source 'abs', not 'rba'.",
        ),
        (
            "get_top_observations",
            {"source": "rba", "identifier": "g1", "start_period": "2020"},
            "start_period is not supported for source 'rba'.",
        ),
        (
            "describe_dataset",
            {"source": "rba", "identifier": "g1", "include_structure": True},
            "include_structure is only supported for ABS descriptions.",
        ),
    ],
)
async def test_parameter_mismatch_errors_are_plain_messages_without_a_traceback(
    tool: str,
    arguments: dict,
    expected: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    message = await _error_text(tool, arguments)

    assert message == expected
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.levelno <= logging.WARNING for record in caplog.records)


async def test_unknown_dataset_description_names_the_discovery_tools() -> None:
    message = await _error_text("describe_dataset", {"source": "rba", "identifier": "zzz"})

    assert message.startswith("Unknown RBA dataset 'zzz'.")
    assert "search_datasets" in message
    assert "list_catalogue" in message


async def test_unknown_apra_publication_names_the_discovery_tool() -> None:
    message = await _error_text("get_apra_data", {"publication_id": "NOPE"})

    assert message.startswith("Unknown APRA publication 'NOPE'.")
    assert "list_catalogue" in message


async def test_unknown_abs_structure_names_the_discovery_tools(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/datastructure/ABS/NOT_A_FLOW").mock(
            return_value=Response(404, text="No Results Found")
        )
        message = await _error_text("get_abs_dataset_structure", {"dataflow_id": "NOT_A_FLOW"})

    assert "NOT_A_FLOW" in message
    assert "search_datasets" in message
    assert "list_catalogue" in message
    assert all(record.exc_info is None for record in caplog.records)

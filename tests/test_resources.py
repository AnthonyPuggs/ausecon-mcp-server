import json

import pytest
from fastmcp import Client

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.catalogue.resolver import CURATED_SHORTCUTS
from ausecon_mcp.server import build_server


async def _read_json(client: Client, uri: str):
    result = await client.read_resource(uri)
    assert result, f"no resource content returned for {uri}"
    return json.loads(result[0].text)


async def test_catalogue_index_lists_every_curated_entry() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = {str(resource.uri) for resource in resources}
        assert "ausecon://catalogue" in uris

        payload = await _read_json(client, "ausecon://catalogue")

    ids = {entry["id"] for entry in payload}
    expected = set(ABS_CATALOGUE.keys()) | set(RBA_CATALOGUE.keys())
    assert ids == expected
    assert all({"id", "source", "name"} <= entry.keys() for entry in payload)


async def test_abs_resource_returns_full_catalogue_entry() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        payload = await _read_json(client, "ausecon://abs/CPI")

    assert payload == ABS_CATALOGUE["CPI"]
    assert payload["variants"] == [
        {
            "name": "headline",
            "aliases": ["headline cpi", "all groups"],
            "abs_key": "1.10001.10.50.Q",
        }
    ]


async def test_rba_resource_returns_full_catalogue_entry() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        payload = await _read_json(client, "ausecon://rba/g1")

    assert payload == RBA_CATALOGUE["g1"]


async def test_concepts_resource_lists_every_curated_shortcut() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        payload = await _read_json(client, "ausecon://concepts")

    concepts = {row["concept"] for row in payload}
    assert concepts == set(CURATED_SHORTCUTS)
    for row in payload:
        expected = CURATED_SHORTCUTS[row["concept"]]
        assert row["source"] == expected["source"]
        assert row["dataset_id"] == expected["dataset_id"]
        assert row["variant"] == expected.get("variant")
        assert row["recommended_call"]["tool"] == "get_economic_series"
        assert row["recommended_call"]["arguments"] == {"concept": row["concept"]}


async def test_abs_resource_exposes_new_building_approvals_entry() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        payload = await _read_json(client, "ausecon://abs/BUILDING_APPROVALS")

    assert payload == ABS_CATALOGUE["BUILDING_APPROVALS"]
    assert payload["variants"] == [
        {
            "name": "headline_approvals",
            "aliases": ["dwelling approvals", "residential approvals"],
            "abs_key": "1.1.9.TOT.100.10.AUS.M",
        }
    ]


async def test_abs_resource_raises_for_unknown_dataflow_id() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        with pytest.raises(Exception, match="Unknown ABS dataflow_id"):
            await client.read_resource("ausecon://abs/NOT_A_REAL_ID")


async def test_rba_resource_raises_for_unknown_table_id() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        with pytest.raises(Exception, match="Unknown RBA table_id"):
            await client.read_resource("ausecon://rba/zzzz")

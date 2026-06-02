from __future__ import annotations

import pytest

from ausecon_mcp.catalogue.resolver import resolve
from ausecon_mcp.identity import normalise_geography


def test_normalise_geography_accepts_common_australian_aliases() -> None:
    assert normalise_geography("Australia") == "aus"
    assert normalise_geography("Commonwealth of Australia") == "aus"
    assert normalise_geography("Queensland") == "qld"
    assert normalise_geography("New South Wales") == "nsw"
    assert normalise_geography("Northern Territory") == "nt"


@pytest.mark.asyncio
async def test_semantic_resolver_normalises_geography_aliases_before_validation() -> None:
    async def fetcher(dataflow_id: str) -> dict:
        return {
            "id": dataflow_id,
            "dimensions": [
                {"id": "MEASURE", "position": 1, "values": [{"code": "1"}]},
                {"id": "INDEX", "position": 2, "values": [{"code": "10001"}]},
                {"id": "TSEST", "position": 3, "values": [{"code": "10"}]},
                {"id": "REGION", "position": 4, "values": [{"code": "50"}]},
                {"id": "FREQ", "position": 5, "values": [{"code": "Q"}]},
            ],
        }

    resolved = await resolve(
        "headline_cpi",
        geography="Australia",
        frequency="Q",
        abs_structure_fetcher=fetcher,
    )

    assert resolved.geography == "aus"
    assert resolved.abs_key == "1.10001.10.50.Q"


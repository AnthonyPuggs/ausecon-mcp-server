"""Source identifiers are case-insensitive.

Each catalogue stores its keys in one case (RBA lowercase, ABS and APRA uppercase) and
upstream URLs are built from them, so "F2", "cpi" or "adi_monthly" used to fail with a
404 or "unknown dataset" even though people write them that way all the time.
"""

import json

import pytest
from fastmcp import Client

from ausecon_mcp.catalogue.resolver import canonical_source_identifier
from ausecon_mcp.server import AuseconService, build_server

_PAYLOAD = {
    "metadata": {"source": "rba", "dataset_id": "f2"},
    "series": [{"series_id": "FCMYGBAG2", "label": "2 year", "dimensions": {}}],
    "observations": [{"date": "2026-11-11", "series_id": "FCMYGBAG2", "value": 4.81}],
}


class _RecordingRBAProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def get_table(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)
        return json.loads(json.dumps(_PAYLOAD))


class _RecordingAPRAProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def get_data(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)
        payload = json.loads(json.dumps(_PAYLOAD))
        payload["metadata"] = {"source": "apra", "dataset_id": kwargs["publication_id"]}
        return payload


@pytest.mark.parametrize(
    ("source", "given", "expected"),
    [
        ("rba", "F2", "f2"),
        ("rba", "f2", "f2"),
        ("rba", "F17", "f17"),
        # Not in the catalogue: RBA CSV filenames are always lowercase.
        ("rba", "Z99", "z99"),
        ("abs", "cpi", "CPI"),
        ("abs", "Ana_Agg", "ANA_AGG"),
        ("abs", "CPI", "CPI"),
        # Not in the catalogue: passed through; the ABS API itself is case-insensitive.
        ("abs", "Some_New_Flow", "Some_New_Flow"),
        ("apra", "adi_monthly", "ADI_MONTHLY"),
        ("apra", "ADI_MONTHLY", "ADI_MONTHLY"),
        ("apra", "not_curated", "not_curated"),
    ],
)
def test_canonical_source_identifier(source: str, given: str, expected: str) -> None:
    assert canonical_source_identifier(source, given) == expected


async def test_get_rba_table_accepts_uppercase_table_ids() -> None:
    rba = _RecordingRBAProvider()
    service = AuseconService(rba_provider=rba)

    payload = await service.get_rba_table("F2")

    assert rba.calls[-1]["table_id"] == "f2"
    assert rba.calls[-1]["csv_path"] == "f2-data.csv"
    assert payload["metadata"]["dataset_id"] == "f2"


async def test_rba_convenience_tools_accept_uppercase_identifiers() -> None:
    rba = _RecordingRBAProvider()
    service = AuseconService(rba_provider=rba)

    await service.get_latest_observations(source="rba", identifier="F2")
    await service.get_top_observations(source="rba", identifier="F2", n=1)

    assert [call["table_id"] for call in rba.calls] == ["f2", "f2"]


async def test_get_apra_data_accepts_lowercase_publication_ids() -> None:
    apra = _RecordingAPRAProvider()
    service = AuseconService(apra_provider=apra)

    await service.get_apra_data("adi_monthly", last_n=1)

    assert apra.calls[-1]["publication_id"] == "ADI_MONTHLY"


@pytest.mark.parametrize(
    ("source", "given", "canonical"),
    [("rba", "F2", "f2"), ("abs", "cpi", "CPI"), ("apra", "adi_monthly", "ADI_MONTHLY")],
)
async def test_describe_dataset_is_case_insensitive(
    source: str, given: str, canonical: str
) -> None:
    service = AuseconService()

    description = await service.describe_dataset(source=source, identifier=given)
    expected = await service.describe_dataset(source=source, identifier=canonical)

    assert description == expected


@pytest.mark.parametrize(
    ("uri", "canonical_uri"),
    [
        ("ausecon://rba/F2", "ausecon://rba/f2"),
        ("ausecon://abs/cpi", "ausecon://abs/CPI"),
        ("ausecon://apra/adi_monthly", "ausecon://apra/ADI_MONTHLY"),
    ],
)
async def test_catalogue_resources_are_case_insensitive(uri: str, canonical_uri: str) -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        given = await client.read_resource(uri)
        canonical = await client.read_resource(canonical_uri)

    assert json.loads(given[0].text) == json.loads(canonical[0].text)

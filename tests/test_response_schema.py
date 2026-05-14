import json
from pathlib import Path

import pytest
import respx
from httpx import Response
from jsonschema import Draft202012Validator

from ausecon_mcp.derived import derive_series
from ausecon_mcp.providers.abs import ABSProvider
from ausecon_mcp.providers.rba import RBAProvider
from ausecon_mcp.server import AuseconService

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "response.schema.json"
PAYLOAD_EXAMPLES = ROOT / "examples" / "payloads"
FIXTURES = Path(__file__).parent / "fixtures"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _assert_valid(payload: dict) -> None:
    _validator().validate(payload)


@pytest.mark.asyncio
async def test_response_schema_validates_abs_provider_payload() -> None:
    provider = ABSProvider()
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text=csv_payload)
        )

        payload = await provider.get_data("CPI", updated_after="2024-01-01T00:00:00Z", last_n=2)

    _assert_valid(payload)


@pytest.mark.asyncio
async def test_response_schema_validates_rba_provider_payload() -> None:
    provider = RBAProvider()
    csv_payload = (FIXTURES / "rba_g1_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            return_value=Response(200, text=csv_payload)
        )

        payload = await provider.get_table("g1", last_n=2)

    _assert_valid(payload)


def test_response_schema_validates_apra_provider_payload() -> None:
    payload = {
        "metadata": {
            "source": "apra",
            "dataset_id": "ADI_PROPERTY_EXPOSURES",
            "frequency": "Quarterly",
            "title": "Quarterly authorised deposit-taking institution property exposures",
            "retrieval_url": (
                "https://www.apra.gov.au/sites/default/files/example-property-exposures.xlsx"
            ),
            "retrieved_at": "2026-05-14T00:00:00Z",
            "server_version": "test",
            "truncated": False,
        },
        "series": [
            {
                "series_id": (
                    "ADI_PROPERTY_EXPOSURES:tab_1b:credit_outstanding:"
                    "total_credit_outstanding"
                ),
                "label": "Credit outstanding: Total credit outstanding",
                "unit": "$ million",
                "frequency": "Quarterly",
                "dimensions": {
                    "table": {
                        "code": "tab_1b",
                        "label": "Residential property exposures",
                    }
                },
                "source_key": "Total credit outstanding",
                "unit_multiplier": None,
                "decimals": None,
                "base_period": None,
            }
        ],
        "observations": [
            {
                "date": "2024-03-31",
                "series_id": (
                    "ADI_PROPERTY_EXPOSURES:tab_1b:credit_outstanding:"
                    "total_credit_outstanding"
                ),
                "value": 1000.0,
                "dimensions": {
                    "table": {
                        "code": "tab_1b",
                        "label": "Residential property exposures",
                    }
                },
                "status": None,
                "comment": None,
            }
        ],
    }

    _assert_valid(payload)


@pytest.mark.asyncio
async def test_response_schema_validates_semantic_payload() -> None:
    service = AuseconService(abs_provider=ABSProvider(), rba_provider=RBAProvider())
    csv_payload = (FIXTURES / "rba_a2_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.rba.gov.au/statistics/tables/csv/a2-data.csv").mock(
            return_value=Response(200, text=csv_payload)
        )

        payload = await service.get_economic_series("cash_rate_target", last_n=4)

    assert payload["metadata"]["semantic"]["concept"] == "cash_rate_target"
    assert payload["metadata"]["semantic"]["target"]["dataset_id"] == "a2"
    _assert_valid(payload)


@pytest.mark.asyncio
async def test_response_schema_validates_derived_payload() -> None:
    payload = derive_series(
        "yield_curve_slope",
        {
            "long_yield": {
                "metadata": {
                    "source": "rba",
                    "dataset_id": "f17",
                    "server_version": "test",
                    "truncated": False,
                    "semantic": {
                        "concept": "government_bond_yield_10y",
                        "variant": "ags_10y",
                        "geography": None,
                        "frequency": "Daily",
                        "requested_bounds": {"start": None, "end": None},
                        "resolved_bounds": {"start": None, "end": None},
                        "target": {
                            "source": "rba",
                            "dataset_id": "f17",
                            "upstream_id": "f17",
                            "abs_key": None,
                            "rba_series_ids": ["FZCY1000D"],
                        },
                    },
                },
                "series": [
                    {
                        "series_id": "FZCY1000D",
                        "label": "10-year yield",
                        "unit": "Percent per annum",
                        "frequency": "Daily",
                        "dimensions": {},
                        "source_key": "FZCY1000D",
                        "unit_multiplier": None,
                        "decimals": None,
                        "base_period": None,
                    }
                ],
                "observations": [
                    {"date": "2024-01-01", "series_id": "FZCY1000D", "value": 4.2, "dimensions": {}}
                ],
            },
            "short_yield": {
                "metadata": {
                    "source": "rba",
                    "dataset_id": "f17",
                    "server_version": "test",
                    "truncated": False,
                    "semantic": {
                        "concept": "government_bond_yield_3y",
                        "variant": "ags_3y",
                        "geography": None,
                        "frequency": "Daily",
                        "requested_bounds": {"start": None, "end": None},
                        "resolved_bounds": {"start": None, "end": None},
                        "target": {
                            "source": "rba",
                            "dataset_id": "f17",
                            "upstream_id": "f17",
                            "abs_key": None,
                            "rba_series_ids": ["FZCY3D"],
                        },
                    },
                },
                "series": [
                    {
                        "series_id": "FZCY3D",
                        "label": "3-year yield",
                        "unit": "Percent per annum",
                        "frequency": "Daily",
                        "dimensions": {},
                        "source_key": "FZCY3D",
                        "unit_multiplier": None,
                        "decimals": None,
                        "base_period": None,
                    }
                ],
                "observations": [
                    {"date": "2024-01-01", "series_id": "FZCY3D", "value": 3.7, "dimensions": {}}
                ],
            },
        },
        requested_start=None,
        requested_end=None,
        last_n=1,
        server_version="test",
    )

    assert payload["metadata"]["source"] == "derived"
    assert payload["metadata"]["dataset_id"] == "yield_curve_slope"
    assert payload["metadata"]["derived"]["concept"] == "yield_curve_slope"
    _assert_valid(payload)


def test_checked_in_payload_examples_validate_against_schema() -> None:
    validator = _validator()
    paths = sorted(PAYLOAD_EXAMPLES.glob("*.json"))

    assert paths, "expected checked-in example payloads under examples/payloads/"
    for path in paths:
        validator.validate(json.loads(path.read_text(encoding="utf-8")))


def test_response_schema_documents_contract_and_abs_metadata_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    series_properties = schema["$defs"]["series_descriptor"]["properties"]
    observation_properties = schema["$defs"]["observation"]["properties"]

    assert "$id" in schema
    assert "server_version" in schema["$defs"]["metadata"]["required"]
    assert "truncated" in schema["$defs"]["metadata"]["required"]
    assert schema["properties"]["metadata"]["description"]
    assert series_properties["unit_multiplier"]["type"] == ["integer", "null"]
    assert series_properties["decimals"]["type"] == ["integer", "null"]
    assert series_properties["base_period"]["type"] == ["string", "null"]
    assert observation_properties["date"]["oneOf"]
    assert observation_properties["comment"]["type"] == ["string", "null"]
    assert "semantic" in schema["$defs"]["metadata"]["properties"]
    assert "derived" in schema["$defs"]["metadata"]["properties"]
    assert "derived" in schema["$defs"]["metadata"]["properties"]["source"]["enum"]
    assert "apra" in schema["$defs"]["metadata"]["properties"]["source"]["enum"]

from __future__ import annotations

import pytest

from ausecon_mcp.providers.abs import ABSProvider
from ausecon_mcp.server import AuseconService

pytestmark = pytest.mark.asyncio


async def test_abs_cpi_structure_has_expected_shape() -> None:
    provider = ABSProvider()

    structure = await provider.get_dataset_structure("CPI")

    assert structure["id"] == "CPI"
    assert len(structure["dimensions"]) >= 5
    dim_ids = {dim["id"] for dim in structure["dimensions"]}
    assert {"MEASURE", "REGION"} <= dim_ids


async def test_abs_cpi_data_returns_observations() -> None:
    provider = ABSProvider()

    result = await provider.get_data(
        "CPI",
        key="1.10001.10.50.Q",
        start_period="2024-Q1",
    )

    assert result["observations"], "expected at least one observation"
    obs = result["observations"][0]
    for field in ("date", "series_id", "value"):
        assert field in obs, f"observation missing field {field!r}"
    assert result["metadata"]["source"] == "abs"
    assert isinstance(result["metadata"]["server_version"], str)


async def test_abs_building_approvals_entry_returns_observations() -> None:
    service = AuseconService()

    result = await service.get_abs_data(
        "BUILDING_APPROVALS",
        key="1.1.9.TOT.100.10.AUS.M",
        last_n=3,
    )

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "BA_GCCSA"
    assert result["observations"], "expected observations for BUILDING_APPROVALS"

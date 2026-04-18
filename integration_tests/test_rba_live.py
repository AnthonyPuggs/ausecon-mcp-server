from __future__ import annotations

import pytest

from ausecon_mcp.providers.rba import RBAProvider

pytestmark = pytest.mark.asyncio


async def test_rba_g1_returns_observations() -> None:
    provider = RBAProvider()

    result = await provider.get_table("g1", start_date="2024-01-01")

    assert result["observations"], "expected at least one observation"
    obs = result["observations"][0]
    for field in ("date", "series_id", "value"):
        assert field in obs, f"observation missing field {field!r}"
    assert any(isinstance(item.get("value"), float) for item in result["observations"])


async def test_rba_a2_event_table_returns_shape() -> None:
    provider = RBAProvider()

    result = await provider.get_table("a2")

    assert result["series"], "expected at least one series row"
    assert result["observations"], "expected at least one observation"
    obs = result["observations"][0]
    assert "date" in obs
    assert "series_id" in obs

from pathlib import Path

import pytest
import respx
from httpx import Response

from ausecon_mcp.providers.rba import RBAProvider

FIXTURES = Path(__file__).parent / "fixtures"


def test_rba_provider_lists_tables_by_category() -> None:
    provider = RBAProvider()

    results = provider.list_tables(category="inflation")

    assert [item["id"] for item in results] == ["g1"]


@pytest.mark.asyncio
async def test_rba_provider_fetches_table_and_uses_cache() -> None:
    provider = RBAProvider()
    csv_payload = (FIXTURES / "rba_g1_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            return_value=Response(200, text=csv_payload)
        )

        first = await provider.get_table("g1", last_n=2)
        second = await provider.get_table("g1", last_n=2)

    assert route.call_count == 1
    assert first == second
    assert len(first["observations"]) == 2
    assert first["metadata"]["truncated"] is True
    assert first["metadata"]["retrieval_url"].endswith("/g1-data.csv")

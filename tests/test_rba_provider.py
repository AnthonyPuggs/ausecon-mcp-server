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


@pytest.mark.asyncio
async def test_rba_provider_reuses_cached_raw_payload_across_client_side_filters() -> None:
    provider = RBAProvider()
    csv_payload = (FIXTURES / "rba_g1_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            return_value=Response(200, text=csv_payload)
        )

        first = await provider.get_table("g1", series_ids=["GCPIAGYP"], last_n=1)
        second = await provider.get_table("g1", series_ids=["GCPIAGSAQP", "GCPIAGYP"], last_n=2)

    assert route.call_count == 1
    assert len(first["observations"]) == 1
    assert len(second["observations"]) == 2


@pytest.mark.asyncio
async def test_rba_provider_normalises_series_id_order_for_equivalent_filters() -> None:
    provider = RBAProvider()
    csv_payload = (FIXTURES / "rba_g1_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            return_value=Response(200, text=csv_payload)
        )

        first = await provider.get_table("g1", series_ids=["GCPIAGYP", "GCPIAGSAQP"])
        second = await provider.get_table("g1", series_ids=["GCPIAGSAQP", "GCPIAGYP"])

    assert route.call_count == 1
    assert first == second


@pytest.mark.asyncio
async def test_rba_provider_retries_transient_failures() -> None:
    provider = RBAProvider()
    csv_payload = (FIXTURES / "rba_g1_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            side_effect=[
                Response(500, text="server unavailable"),
                Response(502, text="bad gateway"),
                Response(200, text=csv_payload),
            ]
        )

        result = await provider.get_table("g1")

    assert route.call_count == 3
    assert result["metadata"]["dataset_id"] == "g1"


@pytest.mark.asyncio
async def test_rba_provider_wraps_parse_failures() -> None:
    provider = RBAProvider()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            return_value=Response(200, text="bad-payload")
        )

        with pytest.raises(Exception, match="Failed to parse RBA table payload for 'g1'"):
            await provider.get_table("g1")


@pytest.mark.asyncio
async def test_rba_provider_does_not_retry_client_errors() -> None:
    provider = RBAProvider()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://www.rba.gov.au/statistics/tables/csv/g1-data.csv").mock(
            return_value=Response(404, text="not found")
        )

        with pytest.raises(Exception, match="404"):
            await provider.get_table("g1")

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_rba_provider_supports_a2_event_tables() -> None:
    provider = RBAProvider()
    csv_payload = (FIXTURES / "rba_a2_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.rba.gov.au/statistics/tables/csv/a2-data.csv").mock(
            return_value=Response(200, text=csv_payload)
        )

        result = await provider.get_table("a2")

    assert result["metadata"]["dataset_id"] == "a2"
    assert result["observations"][0]["date"] == "1990-01-23"
    assert result["observations"][0]["raw_value"] == "-0.50 to -1.00"
    assert result["observations"][-1]["series_id"] == "ARBAMPNORR"
    assert result["observations"][-1]["value"] == 7.25

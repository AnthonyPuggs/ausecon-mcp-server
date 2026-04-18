from pathlib import Path

import pytest
import respx
from httpx import ConnectTimeout, Response

from ausecon_mcp.providers.abs import ABSProvider

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_abs_provider_fetches_structure() -> None:
    provider = ABSProvider()
    structure_xml = (FIXTURES / "abs_cpi_structure.xml").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://data.api.abs.gov.au/rest/datastructure/ABS/CPI").mock(
            return_value=Response(200, text=structure_xml)
        )

        result = await provider.get_dataset_structure("CPI")

    assert route.called
    assert result["id"] == "CPI"
    assert result["dimensions"][0]["id"] == "MEASURE"


@pytest.mark.asyncio
async def test_abs_provider_fetches_filtered_data_and_uses_cache() -> None:
    provider = ABSProvider()
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text=csv_payload)
        )

        first = await provider.get_data(
            "CPI",
            start_period="2024-01",
            end_period="2024-06",
            last_n=2,
        )
        second = await provider.get_data(
            "CPI",
            start_period="2024-01",
            end_period="2024-06",
            last_n=2,
        )

    assert route.call_count == 1
    assert first == second
    assert first["metadata"]["retrieval_url"].endswith(
        "startPeriod=2024-01&endPeriod=2024-06&format=csvfile"
    )
    assert len(first["observations"]) == 2
    assert first["metadata"]["truncated"] is True


@pytest.mark.asyncio
async def test_abs_provider_reuses_cached_raw_payload_across_last_n_filters() -> None:
    provider = ABSProvider()
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text=csv_payload)
        )

        first = await provider.get_data(
            "CPI",
            start_period="2024-01",
            end_period="2024-06",
            last_n=1,
        )
        second = await provider.get_data(
            "CPI",
            start_period="2024-01",
            end_period="2024-06",
            last_n=2,
        )

    assert route.call_count == 1
    assert len(first["observations"]) == 1
    assert len(second["observations"]) == 2


@pytest.mark.asyncio
async def test_abs_provider_retries_transient_failures() -> None:
    provider = ABSProvider()
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            side_effect=[
                ConnectTimeout("temporary timeout"),
                Response(500, text="server unavailable"),
                Response(200, text=csv_payload),
            ]
        )

        result = await provider.get_data("CPI")

    assert route.call_count == 3
    assert result["metadata"]["dataset_id"] == "CPI"


@pytest.mark.asyncio
async def test_abs_provider_wraps_structure_parse_failures() -> None:
    provider = ABSProvider()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/datastructure/ABS/CPI").mock(
            return_value=Response(200, text="<not-xml")
        )

        with pytest.raises(Exception, match="Failed to parse ABS structure payload for 'CPI'"):
            await provider.get_dataset_structure("CPI")


@pytest.mark.asyncio
async def test_abs_provider_wraps_data_parse_failures() -> None:
    provider = ABSProvider()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text="not,a,valid,abs,csv")
        )

        with pytest.raises(Exception, match="Failed to parse ABS data payload for 'CPI'"):
            await provider.get_data("CPI")


@pytest.mark.asyncio
async def test_abs_provider_stamps_server_version_in_metadata() -> None:
    provider = ABSProvider()
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text=csv_payload)
        )

        result = await provider.get_data("CPI")

    assert isinstance(result["metadata"]["server_version"], str)
    assert result["metadata"]["server_version"]


@pytest.mark.asyncio
async def test_abs_provider_returns_stale_on_upstream_failure(_isolated_cache_dir) -> None:
    from ausecon_mcp.cache import TTLCache

    cache = TTLCache(ttl_seconds=60)
    provider = ABSProvider(cache=cache)
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text=csv_payload)
        )
        await provider.get_data("CPI")

    import json as _json

    (file,) = _isolated_cache_dir.glob("*.json")
    data = _json.loads(file.read_text())
    data["expires_at"] = 0.0
    file.write_text(_json.dumps(data))

    fresh_cache = TTLCache(ttl_seconds=60)
    fresh_provider = ABSProvider(cache=fresh_cache)

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            side_effect=ConnectTimeout("network down")
        )

        stale = await fresh_provider.get_data("CPI")

    assert stale["metadata"]["stale"] is True
    assert "cached_at" in stale["metadata"]
    assert "expires_at" in stale["metadata"]
    assert stale["observations"]


@pytest.mark.asyncio
async def test_abs_provider_parse_failure_is_not_masked_by_stale(_isolated_cache_dir) -> None:
    from ausecon_mcp.cache import TTLCache

    cache = TTLCache(ttl_seconds=60)
    provider = ABSProvider(cache=cache)
    csv_payload = (FIXTURES / "abs_cpi_sample.csv").read_text()

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text=csv_payload)
        )
        await provider.get_data("CPI")

    import json as _json

    (file,) = _isolated_cache_dir.glob("*.json")
    data = _json.loads(file.read_text())
    data["expires_at"] = 0.0
    file.write_text(_json.dumps(data))

    fresh_cache = TTLCache(ttl_seconds=60)
    fresh_provider = ABSProvider(cache=fresh_cache)

    with respx.mock(assert_all_called=True) as router:
        router.get("https://data.api.abs.gov.au/rest/data/CPI/all").mock(
            return_value=Response(200, text="not,a,valid,abs,csv")
        )

        with pytest.raises(Exception, match="Failed to parse ABS data payload"):
            await fresh_provider.get_data("CPI")


@pytest.mark.asyncio
async def test_abs_provider_sends_identified_user_agent() -> None:
    provider = ABSProvider()
    structure_xml = (FIXTURES / "abs_cpi_structure.xml").read_text()

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://data.api.abs.gov.au/rest/datastructure/ABS/CPI").mock(
            return_value=Response(200, text=structure_xml)
        )

        await provider.get_dataset_structure("CPI")

    ua = route.calls.last.request.headers["user-agent"]
    assert ua.startswith("ausecon-mcp-server/")
    assert "github.com/AnthonyPuggs/ausecon-mcp-server" in ua

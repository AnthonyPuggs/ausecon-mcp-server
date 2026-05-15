from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO

import pytest
import respx
from httpx import ConnectTimeout, Response
from openpyxl import Workbook

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.errors import AuseconParseError
from ausecon_mcp.providers.apra import APRAProvider, resolve_apra_download_url


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Table 1"
    sheet.append(["($million)"])
    sheet.append(["Period", "ABN", "Institution Name", "Total residents assets"])
    sheet.append([datetime(2024, 1, 31), 11111111111, "Example Bank", 100.5])
    sheet.append([datetime(2024, 2, 29), 11111111111, "Example Bank", 110.0])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _catalogue() -> dict:
    return {
        "TEST_PUBLICATION": {
            "id": "TEST_PUBLICATION",
            "name": "Test APRA publication",
            "description": "Selected APRA test data.",
            "category": "banking",
            "frequency": "Monthly",
            "frequencies": ["M"],
            "geographies": ["aus"],
            "tags": ["apra", "adi"],
            "landing_url": "https://www.apra.gov.au/test-statistics",
            "link_patterns": [r"back-series.*xlsx"],
            "tables": {
                "table_1": {
                    "sheet": "Table 1",
                    "layout": "row_records",
                    "title": "Table 1",
                    "unit": "$ million",
                    "frequency": "Monthly",
                    "header_row": 2,
                    "data_start_row": 3,
                    "date_column": 1,
                    "dimension_columns": {"abn": 2, "institution": 3},
                    "series_start_column": 4,
                    "identity_columns": ["abn"],
                }
            },
        }
    }


@pytest.mark.parametrize(
    "href",
    [
        "https://evil.example/apra-back-series.xlsx",
        "//evil.example/apra-back-series.xlsx",
        "http://www.apra.gov.au/sites/default/files/apra-back-series.xlsx",
    ],
)
def test_resolve_apra_download_url_rejects_non_apra_or_non_https_xlsx_links(
    href: str,
) -> None:
    html = f'<a href="{href}">Test back-series March 2026 XLSX</a>'

    with pytest.raises(AuseconParseError, match="trusted APRA HTTPS"):
        resolve_apra_download_url(
            html,
            base_url="https://www.apra.gov.au/test-statistics",
            patterns=[r"back-series.*xlsx"],
        )


@pytest.mark.asyncio
async def test_apra_provider_resolves_landing_page_xlsx_and_uses_cache() -> None:
    provider = APRAProvider(catalogue=_catalogue())
    html = '<a href="/sites/default/files/test.xlsx">Test back-series March 2026 XLSX</a>'

    with respx.mock(assert_all_called=True) as router:
        landing_route = router.get("https://www.apra.gov.au/test-statistics").mock(
            return_value=Response(200, text=html)
        )
        xlsx_route = router.get("https://www.apra.gov.au/sites/default/files/test.xlsx").mock(
            return_value=Response(200, content=_xlsx_bytes())
        )

        first = await provider.get_data("TEST_PUBLICATION", table_id="table_1", last_n=1)
        second = await provider.get_data("TEST_PUBLICATION", table_id="table_1", last_n=1)

    assert landing_route.call_count == 1
    assert xlsx_route.call_count == 1
    assert first == second
    assert first["metadata"]["source"] == "apra"
    assert first["metadata"]["dataset_id"] == "TEST_PUBLICATION"
    assert first["metadata"]["retrieval_url"].endswith("/sites/default/files/test.xlsx")
    assert first["metadata"]["truncated"] is True
    assert first["observations"][0]["date"] == "2024-02-29"


@pytest.mark.asyncio
async def test_apra_provider_filters_series_ids_and_dates_after_cache() -> None:
    provider = APRAProvider(catalogue=_catalogue())
    html = '<a href="/sites/default/files/test.xlsx">Test back-series March 2026 XLSX</a>'
    series_id = "TEST_PUBLICATION:table_1:11111111111:total_residents_assets"

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.apra.gov.au/test-statistics").mock(
            return_value=Response(200, text=html)
        )
        router.get("https://www.apra.gov.au/sites/default/files/test.xlsx").mock(
            return_value=Response(200, content=_xlsx_bytes())
        )

        result = await provider.get_data(
            "TEST_PUBLICATION",
            table_id="table_1",
            series_ids=[series_id],
            start_date="2024-02-01",
        )

    assert [item["date"] for item in result["observations"]] == ["2024-02-29"]
    assert result["series"][0]["series_id"] == series_id


@pytest.mark.asyncio
async def test_apra_provider_returns_stale_payload_on_upstream_failure(_isolated_cache_dir) -> None:
    cache = TTLCache(ttl_seconds=60)
    provider = APRAProvider(cache=cache, catalogue=_catalogue())
    html = '<a href="/sites/default/files/test.xlsx">Test back-series March 2026 XLSX</a>'

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.apra.gov.au/test-statistics").mock(
            return_value=Response(200, text=html)
        )
        router.get("https://www.apra.gov.au/sites/default/files/test.xlsx").mock(
            return_value=Response(200, content=_xlsx_bytes())
        )
        await provider.get_data("TEST_PUBLICATION", table_id="table_1")

    (file,) = _isolated_cache_dir.glob("*.json")
    data = json.loads(file.read_text())
    data["expires_at"] = 0.0
    file.write_text(json.dumps(data))

    fresh_provider = APRAProvider(cache=TTLCache(ttl_seconds=60), catalogue=_catalogue())

    with respx.mock(assert_all_called=True) as router:
        router.get("https://www.apra.gov.au/test-statistics").mock(
            side_effect=ConnectTimeout("network down")
        )

        result = await fresh_provider.get_data("TEST_PUBLICATION", table_id="table_1")

    assert result["metadata"]["stale"] is True
    assert result["observations"]


@pytest.mark.asyncio
async def test_apra_provider_rejects_unknown_publication() -> None:
    provider = APRAProvider(catalogue=_catalogue())

    with pytest.raises(ValueError, match="Unknown APRA publication"):
        await provider.get_data("UNKNOWN")

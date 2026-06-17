from __future__ import annotations

import httpx
import pytest
import respx

from ausecon_mcp.providers._http import build_client

pytestmark = pytest.mark.asyncio


@respx.mock
async def test_build_client_follows_redirects() -> None:
    respx.get("https://example.test/start").mock(
        return_value=httpx.Response(301, headers={"Location": "https://example.test/final"})
    )
    respx.get("https://example.test/final").mock(return_value=httpx.Response(200, text="ok"))

    client = build_client()
    try:
        response = await client.get("https://example.test/start")
    finally:
        await client.aclose()

    assert response.status_code == 200
    assert str(response.url) == "https://example.test/final"
    assert response.text == "ok"

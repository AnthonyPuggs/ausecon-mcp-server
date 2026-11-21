from __future__ import annotations

import gzip

import httpx
import pytest

from ausecon_mcp.errors import (
    AuseconNotFoundError,
    AuseconResponseTooLargeError,
    AuseconValidationError,
)
from ausecon_mcp.providers._retry import get_with_retries
from ausecon_mcp.providers.abs import ABSProvider
from ausecon_mcp.providers.rba import RBAProvider


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://up.test")


async def _chunks(total: int, size: int = 1000):
    sent = 0
    while sent < total:
        step = min(size, total - sent)
        sent += step
        yield b"x" * step


async def test_download_over_the_declared_limit_is_refused() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 5000)

    async with _client(handler) as client:
        with pytest.raises(AuseconResponseTooLargeError, match="ABS response for 'CPI'"):
            await get_with_retries(
                client, "/data", params=None, source="abs", identifier="CPI", max_bytes=4000
            )


async def test_streamed_download_without_a_length_stops_at_the_limit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_chunks(10_000))

    async with _client(handler) as client:
        with pytest.raises(AuseconResponseTooLargeError):
            await get_with_retries(
                client, "/data", params=None, source="rba", identifier="f16", max_bytes=4000
            )


async def test_download_under_the_limit_keeps_body_and_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="a,b\n1,2\n")

    async with _client(handler) as client:
        response = await get_with_retries(
            client,
            "/data",
            params={"format": "csv"},
            source="abs",
            identifier="CPI",
            max_bytes=4000,
        )

    assert response.text == "a,b\n1,2\n"
    assert str(response.request.url) == "https://up.test/data?format=csv"


async def test_compressed_download_is_decoded_once() -> None:
    body = b"a,b\n" + b"1,2\n" * 200

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=gzip.compress(body), headers={"Content-Encoding": "gzip"}
        )

    async with _client(handler) as client:
        response = await get_with_retries(
            client, "/data", params=None, source="abs", identifier="CPI", max_bytes=4000
        )

    assert response.content == body


async def test_compressed_download_counts_its_decoded_size() -> None:
    body = b"x" * 50_000  # compresses to well under the limit

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=gzip.compress(body), headers={"Content-Encoding": "gzip"}
        )

    async with _client(handler) as client:
        with pytest.raises(AuseconResponseTooLargeError):
            await get_with_retries(
                client, "/data", params=None, source="abs", identifier="CPI", max_bytes=4000
            )


async def test_abs_keyless_request_over_the_limit_says_how_to_narrow_it() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 5000)

    async with _client(handler) as client:
        provider = ABSProvider(client=client, max_data_bytes=4000)
        with pytest.raises(AuseconResponseTooLargeError) as caught:
            await provider.get_data("CPI", last_n=1)

    message = str(caught.value)
    assert "key" in message
    assert "get_abs_dataset_structure" in message
    assert "get_latest_observations" in message


async def test_rba_table_over_the_limit_is_refused() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 5000)

    async with _client(handler) as client:
        provider = RBAProvider(client=client, max_table_bytes=4000)
        with pytest.raises(AuseconResponseTooLargeError, match="RBA response for 'f16'"):
            await provider.get_table("f16")


async def test_abs_rejected_key_explains_the_key_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Not enough key values in query, expecting 5 got 2")

    async with _client(handler) as client:
        provider = ABSProvider(client=client)
        with pytest.raises(AuseconValidationError) as caught:
            await provider.get_data("CPI", key="bad.key")

    message = str(caught.value)
    assert "expecting 5 got 2. get_abs_dataset_structure" in message
    assert "'bad.key'" in message
    assert "get_abs_dataset_structure" in message


async def test_rba_unknown_table_points_to_the_table_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="<html>Not found</html>")

    async with _client(handler) as client:
        provider = RBAProvider(client=client)
        with pytest.raises(AuseconNotFoundError) as caught:
            await provider.get_table("nope")

    message = str(caught.value)
    assert "'nope'" in message
    assert "list_rba_tables" in message
    assert "<html>" not in message

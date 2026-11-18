from __future__ import annotations

import asyncio

import httpx
import pytest

import ausecon_mcp.providers._retry as retry_module
from ausecon_mcp.providers._retry import get_with_retries


class _InFlightCounter:
    """Mock upstream that records how many requests it is serving at once."""

    def __init__(self, statuses: dict[str, list[int]] | None = None) -> None:
        self.in_flight = 0
        self.peak = 0
        self.calls: list[str] = []
        self._statuses = statuses or {}

    async def handler(self, request: httpx.Request) -> httpx.Response:
        name = request.url.path.strip("/")
        self.calls.append(name)
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(0.02)
        finally:
            self.in_flight -= 1
        queued = self._statuses.get(name)
        status = queued.pop(0) if queued else 200
        return httpx.Response(status, json={"name": name})


def _client(counter: _InFlightCounter) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(counter.handler), base_url="https://upstream.test"
    )


async def _fetch(client: httpx.AsyncClient, name: str, source: str) -> httpx.Response:
    return await get_with_retries(
        client, f"/{name}", params=None, source=source, identifier=name
    )


async def test_same_source_requests_never_exceed_the_concurrency_limit(monkeypatch) -> None:
    monkeypatch.setenv("AUSECON_UPSTREAM_CONCURRENCY", "2")
    counter = _InFlightCounter()
    async with _client(counter) as client:
        responses = await asyncio.gather(*(_fetch(client, f"r{i}", "abs") for i in range(6)))

    assert [r.status_code for r in responses] == [200] * 6
    assert counter.peak == 2


async def test_each_source_has_its_own_limit(monkeypatch) -> None:
    monkeypatch.setenv("AUSECON_UPSTREAM_CONCURRENCY", "1")
    counter = _InFlightCounter()
    async with _client(counter) as client:
        await asyncio.gather(_fetch(client, "a", "abs"), _fetch(client, "b", "rba"))

    assert counter.peak == 2


async def test_retry_backoff_does_not_hold_a_slot(monkeypatch) -> None:
    monkeypatch.setenv("AUSECON_UPSTREAM_CONCURRENCY", "1")
    monkeypatch.setattr(retry_module, "DEFAULT_BASE_DELAY_SECONDS", 0.1)
    counter = _InFlightCounter(statuses={"flaky": [503]})
    async with _client(counter) as client:
        flaky, steady = await asyncio.gather(
            _fetch(client, "flaky", "abs"), _fetch(client, "steady", "abs")
        )

    assert (flaky.status_code, steady.status_code) == (200, 200)
    # "steady" is served while "flaky" waits out its backoff, not after its retry.
    assert counter.calls == ["flaky", "steady", "flaky"]


@pytest.mark.parametrize("raw", ["0", "-3", "not-a-number"])
async def test_invalid_concurrency_setting_falls_back_to_a_working_limit(
    monkeypatch, raw: str
) -> None:
    monkeypatch.setenv("AUSECON_UPSTREAM_CONCURRENCY", raw)
    counter = _InFlightCounter()
    async with _client(counter) as client:
        responses = await asyncio.gather(*(_fetch(client, f"r{i}", "abs") for i in range(3)))

    assert [r.status_code for r in responses] == [200] * 3
    assert counter.peak >= 1

from __future__ import annotations

import asyncio

import httpx
import pytest

import ausecon_mcp.server as server_module


class _GatedApp:
    """ASGI app whose POST responses wait until the test opens the gate."""

    def __init__(self) -> None:
        self.gate = asyncio.Event()
        self.started = 0
        self.fail = False

    async def __call__(self, scope, receive, send) -> None:
        if scope["method"] == "POST":
            self.started += 1
            await self.gate.wait()
            if self.fail:
                raise RuntimeError("tool blew up")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def _client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://server.test",
    )


async def _wait_until(predicate) -> None:
    for _ in range(200):
        if predicate():
            return
        await asyncio.sleep(0.005)
    raise AssertionError("condition not reached")


async def test_post_beyond_the_limit_is_rejected_while_slots_are_busy() -> None:
    inner = _GatedApp()
    app = server_module.ConcurrencyLimitMiddleware(inner, max_in_flight=2)
    async with _client(app) as client:
        busy = [asyncio.create_task(client.post("/mcp", content=b"{}")) for _ in range(2)]
        await _wait_until(lambda: inner.started == 2)

        rejected = await client.post("/mcp", content=b"{}")

        inner.gate.set()
        finished = await asyncio.gather(*busy)

    assert rejected.status_code == 503
    assert rejected.headers["retry-after"] == "1"
    assert rejected.json()["error"] == "server_busy"
    assert [r.status_code for r in finished] == [200, 200]
    assert inner.started == 2  # the rejected request never reached the app


async def test_slots_are_released_after_requests_finish() -> None:
    inner = _GatedApp()
    inner.gate.set()
    app = server_module.ConcurrencyLimitMiddleware(inner, max_in_flight=1)
    async with _client(app) as client:
        statuses = [(await client.post("/mcp", content=b"{}")).status_code for _ in range(3)]

    assert statuses == [200, 200, 200]


async def test_slot_is_released_when_the_app_raises() -> None:
    inner = _GatedApp()
    inner.fail = True
    inner.gate.set()
    app = server_module.ConcurrencyLimitMiddleware(inner, max_in_flight=1)
    async with _client(app) as client:
        first = await client.post("/mcp", content=b"{}")
        inner.fail = False
        second = await client.post("/mcp", content=b"{}")

    assert first.status_code == 500
    assert second.status_code == 200


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
async def test_non_post_requests_are_not_limited(method: str) -> None:
    inner = _GatedApp()
    app = server_module.ConcurrencyLimitMiddleware(inner, max_in_flight=1)
    async with _client(app) as client:
        busy = asyncio.create_task(client.post("/mcp", content=b"{}"))
        await _wait_until(lambda: inner.started == 1)

        response = await client.request(method, "/healthz")

        inner.gate.set()
        await busy

    assert response.status_code == 200


class _BodyReadingApp:
    """ASGI app that reads the whole request body before responding, as the MCP app does."""

    def __init__(self, received: list[bytes] | None = None) -> None:
        self.received = received if received is not None else []

    async def __call__(self, scope, receive, send) -> None:
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        self.received.append(body)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


class _StalledBody:
    """Request body that sends one chunk, then stalls until released."""

    def __init__(self) -> None:
        self.release = asyncio.Event()

    async def __aiter__(self):
        yield b"{"
        await self.release.wait()
        yield b"}"


async def test_slow_request_body_does_not_hold_a_slot() -> None:
    app = server_module.ConcurrencyLimitMiddleware(_BodyReadingApp(), max_in_flight=1)
    stalled = _StalledBody()
    async with _client(app) as client:
        slow = asyncio.create_task(client.post("/mcp", content=stalled))
        await asyncio.sleep(0.05)  # the slow client is now mid-body

        fast = await client.post("/mcp", content=b"{}")

        stalled.release.set()
        slow_response = await slow

    assert fast.status_code == 200
    assert slow_response.status_code == 200


async def test_request_body_that_never_finishes_times_out_with_408() -> None:
    inner = _GatedApp()
    inner.gate.set()
    app = server_module.ConcurrencyLimitMiddleware(
        inner, max_in_flight=1, body_timeout_seconds=0.05
    )
    stalled = _StalledBody()
    async with _client(app) as client:
        response = await client.post("/mcp", content=stalled)
        stalled.release.set()

    assert response.status_code == 408
    assert inner.started == 0


async def test_chunked_body_over_the_size_cap_is_rejected_with_413() -> None:
    inner = _GatedApp()
    inner.gate.set()
    app = server_module.ConcurrencyLimitMiddleware(inner, max_in_flight=1, max_body_bytes=10)

    async def chunks():  # no content-length header, so only the bytes can be counted
        for _ in range(4):
            yield b"xxxx"

    async with _client(app) as client:
        response = await client.post("/mcp", content=chunks())

    assert response.status_code == 413
    assert inner.started == 0


async def test_app_receives_the_full_buffered_body() -> None:
    received: list[bytes] = []
    echo = _BodyReadingApp(received)

    async def chunks():
        yield b'{"a":'
        yield b"1}"

    app = server_module.ConcurrencyLimitMiddleware(echo, max_in_flight=1)
    async with _client(app) as client:
        response = await client.post("/mcp", content=chunks())

    assert response.status_code == 200
    assert received == [b'{"a":1}']


def test_http_app_limit_comes_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("AUSECON_HTTP_MAX_IN_FLIGHT", "7")

    middleware = server_module.build_http_middleware()

    limiter = next(m for m in middleware if m.cls is server_module.ConcurrencyLimitMiddleware)
    assert limiter.kwargs["max_in_flight"] == 7

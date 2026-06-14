from __future__ import annotations

import asyncio

import pytest

from ausecon_mcp.providers._single_flight import SingleFlight


async def test_single_flight_runs_factory_once_for_concurrent_keys() -> None:
    flight = SingleFlight()
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return calls

    results = await asyncio.gather(
        flight.run("k", factory),
        flight.run("k", factory),
        flight.run("k", factory),
    )

    assert calls == 1
    assert results == [1, 1, 1]


async def test_single_flight_propagates_exceptions_to_all_callers() -> None:
    flight = SingleFlight()

    async def factory():
        await asyncio.sleep(0.01)
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await asyncio.gather(flight.run("k", factory), flight.run("k", factory))


async def test_single_flight_refetches_after_the_first_call_settles() -> None:
    flight = SingleFlight()
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return calls

    assert await flight.run("k", factory) == 1
    # The key is cleared once settled, so a later call runs the factory again.
    assert await flight.run("k", factory) == 2
    assert calls == 2


async def test_single_flight_cancelling_one_caller_does_not_poison_others() -> None:
    flight = SingleFlight()
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return "ok"

    first = asyncio.ensure_future(flight.run("k", factory))
    second = asyncio.ensure_future(flight.run("k", factory))
    await asyncio.sleep(0.01)  # let both register against the same in-flight task

    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first

    # The shared work survives the first caller's cancellation, and the second
    # caller still receives the real result from the single factory run.
    assert await second == "ok"
    assert calls == 1

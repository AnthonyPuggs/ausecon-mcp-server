from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class SingleFlight:
    """Coalesce concurrent calls that share a key into one in-flight execution.

    The first caller for a key starts ``factory`` as a detached task; concurrent
    callers for the same key await that same task. The key is cleared once the
    task settles, so a later (cache-miss) call runs the factory again.

    Callers await the shared task through :func:`asyncio.shield`, so cancelling
    one caller neither cancels the shared work nor poisons the other coalesced
    callers — a cancellation affects only the caller that requested it. Because
    every caller (including the first) awaits the task, its result or exception
    is always retrieved, avoiding asyncio's "exception was never retrieved" noise.
    """

    def __init__(self) -> None:
        self._inflight: dict[str, asyncio.Task[Any]] = {}

    async def run(self, key: str, factory: Callable[[], Awaitable[Any]]) -> Any:
        task = self._inflight.get(key)
        if task is not None:
            return await asyncio.shield(task)

        task = asyncio.ensure_future(factory())
        # Always retrieve the task's outcome, even if every awaiter is cancelled
        # before it settles, so an orphaned failure never logs "exception was
        # never retrieved". (t.exception() raises on a cancelled task, hence the
        # short-circuit on t.cancelled().)
        task.add_done_callback(lambda t: t.cancelled() or t.exception())
        self._inflight[key] = task
        try:
            return await asyncio.shield(task)
        finally:
            self._inflight.pop(key, None)

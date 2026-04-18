from __future__ import annotations

import asyncio
from time import perf_counter

import httpx

from ausecon_mcp.errors import AuseconUpstreamError
from ausecon_mcp.logging import get_logger

_logger = get_logger("providers._retry")


async def get_with_retries(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, str] | list[tuple[str, str]] | None,
    source: str,
    identifier: str,
    attempts: int = 3,
    base_delay_seconds: float = 0.1,
) -> httpx.Response:
    delay = base_delay_seconds
    start = perf_counter()

    for attempt_number in range(1, attempts + 1):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code < 500 or attempt_number == attempts:
                _logger.error(
                    "request.failed",
                    extra={
                        "source": source,
                        "identifier": identifier,
                        "attempts": attempt_number,
                        "status": status_code,
                        "duration_ms": int((perf_counter() - start) * 1000),
                    },
                )
                raise AuseconUpstreamError(
                    f"{source.upper()} request for '{identifier}' failed with HTTP {status_code}."
                ) from exc
            _logger.warning(
                "request.retry",
                extra={
                    "source": source,
                    "identifier": identifier,
                    "attempt": attempt_number,
                    "status": status_code,
                    "delay": delay,
                },
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if attempt_number == attempts:
                _logger.error(
                    "request.failed",
                    extra={
                        "source": source,
                        "identifier": identifier,
                        "attempts": attempt_number,
                        "error_type": type(exc).__name__,
                        "duration_ms": int((perf_counter() - start) * 1000),
                    },
                )
                raise AuseconUpstreamError(
                    f"{source.upper()} request for '{identifier}' failed after "
                    f"{attempts} attempts: {exc}."
                ) from exc
            _logger.warning(
                "request.retry",
                extra={
                    "source": source,
                    "identifier": identifier,
                    "attempt": attempt_number,
                    "error_type": type(exc).__name__,
                    "delay": delay,
                },
            )

        await asyncio.sleep(delay)
        delay *= 2

    raise AssertionError("Retry loop exited unexpectedly.")

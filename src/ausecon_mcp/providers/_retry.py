from __future__ import annotations

import asyncio

import httpx

from ausecon_mcp.errors import AuseconUpstreamError


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

    for attempt_number in range(1, attempts + 1):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code < 500 or attempt_number == attempts:
                raise AuseconUpstreamError(
                    f"{source.upper()} request for '{identifier}' failed with HTTP {status_code}."
                ) from exc
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if attempt_number == attempts:
                raise AuseconUpstreamError(
                    f"{source.upper()} request for '{identifier}' failed after "
                    f"{attempts} attempts: {exc}."
                ) from exc

        await asyncio.sleep(delay)
        delay *= 2

    raise AssertionError("Retry loop exited unexpectedly.")

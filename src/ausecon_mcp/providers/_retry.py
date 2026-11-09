from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

import httpx

from ausecon_mcp.errors import AuseconNotFoundError, AuseconUpstreamError
from ausecon_mcp.logging import get_logger

_logger = get_logger("providers._retry")

_BODY_PREVIEW_BYTES = 2048

# Upstream gateways (notably the ABS SDMX API) return short bursts of 502/503s. Four
# attempts with 0.5s/1s/2s backoff ride those out without stalling a tool call for long.
# Read at call time so tests can zero the delay.
DEFAULT_ATTEMPTS = 4
DEFAULT_BASE_DELAY_SECONDS = 0.5
MAX_RETRY_AFTER_SECONDS = 10.0


def _safe_body(response: httpx.Response) -> str | None:
    try:
        return response.text[:_BODY_PREVIEW_BYTES]
    except Exception:  # noqa: BLE001 - body preview is best-effort diagnostics only
        return None


def _is_retryable_status(status_code: int) -> bool:
    return status_code >= 500 or status_code == 429


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    if seconds < 0:
        return None
    return min(seconds, MAX_RETRY_AFTER_SECONDS)


def stamp_stale_metadata(
    payload: dict[str, Any], stale_meta: dict[str, Any], *, source: str
) -> None:
    """Mark a payload served from expired cache and say why the live request failed."""
    metadata = payload["metadata"]
    metadata["stale"] = True
    metadata["cached_at"] = stale_meta["cached_at"]
    metadata["expires_at"] = stale_meta["expires_at"]
    cached_at = datetime.fromtimestamp(stale_meta["cached_at"], timezone.utc)
    reason = stale_meta.get("error") or f"The live {source.upper()} request failed."
    metadata.setdefault("warnings", []).append(
        f"{reason} Serving cached data retrieved at "
        f"{cached_at.replace(microsecond=0).isoformat().replace('+00:00', 'Z')}; "
        "it may not include the latest release."
    )


async def get_with_retries(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, str] | list[tuple[str, str]] | None,
    source: str,
    identifier: str,
    attempts: int | None = None,
    base_delay_seconds: float | None = None,
) -> httpx.Response:
    if attempts is None:
        attempts = DEFAULT_ATTEMPTS
    delay = DEFAULT_BASE_DELAY_SECONDS if base_delay_seconds is None else base_delay_seconds
    start = perf_counter()

    for attempt_number in range(1, attempts + 1):
        wait = delay
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if not _is_retryable_status(status_code) or attempt_number == attempts:
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
                message = (
                    f"{source.upper()} request for '{identifier}' failed with HTTP {status_code}"
                )
                if _is_retryable_status(status_code):
                    message += (
                        f" after {attempt_number} attempts; the upstream service may be "
                        "temporarily unavailable, so retry shortly."
                    )
                else:
                    message += "."
                if status_code == 404:
                    raise AuseconNotFoundError(
                        message,
                        status_code=status_code,
                        body=_safe_body(exc.response),
                        url=str(exc.response.request.url),
                    ) from exc
                raise AuseconUpstreamError(message, status_code=status_code) from exc
            retry_after = _retry_after_seconds(exc.response)
            if retry_after is not None:
                wait = max(wait, retry_after)
            _logger.warning(
                "request.retry",
                extra={
                    "source": source,
                    "identifier": identifier,
                    "attempt": attempt_number,
                    "status": status_code,
                    "delay": wait,
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
                    "delay": wait,
                },
            )

        await asyncio.sleep(wait)
        delay *= 2

    raise AssertionError("Retry loop exited unexpectedly.")

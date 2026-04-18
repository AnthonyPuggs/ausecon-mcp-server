from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.errors import AuseconParseError, AuseconUpstreamError
from ausecon_mcp.logging import get_logger
from ausecon_mcp.parsers.abs_csv import parse_abs_csv
from ausecon_mcp.parsers.abs_structure import parse_abs_structure
from ausecon_mcp.providers._http import build_client, resolve_version
from ausecon_mcp.providers._retry import get_with_retries

_logger = get_logger("providers.abs")


class ABSProvider:
    BASE_URL = "https://data.api.abs.gov.au/rest"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._client = client or build_client()
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds

    async def get_dataset_structure(self, dataflow_id: str) -> dict[str, Any]:
        cache_key = f"abs-structure:{dataflow_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            _logger.debug("cache.hit", extra={"source": "abs", "identifier": dataflow_id})
            return cached

        url = f"{self.BASE_URL}/datastructure/ABS/{dataflow_id}"
        _logger.info(
            "request.start",
            extra={"source": "abs", "identifier": dataflow_id, "url": url},
        )
        start = perf_counter()
        response = await get_with_retries(
            self._client,
            url,
            params={"references": "children"},
            source="abs",
            identifier=dataflow_id,
        )
        _logger.info(
            "request.success",
            extra={
                "source": "abs",
                "identifier": dataflow_id,
                "status_code": response.status_code,
                "duration_ms": int((perf_counter() - start) * 1000),
                "bytes": len(response.content),
            },
        )
        try:
            parsed = parse_abs_structure(response.text)
        except (ET.ParseError, KeyError, TypeError, ValueError) as exc:
            _logger.error(
                "parse.failed",
                extra={"source": "abs", "identifier": dataflow_id, "url": url},
            )
            raise AuseconParseError(
                f"Failed to parse ABS structure payload for '{dataflow_id}'."
            ) from exc
        return self._cache.set(cache_key, parsed, self._ttl_seconds)

    async def get_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
    ) -> dict[str, Any]:
        cache_key = f"abs-data:{dataflow_id}:{key}:{start_period}:{end_period}:{updated_after}"
        raw_payload = self._cache.get(cache_key)
        stale_meta: dict[str, Any] | None = None

        if raw_payload is None:
            params: list[tuple[str, str]] = []
            if start_period:
                params.append(("startPeriod", start_period))
            if end_period:
                params.append(("endPeriod", end_period))
            if updated_after:
                params.append(("updatedAfter", updated_after))
            params.append(("format", "csvfile"))

            url = f"{self.BASE_URL}/data/{dataflow_id}/{key}"
            _logger.info(
                "request.start",
                extra={"source": "abs", "identifier": dataflow_id, "url": url},
            )
            start = perf_counter()
            try:
                response = await get_with_retries(
                    self._client,
                    url,
                    params=params,
                    source="abs",
                    identifier=dataflow_id,
                )
            except AuseconUpstreamError:
                stale = self._cache.get_stale(cache_key)
                if stale is None:
                    raise
                raw_payload = stale["value"]
                stale_meta = stale
                _logger.warning(
                    "request.stale_fallback",
                    extra={
                        "source": "abs",
                        "identifier": dataflow_id,
                        "cached_at": stale["cached_at"],
                        "expires_at": stale["expires_at"],
                    },
                )
            else:
                _logger.info(
                    "request.success",
                    extra={
                        "source": "abs",
                        "identifier": dataflow_id,
                        "status_code": response.status_code,
                        "duration_ms": int((perf_counter() - start) * 1000),
                        "bytes": len(response.content),
                    },
                )
                try:
                    raw_payload = parse_abs_csv(response.text)
                except (KeyError, TypeError, ValueError) as exc:
                    _logger.error(
                        "parse.failed",
                        extra={"source": "abs", "identifier": dataflow_id, "url": url},
                    )
                    raise AuseconParseError(
                        f"Failed to parse ABS data payload for '{dataflow_id}'."
                    ) from exc
                raw_payload["metadata"]["retrieval_url"] = str(response.request.url)
                raw_payload["metadata"]["updated_after"] = updated_after
                raw_payload = self._cache.set(cache_key, raw_payload, self._ttl_seconds)

        payload = _slice_observations(deepcopy(raw_payload), last_n)
        payload["metadata"]["server_version"] = resolve_version()
        if stale_meta is not None:
            payload["metadata"]["stale"] = True
            payload["metadata"]["cached_at"] = stale_meta["cached_at"]
            payload["metadata"]["expires_at"] = stale_meta["expires_at"]
        return payload


def _slice_observations(payload: dict[str, Any], last_n: int | None) -> dict[str, Any]:
    observations = payload["observations"]
    if last_n is None or last_n <= 0 or len(observations) <= last_n:
        payload["metadata"]["truncated"] = False
        return payload

    payload["observations"] = observations[-last_n:]
    series_ids = {item["series_id"] for item in payload["observations"]}
    payload["series"] = [item for item in payload["series"] if item["series_id"] in series_ids]
    payload["metadata"]["truncated"] = True
    return payload

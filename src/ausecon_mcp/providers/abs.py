from __future__ import annotations

from copy import deepcopy
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.errors import AuseconParseError
from ausecon_mcp.parsers.abs_csv import parse_abs_csv
from ausecon_mcp.parsers.abs_structure import parse_abs_structure
from ausecon_mcp.providers._retry import get_with_retries


class ABSProvider:
    BASE_URL = "https://data.api.abs.gov.au/rest"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._client = client or httpx.AsyncClient(timeout=30)
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds

    async def get_dataset_structure(self, dataflow_id: str) -> dict[str, Any]:
        cache_key = f"abs-structure:{dataflow_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        response = await get_with_retries(
            self._client,
            f"{self.BASE_URL}/datastructure/ABS/{dataflow_id}",
            params={"references": "children"},
            source="abs",
            identifier=dataflow_id,
        )
        try:
            parsed = parse_abs_structure(response.text)
        except (ET.ParseError, KeyError, TypeError, ValueError) as exc:
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
        cache_key = (
            f"abs-data:{dataflow_id}:{key}:{start_period}:{end_period}:"
            f"{updated_after}"
        )
        raw_payload = self._cache.get(cache_key)

        if raw_payload is None:
            params: list[tuple[str, str]] = []
            if start_period:
                params.append(("startPeriod", start_period))
            if end_period:
                params.append(("endPeriod", end_period))
            if updated_after:
                params.append(("updatedAfter", updated_after))
            params.append(("format", "csvfile"))

            response = await get_with_retries(
                self._client,
                f"{self.BASE_URL}/data/{dataflow_id}/{key}",
                params=params,
                source="abs",
                identifier=dataflow_id,
            )
            try:
                raw_payload = parse_abs_csv(response.text)
            except (KeyError, TypeError, ValueError) as exc:
                raise AuseconParseError(
                    f"Failed to parse ABS data payload for '{dataflow_id}'."
                ) from exc
            raw_payload["metadata"]["retrieval_url"] = str(response.request.url)
            raw_payload["metadata"]["updated_after"] = updated_after
            raw_payload = self._cache.set(cache_key, raw_payload, self._ttl_seconds)

        return _slice_observations(deepcopy(raw_payload), last_n)


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

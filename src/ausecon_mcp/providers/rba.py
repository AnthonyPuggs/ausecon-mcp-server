from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Any

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.errors import AuseconParseError, AuseconUpstreamError
from ausecon_mcp.filters import filter_payload
from ausecon_mcp.logging import get_logger
from ausecon_mcp.parsers.rba_csv import parse_rba_csv
from ausecon_mcp.providers._http import build_client, resolve_version, utc_now_iso
from ausecon_mcp.providers._retry import get_with_retries

_logger = get_logger("providers.rba")


class RBAProvider:
    BASE_URL = "https://www.rba.gov.au/statistics/tables/csv"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._owns_client = client is None
        self._client = client or build_client()
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def list_tables(
        self,
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict[str, Any]]:
        tables = []
        for table in RBA_CATALOGUE.values():
            if category and table.get("category") != category:
                continue
            if table.get("discontinued", False) and not include_discontinued:
                continue
            tables.append(
                {
                    "id": table["id"],
                    "name": table["name"],
                    "category": table["category"],
                    "frequency": table["frequency"],
                    "discontinued": table.get("discontinued", False),
                }
            )
        return tables

    async def get_table(
        self,
        table_id: str,
        series_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        last_n: int | None = None,
        csv_path: str | None = None,
    ) -> dict[str, Any]:
        cache_key = f"rba-table:{table_id}"
        raw_payload = self._cache.get(cache_key)
        stale_meta: dict[str, Any] | None = None

        if raw_payload is None:
            filename = csv_path or f"{table_id}-data.csv"
            url = f"{self.BASE_URL}/{filename}"
            _logger.info(
                "request.start",
                extra={"source": "rba", "identifier": table_id, "url": url},
            )
            start = perf_counter()
            try:
                response = await get_with_retries(
                    self._client,
                    url,
                    params=None,
                    source="rba",
                    identifier=table_id,
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
                        "source": "rba",
                        "identifier": table_id,
                        "cached_at": stale["cached_at"],
                        "expires_at": stale["expires_at"],
                    },
                )
            else:
                _logger.info(
                    "request.success",
                    extra={
                        "source": "rba",
                        "identifier": table_id,
                        "status_code": response.status_code,
                        "duration_ms": int((perf_counter() - start) * 1000),
                        "bytes": len(response.content),
                    },
                )
                try:
                    raw_payload = parse_rba_csv(response.text, table_id=table_id)
                except (IndexError, KeyError, TypeError, ValueError) as exc:
                    _logger.error(
                        "parse.failed",
                        extra={"source": "rba", "identifier": table_id, "url": url},
                    )
                    raise AuseconParseError(
                        f"Failed to parse RBA table payload for '{table_id}'."
                    ) from exc
                raw_payload["metadata"]["retrieval_url"] = str(response.request.url)
                raw_payload["metadata"]["retrieved_at"] = utc_now_iso()
                raw_payload = self._cache.set(cache_key, raw_payload, self._ttl_seconds)

        payload = filter_payload(
            deepcopy(raw_payload),
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )
        payload["metadata"]["server_version"] = resolve_version()
        if stale_meta is not None:
            payload["metadata"]["stale"] = True
            payload["metadata"]["cached_at"] = stale_meta["cached_at"]
            payload["metadata"]["expires_at"] = stale_meta["expires_at"]
        return payload

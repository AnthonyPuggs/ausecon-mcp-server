from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Any

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.errors import AuseconNotFoundError, AuseconParseError, AuseconUpstreamError
from ausecon_mcp.filters import filter_payload
from ausecon_mcp.logging import get_logger
from ausecon_mcp.parsers.rba_csv import parse_rba_csv
from ausecon_mcp.providers._http import build_client, resolve_version, utc_now_iso
from ausecon_mcp.providers._retry import get_with_retries, stamp_stale_metadata
from ausecon_mcp.providers._single_flight import SingleFlight

_logger = get_logger("providers.rba")

# The largest current RBA table CSV is about 2 MB (B3); the cap only stops a runaway download.
MAX_TABLE_BYTES = 8 * 1024 * 1024


class RBAProvider:
    BASE_URL = "https://www.rba.gov.au/statistics/tables/csv"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
        max_table_bytes: int = MAX_TABLE_BYTES,
    ) -> None:
        self._owns_client = client is None
        self._client = client or build_client()
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds
        self._max_table_bytes = max_table_bytes
        self._single_flight = SingleFlight()

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
        raw_payload = await self._cache.aget(cache_key)
        stale_meta: dict[str, Any] | None = None
        if raw_payload is None:
            raw_payload, stale_meta = await self._single_flight.run(
                cache_key,
                lambda: self._fetch_table(table_id, csv_path, cache_key),
            )
            raw_payload = deepcopy(raw_payload)

        payload = filter_payload(
            raw_payload,
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )
        payload["metadata"]["server_version"] = resolve_version()
        if stale_meta is not None:
            stamp_stale_metadata(payload, stale_meta, source="rba")
        return payload

    async def _fetch_table(
        self,
        table_id: str,
        csv_path: str | None,
        cache_key: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        stale_meta: dict[str, Any] | None = None
        raw_payload = None
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
                max_bytes=self._max_table_bytes,
            )
        except AuseconUpstreamError as exc:
            stale = self._cache.get_stale(cache_key)
            if stale is None:
                if isinstance(exc, AuseconNotFoundError):
                    raise AuseconNotFoundError(
                        f"The RBA has no table '{table_id}' (HTTP 404 for {filename}). "
                        "list_rba_tables lists the table IDs this server knows, and "
                        "search_datasets finds them by topic.",
                        status_code=exc.status_code,
                        body=exc.body,
                        url=exc.url,
                    ) from exc
                raise
            raw_payload = stale["value"]
            stale_meta = {**stale, "error": str(exc)}
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
            raw_payload = await self._cache.aset(cache_key, raw_payload, self._ttl_seconds)

        return raw_payload, stale_meta

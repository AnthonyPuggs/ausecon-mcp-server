from __future__ import annotations

from copy import deepcopy
from typing import Any

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.errors import AuseconParseError
from ausecon_mcp.parsers.rba_csv import parse_rba_csv
from ausecon_mcp.providers._retry import get_with_retries


class RBAProvider:
    BASE_URL = "https://www.rba.gov.au/statistics/tables/csv"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._client = client or httpx.AsyncClient(timeout=30)
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds

    def list_tables(
        self,
        category: str | None = None,
        include_discontinued: bool = False,
    ) -> list[dict[str, Any]]:
        del include_discontinued
        tables = []
        for table in RBA_CATALOGUE.values():
            if category and table.get("category") != category:
                continue
            tables.append(
                {
                    "id": table["id"],
                    "name": table["name"],
                    "category": table["category"],
                    "frequency": table["frequency"],
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
    ) -> dict[str, Any]:
        cache_key = f"rba-table:{table_id}"
        raw_payload = self._cache.get(cache_key)

        if raw_payload is None:
            response = await get_with_retries(
                self._client,
                f"{self.BASE_URL}/{table_id}-data.csv",
                params=None,
                source="rba",
                identifier=table_id,
            )
            try:
                raw_payload = parse_rba_csv(response.text, table_id=table_id)
            except (IndexError, KeyError, TypeError, ValueError) as exc:
                raise AuseconParseError(
                    f"Failed to parse RBA table payload for '{table_id}'."
                ) from exc
            raw_payload["metadata"]["retrieval_url"] = str(response.request.url)
            raw_payload = self._cache.set(cache_key, raw_payload, self._ttl_seconds)

        return _filter_rba_payload(
            deepcopy(raw_payload),
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )


def _filter_rba_payload(
    payload: dict[str, Any],
    series_ids: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    last_n: int | None,
) -> dict[str, Any]:
    observations = payload["observations"]
    if series_ids:
        allowed = set(series_ids)
        observations = [item for item in observations if item["series_id"] in allowed]
        payload["series"] = [item for item in payload["series"] if item["series_id"] in allowed]
    if start_date:
        observations = [item for item in observations if item["date"] >= start_date]
    if end_date:
        observations = [item for item in observations if item["date"] <= end_date]

    truncated = False
    if last_n is not None and last_n > 0 and len(observations) > last_n:
        observations = observations[-last_n:]
        truncated = True

    series_id_set = {item["series_id"] for item in observations}
    payload["series"] = [item for item in payload["series"] if item["series_id"] in series_id_set]
    payload["observations"] = observations
    payload["metadata"]["truncated"] = truncated
    return payload

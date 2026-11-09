from __future__ import annotations

import json
from copy import deepcopy
from time import perf_counter
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.errors import AuseconNotFoundError, AuseconParseError, AuseconUpstreamError
from ausecon_mcp.filters import filter_payload
from ausecon_mcp.logging import get_logger
from ausecon_mcp.parsers.abs_availability import parse_abs_availability
from ausecon_mcp.parsers.abs_csv import parse_abs_csv
from ausecon_mcp.parsers.abs_structure import parse_abs_structure
from ausecon_mcp.providers._http import build_client, resolve_version, utc_now_iso
from ausecon_mcp.providers._retry import get_with_retries, stamp_stale_metadata
from ausecon_mcp.providers._single_flight import SingleFlight

_logger = get_logger("providers.abs")


def _no_records_payload(
    dataflow_id: str,
    *,
    url: str | None,
    start_period: str | None,
    end_period: str | None,
    updated_after: str | None,
) -> dict[str, Any]:
    window_parts = []
    if start_period:
        window_parts.append(f"start {start_period}")
    if end_period:
        window_parts.append(f"end {end_period}")
    window = f" in the requested window ({', '.join(window_parts)})" if window_parts else ""
    return {
        "metadata": {
            "source": "abs",
            "dataset_id": dataflow_id,
            "frequency": None,
            "retrieval_url": url or "",
            "retrieved_at": utc_now_iso(),
            "updated_after": updated_after,
            "warnings": [
                f"ABS returned no observations for '{dataflow_id}'{window}. "
                "The series may not extend that far, or may have ceased."
            ],
        },
        "series": [],
        "observations": [],
    }


def _format_codes(codes: list[dict[str, str]], limit: int = 6) -> str:
    rendered = [
        f"{item['code']} ({item['label']})" if item["label"] != item["code"] else item["code"]
        for item in codes[:limit]
    ]
    if len(codes) > limit:
        rendered.append(f"and {len(codes) - limit} more")
    return ", ".join(rendered)


def _availability_hint(key: str, availability: dict[str, Any]) -> str | None:
    """Explain an empty ABS result using the ``availableconstraint`` response for its key."""
    if availability.get("obs_count"):
        time_range = availability.get("time_range")
        if time_range is None:
            return None
        return (
            f"Key '{key}' has data from {time_range[0]} to {time_range[1]}; "
            "widen or move the requested window."
        )

    dimensions = availability.get("dimensions", [])
    if key == "all" or not dimensions:
        return None
    parts = key.split(".")
    if len(parts) != len(dimensions):
        return None

    suggestions = []
    for part, dimension in zip(parts, dimensions, strict=True):
        if not part:
            continue
        requested = set(part.split("+"))
        alternatives = [item for item in dimension["available"] if item["code"] not in requested]
        if alternatives:
            suggestions.append(
                f"{dimension['id']}={part} has no data; with the other dimensions unchanged, "
                f"{dimension['id']} has data for {_format_codes(alternatives)}"
            )
    if not suggestions:
        return (
            f"Key '{key}' has no data, and changing any one dimension does not help; "
            "check the codes with get_abs_dataset_structure."
        )
    return "; ".join(suggestions) + "."


class ABSProvider:
    BASE_URL = "https://data.api.abs.gov.au/rest"

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
        self._single_flight = SingleFlight()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_dataset_structure(self, dataflow_id: str) -> dict[str, Any]:
        cache_key = f"abs-structure:{dataflow_id}"
        cached = await self._cache.aget(cache_key)
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
        return await self._cache.aset(cache_key, parsed, self._ttl_seconds)

    async def get_data(
        self,
        dataflow_id: str,
        key: str = "all",
        start_period: str | None = None,
        end_period: str | None = None,
        last_n: int | None = None,
        updated_after: str | None = None,
        latest_n: int | None = None,
    ) -> dict[str, Any]:
        # Structured encoding so a literal "None" value can never alias an absent one.
        cache_key = "abs-data:" + json.dumps(
            [dataflow_id, key, start_period, end_period, updated_after, latest_n]
        )
        raw_payload = await self._cache.aget(cache_key)
        stale_meta: dict[str, Any] | None = None
        if raw_payload is None:
            raw_payload, stale_meta = await self._single_flight.run(
                cache_key,
                lambda: self._fetch_data(
                    dataflow_id,
                    key,
                    start_period,
                    end_period,
                    updated_after,
                    latest_n,
                    cache_key,
                ),
            )
            raw_payload = deepcopy(raw_payload)

        payload = filter_payload(raw_payload, last_n=last_n)
        payload["metadata"]["server_version"] = resolve_version()
        if stale_meta is not None:
            stamp_stale_metadata(payload, stale_meta, source="abs")
        return payload

    async def _fetch_data(
        self,
        dataflow_id: str,
        key: str,
        start_period: str | None,
        end_period: str | None,
        updated_after: str | None,
        latest_n: int | None,
        cache_key: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        stale_meta: dict[str, Any] | None = None
        raw_payload = None
        params: list[tuple[str, str]] = []
        if start_period:
            params.append(("startPeriod", start_period))
        if end_period:
            params.append(("endPeriod", end_period))
        if updated_after:
            params.append(("updatedAfter", updated_after))
        if latest_n is not None:
            params.append(("lastNObservations", str(latest_n)))
        params.append(("format", "csvfilewithlabels"))

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
        except AuseconNotFoundError as exc:
            # The ABS API answers 404 both for unknown dataflows and for valid
            # dataflows with no observations in the requested window; only the
            # body distinguishes them. Never fall back to stale data on a 404.
            if "norecordsfound" in (exc.body or "").lower():
                _logger.info(
                    "request.no_records",
                    extra={"source": "abs", "identifier": dataflow_id, "url": exc.url},
                )
                raw_payload = _no_records_payload(
                    dataflow_id,
                    url=exc.url,
                    start_period=start_period,
                    end_period=end_period,
                    updated_after=updated_after,
                )
                if updated_after is None:
                    hint = await self._no_records_hint(dataflow_id, key)
                    if hint:
                        raw_payload["metadata"]["warnings"].append(hint)
            else:
                raise AuseconNotFoundError(
                    f"ABS request for '{dataflow_id}' failed with HTTP 404: the dataflow "
                    "appears unknown, renamed, or retired. Check the id with "
                    "search_datasets or list_catalogue.",
                    status_code=exc.status_code,
                    body=exc.body,
                    url=exc.url,
                ) from exc
        except AuseconUpstreamError as exc:
            stale = self._cache.get_stale(cache_key)
            if stale is None:
                raise
            raw_payload = stale["value"]
            stale_meta = {**stale, "error": str(exc)}
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
            raw_payload["metadata"]["retrieved_at"] = utc_now_iso()
            raw_payload["metadata"]["updated_after"] = updated_after
            raw_payload = await self._cache.aset(cache_key, raw_payload, self._ttl_seconds)

        return raw_payload, stale_meta

    async def _no_records_hint(self, dataflow_id: str, key: str) -> str | None:
        """Best-effort explanation of an empty result; never fails the data request."""
        cache_key = "abs-availability:" + json.dumps([dataflow_id, key])
        availability = await self._cache.aget(cache_key)
        if availability is None:
            url = f"{self.BASE_URL}/availableconstraint/{dataflow_id}/{key}/all/all"
            try:
                response = await get_with_retries(
                    self._client,
                    url,
                    params={"mode": "available", "references": "all"},
                    source="abs",
                    identifier=dataflow_id,
                    attempts=1,
                )
                availability = parse_abs_availability(response.text)
            except Exception:  # noqa: BLE001 - the hint is best-effort; the empty payload stands
                _logger.info(
                    "request.availability_failed",
                    extra={"source": "abs", "identifier": dataflow_id, "url": url},
                )
                return None
            # JSON round-trips tuples as lists, so store the range as a list throughout.
            if availability["time_range"] is not None:
                availability["time_range"] = list(availability["time_range"])
            availability = await self._cache.aset(cache_key, availability, self._ttl_seconds)
        return _availability_hint(key, availability)

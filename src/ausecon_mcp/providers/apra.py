from __future__ import annotations

import asyncio
import re
from copy import deepcopy
from html.parser import HTMLParser
from time import perf_counter
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.errors import AuseconParseError, AuseconUpstreamError, AuseconValidationError
from ausecon_mcp.filters import filter_payload
from ausecon_mcp.logging import get_logger
from ausecon_mcp.parsers.apra_xlsx import parse_apra_xlsx
from ausecon_mcp.providers._http import build_client, resolve_version, utc_now_iso
from ausecon_mcp.providers._retry import get_with_retries

_logger = get_logger("providers.apra")
_TRUSTED_APRA_DOWNLOAD_HOSTS = {"apra.gov.au", "www.apra.gov.au"}


class APRAProvider:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
        catalogue: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or build_client()
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds
        self._catalogue = catalogue or APRA_CATALOGUE

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_data(
        self,
        publication_id: str,
        table_id: str | None = None,
        series_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        last_n: int | None = None,
    ) -> dict[str, Any]:
        entry = self._catalogue.get(publication_id)
        if entry is None:
            raise AuseconValidationError(f"Unknown APRA publication {publication_id!r}.")
        if table_id is not None and table_id not in entry["tables"]:
            known = ", ".join(sorted(entry["tables"]))
            raise AuseconValidationError(
                f"Unknown APRA table {table_id!r} for {publication_id!r}. "
                f"Known tables: {known or '(none)'}."
            )

        cache_key = _cache_key(publication_id, table_id)
        raw_payload = self._cache.get(cache_key)
        stale_meta: dict[str, Any] | None = None

        if raw_payload is None:
            try:
                raw_payload = await self._fetch_and_parse(
                    publication_id,
                    entry,
                    table_id=table_id,
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
                        "source": "apra",
                        "identifier": publication_id,
                        "cached_at": stale["cached_at"],
                        "expires_at": stale["expires_at"],
                    },
                )
            else:
                raw_payload = self._cache.set(cache_key, raw_payload, self._ttl_seconds)

        payload = deepcopy(raw_payload)
        if table_id is not None:
            payload["metadata"]["frequency"] = entry["tables"][table_id].get(
                "frequency",
                entry.get("frequency"),
            )
        payload = filter_payload(
            payload,
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

    async def _fetch_and_parse(
        self,
        publication_id: str,
        entry: dict[str, Any],
        *,
        table_id: str | None,
    ) -> dict[str, Any]:
        landing_url = entry["landing_url"]
        _logger.info(
            "request.start",
            extra={
                "source": "apra",
                "identifier": publication_id,
                "table_id": table_id,
                "url": landing_url,
            },
        )
        start = perf_counter()
        landing_response = await get_with_retries(
            self._client,
            landing_url,
            params=None,
            source="apra",
            identifier=publication_id,
        )
        download_url = resolve_apra_download_url(
            landing_response.text,
            base_url=landing_url,
            patterns=entry["link_patterns"],
        )
        xlsx_response = await get_with_retries(
            self._client,
            download_url,
            params=None,
            source="apra",
            identifier=publication_id,
        )
        download_ms = int((perf_counter() - start) * 1000)
        parse_start = perf_counter()
        _logger.info(
            "download.success",
            extra={
                "source": "apra",
                "identifier": publication_id,
                "table_id": table_id,
                "status_code": xlsx_response.status_code,
                "download_ms": download_ms,
                "bytes": len(xlsx_response.content),
            },
        )
        try:
            payload = await asyncio.to_thread(
                parse_apra_xlsx,
                xlsx_response.content,
                publication_id=publication_id,
                title=entry["name"],
                frequency=entry["frequency"],
                table_maps=entry["tables"],
                table_id=table_id,
            )
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            _logger.error(
                "parse.failed",
                extra={
                    "source": "apra",
                    "identifier": publication_id,
                    "table_id": table_id,
                    "url": download_url,
                },
            )
            raise AuseconParseError(
                f"Failed to parse APRA publication payload for '{publication_id}'."
            ) from exc
        parse_ms = int((perf_counter() - parse_start) * 1000)
        _logger.info(
            "request.success",
            extra={
                "source": "apra",
                "identifier": publication_id,
                "table_id": table_id,
                "status_code": xlsx_response.status_code,
                "download_ms": download_ms,
                "parse_ms": parse_ms,
                "duration_ms": int((perf_counter() - start) * 1000),
                "bytes": len(xlsx_response.content),
                "series_count": len(payload["series"]),
                "observation_count": len(payload["observations"]),
            },
        )
        payload["metadata"]["retrieval_url"] = str(xlsx_response.request.url)
        payload["metadata"]["retrieved_at"] = utc_now_iso()
        return payload


def resolve_apra_download_url(html: str, *, base_url: str, patterns: list[str]) -> str:
    links = _LinkExtractor()
    links.feed(html)
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for href, label in links.links:
        normalised_label = re.sub(r"\s+", " ", label).strip()
        if not href or not all(pattern.search(normalised_label) for pattern in compiled):
            continue
        candidate_url = urljoin(base_url, href)
        parsed = urlparse(candidate_url)
        if not parsed.path.lower().endswith(".xlsx"):
            continue
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme == "https" and hostname in _TRUSTED_APRA_DOWNLOAD_HOSTS:
            return candidate_url
    raise AuseconParseError(
        "APRA landing page did not contain the expected trusted APRA HTTPS XLSX link."
    )


def _cache_key(publication_id: str, table_id: str | None) -> str:
    if table_id is None:
        return f"apra-publication:{publication_id}"
    return f"apra-publication:{publication_id}:table:{table_id}"


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {name.lower(): value for name, value in attrs}
        self._current_href = attr_map.get("href")
        self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return
        self.links.append((self._current_href, "".join(self._current_text)))
        self._current_href = None
        self._current_text = []

from __future__ import annotations

import calendar
import json
import re
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from html.parser import HTMLParser
from importlib import resources
from typing import Any

import httpx

from ausecon_mcp.cache import TTLCache
from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.errors import AuseconUpstreamError
from ausecon_mcp.governance.apra import audit_apra_governance, governance_by_publication
from ausecon_mcp.providers._http import build_client
from ausecon_mcp.providers._retry import get_with_retries

ABS_RELEASE_URL = "https://www.abs.gov.au/release-calendar/future-releases"
RBA_RELEASE_URL = "https://www.rba.gov.au/schedules-events/"


class ReleaseProvider:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        ttl_seconds: int = 3600,
        today: date | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or build_client()
        self._cache = cache or TTLCache()
        self._ttl_seconds = ttl_seconds
        self._today = today

    async def list_events(self) -> list[dict[str, Any]]:
        cache_key = "release-events"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return deepcopy(cached)

        try:
            events = await self._fetch_events()
        except AuseconUpstreamError:
            stale = self._cache.get_stale(cache_key)
            if stale is None:
                raise
            return deepcopy(stale["value"])

        stored = self._cache.set(cache_key, events, self._ttl_seconds)
        return deepcopy(stored)

    async def _fetch_events(self) -> list[dict[str, Any]]:
        today = self._today or date.today()
        abs_response = await get_with_retries(
            self._client,
            ABS_RELEASE_URL,
            params=None,
            source="abs",
            identifier="release-calendar",
        )
        rba_response = await get_with_retries(
            self._client,
            RBA_RELEASE_URL,
            params=None,
            source="rba",
            identifier="release-schedule",
        )
        return sorted(
            [
                *parse_abs_release_events(abs_response.text),
                *parse_rba_release_events(rba_response.text, today=today),
                *build_apra_release_events(
                    today=today,
                    seed_checked_at=apra_seed_checked_at(),
                    governance_rows=audit_apra_governance(today=today),
                ),
            ],
            key=lambda row: (row["release_datetime"], row["source"], row["release_name"]),
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


def parse_abs_release_events(
    html: str,
    *,
    source_url: str = ABS_RELEASE_URL,
) -> list[dict[str, Any]]:
    parser = _AbsReleaseParser()
    parser.feed(html)
    events = []
    for item in parser.items:
        release_name = item.get("heading")
        release_datetime = item.get("datetime")
        if not release_name or not release_datetime:
            continue
        reference_period = _reference_period(item.get("text", ""))
        events.append(
            {
                "source": "abs",
                "event_kind": "official_calendar",
                "date_source": "official_page",
                "release_name": release_name,
                "release_datetime": release_datetime,
                "timezone": "Australia/Canberra",
                "reference_period": reference_period,
                "matched_catalogue_ids": _match_catalogue_ids("abs", release_name),
                "upstream_url": source_url,
            }
        )
    return sorted(events, key=lambda row: (row["release_datetime"], row["release_name"]))


def parse_rba_release_events(
    html: str,
    *,
    source_url: str = RBA_RELEASE_URL,
    today: date | None = None,
) -> list[dict[str, Any]]:
    parser = _TableParser()
    parser.feed(html)
    today = today or date.today()
    events = []
    for table in parser.tables:
        if not table:
            continue
        headers = [cell.lower() for cell in table[0]]
        month_columns = _month_columns(headers)
        for row in table[1:]:
            if len(row) < 3:
                continue
            release_name = row[0].strip()
            release_time = _parse_rba_time(row[2])
            for index, month in month_columns:
                if index >= len(row):
                    continue
                raw_day = row[index].strip()
                if not raw_day or raw_day in {"-", "\u2013", "\u2014"}:
                    continue
                match = re.search(r"\d{1,2}", raw_day)
                if not match:
                    continue
                year = today.year + (1 if month < today.month else 0)
                release_date = date(year, month, int(match.group(0)))
                events.append(
                    {
                        "source": "rba",
                        "event_kind": "official_calendar",
                        "date_source": "official_page",
                        "release_name": release_name,
                        "release_datetime": datetime.combine(
                            release_date,
                            release_time,
                        ).isoformat(timespec="seconds"),
                        "timezone": "Australia/Sydney",
                        "reference_period": None,
                        "matched_catalogue_ids": _match_catalogue_ids("rba", release_name),
                        "upstream_url": source_url,
                    }
                )
    return sorted(events, key=lambda row: (row["release_datetime"], row["release_name"]))


def build_apra_release_events(
    catalogue: dict[str, dict[str, Any]] | None = None,
    *,
    today: date | None = None,
    seed_checked_at: str | None = None,
    governance_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    catalogue = catalogue or APRA_CATALOGUE
    today = today or date.today()
    governance_index = governance_by_publication(governance_rows or [])
    events = []
    for entry in catalogue.values():
        if entry.get("ceased") or entry.get("discontinued"):
            continue
        governance = governance_index.get(entry["id"], {})
        row_seed_checked_at = seed_checked_at or governance.get("seed_checked_at")
        governance_status = str(
            governance.get("status")
            or _seed_freshness_status(row_seed_checked_at, entry.get("frequency"), today)
        )
        release_date = _next_expected_apra_date(entry.get("frequency"), today)
        audit = entry.get("audit", {})
        cadence = f"{entry.get('frequency', 'Unknown')} cadence"
        if row_seed_checked_at:
            cadence = f"{cadence}; seed checked {row_seed_checked_at}"
        events.append(
            {
                "source": "apra",
                "event_kind": "expected_release",
                "date_source": "cadence_estimate",
                "release_name": entry["name"],
                "release_datetime": datetime.combine(release_date, time()).isoformat(
                    timespec="seconds"
                ),
                "timezone": "Australia/Sydney",
                "reference_period": cadence,
                "cadence": entry.get("frequency"),
                "seed_checked_at": row_seed_checked_at,
                "audit_last_audited": audit.get("last_audited"),
                "governance_status": governance_status,
                "governance_issues": [
                    issue.get("code") for issue in governance.get("issues", [])
                ],
                "matched_catalogue_ids": [entry["id"]],
                "upstream_url": audit.get("upstream_url", entry.get("landing_url")),
            }
        )
    return sorted(events, key=lambda row: (row["release_datetime"], row["release_name"]))


def apra_seed_checked_at() -> str | None:
    try:
        text = resources.files("ausecon_mcp").joinpath(
            "data/apra_url_seeds.json"
        ).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    seeds = json.loads(text)
    checked_at_values = [
        seed["checked_at"]
        for seed_rows in seeds.values()
        for seed in seed_rows
        if seed.get("checked_at")
    ]
    if not checked_at_values:
        return None
    return min(checked_at_values)


def _seed_freshness_status(
    checked_at: str | None,
    frequency: str | None,
    today: date,
) -> str:
    if checked_at is None:
        return "unknown"
    try:
        checked_date = datetime.fromisoformat(checked_at.replace("Z", "+00:00")).date()
    except ValueError:
        return "fail"
    threshold = {"Monthly": 45, "Quarterly": 120, "Annual": 400}.get(str(frequency), 400)
    return "stale" if (today - checked_date).days > threshold else "ok"


def filter_release_events(
    events: list[dict[str, Any]],
    *,
    source: str | None = None,
    query: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    query_terms = _terms(query or "")
    filtered = []
    for event in events:
        if source is not None and event["source"] != source:
            continue
        event_date = event["release_datetime"][:10]
        if start_date is not None and event_date < start_date:
            continue
        if end_date is not None and event_date > end_date:
            continue
        haystack = " ".join(
            [
                event.get("release_name") or "",
                event.get("reference_period") or "",
                " ".join(event.get("matched_catalogue_ids") or []),
            ]
        )
        if query_terms and not query_terms <= _terms(haystack):
            continue
        filtered.append(event)
    return sorted(filtered, key=lambda row: (row["release_datetime"], row["source"]))[:limit]


def _reference_period(text: str) -> str | None:
    match = re.search(r"Reference period\s+([^\n\r<]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return " ".join(match.group(1).split())


def _month_columns(headers: list[str]) -> list[tuple[int, int]]:
    out = []
    month_names = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
    month_abbrs = {name.lower(): index for index, name in enumerate(calendar.month_abbr) if name}
    for index, header in enumerate(headers):
        key = header.strip().lower()
        if key in month_names:
            out.append((index, month_names[key]))
        elif key in month_abbrs:
            out.append((index, month_abbrs[key]))
    return out


def _parse_rba_time(value: str) -> time:
    normalised = value.strip().lower().replace(".", ":")
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)", normalised)
    if not match:
        return time(11, 30)
    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    if match.group(3) == "pm" and hour != 12:
        hour += 12
    if match.group(3) == "am" and hour == 12:
        hour = 0
    return time(hour, minute)


def _next_expected_apra_date(frequency: str | None, today: date) -> date:
    if frequency == "Monthly":
        return _last_business_day(today.year, today.month)
    if frequency == "Quarterly":
        quarter_month = ((today.month - 1) // 3 + 1) * 3
        return _last_business_day(today.year, quarter_month)
    return today


def _last_business_day(year: int, month: int) -> date:
    candidate = date(year, month, calendar.monthrange(year, month)[1])
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def _terms(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _match_catalogue_ids(source: str, release_name: str) -> list[str]:
    catalogue = {"abs": ABS_CATALOGUE, "rba": RBA_CATALOGUE}[source]
    release_terms = _terms(release_name)
    matches = []
    for entry in catalogue.values():
        candidates = [entry["name"], *entry.get("aliases", [])]
        if any(_terms(candidate) <= release_terms for candidate in candidates):
            matches.append(entry["id"])
    return sorted(matches)


class _AbsReleaseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._capture: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value for name, value in attrs}
        if tag == "time" and attr_map.get("datetime"):
            self._current = {"datetime": attr_map["datetime"] or "", "text": ""}
            self.items.append(self._current)
            self._capture = "text"
        elif tag in {"h2", "h3", "h4"} and self._current is not None:
            self._capture = "heading"
            self._text = []
        elif tag == "p" and self._current is not None:
            self._capture = "paragraph"
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._capture and self._current is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return
        text = " ".join("".join(self._text).split())
        if tag in {"h2", "h3", "h4"} and self._capture == "heading":
            self._current.setdefault("heading", text)
            self._capture = None
        elif tag == "p" and self._capture == "paragraph":
            self._current["text"] = f"{self._current.get('text', '')}\n{text}".strip()
            self._capture = None
        elif tag == "time" and self._capture == "text":
            self._capture = None


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._capture_cell = False
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._capture_cell = True
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._capture_cell:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._capture_cell and self._row is not None:
            self._row.append(" ".join("".join(self._text).split()))
            self._capture_cell = False
        elif tag == "tr" and self._table is not None and self._row is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

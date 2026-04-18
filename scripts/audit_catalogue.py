"""Audit every catalogue entry against live upstream.

Fetches the ABS dataflow registry and the RBA tables index, then diffs each
entry's ``audit.upstream_title`` (and URL reachability) against live. Prints a
markdown report to stdout in the same shape as
``docs/coverage-audit-2026-04.md``. Exits non-zero if any drift is detected.

Run via ``uv run python scripts/audit_catalogue.py`` or wire into CI.
"""

from __future__ import annotations

import html
import re
import sys
from collections.abc import Iterable
from xml.etree import ElementTree as ET

import httpx

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE

ABS_DATAFLOW_INDEX = "https://data.api.abs.gov.au/rest/dataflow/ABS"
RBA_TABLES_INDEX = "https://www.rba.gov.au/statistics/tables/"

_SDMX_NS = {
    "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}


def fetch_abs_dataflows(client: httpx.Client) -> dict[str, str]:
    """Return a mapping of ABS dataflow id -> current Name."""
    resp = client.get(ABS_DATAFLOW_INDEX, timeout=60.0)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    out: dict[str, str] = {}
    for df in root.findall(".//structure:Dataflow", _SDMX_NS):
        df_id = df.attrib.get("id")
        if not df_id:
            continue
        name_el = df.find("./common:Name", _SDMX_NS)
        if name_el is not None and name_el.text:
            out[df_id] = name_el.text.strip()
    return out


_RBA_ANCHOR = re.compile(
    r"<a [^>]*href=\"(?:/statistics/tables/xls(?:-hist)?/|/statistics/historical-data\.html)"
    r"[^\"]*\"[^>]*>(?P<text>[^<]+)</a>",
    re.IGNORECASE,
)
_RBA_TITLE_ID = re.compile(
    r"^(?P<title>.+?)\s*[\u2013\u2014-]\s*(?P<id>[A-Z][0-9]+(?:\.[0-9]+)?)\s*$",
)


def fetch_rba_tables(client: httpx.Client) -> dict[str, str]:
    """Return a mapping of RBA table id (lower-cased) -> current title."""
    resp = client.get(RBA_TABLES_INDEX, timeout=60.0)
    resp.raise_for_status()
    out: dict[str, str] = {}
    for anchor in _RBA_ANCHOR.finditer(resp.text):
        text = html.unescape(anchor.group("text")).strip()
        m = _RBA_TITLE_ID.match(text)
        if not m:
            continue
        table_id = m.group("id").lower()
        title = re.sub(r"\s+", " ", m.group("title")).strip()
        if table_id not in out or len(title) > len(out[table_id]):
            out[table_id] = title
    return out


def _check_url(client: httpx.Client, url: str) -> bool:
    try:
        resp = client.head(url, timeout=30.0, follow_redirects=True)
        if resp.status_code == 405:  # HEAD unsupported
            resp = client.get(url, timeout=30.0, follow_redirects=True)
        return resp.status_code < 400
    except httpx.HTTPError:
        return False


_DASH_RE = re.compile(r"[\u2013\u2014\u2212]")


def _normalise(title: str) -> str:
    collapsed = re.sub(r"\s+", " ", title).strip().casefold()
    return _DASH_RE.sub("-", collapsed)


def audit(
    catalogue: dict,
    live: dict[str, str],
    client: httpx.Client,
    *,
    source_label: str,
    id_key: callable,
) -> tuple[list[str], list[str], list[str]]:
    """Return (drifted, disappeared, new) rows as markdown lines.

    "Disappeared" means both: absent from live index, and the catalogued
    upstream_url no longer 200s. An entry that has fallen off the index but
    whose data file is still reachable is treated as active.
    """
    drifted: list[str] = []
    disappeared: list[str] = []
    catalogued_ids: set[str] = set()

    for entry_id, entry in catalogue.items():
        if entry.get("ceased") or entry.get("discontinued"):
            continue
        audit_meta = entry.get("audit") or {}
        upstream_title = audit_meta.get("upstream_title", "")
        upstream_url = audit_meta.get("upstream_url", "")
        resolved_id = entry.get("upstream_id", entry_id)
        live_id = id_key(resolved_id)
        catalogued_ids.add(live_id)
        live_title = live.get(live_id)
        if live_title is None:
            if upstream_url and _check_url(client, upstream_url):
                continue  # Off the index but data file still live — treat as active.
            disappeared.append(f"| `{entry_id}` | {upstream_title} | *not found in live index* |")
            continue
        if _normalise(live_title) != _normalise(upstream_title):
            drifted.append(f"| `{entry_id}` | {upstream_title} | {live_title} |")

    new_entries = sorted(set(live) - catalogued_ids)
    new_rows = [f"| `{nid}` | {live[nid]} |" for nid in new_entries]
    return drifted, disappeared, new_rows


def _render(
    source_label: str,
    drifted: list[str],
    disappeared: list[str],
    new_rows: list[str],
) -> Iterable[str]:
    yield f"## {source_label}"
    yield ""
    yield "### Drifted (catalogue title differs from live)"
    yield ""
    if drifted:
        yield "| Catalogue ID | Catalogued title | Live title |"
        yield "|---|---|---|"
        yield from drifted
    else:
        yield "_none_"
    yield ""
    yield "### Disappeared (not in live index)"
    yield ""
    if disappeared:
        yield "| Catalogue ID | Catalogued title | Status |"
        yield "|---|---|---|"
        yield from disappeared
    else:
        yield "_none_"
    yield ""
    yield "### New (in live index, not catalogued)"
    yield ""
    if not new_rows:
        yield "_none_"
    elif len(new_rows) > 20:
        yield f"_{len(new_rows)} uncatalogued live entries — informational only; "
        yield "curate selectively via the roadmap. Showing first 10:_"
        yield ""
        yield "| Live ID | Live title |"
        yield "|---|---|"
        yield from new_rows[:10]
    else:
        yield "| Live ID | Live title |"
        yield "|---|---|"
        yield from new_rows
    yield ""


def main() -> int:
    with httpx.Client(headers={"User-Agent": "ausecon-mcp-audit/1.0"}) as client:
        abs_live = fetch_abs_dataflows(client)
        rba_live = fetch_rba_tables(client)

    with httpx.Client(
        headers={"User-Agent": "ausecon-mcp-audit/1.0"}, follow_redirects=True
    ) as client:
        abs_drifted, abs_disappeared, abs_new = audit(
            ABS_CATALOGUE,
            abs_live,
            client,
            source_label="ABS",
            id_key=lambda eid: eid,
        )
        rba_drifted, rba_disappeared, rba_new = audit(
            RBA_CATALOGUE,
            rba_live,
            client,
            source_label="RBA",
            id_key=lambda eid: eid.lower(),
        )

    print("# Catalogue audit report")
    print()
    for line in _render("ABS", abs_drifted, abs_disappeared, abs_new):
        print(line)
    for line in _render("RBA", rba_drifted, rba_disappeared, rba_new):
        print(line)

    has_drift = bool(abs_drifted or abs_disappeared or rba_drifted or rba_disappeared)
    return 1 if has_drift else 0


if __name__ == "__main__":
    sys.exit(main())

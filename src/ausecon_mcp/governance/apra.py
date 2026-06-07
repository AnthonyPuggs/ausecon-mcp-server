from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime
from importlib import resources
from typing import Any
from urllib.parse import urlparse

from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.errors import AuseconParseError
from ausecon_mcp.providers.apra import resolve_apra_download_url_with_fallback

APRA_SEED_FRESHNESS_DAYS = {
    "Monthly": 45,
    "Quarterly": 120,
    "Annual": 400,
}

_TRUSTED_APRA_HOSTS = {"apra.gov.au", "www.apra.gov.au"}
_INSURANCE_AASB17_PUBLICATIONS = {
    "APRA_GENERAL_INSURANCE_PERFORMANCE",
    "APRA_LIFE_INSURANCE_PERFORMANCE",
    "APRA_PHI_PERFORMANCE",
}
_SEED_RESOURCE = "data/apra_url_seeds.json"


def load_apra_seed_manifest() -> dict[str, list[dict[str, Any]]]:
    try:
        text = resources.files("ausecon_mcp").joinpath(_SEED_RESOURCE).read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        return {}
    return json.loads(text)


def audit_apra_governance(
    catalogue: dict[str, dict[str, Any]] | None = None,
    *,
    seed_manifest: dict[str, list[dict[str, Any]]] | None = None,
    landing_pages: dict[str, str] | None = None,
    today: date | None = None,
) -> list[dict[str, Any]]:
    catalogue = catalogue or APRA_CATALOGUE
    seed_manifest = seed_manifest if seed_manifest is not None else load_apra_seed_manifest()
    landing_pages = landing_pages or {}
    today = today or date.today()

    rows = []
    for publication_id in sorted(catalogue):
        entry = catalogue[publication_id]
        seeds = list(seed_manifest.get(publication_id, []))
        issues: list[dict[str, str]] = []
        issues.extend(_audit_entry_shape(publication_id, entry))
        issues.extend(_audit_seed_rows(publication_id, entry, seeds, today=today))
        issues.extend(_audit_aasb17_scope(publication_id, entry))

        resolved_url, resolution_strategy = _resolve_governed_url(
            publication_id,
            entry,
            seeds,
            landing_pages.get(publication_id),
            issues,
        )
        seed_checked_at = _seed_checked_at(seeds)
        audit_last_audited = entry.get("audit", {}).get("last_audited")
        rows.append(
            {
                "publication_id": publication_id,
                "status": _status(issues),
                "issues": issues,
                "resolved_url": resolved_url,
                "resolution_strategy": resolution_strategy,
                "seed_checked_at": seed_checked_at,
                "audit_last_audited": audit_last_audited,
            }
        )
    return rows


def governance_by_publication(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["publication_id"]: row for row in rows}


def _audit_entry_shape(publication_id: str, entry: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("id", "name", "frequency", "landing_url", "link_patterns", "tables", "audit"):
        if not entry.get(field):
            issues.append(
                _issue(
                    "missing_catalogue_field",
                    "error",
                    f"APRA publication {publication_id} is missing catalogue field {field}.",
                )
            )

    audit = entry.get("audit", {})
    for field in ("last_audited", "upstream_url", "upstream_title"):
        if not audit.get(field):
            issues.append(
                _issue(
                    "missing_audit_field",
                    "error",
                    f"APRA publication {publication_id} is missing audit field {field}.",
                )
            )

    for table_id, table in entry.get("tables", {}).items():
        for field in ("sheet", "layout", "title", "frequency"):
            if not table.get(field):
                issues.append(
                    _issue(
                        "table_missing_field",
                        "error",
                        f"APRA table {publication_id}/{table_id} is missing field {field}.",
                    )
                )

    for variant in entry.get("variants", []):
        variant_name = variant.get("name", "(unnamed)")
        table_id = variant.get("apra_table_id")
        if table_id not in entry.get("tables", {}):
            issues.append(
                _issue(
                    "variant_table_missing",
                    "error",
                    f"APRA variant {publication_id}/{variant_name} references unknown table.",
                )
            )
        series_ids = variant.get("apra_series_ids")
        if not isinstance(series_ids, list) or not all(
            isinstance(series_id, str) and series_id for series_id in series_ids
        ):
            issues.append(
                _issue(
                    "variant_series_missing",
                    "error",
                    f"APRA variant {publication_id}/{variant_name} has no wired series IDs.",
                )
            )

    fallback_url = str(entry.get("fallback_url", ""))
    if fallback_url and not _is_trusted_xlsx(fallback_url):
        issues.append(
            _issue(
                "fallback_untrusted_url",
                "error",
                f"APRA publication {publication_id} fallback_url is not a trusted APRA XLSX URL.",
            )
        )
    return issues


def _audit_seed_rows(
    publication_id: str,
    entry: dict[str, Any],
    seeds: list[dict[str, Any]],
    *,
    today: date,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not seeds:
        return [
            _issue(
                "seed_manifest_missing",
                "error",
                f"APRA publication {publication_id} has no bundled URL seed.",
            )
        ]

    for seed in seeds:
        url = str(seed.get("url", ""))
        if not _is_trusted_xlsx(url):
            issues.append(
                _issue(
                    "seed_untrusted_url",
                    "error",
                    f"APRA publication {publication_id} seed URL is not a trusted APRA XLSX URL.",
                )
            )

        checked_at = seed.get("checked_at")
        if not checked_at:
            issues.append(
                _issue(
                    "seed_missing_checked_at",
                    "error",
                    f"APRA publication {publication_id} seed is missing checked_at.",
                )
            )
            continue

        checked_date = _parse_checked_date(str(checked_at))
        if checked_date is None:
            issues.append(
                _issue(
                    "seed_bad_checked_at",
                    "error",
                    f"APRA publication {publication_id} seed checked_at is not ISO datetime.",
                )
            )
            continue

        threshold = APRA_SEED_FRESHNESS_DAYS.get(str(entry.get("frequency")), 400)
        if (today - checked_date).days > threshold:
            issues.append(
                _issue(
                    "seed_stale",
                    "warning",
                    (
                        f"Seed checked_at {checked_at} is older than {threshold} days "
                        f"for {entry.get('frequency')} publication {publication_id}."
                    ),
                )
            )
    return issues


def _audit_aasb17_scope(publication_id: str, entry: dict[str, Any]) -> list[dict[str, str]]:
    has_aasb17 = any(
        item.get("label") == "AASB 17 transition" for item in entry.get("framework_breaks", [])
    )
    expected = publication_id in _INSURANCE_AASB17_PUBLICATIONS
    if has_aasb17 == expected:
        return []
    return [
        _issue(
            "aasb17_scope_mismatch",
            "error",
            f"AASB 17 framework-break scope is wrong for APRA publication {publication_id}.",
        )
    ]


def _resolve_governed_url(
    publication_id: str,
    entry: dict[str, Any],
    seeds: list[dict[str, Any]],
    landing_html: str | None,
    issues: list[dict[str, str]],
) -> tuple[str | None, str | None]:
    governed_entry = deepcopy(entry)
    governed_entry["url_seeds"] = seeds

    if landing_html is not None:
        try:
            url, meta = resolve_apra_download_url_with_fallback(
                landing_html,
                base_url=entry.get("landing_url", ""),
                patterns=list(entry.get("link_patterns", [])),
                publication_id=publication_id,
                entry=governed_entry,
            )
        except AuseconParseError:
            issues.append(
                _issue(
                    "resolution_failed",
                    "error",
                    f"APRA publication {publication_id} could not resolve a trusted XLSX URL.",
                )
            )
            return None, None
        return url, str(meta.get("strategy"))

    for seed in seeds:
        url = str(seed.get("url", ""))
        if _is_trusted_xlsx(url):
            return url, "seed_manifest"

    fallback_url = str(entry.get("fallback_url", ""))
    if _is_trusted_xlsx(fallback_url):
        return fallback_url, "catalogue_fallback"

    issues.append(
        _issue(
            "resolution_failed",
            "error",
            f"APRA publication {publication_id} could not resolve a trusted XLSX URL.",
        )
    )
    return None, None


def _seed_checked_at(seeds: list[dict[str, Any]]) -> str | None:
    values = sorted(str(seed["checked_at"]) for seed in seeds if seed.get("checked_at"))
    return values[0] if values else None


def _parse_checked_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _is_trusted_xlsx(url: str) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return (
        parsed.scheme == "https"
        and hostname in _TRUSTED_APRA_HOSTS
        and parsed.path.lower().endswith(".xlsx")
    )


def _status(issues: list[dict[str, str]]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "fail"
    if any(issue["severity"] == "warning" for issue in issues):
        return "stale"
    return "ok"


def _issue(code: str, severity: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
    }

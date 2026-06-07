from __future__ import annotations

from datetime import date

from ausecon_mcp.catalogue.apra import APRA_CATALOGUE
from ausecon_mcp.governance.apra import audit_apra_governance, load_apra_seed_manifest


def _minimal_catalogue(frequency: str = "Monthly") -> dict[str, dict]:
    return {
        "TEST_PUBLICATION": {
            "id": "TEST_PUBLICATION",
            "name": "Test APRA Publication",
            "frequency": frequency,
            "frequencies": ["M" if frequency == "Monthly" else "Q"],
            "landing_url": "https://www.apra.gov.au/test-publication",
            "link_patterns": [r"test.*xlsx"],
            "fallback_url": "https://www.apra.gov.au/sites/default/files/test.xlsx",
            "tables": {
                "table_1": {
                    "sheet": "Table 1",
                    "layout": "row_records",
                    "title": "Test table",
                    "frequency": frequency,
                }
            },
            "variants": [
                {
                    "name": "test_series",
                    "aliases": ["test series"],
                    "apra_table_id": "table_1",
                    "apra_series_ids": ["TEST_PUBLICATION:table_1:test_series"],
                }
            ],
            "audit": {
                "last_audited": "2026-05-18",
                "upstream_url": "https://www.apra.gov.au/test-publication",
                "upstream_title": "Test APRA Publication",
            },
        }
    }


def test_apra_governance_flags_stale_seed_freshness_without_hard_failure() -> None:
    rows = audit_apra_governance(
        _minimal_catalogue("Monthly"),
        seed_manifest={
            "TEST_PUBLICATION": [
                {
                    "url": "https://www.apra.gov.au/sites/default/files/test.xlsx",
                    "label": "test monthly xlsx",
                    "checked_at": "2026-01-01T00:00:00Z",
                }
            ]
        },
        landing_pages={
            "TEST_PUBLICATION": (
                '<a href="/sites/default/files/test.xlsx">test monthly xlsx</a>'
            )
        },
        today=date(2026, 3, 1),
    )

    assert rows == [
        {
            "publication_id": "TEST_PUBLICATION",
            "status": "stale",
            "issues": [
                {
                    "code": "seed_stale",
                    "severity": "warning",
                    "message": (
                        "Seed checked_at 2026-01-01T00:00:00Z is older than "
                        "45 days for Monthly publication TEST_PUBLICATION."
                    ),
                }
            ],
            "resolved_url": "https://www.apra.gov.au/sites/default/files/test.xlsx",
            "resolution_strategy": "landing_page",
            "seed_checked_at": "2026-01-01T00:00:00Z",
            "audit_last_audited": "2026-05-18",
        }
    ]


def test_apra_governance_rejects_untrusted_or_non_xlsx_urls() -> None:
    catalogue = _minimal_catalogue()
    catalogue["TEST_PUBLICATION"]["fallback_url"] = "https://evil.example/test.csv"

    rows = audit_apra_governance(
        catalogue,
        seed_manifest={
            "TEST_PUBLICATION": [
                {
                    "url": "https://evil.example/test.xlsx",
                    "label": "test monthly xlsx",
                    "checked_at": "2026-02-20T00:00:00Z",
                }
            ]
        },
        landing_pages={"TEST_PUBLICATION": ""},
        today=date(2026, 3, 1),
    )

    assert rows[0]["status"] == "fail"
    assert {issue["code"] for issue in rows[0]["issues"]} >= {
        "seed_untrusted_url",
        "fallback_untrusted_url",
        "resolution_failed",
    }


def test_apra_governance_covers_checked_in_catalogue_and_seed_manifest() -> None:
    rows = audit_apra_governance(
        APRA_CATALOGUE,
        seed_manifest=load_apra_seed_manifest(),
        today=date(2026, 6, 7),
    )

    assert {row["publication_id"] for row in rows} == set(APRA_CATALOGUE)
    assert not [row for row in rows if row["status"] == "fail"]
    assert all(row["audit_last_audited"] for row in rows)
    assert all(row["seed_checked_at"] for row in rows)


def test_apra_governance_keeps_aasb17_scope_to_insurance_performance() -> None:
    rows = audit_apra_governance(
        APRA_CATALOGUE,
        seed_manifest=load_apra_seed_manifest(),
        today=date(2026, 6, 7),
    )

    assert not [
        issue
        for row in rows
        for issue in row["issues"]
        if issue["code"] == "aasb17_scope_mismatch"
    ]

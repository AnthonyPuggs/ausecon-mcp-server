"""Every catalogue entry must carry a fresh `audit` block.

Guards against silent upstream drift: entries without a recent re-verification
should be treated as stale and investigated. Bootstrap tolerance is 24 months;
tighten once governance is routine.
"""

from __future__ import annotations

from datetime import date

import pytest

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE

MAX_AGE_MONTHS = 24


def _iter_entries():
    for entry_id, entry in ABS_CATALOGUE.items():
        yield f"abs/{entry_id}", entry
    for entry_id, entry in RBA_CATALOGUE.items():
        yield f"rba/{entry_id}", entry


@pytest.mark.parametrize(("label", "entry"), list(_iter_entries()))
def test_entry_has_audit_block(label: str, entry: dict) -> None:
    audit = entry.get("audit")
    assert audit is not None, f"{label}: missing audit block"
    for key in ("last_audited", "upstream_url", "upstream_title"):
        assert audit.get(key), f"{label}: audit.{key} missing or empty"


@pytest.mark.parametrize(("label", "entry"), list(_iter_entries()))
def test_audit_last_audited_recent(label: str, entry: dict) -> None:
    audit = entry["audit"]
    last_audited = date.fromisoformat(audit["last_audited"])
    today = date.today()
    months_old = (today.year - last_audited.year) * 12 + (today.month - last_audited.month)
    assert months_old <= MAX_AGE_MONTHS, (
        f"{label}: last_audited {last_audited} is {months_old} months old "
        f"(max {MAX_AGE_MONTHS}); re-run scripts/audit_catalogue.py"
    )

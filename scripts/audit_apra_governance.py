from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ausecon_mcp.catalogue.apra import APRA_CATALOGUE  # noqa: E402
from ausecon_mcp.governance.apra import audit_apra_governance  # noqa: E402


def fetch_landing_pages() -> dict[str, str]:
    pages: dict[str, str] = {}
    with httpx.Client(headers={"User-Agent": "ausecon-apra-governance-audit/1.0"}) as client:
        for publication_id, entry in APRA_CATALOGUE.items():
            response = client.get(entry["landing_url"], timeout=60.0, follow_redirects=True)
            response.raise_for_status()
            pages[publication_id] = response.text
    return pages


def render_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# APRA Governance Audit",
        "",
        "| Publication | Status | Resolution | Seed checked | Issues |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        issue_text = "<br>".join(
            f"{issue['severity']}: {issue['code']} - {issue['message']}"
            for issue in row["issues"]
        )
        if not issue_text:
            issue_text = "-"
        lines.append(
            "| {publication_id} | {status} | {resolution} | {seed_checked} | {issues} |".format(
                publication_id=row["publication_id"],
                status=row["status"],
                resolution=row["resolution_strategy"] or "-",
                seed_checked=row["seed_checked_at"] or "-",
                issues=issue_text,
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit APRA source-governance metadata.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero on hard failures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    rows = audit_apra_governance(landing_pages=fetch_landing_pages())
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(render_markdown(rows), end="")

    if args.check and any(row["status"] == "fail" for row in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

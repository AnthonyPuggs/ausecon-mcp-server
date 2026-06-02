from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = SRC / "ausecon_mcp" / "data" / "apra_url_seeds.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ausecon_mcp.catalogue.apra import APRA_CATALOGUE  # noqa: E402
from ausecon_mcp.providers.apra import resolve_apra_download_url  # noqa: E402


def refresh() -> dict[str, list[dict[str, str]]]:
    seeds: dict[str, list[dict[str, str]]] = {}
    checked_at = _utc_now()
    with httpx.Client(headers={"User-Agent": "ausecon-apra-seed-refresh/1.0"}) as client:
        for publication_id, entry in APRA_CATALOGUE.items():
            response = client.get(entry["landing_url"], timeout=60.0, follow_redirects=True)
            response.raise_for_status()
            url = resolve_apra_download_url(
                response.text,
                base_url=entry["landing_url"],
                patterns=entry["link_patterns"],
            )
            seeds[publication_id] = [
                {
                    "url": url,
                    "label": entry["name"],
                    "checked_at": checked_at,
                }
            ]
    return seeds


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalise_for_check(seeds: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    return {
        publication_id: [
            {key: value for key, value in seed.items() if key != "checked_at"} for seed in seed_rows
        ]
        for publication_id, seed_rows in seeds.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh bundled APRA workbook URL seeds.")
    parser.add_argument("--check", action="store_true", help="Fail if checked-in seeds are stale.")
    args = parser.parse_args()

    rendered = json.dumps(refresh(), indent=2, sort_keys=True) + "\n"
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        current_seeds = json.loads(current) if current else {}
        refreshed_seeds = json.loads(rendered)
        if _normalise_for_check(current_seeds) != _normalise_for_check(refreshed_seeds):
            print(f"{OUTPUT.relative_to(ROOT)} is stale. Run this script without --check.")
            return 1
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

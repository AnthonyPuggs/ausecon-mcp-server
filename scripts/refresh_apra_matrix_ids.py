"""Refresh the checked-in list of series ids the live APRA matrix tables produce.

Matrix tables take their series ids from worksheet headings and indentation, so the list
is what lets the nightly integration run notice when a change at APRA renames or removes
a series. Run this after a deliberate id change, or after confirming that APRA really did
retire a row:

    uv run python scripts/refresh_apra_matrix_ids.py          # rewrite the list
    uv run python scripts/refresh_apra_matrix_ids.py --check  # exit 1 if it is stale
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "integration_tests" / "apra_matrix_series_ids.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ausecon_mcp.catalogue.apra import APRA_CATALOGUE  # noqa: E402
from ausecon_mcp.providers.apra import APRAProvider  # noqa: E402


async def refresh() -> dict[str, list[str]]:
    provider = APRAProvider()
    series_ids: dict[str, list[str]] = {}
    for publication_id, entry in sorted(APRA_CATALOGUE.items()):
        for table_id, table_map in sorted(entry["tables"].items()):
            if table_map["layout"] != "matrix":
                continue
            payload = await provider.get_data(publication_id, table_id=table_id)
            series_ids[f"{publication_id}:{table_id}"] = sorted(
                series["series_id"] for series in payload["series"]
            )
    return series_ids


def _describe_differences(current: dict[str, list[str]], live: dict[str, list[str]]) -> list[str]:
    lines: list[str] = []
    for table in sorted(current.keys() | live.keys()):
        before, after = set(current.get(table, [])), set(live.get(table, []))
        lines.extend(f"{table}: no longer produced: {series_id}" for series_id in before - after)
        lines.extend(f"{table}: new: {series_id}" for series_id in after - before)
    return sorted(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh the live APRA matrix series id list.")
    parser.add_argument("--check", action="store_true", help="Fail if the list is stale.")
    args = parser.parse_args()

    live = asyncio.run(refresh())
    if args.check:
        current = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
        differences = _describe_differences(current, live)
        for line in differences:
            print(line)
        return 1 if differences else 0

    OUTPUT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {sum(len(ids) for ids in live.values())} series ids to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

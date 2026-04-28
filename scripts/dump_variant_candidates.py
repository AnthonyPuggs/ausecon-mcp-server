"""Fetch every curated RBA table and ABS dataflow, and write a reference
document summarising the series / dimensions available for each.

The output at ``docs/variant_candidates.md`` is the maintainer's working
document when hand-populating ``variants[*].rba_series_ids`` and
``variants[*].abs_key`` ahead of the v0.4.0 semantic resolver.

This is a dev-only tool. It is read-only against ABS and RBA endpoints but
does hit the network — run it locally, review the output, commit the
resulting docs update alongside catalogue edits.

Usage:

    uv run python scripts/dump_variant_candidates.py

Optional flags:

    --source abs|rba       limit to one provider
    --ids CPI,LF,g1        limit to a subset of catalogue ids
    --output PATH          override the default output path
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE  # noqa: E402
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE  # noqa: E402
from ausecon_mcp.catalogue.resolver import (  # noqa: E402
    resolve_abs_dataflow_id,
    resolve_abs_structure_id,
)
from ausecon_mcp.providers.abs import ABSProvider  # noqa: E402
from ausecon_mcp.providers.rba import RBAProvider  # noqa: E402

DEFAULT_OUTPUT = ROOT / "docs" / "variant_candidates.md"


async def _dump_rba(ids: set[str] | None) -> list[str]:
    provider = RBAProvider()
    lines: list[str] = ["# RBA — series candidates per table", ""]
    for table_id, entry in sorted(RBA_CATALOGUE.items()):
        if ids is not None and table_id not in ids:
            continue
        print(f"[rba] fetching {table_id}", file=sys.stderr)
        lines.append(f"## `{table_id}` — {entry['name']}")
        lines.append("")
        lines.append(f"- category: `{entry['category']}` · frequency: `{entry['frequency']}`")
        declared = ", ".join(v["name"] for v in entry.get("variants", []))
        lines.append(f"- declared variants: {declared or '_none_'}")
        lines.append("")
        try:
            payload = await provider.get_table(table_id)
        except Exception as exc:  # noqa: BLE001 — surface any upstream/parse failure
            lines.append(f"> **fetch failed:** {exc}")
            lines.append("")
            continue
        series_rows = payload.get("series", [])
        if not series_rows:
            lines.append("> no series rows")
            lines.append("")
            continue
        lines.append("| series_id | label | description | type | unit |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in series_rows:
            dimensions = row.get("dimensions", {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(row.get("series_id", "")),
                        _cell(row.get("label", "")),
                        _cell((dimensions.get("description") or {}).get("label", "")),
                        _cell((dimensions.get("type") or {}).get("label", "")),
                        _cell(row.get("unit", "")),
                    ]
                )
                + " |"
            )
        lines.append("")
    return lines


async def _dump_abs(ids: set[str] | None) -> list[str]:
    provider = ABSProvider()
    lines: list[str] = ["# ABS — dimensions and codelists per dataflow", ""]
    for dataflow_id, entry in sorted(ABS_CATALOGUE.items()):
        if ids is not None and dataflow_id not in ids:
            continue
        print(f"[abs] fetching {dataflow_id}", file=sys.stderr)
        lines.append(f"## `{dataflow_id}` — {entry['name']}")
        lines.append("")
        declared = ", ".join(v["name"] for v in entry.get("variants", []))
        lines.append(f"- declared variants: {declared or '_none_'}")
        lines.append("")
        try:
            structure_id = resolve_abs_structure_id(dataflow_id)
            if structure_id == dataflow_id:
                structure_id = resolve_abs_dataflow_id(dataflow_id)
            structure = await provider.get_dataset_structure(structure_id)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"> **fetch failed:** {exc}")
            lines.append("")
            continue
        for dim in structure.get("dimensions", []):
            lines.append(
                f"### Dimension `{dim['id']}` (position {dim['position']}) — {dim['name']}"
            )
            lines.append("")
            values = dim.get("values", [])
            if not values:
                lines.append("> no codelist values")
                lines.append("")
                continue
            lines.append("| code | label |")
            lines.append("| --- | --- |")
            for value in values:
                lines.append(f"| `{value['code']}` | {_cell(value['label'])} |")
            lines.append("")
    return lines


def _cell(value: Any) -> str:
    text = str(value).replace("|", "\\|").replace("\n", " ").strip()
    return text or "—"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("abs", "rba", "both"), default="both")
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated dataset/table ids to limit the dump to.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    ids = {tok.strip() for tok in args.ids.split(",")} if args.ids else None

    sections: list[str] = []
    if args.source in ("rba", "both"):
        sections.extend(await _dump_rba(ids))
    if args.source in ("abs", "both"):
        sections.extend(await _dump_abs(ids))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(f"wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(_main())

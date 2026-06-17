from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_MANIFEST = Path(__file__).resolve().parent / "golden_values.yaml"
_SOURCES = {"abs", "rba", "apra"}


@dataclass(frozen=True)
class GoldenEntry:
    id: str
    source: str
    identifier: str
    key: str
    start: str
    end: str
    match_date: str
    expected_value: float
    tolerance: float
    note: str
    table_id: str | None = None


def load_golden_values(path: Path = _MANIFEST) -> list[GoldenEntry]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("golden_values.yaml must be a non-empty list of entries")

    entries: list[GoldenEntry] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"entry {index} is not a mapping")
        try:
            entry = GoldenEntry(**item)
        except TypeError as exc:
            raise ValueError(f"entry {index} has bad fields: {exc}") from exc

        if entry.id in seen_ids:
            raise ValueError(f"duplicate golden id {entry.id!r}")
        seen_ids.add(entry.id)

        if entry.source not in _SOURCES:
            raise ValueError(f"{entry.id}: source must be one of {sorted(_SOURCES)}")
        for field in ("id", "identifier", "key", "start", "end", "match_date", "note"):
            value = getattr(entry, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{entry.id}: {field} must be a non-empty string")
        if not isinstance(entry.expected_value, (int, float)) or isinstance(
            entry.expected_value, bool
        ):
            raise ValueError(f"{entry.id}: expected_value must be a number")
        if not isinstance(entry.tolerance, (int, float)) or isinstance(entry.tolerance, bool):
            raise ValueError(f"{entry.id}: tolerance must be a number")
        if entry.tolerance < 0:
            raise ValueError(f"{entry.id}: tolerance must be >= 0")
        if "REPLACE_WITH" in entry.key:
            raise ValueError(f"{entry.id}: unresolved placeholder key")
        entries.append(entry)
    return entries

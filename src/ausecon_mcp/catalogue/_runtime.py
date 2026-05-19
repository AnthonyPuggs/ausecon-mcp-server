from __future__ import annotations

from typing import Any


def strip_unwired_variants(
    catalogue: dict[str, dict[str, Any]], *, key_name: str
) -> dict[str, dict[str, Any]]:
    """Return a runtime catalogue with only fully wired variants exposed."""
    normalised: dict[str, dict[str, Any]] = {}
    for entry_id, entry in catalogue.items():
        variants = entry.get("variants", [])
        normalised[entry_id] = {
            **entry,
            "variants": [variant for variant in variants if variant.get(key_name) is not None],
        }
    return normalised

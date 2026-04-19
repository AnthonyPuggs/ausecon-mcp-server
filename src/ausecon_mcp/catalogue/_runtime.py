from __future__ import annotations

from copy import deepcopy
from typing import Any


def strip_unwired_variants(
    catalogue: dict[str, dict[str, Any]], *, key_name: str
) -> dict[str, dict[str, Any]]:
    """Return a runtime catalogue with only fully wired variants exposed."""
    normalised = deepcopy(catalogue)
    for entry in normalised.values():
        variants = entry.get("variants", [])
        entry["variants"] = [variant for variant in variants if variant.get(key_name) is not None]
    return normalised

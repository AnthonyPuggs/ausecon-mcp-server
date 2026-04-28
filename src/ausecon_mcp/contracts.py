from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def response_schema() -> dict[str, Any]:
    """Load the checked-in retrieval response contract."""
    here = Path(__file__).resolve()
    candidates = (
        here.parents[2] / "schemas" / "response.schema.json",
        here.parents[1] / "schemas" / "response.schema.json",
    )
    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not locate response.schema.json; checked {checked}")


def response_output_schema() -> dict[str, Any]:
    """Return a mutable copy suitable for FastMCP tool registration."""
    return deepcopy(response_schema())

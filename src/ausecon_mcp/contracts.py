from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

_SCHEMA_DIR = "schemas"
_SCHEMA_FILE = "response.schema.json"


def _load_schema_text() -> str:
    checked: list[str] = []

    try:
        resource = resources.files("ausecon_mcp").joinpath(_SCHEMA_DIR).joinpath(_SCHEMA_FILE)
        checked.append(str(resource))
        if resource.is_file():
            return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        checked.append(f"package resource unavailable: {type(exc).__name__}")

    here = Path(__file__).resolve()
    candidates = (
        here.parent / _SCHEMA_DIR / _SCHEMA_FILE,
        here.parents[2] / _SCHEMA_DIR / _SCHEMA_FILE,
    )
    for path in candidates:
        checked.append(str(path))
        if path.is_file():
            return path.read_text(encoding="utf-8")

    raise FileNotFoundError(f"Could not locate {_SCHEMA_FILE}; checked {', '.join(checked)}")


@lru_cache(maxsize=1)
def response_schema() -> dict[str, Any]:
    """Load the checked-in retrieval response contract."""
    return json.loads(_load_schema_text())


def response_output_schema() -> dict[str, Any]:
    """Return a mutable copy suitable for FastMCP tool registration."""
    return deepcopy(response_schema())

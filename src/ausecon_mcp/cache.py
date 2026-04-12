from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any


@dataclass
class _CacheEntry:
    expires_at: float
    value: Any


class TTLCache:
    def __init__(self) -> None:
        self._entries: dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at < monotonic():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> Any:
        self._entries[key] = _CacheEntry(expires_at=monotonic() + ttl_seconds, value=value)
        return value

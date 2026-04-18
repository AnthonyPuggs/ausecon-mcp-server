from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any

from platformdirs import user_cache_dir

from ausecon_mcp.logging import get_logger

_SCHEMA_VERSION = 1
_logger = get_logger("cache")


@dataclass
class _CacheEntry:
    cached_at: float
    expires_at: float
    value: Any


class TTLCache:
    def __init__(
        self,
        *,
        disk_dir: str | os.PathLike[str] | None = None,
        disabled: bool | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._entries: dict[str, _CacheEntry] = {}
        self._ttl_seconds = ttl_seconds

        if disabled is None:
            disabled = os.environ.get("AUSECON_CACHE_DISABLED", "").lower() in {"1", "true", "yes"}
        self._disabled = disabled

        if disk_dir is None:
            disk_dir = os.environ.get("AUSECON_CACHE_DIR") or user_cache_dir("ausecon-mcp")
        self._disk_dir = Path(disk_dir)

    def get(self, key: str) -> Any | None:
        if self._disabled:
            return None

        entry = self._entries.get(key)
        now = time()
        if entry is not None:
            if entry.expires_at >= now:
                return deepcopy(entry.value)
            self._entries.pop(key, None)

        disk = self._read_disk(key)
        if disk is None:
            return None
        if disk.expires_at < now:
            return None

        self._entries[key] = disk
        return deepcopy(disk.value)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> Any:
        if self._disabled:
            return value

        ttl = self._ttl_seconds if ttl_seconds is None else ttl_seconds
        now = time()
        expires_at = now + ttl
        entry = _CacheEntry(cached_at=now, expires_at=expires_at, value=value)
        self._entries[key] = entry
        self._write_disk(key, entry)
        return value

    def get_stale(self, key: str) -> dict[str, Any] | None:
        if self._disabled:
            return None

        entry = self._entries.get(key) or self._read_disk(key)
        if entry is None:
            return None
        return {
            "value": deepcopy(entry.value),
            "cached_at": entry.cached_at,
            "expires_at": entry.expires_at,
        }

    def _path_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._disk_dir / f"{digest}.json"

    def _read_disk(self, key: str) -> _CacheEntry | None:
        path = self._path_for(key)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text())
            if data.get("schema") != _SCHEMA_VERSION:
                raise ValueError(f"unsupported cache schema: {data.get('schema')!r}")
            return _CacheEntry(
                cached_at=float(data["cached_at"]),
                expires_at=float(data["expires_at"]),
                value=data["value"],
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            _logger.warning(
                "cache.disk_error",
                extra={"op": "read", "error_type": type(exc).__name__},
            )
            self._unlink(path)
            return None

    def _write_disk(self, key: str, entry: _CacheEntry) -> None:
        path = self._path_for(key)
        payload = {
            "schema": _SCHEMA_VERSION,
            "cached_at": entry.cached_at,
            "expires_at": entry.expires_at,
            "value": entry.value,
        }
        try:
            self._disk_dir.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(prefix=".cache-", dir=self._disk_dir)
            try:
                with os.fdopen(fd, "w") as fh:
                    json.dump(payload, fh)
                os.replace(tmp_name, path)
            except Exception:
                self._unlink(Path(tmp_name))
                raise
        except OSError as exc:
            _logger.warning(
                "cache.disk_error",
                extra={"op": "write", "error_type": type(exc).__name__},
            )

    @staticmethod
    def _unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

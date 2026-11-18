from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any

from platformdirs import user_cache_dir

from ausecon_mcp.logging import get_logger

_SCHEMA_VERSION = 1
# Each cache keeps at most this much serialised JSON in memory. Parsed Python objects take
# roughly 2-5x their JSON size and the hosted instance has 512 MB, so this stays well clear of
# that even with every provider cache full. Disk remains the complete store; eviction only costs
# a disk read on the next hit.
_DEFAULT_MAX_MEMORY_BYTES = 16 * 1024 * 1024
_MAX_MEMORY_ENV = "AUSECON_CACHE_MAX_MEMORY_MB"
_logger = get_logger("cache")


def _default_disk_dir() -> Path:
    return Path(user_cache_dir("ausecon-mcp")).expanduser().resolve(strict=False)


def _max_memory_bytes_from_env() -> int:
    raw = os.environ.get(_MAX_MEMORY_ENV, "").strip()
    if not raw:
        return _DEFAULT_MAX_MEMORY_BYTES
    try:
        megabytes = float(raw)
    except ValueError:
        _logger.warning("cache.invalid_memory_budget", extra={"value": raw})
        return _DEFAULT_MAX_MEMORY_BYTES
    return max(0, int(megabytes * 1024 * 1024))


@dataclass
class _CacheEntry:
    cached_at: float
    expires_at: float
    value: Any
    size: int = 0


class TTLCache:
    def __init__(
        self,
        *,
        disabled: bool | None = None,
        ttl_seconds: int = 3600,
        max_memory_bytes: int | None = None,
    ) -> None:
        # Least recently used first. Bounded by serialised size, not entry count, because one
        # APRA table can be tens of MB while most entries are a few hundred KB.
        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._memory_bytes = 0
        self._max_memory_bytes = (
            _max_memory_bytes_from_env() if max_memory_bytes is None else max_memory_bytes
        )
        self._ttl_seconds = ttl_seconds
        self._disk_enabled = True

        if disabled is None:
            disabled = os.environ.get("AUSECON_CACHE_DISABLED", "").lower() in {"1", "true", "yes"}
        self._disabled = disabled

        # Keep on-disk cache writes inside the app-owned cache root.
        self._disk_dir = _default_disk_dir()

    def get(self, key: str) -> Any | None:
        if self._disabled:
            return None

        entry = self._entries.get(key)
        now = time()
        if entry is not None:
            if entry.expires_at >= now:
                self._entries.move_to_end(key)
                return deepcopy(entry.value)
            self._forget(key)

        if not self._disk_enabled:
            return None

        disk = self._read_disk(key)
        if disk is None:
            return None
        if disk.expires_at < now:
            return None

        self._remember(key, disk)
        return deepcopy(disk.value)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> Any:
        if self._disabled:
            return value

        ttl = self._ttl_seconds if ttl_seconds is None else ttl_seconds
        now = time()
        expires_at = now + ttl
        entry = _CacheEntry(cached_at=now, expires_at=expires_at, value=value)
        serialised = self._serialise(entry)
        entry.size = len(serialised)
        self._remember(key, entry)
        self._write_disk(key, serialised)
        # Return a private copy (as get() does) so callers may mutate the result
        # freely without aliasing the stored entry. The cache is the sole copy owner.
        return deepcopy(value)

    async def aget(self, key: str) -> Any | None:
        if self._disabled:
            return None
        now = time()
        entry = self._entries.get(key)
        if entry is not None:
            if entry.expires_at >= now:
                self._entries.move_to_end(key)
                return deepcopy(entry.value)
            self._forget(key)
        if not self._disk_enabled:
            return None
        disk = await asyncio.to_thread(self._read_disk, key)
        if disk is None or disk.expires_at < now:
            return None
        self._remember(key, disk)
        return deepcopy(disk.value)

    async def aset(self, key: str, value: Any, ttl_seconds: int | None = None) -> Any:
        if self._disabled:
            return value
        ttl = self._ttl_seconds if ttl_seconds is None else ttl_seconds
        now = time()
        entry = _CacheEntry(cached_at=now, expires_at=now + ttl, value=value)
        serialised = await asyncio.to_thread(self._serialise, entry)
        entry.size = len(serialised)
        self._remember(key, entry)
        await asyncio.to_thread(self._write_disk, key, serialised)
        return deepcopy(value)

    def get_stale(self, key: str) -> dict[str, Any] | None:
        if self._disabled:
            return None

        entry = self._entries.get(key)
        if entry is None:
            if not self._disk_enabled:
                return None
            entry = self._read_disk(key)
        if entry is None:
            return None
        return {
            "value": deepcopy(entry.value),
            "cached_at": entry.cached_at,
            "expires_at": entry.expires_at,
        }

    def _remember(self, key: str, entry: _CacheEntry) -> None:
        self._forget(key)
        if entry.size > self._max_memory_bytes:
            return  # Too big to hold in memory; the disk copy still serves it.
        self._entries[key] = entry
        self._memory_bytes += entry.size
        while self._memory_bytes > self._max_memory_bytes:
            _, evicted = self._entries.popitem(last=False)
            self._memory_bytes -= evicted.size

    def _forget(self, key: str) -> None:
        entry = self._entries.pop(key, None)
        if entry is not None:
            self._memory_bytes -= entry.size

    @staticmethod
    def _serialise(entry: _CacheEntry) -> str:
        return json.dumps(
            {
                "schema": _SCHEMA_VERSION,
                "cached_at": entry.cached_at,
                "expires_at": entry.expires_at,
                "value": entry.value,
            }
        )

    def _path_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._disk_dir / f"{digest}.json"

    def _read_disk(self, key: str) -> _CacheEntry | None:
        try:
            path = self._checked_path(self._path_for(key))
        except ValueError as exc:
            _logger.warning(
                "cache.disk_error",
                extra={"op": "read", "error_type": type(exc).__name__},
            )
            return None
        try:
            if not path.is_file():
                return None
            text = path.read_text()
            data = json.loads(text)
            if data.get("schema") != _SCHEMA_VERSION:
                raise ValueError(f"unsupported cache schema: {data.get('schema')!r}")
            return _CacheEntry(
                cached_at=float(data["cached_at"]),
                expires_at=float(data["expires_at"]),
                value=data["value"],
                size=len(text),
            )
        except PermissionError as exc:
            self._disable_disk("read", exc)
            return None
        except (OSError, ValueError, KeyError, TypeError) as exc:
            _logger.warning(
                "cache.disk_error",
                extra={"op": "read", "error_type": type(exc).__name__},
            )
            self._unlink(path)
            return None

    def _write_disk(self, key: str, serialised: str) -> None:
        if not self._disk_enabled:
            return
        path = self._path_for(key)
        tmp_path: Path | None = None
        try:
            self._disk_dir.mkdir(parents=True, exist_ok=True)
            checked_path = self._checked_path(path)
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self._disk_dir,
                prefix=".cache-",
                delete=False,
            ) as fh:
                tmp_path = self._checked_path(Path(fh.name))
                fh.write(serialised)
            try:
                os.replace(tmp_path, checked_path)
            except Exception:
                if tmp_path is not None:
                    self._unlink(tmp_path)
                raise
        except PermissionError as exc:
            if tmp_path is not None:
                self._unlink(tmp_path)
            self._disable_disk("write", exc)
        except (OSError, ValueError) as exc:
            _logger.warning(
                "cache.disk_error",
                extra={"op": "write", "error_type": type(exc).__name__},
            )

    def _disable_disk(self, op: str, exc: Exception) -> None:
        if not self._disk_enabled:
            return
        self._disk_enabled = False
        _logger.debug(
            "cache.disk_disabled",
            extra={"op": op, "error_type": type(exc).__name__},
        )

    def _checked_path(self, path: Path) -> Path:
        resolved_path = Path(path).expanduser().resolve(strict=False)
        resolved_path.relative_to(self._disk_dir)
        return resolved_path

    def _unlink(self, path: Path) -> None:
        try:
            self._checked_path(path).unlink(missing_ok=True)
        except (OSError, ValueError):
            pass

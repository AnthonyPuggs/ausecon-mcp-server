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


def _default_disk_dir() -> Path:
    return Path(user_cache_dir("ausecon-mcp")).expanduser().resolve(strict=False)


@dataclass
class _CacheEntry:
    cached_at: float
    expires_at: float
    value: Any


class TTLCache:
    def __init__(
        self,
        *,
        disabled: bool | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self._entries: dict[str, _CacheEntry] = {}
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
                return deepcopy(entry.value)
            self._entries.pop(key, None)

        if not self._disk_enabled:
            return None

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
            data = json.loads(path.read_text())
            if data.get("schema") != _SCHEMA_VERSION:
                raise ValueError(f"unsupported cache schema: {data.get('schema')!r}")
            return _CacheEntry(
                cached_at=float(data["cached_at"]),
                expires_at=float(data["expires_at"]),
                value=data["value"],
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

    def _write_disk(self, key: str, entry: _CacheEntry) -> None:
        if not self._disk_enabled:
            return
        path = self._path_for(key)
        payload = {
            "schema": _SCHEMA_VERSION,
            "cached_at": entry.cached_at,
            "expires_at": entry.expires_at,
            "value": entry.value,
        }
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
                json.dump(payload, fh)
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

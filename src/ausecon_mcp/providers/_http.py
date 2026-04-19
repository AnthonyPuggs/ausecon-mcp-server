from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

import httpx

_HOMEPAGE = "https://github.com/AnthonyPuggs/ausecon-mcp-server"


def resolve_version() -> str:
    try:
        return _pkg_version("ausecon-mcp-server")
    except PackageNotFoundError:
        try:
            from ausecon_mcp._version import __version__

            return __version__ or "unknown"
        except ImportError:
            return "unknown"


def build_user_agent() -> str:
    return f"ausecon-mcp-server/{resolve_version()} (+{_HOMEPAGE})"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_client(timeout: float = 30.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, headers={"User-Agent": build_user_agent()})

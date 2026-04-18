from __future__ import annotations

import sys
from pathlib import Path

import pytest

import ausecon_mcp.cache as cache_module

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _isolated_cache_dir(tmp_path, monkeypatch):
    """Point the cache at a per-test tmp dir so unit tests never touch the real cache."""
    cache_dir = tmp_path / "ausecon-cache"
    monkeypatch.setattr(cache_module, "_default_disk_dir", lambda: cache_dir)
    monkeypatch.delenv("AUSECON_CACHE_DIR", raising=False)
    monkeypatch.delenv("AUSECON_CACHE_DISABLED", raising=False)
    yield cache_dir

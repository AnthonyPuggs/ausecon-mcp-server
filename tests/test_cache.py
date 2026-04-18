from __future__ import annotations

import json
import time

import pytest

from ausecon_mcp.cache import TTLCache


def test_cache_round_trip_in_memory() -> None:
    cache = TTLCache(ttl_seconds=60)

    cache.set("k", {"v": 1})

    assert cache.get("k") == {"v": 1}


def test_cache_returns_deep_copies() -> None:
    cache = TTLCache(ttl_seconds=60)
    payload = {"series": [{"id": "a"}]}
    cache.set("k", payload)

    out = cache.get("k")
    out["series"].append({"id": "mutated"})

    assert cache.get("k") == {"series": [{"id": "a"}]}


def test_cache_persists_to_disk_across_instances(tmp_path) -> None:
    disk = tmp_path / "cache"
    first = TTLCache(disk_dir=disk, ttl_seconds=60)
    first.set("k", {"v": 1})

    second = TTLCache(disk_dir=disk, ttl_seconds=60)

    assert second.get("k") == {"v": 1}


def test_cache_expired_disk_entry_is_a_miss(tmp_path) -> None:
    disk = tmp_path / "cache"
    cache = TTLCache(disk_dir=disk, ttl_seconds=1)
    cache.set("k", {"v": 1})

    # Force expiry by rewriting the stored expires_at to the past.
    (file,) = disk.glob("*.json")
    data = json.loads(file.read_text())
    data["expires_at"] = time.time() - 10
    file.write_text(json.dumps(data))

    fresh = TTLCache(disk_dir=disk, ttl_seconds=1)
    assert fresh.get("k") is None


def test_get_stale_returns_expired_value_with_timestamps(tmp_path) -> None:
    disk = tmp_path / "cache"
    cache = TTLCache(disk_dir=disk, ttl_seconds=1)
    cache.set("k", {"v": 1})

    (file,) = disk.glob("*.json")
    data = json.loads(file.read_text())
    data["expires_at"] = time.time() - 10
    file.write_text(json.dumps(data))

    fresh = TTLCache(disk_dir=disk, ttl_seconds=1)
    stale = fresh.get_stale("k")

    assert stale is not None
    assert stale["value"] == {"v": 1}
    assert stale["cached_at"] == data["cached_at"]
    assert stale["expires_at"] == data["expires_at"]


def test_get_stale_is_deep_copy(tmp_path) -> None:
    disk = tmp_path / "cache"
    cache = TTLCache(disk_dir=disk, ttl_seconds=60)
    cache.set("k", {"nested": [1, 2]})

    stale = cache.get_stale("k")
    stale["value"]["nested"].append(99)

    assert cache.get("k") == {"nested": [1, 2]}


def test_get_stale_returns_none_when_missing(tmp_path) -> None:
    cache = TTLCache(disk_dir=tmp_path / "cache", ttl_seconds=60)
    assert cache.get_stale("nope") is None


def test_corrupt_json_self_heals(tmp_path) -> None:
    disk = tmp_path / "cache"
    cache = TTLCache(disk_dir=disk, ttl_seconds=60)
    cache.set("k", {"v": 1})

    (file,) = disk.glob("*.json")
    file.write_text("{ not json")

    fresh = TTLCache(disk_dir=disk, ttl_seconds=60)
    assert fresh.get("k") is None
    assert not file.exists()


def test_schema_mismatch_self_heals(tmp_path) -> None:
    disk = tmp_path / "cache"
    cache = TTLCache(disk_dir=disk, ttl_seconds=60)
    cache.set("k", {"v": 1})

    (file,) = disk.glob("*.json")
    data = json.loads(file.read_text())
    data["schema"] = 999
    file.write_text(json.dumps(data))

    fresh = TTLCache(disk_dir=disk, ttl_seconds=60)
    assert fresh.get("k") is None
    assert not file.exists()


def test_disabled_cache_never_hits(tmp_path) -> None:
    cache = TTLCache(disk_dir=tmp_path / "cache", disabled=True, ttl_seconds=60)

    cache.set("k", {"v": 1})

    assert cache.get("k") is None
    assert cache.get_stale("k") is None


def test_disabled_env_var_also_disables(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AUSECON_CACHE_DISABLED", "1")
    cache = TTLCache(disk_dir=tmp_path / "cache", ttl_seconds=60)

    cache.set("k", {"v": 1})
    assert cache.get("k") is None


def test_cache_dir_env_override(monkeypatch, tmp_path) -> None:
    override = tmp_path / "custom-cache"
    monkeypatch.setenv("AUSECON_CACHE_DIR", str(override))
    cache = TTLCache(ttl_seconds=60)

    cache.set("k", {"v": 1})

    assert any(override.glob("*.json"))


def test_disk_write_failure_is_fail_soft(tmp_path) -> None:
    bad_dir = tmp_path / "readonly" / "cache"
    bad_dir.parent.mkdir()
    bad_dir.parent.chmod(0o500)
    try:
        cache = TTLCache(disk_dir=bad_dir, ttl_seconds=60)
        cache.set("k", {"v": 1})
        assert cache.get("k") == {"v": 1}
    finally:
        bad_dir.parent.chmod(0o700)


def test_set_returns_stored_value() -> None:
    cache = TTLCache(ttl_seconds=60)

    assert cache.set("k", {"v": 1}) == {"v": 1}


@pytest.mark.parametrize("ttl", [0, -1])
def test_zero_or_negative_ttl_expires_immediately(ttl, tmp_path) -> None:
    cache = TTLCache(disk_dir=tmp_path / "cache", ttl_seconds=ttl)
    cache.set("k", {"v": 1})

    assert cache.get("k") is None

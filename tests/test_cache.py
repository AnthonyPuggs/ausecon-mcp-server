from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import pytest

import ausecon_mcp.cache as cache_module
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


def test_cache_persists_to_disk_across_instances(_isolated_cache_dir: Path) -> None:
    first = TTLCache(ttl_seconds=60)
    first.set("k", {"v": 1})

    second = TTLCache(ttl_seconds=60)

    assert second.get("k") == {"v": 1}


def test_cache_expired_disk_entry_is_a_miss(_isolated_cache_dir: Path) -> None:
    cache = TTLCache(ttl_seconds=1)
    cache.set("k", {"v": 1})

    # Force expiry by rewriting the stored expires_at to the past.
    (file,) = _isolated_cache_dir.glob("*.json")
    data = json.loads(file.read_text())
    data["expires_at"] = time.time() - 10
    file.write_text(json.dumps(data))

    fresh = TTLCache(ttl_seconds=1)
    assert fresh.get("k") is None


def test_get_stale_returns_expired_value_with_timestamps(_isolated_cache_dir: Path) -> None:
    cache = TTLCache(ttl_seconds=1)
    cache.set("k", {"v": 1})

    (file,) = _isolated_cache_dir.glob("*.json")
    data = json.loads(file.read_text())
    data["expires_at"] = time.time() - 10
    file.write_text(json.dumps(data))

    fresh = TTLCache(ttl_seconds=1)
    stale = fresh.get_stale("k")

    assert stale is not None
    assert stale["value"] == {"v": 1}
    assert stale["cached_at"] == data["cached_at"]
    assert stale["expires_at"] == data["expires_at"]


def test_get_stale_is_deep_copy() -> None:
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", {"nested": [1, 2]})

    stale = cache.get_stale("k")
    stale["value"]["nested"].append(99)

    assert cache.get("k") == {"nested": [1, 2]}


def test_get_stale_returns_none_when_missing() -> None:
    cache = TTLCache(ttl_seconds=60)
    assert cache.get_stale("nope") is None


def test_corrupt_json_self_heals(_isolated_cache_dir: Path) -> None:
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", {"v": 1})

    (file,) = _isolated_cache_dir.glob("*.json")
    file.write_text("{ not json")

    fresh = TTLCache(ttl_seconds=60)
    assert fresh.get("k") is None
    assert not file.exists()


def test_schema_mismatch_self_heals(_isolated_cache_dir: Path) -> None:
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", {"v": 1})

    (file,) = _isolated_cache_dir.glob("*.json")
    data = json.loads(file.read_text())
    data["schema"] = 999
    file.write_text(json.dumps(data))

    fresh = TTLCache(ttl_seconds=60)
    assert fresh.get("k") is None
    assert not file.exists()


def test_disabled_cache_never_hits() -> None:
    cache = TTLCache(disabled=True, ttl_seconds=60)

    cache.set("k", {"v": 1})

    assert cache.get("k") is None
    assert cache.get_stale("k") is None


def test_disabled_env_var_also_disables(monkeypatch) -> None:
    monkeypatch.setenv("AUSECON_CACHE_DISABLED", "1")
    cache = TTLCache(ttl_seconds=60)

    cache.set("k", {"v": 1})
    assert cache.get("k") is None


def test_cache_dir_env_override_is_ignored(
    monkeypatch, tmp_path, _isolated_cache_dir: Path
) -> None:
    override = tmp_path / "custom-cache"
    monkeypatch.setenv("AUSECON_CACHE_DIR", str(override))
    cache = TTLCache(ttl_seconds=60)

    cache.set("k", {"v": 1})

    assert any(_isolated_cache_dir.glob("*.json"))
    assert not override.exists()


def test_disk_write_failure_is_fail_soft(tmp_path, monkeypatch) -> None:
    bad_dir = tmp_path / "readonly" / "cache"
    bad_dir.parent.mkdir()
    bad_dir.parent.chmod(0o500)
    try:
        monkeypatch.setattr(cache_module, "_default_disk_dir", lambda: bad_dir)
        cache = TTLCache(ttl_seconds=60)
        cache.set("k", {"v": 1})
        assert cache.get("k") == {"v": 1}
    finally:
        bad_dir.parent.chmod(0o700)


def test_permission_denied_write_disables_disk_layer_once(caplog, monkeypatch) -> None:
    cache = TTLCache(ttl_seconds=60)
    attempts = 0

    def raising_named_tempfile(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        raise PermissionError("sandbox denied cache write")

    monkeypatch.setattr(cache_module.tempfile, "NamedTemporaryFile", raising_named_tempfile)

    with caplog.at_level(logging.WARNING, logger="ausecon_mcp.cache"):
        cache.set("first", {"v": 1})
        cache.set("second", {"v": 2})

    assert cache.get("first") == {"v": 1}
    assert cache.get("second") == {"v": 2}
    assert cache._disk_enabled is False
    assert attempts == 1
    assert [
        record.getMessage()
        for record in caplog.records
        if record.name == "ausecon_mcp.cache" and record.levelno >= logging.WARNING
    ] == []


def test_disk_disabled_cache_skips_future_disk_reads(monkeypatch) -> None:
    cache = TTLCache(ttl_seconds=60)

    def raising_named_tempfile(*args, **kwargs):
        raise PermissionError("sandbox denied cache write")

    monkeypatch.setattr(cache_module.tempfile, "NamedTemporaryFile", raising_named_tempfile)
    cache.set("k", {"v": 1})

    def unexpected_disk_read(_key):
        raise AssertionError("disk read should be skipped once disk cache is disabled")

    monkeypatch.setattr(cache, "_read_disk", unexpected_disk_read)

    assert cache.get("k") == {"v": 1}
    assert cache.get("missing") is None
    stale = cache.get_stale("k")
    assert stale is not None
    assert stale["value"] == {"v": 1}
    assert stale["cached_at"] == cache._entries["k"].cached_at
    assert stale["expires_at"] == cache._entries["k"].expires_at
    assert cache.get_stale("missing") is None


def test_set_returns_stored_value() -> None:
    cache = TTLCache(ttl_seconds=60)

    assert cache.set("k", {"v": 1}) == {"v": 1}


def test_cache_uses_digest_based_file_names(_isolated_cache_dir: Path) -> None:
    key = "abs-data:CPI/all?updated_after=2024-01-01"
    cache = TTLCache(ttl_seconds=60)

    cache.set(key, {"v": 1})

    expected = f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}.json"
    files = list(_isolated_cache_dir.glob("*.json"))

    assert [file.name for file in files] == [expected]


def test_cache_keeps_instance_root_for_writes_after_helper_changes(tmp_path, monkeypatch) -> None:
    first_root = tmp_path / "first-cache"
    second_root = tmp_path / "second-cache"
    monkeypatch.setattr(cache_module, "_default_disk_dir", lambda: first_root)
    cache = TTLCache(ttl_seconds=60)

    monkeypatch.setattr(cache_module, "_default_disk_dir", lambda: second_root)
    cache.set("k", {"v": 1})

    assert any(first_root.glob("*.json"))
    assert not second_root.exists()


def test_cache_keeps_instance_root_for_disk_reads_after_helper_changes(
    tmp_path, monkeypatch
) -> None:
    key = "k"
    root = tmp_path / "first-cache"
    monkeypatch.setattr(cache_module, "_default_disk_dir", lambda: root)
    cache = TTLCache(ttl_seconds=60)
    root.mkdir(parents=True)
    cache._path_for(key).write_text(
        json.dumps(
            {
                "schema": 1,
                "cached_at": time.time(),
                "expires_at": time.time() + 60,
                "value": {"v": 1},
            }
        )
    )

    monkeypatch.setattr(cache_module, "_default_disk_dir", lambda: tmp_path / "second-cache")
    assert cache.get(key) == {"v": 1}


def test_disk_write_does_not_escape_trusted_cache_root(
    tmp_path, monkeypatch, _isolated_cache_dir: Path
) -> None:
    outside = tmp_path / "outside.json"
    cache = TTLCache(ttl_seconds=60)
    monkeypatch.setattr(cache, "_path_for", lambda _key: outside)

    cache.set("k", {"v": 1})

    assert cache.get("k") == {"v": 1}
    assert not outside.exists()
    assert not any(_isolated_cache_dir.glob("*.json"))


def test_unlink_ignores_paths_outside_trusted_cache_root(tmp_path) -> None:
    cache = TTLCache(ttl_seconds=60)
    outside = tmp_path / "outside.json"
    outside.write_text("keep me")

    cache._unlink(outside)

    assert outside.exists()


@pytest.mark.parametrize("ttl", [0, -1])
def test_zero_or_negative_ttl_expires_immediately(ttl) -> None:
    cache = TTLCache(ttl_seconds=ttl)
    cache.set("k", {"v": 1})

    assert cache.get("k") is None

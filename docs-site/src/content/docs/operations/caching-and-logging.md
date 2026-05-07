---
title: Caching and Logging
description: Operational behaviour for cache, stale fallback, logging, and upgrades.
---

## Logging

The server writes structured JSON log lines to stderr. It never writes logs to stdout because the
stdio MCP transport owns stdout.

Each log line includes at least `ts`, `level`, `logger`, and `msg`. Retrieval events add source,
identifier, URL, status, duration, and byte metadata so operators can trace upstream calls.

Set `AUSECON_LOG_LEVEL` to control logging for the `ausecon_mcp` namespace:

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUSECON_LOG_LEVEL` | Logger level: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. | `INFO` |

## Cache

Upstream responses are cached in memory and on disk. Repeated calls can reuse payloads across
client restarts, which is useful because many MCP clients spawn fresh stdio processes.

Set `AUSECON_CACHE_DISABLED` to disable all caching:

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUSECON_CACHE_DISABLED` | Set to `1`, `true`, or `yes` to disable memory and disk caching. | unset |

The disk cache location is fixed to the platform application-cache directory:

- Linux: `~/.cache/ausecon-mcp/`
- macOS: `~/Library/Caches/ausecon-mcp/`

`AUSECON_CACHE_DIR` is not supported.

If the disk cache directory is unavailable, the server falls back to in-process memory caching for
the lifetime of the process. Cross-process cache persistence and disk-backed stale reuse are not
available in that degraded mode.

## Stale fallback

If an upstream ABS or RBA request fails and a stale cached payload exists, the server can return the
cached payload and mark `metadata.stale = true` alongside `cached_at` and `expires_at`.

Parse errors are not masked this way. They still raise so upstream shape drift remains visible.

## Upgrading from pre-v0.8.0

The main operational change for users upgrading from releases earlier than `v0.8.0` is cache-root
behaviour:

- `AUSECON_CACHE_DIR` is no longer supported.
- Disk writes stay under the platform application-cache directory.
- The MCP tool, resource, and prompt surface is unchanged by that hardening change.

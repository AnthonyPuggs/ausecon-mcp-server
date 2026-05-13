---
title: Caching and Logging
description: Operational behaviour for cache, stale fallback, logging, and upgrades.
---

## Server observability

The server writes structured JSON log lines to stderr. It never writes logs to stdout because the
stdio MCP transport owns stdout.

Each log line includes at least `ts`, `level`, `logger`, and `msg`. Retrieval events add source,
identifier, URL, status, duration, and byte metadata so operators can trace upstream calls.

Set `AUSECON_LOG_LEVEL` to control logging for the `ausecon_mcp` namespace:

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUSECON_LOG_LEVEL` | Logger level: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. | `INFO` |

For Smithery HTTP containers, Uvicorn access logs are disabled by default. Application logs still go
to stderr and should not contain request bodies or session configuration.

Server observability is about data reliability: upstream request logs, integration-test failures,
catalogue drift, cache fallback, and hosted MCP health. It is separate from documentation-site
analytics. Documentation-site observability does not measure MCP data reliability, ABS/RBA upstream
health, cache state, or hosted MCP tool-call success.

## Documentation-site observability

The documentation site includes Vercel Analytics and Speed Insights so maintainers can understand
documentation usage and page performance. The integration lives in `docs-site/src/layouts/Base.astro`.

Speed Insights receives a sanitised URL. The `speedInsightsBeforeSend` hook strips query strings and
fragments before forwarding the payload, which avoids sending accidental local search terms or
client-side fragments from documentation URLs.
This protects query strings and fragments in documentation telemetry.

Use documentation-site metrics for:

- high-traffic documentation pages that need clearer examples
- page performance regressions in the Astro/Starlight site
- evidence that client-setup or hosted-deployment pages are being used

Do not use documentation-site metrics as evidence that the MCP server is healthy. For that, use
server logs, `/healthz`, Smithery metadata, live integration tests, and catalogue audit output.

## HTTP safety

The Smithery container exposes MCP Streamable HTTP at `/mcp`. It is suitable for public deployment
only because all tools are read-only and retrieve public ABS/RBA data from fixed upstream hosts.

Key safety constraints:

- Local users should prefer stdio. If testing HTTP locally, bind to `127.0.0.1`, not a public
  interface.
- The Smithery entrypoint binds `0.0.0.0` only inside the container so the platform can route to it.
- CORS is wildcard but non-credentialed; `mcp-session-id` is transport state, not authentication.
- Source-native identifiers reject URL and path characters before provider URL construction.
- Large unauthenticated requests remain the main residual risk, so callers should prefer `last_n`
  or explicit date bounds for broad datasets.

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

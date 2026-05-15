---
title: Hosted Deployment
description: Lightweight checks for the Render and Smithery hosted MCP path.
---

The hosted path exposes the same read-only MCP server over Streamable HTTP. Local clients should
continue to use stdio unless they are deliberately testing a container or hosted deployment.

## Lightweight checklist

Run this after Render deploys, Smithery listing changes, and release metadata updates:

- Confirm Render uptime for the hosted service and inspect recent deploy logs.
- `GET /` returns the status document and points clients to `/mcp`.
- `GET /healthz` returns `200` with `{"status": "ok"}`; this is the `/healthz` platform health
  check.
- `GET /.well-known/mcp/server-card.json` returns the current server name, version, homepage, icon,
  tool descriptions, read-only annotations, and output schemas.
- `/.well-known/mcp/server-card.json` is the server-card metadata endpoint used for hosted
  discovery checks.
- Confirm the Smithery listing points to the intended repository, branch, container build, and MCP
  endpoint.
- Use manual MCP tool-call smoke in the Smithery Playground after release changes.

Manual MCP tool-call smoke should stay bounded:

```text
list_economic_concepts(query="cash rate")
get_economic_series(concept="cash_rate_target", last_n=5)
get_derived_series(concept="real_cash_rate", last_n=5)
search_datasets(query="unemployment rate", source="abs")
```

The repository intentionally does not include `scripts/mcp_http_smoke.py`. Reintroduce automated
hosted tool-call smoke only when the deployed transport and client naming are stable enough to avoid
false release failures.

## Residual risks

The public hosted server is acceptable because all tools are read-only and use public ABS, RBA, and
APRA data.
The main residual risk is large unauthenticated retrieval. Prefer examples with `last_n`, `start`,
and `end`, specify `table_id` for APRA XLSX workbooks, and monitor request volume, CPU, memory, and
upstream latency.

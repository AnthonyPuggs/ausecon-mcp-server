---
title: Getting Started
description: Australian economic data in your MCP client in about two minutes.
---

ausecon is an open, free, **no-API-key** MCP server for official Australian economic data —
ABS, RBA, and APRA — with source-traceable provenance and one consistent response shape
(`metadata · series · observations`).

This page takes you from zero to a live answer in about two minutes.

## Try it instantly (no install)

A hosted, read-only, no-API-key instance is available over Streamable HTTP at
`https://mcp.auseconmcp.com/mcp`. Point any MCP client that supports remote servers
at that URL, or in Claude Code:

```bash
claude mcp add --transport http ausecon https://mcp.auseconmcp.com/mcp
```

The hosted instance may take a few seconds to wake on the first request. The previous
`https://ausecon-mcp-server.onrender.com/mcp` URL continues to work and points at the
same instance.

## Install locally

Requirements: Python `3.10+` and [`uv`](https://docs.astral.sh/uv/) for the `uvx` launcher.

The package is published to [PyPI](https://pypi.org/project/ausecon-mcp-server/) and is intended
to be launched on demand:

```bash
uvx ausecon-mcp-server
```

On first use, `uvx` downloads the package into an isolated cached environment. The process then
waits for an MCP client to connect over standard input/output.

## Connect your client

ausecon speaks MCP over stdio, launched on demand with `uvx`.

**Claude Code**

```bash
claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server
```

**Codex**

```bash
codex mcp add ausecon -- uvx ausecon-mcp-server
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ausecon": { "command": "uvx", "args": ["ausecon-mcp-server"] }
  }
}
```

**Cursor** — add to `~/.cursor/mcp.json`, or use the one-click link
[Add to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=ausecon&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJhdXNlY29uLW1jcC1zZXJ2ZXIiXX0=):

```json
{
  "mcpServers": {
    "ausecon": { "command": "uvx", "args": ["ausecon-mcp-server"] }
  }
}
```

**Windsurf** — add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "ausecon": { "command": "uvx", "args": ["ausecon-mcp-server"], "env": {} }
  }
}
```

**VS Code** — add to `.vscode/mcp.json`, or use the one-click link
[Install in VS Code](vscode:mcp/install?%7B%22name%22%3A%22ausecon%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22ausecon-mcp-server%22%5D%7D):

```json
{
  "servers": {
    "ausecon": { "type": "stdio", "command": "uvx", "args": ["ausecon-mcp-server"] }
  }
}
```

## Ask your first question

Ask your agent: **"What's Australia's real cash rate right now?"**

The agent calls one tool:

```text
get_derived_series(concept="real_cash_rate", last_n=3)
```

and gets back the RBA cash-rate target less year-ended monthly CPI inflation, computed
transparently from the two official upstream series (abbreviated):

```json
{
  "metadata": {
    "source": "derived",
    "title": "Real cash rate",
    "retrieved_at": "2026-07-26T13:12:24Z",
    "server_version": "1.14.0",
    "derived": {
      "formula": "cash_rate_target - monthly_inflation",
      "description": "RBA cash-rate target less complete monthly CPI year-ended inflation. This is an ex-post real rate (the nominal rate less realised year-ended CPI inflation), not the ex-ante Fisher rate (less expected inflation).",
      "operands": [
        { "name": "cash_rate", "source": "rba", "dataset_id": "a2", "series_ids": ["ARBAMPCNCRT"] },
        { "name": "inflation", "source": "abs", "dataset_id": "CPI", "abs_key": "3.10001.10.50.M" }
      ],
      "units": "percentage points"
    }
  },
  "series": [
    { "series_id": "real_cash_rate", "label": "Real cash rate", "unit": "percentage points" }
  ],
  "observations": [
    { "date": "2026-03", "series_id": "real_cash_rate", "value": -0.5 },
    { "date": "2026-04", "series_id": "real_cash_rate", "value": -0.1 },
    { "date": "2026-05", "series_id": "real_cash_rate", "value": 0.35 }
  ]
}
```

This one response shows the whole design: a semantic concept resolved to official sources,
a transparent formula with both operands named down to the exact RBA/ABS series identifiers,
provenance stamps (`retrieved_at`, `server_version`), and an explicit caveat that this is an
ex-post real rate. Every retrieval tool returns this same
`metadata · series · observations` shape.

## Where to next

1. Use `list_economic_concepts` for ordinary economic requests such as GDP, CPI, unemployment,
   wages, cash rate, credit, exchange rates, or yields, then `get_economic_series` with the
   selected concept.
2. Use `get_derived_series` for transparent formula-based indicators such as real cash rate,
   yield-curve slope, real wage growth, mortgage-rate spreads, or credit-to-GDP.
3. Use `search_datasets`, `list_catalogue`, `get_abs_dataset_structure`, `get_abs_data`,
   `get_rba_table`, and `get_apra_data` when you need source-native ABS/RBA/APRA control.

Retrieval responses include `metadata`, `series`, and `observations`. Semantic retrievals also
include `metadata.semantic`, recording the resolved source target and normalised date bounds;
derived retrievals include `metadata.derived`, recording the formula, operands, units, and
alignment method.

For more worked calls see [Examples](/user-guide/examples/), and if you are using the server
through an AI agent, see [Prompting AI Agents](/user-guide/prompting-ai-agents/) for
natural-language requests and the MCP tool calls they usually trigger. For the trust story —
freshness stamps, caching, and staleness flags — see
[Data Freshness & Provenance](/user-guide/data-freshness-and-provenance/).

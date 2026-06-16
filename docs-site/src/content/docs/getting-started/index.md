---
title: Getting Started
description: Install and make your first MCP retrieval.
---

## Requirements

- Python `3.10+`.
- [`uv`](https://docs.astral.sh/uv/) for the `uvx` launcher.
- An MCP client that supports local stdio servers.

## Try it instantly (no install)

A hosted, read-only, no-API-key instance is available over Streamable HTTP at
`https://ausecon-mcp-server.onrender.com/mcp`. Point any MCP client that supports remote servers
at that URL, or in Claude Code:

```bash
claude mcp add --transport http ausecon https://ausecon-mcp-server.onrender.com/mcp
```

The hosted instance may take a few seconds to wake on the first request.

## Install

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

## Recommended workflow

1. Use `list_economic_concepts` for ordinary economic requests such as GDP, CPI, unemployment,
   wages, cash rate, credit, exchange rates, or yields.
2. Use `get_economic_series` with the selected concept.
3. Use `get_derived_series` for transparent formula-based indicators such as real cash rate,
   yield-curve slope, real wage growth, mortgage-rate spreads, or credit-to-GDP.
4. Use `search_datasets`, `list_catalogue`, `get_abs_dataset_structure`, `get_abs_data`,
   `get_rba_table`, and `get_apra_data` when you need source-native ABS/RBA/APRA control.

If you are using the server through an AI agent, see
[Prompting AI Agents](/user-guide/prompting-ai-agents/) for examples of natural-language requests
and the MCP tool calls they usually trigger.

## First retrieval pattern

```text
list_economic_concepts(query="cash rate")
```

```text
get_economic_series(
  concept="cash_rate_target",
  start="2020-01-01"
)
```

Retrieval responses include `metadata`, `series`, and `observations`. Semantic retrievals also
include `metadata.semantic`, recording the resolved source target and normalised date bounds.
Derived retrievals include `metadata.derived`, recording the formula, operands, units, alignment
frequency, and alignment method.

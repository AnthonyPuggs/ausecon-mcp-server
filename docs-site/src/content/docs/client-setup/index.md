---
title: Client Setup
description: Configure common MCP clients to launch the server with uvx.
---

Local clients should use the stdio command published on PyPI. The repository also includes a
separate Smithery custom-container entrypoint for hosted MCP Streamable HTTP deployments.

## Claude Desktop

Use this shape in Claude Desktop's MCP configuration:

```json
{
  "mcpServers": {
    "ausecon": {
      "command": "uvx",
      "args": ["ausecon-mcp-server"]
    }
  }
}
```

The repository includes the same example at
[`examples/claude_desktop_config.json`](https://github.com/AnthonyPuggs/ausecon-mcp-server/blob/main/examples/claude_desktop_config.json).

## Claude Code

```bash
claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server
```

## Codex

```bash
codex mcp add ausecon -- uvx ausecon-mcp-server
```

## Smithery

Smithery deployment uses the checked-in `smithery.yaml` and `Dockerfile.smithery`. The container
runs `ausecon-mcp-http`, listens on the `PORT` environment variable supplied by Smithery, and exposes
the MCP endpoint at `/mcp`.

The HTTP entrypoint is intentionally separate from the stdio command. It is unauthenticated because
the server exposes only read-only tools over public ABS and RBA data. Do not reuse this pattern for
private data sources or write-capable tools without adding authentication and origin controls.

## Cursor

Add an entry to `~/.cursor/mcp.json`, or to the project-level `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ausecon": {
      "command": "uvx",
      "args": ["ausecon-mcp-server"]
    }
  }
}
```

## VS Code

Add an entry to `.vscode/mcp.json` in your workspace, or the user-level equivalent:

```json
{
  "servers": {
    "ausecon": {
      "type": "stdio",
      "command": "uvx",
      "args": ["ausecon-mcp-server"]
    }
  }
}
```

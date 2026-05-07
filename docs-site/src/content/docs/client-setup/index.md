---
title: Client Setup
description: Configure common MCP clients to launch the server with uvx.
---

This repository currently provides a local stdio MCP server. Remote HTTP-based MCP connector
setups require a separately hosted HTTP service and are out of scope for version `1.0.0`.

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

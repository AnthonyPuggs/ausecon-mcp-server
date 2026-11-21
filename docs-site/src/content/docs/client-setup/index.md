---
title: Client Setup
description: Connect Claude, ChatGPT, Gemini and other MCP clients to ausecon, hosted or run locally.
---

There are two ways to connect:

- **Hosted:** add `https://mcp.auseconmcp.com/mcp` as a remote MCP server. Nothing to install, no
  sign-in and no API key. This is the only option for chat apps such as Claude, ChatGPT and
  Gemini, which connect to remote servers only.
- **Local:** your client launches the server itself with `uvx ausecon-mcp-server`, using the
  package published on [PyPI](https://pypi.org/project/ausecon-mcp-server/). This needs
  [`uv`](https://docs.astral.sh/uv/) installed.

Both give the same tools and the same data.

## Chat apps (hosted)

Each app has a setting for adding a custom MCP server or connector. Add one, paste the URL below,
and leave authentication off:

```text
https://mcp.auseconmcp.com/mcp
```

Menu names and plan requirements change often, so the links below go to each app's own help page.

### Claude

On the web, desktop or mobile, add a custom connector with the URL above. Once added on any device
it is available on all of them. See
[Getting started with custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp).

In Claude, data results are shown as [interactive charts](/user-guide/inline-charts/).

### ChatGPT

Add a custom MCP server with the URL above. Custom MCP servers are set up in ChatGPT on the web and
then appear in the desktop and mobile apps. Which plans can add one, and whether a workspace admin
must approve it, is set by OpenAI. See
[Connecting custom MCP servers in ChatGPT](https://help.openai.com/en/articles/12584461).

### Gemini

Add a custom app with the URL above in the Gemini web app at gemini.google.com. Once connected it
also works in the Gemini mobile app. Availability depends on your Google account, plan and region.
See [Connect and manage custom apps](https://support.google.com/gemini/answer/17209137).

ChatGPT and Gemini receive the same JSON response as any other client. Inline charts have been
tested in Claude only.

## Coding tools (hosted)

### Claude Code

```bash
claude mcp add --transport http ausecon https://mcp.auseconmcp.com/mcp
```

### Codex

```bash
codex mcp add ausecon --url https://mcp.auseconmcp.com/mcp
```

### Gemini CLI

```bash
gemini mcp add --transport http ausecon https://mcp.auseconmcp.com/mcp
```

Any other client that supports remote MCP servers over Streamable HTTP takes the same URL.

## Run locally (stdio)

Use these if you would rather run the server on your own machine. The hosted server and a local
one return the same results.

### Claude Desktop

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

### Claude Code (local)

```bash
claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server
```

### Codex (local)

```bash
codex mcp add ausecon -- uvx ausecon-mcp-server
```

### Cursor

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

### VS Code

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

## Host it yourself

Smithery deployment uses the checked-in `smithery.yaml` and `Dockerfile.smithery`. The container
runs `ausecon-mcp-http`, listens on the `PORT` environment variable supplied by Smithery, and exposes
the MCP endpoint at `/mcp`.

The HTTP entrypoint is intentionally separate from the stdio command. It is unauthenticated because
the server exposes only read-only tools over public ABS, RBA, and APRA data. Do not reuse this pattern for
private data sources or write-capable tools without adding authentication and origin controls.

# Australian Economic Data (RBA & ABS) MCP Server

<!-- mcp-name: io.github.AnthonyPuggs/ausecon-mcp-server -->

[![CI](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/tag/AnthonyPuggs/ausecon-mcp-server?sort=semver&label=release)](https://github.com/AnthonyPuggs/ausecon-mcp-server/tags)\
[![Smithery](https://smithery.ai/badge/anthonypuggs/ausecon-mcp)](https://smithery.ai/servers/anthonypuggs/ausecon-mcp)
[![Docs](https://img.shields.io/badge/docs-auseconmcp.com-blue)](https://auseconmcp.com/)
[![PyPI](https://img.shields.io/pypi/v/ausecon-mcp-server?label=PyPI)](https://pypi.org/project/ausecon-mcp-server/)
[![Transport](https://img.shields.io/badge/Transport-stdio%20%2B%20HTTP-blue)]()
[![License-MIT](https://img.shields.io/badge/License-MIT-lightgrey)]()

`ausecon-mcp-server` is a Python Model Context Protocol (MCP) server for structured Australian
macroeconomic and financial data from the Australian Bureau of Statistics (ABS) and the Reserve
Bank of Australia (RBA).

Version `1.1.0` is the current hosted release baseline. Transport support is stdio plus
Streamable HTTP. The server exposes eight read-only MCP tools, four read-only MCP resources, eight
prompt templates, and 55 curated macroeconomic concepts for analyst-friendly retrieval through
`get_economic_series`.

## Documentation

Full user and maintainer documentation is published at
[auseconmcp.com](https://auseconmcp.com/).

Useful links:

- [Getting started](https://auseconmcp.com/getting-started/)
- [Client setup](https://auseconmcp.com/client-setup/)
- [Tool reference](https://auseconmcp.com/reference/tools/)
- [Semantic concepts](https://auseconmcp.com/reference/semantic-concepts/)
- [Response schema](https://auseconmcp.com/reference/response-schema/)
- [Roadmap](https://auseconmcp.com/maintainers/roadmap/)
- [Changelog](CHANGELOG.md)

## Install

The package is published to [PyPI](https://pypi.org/project/ausecon-mcp-server/) and is intended to
be launched by an MCP client on demand via [`uvx`](https://docs.astral.sh/uv/):

```bash
uvx ausecon-mcp-server
```

The server speaks MCP over standard input/output. When launched manually, it waits for a client to
connect.

## Client Setup

Claude Desktop:

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

Claude Code:

```bash
claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server
```

Codex:

```bash
codex mcp add ausecon -- uvx ausecon-mcp-server
```

Smithery:

This repository also includes `smithery.yaml` and `Dockerfile.smithery` for hosted Smithery custom
container deployment over MCP Streamable HTTP at `/mcp`. The hosted HTTP entrypoint is
`ausecon-mcp-http`; local users should keep using the stdio command above unless they are testing a
container deployment. Maintainers can follow the deployment checklist in
[`docs/smithery-deployment.md`](docs/smithery-deployment.md).

## Basic Workflow

For normal economic concepts, discover the supported concept first:

```text
list_economic_concepts(query="cash rate")
```

Then retrieve the resolved series:

```text
get_economic_series(
  concept="cash_rate_target",
  start="2020-01-01"
)
```

For exact ABS/RBA control, use `search_datasets`, `list_catalogue`,
`get_abs_dataset_structure`, `get_abs_data`, and `get_rba_table`.

## Development

Python 3.12 is recommended for local development. The package metadata and CI matrix support
Python 3.10+.

```bash
uv sync --python 3.12 --extra dev
uv run pytest
uv run ruff check src tests scripts
```

## Repository

- Repository: [github.com/AnthonyPuggs/ausecon-mcp-server](https://github.com/AnthonyPuggs/ausecon-mcp-server)
- Issues: [GitHub Issues](https://github.com/AnthonyPuggs/ausecon-mcp-server/issues)
- Licence: [MIT](LICENSE)

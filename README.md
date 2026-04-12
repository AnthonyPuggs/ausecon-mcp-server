# ausecon-mcp-server

`ausecon-mcp-server` is a Python MCP server that provides structured access to Australian
macroeconomic and financial data from the Australian Bureau of Statistics (ABS) and the Reserve
Bank of Australia (RBA).

The server is intentionally source-aware rather than chatty: it exposes discovery and retrieval
tools, returns provenance-rich JSON, and leaves natural-language interpretation to the MCP client.

## Planned tool surface

- `search_datasets`
- `get_abs_dataset_structure`
- `get_abs_data`
- `list_rba_tables`
- `get_rba_table`
- `get_economic_series`

## Development

This repository uses `uv` for environment management.

```bash
uv sync --python 3.12
uv run pytest
```

## Claude Desktop example

An example configuration is available at [examples/claude_desktop_config.json](examples/claude_desktop_config.json).

# ausecon-mcp-server

`ausecon-mcp-server` is a Python Model Context Protocol (MCP) server for structured Australian
macroeconomic and financial data. It exposes a small, source-aware tool surface over Australian
Bureau of Statistics (ABS) and Reserve Bank of Australia (RBA) datasets and returns
provenance-rich JSON suitable for downstream analysis.

The server is intentionally narrow in scope. It does not try to be a general economic chatbot.
Instead, it gives MCP clients reliable discovery and retrieval tools that can be composed into
research, policy, and analytical workflows.

## Status

This repository is currently at `v0.1.0`.

The initial release includes:

- curated discovery across a small ABS and RBA catalogue
- ABS dataset structure retrieval
- ABS data retrieval in a normalised response shape
- RBA table listing and retrieval
- a small semantic resolver for a few high-value economic concepts

At this stage, the server should be treated as an opinionated first release rather than a complete
coverage layer for all ABS and RBA content.

## Tool Surface

The MCP server currently exposes the following tools:

| Tool | Purpose | Key inputs |
| --- | --- | --- |
| `search_datasets` | Search the curated ABS and RBA catalogue | `query`, `source` |
| `get_abs_dataset_structure` | Retrieve ABS SDMX dimensions and code lists | `dataflow_id` |
| `get_abs_data` | Retrieve ABS data in a normalised response shape | `dataflow_id`, `key`, `start_period`, `end_period`, `last_n`, `updated_after` |
| `list_rba_tables` | List curated RBA statistical tables | `category`, `include_discontinued` |
| `get_rba_table` | Retrieve an RBA statistical table in a normalised response shape | `table_id`, `series_ids`, `start_date`, `end_date`, `last_n` |
| `get_economic_series` | Resolve a small set of high-value economic concepts to ABS or RBA retrievals | `concept`, `start`, `end` |

### Currently supported semantic concepts

`get_economic_series` currently supports:

- `cash_rate_target`
- `headline_cpi`
- `trimmed_mean_inflation`
- `gdp_growth`

## Response Shape

Data retrieval tools return a normalised payload with three top-level sections:

- `metadata`: source, dataset or table identifier, retrieval URL, and related retrieval metadata
- `series`: long-form series descriptors including labels, units, frequency, and dimensions
- `observations`: long-form observations keyed by `date`, `series_id`, and `value`

This design keeps source provenance explicit while making downstream processing simpler in Python,
R, or other analytical environments.

## Requirements

- Python `3.10+`
- [`uv`](https://docs.astral.sh/uv/) for environment management and local execution

## Installation

Clone the repository and install the project environment:

```bash
git clone <your-repo-url>
cd rba_abs_mcp
uv sync --python 3.12
```

## Running The Server

From the repository root:

```bash
uv run ausecon-mcp-server
```

The server is designed to be launched by an MCP client over standard input/output rather than used
as a standalone command-line application.

## Connecting An MCP Client

### Claude Desktop

An example Claude Desktop configuration is included at
[examples/claude_desktop_config.json](examples/claude_desktop_config.json).

The core shape is:

```json
{
  "mcpServers": {
    "ausecon": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/rba_abs_mcp",
        "run",
        "ausecon-mcp-server"
      ]
    }
  }
}
```

Replace `/absolute/path/to/rba_abs_mcp` with the absolute path to your local checkout.

## How To Use The Server

The most reliable workflow is:

1. Use `search_datasets` when you do not yet know the exact ABS dataset or RBA table.
2. Use `get_abs_dataset_structure` before `get_abs_data` when you need to inspect valid ABS
   dimensions and keys.
3. Use `get_abs_data` or `get_rba_table` for retrieval once you know the target dataset or table.
4. Use `get_economic_series` only for the small curated semantic shortcuts listed above.

### Example client requests

In an MCP-enabled client, the user can ask for things such as:

- “Search for datasets related to trimmed mean inflation.”
- “Show me the ABS structure for CPI.”
- “Fetch the last 12 observations from RBA table g1.”
- “Get headline CPI from 2023 onwards.”

### Example retrieval patterns

Discover relevant datasets:

```text
search_datasets(query="cash rate")
```

Inspect ABS dataset structure before querying:

```text
get_abs_dataset_structure(dataflow_id="CPI")
```

Fetch a filtered ABS dataset:

```text
get_abs_data(
  dataflow_id="CPI",
  key="all",
  start_period="2024-01",
  end_period="2024-12",
  last_n=12
)
```

Fetch an RBA table:

```text
get_rba_table(
  table_id="g1",
  last_n=8
)
```

Resolve a curated economic concept:

```text
get_economic_series(
  concept="cash_rate_target",
  start="2020-01-01"
)
```

## Development

Install the development environment:

```bash
uv sync --python 3.12
```

Run the test suite:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

## Repository Structure

```text
src/ausecon_mcp/
  catalogue/   Curated ABS and RBA discovery metadata
  parsers/     Source-specific parsers for ABS and RBA payloads
  providers/   HTTP retrieval and cache-aware source adapters
  cache.py     Simple in-memory TTL cache
  models.py    Shared normalised data structures
  server.py    FastMCP server entry point and tool registration
tests/
examples/
```

## Release Notes For `v0.1`

The intended `v0.1` release is the initial public baseline for the MCP server. It provides the
core architecture, the first six tools, normalised response models, local development workflow, and
test coverage for parsing, provider behaviour, and server-level integration.

## Releasing

If you want to publish a release from this repository:

1. ensure `pyproject.toml` contains the intended version
2. commit the release-ready state
3. create an annotated git tag such as `v0.1.0`
4. push the branch and the tag to GitHub
5. create a GitHub Release from that tag with release notes

An example tag command is:

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin main
git push origin v0.1.0
```

Once the tag is on GitHub, you can create the release in the GitHub interface under
“Releases” -> “Draft a new release”.

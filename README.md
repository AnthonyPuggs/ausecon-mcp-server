# ausecon-mcp-server

[![CI](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/tag/AnthonyPuggs/ausecon-mcp-server?sort=semver&label=release)](https://github.com/AnthonyPuggs/ausecon-mcp-server/tags)

`ausecon-mcp-server` is a Python Model Context Protocol (MCP) server for structured Australian
macroeconomic and financial data. It exposes a small, source-aware tool surface over Australian
Bureau of Statistics (ABS) and Reserve Bank of Australia (RBA) datasets and returns
provenance-rich JSON suitable for downstream analysis.

The server is intentionally narrow in scope. It does not try to be a general economic chatbot.
Instead, it gives MCP clients reliable discovery and retrieval tools that can be composed into
research, policy, and analytical workflows.

## Status

This repository is currently at `v0.5.0`. See [`CHANGELOG.md`](CHANGELOG.md) for release history.

The current release includes:

- curated discovery across expanded ABS and RBA catalogues
- deterministic search ranking across dataset IDs, aliases, names, tags, and descriptions
- active-only RBA table discovery by default, with optional inclusion of discontinued tables
- ABS dataset structure retrieval
- ABS data retrieval in a normalised response shape
- compatibility with current live ABS structure and CSV payload shapes
- RBA table listing and retrieval
- a semantic resolver whose curated default concepts now narrow to concrete series
- stricter validation for tool inputs and parameter ranges
- source-aware upstream and parse error messages
- retry logic for transient ABS and RBA upstream failures
- provider caching keyed to upstream requests rather than client-side filters
- support for RBA event-style tables such as `a2`

At this stage, the server should still be treated as an opinionated early release rather than a
complete coverage layer for all ABS and RBA content.

## Tool Surface

The MCP server currently exposes the following tools:

| Tool | Purpose | Key inputs |
| --- | --- | --- |
| `search_datasets` | Search the curated ABS and RBA catalogue with deterministic ranking | `query`, `source` |
| `get_abs_dataset_structure` | Retrieve ABS SDMX dimensions and code lists | `dataflow_id` |
| `get_abs_data` | Retrieve ABS data in a normalised response shape | `dataflow_id`, `key`, `start_period`, `end_period`, `last_n`, `updated_after` |
| `list_rba_tables` | List curated RBA statistical tables | `category`, `include_discontinued` |
| `get_rba_table` | Retrieve an RBA statistical table in a normalised response shape | `table_id`, `series_ids`, `start_date`, `end_date`, `last_n` |
| `get_economic_series` | Resolve a small set of high-value economic concepts to ABS or RBA retrievals | `concept`, `variant`, `geography`, `frequency`, `start`, `end` |

### Currently supported semantic concepts

`get_economic_series` currently supports:

- `cash_rate_target`
- `headline_cpi`
- `trimmed_mean_inflation`
- `gdp_growth`

By default, these currently resolve to the following narrowed series:

- `cash_rate_target` -> RBA `a2` cash rate target series (`ARBAMPCNCRT`)
- `headline_cpi` -> ABS `CPI` all groups CPI index for Australia, quarterly (`1.10001.10.50.Q`)
- `trimmed_mean_inflation` -> RBA `g1` year-ended trimmed mean inflation (`GCPIOCPMTMYP`)
- `gdp_growth` -> ABS `ANA_AGG` quarterly real GDP growth (`M2.GPM.20.AUS.Q`)

`variant`, `geography`, and `frequency` are validated against the catalogue entry. For ABS
datasets, populated variants can be literal SDMX keys or partial fragments that are completed
against the live structure. For RBA tables, populated variants narrow the response to the declared
series IDs. Variants that are declared but not yet populated raise a clear "not yet wired" error.

## Discovery And Validation

- `search_datasets` prioritises exact dataset or table IDs, then exact aliases, then exact names,
  then broader multi-term matches.
- common economist phrasing is normalised for ranking, including terms such as "jobless",
  "mortgage", "rates", and "fx".
- discontinued RBA tables are excluded from `search_datasets` by default.
- `list_rba_tables` excludes discontinued tables by default and returns a `discontinued` boolean
  field on every row.
- empty identifiers and empty search queries are rejected before any network call.
- `last_n` must be positive when provided.
- `get_abs_data` validates annual, quarterly, monthly, and half-yearly ABS period strings.
- `get_rba_table` validates ISO date bounds.
- `get_economic_series` validates `start` and `end` after resolving the target source.
- transient ABS and RBA upstream failures are retried automatically.
- malformed upstream payloads are surfaced as source-aware parse failures.
- `search_datasets` scores should be treated as ranking metadata rather than a stable contract.

## Response Shape

Data retrieval tools return a normalised payload with three top-level sections:

- `metadata`: source, dataset or table identifier, retrieval URL, and related retrieval metadata
- `series`: long-form series descriptors including labels, units, frequency, and dimensions
- `observations`: long-form observations keyed by `date`, `series_id`, and `value`; some RBA
  observations may also include `raw_value` when the upstream cell is non-numeric

This design keeps source provenance explicit while making downstream processing simpler in Python,
R, or other analytical environments.

## Discovery Coverage

The curated catalogue is still intentionally selective, but `v0.5.0` covers the main analyst
workflows more credibly:

- ABS prices and inflation, labour, national accounts, activity, housing and construction,
  external sector, and lending indicators
- RBA monetary policy, payments, money and credit, interest rates and yields, exchange rates,
  inflation, output and labour, and external sector tables

## Requirements

- Python `3.10+`
- [`uv`](https://docs.astral.sh/uv/) for environment management and local execution

## Installation

Clone the repository and install the project environment:

```bash
git clone https://github.com/AnthonyPuggs/ausecon-mcp-server.git
cd ausecon-mcp-server
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

This repository currently provides a local stdio MCP server only. Claude API / Anthropic MCP
connector setups and other remote HTTP-based MCP connectors require a separately hosted HTTP server,
which is out of scope for this repository today.

Use the same absolute checkout path in every client example below:

```text
/absolute/path/to/ausecon-mcp-server
```

### Claude Desktop

An example Claude Desktop configuration is included at
[examples/claude_desktop_config.json](examples/claude_desktop_config.json).

That file is the source of truth. The only value you need to customise is the absolute checkout
path passed to `uv --directory`.

```json
"/absolute/path/to/ausecon-mcp-server"
```

Replace `/absolute/path/to/ausecon-mcp-server` with the absolute path to your local checkout.

### Claude Code

Add the server with the Claude Code CLI:

```bash
claude mcp add --transport stdio ausecon -- uv --directory /absolute/path/to/ausecon-mcp-server run ausecon-mcp-server
```

### Codex

Add the server with the Codex CLI:

```bash
codex mcp add ausecon -- uv --directory /absolute/path/to/ausecon-mcp-server run ausecon-mcp-server
```

## How To Use The Server

The most reliable workflow is:

1. Use `search_datasets` when you do not yet know the exact ABS dataset or RBA table.
2. Use `get_abs_dataset_structure` before `get_abs_data` when you need to inspect valid ABS
   dimensions and keys.
3. Use `get_abs_data` or `get_rba_table` for retrieval once you know the target dataset or table.
4. Use `get_economic_series` only for the small curated semantic shortcuts listed above.

### Example client requests

In an MCP-enabled client, the user can ask for things such as:

- "Search for datasets related to trimmed mean inflation."
- "Show me the ABS structure for CPI."
- "Fetch the last 12 observations from RBA table g1."
- "Get headline CPI from 2023 onwards."
- "Get quarterly real GDP growth from 2020."

### Example retrieval patterns

Discover relevant datasets:

```text
search_datasets(query="cash rate")
```

Inspect active inflation tables and optionally include discontinued RBA coverage:

```text
list_rba_tables(category="inflation", include_discontinued=True)
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
  start_period="2024-Q1",
  end_period="2024-Q4",
  last_n=4
)
```

Fetch an RBA table:

```text
get_rba_table(
  table_id="g1",
  last_n=8
)
```

Fetch an event-style RBA policy table:

```text
get_rba_table(
  table_id="a2",
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

Resolve trimmed mean inflation using the default narrowed series:

```text
get_economic_series(
  concept="trimmed_mean_inflation",
  start="2020-01-01"
)
```

Resolve quarterly real GDP growth:

```text
get_economic_series(
  concept="gdp_growth",
  start="2020-Q1"
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
uv run ruff check src tests
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

## Releasing

If you want to publish a release from this repository:

1. ensure `pyproject.toml` contains the intended version
2. commit the release-ready state
3. create an annotated git tag such as `vX.Y.Z`
4. push the branch and the tag to GitHub
5. create a GitHub Release from that tag with release notes

An example tag command is:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Once the tag is on GitHub, you can create the release in the GitHub interface under
"Releases" -> "Draft a new release".

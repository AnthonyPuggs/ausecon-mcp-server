# ausecon-mcp-server

<!-- mcp-name: io.github.AnthonyPuggs/ausecon-mcp-server -->

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

Releases are published to [PyPI](https://pypi.org/project/ausecon-mcp-server/) and versioned via git tags. See [`CHANGELOG.md`](CHANGELOG.md) for release history.

Current capabilities:

- six read-only MCP tools covering dataset discovery, ABS structure inspection, ABS and RBA data retrieval, and a small semantic shortcut layer for common macroeconomic concepts
- three read-only MCP resources exposing the curated catalogue and per-entry metadata without making live upstream calls
- four MCP prompt templates for common economist workflows such as inflation summaries, macro snapshots, and dataset discovery
- provenance-rich JSON responses, structured JSON logging to stderr, and dual-layer caching that survives client restarts

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

The curated catalogue is intentionally selective, but it covers the main analyst workflows across:

- ABS prices and inflation, labour, national accounts, activity, housing and construction,
  external sector, and lending indicators
- RBA monetary policy, payments, money and credit, interest rates and yields, exchange rates,
  inflation, output and labour, and external sector tables

## Requirements

- Python `3.10+`
- [`uv`](https://docs.astral.sh/uv/) (for the `uvx` launcher used by every client below)

## Installation

The server is published to [PyPI](https://pypi.org/project/ausecon-mcp-server/) and is intended to
be launched by an MCP client on demand via [`uvx`](https://docs.astral.sh/uv/). No manual clone or
install is required — the client configurations below handle everything.

To confirm the server is reachable on your machine, you can run it once by hand:

```bash
uvx ausecon-mcp-server
```

`uvx` will download the package into an isolated, cached environment the first time. The server
speaks MCP over standard input/output and waits for a client to connect, so expect it to sit idle
until an MCP client attaches.

## Connecting An MCP Client

This repository currently provides a local stdio MCP server only. Claude API / Anthropic MCP
connector setups and other remote HTTP-based MCP connectors require a separately hosted HTTP server,
which is out of scope for this repository today.

### Claude Desktop

An example Claude Desktop configuration is included at
[examples/claude_desktop_config.json](examples/claude_desktop_config.json):

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

### Claude Code

Add the server with the Claude Code CLI:

```bash
claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server
```

### Codex

Add the server with the Codex CLI:

```bash
codex mcp add ausecon -- uvx ausecon-mcp-server
```

### Cursor

Add an entry to `~/.cursor/mcp.json` (or the project-level `.cursor/mcp.json`):

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

Add an entry to `.vscode/mcp.json` in your workspace (or the user-level equivalent):

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

## Resources

In addition to tools, the server exposes the curated catalogue as MCP
resources. Clients can render these in a resource picker without
calling `search_datasets` first.

| URI | Returns |
| --- | --- |
| `ausecon://catalogue` | Flat index of every curated ABS and RBA entry (id, source, name, description, category, frequency, tags). |
| `ausecon://abs/{dataflow_id}` | Full curated catalogue entry for a single ABS dataflow (e.g. `ausecon://abs/CPI`). |
| `ausecon://rba/{table_id}` | Full curated catalogue entry for a single RBA statistical table (e.g. `ausecon://rba/g1`). |

All resources are read-only, served as `application/json`, and sourced
from the static curated catalogue — no network calls are made to
render them.

## Prompts

The server registers four prompt templates that chain the existing
tools into common economist workflows. Clients such as Claude Desktop
surface these as slash-commands.

| Prompt | Arguments | What it does |
| --- | --- | --- |
| `summarise_latest_inflation` | `months: int = 12` | Pulls headline and trimmed-mean CPI via `get_economic_series` and summarises them against the RBA 2–3% target band. |
| `compare_cash_rate_to_cpi` | `start: str`, `end: str \| None` | Narrates the path of the cash rate target against headline CPI over the window. |
| `macro_snapshot` | `as_of: str \| None` | Assembles a compact snapshot table of cash rate, headline CPI, trimmed-mean CPI, and real GDP growth. |
| `discover_dataset` | `topic: str` | Runs `search_datasets` and `list_rba_tables` for the topic, then recommends the top two candidates. |

Each tool is also annotated with `readOnlyHint` and `openWorldHint` so
compliant clients can indicate that the server only reads from
external, evolving sources.

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

## Operations

The server writes structured JSON log lines to **stderr** (never
stdout — the stdio MCP transport owns stdout). Each line is a single
JSON object with at least `ts`, `level`, `logger`, and `msg` fields;
retrieval events add `source`, `identifier`, `url`, `status_code`,
`duration_ms`, and `bytes` so operators can trace every upstream call.

Upstream responses are cached to disk, so repeated calls survive
process restarts (e.g. `uvx` spawning a fresh server per client
session). On upstream failure, if a stale cached copy exists, the
server returns it and marks `metadata.stale = true` alongside
`cached_at` and `expires_at`; **parse errors are never masked this
way** — they still raise so upstream shape drift stays visible.

Data responses also include `metadata.server_version` so bug reports
can reference the exact release that produced them.

### Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUSECON_CACHE_DISABLED` | Set to `1` / `true` / `yes` to turn off **all** caching (memory and disk). Useful for debugging. | unset (caching on). |
| `AUSECON_LOG_LEVEL` | Logger level for the `ausecon_mcp` namespace (`DEBUG`, `INFO`, `WARNING`, `ERROR`). `DEBUG` enables cache-hit/miss events. | `INFO`. |

The on-disk cache location is fixed to the platform app-cache directory
(`~/.cache/ausecon-mcp/` on Linux, `~/Library/Caches/ausecon-mcp/` on macOS).
`AUSECON_CACHE_DIR` is no longer supported.

## Upgrading From Pre-v0.8.0

If you used a release earlier than `v0.8.0`, the main operational change is the cache-root
behaviour:

- `AUSECON_CACHE_DIR` is no longer supported.
- on-disk cache writes now stay under the platform app-cache directory for the server
  (`~/.cache/ausecon-mcp/` on Linux, `~/Library/Caches/ausecon-mcp/` on macOS).
- this is a behavioural hardening change only; the MCP tool, resource, and prompt surface is
  unchanged.

If you previously redirected the cache into a mounted volume, shared directory, or CI-specific
path, update that operational setup before upgrading.

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
  cache.py     Dual-layer TTL cache (memory + on-disk JSON)
  logging.py   JSON-lines stderr logger for the ausecon_mcp namespace
  models.py    Shared normalised data structures
  server.py    FastMCP server entry point and tool registration
tests/
examples/
```

## Releasing

If you want to publish a release from this repository:

1. ensure the release-ready state is committed, including any changelog updates
2. create a git tag in the repository's `vX.Y.Z` format on the intended release commit
3. push the branch and the tag to GitHub
4. allow the `Release` workflow to build and publish the tagged version
5. draft the GitHub Release notes from that tag

The package version is derived from git tags via `hatch-vcs`, so you do not manually edit a target
version in `pyproject.toml` when cutting a release.

This repository's existing releases use lightweight tags, so a typical release sequence is:

```bash
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

Once the tag is on GitHub, you can create the release in the GitHub interface under
"Releases" -> "Draft a new release".

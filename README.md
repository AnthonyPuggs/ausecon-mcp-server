# Australian Economic Data (RBA & ABS) MCP Server

<!-- mcp-name: io.github.AnthonyPuggs/ausecon-mcp-server -->

[![CI](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/tag/AnthonyPuggs/ausecon-mcp-server?sort=semver&label=release)](https://github.com/AnthonyPuggs/ausecon-mcp-server/tags)
[![Transport](https://img.shields.io/badge/Transport-stdio-blue)]()
[![API](https://img.shields.io/badge/API-JSON%2FSDMX-green)]()
[![License-MIT](https://img.shields.io/badge/License-MIT-lightgrey)]()

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

- eight read-only MCP tools covering dataset discovery (including a model-controlled `list_economic_concepts` surface and an unranked `list_catalogue` complement to `search_datasets`), ABS structure inspection, ABS and RBA data retrieval, and a semantic shortcut layer with 29 curated macroeconomic concepts
- four read-only MCP resources exposing the curated catalogue, per-entry metadata, and an `ausecon://concepts` index of every semantic shortcut with its resolved target
- eight MCP prompt templates for common economist workflows such as inflation summaries, macro snapshots, living-cost comparisons, construction pipeline reviews, labour slack, yield curve snapshots, and dataset discovery
- provenance-rich JSON responses, a checked-in retrieval contract at [`schemas/response.schema.json`](schemas/response.schema.json), structured JSON logging to stderr, and dual-layer caching that survives client restarts

At this stage, the server should still be treated as an opinionated early release rather than a
complete coverage layer for all ABS and RBA content.

## Tool Surface

The MCP server currently exposes the following tools:

| Tool | Purpose | Key inputs |
| --- | --- | --- |
| `search_datasets` | Search the curated ABS and RBA catalogue with deterministic ranking | `query`, `source` |
| `list_catalogue` | List catalogue entries unranked, optionally filtered by source, category, or tag | `source`, `category`, `tag`, `include_ceased`, `include_discontinued` |
| `list_economic_concepts` | List analyst-friendly semantic concepts accepted by `get_economic_series` | `query`, `source`, `category` |
| `get_abs_dataset_structure` | Retrieve ABS SDMX dimensions and code lists | `dataflow_id` |
| `get_abs_data` | Retrieve ABS data in a normalised response shape | `dataflow_id`, `key`, `start_period`, `end_period`, `last_n`, `updated_after` |
| `list_rba_tables` | Deprecated compatibility alias for listing curated RBA statistical tables | `category`, `include_discontinued` |
| `get_rba_table` | Retrieve an RBA statistical table in a normalised response shape | `table_id`, `series_ids`, `start_date`, `end_date`, `last_n` |
| `get_economic_series` | Preferred analyst-facing retrieval tool for curated economic concepts | `concept`, `variant`, `geography`, `frequency`, `start`, `end`, `last_n` |

For LLM-facing integrations, prefer `list_economic_concepts` followed by
`get_economic_series`. For source-native browsing, prefer `list_catalogue(source="rba")`;
`list_rba_tables` remains available only as a compatibility alias for existing clients.

### Currently supported semantic concepts

`get_economic_series` resolves 29 curated concepts across prices, labour, activity, monetary
policy, financial markets, external sector, and credit. The full list is also available at runtime
via the `ausecon://concepts` resource. Resolver variant rules are summarised in
[`docs/variants.md`](docs/variants.md), and the retrieval contract is documented in
[`schemas/response.schema.json`](schemas/response.schema.json) and
[`docs/response-schema.md`](docs/response-schema.md).

**Prices and inflation**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `headline_cpi` | ABS `CPI` | All groups CPI, Australia, quarterly (`1.10001.10.50.Q`) |
| `trimmed_mean_inflation` | RBA `g1` | Year-ended trimmed mean inflation (`GCPIOCPMTMYP`) |
| `weighted_median_inflation` | RBA `g1` | Year-ended weighted median inflation (`GCPIOCPMWMYP`) |
| `monthly_inflation` | RBA `g4` | Monthly headline CPI year-ended (`GCPIAGSAMP`) |
| `producer_price_inflation` | ABS `PPI_FD` | Final demand PPI, Australia, quarterly |
| `inflation_expectations` | RBA `g3` | Consumer inflation expectations |

**Labour**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `employment` | ABS `LF` | Employed people, Australia, seasonally adjusted, monthly |
| `unemployment_rate` | ABS `LF` | Unemployment rate, Australia, seasonally adjusted, monthly |
| `underemployment_rate` | ABS `LF_UNDER` | Underemployment rate, Australia, seasonally adjusted, monthly (composed via structure `DS_LF_UNDER`) |
| `participation_rate` | ABS `LF` | Participation rate, Australia, seasonally adjusted, monthly |
| `hours_worked` | ABS `LF_HOURS` | Monthly hours worked in all jobs, Australia, seasonally adjusted |
| `job_vacancies` | ABS `JV` | Total job vacancies, Australia, seasonally adjusted, quarterly |
| `wage_growth` | ABS `WPI` | Wage Price Index, Australia, all sectors, quarterly |

**Activity**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `gdp_growth` | ABS `ANA_AGG` | Quarterly real GDP growth (`M2.GPM.20.AUS.Q`) |
| `household_spending` | ABS `HSI_M` | Household Spending Indicator, Australia, seasonally adjusted, current prices |
| `dwelling_approvals` | ABS `BUILDING_APPROVALS` | Residential dwelling approvals, Australia, monthly (`1.1.9.TOT.100.10.AUS.M`) |
| `population` | ABS `ERP_Q` | Estimated resident population, Australia, quarterly |

**Monetary policy and rates**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `cash_rate_target` | RBA `a2` | Cash rate target (`ARBAMPCNCRT`) |
| `government_bond_yield_3y` | RBA `f17` | 3-year zero-coupon AGS yield (`FZCY300D`) |
| `government_bond_yield_10y` | RBA `f17` | 10-year zero-coupon AGS yield (`FZCY1000D`) |
| `mortgage_rate` | RBA `f6` | Owner-occupier variable housing rate (`FLRHOOVA`) |
| `business_lending_rate` | RBA `f7` | Small business lending rate indicator |

**FX**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `aud_usd` | RBA `f11` | AUD/USD spot (`FXRUSD`) |
| `trade_weighted_index` | RBA `f11` | Trade-weighted index (`FXRTWI`) |

**External sector**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `trade_balance` | ABS `ITGS` | Balance on goods and services, Australia, monthly |
| `current_account_balance` | ABS `BOP` | Current account balance, Australia, seasonally adjusted, quarterly |
| `commodity_prices` | RBA `i2` | RBA Index of Commodity Prices (SDR terms, `GRCPAISDR`) |

**Credit**

| Concept | Source | Default mapping |
| --- | --- | --- |
| `housing_credit` | RBA `d2` | Owner-occupier + investor housing credit, seasonally adjusted (`DLCACOHS`, `DLCACIHS`) |
| `business_credit` | RBA `d2` | Business credit, seasonally adjusted (`DLCACBS`) |

**Locked default choices**

A few defaults deserve calling out explicitly:

- **`government_bond_yield_*` resolve to `f17`** (zero-coupon AGS yields), not `f16` (indicative
  yields). `f17` is maintained for modelling and avoids the coupon-driven quirks of `f16`.
- **`housing_credit` returns two series from `d2`** (`DLCACOHS` owner-occupier + `DLCACIHS`
  investor) rather than a pre-aggregated total. Clients can sum them; we do not derive an
  aggregate series.
- **`producer_price_inflation` uses `PPI_FD`** (final demand), not the input-stage `PPI`, because
  final demand is the headline measure most analysts track.
- **`underemployment_rate` uses `LF_UNDER`** (dataflow id) but composes its SDMX key against
  structure id `DS_LF_UNDER`, because the live ABS SDMX structure is exposed under the
  `DS_`-prefixed id.
- **`dwelling_approvals` uses `BUILDING_APPROVALS` → `BA_GCCSA`** with the live national
  residential approvals series. The current ABS approvals collection does not expose a clean
  seasonally adjusted national residential default, so the shipped semantic default is the original
  Australia total.

`variant`, `geography`, and `frequency` are validated against the catalogue entry. For ABS
datasets, populated variants can be literal SDMX keys or partial fragments that are completed
against the live structure. For RBA tables, populated variants narrow the response to the declared
series IDs. The runtime catalogue only exposes fully wired variants; future candidates stay in
[`docs/variant_candidates.md`](docs/variant_candidates.md) until they have a real series binding.

## Discovery And Validation

- `search_datasets` prioritises exact dataset or table IDs, then exact aliases, then exact names,
  then broader multi-term matches.
- common economist phrasing is normalised for ranking, including terms such as "jobless",
  "mortgage", "rates", and "fx".
- `list_economic_concepts` exposes every curated semantic shortcut as a model-controlled discovery
  tool, including aliases and the recommended `get_economic_series` call.
- discontinued RBA tables are excluded from `search_datasets` by default.
- `list_rba_tables` is deprecated; use `list_catalogue(source="rba")` for new RBA browse flows.
- empty identifiers and empty search queries are rejected before any network call.
- `last_n` must be positive when provided.
- `get_abs_data` validates annual, quarterly, monthly, and half-yearly ABS period strings.
- `get_rba_table` validates ISO date bounds.
- `get_economic_series` accepts natural analyst bounds (`YYYY`, `YYYY-QN`, `YYYY-SN`,
  `YYYY-MM`, or `YYYY-MM-DD`) and normalises them to the resolved ABS/RBA source.
- transient ABS and RBA upstream failures are retried automatically.
- malformed upstream payloads are surfaced as source-aware parse failures.
- `search_datasets` scores should be treated as ranking metadata rather than a stable contract.

## Response Shape

Data retrieval tools return a normalised payload with three top-level sections:

- `metadata`: source, dataset or table identifier, retrieval URL, and related retrieval metadata
- `series`: long-form series descriptors including labels, units, frequency, and dimensions
- `observations`: long-form observations keyed by `date`, `series_id`, and `value`; some RBA
  observations may also include `raw_value` when the upstream cell is non-numeric

Responses returned through `get_economic_series` also include `metadata.semantic`, which records
the requested concept, resolved source target, requested bounds, and source-native resolved bounds.

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
| `ausecon://concepts` | Index of every curated semantic shortcut with its resolved source, dataset id, variant, aliases, and recommended call. |

All resources are read-only, served as `application/json`, and sourced
from the static curated catalogue — no network calls are made to
render them.

## Prompts

The server registers eight prompt templates that chain the existing
tools into common economist workflows. Clients such as Claude Desktop
surface these as slash-commands.

| Prompt | Arguments | What it does |
| --- | --- | --- |
| `summarise_latest_inflation` | `months: int = 12` | Pulls headline and trimmed-mean CPI via `get_economic_series` and summarises them against the RBA 2–3% target band. |
| `compare_cash_rate_to_cpi` | `start: str`, `end: str \| None` | Narrates the path of the cash rate target against headline CPI over the window. |
| `macro_snapshot` | `as_of: str \| None` | Assembles a compact snapshot table of cash rate, headline CPI, trimmed-mean CPI, and real GDP growth. |
| `living_costs_vs_cpi` | `start: str \| None`, `last_n: int = 8` | Compares Selected Living Cost Indexes across household types against headline CPI to highlight cost-of-living divergence. |
| `construction_pipeline` | `last_n: int = 8` | Summarises construction pipeline strength across total, engineering, and residential/non-residential building activity. |
| `labour_slack_snapshot` | `last_n: int = 12` | Reads `unemployment_rate` and `underemployment_rate` and narrates the combined slack signal. |
| `yield_curve_snapshot` | `last_n: int = 60` | Reads the 3-year and 10-year AGS yields and describes the curve shape and recent shift. |
| `discover_dataset` | `topic: str` | Runs `list_economic_concepts`, `search_datasets`, and `list_catalogue` for the topic, then recommends the top candidates. |

Each tool is also annotated with `readOnlyHint` and `openWorldHint` so
compliant clients can indicate that the server only reads from
external, evolving sources.

## How To Use The Server

The most reliable workflow is:

1. Use `list_economic_concepts` when the user asks for a normal economic concept such as GDP,
   CPI, unemployment, cash rate, credit, or yields.
2. Use `get_economic_series` for the selected concept. Its `start` and `end` bounds accept natural
   analyst date strings and are normalised to the underlying ABS or RBA source.
3. Use `search_datasets`, `list_catalogue`, `get_abs_dataset_structure`, `get_abs_data`, and
   `get_rba_table` when the user needs source-native ABS/RBA tables, SDMX keys, or expert control.
4. Use `list_catalogue(source="rba")` instead of the deprecated `list_rba_tables` alias in new
   integrations.

### Example client requests

In an MCP-enabled client, the user can ask for things such as:

- "Search for datasets related to trimmed mean inflation."
- "Show me the ABS structure for CPI."
- "Fetch the last 12 observations from RBA table g1."
- "Get headline CPI from 2023 onwards."
- "Get quarterly real GDP growth from 2020."
- "Compare Selected Living Cost Indexes across household types against CPI."
- "Pull the last 8 quarters of engineering construction work done."
- "Get the RBA zero-coupon yield curve for this year."

### Example retrieval patterns

Discover relevant datasets:

```text
search_datasets(query="cash rate")
```

Discover curated analyst-facing concepts:

```text
list_economic_concepts(query="cash rate")
```

Inspect active inflation tables from the preferred unranked browse surface:

```text
list_catalogue(source="rba", category="inflation", include_discontinued=True)
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
  start="2020-01-01"
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
can reference the exact release that produced them. Fresh retrievals also include
`metadata.retrieved_at`, which records when the upstream payload was fetched.
The stable retrieval contract is documented in
[`schemas/response.schema.json`](schemas/response.schema.json) and explained in
[`docs/response-schema.md`](docs/response-schema.md).

### Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUSECON_CACHE_DISABLED` | Set to `1` / `true` / `yes` to turn off **all** caching (memory and disk). Useful for debugging. | unset (caching on). |
| `AUSECON_LOG_LEVEL` | Logger level for the `ausecon_mcp` namespace (`DEBUG`, `INFO`, `WARNING`, `ERROR`). `DEBUG` enables cache-hit/miss events. | `INFO`. |

The on-disk cache location is fixed to the platform app-cache directory
(`~/.cache/ausecon-mcp/` on Linux, `~/Library/Caches/ausecon-mcp/` on macOS).
`AUSECON_CACHE_DIR` is no longer supported.
If that directory is unavailable, the server automatically falls back to
in-process memory caching for the lifetime of the process. Cross-process cache
persistence and disk-backed stale reuse are unavailable in that degraded mode.

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

Python 3.12 is recommended for local development, and the package metadata and CI matrix support
Python 3.10+.

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
2. bump `server.json` (`version` + `packages[0].version`) to the new `X.Y.Z` so the MCP registry stays in sync with PyPI; the hygiene test enforces that `server.json` matches the top `CHANGELOG.md` entry
3. create a git tag in the repository's `vX.Y.Z` format on the intended release commit
4. push the branch and the tag to GitHub
5. allow the `Release` workflow to build and publish the tagged version
6. draft the GitHub Release notes from that tag
7. re-publish `server.json` to the MCP registry with `mcp-publisher publish` so downstream directories (PulseMCP, etc.) re-scrape the new version

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

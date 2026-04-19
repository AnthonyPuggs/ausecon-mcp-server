# Ausecon v1.0.0 Roadmap Design

**Goal:** Define the shortest credible path from the current early release to a stable `v1.0.0` for `ausecon-mcp-server`.

**Decision:** Treat `v1.0.0` as a correctness, contract, and usability milestone for the existing ABS + RBA server. Do not broaden the source boundary to Treasury, ASX, or APRA before `v1.0.0`.

## Current Baseline

The server already has a coherent core:

- a thin FastMCP surface over source-specific providers
- curated ABS and RBA catalogues
- normalised response payloads
- resources and prompt templates
- retry, cache, and logging support
- unit tests and live integration checks

The main remaining weakness is not raw feature count. It is catalogue correctness and semantic coverage.

The April 2026 audit established that several ABS entries were ceased or mislabelled and that multiple RBA entries pointed at live upstream tables whose content no longer matched the catalogue description. That class of defect is more severe than ordinary breadth gaps because the server can return plausible-looking but materially wrong data.

## Scope Decision

### In Scope for v1.0.0

- ABS and RBA only
- local stdio MCP transport
- stable read-only discovery and retrieval workflows
- expanded but disciplined semantic shortcut layer
- explicit contract documentation for response shapes

### Out of Scope for v1.0.0

- Treasury as a primary statistical source
- ASX market-data integration
- APRA integration
- non-time-series RBA distribution tables that require a different response model
- broad analytical transforms beyond a very small number of obvious derived concepts
- hosted HTTP or streamable transport as a release gate

## Why Treasury, ASX, and APRA Are Not v1.0.0 Work

### Treasury

Treasury is not the right primary upstream for this server's current purpose. For official Australian macroeconomic and financial statistics, Treasury generally points users back to ABS and RBA rather than acting as the system of record for the statistical series themselves. Adding Treasury before `v1.0.0` would broaden the product without solving the core correctness and contract risks in the existing server.

### ASX

ASX is a poor fit for this release boundary. The server is currently positioned as a curated public-statistics MCP server, not a market-data product. ASX would introduce a different product category, a different user expectation set, and likely more commercial-data complications than the current public ABS and RBA surfaces.

### APRA

APRA is the only realistic next source after `v1.0.0`. It fits the macro-financial mission better than Treasury or ASX, but it is still a proper third-source expansion, not a small additive change. It should land only after the ABS + RBA contract is stable.

## Product Positioning for v1.0.0

`ausecon-mcp-server` should be described at `v1.0.0` as:

> A stable, source-aware MCP server for official Australian macroeconomic and financial data from the ABS and RBA, with curated discovery, provenance-rich retrieval, and a practical economist-facing semantic layer.

That is narrow enough to be credible and broad enough to be useful.

## Release Sequence

### v0.10.0 — Correctness and Audit Governance

This is the highest-priority tranche.

- fix all known wrong RBA catalogue mappings by relabelling or replacing entries so the catalogue matches the live upstream table
- mark ceased ABS entries correctly and remove them from ordinary discovery paths
- complete the `LCI` to `SLCI` correction and keep naming, aliases, tags, and prompts consistent
- add audit metadata consistently to catalogue entries
- build a repeatable catalogue audit script for ABS and RBA
- wire audit checks into the nightly live verification workflow

**Exit condition:** no known catalogue entry returns materially different content from its stated meaning.

### v0.11.0 — Semantic Layer and Discovery Expansion

This is the next highest-value tranche because it improves user utility without broadening the source boundary.

- expand `get_economic_series` beyond the current four shortcuts
- prioritise labour, wages, credit, external sector, and yield concepts
- add `last_n` support to `get_economic_series`
- add a filtered `list_catalogue` tool or equivalent discovery primitive for source, category, and tag browsing
- align prompts and resources with the expanded semantic layer

**Exit condition:** the server has a practical first-tier semantic surface for common macroeconomic workflows.

### v0.12.0 — Remaining In-Scope Breadth

This tranche fills obvious, still-missing ABS and RBA coverage that stays inside the current time-series contract.

- add missing or replacement catalogue entries where the current concept is important but the underlying source changed
- finish only those catalogue additions that materially support the semantic backlog
- avoid long-tail table additions that do not improve the main analyst workflows

**Exit condition:** no obvious, high-demand ABS or RBA concept is missing because of a small catalogue gap.

### v0.13.0 — Contract Freeze

This tranche turns the current informal response model into an explicit compatibility promise.

- write checked-in JSON Schemas for the main response payloads
- write example payloads for the documented happy paths
- decide whether to make one intentional response-shape cleanup before `v1.0.0`
- if a breaking cleanup is made, publish a short migration note and stop changing the response contract afterwards

**Exit condition:** payload structure is explicit, documented, and stable enough for downstream consumers to rely on.

### v0.14.0-rc1 — Release Candidate

This is the stabilisation tranche.

- documentation refresh
- architecture note
- semantic concept reference
- schema reference
- release checklist and migration note
- no contract changes during the RC window

**Exit condition:** one clean release-candidate cycle with no contract churn and no newly discovered correctness regressions.

### v1.0.0

Tag the release only after:

- unit tests are green
- live integration checks are green
- audit automation is green
- no known wrong catalogue mappings remain
- the semantic layer covers the agreed first-tier concept set
- schemas and docs reflect actual behaviour

## Semantic Layer Direction

The semantic layer should remain thin and source-aware.

That means:

- prefer source-native concepts over arbitrary computed statistics
- map each concept to one documented default series
- support variants where the catalogue already encodes defensible distinctions
- avoid turning the server into a general transformation engine before `v1.0.0`

The separate semantic-layer backlog document holds the ranked concept list and tranche ordering.

## Engineering Guidance

### Keep for v1.0.0

- thin MCP server
- source-specific providers
- static curated catalogues
- explicit validation at the tool boundary
- provenance-rich JSON payloads

### Improve Before v1.0.0

- catalogue auditability
- semantic shortcut coverage
- contract documentation
- discovery ergonomics
- test coverage around catalogue correctness and semantic defaults

### Defer Until After v1.0.0

- APRA provider work
- HTTP or streamable server transport
- extensive provider inheritance refactors
- larger derived-series framework

## Release Gates

`v1.0.0` should not ship until all of the following are true:

1. The catalogue is audit-backed and known-bad mappings are fixed.
2. Ceased entries are handled explicitly and do not pollute ordinary discovery.
3. `get_economic_series` covers the agreed first-tier concepts.
4. Response schemas are checked in and match runtime behaviour.
5. The release candidate passes one clean stabilisation cycle with no contract changes.

## Post-v1 Candidates

These are good `v1.1+` candidates:

- APRA ADI statistics as the first third source
- HTTP or streamable transport for hosted deployments
- carefully chosen derived concepts such as `yield_curve_slope`, `real_cash_rate`, and `gdp_per_capita`
- non-time-series statistical tables that require a second response model

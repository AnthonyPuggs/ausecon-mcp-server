# AusEcon MCP Roadmap

This roadmap starts from the v1.1 baseline: stable stdio, hosted Streamable HTTP through
Render/Smithery, curated ABS/RBA retrieval, generated documentation, and docs-site Vercel Analytics
plus Speed Insights.

The release strategy remains official-source-first, macro-financial, read-only, and
Australian-focused. The current response contract, `{metadata, series, observations}`, should be
preserved until a genuinely different data model is required.

## v1.1.x: operational polish

No MCP API or response-schema changes.

- Keep README and documentation wording aligned with v1.1 as the current hosted release baseline.
- Maintain static checks for the docs-site Vercel Analytics and Speed Insights integration,
  including stripping query strings and fragments before Speed Insights payloads are sent.
- Keep hosted deployment checks lightweight: `/`, `/healthz`, server-card metadata, Smithery
  listing state, and Render uptime.
- Keep full hosted MCP tool-call smoke manual unless a stable automated hosted smoke path is
  deliberately reintroduced.
- Separate MCP server observability from docs-site observability in operations documentation.

## v1.2: deeper ABS/RBA semantic coverage

Additive semantic concepts only. `list_economic_concepts` and `ausecon://concepts` should grow
automatically from resolver mappings.

First tranche now landed:

- real GDP level and nominal GDP
- household consumption and private investment
- retail turnover
- broad money
- 3-month bank bill rate

Priority concepts:

- verified monthly CPI 2.0 replacement if the ABS dataflow and default key are stable
- selected financial aggregates
- exchange-rate monthly averages
- selected housing-price or construction concepts where the upstream series is stable

Only add long-tail catalogue entries when they unlock an analyst-facing concept. Each new concept
needs verified catalogue variants, resolver tests, service forwarding tests, generated docs checks,
and bounded live integration coverage.

## v1.3: narrow derived-series layer

Add a new read-only `get_derived_series` tool rather than overloading `get_economic_series`.

Initial derived concepts should stay transparent:

- `real_cash_rate`
- `yield_curve_slope`
- `real_wage_growth`
- `credit_growth`
- `gdp_per_capita`, if population and GDP-level defaults are stable

Preserve the normal retrieval shape and add `metadata.derived` with the formula, operands, source
concepts, alignment frequency, units, and dropped-observation counts. Do not add modelling,
forecasting, seasonal adjustment, arbitrary user formulas, or user-supplied Python/R execution.

## v1.4: APRA as the first third source

APRA should come after ABS/RBA depth is materially stronger. Scope it to official public
macro-financial time series that fit `{metadata, series, observations}`.

Candidate APRA areas:

- ADI credit and deposits
- lending composition
- capital and liquidity aggregates
- arrears, if stable public series are available

Expected public API changes are additive: extend source filters to include `apra`, add a
source-native APRA retrieval tool if needed, and expose APRA-backed semantic concepts only after
fixture and live validation.

Treasury and ASX remain deferred. Treasury is not the main statistical system of record for most
target macro series, and ASX would shift the product toward market data.

## v2.0: only for a second data model

Reserve v2.0 for response-shape changes. Candidate work includes RBA distribution tables, richer
APRA institutional panels, and fiscal table families that cannot honestly fit the current
time-series response contract.

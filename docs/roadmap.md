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

Second tranche now landed:

- total credit and year-ended credit growth
- housing and business credit growth
- M3, money base, and currency in circulation
- monthly AUD/CNY, AUD/JPY, AUD/EUR, AUD/GBP, and AUD/NZD exchange rates

Third tranche now landed:

- complete ABS Monthly CPI 2.0 headline index, monthly change, and year-ended inflation
- complete ABS Monthly CPI 2.0 trimmed mean and weighted median inflation
- ABS national quarterly housing-lending commitments for total, owner-occupier, and investor
  housing lending

Priority concepts:

- ABS housing-price concepts where a clean national or default aggregate key is verified

Only add long-tail catalogue entries when they unlock an analyst-facing concept. Each new concept
needs verified catalogue variants, resolver tests, service forwarding tests, generated docs checks,
and bounded live integration coverage.

## v1.3: narrow derived-series layer

The foundation tranche is now landed: a new read-only `get_derived_series` tool exists rather than
overloading `get_economic_series`.

Initial derived concepts are intentionally transparent:

- `real_cash_rate`
- `yield_curve_slope`
- `real_wage_growth`
- `credit_growth`
- `gdp_per_capita`

The normal retrieval shape is preserved with `metadata.derived` carrying the formula, operands,
source concepts, alignment frequency, units, and dropped-observation counts. Further v1.3 work
should focus on documentation, live reliability, and small formula refinements only. Do not add
modelling, forecasting, seasonal adjustment, arbitrary user formulas, or user-supplied Python/R
execution.

## v1.4: APRA as the first third source

The APRA source-native foundation is now the next landed provider milestone. It adds curated
official APRA XLSX retrieval through `get_apra_data` while preserving
`{metadata, series, observations}` and deferring APRA semantic shortcuts until exact series
definitions are fixture-backed and live-validated.

Initial APRA publication coverage:

- Monthly Authorised Deposit-taking Institution Statistics
- Quarterly Authorised Deposit-taking Institution Performance Statistics
- Authorised Deposit-taking Institution Centralised Publication
- Quarterly Authorised Deposit-taking Institution Property Exposures Statistics

Expected public API changes are additive: source filters include `apra`, `get_apra_data` is the
source-native APRA retrieval tool, and APRA-backed semantic concepts are exposed only after
fixture and live validation.

Treasury and ASX remain deferred. Treasury is not the main statistical system of record for most
target macro series, and ASX would shift the product toward market data.

## v2.0: only for a second data model

Reserve v2.0 for response-shape changes. Candidate work includes RBA distribution tables, richer
APRA institutional panels, and fiscal table families that cannot honestly fit the current
time-series response contract.

---
title: Roadmap
description: Release priorities for AusEcon MCP.
---

The current v1.13.0 release line includes stable stdio, hosted Streamable HTTP through
Render/Smithery, curated ABS/RBA/APRA retrieval, release-event awareness, convenience observation
tools, generated documentation, and docs-site Vercel Analytics plus Speed Insights.

The roadmap stays official-source-first, macro-financial, read-only, and Australian-focused. The
current response contract, `{metadata, series, observations}`, is protected until a genuinely
different data model is required.

## v1.1.x

Operational polish only. No MCP API or response-schema changes.

- Keep release wording aligned with current release metadata.
- Keep hygiene checks around docs-site Vercel Analytics and Speed Insights.
- Keep hosted checks focused on `/`, `/healthz`, server-card metadata, Smithery listing state, and
  Render uptime.
- Keep full hosted MCP tool-call smoke manual unless a stable automated hosted smoke path is
  deliberately reintroduced.

## v1.2

Deepen ABS/RBA semantic coverage before adding new providers. The first v1.2 tranche adds real and
nominal GDP levels, household consumption, private investment, retail turnover, broad money, and a
3-month bank bill rate.

The second v1.2 tranche adds total credit, credit-growth concepts, M3, money base, currency in
circulation, and selected monthly AUD exchange rates.

The third v1.2 tranche adds complete ABS Monthly CPI 2.0 headline, monthly-change, trimmed mean,
and weighted median concepts, plus national quarterly ABS housing-lending commitments for total,
owner-occupier, and investor lending.

Remaining priority areas are ABS housing-price concepts where a clean national or default
aggregate key is verified.

Add concepts only when the upstream mapping is verified and the result fits the existing response
shape.

## v1.3

The foundation tranche adds a narrow `get_derived_series` tool with transparent formulas and
explicit provenance. The first derived concepts were `real_cash_rate`, `yield_curve_slope`,
`real_wage_growth`, `credit_growth`, and `gdp_per_capita`.

Derived responses should preserve `{metadata, series, observations}` and add `metadata.derived`.
They should not introduce modelling, forecasting, seasonal adjustment, or arbitrary user formulas.

## v1.4

The APRA source-native foundation adds curated official APRA XLSX retrieval through
`get_apra_data` while preserving `{metadata, series, observations}`. Initial coverage was limited
to Monthly ADI Statistics, Quarterly ADI Performance, the ADI Centralised Publication, and
Quarterly ADI Property Exposures.

The v1.4.1 reliability patch keeps hosted health checks responsive during APRA workbook parsing by
moving XLSX parsing off the event loop and caching requested APRA tables separately.

## v1.5

The v1.5 semantic and source expansion is landed. It adds ABS quarterly household spending,
selected RBA source-native tables, APRA superannuation and insurance publications, APRA-backed
semantic concepts, and four additional transparent derived concepts:

- `mortgage_rate_spread`
- `real_mortgage_rate`
- `credit_to_gdp`
- `household_spending_growth`

APRA semantic concepts are exposed only where exact APRA table and series identifiers are
fixture-backed. The response schema documents APRA semantic targets through `apra_table_id` and
`apra_series_ids` without changing the top-level response contract.

Treasury and ASX remain deferred. Treasury is not the main statistical system of record for most
target series, and ASX would shift the product toward market data.

## v1.6

The v1.6 work is landed. It is additive convenience and governance hardening, not a product pivot.
The surface adds latest/top observation wrappers, source-aware dataset descriptions, release-event
awareness, APRA URL seed fallback, APRA framework-break warnings, CodeQL, Dependabot, and a broader
Python CI matrix.

These tools preserve source-native identifiers and the combined ABS/RBA/APRA server shape.

## v2.0

Reserve v2.0 for a second response model: non-time-series panels, distribution tables, or
multi-dimensional public tables that cannot honestly fit `{metadata, series, observations}`.

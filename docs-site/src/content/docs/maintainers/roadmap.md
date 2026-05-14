---
title: Roadmap
description: Post-v1.1 release priorities for AusEcon MCP.
---

The v1.1 baseline includes stable stdio, hosted Streamable HTTP through Render/Smithery, curated
ABS/RBA retrieval, generated documentation, and docs-site Vercel Analytics plus Speed Insights.

The roadmap stays official-source-first, macro-financial, read-only, and Australian-focused. The
current response contract, `{metadata, series, observations}`, is protected until a genuinely
different data model is required.

## v1.1.x

Operational polish only. No MCP API or response-schema changes.

- Keep release wording aligned with v1.1 as the current hosted baseline.
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
explicit provenance. Initial derived concepts are `real_cash_rate`, `yield_curve_slope`,
`real_wage_growth`, `credit_growth`, and `gdp_per_capita`.

Derived responses should preserve `{metadata, series, observations}` and add `metadata.derived`.
They should not introduce modelling, forecasting, seasonal adjustment, or arbitrary user formulas.

## v1.4

The APRA source-native foundation adds curated official APRA XLSX retrieval through
`get_apra_data` while preserving `{metadata, series, observations}`. Initial coverage is limited to
Monthly ADI Statistics, Quarterly ADI Performance, the ADI Centralised Publication, and Quarterly
ADI Property Exposures.

APRA-backed semantic concepts remain deferred until exact series definitions are fixture-backed and
live-validated.

Treasury and ASX remain deferred. Treasury is not the main statistical system of record for most
target series, and ASX would shift the product toward market data.

## v2.0

Reserve v2.0 for a second response model: non-time-series panels, distribution tables, or
multi-dimensional public tables that cannot honestly fit `{metadata, series, observations}`.

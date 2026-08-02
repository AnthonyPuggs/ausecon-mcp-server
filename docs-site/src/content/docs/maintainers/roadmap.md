---
title: Roadmap
description: Current direction and shipped release lines for AusEcon MCP.
---

The current v1.14.x release line includes stable stdio, hosted Streamable HTTP through
Render/Smithery, curated ABS/RBA/APRA retrieval, release-event awareness, convenience observation
tools, generated documentation, and docs-site Vercel Analytics plus Speed Insights.

The roadmap stays official-source-first, macro-financial, read-only, and Australian-focused. The
current response contract, `{metadata, series, observations}`, is protected until a genuinely
different data model is required.

## Current direction

The version-numbered release lines below are complete. Work now proceeds on two tracks.

### Credibility layer

Make the server's value measurable and visible rather than asserted:

- A published, reproducible evaluation measuring how much the server improves model answers on
  Australian-economics questions, built on the existing live golden-value verification.
- An automated weekly Australian macro briefing page generated deterministically from release
  events and latest observations — no modelling, no forecasting, facts only.

### Broader Australian coverage

Additive coverage expansion, in rough order of priority:

- State and capital-city variants of existing ABS dataflows (labour force and CPI first).
- AOFM debt issuance, tender results, and outstanding-stock data as a new curated source.
- Jobs and Skills Australia Internet Vacancy Index to complement ABS job vacancies.
- A feasibility assessment of Treasury/Budget aggregates via PBO historical fiscal data.

Proprietary sources, ASX/market data, and forecasting or modelling remain out of scope.

## Shipped release lines

- **v1.1.x** — operational polish: release-metadata alignment, analytics hygiene checks, and
  lightweight hosted deployment checks. No MCP API or response-schema changes.
- **v1.2** — deeper ABS/RBA semantic coverage in three tranches: national accounts, credit and
  money aggregates, monthly CPI 2.0, and housing-lending commitments.
- **v1.3** — the narrow `get_derived_series` layer with transparent formulas and explicit
  provenance; no modelling, forecasting, seasonal adjustment, or arbitrary user formulas.
- **v1.4** — the APRA source-native foundation: curated official APRA XLSX retrieval through
  `get_apra_data`, plus the v1.4.1 reliability patch moving XLSX parsing off the event loop.
- **v1.5** — semantic and source expansion: ABS household spending, additional RBA tables, APRA
  superannuation and insurance publications, and four more derived concepts.
- **v1.6** — convenience and governance hardening: latest/top observation wrappers, dataset
  descriptions, release-event awareness, APRA URL governance, CodeQL, and a broader CI matrix.
- **v1.12–v1.14** — distribution and trust: hosted no-install path, client install configs,
  nightly live golden-value validation, housing-price concepts, the branded
  `mcp.auseconmcp.com` endpoint, and automatic MCP-registry publishing.

## v2.0

Reserve v2.0 for a second response model: non-time-series panels, distribution tables, or
multi-dimensional public tables that cannot honestly fit `{metadata, series, observations}`. The
trigger would be a new source (for example fiscal tables or institution-level panels) that the
current contract cannot represent faithfully.

# Catalogue Audit — 2026-04-18

> **Status (2026-04-19): resolved in v0.10.0** — see
> [Resolution](#resolution--v0100-2026-04-19) at the bottom for the item-by-item
> outcome. The sections below preserve the original audit findings.

Phase 0 audit of every entry in `src/ausecon_mcp/catalogue/abs.py` and
`src/ausecon_mcp/catalogue/rba.py` against live upstream sources.

- ABS source: `https://data.api.abs.gov.au/rest/dataflow/ABS/{id}/latest`
- RBA source: `https://www.rba.gov.au/statistics/tables/index.html` and
  `https://www.rba.gov.au/statistics/tables/changes-to-tables.html`

## ABS — 36 entries audited

### Ceased upstream (need `ceased: True` flag)

| Catalogue ID | Upstream name | Notes |
|---|---|---|
| `BUSINESS_TURNOVER` | Monthly Business Turnover Indicator | Ceased 2025-11-10 |
| `CPI_M` | Monthly Consumer Price Index (CPI) indicator | Ceased — replaced by ABS Monthly CPI 2.0 (different dataflow) |
| `RT` | Retail Trade | Ceased — replaced by Monthly Retail Trade (different dataflow) |
| `RPPI` | Residential Property Price Index | Ceased — replaced by new property prices dataflow |

### Mislabeled (needs full rewrite)

| Catalogue ID | Our name | Upstream name |
|---|---|---|
| `LCI` | Labour Cost Index | **Selected Living Cost Indexes** (6467.0) |

This is the most important ABS correction — `LCI` is currently described as a labour
cost measure but actually returns Selected Living Cost Indexes. All aliases, tags, and
description need to be rewritten. The actual ABS Labour Cost Index (6345.0) is a
discontinued dataset and should not be re-added under this key.

### Active with cosmetic name drift (low priority — leave or tidy)

`ITPI_EXP/IMP`, `LF_HOURS`, `LF_UNDER`, `LABOUR_ACCT_Q`, `CWD`, `RES_DWELL`,
`OAD_COUNTRY`, `PPI` — our descriptive names are reasonable substitutes for the
upstream titles. No action required unless we want strict mirroring.

### Confirmed active and correct

`CPI`, `PPI_FD`, `WPI`, `AWE`, `LF`, `JV`, `ANA_AGG`, `ANA_EXP`, `ANA_INC`,
`QBIS`, `HSI_M`, `CAPEX`, `BUILDING_ACTIVITY`, `ITGS`, `MERCH_EXP`, `MERCH_IMP`,
`BOP`, `BOP_GOODS`, `IIP`, `LEND_HOUSING`, `LEND_BUSINESS`, `LEND_PERSONAL`,
`ERP_Q`, `NOM_FY`.

## RBA — 40 entries audited

### Wrong table assignment (catalogue points to different upstream table)

The RBA reorganized table IDs over the past 18 months. Our catalogue still describes
the previous table at each ID. **The CSV download will succeed but return data for a
completely different topic than the catalogue claims.** This is the highest-severity
correctness bug in the codebase.

| Catalogue ID | Our name (wrong) | Actual upstream |
|---|---|---|
| `c7` | Payments System – Retail Payments | Real-time Gross Settlement Statistics |
| `c9` | ATM Cash Withdrawals | Domestic Banking Fees Charged |
| `d4` | Bank Lending to Business by Size and Sector | Debt Securities Outstanding |
| `d14` | Growth in Selected Financial Aggregates – Consolidated | Lending to Business – Outstanding by Size and Interest Rate Type |
| `e13` | Household Non-Financial Assets | Housing Loan Payments |
| `f4` | Australian Share Market | Advertised Deposit Rates |
| `f8` | Retail Deposit and Investment Rates | Personal Lending Rates |
| `f12` | Exchange Rates – Monthly Average | US Dollar Exchange Rates |
| `g4` | Measures of Consumer Price Inflation | Consumer Price Inflation – Monthly Collection (added Jan 2026) |
| `h2` | Household Finances – Selected Ratios | Demand and Income |
| `h4` | Business Sector Finances | Labour Costs and Productivity |
| `i2` | Australia's Foreign Assets and Liabilities | Commodity Prices |
| `i3` | Australian Exports – Values | Balance of Payments – Financial Account |
| `i4` | Australian Imports – Values | Australia's Gross Foreign Assets and Liabilities |

**14 of 40 RBA entries (35%) are wrong.** Two recovery paths per row:
1. **Relabel** to match the new upstream content (and update aliases/tags).
2. **Drop** the entry if the original topic still belongs in scope but no longer has
   an obvious table mapping — the topic data may have been split across sub-tables
   (e.g. retail payments now spans `C1.1`–`C6.1`).

Recommended approach: **relabel** all 14 to match the new upstream. We then add the
*missing* topics (retail payments, ATM withdrawals, share market, monthly exchange
rates, business sector finances, foreign assets, exports/imports) under their new
upstream IDs in Phase 3 — many already exist in the table index (`C2.1`, `C4.1`,
`F11.1`, `F12.1`, `H4`-equivalent removed, `I3`-equivalent removed, `I4`-equivalent
shifted).

### Renamed (small)

| Catalogue ID | Old name | New upstream name |
|---|---|---|
| `a1` | RBA Liabilities and Assets – Summary | RBA Balance Sheet |
| `a3` | Open Market Operations – Current | Monetary Policy Operations – Current |
| `f3` | Capital Market Yields and Spreads – Non-Government | Aggregate Measures of Australian Corporate Bond Yields |
| `f7` | Business Finance Lending Rates | Business Lending Rates |
| `f11` | Exchange Rates | Exchange Rates – Historical – Daily and Monthly |

### Status check needed

| Catalogue ID | Note |
|---|---|
| `a5` | We marked discontinued; upstream index still lists `A5` — verify whether ours is the legacy daily intervention table |

### Confirmed active and correct (or close enough)

`a2`, `c1`, `d1`, `d2`, `d3`, `d5`, `e1`, `e2`, `f1`, `f2`, `f5`, `f6`, `f15`,
`g1`, `g2`, `g3`, `h1`, `h3`, `h5`, `i1`.

### Series-level removals (informational, no catalogue action)

- `H3` — three retail sales series removed Oct 2024 (data still exists)
- `B1` — RFC money market series removed Sep 2025
- `D5` — public sector securities series removed Jul 2025

### New tables on the index, not yet in catalogue

`A3.1`, `A3.2`, `A4`, `A6`, `A7`, `B2`, `B3`, `B10`, `B11.x`, `B12.x`, `B13.x`,
`B20`, `C1.1`, `C1.2`, `C2.x`, `C3`, `C4.x`, `C5.x`, `C6.x`, `D9`, `D10`, `D11`,
`D12`, `D13`, `D14.1`, `E3`–`E7` (distribution — out of scope), `F1.1`, `F2.1`,
`F4.1`, `F9`, `F10`, `F11.1`, `F16`, `F17`, `I5`, `J1`. Phase 3 will pick from
these per the plan's priority list.

### Discontinued upstream (for awareness)

`F13`, `F14`, `F18` — discontinued May 2024. Not in our catalogue, no action.
`C1.3` — discontinued (Diners Club closure). Not in our catalogue, no action.

## Resolution — v0.10.0 (2026-04-19)

Shipped in `v0.10.0` (PR #9, tag `v0.10.0`, merge commit `e4b4554`). The
nightly Integration workflow now runs `scripts/audit_catalogue.py` against
live upstreams and surfaces drift via the `upstream-drift` issue label.

### ABS

- **Ceased flag added** to `BUSINESS_TURNOVER`, `CPI_M`, `RT`, `RPPI`
  (`ceased: True`). `search_catalogue` suppresses both `ceased` and
  `discontinued`.
- **`LCI` → `SLCI` rename** to match live ABS Selected Living Cost Indexes;
  description, aliases, tags, and category rewritten. The original ABS
  dataflow ID `LCI` is preserved via `upstream_id` indirection so resolver
  behaviour is unchanged.
- **Cosmetic name drift** — left as-is; the audit script would now surface
  any drift that matters.

### RBA

- **14 relabels** of the reassigned table IDs (`c7`, `c9`, `d4`, `d14`,
  `e13`, `f4`, `f8`, `f12`, `g4`, `h2`, `h4`, `i2`, `i3`, `i4`) — names,
  aliases, tags, and categories rewritten to match the current upstream
  table at each ID. All were shipped pre-v0.10.0 in the v0.9.0 correctness
  pass.
- **5 renames** (`a1`, `a3`, `f3`, `f7`, `f11`) aligned to current upstream
  titles.
- **`a5` status check resolved** — table is still active upstream
  (`Daily Foreign Exchange Market Intervention Transactions`).
  `discontinued: True` removed; entry recategorised under `exchange_rates`.
- **Series-level removals** (`H3`, `B1`, `D5`) — no catalogue action; noted
  in individual entry descriptions where user-facing.

### Audit governance (new in v0.10.0)

- Every catalogue entry now carries an `audit: {last_audited, upstream_url,
  upstream_title}` block; ~100 entries calibrated against live.
- `tests/test_catalogue_audit.py` enforces block presence and a 24-month
  freshness ceiling on `last_audited`.
- First post-merge nightly run: **0 drift, 0 disappeared** on both ABS and
  RBA ([run 24608965264](https://github.com/AnthonyPuggs/ausecon-mcp-server/actions/runs/24608965264)).

### Deferred to Phase 3 / future milestones

- **Uncatalogued live tables** — audit reports ~1182 ABS dataflows and
  ~28 RBA tables not in the catalogue (informational only; does not fail
  the audit). Curation is selective per the roadmap.

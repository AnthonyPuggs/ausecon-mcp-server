# Semantic Layer Expansion Design

**Goal:** Define a ranked backlog for expanding `get_economic_series` beyond the four currently shipped shortcuts.

**Current shipped concepts:** `cash_rate_target`, `headline_cpi`, `trimmed_mean_inflation`, `gdp_growth`

## Ranking Principle

The ranking balances:

1. usefulness to a broad economist audience
2. closeness to the current ABS + RBA catalogue
3. fit with the current thin resolver design

The list deliberately prefers source-native concepts over computed transforms.

## Work Codes

- `C` — existing catalogue entry is present; populate the default `abs_key` or `rba_series_ids` and add the shortcut
- `CR` — catalogue replacement or a new audited entry is required first
- `S` — service-layer derived concept
- `P` — provider or parser work required

No concepts in this document currently require `P`.

## Ranked Backlog

| Rank | Concept | Recommended Target | Proposed Default Variant | Work | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `unemployment_rate` | `ABS LF` | `unemployment_rate` | `C` | Variant already exists in the catalogue; populate `abs_key`. |
| 2 | `wage_growth` | `ABS WPI` | `headline_wpi` | `C` | Choose one canonical WPI series and document it. |
| 3 | `participation_rate` | `ABS LF` | `participation_rate` | `C` | Same pattern as unemployment. |
| 4 | `employment` | `ABS LF` | `employment` | `C` | Prefer a clean level concept before derived growth rates. |
| 5 | `weighted_median_inflation` | `RBA g1` | `weighted_median` | `C` | Variant already declared; populate `rba_series_ids`. |
| 6 | `monthly_inflation` | `RBA g4` | `headline_monthly` | `C` | Best near-term monthly inflation shortcut. |
| 7 | `trade_balance` | `ABS ITGS` | `trade_balance` | `C` | Existing `ITGS` variant is the cleanest target. |
| 8 | `government_bond_yield_10y` | `RBA f16` | `ags_10y` | `C` | Standard macro and market concept. |
| 9 | `government_bond_yield_3y` | `RBA f16` | `ags_3y` | `C` | Natural pair with the 10-year series. |
| 10 | `aud_usd` | `RBA f11` | `aud_usd` | `C` | Common FX shortcut. |
| 11 | `trade_weighted_index` | `RBA f11` | `twi` | `C` | Very common in Australian macro work. |
| 12 | `housing_credit` | `RBA d2` | `housing` | `C` | Use stock or outstanding credit, not flow lending. |
| 13 | `business_credit` | `RBA d2` | `business` | `C` | Same pattern as housing credit. |
| 14 | `current_account_balance` | `ABS BOP` | `current_account` | `C` | Canonical external-balance shortcut. |
| 15 | `underemployment_rate` | `ABS LF_UNDER` | `headline_underemployment` | `C` | Choose the national seasonally adjusted default. |
| 16 | `hours_worked` | `ABS LF_HOURS` | `headline_hours` | `C` | Valuable labour and activity bridge. |
| 17 | `job_vacancies` | `ABS JV` | `headline_vacancies` | `C` | Strong labour-tightness indicator. |
| 18 | `mortgage_rate` | `RBA f6` | `owner_occupier_variable` | `C` | Must choose and document the default loan product. |
| 19 | `business_lending_rate` | `RBA f7` | `small_business_indicator` | `C` | Useful, but default-series choice matters. |
| 20 | `population` | `ABS ERP_Q` | `headline_population` | `C` | Clean and broadly useful. |
| 21 | `inflation_expectations` | `RBA g3` | `consumer` | `C` | Good concept, but the generic label is ambiguous without a default. |
| 22 | `producer_price_inflation` | `ABS PPI` | `producer` | `C` | Could also use `PPI_FD`; choose one and stay consistent. |
| 23 | `household_spending` | `ABS HSI_M` | `headline_spending` | `C` | High-value monthly activity concept. |
| 24 | `commodity_prices` | `RBA i2` | `rba_commodity_index` | `C` | Highly relevant in Australia, though narrower than the top tranche. |
| 25 | `state_final_demand` | `ABS ANA_SFD` | `national` | `C` | Valuable once geography pass-through is clear. |
| 26 | `living_costs` | `ABS SLCI` | `employee` | `C` | Useful, but the default household type must be explicit. |
| 27 | `household_consumption` | `ABS ANA_EXP` | `household_final_consumption` | `C` | Needs one clear national-accounts target series. |
| 28 | `business_investment` | `ABS CAPEX` | `private_capex` | `C` | Decide whether this means CAPEX survey or national-accounts investment. |
| 29 | `company_profits` | `ABS QBIS` | `profits` | `C` | Useful and already signposted in the catalogue. |
| 30 | `labour_productivity` | `RBA h4` | `labour_productivity` | `C` | Requires explicit series mapping in the table. |
| 31 | `unit_labour_costs` | `RBA h4` | `unit_labour_costs` | `C` | Same issue as labour productivity. |
| 32 | `natural_increase` | `ABS ERP_COMP_Q` | `natural_increase` | `C` | Useful demographic macro input. |
| 33 | `net_overseas_migration` | `ABS ERP_COMP_Q` | `net_overseas_migration` | `C` | Strong relevance in the Australian context. |
| 34 | `deposit_rate` | `RBA f4.1` | `household_deposit_rate` | `C` | Lower priority than mortgage and business loan rates. |
| 35 | `export_prices` | `ABS PPI` | `export` | `C` | Could alternatively map to `ITPI_EXP`; choose one canonical source. |
| 36 | `import_prices` | `ABS PPI` | `import` | `C` | Same issue as export prices. |
| 37 | `new_housing_lending` | `ABS LEND_HOUSING` | `owner_occupier` | `C` | Flow concept, distinct from housing credit outstanding. |
| 38 | `new_business_lending` | `ABS LEND_BUSINESS` | `headline_business_commitments` | `C` | Flow concept for business finance. |
| 39 | `dwelling_approvals` | `ABS new audited building approvals entry` | `headline_approvals` | `CR` | Current catalogue does not have a clean approvals entry. |
| 40 | `dwelling_prices` | `ABS replacement for ceased RPPI entry` | `headline_dwelling_prices` | `CR` | Current `RPPI` entry is ceased. |
| 41 | `retail_trade` | `ABS replacement for ceased RT entry` | `headline_retail_trade` | `CR` | Current `RT` entry is ceased. |
| 42 | `gdp_per_capita` | `ABS ANA_AGG` + `ABS ERP_Q` | `derived` | `S` | Needs service-layer computation. |
| 43 | `yield_curve_slope` | `RBA f16` | `10y_minus_3y` | `S` | Very useful, but clearly derived. |
| 44 | `real_cash_rate` | `RBA a2` + inflation concept | `cash_minus_trimmed_mean` | `S` | Needs an explicit inflation convention. |
| 45 | `real_wage_growth` | `ABS WPI` + inflation concept | `wpi_minus_headline_cpi` | `S` | Also clearly derived. |

## Concepts Requiring Extra Catalogue Work Now

### Already Declared, But Still Unpopulated

- `ABS LF` — `employment`, `unemployment_rate`, `participation_rate`
- `ABS SLCI` — all household-type variants
- `ABS ITGS` — `exports`, `imports`, `trade_balance`
- `ABS BOP` — `current_account`, `capital_account`, `financial_account`
- `ABS PPI` — `producer`, `export`, `import`
- `RBA g1` — `weighted_median`
- `RBA d1` — `credit`, `money`
- `RBA d2` — `housing`, `business`, `household`
- `RBA f6` — `owner_occupier`, `investor`
- `RBA f7` — `small_business`, `large_business`
- `RBA g3` — `consumer`, `market`, `union`
- `RBA i1` — `trade`, `current_account`

### Existing Entry, But Default Series Choice Still Needs To Be Made

- `ABS WPI`
- `ABS JV`
- `ABS LF_UNDER`
- `ABS LF_HOURS`
- `ABS ERP_Q`
- `ABS HSI_M`
- `ABS CAPEX`
- `ABS ANA_EXP`
- `ABS QBIS`
- `RBA h4`
- `RBA f4.1`
- `RBA f16`
- `RBA f11`

### Replacement or New Audited Entry Required

- `dwelling_approvals`
- `dwelling_prices`
- `retail_trade`

## Recommended Tranches

### Tranche A

Ranks `1–12`

This is the best immediate semantic expansion tranche. It materially improves the server for mainstream macro, labour, inflation, credit, rates, and FX use without any provider work.

### Tranche B

Ranks `13–24`

This tranche rounds out labour slack, spending, population, and external-sector use cases.

### Tranche C

Ranks `25–38`

This tranche adds useful but slightly more niche concepts and concepts with more default-selection ambiguity.

### Tranche D

Ranks `39–45`

This tranche should come last because it either needs catalogue replacement work or moves beyond the current thin resolver design.

## Design Guidance

- keep the semantic layer source-aware and conservative
- prefer one documented default series per concept
- use variants only where the distinction is already legible in the catalogue
- avoid broad computed concepts before the source-native backlog is largely complete

## Implementation Notes (v0.11.0, Tranches A + B)

Locked decisions recorded at implementation time so future reviewers
can see why the defaults look the way they do:

- **Bond-yield tenors resolve to `f17`, not `f16`.** `f17` (zero-coupon
  yields) is the modelling-friendly series and avoids the coupon-driven
  distortions in `f16`. Series IDs: `FZCY0300D` (3y), `FZCY1000D` (10y).
- **`housing_credit` returns two SA series, not an aggregate.** The
  default resolves `d2` to `DLCACOHS` (owner-occupier) and `DLCACIHS`
  (investor). Clients that want a total can sum them; we deliberately
  do not derive an aggregate to keep provenance clean.
- **`business_credit` uses broad SA `DLCACBS`**, not the narrower
  non-financial business series, because the broad aggregate is the
  headline analysts reach for.
- **`producer_price_inflation` uses `PPI_FD`**, not the input-stage
  `PPI`, so the default matches the commonly reported final-demand
  headline.
- **`household_spending` uses `HSI_M` SA current-price totals.** The
  chain-volume Australia-total series is not cleanly exposed in
  `HSI_M`, so the current-price SA total is the least-surprising
  default.
- **`commodity_prices` uses the SDR index (`GRCPAISDR`)**, not the
  AUD-denominated variant, so AUD moves are not baked into the default.
- **`underemployment_rate` composes via structure id `DS_LF_UNDER`.**
  The dataflow id is `LF_UNDER` but the live SDMX DataStructure is
  exposed as `DS_LF_UNDER`; a new `resolve_abs_structure_id()` helper
  and an optional `structure_id` field on ABS catalogue entries route
  the structure fetch to the correct id without changing the dataflow
  id used for data requests.

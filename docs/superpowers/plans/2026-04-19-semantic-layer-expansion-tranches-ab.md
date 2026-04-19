# Semantic Layer Expansion Tranches A+B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `get_economic_series` from 4 to 28 stable semantic shortcuts by implementing the combined Tranche A and Tranche B backlog with explicit, audited ABS keys and RBA series mappings.

**Architecture:** Keep the semantic layer intentionally thin. Populate existing catalogue entries with literal ABS keys or explicit RBA `series_ids`, extend `CURATED_SHORTCUTS` so the semantic names resolve deterministically, and add a small ABS structure-resolution hardening path for entries whose live SDMX structure ID differs from the dataflow ID. Do not add new MCP tools, alter response shapes, or broaden the provider architecture.

**Tech Stack:** Python 3.10+, FastMCP, httpx, pytest, Ruff

---

## Summary

Replace the Tranche A-only rollout with a single combined implementation covering both Tranche A and Tranche B semantic concepts in one pass.

After implementation, `get_economic_series` will support:

- the 4 currently shipped concepts
- 12 Tranche A additions
- 12 Tranche B additions

Public interface impact:

- no change to the `get_economic_series` tool signature
- no change to the normalised response shape
- one internal interface addition: support an optional ABS catalogue `structure_id` so semantic resolution can fetch the correct SDMX structure when it differs from the dataflow ID

## Locked Defaults

Existing shipped defaults remain unchanged:

- `cash_rate_target` -> `a2.target` -> `ARBAMPCNCRT`
- `headline_cpi` -> `CPI.headline` -> `1.10001.10.50.Q`
- `trimmed_mean_inflation` -> `g1.trimmed_mean` -> `GCPIOCPMTMYP`
- `gdp_growth` -> `ANA_AGG.gdp_growth` -> `M2.GPM.20.AUS.Q`

### Tranche A Defaults

| Concept | Dataset | Variant | Default mapping |
| --- | --- | --- | --- |
| `employment` | `LF` | `employment` | `M3.3.1599.20.AUS.M` |
| `unemployment_rate` | `LF` | `unemployment_rate` | `M13.3.1599.20.AUS.M` |
| `participation_rate` | `LF` | `participation_rate` | `M12.3.1599.20.AUS.M` |
| `wage_growth` | `WPI` | `headline_wpi` | `3.THRPEB.7.TOT.20.AUS.Q` |
| `trade_balance` | `ITGS` | `trade_balance` | `M1.170.20.AUS.M` |
| `weighted_median_inflation` | `g1` | `weighted_median` | `GCPIOCPMWMYP` |
| `monthly_inflation` | `g4` | `headline_monthly` | `GCPIAGSAMP` |
| `aud_usd` | `f11` | `aud_usd` | `FXRUSD` |
| `trade_weighted_index` | `f11` | `twi` | `FXRTWI` |
| `government_bond_yield_3y` | `f17` | `ags_3y` | `FZCY300D` |
| `government_bond_yield_10y` | `f17` | `ags_10y` | `FZCY1000D` |
| `housing_credit` | `d2` | `housing` | `DLCACOHS`, `DLCACIHS` |

### Tranche B Defaults

| Concept | Dataset | Variant | Default mapping |
| --- | --- | --- | --- |
| `business_credit` | `d2` | `business` | `DLCACBS` |
| `current_account_balance` | `BOP` | `current_account` | `1.100.20.Q` |
| `underemployment_rate` | `LF_UNDER` | `headline_underemployment` | `M23.3.1599.20.AUS.M` |
| `hours_worked` | `LF_HOURS` | `headline_hours` | `M18.3.1599.TOT.20.AUS.M` |
| `job_vacancies` | `JV` | `headline_vacancies` | `M1.7.TOT.20.AUS.Q` |
| `mortgage_rate` | `f6` | `owner_occupier_variable` | `FLRHOOVA` |
| `business_lending_rate` | `f7` | `small_business_indicator` | `FLRBFOSBT` |
| `population` | `ERP_Q` | `headline_population` | `1.3.TOT.AUS.Q` |
| `inflation_expectations` | `g3` | `consumer` | `GCONEXP` |
| `producer_price_inflation` | `PPI_FD` | `producer` | `3.TOT.TOT.TOTXE.Q` |
| `household_spending` | `HSI_M` | `headline_spending` | `7.TOT.CUR.20.AUS.M` |
| `commodity_prices` | `i2` | `rba_commodity_index` | `GRCPAISDR` |

Locked choices that must not be reopened during implementation:

- Use `f17`, not `f16`, for tenor yield concepts.
- `housing_credit` returns two seasonally adjusted series from `d2`; do not derive an aggregate.
- `business_credit` uses the broad seasonally adjusted business-credit series `DLCACBS`, not the narrower non-financial-business series.
- `producer_price_inflation` uses `PPI_FD`, not `PPI`.
- `household_spending` uses the seasonally adjusted current-price total because the current `HSI_M` slice does not expose a clean Australia-total chain-volume default.
- `commodity_prices` uses the all-items SDR index to avoid baking AUD moves into the default commodity-price concept.

## Key Implementation Changes

### Resolver and ABS Structure Hardening

- Extend `CURATED_SHORTCUTS` to include all 24 new Tranche A+B concept names.
- Add an internal ABS structure-resolution helper, `resolve_abs_structure_id()`, parallel to `resolve_abs_dataflow_id()`.
- Add an optional `structure_id` field on ABS catalogue entries; default behaviour remains “use the dataset ID”.
- Set `LF_UNDER.structure_id = "DS_LF_UNDER"` and use that mapping whenever semantic resolution needs to fetch an ABS structure for key composition.
- Keep `get_economic_series` unchanged externally; the structure-ID mapping is internal only.

This hardening is required because `LF_UNDER` is a valid ABS dataflow but its live structure is exposed under `DS_LF_UNDER`, not `LF_UNDER`. Without this change, future semantic calls that require ABS structure composition for `LF_UNDER` will fail even though the dataflow itself is correct.

### ABS Catalogue Population

Populate only the ABS variants required by Tranches A+B:

- `LF`: `employment`, `unemployment_rate`, `participation_rate`
- `WPI`: `headline_wpi`
- `ITGS`: `trade_balance`
- `LF_UNDER`: `headline_underemployment`
- `LF_HOURS`: `headline_hours`
- `JV`: `headline_vacancies`
- `ERP_Q`: `headline_population`
- `BOP`: `current_account`
- `PPI_FD`: `producer`
- `HSI_M`: `headline_spending`

Do not opportunistically fill unrelated placeholder variants in the same pass unless they are needed by Tranches A+B.

### RBA Catalogue Population

Populate only the RBA variants required by Tranches A+B:

- `g1`: `weighted_median`
- `g4`: `headline_monthly`
- `f11`: `aud_usd`, `twi`
- `f17`: `ags_3y`, `ags_10y`
- `d2`: `housing`, `business`
- `f6`: `owner_occupier_variable`
- `f7`: `small_business_indicator`
- `g3`: `consumer`
- `i2`: `rba_commodity_index`

### Tests and Documentation

Expand tests in three layers:

- resolver tests for every new concept, asserting the expected dataset, variant, and ABS key or RBA `series_ids`
- service tests asserting that `AuseconService.get_economic_series()` forwards the exact keys and `series_ids` to the underlying providers
- live semantic smoke tests covering both tranches, including `underemployment_rate`, `hours_worked`, `current_account_balance`, `mortgage_rate`, `population`, and `commodity_prices`, in addition to the Tranche A live cases

Update README and semantic design docs so they:

- list all 28 supported shortcuts
- document the grouped default mappings
- explicitly explain the `f17` yield choice, the two-series `housing_credit` default, the `PPI_FD` producer-price choice, and the `LF_UNDER` structure-ID nuance

## Test Plan

The implementation is complete only when all of the following pass:

- resolver tests for all 24 new concepts
- service forwarding tests for all 24 new concepts
- helper tests for `resolve_abs_structure_id()`:
  - unknown key passes through unchanged
  - a catalogue entry without `structure_id` falls back to the dataset ID
  - `LF_UNDER` returns `DS_LF_UNDER`
- one `LF_UNDER` semantic resolution test confirming structure-based resolution works with the mapped structure ID rather than failing on a 404
- live semantic smoke tests for both tranches
- existing repository hygiene tests after README updates
- full `pytest` suite
- full Ruff check

Representative live scenarios that should be present:

- `unemployment_rate`
- `wage_growth`
- `monthly_inflation`
- `government_bond_yield_10y`
- `housing_credit`
- `current_account_balance`
- `underemployment_rate`
- `mortgage_rate`
- `population`
- `commodity_prices`

## Assumptions and Defaults

- No new MCP tools, prompts, or response-shape changes are part of this plan.
- `last_n` support for `get_economic_series` is not part of this plan.
- No provider base-class refactor is part of this plan.
- No derived concepts are included beyond the locked multi-series `housing_credit` default.
- The implementation remains narrowly scoped to ABS + RBA only.
- This combined plan supersedes the Tranche A-only plan for execution purposes.

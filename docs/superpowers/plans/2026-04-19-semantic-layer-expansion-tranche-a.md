# Semantic Layer Expansion Tranche A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `get_economic_series` from 4 to 16 stable semantic shortcuts by implementing the Tranche A backlog with explicit, audited ABS keys and RBA series mappings.

**Architecture:** Keep the semantic layer thin. Populate existing catalogue entries with literal ABS keys or explicit RBA `series_ids`, then extend `CURATED_SHORTCUTS` in the resolver so `get_economic_series` remains a small source-aware routing layer over existing ABS and RBA providers. For tenor yields, use `f17` zero-coupon tenor series rather than `f16` bond-line series; for `housing_credit`, deliberately return the two seasonally adjusted housing-credit components because `d2` does not expose a single clean total-housing series in the current curated slice.

**Tech Stack:** Python 3.10+, FastMCP, httpx, pytest, Ruff

---

## Locked Mapping Decisions

These defaults should be treated as implementation decisions for Tranche A, not open questions:

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

### Tranche B Reference Defaults

These defaults are locked for planning consistency, but they are not part of the executable scope of this Tranche A implementation plan. They should be reused when the Tranche B implementation plan is written.

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

Tranche B notes:

- `producer_price_inflation` is locked to `PPI_FD`, not `PPI`, because the final-demand year-ended series is the cleaner headline producer-price default.
- `household_spending` is locked to the seasonally adjusted current-price total because the current `HSI_M` slice does not expose a clean Australia-total chain-volume series under the same semantic surface.
- `commodity_prices` is locked to the all-items SDR index so the default is less mechanically driven by AUD movements.

## File Map

- Modify: `src/ausecon_mcp/catalogue/abs.py`
  Purpose: populate `LF`, `WPI`, and `ITGS` variants used by the new ABS semantic shortcuts.
- Modify: `src/ausecon_mcp/catalogue/rba.py`
  Purpose: populate `g1`, `g4`, `f11`, `f17`, and `d2` variants used by the new RBA semantic shortcuts.
- Modify: `src/ausecon_mcp/catalogue/resolver.py`
  Purpose: extend `CURATED_SHORTCUTS` so the new concept names resolve deterministically.
- Modify: `tests/test_resolver.py`
  Purpose: lock the resolver contract for new ABS and RBA shortcuts and update shortcut-coverage assertions.
- Modify: `tests/test_server.py`
  Purpose: verify `AuseconService.get_economic_series()` forwards the expected ABS keys and RBA series lists.
- Create: `integration_tests/test_semantic_live.py`
  Purpose: add live smoke tests over representative semantic shortcuts so drift in upstream mappings is visible.
- Modify: `README.md`
  Purpose: document the expanded semantic surface and the exact default mappings.
- Modify: `docs/superpowers/specs/2026-04-19-semantic-layer-expansion-design.md`
  Purpose: record the implementation choice to use `f17` for tenor yields and a two-series default for `housing_credit`.

### Task 1: Add failing tests for the new ABS semantic shortcuts

**Files:**
- Modify: `tests/test_resolver.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Add resolver tests for the new ABS defaults**

Insert the following parametrised test block into `tests/test_resolver.py` near the existing shortcut tests:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("concept", "dataset_id", "abs_key", "variant"),
    [
        ("employment", "LF", "M3.3.1599.20.AUS.M", "employment"),
        ("unemployment_rate", "LF", "M13.3.1599.20.AUS.M", "unemployment_rate"),
        ("participation_rate", "LF", "M12.3.1599.20.AUS.M", "participation_rate"),
        ("wage_growth", "WPI", "3.THRPEB.7.TOT.20.AUS.Q", "headline_wpi"),
        ("trade_balance", "ITGS", "M1.170.20.AUS.M", "trade_balance"),
    ],
)
async def test_resolve_abs_tranche_a_shortcuts_default_to_expected_keys(
    concept: str,
    dataset_id: str,
    abs_key: str,
    variant: str,
) -> None:
    result = await resolve(concept)

    assert result.source == "abs"
    assert result.dataset_id == dataset_id
    assert result.abs_key == abs_key
    assert result.variant == variant
```

Also replace the current shortcut coverage assertion with this exact set:

```python
def test_curated_shortcuts_cover_semantic_tranche_a_concepts() -> None:
    assert set(CURATED_SHORTCUTS) == {
        "aud_usd",
        "cash_rate_target",
        "employment",
        "gdp_growth",
        "government_bond_yield_10y",
        "government_bond_yield_3y",
        "headline_cpi",
        "housing_credit",
        "monthly_inflation",
        "participation_rate",
        "trade_balance",
        "trade_weighted_index",
        "trimmed_mean_inflation",
        "unemployment_rate",
        "wage_growth",
        "weighted_median_inflation",
    }
```

- [ ] **Step 2: Add service forwarding tests for the new ABS defaults**

Insert the following block into `tests/test_server.py` near the existing `get_economic_series` service tests:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("concept", "dataset_id", "key"),
    [
        ("employment", "LF", "M3.3.1599.20.AUS.M"),
        ("unemployment_rate", "LF", "M13.3.1599.20.AUS.M"),
        ("participation_rate", "LF", "M12.3.1599.20.AUS.M"),
        ("wage_growth", "WPI", "3.THRPEB.7.TOT.20.AUS.Q"),
        ("trade_balance", "ITGS", "M1.170.20.AUS.M"),
    ],
)
async def test_service_forwards_default_abs_keys_for_tranche_a_shortcuts(
    concept: str,
    dataset_id: str,
    key: str,
) -> None:
    abs_provider = StubABSProvider()
    service = AuseconService(abs_provider=abs_provider, rba_provider=StubRBAProvider())

    await service.get_economic_series(concept)

    assert abs_provider.last_get_data_kwargs is not None
    assert abs_provider.last_get_data_kwargs["dataflow_id"] == dataset_id
    assert abs_provider.last_get_data_kwargs["key"] == key
```

- [ ] **Step 3: Run the targeted tests and confirm they fail**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_resolver.py tests/test_server.py -k "employment or unemployment_rate or participation_rate or wage_growth or trade_balance or semantic_tranche_a" -v
```

Expected: `FAIL` because the new concepts are not yet present in `CURATED_SHORTCUTS`, and the shortcut coverage assertion still reflects the four-concept baseline.

- [ ] **Step 4: Populate the ABS catalogue and resolver**

Update `src/ausecon_mcp/catalogue/abs.py` with these exact variant definitions:

```python
"WPI": {
    "id": "WPI",
    "source": "abs",
    "name": "Wage Price Index",
    "description": "Wage inflation across sectors and industries in Australia.",
    "frequency": "Quarterly",
    "category": "prices_inflation",
    "aliases": [
        "wpi",
        "wage price index",
        "wage inflation",
    ],
    "tags": [
        "wages",
        "labour costs",
        "earnings",
    ],
    "frequencies": ["Q"],
    "geographies": ["national"],
    "variants": [
        {
            "name": "headline_wpi",
            "aliases": ["wage growth", "headline wage growth", "year-ended wage growth"],
            "abs_key": "3.THRPEB.7.TOT.20.AUS.Q",
        },
    ],
    "audit": {
        "last_audited": "2026-04-18",
        "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/WPI/latest",
        "upstream_title": "Wage Price Index",
    },
},
```

Replace the existing `variants` list inside `LF` with:

```python
"variants": [
    {
        "name": "employment",
        "aliases": ["employed persons"],
        "abs_key": "M3.3.1599.20.AUS.M",
    },
    {
        "name": "unemployment_rate",
        "aliases": ["unemployment", "jobless rate"],
        "abs_key": "M13.3.1599.20.AUS.M",
    },
    {
        "name": "participation_rate",
        "aliases": ["participation"],
        "abs_key": "M12.3.1599.20.AUS.M",
    },
],
```

Replace the existing `variants` list inside `ITGS` with:

```python
"variants": [
    {"name": "exports", "aliases": [], "abs_key": None},
    {"name": "imports", "aliases": [], "abs_key": None},
    {
        "name": "trade_balance",
        "aliases": ["net exports"],
        "abs_key": "M1.170.20.AUS.M",
    },
],
```

Then extend `CURATED_SHORTCUTS` in `src/ausecon_mcp/catalogue/resolver.py` with these entries:

```python
CURATED_SHORTCUTS: dict[str, dict[str, Any]] = {
    "cash_rate_target": {"source": "rba", "dataset_id": "a2", "variant": "target"},
    "headline_cpi": {"source": "abs", "dataset_id": "CPI", "variant": "headline"},
    "trimmed_mean_inflation": {"source": "rba", "dataset_id": "g1", "variant": "trimmed_mean"},
    "gdp_growth": {"source": "abs", "dataset_id": "ANA_AGG", "variant": "gdp_growth"},
    "employment": {"source": "abs", "dataset_id": "LF", "variant": "employment"},
    "unemployment_rate": {"source": "abs", "dataset_id": "LF", "variant": "unemployment_rate"},
    "participation_rate": {"source": "abs", "dataset_id": "LF", "variant": "participation_rate"},
    "wage_growth": {"source": "abs", "dataset_id": "WPI", "variant": "headline_wpi"},
    "trade_balance": {"source": "abs", "dataset_id": "ITGS", "variant": "trade_balance"},
}
```

- [ ] **Step 5: Re-run the targeted ABS tests and confirm they pass**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_resolver.py tests/test_server.py -k "employment or unemployment_rate or participation_rate or wage_growth or trade_balance or semantic_tranche_a" -v
```

Expected: `PASS` for the new ABS resolver and service tests.

- [ ] **Step 6: Commit the ABS semantic shortcut tranche**

```bash
git add src/ausecon_mcp/catalogue/abs.py src/ausecon_mcp/catalogue/resolver.py tests/test_resolver.py tests/test_server.py
git commit -m "feat: add abs semantic shortcut tranche"
```

### Task 2: Add failing tests and implementation for RBA inflation and FX shortcuts

**Files:**
- Modify: `tests/test_resolver.py`
- Modify: `tests/test_server.py`
- Modify: `src/ausecon_mcp/catalogue/rba.py`
- Modify: `src/ausecon_mcp/catalogue/resolver.py`

- [ ] **Step 1: Add resolver tests for weighted median, monthly inflation, and FX**

Insert this block into `tests/test_resolver.py` after the ABS tranche tests:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("concept", "dataset_id", "series_ids", "variant"),
    [
        ("weighted_median_inflation", "g1", ["GCPIOCPMWMYP"], "weighted_median"),
        ("monthly_inflation", "g4", ["GCPIAGSAMP"], "headline_monthly"),
        ("aud_usd", "f11", ["FXRUSD"], "aud_usd"),
        ("trade_weighted_index", "f11", ["FXRTWI"], "twi"),
    ],
)
async def test_resolve_rba_inflation_and_fx_tranche_defaults(
    concept: str,
    dataset_id: str,
    series_ids: list[str],
    variant: str,
) -> None:
    result = await resolve(concept)

    assert result.source == "rba"
    assert result.dataset_id == dataset_id
    assert result.rba_series_ids == series_ids
    assert result.variant == variant
```

- [ ] **Step 2: Add service forwarding tests for the same RBA concepts**

Insert this block into `tests/test_server.py`:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("concept", "table_id", "series_ids"),
    [
        ("weighted_median_inflation", "g1", ["GCPIOCPMWMYP"]),
        ("monthly_inflation", "g4", ["GCPIAGSAMP"]),
        ("aud_usd", "f11", ["FXRUSD"]),
        ("trade_weighted_index", "f11", ["FXRTWI"]),
    ],
)
async def test_service_forwards_default_rba_series_ids_for_inflation_and_fx_tranche(
    concept: str,
    table_id: str,
    series_ids: list[str],
) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series(concept)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == table_id
    assert rba.last_get_table_kwargs["series_ids"] == series_ids
```

- [ ] **Step 3: Run the targeted tests and confirm they fail**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_resolver.py tests/test_server.py -k "weighted_median_inflation or monthly_inflation or aud_usd or trade_weighted_index" -v
```

Expected: `FAIL` because the new shortcuts do not yet exist, `g1.weighted_median` is still unpopulated, and `g4` / `f11` currently have no variants.

- [ ] **Step 4: Populate the RBA catalogue entries and resolver shortcuts**

Update `src/ausecon_mcp/catalogue/rba.py` with the following exact variant definitions:

Replace the existing `variants` list inside `g1` with:

```python
"variants": [
    {
        "name": "headline",
        "aliases": ["headline cpi", "cpi"],
        "rba_series_ids": ["GCPIAG"],
    },
    {
        "name": "trimmed_mean",
        "aliases": ["core", "trimmed mean inflation"],
        "rba_series_ids": ["GCPIOCPMTMYP"],
    },
    {
        "name": "weighted_median",
        "aliases": ["weighted median inflation"],
        "rba_series_ids": ["GCPIOCPMWMYP"],
    },
],
```

Replace the existing `variants` list inside `g4` with:

```python
"variants": [
    {
        "name": "headline_monthly",
        "aliases": ["monthly inflation", "monthly cpi"],
        "rba_series_ids": ["GCPIAGSAMP"],
    },
],
```

Replace the existing `variants` list inside `f11` with:

```python
"variants": [
    {
        "name": "aud_usd",
        "aliases": ["a$1=usd", "aud usd", "aud/usd"],
        "rba_series_ids": ["FXRUSD"],
    },
    {
        "name": "twi",
        "aliases": ["trade weighted index", "trade-weighted index"],
        "rba_series_ids": ["FXRTWI"],
    },
],
```

Then extend `CURATED_SHORTCUTS` in `src/ausecon_mcp/catalogue/resolver.py` with:

```python
    "weighted_median_inflation": {
        "source": "rba",
        "dataset_id": "g1",
        "variant": "weighted_median",
    },
    "monthly_inflation": {"source": "rba", "dataset_id": "g4", "variant": "headline_monthly"},
    "aud_usd": {"source": "rba", "dataset_id": "f11", "variant": "aud_usd"},
    "trade_weighted_index": {"source": "rba", "dataset_id": "f11", "variant": "twi"},
```

- [ ] **Step 5: Re-run the targeted tests and confirm they pass**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_resolver.py tests/test_server.py -k "weighted_median_inflation or monthly_inflation or aud_usd or trade_weighted_index" -v
```

Expected: `PASS` for the new RBA inflation and FX tests.

- [ ] **Step 6: Commit the RBA inflation and FX shortcut tranche**

```bash
git add src/ausecon_mcp/catalogue/rba.py src/ausecon_mcp/catalogue/resolver.py tests/test_resolver.py tests/test_server.py
git commit -m "feat: add rba inflation and fx semantic shortcuts"
```

### Task 3: Implement yield and housing-credit semantics with explicit design notes

**Files:**
- Modify: `tests/test_resolver.py`
- Modify: `tests/test_server.py`
- Modify: `src/ausecon_mcp/catalogue/rba.py`
- Modify: `src/ausecon_mcp/catalogue/resolver.py`
- Modify: `docs/superpowers/specs/2026-04-19-semantic-layer-expansion-design.md`

- [ ] **Step 1: Add failing tests for the yield and housing-credit concepts**

Insert this block into `tests/test_resolver.py`:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("concept", "dataset_id", "series_ids", "variant"),
    [
        ("government_bond_yield_3y", "f17", ["FZCY300D"], "ags_3y"),
        ("government_bond_yield_10y", "f17", ["FZCY1000D"], "ags_10y"),
        ("housing_credit", "d2", ["DLCACOHS", "DLCACIHS"], "housing"),
    ],
)
async def test_resolve_rba_yield_and_credit_tranche_defaults(
    concept: str,
    dataset_id: str,
    series_ids: list[str],
    variant: str,
) -> None:
    result = await resolve(concept)

    assert result.source == "rba"
    assert result.dataset_id == dataset_id
    assert result.rba_series_ids == series_ids
    assert result.variant == variant
```

Insert this block into `tests/test_server.py`:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("concept", "table_id", "series_ids"),
    [
        ("government_bond_yield_3y", "f17", ["FZCY300D"]),
        ("government_bond_yield_10y", "f17", ["FZCY1000D"]),
        ("housing_credit", "d2", ["DLCACOHS", "DLCACIHS"]),
    ],
)
async def test_service_forwards_default_rba_series_ids_for_yield_and_credit_tranche(
    concept: str,
    table_id: str,
    series_ids: list[str],
) -> None:
    rba = StubRBAProvider()
    service = AuseconService(abs_provider=StubABSProvider(), rba_provider=rba)

    await service.get_economic_series(concept)

    assert rba.last_get_table_kwargs is not None
    assert rba.last_get_table_kwargs["table_id"] == table_id
    assert rba.last_get_table_kwargs["series_ids"] == series_ids
```

- [ ] **Step 2: Run the targeted tests and confirm they fail**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_resolver.py tests/test_server.py -k "government_bond_yield_3y or government_bond_yield_10y or housing_credit" -v
```

Expected: `FAIL` because the concepts are absent from `CURATED_SHORTCUTS`, `f17` has no variants, and `d2.housing` is still unpopulated.

- [ ] **Step 3: Populate the `f17` and `d2` catalogue variants and wire the resolver**

Update `src/ausecon_mcp/catalogue/rba.py`:

Replace the existing `variants` list inside `f17` with:

```python
"variants": [
    {
        "name": "ags_3y",
        "aliases": ["3 year", "3-year", "3y"],
        "rba_series_ids": ["FZCY300D"],
    },
    {
        "name": "ags_10y",
        "aliases": ["10 year", "10-year", "10y"],
        "rba_series_ids": ["FZCY1000D"],
    },
],
```

Replace the existing `variants` list inside `d2` with:

```python
"variants": [
    {
        "name": "housing",
        "aliases": ["housing credit"],
        "rba_series_ids": ["DLCACOHS", "DLCACIHS"],
    },
    {"name": "business", "aliases": ["business credit"], "rba_series_ids": None},
    {"name": "household", "aliases": ["household credit"], "rba_series_ids": None},
],
```

Then extend `CURATED_SHORTCUTS` in `src/ausecon_mcp/catalogue/resolver.py`:

```python
    "government_bond_yield_3y": {"source": "rba", "dataset_id": "f17", "variant": "ags_3y"},
    "government_bond_yield_10y": {"source": "rba", "dataset_id": "f17", "variant": "ags_10y"},
    "housing_credit": {"source": "rba", "dataset_id": "d2", "variant": "housing"},
```

- [ ] **Step 4: Record the design choice in the semantic design spec**

Add this note to `docs/superpowers/specs/2026-04-19-semantic-layer-expansion-design.md` immediately after the ranked backlog table:

```md
## Tranche A Implementation Notes

- `government_bond_yield_3y` and `government_bond_yield_10y` should resolve to `RBA f17`, not `f16`. `f16` is bond-line data keyed to individual securities, while the semantic layer needs clean tenor defaults.
- `housing_credit` should resolve to the two seasonally adjusted housing-credit component series in `d2` (`DLCACOHS`, `DLCACIHS`) because the current curated slice does not expose a single clean headline housing-credit total.
```

- [ ] **Step 5: Re-run the targeted tests and confirm they pass**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_resolver.py tests/test_server.py -k "government_bond_yield_3y or government_bond_yield_10y or housing_credit" -v
```

Expected: `PASS` for the yield and housing-credit tests.

- [ ] **Step 6: Commit the yield and housing-credit tranche**

```bash
git add src/ausecon_mcp/catalogue/rba.py src/ausecon_mcp/catalogue/resolver.py tests/test_resolver.py tests/test_server.py docs/superpowers/specs/2026-04-19-semantic-layer-expansion-design.md
git commit -m "feat: add yield and housing credit semantic shortcuts"
```

### Task 4: Add live smoke coverage for the semantic layer

**Files:**
- Create: `integration_tests/test_semantic_live.py`

- [ ] **Step 1: Add a live semantic smoke-test file**

Create `integration_tests/test_semantic_live.py` with this exact content:

```python
from __future__ import annotations

import pytest

from ausecon_mcp.providers.abs import ABSProvider
from ausecon_mcp.providers.rba import RBAProvider
from ausecon_mcp.server import AuseconService

pytestmark = pytest.mark.asyncio


def _service() -> AuseconService:
    return AuseconService(abs_provider=ABSProvider(), rba_provider=RBAProvider())


async def test_semantic_unemployment_rate_live_returns_observations() -> None:
    service = _service()

    result = await service.get_economic_series("unemployment_rate", start="2024-01")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "LF"
    assert result["observations"]


async def test_semantic_wage_growth_live_returns_observations() -> None:
    service = _service()

    result = await service.get_economic_series("wage_growth", start="2023-Q1")

    assert result["metadata"]["source"] == "abs"
    assert result["metadata"]["dataset_id"] == "WPI"
    assert result["observations"]


async def test_semantic_monthly_inflation_live_returns_expected_series() -> None:
    service = _service()

    result = await service.get_economic_series("monthly_inflation", start="2024-01-01")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "g4"
    assert {item["series_id"] for item in result["series"]} == {"GCPIAGSAMP"}


async def test_semantic_government_bond_yield_10y_live_returns_expected_series() -> None:
    service = _service()

    result = await service.get_economic_series("government_bond_yield_10y", start="2024-01-01")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "f17"
    assert {item["series_id"] for item in result["series"]} == {"FZCY1000D"}


async def test_semantic_housing_credit_live_returns_two_series() -> None:
    service = _service()

    result = await service.get_economic_series("housing_credit", start="2024-01-01")

    assert result["metadata"]["source"] == "rba"
    assert result["metadata"]["dataset_id"] == "d2"
    assert {item["series_id"] for item in result["series"]} == {"DLCACOHS", "DLCACIHS"}
```

- [ ] **Step 2: Run the live semantic smoke tests**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest integration_tests/test_semantic_live.py -v
```

Expected: `PASS`. If a live test fails because upstream changed, stop and update the catalogue mapping before continuing.

- [ ] **Step 3: Commit the live smoke coverage**

```bash
git add integration_tests/test_semantic_live.py
git commit -m "test: add live semantic smoke coverage"
```

### Task 5: Update the public documentation and run the full verification suite

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Expand the supported semantic concepts section in the README**

Replace the current four-item semantic list in `README.md` with this exact list:

```md
`get_economic_series` currently supports:

- `cash_rate_target`
- `headline_cpi`
- `trimmed_mean_inflation`
- `gdp_growth`
- `employment`
- `unemployment_rate`
- `participation_rate`
- `wage_growth`
- `trade_balance`
- `weighted_median_inflation`
- `monthly_inflation`
- `aud_usd`
- `trade_weighted_index`
- `government_bond_yield_3y`
- `government_bond_yield_10y`
- `housing_credit`
```

Then replace the default-mapping bullet list with:

```md
By default, these currently resolve to the following narrowed series:

- `cash_rate_target` -> RBA `a2` cash rate target series (`ARBAMPCNCRT`)
- `headline_cpi` -> ABS `CPI` all groups CPI index for Australia, quarterly (`1.10001.10.50.Q`)
- `trimmed_mean_inflation` -> RBA `g1` year-ended trimmed mean inflation (`GCPIOCPMTMYP`)
- `gdp_growth` -> ABS `ANA_AGG` quarterly real GDP growth (`M2.GPM.20.AUS.Q`)
- `employment` -> ABS `LF` employed persons, seasonally adjusted (`M3.3.1599.20.AUS.M`)
- `unemployment_rate` -> ABS `LF` unemployment rate, seasonally adjusted (`M13.3.1599.20.AUS.M`)
- `participation_rate` -> ABS `LF` participation rate, seasonally adjusted (`M12.3.1599.20.AUS.M`)
- `wage_growth` -> ABS `WPI` year-ended total hourly wage growth excluding bonuses, seasonally adjusted (`3.THRPEB.7.TOT.20.AUS.Q`)
- `trade_balance` -> ABS `ITGS` balance on goods, seasonally adjusted (`M1.170.20.AUS.M`)
- `weighted_median_inflation` -> RBA `g1` year-ended weighted median inflation (`GCPIOCPMWMYP`)
- `monthly_inflation` -> RBA `g4` monthly inflation, seasonally adjusted (`GCPIAGSAMP`)
- `aud_usd` -> RBA `f11` AUD/USD exchange rate (`FXRUSD`)
- `trade_weighted_index` -> RBA `f11` trade-weighted index (`FXRTWI`)
- `government_bond_yield_3y` -> RBA `f17` three-year zero-coupon yield (`FZCY300D`)
- `government_bond_yield_10y` -> RBA `f17` ten-year zero-coupon yield (`FZCY1000D`)
- `housing_credit` -> RBA `d2` seasonally adjusted owner-occupier and investor housing credit (`DLCACOHS`, `DLCACIHS`)
```

- [ ] **Step 2: Run the focused documentation and hygiene tests**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_repository_hygiene.py tests/test_resolver.py tests/test_server.py integration_tests/test_semantic_live.py -v
```

Expected: `PASS`.

- [ ] **Step 3: Run the full repository verification suite**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest
env UV_CACHE_DIR=.uv-cache uv run ruff check src tests integration_tests
```

Expected: both commands finish cleanly with no test failures and no Ruff findings.

- [ ] **Step 4: Commit the documentation and final verification pass**

```bash
git add README.md
git commit -m "docs: document semantic shortcut tranche a"
```

## Completion Criteria

The implementation is complete when all of the following are true:

- `get_economic_series` supports 16 documented shortcuts: the original 4 plus the 12 Tranche A additions.
- All new shortcuts resolve without fallback ambiguity.
- `government_bond_yield_3y` and `government_bond_yield_10y` resolve to `f17`, not `f16`.
- `housing_credit` deliberately returns two seasonally adjusted series from `d2`.
- `tests/test_resolver.py`, `tests/test_server.py`, and `integration_tests/test_semantic_live.py` all pass.
- `README.md` and the semantic design spec describe the implemented mappings accurately.

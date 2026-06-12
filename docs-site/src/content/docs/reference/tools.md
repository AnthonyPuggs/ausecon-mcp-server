---
title: Tools
description: The MCP tool surface exposed by ausecon-mcp-server.
---

All tools are read-only and use `openWorldHint` because they retrieve external, evolving ABS, RBA,
and APRA data.

| Tool | Purpose | Key inputs |
| --- | --- | --- |
| `search_datasets` | Search the curated ABS, RBA, and APRA catalogue with deterministic ranking. | `query`, `source` |
| `list_catalogue` | List catalogue entries unranked, optionally filtered by source, category, or tag. | `source`, `category`, `tag`, `include_ceased`, `include_discontinued` |
| `list_economic_concepts` | List semantic concepts accepted by `get_economic_series`. | `query`, `source`, `category` |
| `get_abs_dataset_structure` | Retrieve ABS SDMX dimensions and code lists. | `dataflow_id` |
| `get_abs_data` | Retrieve ABS data in a normalised response shape. | `dataflow_id`, `key`, `start_period`, `end_period`, `last_n`, `updated_after` |
| `list_rba_tables` | Deprecated compatibility alias for curated RBA tables. | `category`, `include_discontinued` |
| `get_rba_table` | Retrieve an RBA statistical table in a normalised response shape. | `table_id`, `series_ids`, `start_date`, `end_date`, `last_n` |
| `get_apra_data` | Retrieve a curated official APRA XLSX publication in a normalised response shape. | `publication_id`, `table_id`, `series_ids`, `start_date`, `end_date`, `last_n` |
| `get_economic_series` | Preferred analyst-facing retrieval for curated concepts. | `concept`, `variant`, `geography`, `frequency`, `start`, `end`, `last_n` |
| `get_derived_series` | Retrieve transparent formula-based indicators derived from curated concepts. | `concept`, `start`, `end`, `last_n` |
| `get_latest_observations` | Convenience wrapper for the latest source-native observations. | `source`, `identifier`, `key`, `table_id`, `series_ids`, `count` |
| `get_top_observations` | Convenience wrapper for highest or lowest numeric source-native observations. | `source`, `identifier`, `n`, `direction`, `key`, `table_id`, `series_ids`, source-native bounds |
| `describe_dataset` | Describe a curated ABS, RBA, or APRA entry in plain English while preserving native IDs. | `source`, `identifier`, `table_id`, `include_structure` |
| `list_release_events` | List ABS/RBA release-calendar and APRA release-pulse rows. | `source`, `query`, `start_date`, `end_date`, `limit` |

## Preferred LLM flow

For LLM-facing integrations, use:

```text
list_economic_concepts(query="...")
```

then:

```text
get_economic_series(concept="...")
```

This gives the model a constrained discovery surface before retrieval.

For user-facing natural-language examples, see
[Prompting AI Agents](/user-guide/prompting-ai-agents/).

For the small derived layer, call:

```text
get_derived_series(concept="real_cash_rate")
```

Supported derived concepts are `real_cash_rate`, `real_mortgage_rate`,
`real_10y_bond_yield`, `real_bank_bill_rate`, `real_business_lending_rate`,
`yield_curve_slope`, `real_wage_growth`, `credit_growth`, `broad_money_growth`,
`employment_growth`, `gdp_per_capita`, `mortgage_rate_spread`, `credit_to_gdp`,
`household_spending_growth`, `misery_index`, and `terms_of_trade`.

## Expert source-native flow

For exact source-native control, use `search_datasets` or `list_catalogue`, inspect structures
where needed, then call `get_abs_data`, `get_rba_table`, or `get_apra_data`. APRA retrieval is
limited to curated official publication IDs and does not accept arbitrary workbook URLs. For APRA
XLSX workbooks, provide `table_id` where possible so the hosted server can parse and cache only the
requested table.

## Convenience flow

Use `describe_dataset` when an agent or analyst needs a source-aware explanation before retrieval.
It returns source controls, source-native identifiers, governance metadata, and safe convenience
calls that keep the underlying ABS, RBA, or APRA identifier visible. Use `get_latest_observations`
and `get_top_observations` for quick data checks, but keep source-native IDs in the call arguments
for reproducibility. `list_release_events` combines official ABS and RBA release-calendar rows with
APRA expected-release cadence estimates, seed freshness, audit dates, and governance status.

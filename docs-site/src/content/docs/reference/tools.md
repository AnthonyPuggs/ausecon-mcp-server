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

For the small derived layer, call:

```text
get_derived_series(concept="real_cash_rate")
```

Supported derived concepts are `real_cash_rate`, `yield_curve_slope`, `real_wage_growth`,
`credit_growth`, and `gdp_per_capita`.

## Expert source-native flow

For exact source-native control, use `search_datasets` or `list_catalogue`, inspect structures
where needed, then call `get_abs_data`, `get_rba_table`, or `get_apra_data`. APRA retrieval is
limited to curated official publication IDs and does not accept arbitrary workbook URLs.

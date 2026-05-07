---
title: Tools
description: The MCP tool surface exposed by ausecon-mcp-server.
---

All tools are read-only and use `openWorldHint` because they retrieve external, evolving ABS and
RBA data.

| Tool | Purpose | Key inputs |
| --- | --- | --- |
| `search_datasets` | Search the curated ABS and RBA catalogue with deterministic ranking. | `query`, `source` |
| `list_catalogue` | List catalogue entries unranked, optionally filtered by source, category, or tag. | `source`, `category`, `tag`, `include_ceased`, `include_discontinued` |
| `list_economic_concepts` | List semantic concepts accepted by `get_economic_series`. | `query`, `source`, `category` |
| `get_abs_dataset_structure` | Retrieve ABS SDMX dimensions and code lists. | `dataflow_id` |
| `get_abs_data` | Retrieve ABS data in a normalised response shape. | `dataflow_id`, `key`, `start_period`, `end_period`, `last_n`, `updated_after` |
| `list_rba_tables` | Deprecated compatibility alias for curated RBA tables. | `category`, `include_discontinued` |
| `get_rba_table` | Retrieve an RBA statistical table in a normalised response shape. | `table_id`, `series_ids`, `start_date`, `end_date`, `last_n` |
| `get_economic_series` | Preferred analyst-facing retrieval for curated concepts. | `concept`, `variant`, `geography`, `frequency`, `start`, `end`, `last_n` |

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

## Expert source-native flow

For exact ABS/RBA control, use `search_datasets` or `list_catalogue`, inspect structures where
needed, then call `get_abs_data` or `get_rba_table`.

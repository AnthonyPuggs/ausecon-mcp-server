---
title: Discovery and Retrieval
description: Choose between semantic retrieval and source-native ABS/RBA retrieval.
---

## Choosing the right surface

Use `list_economic_concepts` and `get_economic_series` for ordinary analyst requests. This route is
the safest LLM-facing path because the server controls the mapping from economic concepts to
audited source datasets and series.

Use source-native tools when you know the ABS dataflow, SDMX key, RBA table, or RBA series IDs you
want:

- `search_datasets` ranks matching curated ABS and RBA entries.
- `list_catalogue` lists entries unranked and supports source, category, and tag filters.
- `get_abs_dataset_structure` retrieves ABS SDMX dimensions and code lists.
- `get_abs_data` retrieves ABS data in the normalised response shape.
- `get_rba_table` retrieves RBA statistical tables in the normalised response shape.

`list_rba_tables` remains available as a deprecated compatibility alias. New integrations should
use `list_catalogue(source="rba")`.

## Date bounds

`get_economic_series` accepts analyst-friendly bounds:

- `YYYY`
- `YYYY-QN`
- `YYYY-SN`
- `YYYY-MM`
- `YYYY-MM-DD`

The server normalises these to ABS periods or RBA ISO dates after resolving the concept.

Raw ABS and RBA tools keep source-native conventions:

- ABS retrieval uses `start_period` and `end_period`.
- RBA retrieval uses `start_date` and `end_date`.

## Validation behaviour

- Empty identifiers and empty search queries are rejected before any network call.
- `last_n` must be positive when provided.
- ABS period strings are validated for annual, half-yearly, quarterly, and monthly formats.
- RBA date bounds are validated as ISO dates.
- Unknown semantic concepts and unsupported variants raise explicit validation errors.

Search scores are ranking metadata, not a stable public contract.

---
title: Discovery and Retrieval
description: Choose between semantic retrieval and source-native ABS/RBA/APRA retrieval.
---

## Choosing the right surface

Use `list_economic_concepts` and `get_economic_series` for ordinary analyst requests. This route is
the safest LLM-facing path because the server controls the mapping from economic concepts to
audited source datasets and series.

Use `get_derived_series` for the deliberately small set of transparent formula-based indicators
such as real rates, year-ended transformations, and yield-curve slope. Derived retrieval still
returns the normal `metadata`, `series`, and `observations` shape, with formula provenance in
`metadata.derived`.

Use source-native tools when you know the ABS dataflow, SDMX key, RBA table, RBA series IDs, APRA
publication, APRA table, or APRA series IDs you want:

- `search_datasets` ranks matching curated ABS, RBA, and APRA entries.
- `list_catalogue` lists entries unranked and supports source, category, and tag filters.
- `get_abs_dataset_structure` retrieves ABS SDMX dimensions and code lists.
- `get_abs_data` retrieves ABS data in the normalised response shape.
- `get_rba_table` retrieves RBA statistical tables in the normalised response shape.
- `get_apra_data` retrieves curated official APRA XLSX publications in the normalised response
  shape. Specify `table_id` for APRA workbooks when you know the table you need.

`list_rba_tables` remains available as a deprecated compatibility alias. New integrations should
use `list_catalogue(source="rba")`.

## Derived retrieval

`get_derived_series` currently supports:

- `real_cash_rate`
- `yield_curve_slope`
- `real_wage_growth`
- `credit_growth`
- `gdp_per_capita`

It does not accept arbitrary formulas or user-supplied code. Operands are fetched through the
curated semantic layer and then combined by fixed, documented formulas.

## Date bounds

`get_economic_series` and `get_derived_series` accept analyst-friendly bounds:

- `YYYY`
- `YYYY-QN`
- `YYYY-SN`
- `YYYY-MM`
- `YYYY-MM-DD`

The server normalises these to ABS periods or RBA ISO dates after resolving the concept.

Raw ABS, RBA, and APRA tools keep source-native conventions:

- ABS retrieval uses `start_period` and `end_period`.
- RBA retrieval uses `start_date` and `end_date`.
- APRA retrieval uses `start_date` and `end_date`.

## Validation behaviour

- Empty identifiers and empty search queries are rejected before any network call.
- `last_n` must be positive when provided.
- ABS period strings are validated for annual, half-yearly, quarterly, and monthly formats.
- RBA date bounds are validated as ISO dates.
- APRA date bounds are validated as ISO dates.
- Unknown semantic concepts and unsupported variants raise explicit validation errors.
- Unknown derived concepts raise explicit validation errors.

Search scores are ranking metadata, not a stable public contract.

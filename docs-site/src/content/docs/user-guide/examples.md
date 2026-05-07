---
title: Examples
description: Common discovery and retrieval calls for MCP clients.
---

## Discovery

Search for datasets related to the cash rate:

```text
search_datasets(query="cash rate")
```

Discover semantic concepts related to inflation:

```text
list_economic_concepts(query="inflation")
```

Browse active RBA inflation tables:

```text
list_catalogue(source="rba", category="inflation")
```

## ABS retrieval

Inspect the ABS CPI data structure:

```text
get_abs_dataset_structure(dataflow_id="CPI")
```

Fetch a filtered ABS CPI response:

```text
get_abs_data(
  dataflow_id="CPI",
  key="all",
  start_period="2024-Q1",
  end_period="2024-Q4",
  last_n=4
)
```

## RBA retrieval

Fetch the latest observations from RBA table `g1`:

```text
get_rba_table(
  table_id="g1",
  last_n=8
)
```

Fetch an event-style policy table:

```text
get_rba_table(
  table_id="a2",
  last_n=8
)
```

## Semantic retrieval

Resolve the cash rate target:

```text
get_economic_series(
  concept="cash_rate_target",
  start="2020-01-01"
)
```

Resolve trimmed mean inflation:

```text
get_economic_series(
  concept="trimmed_mean_inflation",
  start="2020-01-01"
)
```

Resolve quarterly real GDP growth:

```text
get_economic_series(
  concept="gdp_growth",
  start="2020-01-01"
)
```

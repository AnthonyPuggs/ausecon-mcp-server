---
title: Examples
description: Common discovery and retrieval calls for MCP clients.
---

## Discovery

For examples that start with a natural-language user prompt and show the likely AI-agent tool
sequence, see [Prompting AI Agents](/user-guide/prompting-ai-agents/).

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
get_latest_observations(
  source="rba",
  identifier="g1",
  count=8
)
```

Fetch the highest numeric observations in an RBA table:

```text
get_top_observations(
  source="rba",
  identifier="g1",
  n=5,
  direction="highest"
)
```

Fetch an event-style policy table:

```text
get_rba_table(
  table_id="a2",
  last_n=8
)
```

## APRA retrieval

Fetch a bounded APRA table directly:

```text
get_apra_data(
  publication_id="ADI_QUARTERLY_PERFORMANCE",
  table_id="key_stats",
  last_n=4
)
```

Describe an APRA publication before retrieving it:

```text
describe_dataset(
  source="apra",
  identifier="ADI_QUARTERLY_PERFORMANCE",
  table_id="key_stats"
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

Resolve an APRA-backed ADI capital ratio:

```text
get_economic_series(
  concept="adi_capital_ratio",
  last_n=4
)
```

## Derived retrieval

Fetch transparent formula-based indicators:

```text
get_derived_series(
  concept="real_cash_rate",
  last_n=12
)
```

```text
get_derived_series(
  concept="yield_curve_slope",
  start="2024-01-01",
  last_n=5
)
```

```text
get_derived_series(
  concept="credit_to_gdp",
  start="2020-Q1"
)
```

## Release awareness

Find upcoming release or release-pulse rows:

```text
list_release_events(
  source="rba",
  query="balance sheet",
  limit=5
)
```

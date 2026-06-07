---
title: Prompting AI Agents
description: How natural-language economic requests map to MCP tool calls.
---

Users normally interact with this server through an LLM or AI agent, not by typing raw MCP calls.
The user asks an economic question in ordinary language, the agent chooses one or more read-only
tools, and the server returns structured `metadata`, `series`, and `observations`.

This page describes the recommended routing patterns. It is not a hard guarantee that every model
or MCP client will choose the exact same sequence. The server provides tool descriptions, schemas,
resources, and prompt templates; the LLM client decides when to call them.

## Main routing patterns

Use ordinary economic language, but include the indicator, geography, frequency, date window, and
preferred output format when those details matter.

| User intent | Typical MCP route |
| --- | --- |
| Ordinary analyst request for GDP, CPI, unemployment, cash rate, credit, exchange rates, or yields | `list_economic_concepts` then `get_economic_series` |
| Transparent formula-based indicator such as real cash rate, yield-curve slope, or credit-to-GDP | `get_derived_series` |
| Exact ABS, RBA, or APRA source control | `search_datasets` or `list_catalogue`, then `get_abs_data`, `get_rba_table`, or `get_apra_data` |
| Exploratory or quick-turnaround request | `describe_dataset`, `get_latest_observations`, or `get_top_observations` |

## Prompt examples

### Quarterly real GDP growth

User prompt:

```text
List the quarterly real GDP growth data for the past 10 years.
```

Typical tool calls:

```text
list_economic_concepts(query="quarterly real GDP growth")
get_economic_series(concept="gdp_growth", last_n=40)
```

Why: the prompt describes a curated economic concept and a quarterly 10-year window. Forty
quarterly observations is the compact way to express that window when the user wants the past 10
years of available data.

### Latest cash rate target

User prompt:

```text
What is the latest RBA cash rate target?
```

Typical tool calls:

```text
list_economic_concepts(query="cash rate")
get_economic_series(concept="cash_rate_target", last_n=1)
```

Why: the cash rate target is a curated semantic concept, and `last_n=1` asks for the latest
available observation.

### Real cash rate

User prompt:

```text
Compare the real cash rate over the last year.
```

Typical tool call:

```text
get_derived_series(concept="real_cash_rate", last_n=12)
```

Why: the real cash rate is part of the server's transparent derived-series layer. The response
includes formula and operand provenance in `metadata.derived`.

### Housing credit source discovery

User prompt:

```text
Find the best ABS or RBA data source for housing credit.
```

Typical tool calls:

```text
list_economic_concepts(query="housing credit")
search_datasets(query="housing credit")
```

Why: the first call checks whether a curated semantic shortcut already exists. The second call
ranks source-level ABS, RBA, and APRA catalogue entries for cases where the user needs a dataset
or table recommendation before retrieval.

## Prompting tips

- Ask for the output format you need, such as a table, a short summary, or a comparison.
- Include frequency and window language when relevant, such as monthly, quarterly, latest,
  last 12 observations, or 2020 to 2024.
- Ask the agent to preserve source identifiers or provenance when you need reproducibility.
- For exact ABS/RBA/APRA work, name the dataflow, table, publication, or series ID if you already
  know it.
- If a result looks ambiguous, ask the agent which MCP tool it called and which `metadata`
  fields identify the resolved source.

For direct call syntax, see [Examples](/user-guide/examples/) and the [Tools reference](/reference/tools/).

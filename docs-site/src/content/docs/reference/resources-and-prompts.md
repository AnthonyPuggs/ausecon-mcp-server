---
title: Resources and Prompts
description: Read-only MCP resources and prompt templates exposed by the server.
---

## Resources

The server exposes the curated catalogue as MCP resources. These are read-only, served as
`application/json`, and sourced from the static catalogue without making network calls.

| URI | Returns |
| --- | --- |
| `ausecon://catalogue` | Flat index of every curated ABS, RBA, and APRA entry. |
| `ausecon://abs/{dataflow_id}` | Full curated catalogue entry for one ABS dataflow. |
| `ausecon://rba/{table_id}` | Full curated catalogue entry for one RBA statistical table. |
| `ausecon://concepts` | Every curated semantic shortcut with its resolved target and recommended call. |

## Prompts

The server registers prompt templates that chain existing tools into common economist workflows.

| Prompt | Arguments | What it does |
| --- | --- | --- |
| `summarise_latest_inflation` | `months: int = 12` | Pulls headline and trimmed-mean CPI and compares them with the RBA target band. |
| `compare_cash_rate_to_cpi` | `start: str`, `end: str \| None` | Narrates the cash rate target against headline CPI over a window. |
| `macro_snapshot` | `as_of: str \| None` | Builds a compact snapshot of cash rate, CPI, trimmed-mean CPI, and real GDP growth. |
| `living_costs_vs_cpi` | `start: str \| None`, `last_n: int = 8` | Compares Selected Living Cost Indexes across household types against CPI. |
| `construction_pipeline` | `last_n: int = 8` | Summarises construction pipeline strength across engineering and building activity. |
| `labour_slack_snapshot` | `last_n: int = 12` | Reads unemployment and underemployment rates to summarise labour slack. |
| `yield_curve_snapshot` | `last_n: int = 60` | Compares 3-year and 10-year Australian Government Security yields. |
| `discover_dataset` | `topic: str` | Runs concept, ranked search, and unranked catalogue discovery for a topic. |

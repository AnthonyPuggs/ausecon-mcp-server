---
title: Getting Started
description: Install and make your first MCP retrieval.
---

## Requirements

- Python `3.10+`.
- [`uv`](https://docs.astral.sh/uv/) for the `uvx` launcher.
- An MCP client that supports local stdio servers.

## Install

The package is published to [PyPI](https://pypi.org/project/ausecon-mcp-server/) and is intended
to be launched on demand:

```bash
uvx ausecon-mcp-server
```

On first use, `uvx` downloads the package into an isolated cached environment. The process then
waits for an MCP client to connect over standard input/output.

## Recommended workflow

1. Use `list_economic_concepts` for ordinary economic requests such as GDP, CPI, unemployment,
   wages, cash rate, credit, exchange rates, or yields.
2. Use `get_economic_series` with the selected concept.
3. Use `get_derived_series` for transparent formula-based indicators such as real cash rate,
   yield-curve slope, real wage growth, credit growth, or real GDP per capita.
4. Use `search_datasets`, `list_catalogue`, `get_abs_dataset_structure`, `get_abs_data`, and
   `get_rba_table` when you need source-native ABS/RBA control.

## First retrieval pattern

```text
list_economic_concepts(query="cash rate")
```

```text
get_economic_series(
  concept="cash_rate_target",
  start="2020-01-01"
)
```

Retrieval responses include `metadata`, `series`, and `observations`. Semantic retrievals also
include `metadata.semantic`, recording the resolved source target and normalised date bounds.
Derived retrievals include `metadata.derived`, recording the formula, operands, units, and
alignment frequency.

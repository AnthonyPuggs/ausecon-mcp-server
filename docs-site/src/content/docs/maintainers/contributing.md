---
title: Contributing
description: Local development and verification for maintainers.
---

`ausecon-mcp-server` is intentionally narrow: ABS and RBA only, stdio transport only, and a small
curated semantic layer over source-native retrievals.

## Local setup

Use Python 3.12 for local development:

```bash
env UV_CACHE_DIR=.uv-cache uv sync --python 3.12 --extra dev
```

## Standard verification

Run the normal local checks before opening a pull request or cutting a tag:

```bash
env UV_CACHE_DIR=.uv-cache uv run ruff check src tests scripts
env UV_CACHE_DIR=.uv-cache uv run pytest
env UV_CACHE_DIR=.uv-cache uv run pytest integration_tests/ -v
env UV_CACHE_DIR=.uv-cache uv run python scripts/audit_catalogue.py
```

## Real client smoke

Before a release tag, run the checked-in stdio smoke path:

```bash
env UV_CACHE_DIR=.uv-cache uv run python scripts/mcp_client_smoke.py
```

The smoke path uses a real FastMCP stdio client transport and verifies:

- `search_datasets`
- `list_economic_concepts`
- `list_catalogue`
- `get_abs_data`
- `get_economic_series`

## Release discipline

- Keep the MCP tool surface stable unless there is a strong reason to break it.
- Do not expose placeholder variants in the runtime catalogue.
- Prefer audited upstream fixes over broad catalogue growth.
- If an ABS or RBA replacement series is not cleanly source-native, defer it rather than shipping
  an approximate semantic shortcut.

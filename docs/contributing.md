# Contributing

`ausecon-mcp-server` is intentionally narrow: ABS + RBA only, stdio plus hosted HTTP transport,
and small curated semantic and derived layers over source-native retrievals.

## Local Setup

Use Python 3.12 for local development:

```bash
env UV_CACHE_DIR=.uv-cache uv sync --python 3.12 --extra dev
```

## Standard Verification

Run the normal local checks before opening a PR or cutting a tag:

```bash
env UV_CACHE_DIR=.uv-cache uv run ruff check src tests
env UV_CACHE_DIR=.uv-cache uv run pytest
env UV_CACHE_DIR=.uv-cache uv run pytest integration_tests/ -v
env UV_CACHE_DIR=.uv-cache uv run python scripts/audit_catalogue.py
```

## Real Client Smoke

Before a release tag, run the checked-in stdio smoke path:

```bash
env UV_CACHE_DIR=.uv-cache uv run python scripts/mcp_client_smoke.py
```

This uses a real FastMCP stdio client transport and verifies:

- `search_datasets`
- `list_economic_concepts`
- `list_catalogue`
- `get_abs_data`
- `get_economic_series`
- `get_derived_series`

The smoke path currently exercises the `BUILDING_APPROVALS` catalogue entry and the
`dwelling_approvals` semantic shortcut because they are the newest pre-`v1.0.0` coverage additions.

## Release Discipline

- Keep the MCP tool surface stable unless there is a strong reason to break it.
- Do not expose placeholder variants in the runtime catalogue.
- Prefer audited upstream fixes over broad catalogue growth.
- Keep `get_derived_series` read-only, transparent, and formula-based; do not add modelling,
  forecasting, seasonal adjustment, or arbitrary user formulas without a separate design.
- If an ABS or RBA replacement series is not cleanly source-native, defer it rather than shipping an
  approximate semantic shortcut.

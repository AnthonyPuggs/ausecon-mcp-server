# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.12 is recommended for local development. The package metadata and CI matrix support Python 3.10+.

```bash
# Install dependencies
uv sync --python 3.12

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_catalogue.py

# Run a single test by name
uv run pytest tests/test_catalogue.py::test_search_catalogue_prefers_high_value_alias_matches

# Lint and format
uv run ruff check src tests
uv run ruff format src tests

# Run the MCP server (stdio mode)
uv run ausecon-mcp-server
```

## Architecture

This is a **FastMCP server** that wraps ABS (Australian Bureau of Statistics) and RBA (Reserve Bank of Australia) data APIs. The design is intentionally thin on the MCP surface and delegates all logic to internal layers.

### Layer structure

```
server.py          → FastMCP tool definitions, AuseconService orchestrator
providers/         → Async httpx clients for each source (ABS, RBA), TTLCache wrappers
parsers/           → Pure functions: raw HTTP response text → normalised dicts
catalogue/         → Static curated dicts (abs.py, rba.py) + search.py ranking logic
models.py          → SeriesDescriptor and Observation dataclasses; shared to_dict() helpers
cache.py           → Dual-layer TTLCache (memory + on-disk JSON cache)
```

### Data flow

1. MCP tool call → `AuseconService` method
2. `AuseconService` → `ABSProvider` or `RBAProvider` (checks TTLCache first)
3. Provider → httpx GET → raw CSV or XML response
4. Parser (`parse_abs_csv`, `parse_rba_csv`, `parse_abs_structure`) → `{metadata, series, observations}` dict
5. Optional post-fetch filtering (`filters.py`) for `last_n`, date ranges, and series IDs
6. Result cached and returned as dict (not model instances)

### ABS vs RBA differences

- **ABS** uses SDMX REST (`data.api.abs.gov.au/rest`): structure endpoint returns XML, data endpoint returns CSV with `format=csvfile`.
- **RBA** serves static CSVs at `rba.gov.au/statistics/tables/csv/{table_id}-data.csv`; all filtering is done client-side after download.

### Tool injection pattern

`build_server()` in `server.py` creates the FastMCP instance and registers all tools as closures over an `AuseconService`. Tests inject mock providers directly into `AuseconService`, which is then passed to `build_server()`.

### Catalogue search scoring

`search_catalogue` in `catalogue/search.py` ranks entries by weighted keyword matching: exact alias match (+120) > exact name match (+100) > substring in name (+45) > substring in description (+25) > alias term overlap (+20 per term). Source filtering (`source="abs"` or `"rba"`) is applied before scoring.

### Response shape

All retrieval tools return `{metadata: {...}, series: [...], observations: [...]}`. Provenance fields such as `retrieval_url`, `retrieved_at`, `truncated`, `updated_after`, and `server_version` are stamped onto `metadata` after parsing. The checked-in contract lives at `schemas/response.schema.json`.

## Key conventions

- All provider methods are `async`; `list_tables` on `RBAProvider` is the only sync exception (no I/O).
- `asyncio_mode = "auto"` is set in `pyproject.toml` — no `@pytest.mark.asyncio` decorator needed.
- Tests use `respx` for HTTP mocking and fixture files in `tests/fixtures/`.
- Ruff target is Python 3.10 with `E, F, I, B, UP` rules and line length 100.

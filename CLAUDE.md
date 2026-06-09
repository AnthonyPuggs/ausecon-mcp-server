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

This is a **FastMCP server** that wraps ABS (Australian Bureau of Statistics), RBA (Reserve Bank of Australia), and APRA (Australian Prudential Regulation Authority) data APIs. The design is intentionally thin on the MCP surface and delegates all logic to internal layers.

### Layer structure

```
server.py          → FastMCP tool definitions, AuseconService orchestrator
providers/         → Async httpx clients for each source (ABS, RBA, APRA), TTLCache wrappers
parsers/           → Pure functions: raw CSV/XML/XLSX responses → normalised dicts
catalogue/         → Curated dicts (abs.py, rba.py, apra.py), search.py ranking,
                     resolver.py semantic-concept shortcuts
periods.py         → Shared period parsing and sort keys for YYYY, YYYY-QN, YYYY-SN,
                     YYYY-MM, and YYYY-MM-DD observation dates
filters.py         → Post-fetch filtering (series_ids, date bounds, last_n); sorts
                     observations chronologically
bounds.py          → Analyst-friendly date bounds → source-native period normalisation
validation.py      → Tool input validation helpers
derived.py         → Transparent derived indicators (real rates, growth rates, yield slope)
convenience.py     → describe_dataset and latest/top observation selection metadata
releases.py        → Release calendar events
governance/        → APRA URL governance and audit checks
models.py          → SeriesDescriptor and Observation dataclasses; shared to_dict() helpers
cache.py           → Dual-layer TTLCache (memory + on-disk JSON cache)
```

### Data flow

1. MCP tool call → `AuseconService` method
2. `AuseconService` → `ABSProvider`, `RBAProvider`, or `APRAProvider` (checks TTLCache first)
3. Provider → httpx GET → raw CSV, XML, or XLSX response
4. Parser (`parse_abs_csv`, `parse_rba_csv`, `parse_abs_structure`, `parse_apra_xlsx`) → `{metadata, series, observations}` dict
5. Post-fetch filtering (`filters.py`) for `last_n`, date ranges, and series IDs. Observations are sorted chronologically here (ABS SDMX CSV row order is arbitrary), and `last_n` keeps the most recent N observations per series.
6. Result cached and returned as dict (not model instances)

### Source differences

- **ABS** uses SDMX REST (`data.api.abs.gov.au/rest`): structure endpoint returns XML, data endpoint returns CSV with `format=csvfile`.
- The ABS data endpoint answers HTTP 404 both for unknown dataflows and for valid dataflows with no observations in the requested window (response body `NoRecordsFound`). The provider maps the no-results case to an empty payload with a metadata warning; 404s never fall back to stale cache (`AuseconNotFoundError`), unlike transient 5xx/timeout failures which do.
- **RBA** serves static CSVs at `rba.gov.au/statistics/tables/csv/`; most files use `{table_id}-data.csv`, while catalogue `csv_path` overrides cover exceptions such as `f17-yields.csv`. Filtering is done client-side after download.
- **APRA** publishes XLSX workbooks; download URLs are resolved via landing pages with seed-manifest and catalogue fallbacks (`governance/`).

### Tool injection pattern

`build_server()` in `server.py` creates the FastMCP instance and registers all tools as closures over an `AuseconService`. Tests inject mock providers directly into `AuseconService`, which is then passed to `build_server()`.

### Catalogue search scoring

`search_catalogue` in `catalogue/search.py` ranks entries deterministically: exact ID (1000) > exact alias (900) > exact name (800) > full query-term coverage in aliases/name/tags (700+) > partial term overlap (400+) > description overlap (100+). Source filtering (`source="abs"` or `"rba"`) is applied before scoring.

### Response shape

All retrieval tools return `{metadata: {...}, series: [...], observations: [...]}`. Observations are always chronologically ascending; `last_n` selects the most recent N per series, with `truncated` and `observations_dropped` recording what was removed. Provenance fields such as `retrieval_url`, `retrieved_at`, `updated_after`, and `server_version` are stamped onto `metadata` after parsing. The checked-in contract lives at `schemas/response.schema.json` (mirrored at `src/ausecon_mcp/schemas/` for packaging).

## Key conventions

- All provider methods are `async`; `list_tables` on `RBAProvider` is the only sync exception (no I/O).
- `asyncio_mode = "auto"` is set in `pyproject.toml` — no `@pytest.mark.asyncio` decorator needed.
- Tests use `respx` for HTTP mocking and fixture files in `tests/fixtures/`.
- Ruff target is Python 3.10 with `E, F, I, B, UP` rules and line length 100.

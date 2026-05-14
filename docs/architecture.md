# Architecture

`ausecon-mcp-server` is a thin FastMCP surface over curated ABS and RBA retrieval layers.
The server stays deliberately narrow: it exposes model-controlled concept discovery,
source-native discovery, retrieval, a small semantic shortcut layer, and a narrow transparent
derived-series layer, but it does not try to become a generic analytics engine.

## Layers

- `src/ausecon_mcp/server.py`: FastMCP tool registration and the `AuseconService` orchestrator.
- `src/ausecon_mcp/catalogue/`: Curated ABS and RBA metadata plus semantic resolution and search.
- `src/ausecon_mcp/providers/`: Async HTTP clients, retry logic, cache integration, and metadata stamping.
- `src/ausecon_mcp/parsers/`: Pure payload normalisers from upstream CSV/XML into the shared response shape.
- `src/ausecon_mcp/derived.py`: Fixed formula implementations for the narrow derived-series tool.
- `src/ausecon_mcp/filters.py`: Shared client-side filtering for `last_n`, date windows, and series pruning.
- `src/ausecon_mcp/resources.py` and `src/ausecon_mcp/prompts.py`: Read-only MCP resources and prompt templates.
- `src/ausecon_mcp/bounds.py`: Semantic-only date-bound normalisation from analyst inputs to
  ABS periods or RBA ISO dates.

## Retrieval Flow

1. A client calls a retrieval tool, `get_economic_series`, or `get_derived_series`.
2. `AuseconService` validates inputs and resolves semantic shortcuts when needed.
3. The relevant provider fetches or reuses a cached upstream payload.
4. A parser converts the raw response into `{metadata, series, observations}`.
5. Shared filtering trims the response and prunes unused series.
6. Providers stamp provenance fields such as `retrieval_url`, `retrieved_at`, and `server_version`.

For `get_economic_series`, analyst-friendly `start` and `end` values are normalised after semantic
resolution. Raw ABS/RBA tools deliberately keep source-native date conventions.

For `get_derived_series`, the service fetches fixed semantic operands, applies the documented
formula, then returns the same top-level shape with `metadata.derived` provenance.

## Scope Boundaries

- ABS structure inspection remains a separate tool because it returns SDMX structure metadata, not the retrieval contract.
- Retrieval responses for ABS and RBA share one top-level shape, documented in
  [`schemas/response.schema.json`](../schemas/response.schema.json).
- Derived series are fixed read-only formulas only; arbitrary user formulas, modelling, and
  forecasting remain out of scope.

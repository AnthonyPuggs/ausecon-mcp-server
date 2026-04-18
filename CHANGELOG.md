# Changelog

All notable changes to `ausecon-mcp-server` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-04-18

Production hardening release.

### Added
- **Structured JSON logging** for the `ausecon_mcp` namespace.
  Events cover `request.start`, `request.success` (with
  `duration_ms`, `status_code`, `bytes`), `request.retry`,
  `request.failed`, `request.stale_fallback`, `parse.failed`, and
  cache hit/miss at `DEBUG`. Logs are written to stderr only so the
  stdio MCP transport is never interfered with.
- **Identified User-Agent** on every outgoing upstream request:
  `ausecon-mcp-server/<version> (+https://github.com/AnthonyPuggs/ausecon-mcp-server)`.
- **Persistent on-disk cache**. The in-memory `TTLCache` is now a
  memory + disk dual-layer cache that survives process restarts,
  so `uvx`-spawned server sessions no longer pay full upstream
  latency on every first call. Disk I/O is fail-soft: corrupt
  JSON, schema mismatches, and write errors self-heal and log a
  warning without failing the request.
- **`stale-if-error` fallback**. If an upstream request fails
  (`AuseconUpstreamError`) and a previously cached payload exists
  on disk, the server returns the cached payload with
  `metadata.stale = true`, `metadata.cached_at`, and
  `metadata.expires_at`. Parse errors (`AuseconParseError`) are
  **not** masked — those still raise, so upstream shape drift
  remains a first-class signal.
- **`metadata.server_version`** on every data response so bug
  reports can reference the exact release that produced them.
- **Nightly integration suite** in `integration_tests/` that hits
  the live ABS and RBA endpoints, plus a GitHub Actions workflow
  (`integration.yml`) that runs on a cron schedule, uploads pytest
  output as an artefact, and upserts a single `upstream-drift`
  issue on failure instead of opening duplicates.
- Environment knobs `AUSECON_CACHE_DIR`, `AUSECON_CACHE_DISABLED`,
  and `AUSECON_LOG_LEVEL` documented in a new README "Operations"
  section.

### Changed
- `TTLCache` config (disk directory, disabled flag, TTL) is now
  resolved in `__init__`, not at import. Cache reads return deep
  copies so callers cannot mutate stored payloads.
- Added `platformdirs` as a direct dependency for cache location
  resolution.

## [0.6.0] - 2026-04-18

### Added
- MCP `resources` surface: `ausecon://catalogue` (flat index of every
  curated ABS and RBA entry), `ausecon://abs/{dataflow_id}`, and
  `ausecon://rba/{table_id}`. Lets clients browse the catalogue in a
  resource picker without calling `search_datasets` blind.
- MCP `prompts` surface: four slash-command templates —
  `summarise_latest_inflation`, `compare_cash_rate_to_cpi`,
  `macro_snapshot`, and `discover_dataset` — that chain existing tools
  into common economist workflows.
- `readOnlyHint` and `openWorldHint` annotations on every tool so
  compliant clients can render them appropriately.

## [0.5.5] - 2026-04-18

### Fixed
- The `mcp-name` marker in the README and the `server.json` name now
  use the GitHub username casing `AnthonyPuggs` instead of lowercase.
  The MCP Registry's namespace check is case-sensitive and was
  rejecting the publish with a 403.

## [0.5.4] - 2026-04-18

### Added
- Hidden `mcp-name` marker in the README and a `server.json` manifest at
  the repo root, in preparation for listing in the official MCP Registry
  (`registry.modelcontextprotocol.io`). The marker becomes part of the
  PyPI package description and is how the registry verifies ownership
  of the PyPI package for server name
  `io.github.anthonypuggs/ausecon-mcp-server`.
- `Dockerfile` installing the published PyPI package into an isolated
  `uv tool` environment and running it as a non-root user.

### Changed
- README and example client configs install the server via
  `uvx ausecon-mcp-server` from PyPI instead of guiding a local clone
  plus `uv --directory ...` invocation.
- `fastmcp.json` now declares `name`, `description`, `tags`, and
  `homepage` metadata for registry discovery.
- The `Release` workflow now also builds and publishes a container
  image to `ghcr.io/AnthonyPuggs/ausecon-mcp-server` after each PyPI
  release, tagged with the semver and `latest`.

### Fixed
- The release Dockerfile no longer passes two package specs to
  `uv tool install` when pinning the package version; the build used to
  fail with exit code 2 because `${VAR:+...}` and `${VAR:-...}` both
  fired on a set variable.

### Changed
- README and example client configs now install the server via
  `uvx ausecon-mcp-server` from PyPI instead of guiding a local clone
  plus `uv --directory ...` invocation.
- `fastmcp.json` now declares `name`, `description`, `tags`, and
  `homepage` metadata for registry discovery.
- The `Release` workflow now also builds and publishes a container
  image to `ghcr.io/AnthonyPuggs/ausecon-mcp-server` after each PyPI
  release, tagged with the semver and `latest`.

### Added
- `Dockerfile` installing the published PyPI package into an isolated
  `uv tool` environment and running it as a non-root user.

## [0.5.2] - 2026-04-17

### Changed
- Package version is now derived from git tags via `hatch-vcs` instead of
  being hardcoded in `pyproject.toml`, keeping the tag and the published
  PyPI artifact in sync automatically.
- Added Cursor and VS Code configuration snippets to the README alongside
  the existing Claude Desktop, Claude Code, and Codex entries.
- Added a tag-triggered `Release` workflow that builds and publishes to
  PyPI via Trusted Publishing (OIDC).

## [0.5.0] - 2026-04-17

Semantic-defaults and release-readiness release. Curated
`get_economic_series` concepts now resolve to concrete series by default, and
the public onboarding docs now cover the main local MCP clients.

### Changed
- `cash_rate_target`, `headline_cpi`, `trimmed_mean_inflation`, and
  `gdp_growth` now resolve to narrowed default series instead of broad ABS
  datasets or RBA tables.
- Curated catalogue entries for `CPI`, `ANA_AGG`, `a2`, and `g1` now include
  populated default semantic variants used by the resolver.
- `README.md` now documents the actual `get_economic_series` inputs and
  provides self-serve local setup instructions for Claude Desktop, Claude Code,
  and Codex.

### Fixed
- ABS structure parsing now handles the current SDMX structure shape where
  dimension metadata is nested under `ConceptIdentity` / `LocalRepresentation`
  and includes `TimeDimension` entries.
- ABS CSV parsing now handles current upstream column names such as
  `TIME_PERIOD`, `UNIT_MEASURE`, `UNIT_MULT`, and `OBS_STATUS`, rather than
  only the older labelled column variants.
- Repository hygiene and behavioural tests now pin the `v0.5.0` semantic
  shortcut contract and public onboarding text.

## [0.4.0] - 2026-04-17

Semantic resolver release. `get_economic_series` accepts variant / geography /
frequency and dispatches to narrowed ABS or RBA retrievals.

### Added
- `ausecon_mcp.catalogue.resolver` module exposing `resolve()`, `build_abs_key()`,
  `ResolvedQuery`, and the `CURATED_SHORTCUTS` map (replaces the removed
  `CURATED_SERIES` dict on `server`).
- ABS SDMX key construction that orders dimensions by `position`, composes from
  literal dot-keys or `DIM=code;DIM=code` variant fragments, and validates each
  emitted code against the live codelist.
- RBA variant resolution returns the variant's `rba_series_ids` as the
  `get_rba_table` filter.
- `tests/test_resolver.py` — 19 unit tests covering unknown/ambiguous concepts,
  unknown/unpopulated variants, frequency/geography validation, key composition,
  and codelist mismatches.
- First populated variant: `g1.headline` → `["GCPIAG"]`. Additional variants are
  populated progressively as `scripts/dump_variant_candidates.py` output is
  reviewed.

### Changed
- `get_economic_series` no longer rejects `variant` / `geography` / `frequency`;
  it routes through the new resolver. Unknown values raise actionable errors
  listing what is available.
- When a curated shortcut has no variant supplied and no explicit variant is
  declared, the response is identical to v0.3.2 (whole dataset or whole table).

### Removed
- `CURATED_SERIES` dict and `_unsupported_semantic_options` helper from
  `server.py`.

## [0.3.2] - 2026-04-17

Bridge release between the v0.3.x discovery work and the upcoming v0.4.0 semantic
resolver. No tool-surface changes.

### Added
- `CHANGELOG.md` seeded from git history. Earlier releases are reconstructed from
  commit history and the README version notes.
- `scripts/dump_variant_candidates.py` — dev-only helper that fetches each curated
  RBA table and ABS dataflow structure, then writes a reviewable reference doc at
  `docs/variant_candidates.md`. Used to hand-populate `variants[*].abs_key` and
  `variants[*].rba_series_ids` in preparation for the v0.4.0 resolver.

### Changed
- `get_economic_series` now raises a version-neutral message when `variant`,
  `geography`, or `frequency` are supplied. The previous message referenced
  `v0.3.0` even in v0.3.1.

## [0.3.1] - 2026-04-16

### Fixed
- Support Python 3.10 by depending on `tomli` for pre-3.11 interpreters.
- Allow `pytest >= 9`.

### Changed
- README now displays a release badge.

## [0.3.0] - 2026-04-14

Discovery release. Same six-tool surface, materially expanded catalogue and
deterministic search ranking.

### Added
- Expanded ABS catalogue to ~30 curated dataflows across prices, labour, national
  accounts, activity, housing & construction, external sector, credit & finance,
  and demographics.
- Expanded RBA catalogue to ~30 active tables (plus `discontinued: True` tagging
  where applicable) across monetary policy, payments, money & credit, interest
  rates, exchange rates, inflation, output & labour, external sector, and
  household finance.
- `search_datasets` uses deterministic tiered scoring: exact id > exact alias >
  exact name > full-term match > partial-term match > description match.
- Catalogue entries declare resolver schema fields (`frequencies`, `geographies`,
  `variants`) that stay inert until the v0.4.0 resolver consumes them.
- Catalogue-coverage and search-ranking tests in `tests/test_catalogue.py`.

## [0.2.0] - 2026-04-12

Hardening release.

### Added
- `validation.py` — input validation for dataflow IDs, keys, ABS periods, ISO
  dates, positive integers, series IDs, categories, and `updated_after`
  timestamps. Applied at every tool boundary.
- `providers/_retry.py` — exponential backoff (0.1s → 0.2s → 0.4s, 3 attempts)
  with 4xx-no-retry / 5xx-retry / timeout-retry behaviour.
- Provider-level error wrapping: `AuseconParseError` for malformed upstream
  payloads, `AuseconUpstreamError` for HTTP failures.
- Per-provider TTLCache (3600s default) for raw upstream payloads.
- Support for ABS `a2` event-style tables.

## [0.1.0] - 2026-04-12

Initial public release.

### Added
- FastMCP server exposing six tools (`search_datasets`, `get_abs_data`,
  `get_abs_dataset_structure`, `get_rba_table`, `list_rba_tables`,
  `get_economic_series`).
- Async httpx providers for ABS SDMX REST and RBA statistical CSVs.
- Pure-function parsers for ABS SDMX CSV, ABS structure XML, and RBA CSVs.
- Initial curated catalogues for ABS and RBA, plus a four-concept
  `CURATED_SERIES` semantic shortcut map.

[0.7.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.5.5...v0.6.0
[0.5.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/releases/tag/v0.1.0

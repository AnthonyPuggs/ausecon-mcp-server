# Changelog

All notable changes to `ausecon-mcp-server` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-05-15

### Added
 Added `get_apra_data(...)`, a new source-native read-only MCP tool for curated APRA public XLSX publications.
- Added APRA catalogue coverage for:
  - Monthly ADI Statistics
  - Quarterly ADI Performance Statistics
  - ADI Centralised Publication
  - ADI Property Exposures Statistics
- Extended source filters to support `abs | rba | apra` across catalogue and discovery tools.
- Updated README, generated references, docs site, response schema, Smithery/hosted docs, and roadmap wording for ten read-only MCP tools.

## [1.3.0] - 2026-05-14

### Added
- Added `get_derived_series`, a read-only derived-series tool for transparent
  formulas over curated ABS/RBA semantic operands.
- Added initial derived concepts for `real_cash_rate`, `yield_curve_slope`,
  `real_wage_growth`, `credit_growth`, and `gdp_per_capita`, with formula,
  operand, units, alignment-frequency, and dropped-observation provenance in
  `metadata.derived`.

### Security

- APRA workbook downloads are restricted to trusted APRA HTTPS hosts.
- Added workbook parsing limits for compressed size, uncompressed XLSX size, member count, rows, and columns.
- Added hosted HTTP request-size protection for oversized MCP requests.
- Updated docs-site dependencies to resolve npm audit findings.

### Changed
- Extended the checked-in response schema to allow `metadata.source =
  "derived"` and validate derived-series provenance without changing the
  top-level `{metadata, series, observations}` contract.
- Updated README, maintainer docs, docs-site references, roadmap wording, and
  the stdio client smoke path for the new derived retrieval surface.

## [1.2.1] - 2026-05-14

### Added
- Added another 12 new semantic concepts:
  - `bank_bill_rate`
  - `total_credit`
  - `total_credit_growth`
  - `housing_credit_growth`
  - `business_credit_growth`
  - `m3`
  - `money_base`
  - `currency_in_circulation`
  - `aud_cny`
  - `aud_jpy`
  - `aud_eur`
  - `aud_gbp`
  - `aud_nzd`

## [1.2.0] - 2026-05-14

### Added
- Added 7 new analyst-friendly semantic concepts:
  - `real_gdp`
  - `nominal_gdp`
  - `household_consumption`
  - `private_investment`
  - `retail_turnover`
  - `broad_money`
  - `bank_bill_rate``
- Added resolver, service-forwarding, generated-docs, and bounded live integration coverage for the new concepts.
- Added post-v1.1 roadmap documentation for v1.2, v1.3, v1.4, and v2.0.
- Added hosted deployment checklist documentation for `/`, `/healthz`, server-card metadata, Smithery listing state, and Render uptime.
- Added docs-site hygiene checks for Vercel Analytics and Speed Insights.

### Changed

- Updated README and generated semantic reference from 29 to 48 curated macroeconomic concepts.
- Corrected `f11` exchange-rate semantic metadata to monthly, matching the RBA series returned by `f11-data.csv`.
- Expanded operations documentation to distinguish MCP server observability from docs-site observability.
- Updated roadmap documentation to mark the first two v1.2 semantic tranches as landed.
- Kept ABS housing and monthly CPI replacement work deferred until source-native retrieval is stable.

### Fixed

- Fixed Python 3.10 CI failures by normalising nested optional-union parameter descriptions to top-level tool schema descriptions.
- Preserved Smithery/server-card compatibility across supported Python versions.

## [1.1.0] - 2026-05-12

### Added
- Added `ausecon-mcp-http`, a Streamable HTTP entrypoint for hosted MCP
  deployments at `/mcp`.
- Added Smithery custom-container packaging with `smithery.yaml` and
  `Dockerfile.smithery`.
- Added HTTP entrypoint, CORS, Smithery metadata, Docker packaging, and
  source-native identifier validation tests.

### Changed
- Documented Smithery as an additional hosted transport while preserving stdio
  as the default local and registry-oriented transport.
- Raised the FastMCP dependency floor for Streamable HTTP support and added
  Starlette as a direct dependency for HTTP middleware.

### Security
- Hardened source-native ABS/RBA identifiers and search inputs before HTTP
  exposure.
- Configured HTTP CORS without credentials and documented that the public
  Smithery design is only appropriate for read-only public-data tools.

## [1.0.0] - 2026-05-07

### Added
- Added `list_economic_concepts`, a model-controlled discovery tool for
  analyst-friendly concepts with source, dataset, variant, frequency,
  geography, aliases, and recommended `get_economic_series` calls.
- Added semantic bounds normalisation for `get_economic_series`, accepting
  `YYYY`, `YYYY-Qn`, `YYYY-Sn`, `YYYY-MM`, and `YYYY-MM-DD` while forwarding
  source-native ABS periods or RBA ISO dates internally.
- Added semantic provenance metadata to retrieval responses, including the
  requested bounds, resolved bounds, concept, variant, geography, frequency,
  and upstream target.
- Added response-schema coverage for optional semantic metadata and stronger
  prompt tests that validate documented tool-call snippets against the
  registered MCP tool contracts.

### Changed
- Reframed `get_economic_series` as the preferred LLM-facing retrieval tool,
  with raw ABS and RBA tools documented as expert source-native surfaces.
- Rewrote MCP prompts so suggested calls are valid, bounded, and aligned with
  the semantic workflow.
- Updated tool descriptions, human-readable annotation titles, server
  instructions, README workflows, architecture notes, and client smoke coverage
  for the V1 MCP user experience.
- `ausecon://concepts` now shares the same concept-index implementation as
  `list_economic_concepts`.

### Deprecated
- Marked `list_rba_tables` as a compatibility alias. New prompts and docs
  prefer `list_catalogue(source="rba")`.

## [0.13.1] - 2026-04-21

### Fixed
- Disk-cache permission failures now degrade a cache instance to in-process
  memory caching instead of emitting repeated warning-level `cache.disk_error`
  events on every access attempt.

## [0.13.0] - 2026-04-20

### Added
- New ABS catalogue entry `BUILDING_APPROVALS`, backed by live ABS dataflow
  `BA_GCCSA`, with a national residential approvals default.
- New semantic shortcut `dwelling_approvals` resolving to
  `BUILDING_APPROVALS.headline_approvals`.
- New maintainer docs at `docs/contributing.md`, a checked-in stdio client
  smoke path at `scripts/mcp_client_smoke.py`, and a release migration note at
  `docs/migration-v0.13.0.md`.

### Changed
- Runtime catalogue entries now expose only fully wired variants; placeholder
  ABS and RBA variants are no longer public in resources or semantic
  resolution.
- `RT` has been re-activated after live validation showed the ABS retail trade
  dataflow is current again.
- `BUILDING_ACTIVITY` no longer carries `building approvals` aliasing now that
  approvals have a dedicated live entry.

## [0.12.1] - 2026-04-19

### Fixed
- Synced `server.json` with the tagged release after `v0.12.0` was cut
  with stale MCP registry metadata (`0.11.0`).
- Promoted the `v0.12.0` contract-freeze notes out of `Unreleased` so the
  changelog reflects the actual tagged release history.

## [0.12.0] - 2026-04-19

### Added
- Checked-in response contract artefacts for the retrieval surface:
  `schemas/response.schema.json`, `docs/response-schema.md`, and example
  payloads under `examples/payloads/`.
- Additive `metadata.retrieved_at` on ABS and RBA retrieval responses so
  downstream users can distinguish upstream retrieval time from cache state.

### Changed
- Shared retrieval filtering now lives in `src/ausecon_mcp/filters.py`,
  keeping `last_n`, date-window, and series-pruning behaviour aligned across
  ABS and RBA payloads.
- The release workflow now smoke-installs the built wheel and verifies the
  `ausecon-mcp-server` console script before PyPI publish.

## [0.11.0] - 2026-04-19

### Added
- 24 new curated semantic concepts for `get_economic_series` across
  prices, labour, activity, rates, FX, external sector, and credit —
  taking the total from 4 to 28. Locked default mappings include
  `f17` for bond-yield tenors, two-series `housing_credit` from `d2`,
  `PPI_FD` for producer-price inflation, and the SDR index for
  `commodity_prices`.
- ABS structure-ID hardening via a new `resolve_abs_structure_id()`
  helper and optional `structure_id` field on ABS catalogue entries;
  `underemployment_rate` now composes its SDMX key against
  `DS_LF_UNDER` while keeping dataflow id `LF_UNDER` for data
  requests.
- `last_n` parameter on `get_economic_series`, forwarded to the
  underlying ABS or RBA call.
- New `list_catalogue` tool — unranked complement to
  `search_datasets` with source, category, tag, and
  ceased/discontinued filters.
- New `ausecon://concepts` MCP resource listing every curated
  shortcut with its resolved target.
- Two new prompt templates: `labour_slack_snapshot` and
  `yield_curve_snapshot`.

## [0.10.0] - 2026-04-19

### Changed
- Renamed catalogue entry `LCI` → `SLCI` to match the live ABS
  dataflow label; `upstream_id` indirection preserves resolver
  behaviour.
- Reclassified 4 ABS entries (`CPI_M`, `RT`, `BUSINESS_TURNOVER`,
  `RPPI`) from `discontinued` to `ceased` to distinguish
  upstream-dead from semantically retired datasets.
- Re-activated RBA table `a5` after confirming it is still live
  upstream; recategorised under `exchange_rates`.

### Added
- Every catalogue entry now carries an `audit` block
  (`last_audited`, `upstream_url`, `upstream_title`) calibrated
  against live ABS and RBA.
- `scripts/audit_catalogue.py` diffs the catalogue against the live
  ABS SDMX dataflow index and the RBA tables index and emits a
  markdown drift report.

## [0.9.0] - 2026-04-18

### Added
- Expanded RBA and ABS catalogue coverage with new data entries.
- Hardened CSV path resolution for RBA tables with non-standard
  URLs, plus supporting service tests.

## [0.8.0] - 2026-04-18

### Changed
- Hardened the on-disk cache path handling so all cache file reads,
  writes, and deletes are validated against the cache instance's
  trusted app-cache root.
- Removed support for the `AUSECON_CACHE_DIR` override. Disk cache
  writes now stay under the platform app-cache directory.
- Added an `Unreleased`-style follow-up cleanup to keep the branch
  locally clean under `ruff format --check`, reformatting previously
  drifting source files without changing runtime behaviour.

### Fixed
- Addressed the post-`v0.7.0` CodeQL findings by pinning third-party
  GitHub Actions to immutable commit SHAs and by adding explicit
  least-privilege top-level workflow permissions where required.

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

[Unreleased]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.13.1...v1.0.0
[0.13.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.12.1...v0.13.0
[0.12.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.5.5...v0.6.0
[0.5.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/releases/tag/v0.1.0

# Changelog

All notable changes to `ausecon-mcp-server` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.3.2]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/releases/tag/v0.1.0

# Claude Recommendation Review - 2026-05-18

This review triages the Claude Haiku 4.5 recommendations against the live
`ausecon-mcp-server` repository. The recommendations were treated as hypotheses, not
accepted findings.

## Summary

The review found useful test-hardening work, but Claude overstated several gaps. The
repository already had meaningful coverage for catalogue search, provider cache behaviour,
stale fallback, parse-error wrapping, and semantic-bound behaviour through service tests.

The implemented response is deliberately conservative:

- add direct validation unit tests for edge cases not covered by service integration tests;
- add direct semantic-bound tests for frequency inference and source-native conversion cases;
- move existing catalogue-search tests into a dedicated test module without duplicating them;
- defer broad provider deduplication because the provider cache semantics differ by source.

## Recommendation Triage

| Claude recommendation | Decision | Evidence and rationale |
|---|---|---|
| Add dedicated `validation.py` tests | Accept | `tests/test_server.py` covered several validation failures through the service surface, but direct unit tests were missing for unsafe URL/path text, trimmed length checks, APRA colon-delimited series IDs, ISO datetime variants, and half-yearly ABS periods. Added `tests/test_validation.py`. |
| Add dedicated `bounds.py` tests | Accept, modified | Service tests already covered key semantic bounds for ABS quarterly/monthly and RBA date conversion. Direct unit tests still add value for annual, half-yearly, frequency inference from `abs_key`, single-frequency catalogue entries, ambiguous ABS frequency, and invalid bound strings. Added `tests/test_bounds.py`. |
| Add `catalogue/search.py` ranking tests | Modify | Ranking tests already existed in `tests/test_catalogue.py`, including alias, exact ID, source filter, real GDP, ceased dataflows, and retail trade. Moved those tests to `tests/test_catalogue_search.py` for clearer ownership, without duplicating behaviour. |
| Introduce `providers/_fetch.py` shared helper | Reject for this pass | A shared helper would need to preserve different cache identities: RBA caches by table and applies `series_ids`, dates, and `last_n` after fetch; ABS includes source-native upstream date/update parameters in the cache key but applies `last_n` after fetch; APRA uses table-aware cache entries after a landing-page-to-XLSX download flow. The current duplication is less risky than hiding those differences behind a premature abstraction. |
| Extract APRA link extraction | Defer | `resolve_apra_download_url()` is already directly tested for trusted APRA HTTPS XLSX behaviour in `tests/test_apra_provider.py`. Extraction would be tidy, but not high-value unless the APRA provider grows further. |
| Add `.pyi` stubs | Reject | The package already ships `src/ausecon_mcp/py.typed`. Separate stubs would add maintenance surface without a current public typing problem. |
| Add request-scoped trace IDs | Defer | This is a cross-layer observability feature, not a small review cleanup. It should be designed separately if hosted or concurrent production traces become hard to correlate. |

## Provider Cache Semantics

Provider cache behaviour should be preserved as source-specific, not normalised by line count:

- RBA: `rba-table:{table_id}` stores the upstream table payload. `series_ids`,
  `start_date`, `end_date`, and `last_n` are client-side filters.
- ABS data: `abs-data:{dataflow_id}:{key}:{start_period}:{end_period}:{updated_after}`
  stores the upstream query payload. `last_n` is a client-side filter.
- APRA: `apra-publication:{publication_id}` or
  `apra-publication:{publication_id}:table:{table_id}` stores parsed workbook payloads
  after the landing-page link resolution and XLSX download. `series_ids`, dates, and
  `last_n` are client-side filters.

Any later provider refactor should first codify these invariants in tests and only then
extract shared behaviour.

## Verification Results

The implementation was checked with:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_validation.py tests/test_bounds.py tests/test_catalogue.py tests/test_catalogue_search.py -q
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_catalogue.py tests/test_rba_provider.py tests/test_abs_provider.py tests/test_apra_provider.py -q
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_server.py::test_service_normalises_semantic_abs_iso_bounds_for_quarterly_concept tests/test_server.py::test_service_normalises_semantic_abs_quarter_bounds_for_monthly_concept tests/test_server.py::test_service_normalises_semantic_rba_coarse_bounds_to_iso_dates tests/test_server.py::test_service_rejects_invalid_semantic_bounds_after_resolution tests/test_server.py::test_service_rejects_invalid_abs_period_format tests/test_server.py::test_service_rejects_mixed_abs_period_bounds -q
UV_CACHE_DIR=.uv-cache uv run ruff check src tests
UV_CACHE_DIR=.uv-cache uv run pytest -q
```

Observed results:

- Focused validation, bounds, catalogue, and catalogue-search tests: 63 passed.
- Provider/cache baseline: 44 passed. This is lower than the pre-move 52-test count because
  the search-ranking tests now live in `tests/test_catalogue_search.py`.
- Targeted semantic-bound service tests: 6 passed.
- Ruff: all checks passed.
- Full test suite: 639 passed.

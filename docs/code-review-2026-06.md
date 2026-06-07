# Code Review: ausecon-mcp-server

_Reviewed 7 June 2026 against `f5ef55e` (v1.6.1 release hygiene). Scope: `src/ausecon_mcp` core (server, providers, parsers, cache, validation, bounds, derived, filters, catalogue/search, models, logging) plus repo hygiene._

## Summary

This is a mature, carefully engineered MCP server (~9k LOC source, ~9k LOC tests). The layering is clean and disciplined — the MCP surface is genuinely thin and delegates to a service orchestrator, providers, pure parsers, and a curated catalogue, exactly as `CLAUDE.md` claims. Security posture is well above average for a data-wrapper: defence-in-depth input validation, an SSRF allowlist on APRA downloads, zip-bomb guards, atomic cache writes with path containment, and a stale-cache resilience fallback. The issues below are refinements, not structural problems. Overall verdict: **Approve**, with a handful of correctness and performance items worth addressing.

I could not execute the test suite in the review sandbox (restricted network blocked the Python/dependency download), so test commentary is from reading the 25 test modules and CI config rather than a live run. The suite breadth (schema-contract, repository-hygiene, parser benchmark, per-module) is a strength in itself.

## Critical / correctness issues

| # | File | Line(s) | Issue | Severity |
|---|------|---------|-------|----------|
| 1 | `filters.py` | 26–35 | `last_n` keeps the last _N_ rows **per series by list position**, assuming `observations` is already in chronological-ascending order. ABS SDMX CSV does not guarantee time ordering, so "latest N" can silently return the wrong observations. APRA explicitly sorts before this point; ABS and RBA rely on an undocumented source-order invariant. | 🟠 High |
| 2 | `server.py` | 657–664 | `get_latest_observations` for ABS downloads the **entire dataflow** (no period bounds) and then keeps the last _N_ client-side. The ABS API supports `lastNObservations`; not using it makes "give me the latest CPI print" potentially a multi-MB fetch. | 🟠 High |
| 3 | `parsers/abs_csv.py` | 71 | `parse_float(row["OBS_VALUE"])` raises `ValueError` on any non-numeric/thousands-separated value, which the provider escalates to a full `AuseconParseError` — one malformed cell fails the whole dataset. RBA/APRA degrade gracefully to `raw_value`; ABS does not. | 🟡 Medium |

## Suggestions

| # | File | Line(s) | Suggestion | Category |
|---|------|---------|------------|----------|
| 4 | `providers/abs.py`, `rba.py`, `apra.py` | e.g. abs 92 & 160 | Double `deepcopy` on every cache hit: `TTLCache.get()` already returns `deepcopy(entry.value)`, then the provider wraps it in `filter_payload(deepcopy(raw_payload), …)`. Drop the provider-side copy (the cache copy is already private) to halve copy cost on large payloads. | Performance |
| 5 | `server.py` | 619–631 | `get_derived_series` awaits each operand fetch sequentially. Operands are independent network calls — `asyncio.gather` them to roughly halve latency for two-operand derived series (most of them). | Performance |
| 6 | `cache.py` | 50–83 | No in-flight de-duplication: concurrent identical requests each hit upstream (cache stampede). A per-key `asyncio.Lock`/single-flight would cut redundant fetches under load. | Performance |
| 7 | `server.py` | 309–321, 1265 | `_normalise_registered_tool_parameter_descriptions` reaches into FastMCP internals (`_local_provider._components`). This is a silent-breakage risk on FastMCP upgrades; guard with a feature check or pin/track the FastMCP version explicitly. | Maintainability |
| 8 | `server.py` | 641–784 | `get_latest_observations`, `get_top_observations`, and `describe_dataset` repeat the same source-dispatch + per-source `_reject_parameter` ladder. Extract a small dispatch table / helper to remove the triplicated branching. | Maintainability |
| 9 | `server.py` | 386–389 | Provider params typed `ABSProvider \| Any \| None` — the `\| Any` defeats type-checking on the hot path. Define a `Protocol` for the provider interface so mocks satisfy it without `Any`. | Maintainability |
| 10 | `providers/abs.py` | 40–80 | `get_dataset_structure` has no stale-cache fallback, unlike `get_data` and the RBA/APRA equivalents. Minor inconsistency in resilience behaviour. | Correctness |
| 11 | `bounds.py` / `derived.py` | bounds 177–181; derived 178–180 | Nested ternaries in `_month_for`/`_quarter_for` (semester branch) are correct but hard to verify by eye. Flatten to explicit `if` blocks or a small lookup — date-boundary logic is exactly where you want maximum readability. | Maintainability |
| 12 | `providers/_retry.py` | 85–86 | Exponential backoff has no jitter. With several clients this can synchronise retries against ABS/RBA. Add a small random jitter to `delay`. | Performance |
| 13 | `server.py` | 1199–1204 | `CORSMiddleware(allow_origins=["*"])` and `authentication.required = False` are fine for public read-only data, but worth an explicit comment so a future private/auth’d deployment doesn’t inherit the open default unintentionally. | Security |
| 14 | `parsers/abs_csv.py` | 42 | `frequency` is taken from the first series only; a multi-frequency dataflow reports just the first in `metadata.frequency`. Consider omitting it (or making it a set) when ambiguous. | Correctness |

## Economic-methodology note (derived series)

The `derived.py` layer is a strength and the right call architecturally — keeping transformations transparent (formula, operands, source concepts, and dropped-observation accounting all stamped into metadata) is exactly what makes a derived indicator auditable. Two things worth a second look on the empirical side:

- **Mixed-frequency alignment via carry-forward.** `_carry_forward_to_periods` (used by `credit_to_gdp`, `mortgage_rate_spread`) carries the latest available higher-frequency value onto the lower-frequency grid. That is a defensible last-observation-carried-forward (LOCF) choice, but it is a methodological decision that should be surfaced to the analyst — it can bias spreads/ratios around turning points. It's already noted in `description`; consider also flagging the alignment method explicitly in the `derived` metadata block (you already expose `alignment_frequency`).
- **`real_cash_rate` is a real _ex-post_ rate** (cash rate target minus realised year-ended CPI), not an ex-ante real rate (minus _expected_ inflation). Both are legitimate, but they answer different questions; a one-line note in the concept description would prevent misinterpretation by a user who assumes the Fisher ex-ante definition.

These aren't bugs — the maths checks out — just places where the economic interpretation deserves to be explicit, consistent with the project's overall transparency ethos.

## What looks good

- **Input validation (`validation.py`).** Control-character / path / URI-scheme rejection, length caps, and source/category allowlisting, applied both at the Pydantic `Field` layer and again in the service — genuine defence in depth.
- **APRA fetch security (`providers/apra.py`).** Download URLs must be HTTPS, on an allowlisted host, and end in `.xlsx`; the parser adds zip-bomb guards (compressed size, member count, uncompressed total) and sheet-bound caps. This is the strongest part of the codebase.
- **Cache durability (`cache.py`).** Atomic `tempfile` + `os.replace`, SHA-256 keyed filenames, `relative_to` containment check on every path, and graceful permanent disable on `PermissionError`.
- **Resilience.** Stale-cache fallback on upstream failure, with provenance (`stale`, `cached_at`, `expires_at`) stamped onto the response — good operational behaviour and observable.
- **Non-blocking parsing.** `asyncio.to_thread` around the CPU-bound openpyxl parse keeps the event loop responsive.
- **Observability.** Structured JSON logging with reserved-key filtering and consistent `request.start/success/failed/retry` events.
- **Contract discipline.** A checked-in response JSON schema with contract tests, plus a repository-hygiene test and a parser benchmark.
- **Repo health.** No committed junk (`.DS_Store`/`__pycache__`/duplicate files seen in the working tree are local artefacts, not tracked), active dependabot + CodeQL, and consistent Australian English throughout the code and docs.

## Verdict

**Approve.** Ship-quality. Prioritise #1 (sort-before-`last_n`) and #2 (use ABS `lastNObservations`) — both are correctness/cost issues on the most common "latest value" path. #3 and the performance items (#4–#6) are good follow-ups. Everything else is polish.

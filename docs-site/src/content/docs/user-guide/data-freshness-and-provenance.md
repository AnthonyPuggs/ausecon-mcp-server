---
title: Data Freshness and Provenance
description: How ausecon keeps data fresh, fully source-traceable, and continuously verified.
---

Every value ausecon returns is fetched live from an official source and stamped with where it
came from. This page explains the guarantees behind the "fresh and fully source-traceable" promise.

## Every value is source-traceable

Each retrieval response stamps provenance onto `metadata`:

- `retrieval_url` — the exact upstream ABS, RBA, or APRA URL the data was read from.
- `retrieved_at` — UTC timestamp of the fetch.
- `server_version` — the ausecon version that produced the response.
- `updated_after` — echoes any upstream "updated after" filter you supplied.

Because the source URL travels with the data, any number can be traced straight back to the
official source that published it.

## Fresh by default, honest when stale

Values are fetched live on every call. A short-lived cache exists only for performance (so repeated
calls and fresh client processes do not re-hit upstream needlessly).

If — and only if — an upstream request *fails* and a previously cached payload exists, ausecon may
serve that last-good payload rather than error out. When it does, it says so explicitly:
`metadata.stale` is set to `true` alongside `cached_at` and `expires_at`. **Stale data is always
flagged, never served silently.** Parse errors are never masked this way — they surface so upstream
shape changes stay visible.

## Continuously verified

A nightly integration suite exercises the live ABS, RBA, and APRA sources and checks both:

- **Shape and availability** — datasets resolve and return well-formed observations.
- **Golden values** — specific known-good observations for finalized, non-revising periods (for
  example, the RBA cash-rate-target change on 3 August 2016) must still match the live source.

The pinned facts live in
[`integration_tests/golden_values.yaml`](https://github.com/AnthonyPuggs/ausecon-mcp-server/blob/main/integration_tests/golden_values.yaml).
If any check drifts, a tracked issue is opened automatically, so silent value or shape regressions
cannot go unnoticed. The current status is the **Integration** badge in the
[project README](https://github.com/AnthonyPuggs/ausecon-mcp-server#readme).

See the [Response Schema](/reference/response-schema/) for the full list of metadata fields.

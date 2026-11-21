---
title: Response Schema
description: The normalised retrieval contract for ABS, RBA, APRA, semantic, and derived responses.
---

The retrieval contract for `get_abs_data`, `get_rba_table`, `get_apra_data`,
`get_economic_series`, `get_derived_series`, `get_latest_observations`, and
`get_top_observations` is checked in at
[`schemas/response.schema.json`](https://github.com/AnthonyPuggs/ausecon-mcp-server/blob/main/schemas/response.schema.json).

## Top-level shape

Every retrieval response is a JSON object with three keys:

- `metadata`: source, dataset or table identifier, retrieval URL, and request-level metadata.
- `series`: long-form series descriptors.
- `observations`: long-form observations keyed by `series_id`.

## Metadata

Common fields include:

- `source`
- `dataset_id`
- `retrieval_url`
- `retrieved_at`
- `server_version`
- `truncated`

Optional fields appear when relevant:

- `frequency`
- `observations_dropped` — observations removed by `last_n` selection or the response limit
  below; `truncated` is `true` when this is non-zero
- `series_dropped` — series left out because the request matched more than one response holds
  (see below); pass `series_ids` to choose which series to return
- `updated_after`
- `title` and `publication_date`
- `semantic`
- `derived`
- `selection`
- `apra_url_resolution`
- `framework_breaks` and `warnings`
- `components`, on multi-concept `get_economic_series` responses (see below)
- `date_window` — the date bounds applied to an RBA or APRA download. Event-driven series
  listed in `carried_in`, such as the cash rate target, also keep their last change before
  `start`, because that value was still in effect when the window opens.
- `chart_note`, only for clients that display [inline charts](/user-guide/inline-charts/), when
  the result is shown as a chart. It tells the model the chart is already on screen.
- `stale`, `cached_at`, and `expires_at`

See [Data freshness and provenance](/user-guide/data-freshness-and-provenance/) for how these
provenance and freshness fields are produced and verified.

`semantic` appears on responses returned by `get_economic_series`. It records the requested
concept, resolved variant, requested bounds, resolved source-native bounds, and ABS/RBA/APRA
target. APRA semantic targets include `apra_table_id` and `apra_series_ids`. Raw source-native
responses from `get_abs_data`, `get_rba_table`, and `get_apra_data` do not include
`metadata.semantic`.

When `get_economic_series` is given a list of concepts, `source` is `multiple`, `dataset_id`
joins the component datasets with `+` (for example `LF+a2`), and `components` lists one entry per
concept in request order: the `series_ids` it returned and that concept's own `metadata`, including
its `semantic` block, `retrieval_url` and `date_window`. The top-level `retrieved_at` is the oldest
component's, `truncated` and `stale` are true if any component's is, and component warnings are
prefixed with their concept.

`derived` appears on responses returned by `get_derived_series`. It records the formula, operands,
source concepts, alignment frequency, output units, requested and resolved bounds, and
dropped-observation counts.

`selection` appears on responses returned by `get_latest_observations` and
`get_top_observations`. Latest-selection metadata records the requested count, returned observation
count, and series count. Top-selection metadata records whether the tool selected the highest or
lowest numeric observations, how many numeric observations were eligible, and how many non-numeric
rows were dropped before ranking.

`apra_url_resolution`, `framework_breaks`, and `warnings` appear where relevant on APRA responses.
The URL-resolution metadata records whether the workbook URL came from the live landing page or a
trusted bundled seed, with catalogue fallback as the final APRA-hosted XLSX path. Framework
warnings flag known source reporting breaks such as the AASB 17 insurance performance transition.

## Series and observations

`series` entries include `series_id`, `label`, optional `unit`, optional `frequency`, and a
`dimensions` map.

`observations` entries include `date`, `series_id`, nullable `value`, optional `raw_value`, a
`dimensions` map, optional `status`, and optional ABS comments.

Observations are returned in chronological order (ascending by period end date), regardless of
upstream row order. `last_n` selects the most recent N observations per series.

## Response limits

One tool response holds at most 200 series and about 5,000 observations. A request that matches
more series returns the first 200 in source order and records the rest in `series_dropped`. A
request with more observations keeps the same number of the most recent observations for every
series, so the newest value of each series always comes back, and sets `truncated`. Either way a
`warnings` entry says how to narrow the request: `series_ids` picks series, and a start date or
`last_n` picks the window. Derived indicators compute from complete data before any limit
applies.

Upstream downloads are limited too: 5 MB for an ABS data request and 8 MB for an RBA table. A
request over the limit, such as a whole ABS dataflow with no `key`, returns an error that says
how to narrow it.

Representative payloads live under
[`examples/payloads/`](https://github.com/AnthonyPuggs/ausecon-mcp-server/tree/main/examples/payloads)
and are validated in CI.

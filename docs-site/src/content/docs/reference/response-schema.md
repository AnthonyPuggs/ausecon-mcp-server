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
- `observations_dropped` — observations removed by `last_n` selection; `truncated` is
  `true` when this is non-zero
- `updated_after`
- `title` and `publication_date`
- `semantic`
- `derived`
- `selection`
- `apra_url_resolution`
- `framework_breaks` and `warnings`
- `stale`, `cached_at`, and `expires_at`

See [Data freshness and provenance](/user-guide/data-freshness-and-provenance/) for how these
provenance and freshness fields are produced and verified.

`semantic` appears on responses returned by `get_economic_series`. It records the requested
concept, resolved variant, requested bounds, resolved source-native bounds, and ABS/RBA/APRA
target. APRA semantic targets include `apra_table_id` and `apra_series_ids`. Raw source-native
responses from `get_abs_data`, `get_rba_table`, and `get_apra_data` do not include
`metadata.semantic`.

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

Representative payloads live under
[`examples/payloads/`](https://github.com/AnthonyPuggs/ausecon-mcp-server/tree/main/examples/payloads)
and are validated in CI.

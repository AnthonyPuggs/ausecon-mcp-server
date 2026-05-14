---
title: Response Schema
description: The normalised retrieval contract for ABS, RBA, APRA, semantic, and derived responses.
---

The retrieval contract for `get_abs_data`, `get_rba_table`, `get_apra_data`,
`get_economic_series`, and `get_derived_series` is checked in at
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
- `updated_after`
- `title` and `publication_date`
- `semantic`
- `derived`
- `stale`, `cached_at`, and `expires_at`

`semantic` appears on responses returned by `get_economic_series`. It records the requested
concept, resolved variant, requested bounds, resolved source-native bounds, and ABS/RBA target.
APRA is source-native only in the v1.4.0 foundation tranche, so APRA payloads do not include
`metadata.semantic`.

`derived` appears on responses returned by `get_derived_series`. It records the formula, operands,
source concepts, alignment frequency, output units, requested and resolved bounds, and
dropped-observation counts.

## Series and observations

`series` entries include `series_id`, `label`, optional `unit`, optional `frequency`, and a
`dimensions` map.

`observations` entries include `date`, `series_id`, nullable `value`, optional `raw_value`, a
`dimensions` map, optional `status`, and optional ABS comments.

Representative payloads live under
[`examples/payloads/`](https://github.com/AnthonyPuggs/ausecon-mcp-server/tree/main/examples/payloads)
and are validated in CI.

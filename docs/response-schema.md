# Response Schema

The retrieval contract for `get_abs_data`, `get_rba_table`, `get_economic_series`, and
`get_derived_series` is checked in at
[`schemas/response.schema.json`](../schemas/response.schema.json).

## Top-Level Shape

Every retrieval response is a JSON object with three keys:

- `metadata`: provenance and request-level fields.
- `series`: series descriptors present in the response.
- `observations`: long-form observations keyed by `series_id`.

## Metadata Fields

Common fields:

- `source`
- `dataset_id`
- `retrieval_url`
- `retrieved_at`
- `server_version`
- `truncated`

Optional fields appear when relevant:

- `frequency`
- `updated_after` for ABS requests that use the upstream SDMX filter
- `title` and `publication_date` for RBA tables
- `semantic` for responses returned by `get_economic_series`
- `derived` for responses returned by `get_derived_series`
- `stale`, `cached_at`, and `expires_at` when a stale cached payload is returned after an upstream failure

`cached_at` and `expires_at` are Unix timestamps from the cache layer rather than ISO datetimes.

`semantic` records the analyst-facing concept, resolved variant, requested `start`/`end` bounds,
source-native resolved bounds, and the ABS/RBA target used for retrieval. Raw `get_abs_data` and
`get_rba_table` responses do not include this field.

`derived` records the formula, operands, source concepts, alignment frequency, output units,
requested and resolved bounds, and dropped-observation counts for transparent derived indicators.

## Series And Observations

- `series` entries describe each returned series with `series_id`, `label`, optional `unit`,
  optional `frequency`, and a `dimensions` map. ABS payloads may also include
  `unit_multiplier`, `decimals`, and `base_period` when the upstream CSV supplies them.
- `observations` entries carry `date`, `series_id`, nullable `value`, optional `raw_value`,
  a `dimensions` map, optional `status`, and optional ABS `comment`.

The `dimensions` map is intentionally shared across ABS and RBA payloads so downstream consumers can
parse one stable shape.

## Checked-In Examples

Representative example payloads live under `examples/payloads/` and are validated against the schema
in CI.

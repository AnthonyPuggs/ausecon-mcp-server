# Response Schema

The retrieval contract for `get_abs_data`, `get_rba_table`, `get_apra_data`,
`get_economic_series`, and `get_derived_series` is checked in at
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
- `observations_dropped` — number of observations removed by `last_n` selection;
  `truncated` is `true` when this is non-zero
- `updated_after` for ABS requests that use the upstream SDMX filter
- `title` and `publication_date` for source-native table or publication metadata
- `semantic` for responses returned by `get_economic_series`
- `derived` for responses returned by `get_derived_series`
- `stale`, `cached_at`, and `expires_at` when a stale cached payload is returned after an upstream failure
- `warnings` — plain-English source warnings, including the empty-window notice when ABS
  reports no observations for the requested period

`cached_at` and `expires_at` are Unix timestamps from the cache layer rather than ISO datetimes.

`semantic` records the analyst-facing concept, resolved variant, requested `start`/`end` bounds,
source-native resolved bounds, and the ABS/RBA/APRA target used for retrieval. APRA semantic
targets include `apra_table_id` and `apra_series_ids`. Raw `get_abs_data`, `get_rba_table`, and
`get_apra_data` responses do not include this field.

`derived` records the formula, operands, source concepts, alignment frequency, output units,
requested and resolved bounds, and dropped-observation counts for transparent derived indicators.

## Series And Observations

- `series` entries describe each returned series with `series_id`, `label`, optional `unit`,
  optional `frequency`, and a `dimensions` map. ABS payloads may also include
  `unit_multiplier`, `decimals`, and `base_period` when the upstream CSV supplies them.
- `observations` entries carry `date`, `series_id`, nullable `value`, optional `raw_value`,
  a `dimensions` map, optional `status`, and optional ABS `comment`.

The `dimensions` map is intentionally shared across ABS, RBA, and APRA payloads so downstream
consumers can parse one stable shape.

Observations are returned in chronological order (ascending by period end date), regardless of
upstream row order. `last_n` selects the most recent N observations per series.

## Checked-In Examples

Representative example payloads live under `examples/payloads/` and are validated against the schema
in CI.

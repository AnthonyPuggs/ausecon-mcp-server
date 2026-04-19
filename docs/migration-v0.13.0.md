# v0.13.0 Migration Notes

## Public Surface Changes

- `RT` is live again and is no longer suppressed from ordinary discovery.
- `BUILDING_APPROVALS` is a new ABS catalogue entry backed by upstream dataflow `BA_GCCSA`.
- `dwelling_approvals` is a new semantic shortcut resolving to the national residential approvals
  series `1.1.9.TOT.100.10.AUS.M`.

## Variant Cleanup

Runtime catalogue entries now expose only fully wired variants.

That means placeholder variants such as undeclared ABS `abs_key` values or undeclared RBA
`rba_series_ids` are no longer visible through:

- `get_economic_series`
- `ausecon://abs/{dataflow_id}`
- `ausecon://rba/{table_id}`
- `ausecon://concepts`

If you previously depended on a placeholder variant name that never had a live series binding, the
runtime now treats it as an unknown variant. Use `get_abs_data` or `get_rba_table` directly until a
real wired variant is added.

## Deferred

`RPPI` remains ceased in `v0.13.0`. A like-for-like live replacement was not cleanly auditable
against the current time-series contract, so it has been left out of the semantic layer on purpose.

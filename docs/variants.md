# Semantic Variants

The semantic layer in `get_economic_series` stays source-aware. Each concept resolves to a concrete
ABS or RBA target, and optional variants narrow that target without turning the server into a broad
transformation engine.

## ABS Variant Forms

ABS catalogue variants use one of two encodings:

- **Literal SDMX keys** such as `Q.2.50`: every dimension is already pinned.
- **Fragments** such as `MEASURE=2;REGION=50`: only some dimensions are pinned, and the resolver
  completes the rest using the live ABS structure metadata plus any user-supplied `frequency` or
  `geography`.

Fragments exist so the catalogue can stay readable while still resolving against the current ABS
dimension order.

## RBA Variant Form

RBA catalogue variants declare one or more `rba_series_ids`. The resolver passes those series IDs to
`get_rba_table`, which filters the already-downloaded CSV client-side.

## Resolver Rules

- Unknown concepts and unsupported variants raise explicit validation errors.
- Variants declared without a concrete ABS key or `rba_series_ids` raise a clear “not yet wired” error.
- The semantic layer only exposes curated source-native concepts. Derived concepts remain deferred until after the retrieval contract is stable.

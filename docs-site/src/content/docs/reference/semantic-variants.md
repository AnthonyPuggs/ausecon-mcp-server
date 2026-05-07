---
title: Semantic Variants
description: How get_economic_series narrows ABS and RBA source targets.
---

The semantic layer stays source-aware. Each concept resolves to a concrete ABS or RBA target, and
optional variants narrow that target without turning the server into a broad transformation engine.

## ABS variants

ABS catalogue variants use one of two encodings:

- Literal SDMX keys such as `Q.2.50`, where every dimension is already pinned.
- Fragments such as `MEASURE=2;REGION=50`, where selected dimensions are pinned and the resolver
  completes the rest using live ABS structure metadata plus user-supplied `frequency` or
  `geography`.

## RBA variants

RBA catalogue variants declare one or more `rba_series_ids`. The resolver passes those IDs to
`get_rba_table`, which filters the already-downloaded CSV client-side.

## Resolver rules

- Unknown concepts and unsupported variants raise explicit validation errors.
- The runtime catalogue exposes only fully wired variants.
- Placeholder candidates stay out of the runtime catalogue until they have a real ABS key or RBA
  series binding.
- Derived concepts remain deferred until the retrieval contract can support them explicitly.

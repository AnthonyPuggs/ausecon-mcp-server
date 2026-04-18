"""Semantic resolver for curated ABS and RBA concepts.

Resolves ``(concept, variant, geography, frequency)`` into a concrete
``ResolvedQuery`` that downstream providers can execute directly: an ABS
SDMX key, or an RBA series-id allowlist.

Variant encoding for ABS datasets (``variants[*].abs_key``):

* Literal dot-key — e.g. ``"Q.2.50"``. Every dimension is pinned. Used
  verbatim when the caller does not add extra ``frequency`` / ``geography``
  constraints on top.
* Fragment form — e.g. ``"MEASURE=2"`` or ``"MEASURE=2;REGION=50"``.
  Pins only the dimensions the variant cares about; any remaining
  ``frequency`` / ``geography`` inputs fill the rest at resolve time by
  consulting the live SDMX ``DataStructure`` (via an injected fetcher).

Variant encoding for RBA tables (``variants[*].rba_series_ids``): a list
of series IDs that exist as columns in the RBA CSV. These are passed to
``RBAProvider.get_table(series_ids=...)``.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE
from ausecon_mcp.errors import AuseconValidationError

_FRAGMENT_PIECE_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)=([0-9A-Z_+]+)$")
_LITERAL_KEY_RE = re.compile(r"^[0-9A-Z_+]+(\.[0-9A-Z_+]+)*$")


def resolve_abs_dataflow_id(dataflow_id: str) -> str:
    """Map a catalogue key to its upstream ABS SDMX dataflow ID.

    Catalogue entries may declare an ``upstream_id`` when the ergonomic catalogue
    key differs from the real ABS dataflow identifier. Falls back to the input ID
    so unknown keys (and entries without ``upstream_id``) pass through unchanged.
    """
    entry = ABS_CATALOGUE.get(dataflow_id)
    if entry is None:
        return dataflow_id
    return entry.get("upstream_id", dataflow_id)


def resolve_abs_structure_id(dataflow_id: str) -> str:
    """Map a catalogue key to its upstream ABS SDMX DataStructure ID.

    Some ABS dataflows expose their DataStructure under a different ID than the
    dataflow itself (for example, dataflow ``LF_UNDER`` has structure
    ``DS_LF_UNDER``). Catalogue entries may declare an optional ``structure_id``
    to capture this. Falls back to the dataflow id so unknown keys and entries
    without ``structure_id`` pass through unchanged.
    """
    entry = ABS_CATALOGUE.get(dataflow_id)
    if entry is None:
        return dataflow_id
    return entry.get("structure_id", dataflow_id)


def resolve_rba_csv_path(table_id: str) -> str:
    """Map a catalogue key to its upstream RBA CSV filename.

    Most RBA tables follow ``{table_id}-data.csv``; catalogue entries may declare
    an explicit ``csv_path`` for the exceptions (e.g. ``f17``). Falls back to the
    default pattern for unknown keys and entries without ``csv_path``.
    """
    entry = RBA_CATALOGUE.get(table_id)
    if entry is not None:
        explicit = entry.get("csv_path")
        if explicit:
            return explicit
    return f"{table_id}-data.csv"


CURATED_SHORTCUTS: dict[str, dict[str, Any]] = {
    "cash_rate_target": {"source": "rba", "dataset_id": "a2", "variant": "target"},
    "headline_cpi": {"source": "abs", "dataset_id": "CPI", "variant": "headline"},
    "trimmed_mean_inflation": {"source": "rba", "dataset_id": "g1", "variant": "trimmed_mean"},
    "gdp_growth": {"source": "abs", "dataset_id": "ANA_AGG", "variant": "gdp_growth"},
    # Tranche A
    "employment": {"source": "abs", "dataset_id": "LF", "variant": "employment"},
    "unemployment_rate": {"source": "abs", "dataset_id": "LF", "variant": "unemployment_rate"},
    "participation_rate": {"source": "abs", "dataset_id": "LF", "variant": "participation_rate"},
    "wage_growth": {"source": "abs", "dataset_id": "WPI", "variant": "headline_wpi"},
    "trade_balance": {"source": "abs", "dataset_id": "ITGS", "variant": "trade_balance"},
    "weighted_median_inflation": {
        "source": "rba",
        "dataset_id": "g1",
        "variant": "weighted_median",
    },
    "monthly_inflation": {"source": "rba", "dataset_id": "g4", "variant": "headline_monthly"},
    "aud_usd": {"source": "rba", "dataset_id": "f11", "variant": "aud_usd"},
    "trade_weighted_index": {"source": "rba", "dataset_id": "f11", "variant": "twi"},
    "government_bond_yield_3y": {"source": "rba", "dataset_id": "f17", "variant": "ags_3y"},
    "government_bond_yield_10y": {"source": "rba", "dataset_id": "f17", "variant": "ags_10y"},
    "housing_credit": {"source": "rba", "dataset_id": "d2", "variant": "housing"},
}


@dataclass(frozen=True)
class ResolvedQuery:
    source: str
    dataset_id: str
    abs_key: str | None
    rba_series_ids: list[str] | None
    frequency: str | None
    variant: str | None
    geography: str | None
    entry: dict[str, Any]


async def resolve(
    concept: str,
    *,
    variant: str | None = None,
    geography: str | None = None,
    frequency: str | None = None,
    abs_structure_fetcher: Callable[[str], Awaitable[dict]] | None = None,
) -> ResolvedQuery:
    """Resolve a semantic concept to a concrete provider query."""
    if not isinstance(concept, str) or not concept.strip():
        raise AuseconValidationError("concept must be a non-empty string.")
    concept_text = concept.strip()

    source, dataset_id, entry = _match_concept(concept_text)
    applied_variant = _match_variant(entry, _pick_variant(concept_text, variant))

    _validate_frequency(entry, frequency)
    _validate_geography(entry, geography)

    if source == "rba":
        return ResolvedQuery(
            source="rba",
            dataset_id=dataset_id,
            abs_key=None,
            rba_series_ids=_resolve_rba_series_ids(entry, applied_variant),
            frequency=frequency,
            variant=applied_variant["name"] if applied_variant else None,
            geography=geography,
            entry=entry,
        )

    abs_key = await _resolve_abs_key(
        entry,
        applied_variant,
        frequency=frequency,
        geography=geography,
        abs_structure_fetcher=abs_structure_fetcher,
    )
    return ResolvedQuery(
        source="abs",
        dataset_id=dataset_id,
        abs_key=abs_key,
        rba_series_ids=None,
        frequency=frequency,
        variant=applied_variant["name"] if applied_variant else None,
        geography=geography,
        entry=entry,
    )


def _pick_variant(concept: str, user_variant: str | None) -> str | None:
    shortcut = CURATED_SHORTCUTS.get(concept)
    if shortcut is None:
        return user_variant
    return user_variant or shortcut.get("variant")


def _match_concept(concept: str) -> tuple[str, str, dict[str, Any]]:
    shortcut = CURATED_SHORTCUTS.get(concept)
    if shortcut is not None:
        source = shortcut["source"]
        dataset_id = shortcut["dataset_id"]
        catalogue = ABS_CATALOGUE if source == "abs" else RBA_CATALOGUE
        entry = catalogue.get(dataset_id)
        if entry is None:
            raise AuseconValidationError(
                f"Curated shortcut {concept!r} points at unknown {source} dataset {dataset_id!r}."
            )
        return source, dataset_id, entry

    abs_entry = ABS_CATALOGUE.get(concept)
    rba_entry = RBA_CATALOGUE.get(concept)
    if abs_entry and rba_entry:
        raise AuseconValidationError(
            f"Concept {concept!r} is ambiguous; it matches both ABS and RBA datasets. "
            "Pass a curated shortcut instead."
        )
    if abs_entry:
        return "abs", abs_entry["id"], abs_entry
    if rba_entry:
        return "rba", rba_entry["id"], rba_entry

    candidates: list[tuple[str, str, dict[str, Any]]] = []
    lowered = concept.lower()
    for src, collection in (("abs", ABS_CATALOGUE), ("rba", RBA_CATALOGUE)):
        for entry in collection.values():
            if entry.get("discontinued", False):
                continue
            aliases = [alias.strip().lower() for alias in entry.get("aliases", [])]
            if lowered in aliases:
                candidates.append((src, entry["id"], entry))

    if not candidates:
        supported = ", ".join(sorted(CURATED_SHORTCUTS))
        raise AuseconValidationError(
            f"Unknown concept {concept!r}. Try search_datasets for discovery, "
            f"or use one of the curated shortcuts: {supported}."
        )
    if len(candidates) > 1:
        matches = ", ".join(f"{src}/{id_}" for src, id_, _ in candidates)
        raise AuseconValidationError(
            f"Concept {concept!r} is ambiguous; it matches: {matches}. "
            "Pass a dataset id directly (for example 'CPI' or 'g1')."
        )
    src, id_, entry = candidates[0]
    return src, id_, entry


def _match_variant(entry: dict[str, Any], variant: str | None) -> dict[str, Any] | None:
    if variant is None:
        return None
    variants = entry.get("variants", [])
    lowered = variant.strip().lower()
    for candidate in variants:
        if candidate["name"].lower() == lowered:
            return candidate
        aliases = [alias.strip().lower() for alias in candidate.get("aliases", [])]
        if lowered in aliases:
            return candidate
    known = ", ".join(v["name"] for v in variants) or "(none declared)"
    raise AuseconValidationError(
        f"Unknown variant {variant!r} for concept {entry['id']!r}. Known variants: {known}."
    )


def _validate_frequency(entry: dict[str, Any], frequency: str | None) -> None:
    if frequency is None:
        return
    freqs = entry.get("frequencies", [])
    if frequency not in freqs:
        raise AuseconValidationError(
            f"Frequency {frequency!r} is not supported for {entry['id']!r}. "
            f"Supported frequencies: {', '.join(freqs) or '(none)'}."
        )


def _validate_geography(entry: dict[str, Any], geography: str | None) -> None:
    if geography is None:
        return
    geos = entry.get("geographies", [])
    if geography not in geos:
        raise AuseconValidationError(
            f"Geography {geography!r} is not supported for {entry['id']!r}. "
            f"Supported geographies: {', '.join(geos) or '(none)'}."
        )


def _resolve_rba_series_ids(
    entry: dict[str, Any],
    variant: dict[str, Any] | None,
) -> list[str] | None:
    if variant is None:
        return None
    series_ids = variant.get("rba_series_ids")
    if series_ids is None:
        raise AuseconValidationError(
            f"Variant {variant['name']!r} is declared for {entry['id']!r} but has no "
            "rba_series_ids populated yet. Call get_rba_table directly in the meantime."
        )
    return list(series_ids)


async def _resolve_abs_key(
    entry: dict[str, Any],
    variant: dict[str, Any] | None,
    *,
    frequency: str | None,
    geography: str | None,
    abs_structure_fetcher: Callable[[str], Awaitable[dict]] | None,
) -> str | None:
    variant_key = variant.get("abs_key") if variant else None

    if variant is not None and variant_key is None:
        raise AuseconValidationError(
            f"Variant {variant['name']!r} is declared for {entry['id']!r} but has no "
            "abs_key populated yet. Call get_abs_data directly in the meantime."
        )

    if variant_key is None and frequency is None and geography is None:
        return None

    is_literal = bool(variant_key) and _LITERAL_KEY_RE.match(variant_key) is not None
    if is_literal and frequency is None and geography is None:
        return variant_key

    if abs_structure_fetcher is None:
        raise AuseconValidationError(
            f"Resolving {entry['id']!r} with variant/frequency/geography requires the "
            "ABS dataset structure; no abs_structure_fetcher was provided."
        )
    structure = await abs_structure_fetcher(resolve_abs_structure_id(entry["id"]))

    fragment: dict[str, str] = {}
    if variant_key is not None:
        fragment = _fragment_from_variant_key(variant_key, structure)

    return build_abs_key(
        structure,
        variant_fragment=fragment,
        frequency=frequency,
        geography=geography,
        geography_codes=entry.get("geography_codes", {}),
    )


def _fragment_from_variant_key(variant_key: str, structure: dict[str, Any]) -> dict[str, str]:
    if _LITERAL_KEY_RE.match(variant_key):
        ordered_dims = sorted(structure.get("dimensions", []), key=lambda dim: dim["position"])
        fragment: dict[str, str] = {}
        for dim, part in zip(ordered_dims, variant_key.split("."), strict=False):
            if part:
                fragment[dim["id"]] = part
        return fragment
    return _parse_fragment(variant_key)


def _parse_fragment(fragment: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for raw in fragment.split(";"):
        piece = raw.strip()
        if not piece:
            continue
        match = _FRAGMENT_PIECE_RE.match(piece)
        if not match:
            raise AuseconValidationError(
                f"Invalid SDMX key fragment piece {piece!r}; expected DIM=code."
            )
        parts[match.group(1)] = match.group(2)
    return parts


def build_abs_key(
    structure: dict[str, Any],
    *,
    variant_fragment: dict[str, str],
    frequency: str | None,
    geography: str | None,
    geography_codes: dict[str, str],
    freq_dim: str = "FREQ",
    region_dim: str = "REGION",
) -> str:
    """Compose an SDMX dot-key in the order declared by ``structure["dimensions"]``."""
    dim_to_code: dict[str, str] = dict(variant_fragment)

    if frequency is not None and freq_dim not in dim_to_code:
        dim_to_code[freq_dim] = frequency
    if geography is not None and region_dim not in dim_to_code:
        if geography not in geography_codes:
            raise AuseconValidationError(
                f"No geography code mapped for {geography!r} in {structure['id']!r}. "
                "Add a geography_codes mapping on the catalogue entry."
            )
        dim_to_code[region_dim] = geography_codes[geography]

    known_dims = {dim["id"]: dim for dim in structure.get("dimensions", [])}
    for dim_id, code in dim_to_code.items():
        dim = known_dims.get(dim_id)
        if dim is None:
            raise AuseconValidationError(
                f"Dimension {dim_id!r} is not present in structure for {structure['id']!r}."
            )
        allowed = {value["code"] for value in dim.get("values", [])}
        if allowed and code not in allowed:
            raise AuseconValidationError(
                f"Code {code!r} is not in codelist for dimension {dim_id!r} "
                f"(dataset {structure['id']!r})."
            )

    ordered = sorted(structure.get("dimensions", []), key=lambda dim: dim["position"])
    parts = [dim_to_code.get(dim["id"], "") for dim in ordered]
    while parts and parts[-1] == "":
        parts.pop()
    return ".".join(parts)

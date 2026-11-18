"""Merge several curated-concept payloads into one multi-source response.

``get_economic_series`` with a list of concepts fetches each one through the ordinary
single-concept path, then merges them here. The result keeps the normalised
``{metadata, series, observations}`` shape, with ``metadata.source = "multiple"`` and each
concept's own metadata (source, retrieval URL, semantic resolution, date window, ...) under
``metadata.components``, so every series keeps exact provenance.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.periods import try_period_sort_key

# One concept per chart colour: the inline chart draws at most eight series.
MAX_CONCEPTS = 8

# Added per response by the chart middleware; never part of a component. server_version stays:
# component metadata validates against the same schema definition, which requires it.
_COMPONENT_ONLY_FIELDS = ("chart_note",)


def merge_concept_payloads(parts: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Merge ``(concept, payload)`` pairs, in request order, into one response."""
    series: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    owner: dict[str, tuple[str, str]] = {}  # series_id -> (source, dataset_id) that supplied it

    for concept, payload in parts:
        metadata = deepcopy(payload.get("metadata") or {})
        dataset = (str(metadata.get("source")), str(metadata.get("dataset_id")))
        series_ids: list[str] = []
        fresh: set[str] = set()
        for descriptor in payload.get("series") or []:
            series_id = descriptor["series_id"]
            series_ids.append(series_id)
            if series_id in owner:
                if owner[series_id] != dataset:
                    raise AuseconValidationError(
                        f"Concept '{concept}' returns series {series_id!r}, which another "
                        f"concept also returns from {owner[series_id][0].upper()} "
                        f"{owner[series_id][1]}; retrieve these concepts separately."
                    )
                continue
            owner[series_id] = dataset
            fresh.add(series_id)
            series.append(deepcopy(descriptor))
        observations.extend(
            deepcopy(item)
            for item in payload.get("observations") or []
            if item["series_id"] in fresh
        )
        for field in _COMPONENT_ONLY_FIELDS:
            metadata.pop(field, None)
        components.append({"series_ids": series_ids, "metadata": metadata})

    keys = [try_period_sort_key(item["date"]) for item in observations]
    if all(key is not None for key in keys):
        order = sorted(range(len(observations)), key=lambda index: keys[index])
        observations = [observations[index] for index in order]

    component_meta = [component["metadata"] for component in components]
    first = parts[0][1].get("metadata") or {}
    merged: dict[str, Any] = {
        "source": "multiple",
        "dataset_id": "+".join(str(meta.get("dataset_id")) for meta in component_meta),
        "title": ", ".join(concept for concept, _ in parts),
    }
    frequencies = {meta.get("frequency") for meta in component_meta}
    if len(frequencies) == 1 and next(iter(frequencies)):
        merged["frequency"] = next(iter(frequencies))
    retrieved = [meta["retrieved_at"] for meta in component_meta if meta.get("retrieved_at")]
    if retrieved:
        # The oldest retrieval, so the combined result never looks fresher than its parts.
        merged["retrieved_at"] = min(retrieved)
    if "server_version" in first:
        merged["server_version"] = first["server_version"]
    merged["truncated"] = any(bool(meta.get("truncated")) for meta in component_meta)
    merged["observations_dropped"] = sum(
        int(meta.get("observations_dropped") or 0) for meta in component_meta
    )
    if any(meta.get("stale") for meta in component_meta):
        merged["stale"] = True
    warnings = [
        f"{concept}: {warning}"
        for (concept, _), meta in zip(parts, component_meta, strict=True)
        for warning in meta.get("warnings") or []
    ]
    if warnings:
        merged["warnings"] = warnings
    merged["components"] = components

    return {"metadata": merged, "series": series, "observations": observations}

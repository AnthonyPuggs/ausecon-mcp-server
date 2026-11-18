from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from difflib import get_close_matches
from typing import Any

from ausecon_mcp.errors import AuseconValidationError
from ausecon_mcp.periods import period_end_date, period_start_date, try_period_sort_key

# How many of a dataset's series an unknown-series_ids message lists.
MAX_LISTED_SERIES = 30
# Bounds on the unknown-series_ids message: fuzzy matching runs against every series in the
# dataset (thousands for APRA), so only the first few unknown IDs get suggestions.
MAX_QUOTED_UNKNOWN = 10
MAX_SUGGESTED_UNKNOWN = 5
# Series whose value holds until the next change (RBA policy rates are "As announced").
# Matches the chart view's step-line rule, less "irregular", which also covers flows.
EVENT_DRIVEN_FREQUENCY = re.compile(r"announc|event", re.IGNORECASE)


def filter_payload(
    payload: dict[str, Any],
    *,
    series_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    last_n: int | None = None,
) -> dict[str, Any]:
    observations = payload["observations"]
    if series_ids:
        _check_series_ids(payload, series_ids)
        allowed = set(series_ids)
        observations = [item for item in observations if item["series_id"] in allowed]

    sort_keys = [try_period_sort_key(item["date"]) for item in observations]
    if all(key is not None for key in sort_keys):
        # Source row order is unreliable (ABS SDMX CSVs arrive unordered), so establish
        # chronological order before bound filtering and last_n selection. The sort is
        # stable, preserving source order for observations sharing a period.
        observations = [
            item
            for _, item in sorted(
                zip(sort_keys, observations, strict=True), key=lambda pair: pair[0]
            )
        ]
        carried_in: list[str] = []
        if start_date:
            window_start = period_start_date(start_date)
            carried = _carried_in_observations(payload, observations, window_start)
            carried_in = [item["series_id"] for item in carried]
            observations = carried + [
                item for item in observations if period_end_date(item["date"]) >= window_start
            ]
        if end_date:
            window_end = period_end_date(end_date)
            observations = [
                item for item in observations if period_start_date(item["date"]) <= window_end
            ]
        if start_date or end_date:
            payload["metadata"]["date_window"] = {
                "start": period_start_date(start_date).isoformat() if start_date else None,
                "end": period_end_date(end_date).isoformat() if end_date else None,
                "carried_in": carried_in,
            }
    else:
        # Unrecognised period format: keep source order and fall back to string bounds
        # rather than failing the whole retrieval.
        if start_date:
            observations = [item for item in observations if item["date"] >= start_date]
        if end_date:
            observations = [item for item in observations if item["date"] <= end_date]

    truncated = False
    dropped = 0
    if last_n is not None and last_n > 0 and len(observations) > last_n:
        keep_indices: set[int] = set()
        seen_by_series: dict[str, int] = defaultdict(int)
        for index in range(len(observations) - 1, -1, -1):
            series_id = observations[index]["series_id"]
            seen_by_series[series_id] += 1
            if seen_by_series[series_id] <= last_n:
                keep_indices.add(index)
        dropped = len(observations) - len(keep_indices)
        truncated = dropped > 0
        observations = [item for index, item in enumerate(observations) if index in keep_indices]

    series_id_set = {item["series_id"] for item in observations}
    payload["series"] = [item for item in payload["series"] if item["series_id"] in series_id_set]
    payload["observations"] = observations
    payload["metadata"]["truncated"] = truncated
    payload["metadata"]["observations_dropped"] = dropped
    return payload


def _carried_in_observations(
    payload: dict[str, Any], observations: list[dict[str, Any]], window_start: date
) -> list[dict[str, Any]]:
    """The latest pre-window observation of each event-driven series, when the series has no
    observation on the window start itself.

    An event-driven series (a policy rate "as announced") holds its value until the next
    change, so the value in effect at the window start is the last change before it. Dropping
    it made "cash rate since 2019" begin at the June 2019 cut, and a window with no change
    inside it returned nothing at all. ``observations`` must already be chronological.
    """
    event_driven = {
        item["series_id"]
        for item in payload.get("series") or []
        if EVENT_DRIVEN_FREQUENCY.search(str(item.get("frequency") or ""))
    }
    if not event_driven:
        return []
    latest_before: dict[str, dict[str, Any]] = {}
    on_start: set[str] = set()
    for item in observations:
        series_id = item["series_id"]
        if series_id not in event_driven or item.get("value") is None:
            continue
        start = period_start_date(item["date"])
        if start < window_start:
            latest_before[series_id] = item
        elif start == window_start:
            on_start.add(series_id)
    return [item for series_id, item in latest_before.items() if series_id not in on_start]


def _check_series_ids(payload: dict[str, Any], series_ids: list[str]) -> None:
    """Reject series_ids that match nothing, and warn about any that match nothing alongside
    ones that do.

    An unmatched ID used to produce an empty result, leaving the caller (usually a model that
    guessed an ID such as FCMYGBAG2 for FCMYGBAG2D) with nothing to correct it from.
    """
    descriptors = payload.get("series") or []
    available = [item["series_id"] for item in descriptors]
    if not available:
        return
    known = set(available)
    unknown = [series_id for series_id in series_ids if series_id not in known]
    if not unknown:
        return

    metadata = payload.get("metadata") or {}
    dataset = " ".join(
        part
        for part in (str(metadata.get("source") or "").upper(), metadata.get("dataset_id"))
        if part
    )
    quoted = ", ".join(repr(series_id) for series_id in unknown[:MAX_QUOTED_UNKNOWN])
    if len(unknown) > MAX_QUOTED_UNKNOWN:
        quoted += f" and {len(unknown) - MAX_QUOTED_UNKNOWN} more"
    suggestions = []
    for series_id in unknown[:MAX_SUGGESTED_UNKNOWN]:
        for match in get_close_matches(series_id, available, n=1, cutoff=0.6):
            if match not in suggestions:
                suggestions.append(match)
    hint = f" Did you mean {', '.join(suggestions)}?" if suggestions else ""

    if len(unknown) < len(series_ids):
        payload.setdefault("metadata", {}).setdefault("warnings", []).append(
            f"series_ids not found in {dataset or 'this dataset'} and ignored: {quoted}.{hint}"
        )
        return

    listed = "; ".join(
        f"{item['series_id']} ({item['label']})" if item.get("label") else item["series_id"]
        for item in descriptors[:MAX_LISTED_SERIES]
    )
    more = len(descriptors) - MAX_LISTED_SERIES
    if more > 0:
        listed += f"; and {more} more"
    raise AuseconValidationError(
        f"None of the requested series_ids are in {dataset or 'this dataset'}: {quoted}.{hint} "
        f"Available series: {listed}."
    )


def strip_observation_dimensions(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop the per-observation dimension dicts, keeping them on the series descriptors.

    Each observation repeats the dimension dict already present on its series
    descriptor (and encoded in ``series_id``), roughly tripling payload size for
    no information.
    """
    for observation in payload.get("observations", []):
        observation.pop("dimensions", None)
    return payload


def compact_observation_dimensions(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop observation dimension dicts that equal their series descriptor's.

    Unlike ``strip_observation_dimensions`` this is lossless: observations whose
    dimensions differ (APRA institutions renamed under the same ABN) keep them, and
    ``expand_observation_dimensions`` restores the rest. Used to keep large cached
    payloads small.
    """
    series_dimensions = {item["series_id"]: item.get("dimensions") for item in payload["series"]}
    for observation in payload.get("observations", []):
        dimensions = observation.get("dimensions")
        if dimensions is not None and dimensions == series_dimensions.get(observation["series_id"]):
            del observation["dimensions"]
    return payload


def expand_observation_dimensions(payload: dict[str, Any]) -> dict[str, Any]:
    """Restore observation dimensions removed by ``compact_observation_dimensions``."""
    series_dimensions = {item["series_id"]: item.get("dimensions") for item in payload["series"]}
    for observation in payload.get("observations", []):
        if "dimensions" not in observation:
            dimensions = series_dimensions.get(observation["series_id"])
            if dimensions is not None:
                observation["dimensions"] = dimensions
    return payload

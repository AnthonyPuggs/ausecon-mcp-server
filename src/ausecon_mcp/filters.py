from __future__ import annotations

from collections import defaultdict
from typing import Any

from ausecon_mcp.periods import period_end_date, period_start_date, try_period_sort_key


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
        if start_date:
            window_start = period_start_date(start_date)
            observations = [
                item for item in observations if period_end_date(item["date"]) >= window_start
            ]
        if end_date:
            window_end = period_end_date(end_date)
            observations = [
                item for item in observations if period_start_date(item["date"]) <= window_end
            ]
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


def strip_observation_dimensions(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop the per-observation dimension dicts, keeping them on the series descriptors.

    Each observation repeats the dimension dict already present on its series
    descriptor (and encoded in ``series_id``), roughly tripling payload size for
    no information.
    """
    for observation in payload.get("observations", []):
        observation.pop("dimensions", None)
    return payload

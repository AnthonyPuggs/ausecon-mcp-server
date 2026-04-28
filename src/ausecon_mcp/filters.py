from __future__ import annotations

from collections import defaultdict
from typing import Any


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

    if start_date:
        observations = [item for item in observations if item["date"] >= start_date]
    if end_date:
        observations = [item for item in observations if item["date"] <= end_date]

    truncated = False
    if last_n is not None and last_n > 0 and len(observations) > last_n:
        keep_indices: set[int] = set()
        seen_by_series: dict[str, int] = defaultdict(int)
        for index in range(len(observations) - 1, -1, -1):
            series_id = observations[index]["series_id"]
            seen_by_series[series_id] += 1
            if seen_by_series[series_id] <= last_n:
                keep_indices.add(index)
        truncated = len(keep_indices) < len(observations)
        observations = [item for index, item in enumerate(observations) if index in keep_indices]

    series_id_set = {item["series_id"] for item in observations}
    payload["series"] = [item for item in payload["series"] if item["series_id"] in series_id_set]
    payload["observations"] = observations
    payload["metadata"]["truncated"] = truncated
    return payload

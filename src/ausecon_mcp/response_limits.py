"""Bounds on what one retrieval tool response returns.

Unfiltered requests can be very large: a whole RBA table such as F16 is over 100,000
observations (about 10 MB of JSON), and one APRA publication holds thousands of series. These
limits apply at the MCP tool boundary only, so derived indicators and the latest/top selections
still compute from complete data.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

MAX_RESPONSE_SERIES = 200
MAX_RESPONSE_OBSERVATIONS = 5_000


def limit_response(
    payload: dict[str, Any],
    *,
    max_series: int | None = None,
    max_observations: int | None = None,
) -> dict[str, Any]:
    """Keep at most ``max_series`` series and about ``max_observations`` observations.

    Series beyond the limit are dropped in source order. Observations over the limit are
    trimmed to the same most-recent count for every series, never fewer than one, so the
    newest value of each kept series always survives. ``observations`` must be chronological.
    """
    # Read the module limits at call time so tests can raise them.
    max_series = MAX_RESPONSE_SERIES if max_series is None else max_series
    max_observations = MAX_RESPONSE_OBSERVATIONS if max_observations is None else max_observations
    metadata = payload.setdefault("metadata", {})
    series = payload.get("series") or []
    observations = payload.get("observations") or []

    if len(series) > max_series:
        kept_series = series[:max_series]
        kept_ids = {item["series_id"] for item in kept_series}
        payload["series"] = kept_series
        observations = [item for item in observations if item["series_id"] in kept_ids]
        payload["observations"] = observations
        metadata["series_dropped"] = len(series) - max_series
        metadata.setdefault("warnings", []).append(
            f"This request matches {len(series):,} series; the response holds the first "
            f"{max_series}. Pass series_ids to choose which series to return."
        )

    if len(observations) > max_observations:
        series_count = len({item["series_id"] for item in observations})
        per_series = max(1, max_observations // max(series_count, 1))
        seen: dict[str, int] = defaultdict(int)
        keep: list[bool] = [False] * len(observations)
        for index in range(len(observations) - 1, -1, -1):
            series_id = observations[index]["series_id"]
            seen[series_id] += 1
            keep[index] = seen[series_id] <= per_series
        kept = [item for item, flag in zip(observations, keep, strict=True) if flag]
        dropped = len(observations) - len(kept)
        payload["observations"] = kept
        metadata["truncated"] = True
        metadata["observations_dropped"] = int(metadata.get("observations_dropped") or 0) + dropped
        metadata.setdefault("warnings", []).append(
            f"Returned the most recent {per_series:,} observations of each series "
            f"({dropped:,} older ones dropped) to keep the response under "
            f"{max_observations:,} observations. Set a start date (start_date, start_period "
            "or start, depending on the tool) or last_n to choose the window."
        )

    return payload

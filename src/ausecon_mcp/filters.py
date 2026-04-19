from __future__ import annotations

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
        observations = observations[-last_n:]
        truncated = True

    series_id_set = {item["series_id"] for item in observations}
    payload["series"] = [item for item in payload["series"] if item["series_id"] in series_id_set]
    payload["observations"] = observations
    payload["metadata"]["truncated"] = truncated
    return payload

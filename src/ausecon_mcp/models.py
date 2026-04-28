from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def split_code_and_label(value: str) -> tuple[str, str]:
    raw = (value or "").strip()
    if ":" not in raw:
        return raw, raw
    code, label = raw.split(":", 1)
    return code.strip(), label.strip()


def parse_float(value: str) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    return float(text)


@dataclass
class SeriesDescriptor:
    series_id: str
    label: str
    unit: str | None = None
    frequency: str | None = None
    dimensions: dict[str, dict[str, str]] = field(default_factory=dict)
    source_key: str | None = None
    unit_multiplier: int | None = None
    decimals: int | None = None
    base_period: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "series_id": self.series_id,
            "label": self.label,
            "unit": self.unit,
            "frequency": self.frequency,
            "dimensions": self.dimensions,
            "source_key": self.source_key,
            "unit_multiplier": self.unit_multiplier,
            "decimals": self.decimals,
            "base_period": self.base_period,
        }


@dataclass
class Observation:
    date: str
    series_id: str
    value: float | None
    raw_value: str | None = None
    dimensions: dict[str, dict[str, str]] = field(default_factory=dict)
    status: str | None = None
    comment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "date": self.date,
            "series_id": self.series_id,
            "value": self.value,
            "dimensions": self.dimensions,
            "status": self.status,
            "comment": self.comment,
        }
        if self.raw_value is not None:
            payload["raw_value"] = self.raw_value
        return payload

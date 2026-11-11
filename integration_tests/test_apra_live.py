from __future__ import annotations

import pytest

from ausecon_mcp.providers.apra import APRAProvider

pytestmark = pytest.mark.asyncio


async def test_apra_quarterly_performance_live_returns_key_stats() -> None:
    provider = APRAProvider()

    result = await provider.get_data(
        "ADI_QUARTERLY_PERFORMANCE",
        table_id="key_stats",
        last_n=1,
    )

    assert result["metadata"]["source"] == "apra"
    assert result["metadata"]["dataset_id"] == "ADI_QUARTERLY_PERFORMANCE"
    assert result["series"]
    assert result["observations"]


async def test_apra_property_exposures_live_returns_residential_property_table() -> None:
    provider = APRAProvider()

    result = await provider.get_data(
        "ADI_PROPERTY_EXPOSURES",
        table_id="tab_1b",
        last_n=1,
    )

    assert result["metadata"]["source"] == "apra"
    assert result["metadata"]["dataset_id"] == "ADI_PROPERTY_EXPOSURES"
    assert any(
        "total_credit_outstanding" in series["series_id"]
        or "total_credit_oustanding" in series["series_id"]
        for series in result["series"]
    )
    assert result["observations"]


# Every curated APRA concept, end to end through the semantic layer. Added after APRA
# renamed the PHI performance data sheet ("Database" -> "Database ") and the nightly
# suite kept passing for weeks because no APRA concept was exercised here.
_APRA_CONCEPT_MAX_AGE_DAYS = 200


def _apra_concepts() -> list[str]:
    from ausecon_mcp.catalogue.resolver import list_economic_concepts

    return sorted(entry["concept"] for entry in list_economic_concepts(source="apra"))


@pytest.mark.parametrize("concept", _apra_concepts())
async def test_live_every_apra_concept_resolves_with_recent_data(concept: str) -> None:
    from datetime import date, timedelta

    from ausecon_mcp.server import AuseconService

    result = await AuseconService().get_economic_series(concept, last_n=1)

    assert result["metadata"]["source"] == "apra"
    assert result["observations"], f"expected observations for {concept}"
    latest = date.fromisoformat(result["observations"][-1]["date"])
    assert date.today() - latest <= timedelta(days=_APRA_CONCEPT_MAX_AGE_DAYS), (
        f"{concept} latest observation {latest} is stale"
    )


# Matrix tables take their series ids from worksheet headings and indentation, so a
# formatting change at APRA can rename or merge series without any error. The checked-in
# list (scripts/refresh_apra_matrix_ids.py) turns that into a failed nightly run.
def _matrix_tables() -> list[tuple[str, str]]:
    from ausecon_mcp.catalogue.apra import APRA_CATALOGUE

    return [
        (publication_id, table_id)
        for publication_id, entry in APRA_CATALOGUE.items()
        for table_id, table_map in entry["tables"].items()
        if table_map["layout"] == "matrix"
    ]


@pytest.mark.parametrize(("publication_id", "table_id"), _matrix_tables())
async def test_live_apra_matrix_series_ids_are_unique_and_known(
    publication_id: str, table_id: str
) -> None:
    import json
    from pathlib import Path

    known = json.loads(
        (Path(__file__).parent / "apra_matrix_series_ids.json").read_text(encoding="utf-8")
    )[f"{publication_id}:{table_id}"]

    result = await APRAProvider().get_data(publication_id, table_id=table_id)

    keys = [(obs["series_id"], obs["date"]) for obs in result["observations"]]
    assert len(keys) == len(set(keys)), "a series returned two values for one date"
    numbered = [w for w in result["metadata"].get("warnings", []) if w.startswith("APRA table")]
    assert not numbered, numbered
    missing = sorted(set(known) - {series["series_id"] for series in result["series"]})
    assert not missing, f"series ids no longer produced (renamed or removed by APRA): {missing}"

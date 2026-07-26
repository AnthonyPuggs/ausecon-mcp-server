from __future__ import annotations

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.resolver import CURATED_SHORTCUTS, list_economic_concepts


def _abs_keys(dataflow_id: str) -> dict[str, str | None]:
    return {v["name"]: v["abs_key"] for v in ABS_CATALOGUE[dataflow_id]["variants"]}


def test_housing_price_concepts_registered() -> None:
    expected = {
        "mean_dwelling_price": "5.AUS.Q",
        "dwelling_stock_value": "1.AUS.Q",
        "residential_dwellings": "4.AUS.Q",
    }

    keys = _abs_keys("RES_DWELL_ST")

    for concept, abs_key in expected.items():
        assert CURATED_SHORTCUTS[concept] == {
            "source": "abs",
            "dataset_id": "RES_DWELL_ST",
            "variant": concept,
        }
        assert keys[concept] == abs_key


def test_housing_price_concepts_are_listed() -> None:
    names = {concept["concept"] for concept in list_economic_concepts()}

    assert {"mean_dwelling_price", "dwelling_stock_value", "residential_dwellings"} <= names


def test_total_value_of_dwellings_catalogue_entry_documents_unit_scaling() -> None:
    entry = ABS_CATALOGUE["RES_DWELL_ST"]

    assert entry["category"] == "housing_construction"
    # Values are scaled upstream; the description must warn agents about the scales.
    for fragment in ("$ millions", "$ thousands", "thousands"):
        assert fragment in entry["description"]

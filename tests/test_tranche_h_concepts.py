from __future__ import annotations

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.resolver import CURATED_SHORTCUTS, list_economic_concepts


def _abs_keys(dataflow_id: str) -> dict[str, str | None]:
    return {v["name"]: v["abs_key"] for v in ABS_CATALOGUE[dataflow_id]["variants"]}


def test_national_accounts_concepts_registered() -> None:
    expected = {
        "household_saving_ratio": ("ANA_AGG", "M7.HSR.20.AUS.Q"),
        "real_net_national_disposable_income": ("ANA_AGG", "M1.NNDI.20.AUS.Q"),
        "gdp_deflator": ("ANA_EXP", "DCH.GPM.SSS.20.AUS.Q"),
        "government_consumption": ("ANA_EXP", "VCH.FCE.GGS.20.AUS.Q"),
        "exports": ("ANA_EXP", "VCH.XGS.SSS.20.AUS.Q"),
        "imports": ("ANA_EXP", "VCH.MGS.SSS.20.AUS.Q"),
    }

    agg_keys = _abs_keys("ANA_AGG")
    exp_keys = _abs_keys("ANA_EXP")
    keys_by_dataflow = {"ANA_AGG": agg_keys, "ANA_EXP": exp_keys}

    for concept, (dataflow, abs_key) in expected.items():
        assert CURATED_SHORTCUTS[concept] == {
            "source": "abs",
            "dataset_id": dataflow,
            "variant": concept,
        }
        assert keys_by_dataflow[dataflow][concept] == abs_key

    concepts = {row["concept"] for row in list_economic_concepts()}
    assert set(expected) <= concepts

from fastmcp import Client

from ausecon_mcp.server import build_server


async def _get_prompt_text(client: Client, name: str, arguments: dict | None = None) -> str:
    result = await client.get_prompt(name, arguments or {})
    assert result.messages, f"no messages returned for prompt {name}"
    content = result.messages[0].content
    text = getattr(content, "text", content)
    assert isinstance(text, str) and text.strip()
    return text


async def test_prompts_are_listed() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        prompts = await client.list_prompts()

    names = {prompt.name for prompt in prompts}
    assert {
        "summarise_latest_inflation",
        "compare_cash_rate_to_cpi",
        "macro_snapshot",
        "living_costs_vs_cpi",
        "construction_pipeline",
        "labour_slack_snapshot",
        "yield_curve_snapshot",
        "discover_dataset",
    } <= names


async def test_summarise_latest_inflation_references_required_concepts() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "summarise_latest_inflation", {"months": 24})

    assert "24" in text
    assert "headline_cpi" in text
    assert "trimmed_mean_inflation" in text


async def test_compare_cash_rate_to_cpi_embeds_range() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(
            client,
            "compare_cash_rate_to_cpi",
            {"start": "2020-01-01", "end": "2024-01-01"},
        )

    assert "2020-01-01" in text
    assert "2024-01-01" in text
    assert "cash_rate_target" in text
    assert "headline_cpi" in text


async def test_macro_snapshot_lists_all_indicators() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "macro_snapshot", {})

    for concept in ("cash_rate_target", "headline_cpi", "trimmed_mean_inflation", "gdp_growth"):
        assert concept in text


async def test_living_costs_vs_cpi_references_lci_and_cpi() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "living_costs_vs_cpi", {"start": "2021-Q1"})

    assert "SLCI" in text
    assert "headline_cpi" in text
    assert "2021-Q1" in text


async def test_construction_pipeline_references_all_series() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "construction_pipeline", {"last_n": 12})

    for dataflow in ("CWD", "EWD", "BUILDING_ACTIVITY"):
        assert dataflow in text
    assert "12" in text


async def test_labour_slack_snapshot_references_both_rates() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "labour_slack_snapshot", {"last_n": 24})

    assert "unemployment_rate" in text
    assert "underemployment_rate" in text
    assert "24" in text


async def test_yield_curve_snapshot_references_both_tenors() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "yield_curve_snapshot", {"last_n": 90})

    assert "government_bond_yield_3y" in text
    assert "government_bond_yield_10y" in text
    assert "90" in text


async def test_discover_dataset_embeds_topic() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "discover_dataset", {"topic": "labour market"})

    assert "labour market" in text
    assert "search_datasets" in text
    assert "list_rba_tables" in text

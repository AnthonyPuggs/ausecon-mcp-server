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


async def test_discover_dataset_embeds_topic() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "discover_dataset", {"topic": "labour market"})

    assert "labour market" in text
    assert "search_datasets" in text
    assert "list_rba_tables" in text

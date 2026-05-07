import ast
import re

from fastmcp import Client

from ausecon_mcp.server import build_server

_TOOL_CALL_RE = re.compile(r"`([a-z_]+)\((.*?)\)`")


async def _get_prompt_text(client: Client, name: str, arguments: dict | None = None) -> str:
    result = await client.get_prompt(name, arguments or {})
    assert result.messages, f"no messages returned for prompt {name}"
    content = result.messages[0].content
    text = getattr(content, "text", content)
    assert isinstance(text, str) and text.strip()
    return text


def _tool_calls(text: str) -> list[tuple[str, dict]]:
    calls = []
    for name, args_text in _TOOL_CALL_RE.findall(text):
        parsed = ast.parse(f"_f({args_text})", mode="eval")
        call = parsed.body
        assert isinstance(call, ast.Call)
        assert not call.args
        kwargs = {}
        for keyword in call.keywords:
            assert keyword.arg is not None
            kwargs[keyword.arg] = ast.literal_eval(keyword.value)
        calls.append((name, kwargs))
    return calls


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
    assert "last_n=8" in text


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
    assert 'concept="cash_rate_target", start="2020-01-01", end="2024-01-01"' in text
    assert 'concept="headline_cpi", start="2020-01-01", end="2024-01-01"' in text
    assert "cash_rate_target" in text
    assert "headline_cpi" in text


async def test_macro_snapshot_lists_all_indicators_and_passes_as_of_bounds() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "macro_snapshot", {"as_of": "2024-06-30"})

    for concept in ("cash_rate_target", "headline_cpi", "trimmed_mean_inflation", "gdp_growth"):
        assert concept in text
    assert 'concept="cash_rate_target", end="2024-06-30"' in text
    assert 'concept="headline_cpi", end="2024-06-30"' in text
    assert 'concept="trimmed_mean_inflation", end="2024-06-30"' in text
    assert 'concept="gdp_growth", end="2024-06-30"' in text


async def test_living_costs_vs_cpi_references_lci_and_cpi() -> None:
    mcp = build_server()

    async with Client(mcp) as client:
        text = await _get_prompt_text(client, "living_costs_vs_cpi", {"start": "2021-Q1"})

    assert "SLCI" in text
    assert "headline_cpi" in text
    assert 'start_period="2021-Q1"' in text
    assert 'concept="headline_cpi", start="2021-Q1"' in text
    assert "last_n=8" in text


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
    assert "list_economic_concepts" in text
    assert "list_catalogue" in text
    assert "list_rba_tables" not in text
    assert '"labour"' not in text
    assert '"output_labour"' in text


async def test_prompt_tool_call_snippets_match_registered_tool_contracts() -> None:
    prompt_examples = {
        "summarise_latest_inflation": {"months": 24},
        "compare_cash_rate_to_cpi": {"start": "2020-01-01", "end": "2024-01-01"},
        "macro_snapshot": {"as_of": "2024-06-30"},
        "living_costs_vs_cpi": {"start": "2021-Q1"},
        "construction_pipeline": {"last_n": 12},
        "labour_slack_snapshot": {"last_n": 24},
        "yield_curve_snapshot": {"last_n": 90},
        "discover_dataset": {"topic": "labour market"},
    }
    mcp = build_server()

    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        prompt_texts = {
            name: await _get_prompt_text(client, name, arguments)
            for name, arguments in prompt_examples.items()
        }

    for prompt_name, text in prompt_texts.items():
        calls = _tool_calls(text)
        assert calls, f"{prompt_name} did not expose executable tool call snippets"
        for tool_name, kwargs in calls:
            assert tool_name in tools
            properties = tools[tool_name].inputSchema["properties"]
            assert set(kwargs) <= set(properties)
            if "last_n" in kwargs:
                assert isinstance(kwargs["last_n"], int)
                assert kwargs["last_n"] > 0

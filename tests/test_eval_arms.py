from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals import arms  # noqa: E402
from evals.arms import (  # noqa: E402
    ARMS,
    SUBMIT_ANSWER_TOOL,
    WEB_SEARCH_TOOL,
    AuseconToolbox,
    build_arm_tools,
)


def test_submit_answer_tool_is_strict_and_complete() -> None:
    assert SUBMIT_ANSWER_TOOL["name"] == "submit_answer"
    assert SUBMIT_ANSWER_TOOL["strict"] is True
    schema = SUBMIT_ANSWER_TOOL["input_schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"value", "unit", "period", "not_found"}


async def test_ausecon_toolbox_exposes_mcp_tools() -> None:
    async with AuseconToolbox() as toolbox:
        tools = await toolbox.list_anthropic_tools()
    names = {tool["name"] for tool in tools}
    assert "get_economic_series" in names
    assert "get_derived_series" in names
    assert "search_datasets" in names
    for tool in tools:
        assert tool["description"]
        assert tool["input_schema"]["type"] == "object"


async def test_build_arm_tools_shapes() -> None:
    bare = await build_arm_tools("bare", None)
    assert bare == [SUBMIT_ANSWER_TOOL]

    web = await build_arm_tools("web", None)
    assert WEB_SEARCH_TOOL in web and SUBMIT_ANSWER_TOOL in web

    async with AuseconToolbox() as toolbox:
        ausecon = await build_arm_tools("ausecon", toolbox)
    names = [tool["name"] for tool in ausecon]
    assert "submit_answer" in names and "get_economic_series" in names
    assert "web_search" not in names


def test_arms_constant() -> None:
    assert ARMS == ("bare", "web", "ausecon")


async def test_dispatch_returns_json_for_structured_content() -> None:
    async with AuseconToolbox() as toolbox:
        result = await toolbox.dispatch("search_datasets", {"query": "cpi"})
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed


async def test_dispatch_falls_back_to_text_content_when_no_structured_content() -> None:
    class _FakeBlock:
        def __init__(self, text: str) -> None:
            self.text = text

    class _FakeResult:
        structured_content = None
        content = [_FakeBlock("hello world")]

    async def _fake_call_tool(name: str, arguments: dict) -> _FakeResult:
        return _FakeResult()

    async with AuseconToolbox() as toolbox:
        toolbox._client.call_tool = _fake_call_tool
        result = await toolbox.dispatch("whatever", {})
    assert result == "hello world"


async def test_dispatch_truncates_long_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(arms, "MAX_TOOL_RESULT_CHARS", 20)
    async with AuseconToolbox() as toolbox:
        result = await toolbox.dispatch("search_datasets", {"query": "cpi"})
    assert result.endswith("\n...[truncated]")
    assert len(result) == 20 + len("\n...[truncated]")


async def test_build_arm_tools_ausecon_without_toolbox_raises() -> None:
    with pytest.raises(ValueError, match="ausecon arm requires"):
        await build_arm_tools("ausecon", None)


async def test_build_arm_tools_unknown_arm_raises() -> None:
    with pytest.raises(ValueError, match="unknown arm"):
        await build_arm_tools("bogus", None)


async def test_aexit_closes_service_even_when_client_aexit_raises() -> None:
    class _FakeService:
        def __init__(self) -> None:
            self.aclose_calls = 0

        async def aclose(self) -> None:
            self.aclose_calls += 1

    class _RaisingClientStub:
        async def __aenter__(self) -> _RaisingClientStub:
            return self

        async def __aexit__(self, *exc_info: object) -> None:
            raise RuntimeError("client cleanup failed")

    fake_service = _FakeService()
    toolbox = AuseconToolbox(service=fake_service)  # type: ignore[arg-type]
    toolbox._client = _RaisingClientStub()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="client cleanup failed"):
        async with toolbox:
            pass

    assert fake_service.aclose_calls == 1

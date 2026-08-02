from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.arms import SUBMIT_ANSWER_TOOL  # noqa: E402
from evals.loop import run_cell  # noqa: E402


def _block(type_: str, **kwargs):
    return SimpleNamespace(type=type_, **kwargs)


def _response(blocks, stop_reason="tool_use", in_tok=100, out_tok=50):
    return SimpleNamespace(
        content=blocks,
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=in_tok, output_tokens=out_tok),
    )


class StubClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    @property
    def messages(self):
        return self

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


ANSWER = {"value": 4.35, "unit": "per cent", "period": "2026-Q1", "not_found": False}


async def test_immediate_submit_answer() -> None:
    client = StubClient(
        [_response([_block("tool_use", name="submit_answer", id="t1", input=ANSWER)])]
    )
    result = await run_cell(client, "What is the cash rate?", [SUBMIT_ANSWER_TOOL], None)
    assert result.submitted == ANSWER
    assert result.error is None
    assert result.input_tokens == 100 and result.output_tokens == 50


async def test_custom_tool_dispatch_then_answer() -> None:
    calls = []

    async def dispatch(name, arguments):
        calls.append((name, arguments))
        return '{"observations": []}'

    client = StubClient(
        [
            _response(
                [_block("tool_use", name="get_economic_series", id="t1", input={"concept": "x"})]
            ),
            _response([_block("tool_use", name="submit_answer", id="t2", input=ANSWER)]),
        ]
    )
    tools = [
        {"name": "get_economic_series", "description": "d", "input_schema": {}},
        SUBMIT_ANSWER_TOOL,
    ]
    result = await run_cell(client, "Q?", tools, dispatch)
    assert result.submitted == ANSWER
    assert calls == [("get_economic_series", {"concept": "x"})]
    assert result.tool_calls == 2
    # second request must carry the tool_result back
    second = client.requests[1]
    tool_results = [b for b in second["messages"][-1]["content"] if b.get("type") == "tool_result"]
    assert tool_results and tool_results[0]["tool_use_id"] == "t1"


async def test_pause_turn_resumes() -> None:
    client = StubClient(
        [
            _response(
                [_block("server_tool_use", name="web_search", id="s1", input={})],
                stop_reason="pause_turn",
            ),
            _response([_block("tool_use", name="submit_answer", id="t2", input=ANSWER)]),
        ]
    )
    result = await run_cell(client, "Q?", [SUBMIT_ANSWER_TOOL], None)
    assert result.submitted == ANSWER
    # Verify pause_turn response was echoed in second request
    second = client.requests[1]
    assert second["messages"][-1]["role"] == "assistant"


async def test_max_tokens_stop_reason_records_truncation_immediately() -> None:
    # A max_tokens stop must be recorded as its own error rather than falling through
    # to the "no tool_uses -> nudge" path, since a truncated response often has no
    # complete content blocks to nudge from.
    client = StubClient([_response([_block("text", text="partial...")], stop_reason="max_tokens")])
    result = await run_cell(client, "Q?", [SUBMIT_ANSWER_TOOL], None)
    assert result.submitted is None
    assert result.error == "max_tokens_truncated"
    # Must not have attempted a second (nudge) request.
    assert len(client.requests) == 1


async def test_iteration_cap_yields_no_answer() -> None:
    responses = [_response([_block("text", text="hmm")], stop_reason="end_turn") for _ in range(12)]
    client = StubClient(responses)
    result = await run_cell(client, "Q?", [SUBMIT_ANSWER_TOOL], None)
    assert result.submitted is None
    assert result.error == "no_submit_answer"


async def test_api_error_is_captured_not_raised() -> None:
    class ExplodingClient:
        @property
        def messages(self):
            return self

        async def create(self, **kwargs):
            raise RuntimeError("boom")

    result = await run_cell(ExplodingClient(), "Q?", [SUBMIT_ANSWER_TOOL], None)
    assert result.submitted is None
    assert "RuntimeError" in (result.error or "")


async def test_dispatch_raises_error_sent_back_to_model() -> None:
    async def dispatch_that_raises(name, arguments):
        raise ValueError("invalid argument")

    client = StubClient(
        [
            _response([_block("tool_use", name="get_economic_series", id="t1", input={})]),
            _response([_block("tool_use", name="submit_answer", id="t2", input=ANSWER)]),
        ]
    )
    tools = [
        {"name": "get_economic_series", "description": "d", "input_schema": {}},
        SUBMIT_ANSWER_TOOL,
    ]
    result = await run_cell(client, "Q?", tools, dispatch_that_raises)
    assert result.submitted == ANSWER
    # Check that error was sent back to model
    second = client.requests[1]
    tool_results = [b for b in second["messages"][-1]["content"] if b.get("type") == "tool_result"]
    assert tool_results and "ValueError" in tool_results[0]["content"]


async def test_dispatch_none_unavailable_message_sent_back() -> None:
    client = StubClient(
        [
            _response([_block("tool_use", name="get_economic_series", id="t1", input={})]),
            _response([_block("tool_use", name="submit_answer", id="t2", input=ANSWER)]),
        ]
    )
    tools = [
        {"name": "get_economic_series", "description": "d", "input_schema": {}},
        SUBMIT_ANSWER_TOOL,
    ]
    result = await run_cell(client, "Q?", tools, None)
    assert result.submitted == ANSWER
    # Check that unavailable message was sent back
    second = client.requests[1]
    tool_results = [b for b in second["messages"][-1]["content"] if b.get("type") == "tool_result"]
    assert tool_results and "is not available" in tool_results[0]["content"]


async def test_text_only_response_nudges_submit_answer() -> None:
    client = StubClient(
        [
            _response([_block("text", text="The cash rate is 4.35%")], stop_reason="end_turn"),
            _response([_block("tool_use", name="submit_answer", id="t2", input=ANSWER)]),
        ]
    )
    result = await run_cell(client, "Q?", [SUBMIT_ANSWER_TOOL], None)
    assert result.submitted == ANSWER
    # Check that assistant's response was preserved before nudge. response.content is
    # passed through verbatim (SDK-native pass-through), so this is attribute access on
    # the stub's SimpleNamespace blocks, not dict access.
    second = client.requests[1]
    assert second["messages"][-2]["role"] == "assistant"
    assert second["messages"][-2]["content"][0].type == "text"
    assert second["messages"][-1]["role"] == "user"
    assert second["messages"][-1]["content"] == "Call submit_answer now."

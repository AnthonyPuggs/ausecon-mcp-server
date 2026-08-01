from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

MODEL = "claude-sonnet-5"
MAX_ITERATIONS = 10
MAX_TOKENS = 4096

SYSTEM_PROMPT = (
    "You are answering a factual question about the Australian economy. "
    "Use the tools available to you to find the answer when your own knowledge "
    "may be stale or insufficient. You MUST finish by calling the submit_answer "
    "tool exactly once with your final numeric answer, its unit, and the period "
    "it refers to (formats like '2026-Q1', '2026-05', or '2026-05-05'). "
    "If you cannot determine the answer, call submit_answer with not_found=true. "
    "Never answer in plain text."
)


@dataclass
class CellResult:
    submitted: dict | None
    tool_calls: int
    input_tokens: int
    output_tokens: int
    latency_s: float
    error: str | None


async def run_cell(client, question_text: str, tools: list[dict], dispatch) -> CellResult:
    messages: list[dict[str, Any]] = [{"role": "user", "content": question_text}]
    tool_calls = 0
    input_tokens = 0
    output_tokens = 0
    started = time.monotonic()

    try:
        for _ in range(MAX_ITERATIONS):
            response = await client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )
            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens

            if response.stop_reason == "pause_turn":
                messages.append(
                    {"role": "assistant", "content": _serialise_content(response.content)}
                )
                continue

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                messages.append({"role": "user", "content": "Call submit_answer now."})
                continue

            tool_calls += len(tool_uses)
            for block in tool_uses:
                if block.name == "submit_answer":
                    return CellResult(
                        submitted=dict(block.input),
                        tool_calls=tool_calls,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_s=time.monotonic() - started,
                        error=None,
                    )

            messages.append({"role": "assistant", "content": _serialise_content(response.content)})
            results = []
            for block in tool_uses:
                if dispatch is None:
                    text = f"Tool {block.name} is not available."
                else:
                    try:
                        text = await dispatch(block.name, dict(block.input))
                    except Exception as exc:  # noqa: BLE001 - tool errors go back to the model
                        text = f"Tool error: {type(exc).__name__}: {exc}"
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": text})
            messages.append({"role": "user", "content": results})

        error = "no_submit_answer"
    except Exception as exc:  # noqa: BLE001 - cell failures must never kill the run
        error = f"{type(exc).__name__}: {exc}"

    return CellResult(
        submitted=None,
        tool_calls=tool_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_s=time.monotonic() - started,
        error=error,
    )


def _serialise_content(content: list[Any]) -> list[dict[str, Any]]:
    blocks = []
    for block in content:
        if block.type == "text":
            blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            blocks.append(
                {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
            )
        else:
            dump = getattr(block, "model_dump", None)
            if dump is not None:
                blocks.append(dump())
    return blocks

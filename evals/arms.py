from __future__ import annotations

import json
from typing import Any

from fastmcp import Client

from ausecon_mcp.server import AuseconService, build_server

ARMS = ("bare", "web", "ausecon")
MAX_TOOL_RESULT_CHARS = 40_000

SUBMIT_ANSWER_TOOL: dict[str, Any] = {
    "name": "submit_answer",
    "description": (
        "Submit your final answer to the question. You MUST call this exactly once "
        "as your final action. If you cannot determine the answer, set not_found to "
        "true and value to 0."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "The numeric answer."},
            "unit": {"type": "string", "description": "Unit of the value, e.g. 'per cent'."},
            "period": {
                "type": "string",
                "description": (
                    "Period the value refers to, e.g. '2026-Q1', '2026-05', '2026-05-05'."
                ),
            },
            "not_found": {
                "type": "boolean",
                "description": "True if you cannot determine the answer.",
            },
        },
        "required": ["value", "unit", "period", "not_found"],
        "additionalProperties": False,
    },
}

WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "web_search_20260209",
    "name": "web_search",
    "max_uses": 5,
}


class AuseconToolbox:
    """In-memory MCP client over the local server; the 'ausecon' arm's tool source."""

    def __init__(self, service: AuseconService | None = None) -> None:
        self._service = service or AuseconService()
        self._client = Client(build_server(self._service))

    async def __aenter__(self) -> AuseconToolbox:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.__aexit__(*exc_info)
        await self._service.aclose()

    async def list_anthropic_tools(self) -> list[dict[str, Any]]:
        tools = await self._client.list_tools()
        converted = []
        for tool in tools:
            converted.append(
                {
                    "name": tool.name,
                    "description": tool.description or tool.name,
                    "input_schema": tool.inputSchema,
                }
            )
        return converted

    async def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self._client.call_tool(name, arguments)
        if result.structured_content is not None:
            text = json.dumps(result.structured_content)
        else:
            text = "\n".join(block.text for block in result.content if getattr(block, "text", None))
        if len(text) > MAX_TOOL_RESULT_CHARS:
            text = text[:MAX_TOOL_RESULT_CHARS] + "\n...[truncated]"
        return text


async def build_arm_tools(arm: str, toolbox: AuseconToolbox | None) -> list[dict[str, Any]]:
    if arm == "bare":
        return [SUBMIT_ANSWER_TOOL]
    if arm == "web":
        return [WEB_SEARCH_TOOL, SUBMIT_ANSWER_TOOL]
    if arm == "ausecon":
        if toolbox is None:
            raise ValueError("ausecon arm requires an AuseconToolbox")
        return [*await toolbox.list_anthropic_tools(), SUBMIT_ANSWER_TOOL]
    raise ValueError(f"unknown arm {arm!r}")

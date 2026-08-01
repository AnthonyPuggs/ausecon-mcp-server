from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evals" / "results" / "latest.json"
OUTPUT = ROOT / "docs-site" / "src" / "content" / "docs" / "user-guide" / "evaluation.md"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARM_LABELS = {
    "bare": "Claude alone",
    "web": "Claude + web search",
    "ausecon": "Claude + ausecon MCP",
}
ARM_ORDER = ("bare", "web", "ausecon")


def render(document: dict[str, Any]) -> str:
    run = document["run"]
    aggregates = document["aggregates"]
    lines = [
        "---",
        "title: Evaluation",
        "description: Measured impact of the ausecon MCP server on Claude's "
        "Australian-economics answers.",
        "---",
        "",
        f"Benchmark run {run['timestamp']} on `{run['model']}`, package version "
        f"{run['package_version']}, {run['question_count']} questions, three arms. "
        f"Estimated API cost: ${run['est_cost_usd']}.",
        "",
        "## Results",
        "",
        "| Arm | Accuracy | Freshness (live questions) | Abstained | Errors |",
        "| --- | --- | --- | --- | --- |",
    ]
    for arm in ARM_ORDER:
        if arm not in aggregates:
            continue
        agg = aggregates[arm]
        lines.append(
            f"| {ARM_LABELS[arm]} | {agg['accuracy']:.0%} | {agg['freshness']:.0%} "
            f"| {agg['abstain_rate']:.0%} | {agg['error_count']} |"
        )
    lines += [
        "",
        "| Arm | Avg tool calls | Avg latency (s) | Tokens (in / out) |",
        "| --- | --- | --- | --- |",
    ]
    for arm in ARM_ORDER:
        if arm not in aggregates:
            continue
        agg = aggregates[arm]
        lines.append(
            f"| {ARM_LABELS[arm]} | {agg['avg_tool_calls']:.1f} | {agg['avg_latency_s']} "
            f"| {agg['input_tokens']:,} / {agg['output_tokens']:,} |"
        )
    lines += [
        "",
        "## Methodology",
        "",
        "Every arm answers through a strict-schema `submit_answer` tool; grading is",
        "arithmetic (answer within a per-question tolerance), with no LLM judge.",
        "Accuracy is measured over graded cells (API-error cells are excluded and",
        "reported separately). Freshness asks whether the answer refers to the",
        "latest published period, over live questions only. The ausecon arm calls",
        "the MCP tools in-process against the exact release version; the web arm",
        "uses Anthropic's server-side web search; the bare arm has no tools.",
        "",
        "Ground truth for live questions is resolved from the server itself at run",
        "time — circular in isolation, so two mitigations apply: nightly golden-value",
        "integration tests independently verify the server against ABS, RBA, and",
        "APRA, and every resolved value is recorded in the committed results file",
        "([evals/results](https://github.com/AnthonyPuggs/ausecon-mcp-server/tree/main/evals/results))",
        "for direct spot-checking against the primary sources.",
        "",
        "Costs are estimated at standard list rates ($3/$15 per MTok) and exclude",
        "server-side web-search fees, so the reported figure may differ from billed",
        "spend.",
        "",
        "## Limitations",
        "",
        "- Single run per release; no variance bars.",
        "- Numeric-answer questions only; no open-ended analysis tasks.",
        "- The question set is public, so future models could train on it.",
        "- Live ground truth is self-resolved (mitigated as described above).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify the Starlight evaluation results page."
    )
    parser.add_argument("--check", action="store_true", help="Fail if the generated page is stale.")
    args = parser.parse_args()

    if not RESULTS.exists():
        print(
            f"{RESULTS.relative_to(ROOT)} does not exist; no eval results yet. "
            "Run the eval harness first."
        )
        return 1

    document = json.loads(RESULTS.read_text(encoding="utf-8"))
    rendered = render(document)

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(
                f"{OUTPUT.relative_to(ROOT)} is stale. "
                "Run `uv run python scripts/update_docs_eval.py`."
            )
            return 1
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)}. If the sidebar doesn't already list it, add "
        "a { label: 'Evaluation', slug: 'user-guide/evaluation' } entry to the "
        "user-guide section of docs-site/astro.config.mjs — Starlight won't surface "
        "the page until it's in the sidebar."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

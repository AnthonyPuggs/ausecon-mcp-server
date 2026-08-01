"""Manual eval runner. Requires ANTHROPIC_API_KEY. Usage:

uv run --group evals python -m evals.run_eval --dry-run
uv run --group evals python -m evals.run_eval --arms bare ausecon --limit 5
uv run --group evals python -m evals.run_eval
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.arms import ARMS, AuseconToolbox, build_arm_tools  # noqa: E402
from evals.grading import grade  # noqa: E402
from evals.loop import MODEL, CellResult, run_cell  # noqa: E402
from evals.manifest import load_questions  # noqa: E402
from evals.resolve import resolve_ground_truth  # noqa: E402
from evals.results import build_cell_record, build_results_document, estimate_cost_usd  # noqa: E402

RESULTS_DIR = ROOT / "evals" / "results"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the three-arm ausecon benchmark.")
    parser.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    parser.add_argument("--limit", type=int, default=None, help="Only the first N questions.")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--max-cost-usd",
        type=float,
        default=15.0,
        help=(
            "Abort remaining cells once estimated spend exceeds this ceiling. Checked "
            "after each completed cell, not before it starts, so with --concurrency N "
            "the run can overshoot the ceiling by up to N-1 in-flight cells' cost."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve ground truth and print the grid; no API calls.",
    )
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    questions = load_questions()
    if args.limit:
        questions = questions[: args.limit]

    from ausecon_mcp.server import AuseconService, resolve_version

    truth_service = AuseconService()
    truths = {}
    try:
        for question in questions:
            truths[question.id] = await resolve_ground_truth(truth_service, question)
            print(f"truth {question.id}: {truths[question.id]}")
    finally:
        await truth_service.aclose()

    if args.dry_run:
        print(
            f"\nDry run: {len(questions)} questions x {len(args.arms)} arms "
            f"= {len(questions) * len(args.arms)} cells. No API calls made."
        )
        return 0

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic()
    semaphore = asyncio.Semaphore(args.concurrency)
    spent = {"input": 0, "output": 0}
    budget_blown = asyncio.Event()
    cell_records = []

    async with AuseconToolbox() as toolbox:
        arm_tools = {arm: await build_arm_tools(arm, toolbox) for arm in args.arms}

        async def run_one(question, arm: str) -> None:
            async with semaphore:
                if budget_blown.is_set():
                    cell = CellResult(None, 0, 0, 0, 0.0, "skipped_budget")
                else:
                    dispatch = toolbox.dispatch if arm == "ausecon" else None
                    cell = await run_cell(client, question.question, arm_tools[arm], dispatch)
                    spent["input"] += cell.input_tokens
                    spent["output"] += cell.output_tokens
                    if estimate_cost_usd(spent["input"], spent["output"]) > args.max_cost_usd:
                        budget_blown.set()

            # A failure past this point (grading, record-building, a missing truth) must not
            # abort the whole gather()/paid run — record a fallback cell and move on.
            try:
                verdict = grade(cell.submitted, truths[question.id], question.tolerance)
                record = build_cell_record(question, arm, truths[question.id], cell, verdict)
                outcome = verdict.outcome
                error = cell.error
            except Exception as exc:  # noqa: BLE001 - must never abort the run
                record = {
                    "question_id": question.id,
                    "arm": arm,
                    "answer_type": question.answer_type,
                    "outcome": "no_answer",
                    "value_ok": False,
                    "fresh": False,
                    "unit_flag": False,
                    "submitted": None,
                    "expected_value": None,
                    "expected_period": None,
                    "tool_calls": cell.tool_calls,
                    "input_tokens": cell.input_tokens,
                    "output_tokens": cell.output_tokens,
                    "latency_s": round(cell.latency_s, 2),
                    "error": f"record_failure:{type(exc).__name__}: {exc}",
                }
                outcome = record["outcome"]
                error = record["error"]

            cell_records.append(record)
            print(f"{question.id} [{arm}]: {outcome}" + (f" ({error})" if error else ""))

        await asyncio.gather(*(run_one(q, arm) for q in questions for arm in args.arms))

    timestamp = datetime.now(timezone.utc)
    document = build_results_document(
        model=MODEL,
        package_version=resolve_version(),
        timestamp_iso=timestamp.isoformat(timespec="seconds"),
        ground_truth={
            qid: {"value": t.value, "period": t.period, "unit": t.unit} for qid, t in truths.items()
        },
        cell_records=sorted(cell_records, key=lambda c: (c["question_id"], c["arm"])),
    )

    # A pilot run (--limit and/or a subset of --arms) is not representative of the
    # published benchmark, so it must never overwrite latest.json — only a full run
    # (all arms, no --limit) does. The stamped file is always written, and carries a
    # time component so pilot and full runs on the same day don't collide.
    is_full_run = args.limit is None and set(args.arms) == set(ARMS)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamped = RESULTS_DIR / (f"{timestamp.strftime('%Y-%m-%dT%H%M%S')}-v{resolve_version()}.json")
    stamped.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {stamped}")
    if is_full_run:
        (RESULTS_DIR / "latest.json").write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
    else:
        print("partial run — latest.json not updated")
    for arm, agg in document["aggregates"].items():
        print(
            f"{arm:8s} accuracy={agg['accuracy']:.0%} freshness={agg['freshness']:.0%} "
            f"abstain={agg['abstain_rate']:.0%} errors={agg['error_count']}"
        )
    print(f"Estimated cost: ${document['run']['est_cost_usd']}")
    if budget_blown.is_set():
        print("WARNING: cost ceiling hit; remaining cells recorded as skipped_budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

from __future__ import annotations

from typing import Any

PRICE_INPUT_PER_MTOK = 3.0
PRICE_OUTPUT_PER_MTOK = 15.0


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * PRICE_INPUT_PER_MTOK / 1_000_000
        + output_tokens * PRICE_OUTPUT_PER_MTOK / 1_000_000
    )


def build_cell_record(question, arm: str, truth, cell, verdict) -> dict[str, Any]:
    return {
        "question_id": question.id,
        "arm": arm,
        "answer_type": question.answer_type,
        "outcome": verdict.outcome,
        "value_ok": verdict.value_ok,
        "fresh": verdict.fresh,
        "unit_flag": verdict.unit_flag,
        "submitted": cell.submitted,
        "expected_value": truth.value,
        "expected_period": truth.period,
        "tool_calls": cell.tool_calls,
        "input_tokens": cell.input_tokens,
        "output_tokens": cell.output_tokens,
        "latency_s": round(cell.latency_s, 2),
        "error": cell.error,
    }


def aggregate(cell_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    arms = sorted({cell["arm"] for cell in cell_records})
    out: dict[str, dict[str, Any]] = {}
    for arm in arms:
        cells = [c for c in cell_records if c["arm"] == arm]
        errors = [c for c in cells if c["error"] and c["outcome"] == "no_answer"]
        graded = [c for c in cells if c not in errors]
        correct = [c for c in graded if c["outcome"] == "correct"]
        abstained = [c for c in graded if c["outcome"] == "abstain"]
        live_graded = [c for c in graded if c["answer_type"] == "live"]
        live_fresh = [c for c in live_graded if c["fresh"]]
        out[arm] = {
            "cells": len(cells),
            "accuracy": len(correct) / len(graded) if graded else 0.0,
            "freshness": len(live_fresh) / len(live_graded) if live_graded else 0.0,
            "abstain_rate": len(abstained) / len(graded) if graded else 0.0,
            "error_count": len(errors),
            "avg_tool_calls": (sum(c["tool_calls"] for c in cells) / len(cells) if cells else 0.0),
            "avg_latency_s": (
                round(sum(c["latency_s"] for c in cells) / len(cells), 2) if cells else 0.0
            ),
            "input_tokens": sum(c["input_tokens"] for c in cells),
            "output_tokens": sum(c["output_tokens"] for c in cells),
        }
    return out


def build_results_document(
    model: str,
    package_version: str,
    timestamp_iso: str,
    ground_truth: dict[str, dict[str, Any]],
    cell_records: list[dict[str, Any]],
) -> dict[str, Any]:
    total_in = sum(c["input_tokens"] for c in cell_records)
    total_out = sum(c["output_tokens"] for c in cell_records)
    return {
        "run": {
            "model": model,
            "package_version": package_version,
            "timestamp": timestamp_iso,
            "question_count": len(ground_truth),
            "input_tokens": total_in,
            "output_tokens": total_out,
            "est_cost_usd": round(estimate_cost_usd(total_in, total_out), 2),
        },
        "ground_truth": ground_truth,
        "cells": cell_records,
        "aggregates": aggregate(cell_records),
    }

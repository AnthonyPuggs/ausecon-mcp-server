---
title: Evaluation Harness
description: How to run the three-arm benchmark that measures the server's impact on model answers.
---

The repository ships a manual benchmark under `evals/` that measures whether the server actually
improves a model's answers to Australian-economics questions, rather than asserting it. It runs the
same question set through three arms and compares them:

- **bare** — the model alone, no tools.
- **web** — the model with Anthropic server-side web search.
- **ausecon** — the model with the full ausecon MCP tool surface, served in-process from the local
  working copy.

The question set (`evals/questions.yaml`) holds 52 questions: 20 **pinned** questions with fixed
historical answers (past cash-rate decisions, historical CPI index numbers, past ADI totals) and 32
**live** questions whose ground truth is re-resolved against ABS, RBA, and APRA at run time, so the
benchmark stays current without manual re-answering.

In every arm the model must call a strict `submit_answer` tool with a numeric value, unit, and
period. Grading is deterministic (`evals/grading.py`): the value must fall within the question's
tolerance, the period must match the ground-truth period for the answer to count as fresh, and unit
mismatches are flagged separately. An explicit `not_found` submission is recorded as an abstention,
not an error.

## Running

Only the model-under-test calls are paid; ground-truth resolution and grading are free. A full
three-arm run needs `ANTHROPIC_API_KEY` and costs roughly $10–15 at Sonnet pricing.

```bash
# Free: resolve ground truth for all questions and print the grid; no API calls.
env UV_CACHE_DIR=.uv-cache uv run --group evals python -m evals.run_eval --dry-run

# Cheap pilot: first 5 questions, two arms.
env UV_CACHE_DIR=.uv-cache uv run --group evals python -m evals.run_eval --arms bare ausecon --limit 5

# Full three-arm run.
env UV_CACHE_DIR=.uv-cache uv run --group evals python -m evals.run_eval
```

Always dry-run first: it verifies every question still resolves against the live sources before any
money is spent. Follow with a pilot before the first full run on a changed harness.

Cost is bounded by `--max-cost-usd` (default 15). The ceiling is checked after each completed cell,
so with `--concurrency N` a run can overshoot by up to N−1 in-flight cells; remaining cells are
recorded as `skipped_budget` rather than aborting the run.

The eval loop pins its model in `evals/loop.py` (`MODEL`). Change it there deliberately; results
documents record the model used.

## Results files

Every run writes a timestamped document to `evals/results/`. Only a **full** run — all three arms,
no `--limit` — also updates `evals/results/latest.json`; pilots never overwrite the published
baseline.

## Regenerating the docs page

After a full run, regenerate the public results page from `latest.json`:

```bash
env UV_CACHE_DIR=.uv-cache uv run python scripts/update_docs_eval.py
```

This writes `docs-site/src/content/docs/user-guide/evaluation.md`. The first time only, add a
`user-guide/evaluation` sidebar entry to `docs-site/astro.config.mjs`. Do not hand-edit numbers into
the README or docs; anything quantitative should come from `latest.json` so published claims cannot
drift from the recorded run.

## When to run

The benchmark is manual and paid, so run it when results could plausibly change or need to be
re-published:

- before a release that changes the tool surface, catalogue, or semantic layer;
- after resolver or grading changes to the harness itself (pilot first);
- when the published results page is stale enough that live-question freshness claims no longer
  reflect current data.

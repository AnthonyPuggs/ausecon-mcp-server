---
title: Contributing
description: Local development and verification for maintainers.
---

`ausecon-mcp-server` is intentionally narrow: official ABS, RBA, and APRA sources, stdio plus hosted
HTTP transport, and small curated semantic and derived layers over source-native retrievals.

## Local setup

Use Python 3.12 for local development:

```bash
env UV_CACHE_DIR=.uv-cache uv sync --python 3.12 --extra dev
```

## Standard verification

Run the normal local checks before opening a pull request or cutting a tag:

```bash
env UV_CACHE_DIR=.uv-cache uv run ruff check src tests scripts
env UV_CACHE_DIR=.uv-cache uv run pytest
env UV_CACHE_DIR=.uv-cache uv run pytest integration_tests/ -v
env UV_CACHE_DIR=.uv-cache uv run python scripts/audit_catalogue.py
```

## Real client smoke

Before a release tag, run the checked-in stdio smoke path:

```bash
env UV_CACHE_DIR=.uv-cache uv run python scripts/mcp_client_smoke.py
```

The smoke path uses a real FastMCP stdio client transport and verifies:

- `search_datasets`
- `list_economic_concepts`
- `list_catalogue`
- `get_abs_data`
- `get_apra_data`
- `get_economic_series`
- `get_derived_series`

## Review and maintenance discipline

### Dependency update triage

For every dependency pull request, classify the change explicitly as a direct or transitive
dependency change, then read the changelog and any security advisory before merging. For
lockfile-only updates, state the affected runtime surface in the PR notes: server runtime, tests,
docs-site, or build tooling.

Run the smallest relevant verification first, then the standard suite if the dependency touches
runtime code. A docs-site preview proves that the documentation site built; it does not prove MCP
retrieval correctness.

### Review-to-regression lock

Accepted review findings should leave behind a regression test, repository hygiene assertion, or
client smoke assertion. Prefer behaviour-focused tests that describe the invariant that failed, such
as schema format validation, package-data layout, search-result independence, or catalogue filtering.

### Catalogue source governance

Catalogue changes need source-native evidence. Record the official source identifier, exact
`csv_path` or SDMX key, `upstream_url`, `upstream_title`, `last_audited`, aliases, variants, and the
reason the entry belongs in the curated surface. Keep README, docs-site reference pages, semantic
design notes, and tests in documentation parity with the implemented identifiers.

If an ABS, RBA, or APRA entry cannot be reconciled to the official source without approximation,
defer it rather than shipping a semantic shortcut that is difficult to audit.

### Artefact hygiene

Before opening a pull request or cutting a release, check `git status --short` and inspect generated
or packaged-data directories for copied artefacts. The response schema should exist only at the
canonical source paths: `schemas/response.schema.json` for the public contract and
`src/ausecon_mcp/schemas/response.schema.json` for package data.

## Release discipline

- Keep the MCP tool surface stable unless there is a strong reason to break it.
- Do not expose placeholder variants in the runtime catalogue.
- Prefer audited upstream fixes over broad catalogue growth.
- Keep `get_derived_series` read-only, transparent, and formula-based; do not add modelling,
  forecasting, seasonal adjustment, or arbitrary user formulas without a separate design.
- If an ABS, RBA, or APRA replacement series is not cleanly source-native, defer it rather than
  shipping an approximate semantic shortcut.

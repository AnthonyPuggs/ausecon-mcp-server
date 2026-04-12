# RBA + ABS MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server that exposes ABS and RBA discovery and retrieval tools with a consistent, provenance-rich response model.

**Architecture:** Keep source-specific logic in dedicated ABS and RBA providers, normalise tool responses through shared models, and expose a small MCP surface through a thin FastMCP server entry point. Use curated catalogues for economist-friendly discovery, but preserve live-source metadata and provenance on every retrieval.

**Tech Stack:** Python 3.10+, FastMCP, httpx, pytest, respx, Ruff

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `docs/superpowers/plans/2026-04-12-rba-abs-mcp-server.md`

- [ ] Create the package, test, fixture, and examples directories.
- [ ] Add dependency and test configuration for FastMCP, httpx, pytest, pytest-asyncio, respx, and Ruff.
- [ ] Add a short README describing the tool surface and local development commands.

### Task 2: Shared models, catalogues, and parsers

**Files:**
- Create: `src/ausecon_mcp/models.py`
- Create: `src/ausecon_mcp/catalogue/*.py`
- Create: `src/ausecon_mcp/parsers/*.py`
- Create: `tests/test_catalogue.py`
- Create: `tests/test_parsers.py`
- Create: `tests/fixtures/*`

- [ ] Write parser and catalogue tests first for ABS structure parsing, ABS CSV parsing, RBA CSV parsing, and discovery ranking.
- [ ] Implement shared normalised response models and the curated ABS/RBA catalogues needed by the tests.
- [ ] Implement parser functions that turn raw ABS and RBA payloads into the shared model shape.

### Task 3: Providers and MCP tools

**Files:**
- Create: `src/ausecon_mcp/cache.py`
- Create: `src/ausecon_mcp/providers/*.py`
- Create: `src/ausecon_mcp/server.py`
- Create: `tests/test_abs_provider.py`
- Create: `tests/test_rba_provider.py`
- Create: `tests/test_server.py`
- Create: `examples/claude_desktop_config.json`

- [ ] Write provider and tool tests first, including HTTP fetch mocking and response shape checks.
- [ ] Implement ABS and RBA providers with async httpx clients, source-specific fetch logic, and TTL caching.
- [ ] Implement the FastMCP server and the six planned tools using the providers and shared models.

### Task 4: Verification

**Files:**
- Modify: `README.md`

- [ ] Run the full test suite.
- [ ] Run Ruff across the repository.
- [ ] Update README usage examples if the implemented interface differs from the initial scaffold.

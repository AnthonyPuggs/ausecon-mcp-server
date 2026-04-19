import json
import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CLAUDE_EXAMPLE = ROOT / "examples" / "claude_desktop_config.json"
PYPROJECT = ROOT / "pyproject.toml"
LICENSE = ROOT / "LICENSE"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
SERVER_JSON = ROOT / "server.json"
CHANGELOG = ROOT / "CHANGELOG.md"


def test_readme_and_example_advertise_pypi_uvx_install() -> None:
    readme_text = README.read_text(encoding="utf-8")
    example_text = CLAUDE_EXAMPLE.read_text(encoding="utf-8")

    assert "uvx ausecon-mcp-server" in readme_text
    assert "https://pypi.org/project/ausecon-mcp-server/" in readme_text
    assert '"uvx"' in example_text
    assert '"ausecon-mcp-server"' in example_text
    assert "<your-repo-url>" not in readme_text
    assert "rba_abs_mcp" not in readme_text
    assert "rba_abs_mcp" not in example_text
    assert "/absolute/path/to/ausecon-mcp-server" not in example_text


def test_project_metadata_points_to_license_file_and_repository_urls() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert "version" in project.get("dynamic", [])
    assert project["license"] == {"file": "LICENSE"}
    assert project["urls"] == {
        "Homepage": "https://github.com/AnthonyPuggs/ausecon-mcp-server",
        "Repository": "https://github.com/AnthonyPuggs/ausecon-mcp-server",
        "Issues": "https://github.com/AnthonyPuggs/ausecon-mcp-server/issues",
    }


def test_repository_root_includes_visible_mit_license_file() -> None:
    assert LICENSE.is_file()

    license_text = LICENSE.read_text(encoding="utf-8")

    assert "MIT License" in license_text
    assert "Permission is hereby granted, free of charge" in license_text


def test_ci_workflow_exists_with_quality_checks_and_hygiene_guard() -> None:
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "name: CI" in workflow_text
    assert "push:" in workflow_text
    assert "pull_request:" in workflow_text
    assert "workflow_dispatch:" in workflow_text
    assert "actions/checkout@" in workflow_text
    assert "actions/setup-python@" in workflow_text
    assert "astral-sh/setup-uv@" in workflow_text
    assert "python-version: ['3.10', '3.12']" in workflow_text
    assert "uv sync --python ${{ matrix.python-version }} --extra dev" in workflow_text
    assert "uv run ruff check src tests" in workflow_text
    assert "uv run pytest" in workflow_text
    assert "test -f LICENSE" in workflow_text
    assert 'rg -n "rba_abs_mcp|<your-repo-url>" README.md examples pyproject.toml' in workflow_text


def test_readme_tracks_current_release_state() -> None:
    readme_text = README.read_text(encoding="utf-8")
    tool_row = (
        "`get_economic_series` | Resolve a curated economic concept to an ABS or RBA retrieval | "
        "`concept`, `variant`, `geography`, `frequency`, `start`, `end`, `last_n` |"
    )

    assert "https://pypi.org/project/ausecon-mcp-server/" in readme_text
    assert tool_row in readme_text
    assert "claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server" in readme_text
    assert "codex mcp add ausecon -- uvx ausecon-mcp-server" in readme_text
    assert "This repository currently provides a local stdio MCP server only." in readme_text
    assert "`v0.3.0` is a discovery release" not in readme_text
    assert "The current release includes:" not in readme_text
    assert "`v0.5.0` covers the main analyst workflows more credibly" not in readme_text


def test_readme_documents_schema_and_preferred_rba_listing_surface() -> None:
    readme_text = README.read_text(encoding="utf-8")

    assert "schemas/response.schema.json" in readme_text
    assert "docs/response-schema.md" in readme_text
    assert 'list_catalogue(source="rba")' in readme_text


def test_contract_and_architecture_docs_exist() -> None:
    assert (ROOT / "docs" / "architecture.md").is_file()
    assert (ROOT / "docs" / "variants.md").is_file()
    assert (ROOT / "docs" / "response-schema.md").is_file()


def test_release_workflow_smoke_tests_built_wheel() -> None:
    workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "Smoke-test built wheel" in workflow_text
    assert "dist/*.whl" in workflow_text
    assert "ausecon-mcp-server" in workflow_text


def test_python_version_story_is_consistent_across_docs_and_ci() -> None:
    readme_text = README.read_text(encoding="utf-8")
    claude_text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert pyproject["project"]["requires-python"] == ">=3.10"
    assert "Python 3.12 is recommended for local development" in readme_text
    assert "Python 3.10+" in readme_text
    assert "Python 3.12 is recommended for local development" in claude_text
    assert "python-version: ['3.10', '3.12']" in workflow_text


def test_readme_release_instructions_match_tag_derived_versioning() -> None:
    readme_text = README.read_text(encoding="utf-8")

    assert "version is derived from git tags via `hatch-vcs`" in readme_text
    assert "ensure `pyproject.toml` contains the intended version" not in readme_text
    assert "git tag -a vX.Y.Z" not in readme_text


def test_server_metadata_matches_current_changelog_release() -> None:
    changelog_text = CHANGELOG.read_text(encoding="utf-8")
    server_metadata = json.loads(SERVER_JSON.read_text(encoding="utf-8"))

    match = re.search(r"^## \[(\d+\.\d+\.\d+)\] - ", changelog_text, re.MULTILINE)
    assert match is not None
    current_release = match.group(1)

    assert server_metadata["version"] == current_release
    assert server_metadata["packages"][0]["version"] == current_release
    assert (
        f"[{current_release}]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/"
        in changelog_text
    )

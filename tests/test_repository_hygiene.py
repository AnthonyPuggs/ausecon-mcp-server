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
        "`get_economic_series` | Resolve a small set of high-value economic concepts to ABS or "
        "RBA retrievals | `concept`, `variant`, `geography`, `frequency`, `start`, `end` |"
    )

    assert "https://pypi.org/project/ausecon-mcp-server/" in readme_text
    assert tool_row in readme_text
    assert "claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server" in readme_text
    assert "codex mcp add ausecon -- uvx ausecon-mcp-server" in readme_text
    assert "This repository currently provides a local stdio MCP server only." in readme_text
    assert "`v0.3.0` is a discovery release" not in readme_text

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CLAUDE_EXAMPLE = ROOT / "examples" / "claude_desktop_config.json"
PYPROJECT = ROOT / "pyproject.toml"
LICENSE = ROOT / "LICENSE"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_readme_and_example_use_canonical_repository_paths() -> None:
    readme_text = README.read_text(encoding="utf-8")
    example_text = CLAUDE_EXAMPLE.read_text(encoding="utf-8")

    assert "git clone https://github.com/AnthonyPuggs/ausecon-mcp-server.git" in readme_text
    assert "cd ausecon-mcp-server" in readme_text
    assert "/absolute/path/to/ausecon-mcp-server" in readme_text
    assert "/absolute/path/to/ausecon-mcp-server" in example_text
    assert "<your-repo-url>" not in readme_text
    assert "rba_abs_mcp" not in readme_text
    assert "rba_abs_mcp" not in example_text


def test_project_metadata_points_to_license_file_and_repository_urls() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["version"] == "0.3.0"
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


def test_readme_tracks_v0_3_release_state() -> None:
    readme_text = README.read_text(encoding="utf-8")

    assert "This repository is currently at `v0.3.0`." in readme_text
    assert "v0.2.0" not in readme_text
    assert "but it remains a no-op in `v0.2.0`." not in readme_text

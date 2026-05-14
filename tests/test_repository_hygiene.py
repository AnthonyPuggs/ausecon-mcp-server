import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

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
DOCS_WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
SMITHERY_YAML = ROOT / "smithery.yaml"
SMITHERY_DOCKERFILE = ROOT / "Dockerfile.smithery"
SERVER_JSON = ROOT / "server.json"
FASTMCP_JSON = ROOT / "fastmcp.json"
CHANGELOG = ROOT / "CHANGELOG.md"
CONTRIBUTING = ROOT / "docs" / "contributing.md"
CLIENT_SMOKE = ROOT / "scripts" / "mcp_client_smoke.py"
DOCS_SITE = ROOT / "docs-site"
DOCS_ICON = DOCS_SITE / "public" / "ausecon-icon.svg"
ROADMAP = ROOT / "docs" / "roadmap.md"
DOCS_URL = "https://auseconmcp.com/"
REPOSITORY_URL = "https://github.com/AnthonyPuggs/ausecon-mcp-server"


def test_readme_and_example_advertise_pypi_uvx_install() -> None:
    readme_text = README.read_text(encoding="utf-8")
    example_text = CLAUDE_EXAMPLE.read_text(encoding="utf-8")

    assert "uvx ausecon-mcp-server" in readme_text
    assert "https://pypi.org/project/ausecon-mcp-server/" in readme_text
    assert DOCS_URL in readme_text
    assert '"uvx"' in example_text
    assert '"ausecon-mcp-server"' in example_text
    assert "<your-repo-url>" not in readme_text
    assert "rba_abs_mcp" not in readme_text
    assert "rba_abs_mcp" not in example_text
    assert "/absolute/path/to/ausecon-mcp-server" not in example_text


def test_docs_site_exposes_public_icon_for_hosted_mcp_metadata() -> None:
    icon_text = DOCS_ICON.read_text(encoding="utf-8")

    assert "<svg" in icon_text
    assert "AusEcon MCP Server" in icon_text


def test_project_metadata_points_to_license_file_and_repository_urls() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert "version" in project.get("dynamic", [])
    assert project["license"] == {"file": "LICENSE"}
    assert project["urls"] == {
        "Homepage": DOCS_URL,
        "Documentation": DOCS_URL,
        "Repository": REPOSITORY_URL,
        "Issues": f"{REPOSITORY_URL}/issues",
    }


def test_project_metadata_includes_http_container_entrypoint_dependencies() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["scripts"]["ausecon-mcp-server"] == "ausecon_mcp.server:main"
    assert project["scripts"]["ausecon-mcp-http"] == "ausecon_mcp.server:main_http"
    assert "fastmcp>=3.2.4" in project["dependencies"]
    assert "starlette>=0.27,<1" in project["dependencies"]


def test_fastmcp_metadata_points_homepage_to_docs_site() -> None:
    metadata = json.loads(FASTMCP_JSON.read_text(encoding="utf-8"))

    assert metadata["homepage"] == DOCS_URL


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
    assert "uv run ruff check src tests scripts" in workflow_text
    assert "uv run pytest" in workflow_text
    assert "test -f LICENSE" in workflow_text
    assert 'command -v rg >/dev/null 2>&1' in workflow_text
    assert (
        'rg -n "rba_abs_mcp|<your-repo-url>" README.md docs-site examples '
        "pyproject.toml fastmcp.json server.json smithery.yaml Dockerfile.smithery"
        in workflow_text
    )
    assert (
        'grep -R -n -E "rba_abs_mcp|<your-repo-url>" README.md docs-site examples '
        "pyproject.toml fastmcp.json server.json smithery.yaml Dockerfile.smithery"
        in workflow_text
    )


def test_readme_is_slim_landing_page_for_current_release_state() -> None:
    readme_text = README.read_text(encoding="utf-8")

    assert len(readme_text.splitlines()) < 140
    assert "Version `1.1.0` is the current hosted release baseline." in readme_text
    assert re.search(r"stdio plus\s+Streamable HTTP", readme_text)
    assert "ten read-only MCP tools" in readme_text
    assert "55 curated macroeconomic concepts" in readme_text
    assert "48 curated macroeconomic concepts" not in readme_text
    assert "36 curated macroeconomic concepts" not in readme_text
    assert "29 curated macroeconomic concepts" not in readme_text
    assert "28 curated macroeconomic concepts" not in readme_text
    assert DOCS_URL in readme_text
    assert "claude mcp add --transport stdio ausecon -- uvx ausecon-mcp-server" in readme_text
    assert "codex mcp add ausecon -- uvx ausecon-mcp-server" in readme_text
    assert "get_economic_series" in readme_text
    assert "## Releasing" not in readme_text
    assert "## Operations" not in readme_text
    assert "`v0.3.0` is a discovery release" not in readme_text
    assert "The current release includes:" not in readme_text
    assert "`v0.5.0` covers the main analyst workflows more credibly" not in readme_text


def test_docs_site_instruments_vercel_observability_without_query_payloads() -> None:
    package_json = json.loads((DOCS_SITE / "package.json").read_text(encoding="utf-8"))
    layout_text = (DOCS_SITE / "src/layouts/Base.astro").read_text(encoding="utf-8")

    assert package_json["dependencies"]["@vercel/analytics"].startswith("^")
    assert package_json["dependencies"]["@vercel/speed-insights"].startswith("^")
    assert "import Analytics from '@vercel/analytics/astro'" in layout_text
    assert "import SpeedInsights from '@vercel/speed-insights/astro'" in layout_text
    assert "function speedInsightsBeforeSend" in layout_text
    assert "window.speedInsightsBeforeSend = speedInsightsBeforeSend" in layout_text
    assert "u.search = ''" in layout_text
    assert "u.hash = ''" in layout_text
    assert "<SpeedInsights />" in layout_text
    assert "<Analytics />" in layout_text


def test_operations_docs_separate_server_and_docs_site_observability() -> None:
    operations_text = (
        DOCS_SITE / "src/content/docs/operations/caching-and-logging.md"
    ).read_text(encoding="utf-8")

    assert "## Server observability" in operations_text
    assert "## Documentation-site observability" in operations_text
    assert "Vercel Analytics" in operations_text
    assert "Speed Insights" in operations_text
    assert "does not measure MCP data reliability" in operations_text
    assert "query strings and fragments" in operations_text


def test_hosted_deployment_checklist_is_documented_without_http_smoke_script() -> None:
    smithery_text = (ROOT / "docs" / "smithery-deployment.md").read_text(encoding="utf-8")
    docs_page = (
        DOCS_SITE / "src/content/docs/operations/hosted-deployment.md"
    ).read_text(encoding="utf-8")

    assert not (ROOT / "scripts" / "mcp_http_smoke.py").exists()
    for text in (smithery_text, docs_page):
        assert "Render uptime" in text
        assert "`/healthz`" in text
        assert "`/.well-known/mcp/server-card.json`" in text
        assert "Smithery listing" in text
        assert "manual MCP tool-call smoke" in text


def test_post_v11_roadmap_is_documented_and_contract_preserving() -> None:
    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    docs_roadmap_text = (
        DOCS_SITE / "src/content/docs/maintainers/roadmap.md"
    ).read_text(encoding="utf-8")

    for text in (roadmap_text, docs_roadmap_text):
        assert "v1.2" in text
        assert "v1.3" in text
        assert "v1.4" in text
        assert "v2.0" in text
        assert "APRA" in text
        assert "APRA source-native foundation" in text
        assert "{metadata, series, observations}" in text
        assert "mcp_http_smoke.py" not in text


def test_docs_site_documents_schema_and_preferred_rba_listing_surface() -> None:
    tools_text = (DOCS_SITE / "src/content/docs/reference/tools.md").read_text(encoding="utf-8")
    schema_text = (DOCS_SITE / "src/content/docs/reference/response-schema.md").read_text(
        encoding="utf-8"
    )
    user_guide_text = (
        DOCS_SITE / "src/content/docs/user-guide/discovery-and-retrieval.md"
    ).read_text(encoding="utf-8")

    assert "schemas/response.schema.json" in schema_text
    assert 'list_catalogue(source="rba")' in user_guide_text
    assert "Deprecated compatibility alias" in tools_text


def test_contract_and_architecture_docs_exist() -> None:
    assert (ROOT / "docs" / "architecture.md").is_file()
    assert (ROOT / "docs" / "variants.md").is_file()
    assert (ROOT / "docs" / "response-schema.md").is_file()
    assert CONTRIBUTING.is_file()


def test_docs_site_scaffold_exists_with_custom_domain_configuration() -> None:
    package_json = json.loads((DOCS_SITE / "package.json").read_text(encoding="utf-8"))
    astro_config = (DOCS_SITE / "astro.config.mjs").read_text(encoding="utf-8")

    assert (DOCS_SITE / ".nvmrc").read_text(encoding="utf-8").strip() == "22.12.0"
    assert package_json["scripts"]["check"] == "astro check"
    assert package_json["scripts"]["build"] == "astro build"
    assert package_json["dependencies"]["@astrojs/starlight"].startswith("^")
    assert "site: 'https://auseconmcp.com'" in astro_config
    assert "base: '/ausecon-mcp-server'" not in astro_config
    assert "reference/semantic-concepts" in astro_config


def test_docs_workflow_builds_and_deploys_github_pages_site() -> None:
    workflow_text = DOCS_WORKFLOW.read_text(encoding="utf-8")

    assert "name: Docs" in workflow_text
    assert "node-version-file: docs-site/.nvmrc" in workflow_text
    assert "cache-dependency-path: docs-site/package-lock.json" in workflow_text
    assert "working-directory: docs-site" in workflow_text
    assert "npm ci" in workflow_text
    assert "npm run check" in workflow_text
    assert "npm run build" in workflow_text
    assert "actions/upload-pages-artifact@" in workflow_text
    assert "actions/deploy-pages@" in workflow_text
    assert "pages: write" in workflow_text
    assert "id-token: write" in workflow_text


def test_generated_semantic_concepts_reference_is_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/update_docs_reference.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_contributing_doc_mentions_client_smoke_path() -> None:
    text = CONTRIBUTING.read_text(encoding="utf-8")

    assert "mcp_client_smoke.py" in text
    assert "search_datasets" in text
    assert "list_economic_concepts" in text
    assert "list_catalogue" in text
    assert "get_abs_data" in text
    assert "get_economic_series" in text
    assert "get_derived_series" in text


def test_client_smoke_script_exists() -> None:
    assert CLIENT_SMOKE.is_file()


def test_release_workflow_smoke_tests_built_wheel() -> None:
    workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "Smoke-test built wheel" in workflow_text
    assert "dist/*.whl" in workflow_text
    assert "ausecon-mcp-server" in workflow_text


def test_dockerfile_supports_local_and_pypi_install_modes() -> None:
    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")

    assert "apt-get install --yes --no-install-recommends git" in dockerfile_text
    assert "ARG AUSECON_INSTALL_SOURCE=local" in dockerfile_text
    assert "ARG AUSECON_VERSION=" in dockerfile_text
    assert "COPY --chown=ausecon:ausecon . /home/ausecon/src" in dockerfile_text
    assert 'if [ "$AUSECON_INSTALL_SOURCE" = "local" ]; then' in dockerfile_text
    assert "uv tool install /home/ausecon/src" in dockerfile_text
    assert 'elif [ "$AUSECON_INSTALL_SOURCE" = "pypi" ]; then' in dockerfile_text
    assert 'if [ -z "$AUSECON_VERSION" ]; then' in dockerfile_text
    assert 'uv tool install "ausecon-mcp-server==${AUSECON_VERSION}"' in dockerfile_text


def test_smithery_yaml_declares_http_container_without_session_config() -> None:
    metadata = yaml.safe_load(SMITHERY_YAML.read_text(encoding="utf-8"))

    assert metadata["runtime"] == "container"
    assert metadata["build"] == {
        "dockerfile": "Dockerfile.smithery",
        "dockerBuildPath": ".",
    }
    assert metadata["startCommand"]["type"] == "http"
    assert "configSchema" not in metadata["startCommand"]
    assert "exampleConfig" not in metadata["startCommand"]


def test_smithery_dockerfile_uses_multistage_non_root_runtime_without_git_copy() -> None:
    dockerfile_text = SMITHERY_DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM python:3.12-slim AS builder" in dockerfile_text
    assert "FROM python:3.12-slim AS runtime" in dockerfile_text
    assert "ARG AUSECON_VERSION=" in dockerfile_text
    assert "server.json" in dockerfile_text
    assert "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_AUSECON_MCP_SERVER" in dockerfile_text
    assert "apt-get install --yes --no-install-recommends git" in dockerfile_text
    assert "uv build --wheel --out-dir /dist" in dockerfile_text
    assert "COPY --from=builder /dist/*.whl /tmp/" in dockerfile_text
    assert "USER ausecon" in dockerfile_text
    assert "EXPOSE 8081" in dockerfile_text
    assert 'ENTRYPOINT ["ausecon-mcp-http"]' in dockerfile_text
    assert "COPY --from=builder /build" not in dockerfile_text
    assert ".git" not in dockerfile_text


def test_dockerignore_keeps_git_for_smithery_builder_but_excludes_local_state() -> None:
    ignored = {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }

    assert ".git" not in ignored
    assert ".venv/" in ignored
    assert ".worktrees/" in ignored
    assert "docs-site/node_modules/" in ignored
    assert "README.html" in ignored
    assert "README_files/" in ignored


def test_release_workflow_builds_container_from_pypi_release_artifact() -> None:
    workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "AUSECON_INSTALL_SOURCE=pypi" in workflow_text
    assert "AUSECON_VERSION=${{ steps.version.outputs.value }}" in workflow_text


def test_ci_workflow_runs_local_docker_smoke_build() -> None:
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "Docker smoke build" in workflow_text
    assert "docker build ." in workflow_text


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
    releasing_text = (DOCS_SITE / "src/content/docs/maintainers/releasing.md").read_text(
        encoding="utf-8"
    )

    assert "version is derived from git tags via `hatch-vcs`" in releasing_text
    assert "ensure `pyproject.toml` contains the intended version" not in releasing_text
    assert "git tag -a vX.Y.Z" not in releasing_text


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


def test_claude_session_lock_is_not_tracked() -> None:
    assert not (ROOT / ".claude" / "scheduled_tasks.lock").exists()


def test_integration_fixture_monkeypatches_cache_root_directly() -> None:
    text = (ROOT / "integration_tests" / "conftest.py").read_text(encoding="utf-8")

    assert "AUSECON_CACHE_DIR" not in text
    assert 'monkeypatch.setattr(cache_module, "_default_disk_dir"' in text

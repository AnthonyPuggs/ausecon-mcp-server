import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
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
CODEQL_WORKFLOW = ROOT / ".github" / "workflows" / "codeql.yml"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
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
DOCS_SITE_CONTRIBUTING = DOCS_SITE / "src" / "content" / "docs" / "maintainers" / "contributing.md"
DOCS_ICON = DOCS_SITE / "public" / "ausecon-icon.svg"
HOSTED_DEPLOYMENT = DOCS_SITE / "src" / "content" / "docs" / "operations" / "hosted-deployment.md"
SEMANTIC_REFERENCE = DOCS_SITE / "src" / "content" / "docs" / "reference" / "semantic-concepts.md"
PROMPTING_GUIDE = DOCS_SITE / "src" / "content" / "docs" / "user-guide" / "prompting-ai-agents.md"
DOCS_URL = "https://auseconmcp.com/"
REPOSITORY_URL = "https://github.com/AnthonyPuggs/ausecon-mcp-server"


def _normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


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
    assert "starlette>=0.27,<2" in project["dependencies"]


def test_project_metadata_declares_yaml_test_dependency_explicitly() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]

    assert any(dependency.lower().startswith("pyyaml") for dependency in dev_dependencies)


def test_response_schema_is_packaged_under_project_namespace() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]

    assert force_include == {
        "src/ausecon_mcp/schemas/response.schema.json": (
            "ausecon_mcp/schemas/response.schema.json"
        ),
        "src/ausecon_mcp/data/apra_url_seeds.json": "ausecon_mcp/data/apra_url_seeds.json",
    }


def test_packaged_schema_directory_contains_only_canonical_schema_file() -> None:
    schema_dir = ROOT / "src" / "ausecon_mcp" / "schemas"

    assert sorted(path.name for path in schema_dir.iterdir() if path.is_file()) == [
        "response.schema.json"
    ]


def test_maintainer_docs_capture_review_and_dependency_triage_disciplines() -> None:
    required_phrases = {
        "Dependency update triage",
        "direct or transitive dependency",
        "security advisory",
        "Review-to-regression lock",
        "regression test",
        "Catalogue source governance",
        "upstream_title",
        "csv_path",
        "documentation parity",
        "Artefact hygiene",
    }

    for path in (CONTRIBUTING, DOCS_SITE_CONTRIBUTING):
        text = _normalise_whitespace(path.read_text(encoding="utf-8"))
        for phrase in required_phrases:
            assert phrase in text, f"{path} is missing {phrase!r}"


def test_maintainer_docs_capture_codeql_advanced_setup_requirement() -> None:
    required_phrases = {
        "CodeQL advanced setup",
        "disable CodeQL default setup",
        "advanced CodeQL workflow",
        "default setup",
    }

    for path in (CONTRIBUTING, DOCS_SITE_CONTRIBUTING):
        text = _normalise_whitespace(path.read_text(encoding="utf-8"))
        for phrase in required_phrases:
            assert phrase in text, f"{path} is missing {phrase!r}"


def test_hosted_deployment_docs_scope_vercel_preview_signals_to_docs_site() -> None:
    hosted_text = _normalise_whitespace(HOSTED_DEPLOYMENT.read_text(encoding="utf-8"))

    assert "Vercel preview" in hosted_text
    assert "docs-site" in hosted_text
    assert "not MCP retrieval correctness" in hosted_text
    assert "manual MCP tool-call smoke" in hosted_text


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
    assert "python-version: ['3.10', '3.11', '3.12', '3.13']" in workflow_text
    assert "uv sync --python ${{ matrix.python-version }} --extra dev" in workflow_text
    assert "uv run ruff check src tests scripts" in workflow_text
    assert "uv run pytest" in workflow_text
    assert "test -f LICENSE" in workflow_text
    assert "command -v rg >/dev/null 2>&1" in workflow_text
    assert (
        'rg -n "rba_abs_mcp|<your-repo-url>" README.md docs-site examples '
        "pyproject.toml fastmcp.json server.json smithery.yaml Dockerfile.smithery" in workflow_text
    )
    assert (
        'grep -R -n -E "rba_abs_mcp|<your-repo-url>" README.md docs-site examples '
        "pyproject.toml fastmcp.json server.json smithery.yaml Dockerfile.smithery" in workflow_text
    )


def test_readme_is_rich_landing_page_for_current_release_state() -> None:
    readme_text = README.read_text(encoding="utf-8")
    docs_home_text = (DOCS_SITE / "src/content/docs/index.mdx").read_text(encoding="utf-8")

    assert '<img src="assets/banner.svg"' in readme_text
    assert "Australian economic data is authoritative but awkward to reach" in readme_text
    assert "Version `1.13.0` is the current release line." in docs_home_text
    assert "Version `1.12.1` is the current release line." not in readme_text
    assert "Version `1.12.1` is the current release line." not in docs_home_text

    assert "read-only tools" in readme_text
    assert "economic concepts" in readme_text
    assert "derived indicators" in readme_text
    assert "stdio locally, Streamable HTTP when hosted" in readme_text

    assert "55 curated macroeconomic concepts" not in readme_text
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


def test_readme_leads_with_open_free_correctness_value_props() -> None:
    readme_text = README.read_text(encoding="utf-8")

    # Differentiator strip + "Why this exists" lead on the durable value props.
    assert "no API key" in readme_text
    assert "no-API-key" in readme_text
    assert "fresh &amp; fully source-traceable" in readme_text

    # Correctness framed honestly: staleness is flagged, not denied (no false absolute).
    assert "Fresh &amp; source-traceable" in readme_text
    assert "never served silently" in readme_text
    assert "never from a stale cache" not in readme_text

    # Lead clause preserved; no competitor naming.
    assert "Australian economic data is authoritative but awkward to reach" in readme_text
    assert "ausdata" not in readme_text.lower()


def test_docs_landing_leads_with_open_free_correctness_value_props() -> None:
    docs_home = (DOCS_SITE / "src/content/docs/index.mdx").read_text(encoding="utf-8")

    assert "no-API-key" in docs_home
    assert "source-traceable" in docs_home
    # Correctness framed honestly (no false absolute).
    assert "flagged, never silent" in docs_home
    assert "never a stale cache" not in docs_home
    assert "ausdata" not in docs_home.lower()
    # Release-line marker preserved (asserted elsewhere too).
    assert "Version `1.13.0` is the current release line." in docs_home


def test_readme_documents_local_client_install_configs() -> None:
    readme_text = README.read_text(encoding="utf-8")

    # Cursor: config file path, mcpServers config, and the one-click deeplink.
    assert "~/.cursor/mcp.json" in readme_text
    assert (
        "cursor://anysphere.cursor-deeplink/mcp/install?name=ausecon&config="
        "eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJhdXNlY29uLW1jcC1zZXJ2ZXIiXX0=" in readme_text
    )

    # Windsurf: config file path and mcpServers config (no one-click for unlisted servers).
    assert "~/.codeium/windsurf/mcp_config.json" in readme_text

    # VS Code: .vscode/mcp.json "servers" config + GitHub-clickable https install badge.
    assert ".vscode/mcp.json" in readme_text
    assert '"servers"' in readme_text
    assert (
        "https://insiders.vscode.dev/redirect/mcp/install?name=ausecon&config="
        "%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22ausecon-mcp-server%22%5D%7D"
        in readme_text
    )


def test_docs_site_getting_started_documents_client_install_configs() -> None:
    getting_started = (
        DOCS_SITE / "src/content/docs/getting-started/index.md"
    ).read_text(encoding="utf-8")

    # Same three new clients as the README, with the docs-site (real HTML) using
    # the directly-clickable URI-scheme one-click links.
    assert "~/.cursor/mcp.json" in getting_started
    assert "cursor://anysphere.cursor-deeplink/mcp/install?name=ausecon" in getting_started
    assert "~/.codeium/windsurf/mcp_config.json" in getting_started
    assert ".vscode/mcp.json" in getting_started
    assert "vscode:mcp/install?" in getting_started


def test_readme_does_not_advertise_a_contradictory_derived_count() -> None:
    readme_text = README.read_text(encoding="utf-8")

    # The derived-indicator count lives once, in the stats table. Prose must not
    # hardcode a second, drift-prone figure (this is how "Nine" went stale while
    # the table correctly said 16).
    assert "Nine formula-based indicators" not in readme_text
    assert "Formula-based indicators like <code>real_cash_rate</code>" in readme_text


async def test_readme_surface_counts_are_code_derived() -> None:
    from ausecon_mcp.catalogue.resolver import list_economic_concepts
    from ausecon_mcp.derived import DERIVED_CONCEPTS
    from ausecon_mcp.server import build_server

    mcp = build_server()
    tools = await mcp.list_tools(run_middleware=False)
    prompts = await mcp.list_prompts()

    # Each cell in the README stats table must match the live count from code.
    expected = {
        "read-only tools": len(tools),
        "economic concepts": len(list_economic_concepts()),
        "derived indicators": len(DERIVED_CONCEPTS),
        "prompt templates": len(prompts),
        "data sources": 3,  # ABS, RBA, APRA — fixed architectural triad
    }

    readme_text = README.read_text(encoding="utf-8")
    for label, count in expected.items():
        match = re.search(rf"<b>(\d+)</b><br/><sub>{re.escape(label)}</sub>", readme_text)
        assert match is not None, f"README stats table has no cell labelled {label!r}"
        assert int(match.group(1)) == count, (
            f"README says {match.group(1)} {label!r}, code has {count}. "
            "Update the stats table in README.md."
        )


def test_public_semantic_docs_do_not_contain_known_stale_series_ids() -> None:
    stale_ids = {"FZCY0300D"}
    # The semantic design doc now lives under the gitignored docs/superpowers/ tree
    # (a private planning doc), so it is no longer a public surface this guard polices.
    docs = {
        "README": README,
        "semantic reference": SEMANTIC_REFERENCE,
    }

    for label, path in docs.items():
        text = path.read_text(encoding="utf-8")
        for stale_id in stale_ids:
            assert stale_id not in text, f"{label} contains stale semantic series id {stale_id}"


def test_mcp_client_smoke_does_not_assume_search_result_order() -> None:
    smoke_text = CLIENT_SMOKE.read_text(encoding="utf-8")

    assert 'search.data[0]["id"] == "a2"' not in smoke_text
    assert 'any(row.get("id") == "a2" for row in search.data)' in smoke_text


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
    operations_text = (DOCS_SITE / "src/content/docs/operations/caching-and-logging.md").read_text(
        encoding="utf-8"
    )

    assert "## Server observability" in operations_text
    assert "## Documentation-site observability" in operations_text
    assert "Vercel Analytics" in operations_text
    assert "Speed Insights" in operations_text
    assert "does not measure MCP data reliability" in operations_text
    assert "query strings and fragments" in operations_text


def test_hosted_deployment_checklist_is_documented_without_http_smoke_script() -> None:
    smithery_text = (ROOT / "docs" / "smithery-deployment.md").read_text(encoding="utf-8")
    docs_page = (DOCS_SITE / "src/content/docs/operations/hosted-deployment.md").read_text(
        encoding="utf-8"
    )

    assert not (ROOT / "scripts" / "mcp_http_smoke.py").exists()
    for text in (smithery_text, docs_page):
        assert "Render uptime" in text
        assert "`/healthz`" in text
        assert "`/.well-known/mcp/server-card.json`" in text
        assert "Smithery listing" in text
        assert "manual MCP tool-call smoke" in text


def test_post_v11_roadmap_is_documented_and_contract_preserving() -> None:
    docs_roadmap_text = (DOCS_SITE / "src/content/docs/maintainers/roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "v1.2" in docs_roadmap_text
    assert "v1.3" in docs_roadmap_text
    assert "v1.4" in docs_roadmap_text
    assert "v1.5" in docs_roadmap_text
    assert "v1.6" in docs_roadmap_text
    assert "v2.0" in docs_roadmap_text
    assert "current v1.13.0 release line" in docs_roadmap_text
    assert "APRA" in docs_roadmap_text
    assert "APRA source-native foundation" in docs_roadmap_text
    assert "{metadata, series, observations}" in docs_roadmap_text
    assert "mcp_http_smoke.py" not in docs_roadmap_text


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


def test_docs_site_documents_ai_agent_prompting_flow() -> None:
    readme_text = README.read_text(encoding="utf-8")
    guide_text = PROMPTING_GUIDE.read_text(encoding="utf-8")
    astro_config = (DOCS_SITE / "astro.config.mjs").read_text(encoding="utf-8")
    getting_started_text = (DOCS_SITE / "src/content/docs/getting-started/index.md").read_text(
        encoding="utf-8"
    )
    discovery_text = (
        DOCS_SITE / "src/content/docs/user-guide/discovery-and-retrieval.md"
    ).read_text(encoding="utf-8")
    examples_text = (DOCS_SITE / "src/content/docs/user-guide/examples.md").read_text(
        encoding="utf-8"
    )
    tools_text = (DOCS_SITE / "src/content/docs/reference/tools.md").read_text(encoding="utf-8")

    assert "## A quick taste" in readme_text
    assert 'list_economic_concepts(query="cash rate")' in readme_text
    assert 'get_derived_series(concept="real_cash_rate", last_n=12)' in readme_text
    assert "Connected to an AI agent" in readme_text
    assert "Prompting AI Agents" in astro_config
    assert "user-guide/prompting-ai-agents" in astro_config
    for text in (getting_started_text, discovery_text, examples_text, tools_text):
        assert "/user-guide/prompting-ai-agents/" in text

    assert 'list_economic_concepts(query="quarterly real GDP growth")' in guide_text
    assert 'get_economic_series(concept="gdp_growth", last_n=40)' in guide_text
    assert 'get_economic_series(concept="cash_rate_target", last_n=1)' in guide_text
    assert 'get_derived_series(concept="real_cash_rate", last_n=12)' in guide_text
    assert 'search_datasets(query="housing credit")' in guide_text
    assert "not a hard guarantee" in guide_text
    assert "`metadata`, `series`, and `observations`" in guide_text


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
    assert "Python 3.12 is recommended; the CI matrix supports 3.10+." in readme_text
    assert "Python 3.12 is recommended for local development" in claude_text
    assert "python-version: ['3.10', '3.11', '3.12', '3.13']" in workflow_text


def test_codeql_and_dependabot_are_configured_for_visible_security_automation() -> None:
    codeql_text = CODEQL_WORKFLOW.read_text(encoding="utf-8")
    dependabot_text = DEPENDABOT.read_text(encoding="utf-8")
    releasing_text = (DOCS_SITE / "src/content/docs/maintainers/releasing.md").read_text(
        encoding="utf-8"
    )

    assert "name: CodeQL" in codeql_text
    assert "github/codeql-action/init@" in codeql_text
    assert "security-extended" in codeql_text
    assert "github/codeql-action/analyze@" in codeql_text
    assert 'package-ecosystem: "pip"' in dependabot_text
    assert 'package-ecosystem: "github-actions"' in dependabot_text
    assert 'package-ecosystem: "npm"' in dependabot_text
    assert 'directory: "/docs-site"' in dependabot_text
    assert "CodeQL default setup is disabled" in releasing_text
    assert "advanced CodeQL workflow" in releasing_text


def test_changelog_promotes_v1130_and_keeps_fresh_unreleased_section() -> None:
    changelog_text = CHANGELOG.read_text(encoding="utf-8")
    unreleased_index = changelog_text.index("## [Unreleased]")
    v1130_index = changelog_text.index("## [1.13.0] - 2026-06-18")

    assert unreleased_index < v1130_index
    unreleased_section = changelog_text[unreleased_index:v1130_index]
    v1130_section = changelog_text[v1130_index : changelog_text.index("## [1.12.1]")]

    assert "household_saving_ratio" not in unreleased_section
    assert "household_saving_ratio" in v1130_section
    assert (
        "[Unreleased]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.13.0...HEAD"
    ) in changelog_text
    assert (
        "[1.13.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.12.1...v1.13.0"
    ) in changelog_text
    assert (
        "[1.12.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.12.0...v1.12.1"
    ) in changelog_text
    assert (
        "[1.12.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.11.0...v1.12.0"
    ) in changelog_text
    assert (
        "[1.11.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.10.0...v1.11.0"
    ) in changelog_text
    assert (
        "[1.10.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.9.0...v1.10.0"
    ) in changelog_text
    assert (
        "[1.9.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.8.0...v1.9.0"
    ) in changelog_text
    assert (
        "[1.8.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.7.1...v1.8.0"
    ) in changelog_text
    assert (
        "[1.7.1]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.7.0...v1.7.1"
    ) in changelog_text
    assert (
        "[1.7.0]: https://github.com/AnthonyPuggs/ausecon-mcp-server/compare/v1.6.0...v1.7.0"
    ) in changelog_text


def test_smithery_deployment_docs_match_current_release_state() -> None:
    smithery_text = (ROOT / "docs" / "smithery-deployment.md").read_text(encoding="utf-8")

    assert "v1.13.0" in smithery_text
    assert "1.13.0" in smithery_text
    assert "fourteen tools" in smithery_text
    assert "get_latest_observations" in smithery_text
    assert "list_release_events" in smithery_text
    assert "v1.12.1" not in smithery_text


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


def test_server_json_advertises_hosted_streamable_http_remote() -> None:
    server_metadata = json.loads(SERVER_JSON.read_text(encoding="utf-8"))

    remotes = server_metadata.get("remotes", [])
    assert any(
        remote.get("type") == "streamable-http"
        and remote.get("url") == "https://ausecon-mcp-server.onrender.com/mcp"
        for remote in remotes
    ), "server.json must advertise the hosted Streamable HTTP /mcp remote"

    # packages (stdio) must remain alongside the new remote.
    assert server_metadata["packages"][0]["transport"]["type"] == "stdio"


def test_readme_advertises_hosted_try_instantly_path() -> None:
    readme_text = README.read_text(encoding="utf-8")

    assert "Try it instantly" in readme_text
    assert "https://ausecon-mcp-server.onrender.com/mcp" in readme_text
    assert (
        "claude mcp add --transport http ausecon "
        "https://ausecon-mcp-server.onrender.com/mcp" in readme_text
    )


def test_docs_site_getting_started_advertises_hosted_try_instantly_path() -> None:
    getting_started = (
        DOCS_SITE / "src/content/docs/getting-started/index.md"
    ).read_text(encoding="utf-8")

    assert "Try it instantly" in getting_started
    assert "https://ausecon-mcp-server.onrender.com/mcp" in getting_started


def test_claude_session_lock_is_not_tracked() -> None:
    assert not (ROOT / ".claude" / "scheduled_tasks.lock").exists()


def test_integration_fixture_monkeypatches_cache_root_directly() -> None:
    text = (ROOT / "integration_tests" / "conftest.py").read_text(encoding="utf-8")

    assert "AUSECON_CACHE_DIR" not in text
    assert 'monkeypatch.setattr(cache_module, "_default_disk_dir"' in text


def test_no_sync_collision_duplicate_python_files_are_tracked() -> None:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git ls-files unavailable (e.g. sdist checkout)")
    offenders = [line for line in result.stdout.splitlines() if re.search(r"\s\d+\.py$", line)]
    assert not offenders, f"sync-collision duplicate files tracked: {offenders}"


DATA_FRESHNESS_PAGE = (
    DOCS_SITE / "src" / "content" / "docs" / "user-guide" / "data-freshness-and-provenance.md"
)
ASTRO_CONFIG = DOCS_SITE / "astro.config.mjs"


def test_data_freshness_page_exists_and_is_linked() -> None:
    page = DATA_FRESHNESS_PAGE.read_text(encoding="utf-8")
    sidebar = ASTRO_CONFIG.read_text(encoding="utf-8")
    schema = (
        DOCS_SITE / "src" / "content" / "docs" / "reference" / "response-schema.md"
    ).read_text(encoding="utf-8")

    # The page documents the already-stamped provenance fields and the honest stale rule.
    for field in ("retrieval_url", "retrieved_at", "server_version", "updated_after"):
        assert field in page, f"freshness page must document {field}"
    assert "stale" in page
    assert "never" in page.lower()  # the honest "never silently stale" framing
    assert "ausdata" not in page.lower()  # name no competitor

    # Registered in the sidebar and cross-linked from the response schema.
    assert "user-guide/data-freshness-and-provenance" in sidebar
    assert "data-freshness-and-provenance" in schema


def test_readme_advertises_nightly_integration_badge() -> None:
    readme_text = README.read_text(encoding="utf-8")
    assert "actions/workflow/status/AnthonyPuggs/ausecon-mcp-server/integration.yml" in readme_text
    assert "label=Integration" in readme_text

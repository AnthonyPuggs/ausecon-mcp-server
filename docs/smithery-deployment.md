# Smithery Deployment Runbook

This runbook covers the hosted Smithery deployment path for
`ausecon-mcp-server`. The stdio command remains the default for local MCP
clients, PyPI, and MCP registry usage.

## Preflight

Before connecting Smithery, confirm the release state is consistent:

```bash
git status --short --branch
git ls-remote origin refs/heads/main refs/tags/v1.1.0
python3 -m pip index versions ausecon-mcp-server
```

Expected state for the v1.1.0 Smithery release:

- `main` and `v1.1.0` point at the same published release commit.
- PyPI lists `ausecon-mcp-server (1.1.0)`.
- `server.json` and `CHANGELOG.md` both refer to `1.1.0`.
- `smithery.yaml` declares `runtime: "container"` and `startCommand.type: "http"`.
- `Dockerfile.smithery` builds the local wheel and runs `ausecon-mcp-http`.

Keep generated local artefacts such as `README.html` and `README_files/` out of
Git and Docker build contexts.

## Smithery Setup

Install the Smithery GitHub app with least privilege:

- Choose selected repositories only.
- Grant access to `AnthonyPuggs/ausecon-mcp-server`.
- Use `main` as the deployment branch.
- Use repository base directory `.`.
- Leave auto-deploy disabled until the first deployment has been inspected.

Create the Smithery server from the GitHub repository, not URL publishing,
Uplink, local MCPB, or stdio. The server should use the checked-in
`smithery.yaml`:

```yaml
runtime: "container"
build:
  dockerfile: "Dockerfile.smithery"
  dockerBuildPath: "."
startCommand:
  type: "http"
```

Do not add `configSchema` or `exampleConfig` for v1.1.0. The server does not
need user secrets or per-session configuration because every exposed tool reads
public ABS/RBA data.

## Deployment Checks

After the first Smithery build:

- Confirm the container starts `ausecon-mcp-http`.
- Confirm Smithery routes MCP traffic to `/mcp`.
- Confirm the server listens on the platform-provided `PORT`.
- Confirm Smithery detects the expected tools: `list_economic_concepts`,
  `get_economic_series`, `search_datasets`, `get_abs_data`, and
  `get_rba_table`.
- Check response metadata from a live retrieval. `metadata.server_version`
  should report `1.1.0`; if it reports a fallback value, configure Smithery to
  pass `AUSECON_VERSION=1.1.0` as a Docker build argument if the platform
  supports build args.

Use the Smithery Playground for smoke tests:

- `list_economic_concepts(query="cash rate")`
- `get_economic_series(concept="cash_rate_target", last_n=5)`
- `search_datasets(query="unemployment rate", source="abs")`

Keep the listing private or unlisted until these checks pass, then switch to
public discovery.

## Security And Safety

The public HTTP deployment is acceptable only because the tools are read-only,
use public ABS/RBA data, and require no secrets. Do not copy this unauthenticated
pattern for private APIs, paid APIs, account data, or write-capable tools.

Operational rules:

- Treat `mcp-session-id` as transport state, not identity or authorisation.
- Keep CORS non-credentialed unless future authentication is deliberately added.
- Keep local HTTP testing bound to `127.0.0.1`; binding `0.0.0.0` is only for
  the hosted container entrypoint.
- Keep outbound network access restricted to the existing ABS and RBA HTTPS
  endpoints.
- Do not add arbitrary URLs, callback URLs, proxy URLs, or user-supplied
  hostnames.
- Do not log request bodies or future session configuration.
- Monitor CPU, memory, request volume, and large dataset calls. Prefer bounded
  examples using `last_n`, `start`, and `end`.

MCP HTTP deployments should validate browser `Origin` headers to reduce DNS
rebinding risk. Smithery's current custom-container guidance requires browser
CORS support, so verify the live Smithery request origins before adding a strict
allowlist. If future private or write-capable tools are added, strict Origin
validation and authentication must be implemented before public deployment.

## Troubleshooting

- Build failure: check whether the failure is in Docker, `uv build`, or runtime
  dependency installation.
- Scan failure: confirm the path is `/mcp`, not `/`.
- Missing tools: confirm the container entrypoint is `ausecon-mcp-http`, not the
  stdio command.
- 403 during scan: check whether any future WAF, bot filter, or Origin guard is
  blocking Smithery's scanner or Playground.
- Version fallback: pass `AUSECON_VERSION` as a build arg if Smithery supports
  it; otherwise the Dockerfile derives the version from `server.json`.

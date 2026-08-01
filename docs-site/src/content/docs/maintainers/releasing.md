---
title: Releasing
description: Release checklist for PyPI, GHCR, and MCP registry metadata.
---

The package version is derived from git tags via `hatch-vcs`. Do not manually edit a target version
in `pyproject.toml` when cutting a release.

## Checklist

1. Ensure the release-ready state is committed, including changelog updates.
2. Bump `server.json` so `version` and `packages[0].version` match the new `X.Y.Z`.
3. Confirm GitHub CodeQL default setup is disabled when the checked-in advanced CodeQL workflow is
   enabled; otherwise GitHub rejects the workflow's CodeQL SARIF upload.
4. Confirm the hygiene test passes; it enforces that `server.json` matches the top changelog entry.
5. Create a git tag in the repository's `vX.Y.Z` format on the intended release commit.
6. Push the branch and tag to GitHub.
7. *(Optional)* Re-run the eval (`uv run --group evals python -m evals.run_eval`), commit `evals/results/`, and regenerate the evaluation page (`scripts/update_docs_eval.py`).
8. Allow the release workflow to build and publish the tagged version.
9. Draft GitHub Release notes from that tag.
10. The release workflow republishes to the MCP registry automatically (its `mcp-registry` job
    stamps the tag version into `server.json` and publishes via GitHub OIDC). Verify the new
    version appears in the registry; `mcp-publisher publish` remains available as a manual
    fallback if that job fails.

This repository's existing releases use lightweight tags:

```bash
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

Once the tag is on GitHub, create the release in the GitHub interface under
`Releases` -> `Draft a new release`.

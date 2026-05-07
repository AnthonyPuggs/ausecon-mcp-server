---
title: Releasing
description: Release checklist for PyPI, GHCR, and MCP registry metadata.
---

The package version is derived from git tags via `hatch-vcs`. Do not manually edit a target version
in `pyproject.toml` when cutting a release.

## Checklist

1. Ensure the release-ready state is committed, including changelog updates.
2. Bump `server.json` so `version` and `packages[0].version` match the new `X.Y.Z`.
3. Confirm the hygiene test passes; it enforces that `server.json` matches the top changelog entry.
4. Create a git tag in the repository's `vX.Y.Z` format on the intended release commit.
5. Push the branch and tag to GitHub.
6. Allow the release workflow to build and publish the tagged version.
7. Draft GitHub Release notes from that tag.
8. Republish `server.json` to the MCP registry with `mcp-publisher publish`.

This repository's existing releases use lightweight tags:

```bash
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

Once the tag is on GitHub, create the release in the GitHub interface under
`Releases` -> `Draft a new release`.

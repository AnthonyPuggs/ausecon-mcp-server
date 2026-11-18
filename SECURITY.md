# Security Policy

ausecon is an independent, open-source project maintained by one person. This page explains how to
report a security problem and what to expect afterwards.

## Supported versions

| Version | Supported |
| --- | --- |
| Hosted server (`mcp.auseconmcp.com`) | Yes. It runs the latest release. |
| Latest minor release on PyPI | Yes |
| Older releases | No. Please upgrade first. |

Fixes are released as a new patch version on PyPI and deployed to the hosted server. They are not
backported to older minor versions.

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security problem.**

Report it privately through GitHub instead:
[Report a vulnerability](https://github.com/AnthonyPuggs/ausecon-mcp-server/security/advisories/new).

Helpful details to include:

- the affected component (hosted server, PyPI package, or container image) and its version;
- the tool call or request that triggers the problem, with its arguments;
- what happens, and what you expected to happen;
- any proof of concept, logs, or stack traces.

## What to expect

- An acknowledgement within 7 days.
- An initial assessment, and a rough timeline for a fix, within 14 days of the acknowledgement.
- Updates through the private advisory while a fix is in progress.
- Once a fix is released, the advisory is published. You are credited in it unless you would rather
  not be.

These are best-effort targets for a solo-maintained project. There is no bug bounty.

## Scope

In scope:

- the `ausecon-mcp-server` Python package and its container image;
- the hosted MCP server at `https://mcp.auseconmcp.com/mcp`
  (`https://ausecon-mcp-server.onrender.com/mcp`);
- how the server validates tool arguments, builds upstream requests, parses ABS, RBA and APRA
  responses (SDMX, CSV, XLSX), and reads and writes its cache.

Examples of what matters here: requests reaching hosts other than the ABS, RBA or APRA, cache
poisoning, path traversal in the cache directory, crafted input or upstream files that crash the
server or exhaust its memory, or ways around the hosted server's request limits (body size and
time limits, the cap on concurrent tool calls) that let a few clients lock out everyone else. The
limits are described under
[HTTP safety](https://auseconmcp.com/operations/caching-and-logging/#http-safety).

Out of scope:

- the ABS, RBA and APRA services themselves (report those to the agency concerned);
- Render and Vercel infrastructure (report those to the provider);
- the documentation site's content and its Vercel analytics;
- findings that rely only on volume, such as rate limiting or denial of service through
  sheer request volume.

## Testing the hosted server

The hosted server is a single small instance that other people rely on, and its bandwidth is paid
for by the maintainer. Please:

- do not load-test it or run automated scanners against it;
- keep testing to the minimum needed to show the problem;
- where you can, reproduce issues locally with `uvx ausecon-mcp-server` or the container image.

## Privacy

For what the server collects and logs, see the
[privacy policy](https://auseconmcp.com/privacy/).

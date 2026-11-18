---
title: Privacy Policy
description: What the hosted ausecon MCP server, the installable package, and this documentation site collect, and what they do with it.
---

Last updated: 12 November 2026.

ausecon is an independent, open-source project. It is not operated by, affiliated with, or endorsed
by the Australian Bureau of Statistics (ABS), the Reserve Bank of Australia (RBA), or the Australian
Prudential Regulation Authority (APRA). It retrieves data those agencies publish openly.

This policy covers three things:

- the **hosted MCP server** at `https://ausecon-mcp-server.onrender.com/mcp` (also reachable as
  `https://mcp.auseconmcp.com/mcp`), which is what you use when you add ausecon as a connector in
  Claude or another client;
- the **installable package** (`ausecon-mcp-server` on PyPI, and its container image), which you run
  on your own machine;
- this **documentation site** at `auseconmcp.com`.

## The short version

- There are no accounts, no sign-in, no API keys and no cookies.
- The server does not collect personal information, and does not sell, rent or share anything about
  you.
- The server keeps no record of who called it. Its logs record which public dataset was fetched,
  and the error message when a call fails, but not who made the request.
- The only things sent on to the ABS, RBA or APRA are dataset and series identifiers and date
  ranges.

## Hosted MCP server

### What the server receives

When your AI assistant calls an ausecon tool, the server receives the tool name and its arguments.
These are things like a dataset identifier (`CPI`), a series identifier, a date range, a number of
observations, or a short search phrase such as "cash rate". Your assistant chooses these arguments.
The server never sees your conversation, your files or your account details.

Because the assistant writes the arguments, a search phrase could in principle contain text from
your conversation. The server uses that text only to answer the request, and keeps it only in the
error log described under [Logging](#logging) if the call fails.

Like any website, the server also receives standard connection information, such as your client's IP
address and request headers. These are handled by the hosting provider (see below).

### What the server does with it

The server uses each request only to answer it:

- **Search and discovery tools** (`search_datasets`, `list_catalogue`, `list_economic_concepts`,
  `describe_dataset`) match your request against a catalogue built into the server. Nothing is sent
  anywhere else.
- **Retrieval tools** request the matching public data from the ABS, RBA or APRA. Those requests
  contain only dataset and series identifiers and date bounds. They come from the server, so the
  agencies see the server's address, not yours.
- **The release calendar** (`list_release_events`) is read from fixed public ABS and RBA pages.

### Logging

The server writes operational logs so the maintainer can see whether upstream sources are working.
A log line records the event (for example `request.success`), the source (`abs`, `rba` or `apra`),
the public dataset identifier, the upstream URL, the HTTP status, the duration and the response size.

The server does not log:

- HTTP access logs (they are turned off);
- client IP addresses or request headers;
- request or response bodies;
- the arguments of successful tool calls, including search phrases.

When a tool call fails, the error is logged so the maintainer can fix the cause. The error message
can include the argument that caused it, for example an unrecognised concept name. These error logs
are never linked to a client's IP address or identity.

### Caching

To avoid fetching the same public data repeatedly, the server keeps copies of ABS, RBA and APRA
responses in memory and on disk. A copy is treated as fresh for up to an hour. An older copy may be
returned, clearly marked `stale`, if a source is temporarily unavailable. The cache holds only public
statistical data. It holds nothing about who requested it.

The hosted server's cache lives on the hosting provider's temporary storage, which is cleared
whenever the service is redeployed or restarted.

### Sessions

The MCP protocol gives each connection a session identifier (`mcp-session-id`). It is used only to
route your client's requests and is not linked to any identity. It is not authentication, and it is
held in memory only.

### Hosting provider

The hosted server runs on [Render](https://render.com). Render handles network traffic to the
server, and may keep its own infrastructure and request logs under its own terms; see
[Render's privacy policy](https://render.com/privacy). The ausecon project does not add tracking,
analytics or advertising to the hosted server, and does not export its logs to any other service.

## Installable package

When you install ausecon from PyPI or run its container image yourself, it runs entirely on your
machine. It contacts only the public ABS, RBA and APRA endpoints needed to answer your requests. It
sends no telemetry or usage data to the ausecon project or anyone else.

Its cache is stored in your user cache directory (`~/.cache/ausecon-mcp/` on Linux,
`~/Library/Caches/ausecon-mcp/` on macOS). You can disable it with `AUSECON_CACHE_DISABLED=1`.

## Documentation site

This site is hosted on [Vercel](https://vercel.com) and uses Vercel Web Analytics and Speed
Insights. They measure page views and page performance in aggregate, so the maintainer can see which
pages are useful and whether the site is fast. Query strings and URL fragments are removed before
performance data is sent. See [Vercel's privacy policy](https://vercel.com/legal/privacy-policy) for
how Vercel processes this data.

## Data sharing and retention

ausecon does not sell, rent or trade any data. Apart from the hosting providers named above, it
shares nothing with third parties. The only data sent to the ABS, RBA or APRA is the dataset
identifiers and date ranges described above.

Cached public data is kept for as long as the cache needs it and is cleared on redeploy.
Operational logs are kept only for as long as the hosting provider's log retention for the service.

## Children

ausecon is a statistical data service. It is not directed at children and does not knowingly
collect information from anyone.

## Changes to this policy

If this policy changes, the new version will be published on this page with a new "Last updated"
date. The full history is in the
[project repository](https://github.com/AnthonyPuggs/ausecon-mcp-server/commits/main/docs-site/src/content/docs/privacy.md).

## Contact

For privacy questions or requests, open an issue at
[github.com/AnthonyPuggs/ausecon-mcp-server/issues](https://github.com/AnthonyPuggs/ausecon-mcp-server/issues).

To report a security vulnerability, do not open a public issue. Use the private reporting process in
the project's
[security policy](https://github.com/AnthonyPuggs/ausecon-mcp-server/security/policy).

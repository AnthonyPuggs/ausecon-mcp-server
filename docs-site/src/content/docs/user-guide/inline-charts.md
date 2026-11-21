---
title: Inline Charts
description: How MCP Apps clients such as Claude show retrieval results as an interactive chart.
---

In clients that support [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps),
results from the five retrieval tools are shown as an interactive chart in the conversation, next
to the tool call: `get_economic_series`, `get_derived_series`, `get_rba_table`, `get_abs_data` and
`get_apra_data`. Every other client receives the same JSON response as before.

<video controls muted playsinline loop preload="metadata" poster="/media/inline-chart-demo-poster.jpg" width="1000" style="width: 100%; height: auto; border-radius: 8px;" aria-label="Claude answering a question about the household saving ratio and the cash rate with one interactive chart">
  <source src="/media/inline-chart-demo.mp4" type="video/mp4" />
</video>

*Asking Claude "How has the household saving ratio moved alongside the cash rate since 2019?"
returns ABS and RBA data in one chart. Hovering shows each series' value, with its own period
when it differs from the date under the pointer.*

## Where charts appear

| Client | What you see |
| --- | --- |
| Claude on the web, desktop and mobile, with the [hosted server](/getting-started/) added as a connector | The interactive chart. This is the setup the chart has been tested on. |
| Other MCP Apps clients, and Claude Desktop running the server locally | Should show the chart, but these are not yet tested. |
| Claude Code, Cursor, Codex, VS Code and other text-only clients | The JSON response, unchanged. |

## Getting a chart

Ask for an indicator in ordinary language:

```text
Show me trimmed mean inflation since 2015.
```

The chart shows up to eight series. A wider result, such as a whole RBA table or an ABS dataflow
without a key, shows a one-line message instead: ask for fewer series to get a chart. For example,
name the series you want, or ask for a specific RBA series ID, ABS key or APRA table.

```text
Chart the 2-year and 10-year government bond yields from RBA table F2 since 2020.
```

To compare indicators from different sources, ask for them together. `get_economic_series` takes a
list of up to eight concepts and returns them in one result, so they appear on one chart:

```text
How have the cash rate, mortgage rates and the 10-year bond yield moved since 2019?
```

<img src="/media/combined-rates-chart.webp" width="1132" height="1110" loading="lazy" style="width: 100%; height: auto; border-radius: 8px;" alt="Claude answering the question above with one chart of the RBA cash rate target, the outstanding owner-occupier mortgage rate and the 10-year government bond yield since 2019, on a single per cent axis, with one source line each for RBA tables A2, F6 and F17" />

Series in the same unit share one axis, as these three rates do; series in different units get
their own panel within the same chart.

## What the chart shows

- **Header:** the source, dataset and frequency, and the series name. A combined result names
  each source (for example `ABS · RBA`) and the series it compares.
- **Headline:** for a single series, the latest value, its date, and the change from the
  previous observation. Changes in a per cent series are given in percentage points (`pts`).
- **Line chart:** hover over the chart, or focus it and use the arrow keys, to read every series'
  value at a date. When series have different frequencies, each shows the value in effect at that
  date, with its own period in brackets when it differs (for example `Mortgage rate (Nov 2022)`
  under a cash rate decision date).
- **Event-driven series** such as the cash rate target are drawn as steps. Each value holds until
  the next change and runs through to the retrieval date.
- **Units:** series with different units go in separate panels, never on a second axis.
- **Notices:** cached data served while the source was unavailable, truncated results and source
  warnings appear above the chart. Known series breaks are marked with a dashed vertical line.
- **Data table:** collapsed by default, showing the most recent 400 dates. Series with different
  frequencies get a table each, captioned by frequency (for example `As announced`, `Monthly` and
  `Daily`).
- **Single-date results**, such as the latest value of each series, appear as a list of values
  instead of a chart.
- **Footer:** publication and retrieval dates and a link to the source file, one line per source
  for a combined result.

The chart follows your client's light or dark theme.

## How the model treats the chart

When your client supports MCP Apps and the result has been charted, the tool result tells the
model that the data is already on screen, in a `metadata.chart_note` field. The result stays a
single JSON document, so code that reads it as data still works. The note states what is on screen
and leaves the decision to the model, which usually describes the data in prose rather than
drawing a second chart of the same series. To get a different chart, such as trimmed mean against
headline CPI, ask for it explicitly.

## Privacy and security

The chart is a single self-contained HTML page that the server publishes as the
`ui://ausecon/series-chart.html` resource. Your client runs it in a sandboxed frame. It loads
nothing from the network and only displays the data already in the tool result.

The chart may pass your client a short summary of what it is showing, such as the series names
and the latest value, so the model can refer to the chart in later turns. That summary stays
within your client and is never sent to the server. See the [privacy policy](/privacy/) for what
the hosted server logs.

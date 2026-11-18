---
title: Inline Charts
description: How MCP Apps clients such as claude.ai show retrieval results as an interactive chart.
---

In clients that support [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps),
results from the five retrieval tools are shown as an interactive chart in the conversation, next
to the tool call: `get_economic_series`, `get_derived_series`, `get_rba_table`, `get_abs_data` and
`get_apra_data`. Every other client receives the same JSON response as before.

## Where charts appear

| Client | What you see |
| --- | --- |
| claude.ai, connected to the [hosted server](/getting-started/) | The interactive chart. This is the setup the chart has been tested on. |
| Other MCP Apps clients, such as Claude Desktop | Should show the chart, but these are not yet tested. |
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

## What the chart shows

- **Header:** the source, dataset and frequency, and the series name.
- **Headline:** for a single series, the latest value, its date, and the change from the
  previous observation. Changes in a per cent series are given in percentage points (`pts`).
- **Line chart:** hover over the chart, or focus it and use the arrow keys, to read every series'
  value at a date.
- **Event-driven series** such as the cash rate target are drawn as steps. Each value holds until
  the next change and runs through to the retrieval date.
- **Units:** series with different units go in separate panels, never on a second axis.
- **Notices:** cached data served while the source was unavailable, truncated results and source
  warnings appear above the chart. Known series breaks are marked with a dashed vertical line.
- **Data table:** collapsed by default, showing the most recent 400 dates.
- **Footer:** publication and retrieval dates and a link to the source file.

The chart follows your client's light or dark theme.

## How the model treats the chart

When your client supports MCP Apps and the result has been charted, the tool result tells the
model that the data is already on screen. The model then describes the data in prose, without
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

from __future__ import annotations

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="summarise_latest_inflation",
        description=(
            "Summarise the most recent Australian headline and trimmed-mean CPI prints "
            "and compare them to the RBA's 2–3% target band."
        ),
    )
    def summarise_latest_inflation(months: int = 12) -> str:
        return (
            f"You are helping the user understand Australian inflation over the last "
            f"{months} months.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            '1. Call `get_economic_series` with concept="headline_cpi".\n'
            '2. Call `get_economic_series` with concept="trimmed_mean_inflation".\n'
            "3. If the user has given a start date, pass it as `start`; otherwise leave it "
            "unset and take the most recent observations from the returned series.\n"
            "\n"
            "Then write a tight summary that covers:\n"
            "- the latest headline CPI year-ended change and its observation date,\n"
            "- the latest trimmed-mean CPI year-ended change and its observation date,\n"
            "- whether each measure sits inside, above, or below the RBA 2–3% target band,\n"
            "- one sentence on direction of travel over the requested window.\n"
            "\n"
            "Do not fabricate numbers. If a series is missing or sparse, say so plainly."
        )

    @mcp.prompt(
        name="compare_cash_rate_to_cpi",
        description=(
            "Narrate the relationship between the RBA cash rate target and headline CPI "
            "over a user-specified window."
        ),
    )
    def compare_cash_rate_to_cpi(start: str, end: str | None = None) -> str:
        end_clause = f"up to {end}" if end else "through to the most recent observation"
        return (
            "You are helping the user see how Australian monetary policy has interacted "
            f"with headline inflation from {start} {end_clause}.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            f'1. Call `get_economic_series` with concept="cash_rate_target", start="{start}"'
            + (f', end="{end}"' if end else "")
            + ".\n"
            f'2. Call `get_economic_series` with concept="headline_cpi", start="{start}"'
            + (f', end="{end}"' if end else "")
            + ".\n"
            "\n"
            "Then narrate the relationship in 4–6 sentences:\n"
            "- describe the path of the cash rate over the window,\n"
            "- describe the path of headline CPI (year-ended) over the same window,\n"
            "- call out obvious leads/lags between policy changes and inflation outcomes,\n"
            "- avoid causal claims that are not clearly supported by the data shown.\n"
            "\n"
            "Report real figures from the tool responses. Do not invent numbers."
        )

    @mcp.prompt(
        name="macro_snapshot",
        description=(
            "Produce a tight snapshot of the Australian macro backdrop: cash rate, "
            "headline and trimmed-mean CPI, and real GDP growth."
        ),
    )
    def macro_snapshot(as_of: str | None = None) -> str:
        as_of_clause = f"as of {as_of}" if as_of else "as of the most recent observations available"
        return (
            f"Build an Australian macro snapshot {as_of_clause}.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            '1. `get_economic_series` concept="cash_rate_target".\n'
            '2. `get_economic_series` concept="headline_cpi".\n'
            '3. `get_economic_series` concept="trimmed_mean_inflation".\n'
            '4. `get_economic_series` concept="gdp_growth".\n'
            "\n"
            "Present the results as a compact markdown table with columns:\n"
            "`Indicator | Latest value | As of | Frequency`.\n"
            "Use the exact values and observation dates returned by the tools.\n"
            "Then add two sentences of context: one on prices, one on activity."
        )

    @mcp.prompt(
        name="living_costs_vs_cpi",
        description=(
            "Compare Selected Living Cost Indexes (SLCI) across household types "
            "against headline CPI to show cost-of-living divergence."
        ),
    )
    def living_costs_vs_cpi(start: str | None = None) -> str:
        start_clause = f'start="{start}"' if start else "the default window"
        return (
            "The user wants to see how cost-of-living pressures differ across "
            "Australian household types compared with the headline CPI. "
            "SLCI weights reflect actual spending patterns for each household "
            "type, so the series can diverge materially from CPI.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            f'1. Call `get_abs_data` with dataflow_id="SLCI" and {start_clause} '
            "to retrieve Selected Living Cost Indexes across household types.\n"
            f'2. Call `get_economic_series` with concept="headline_cpi" '
            f"using {start_clause} for the CPI benchmark.\n"
            "\n"
            "Then write 4-6 sentences covering:\n"
            "- the SLCI household type with the highest annual change and its value,\n"
            "- the household type with the lowest, and the gap between them,\n"
            "- how both compare to headline CPI over the same window,\n"
            "- a plain-language interpretation (which households are feeling "
            "the most cost-of-living pressure and why).\n"
            "\n"
            "Do not fabricate numbers. Use the exact values the tools return."
        )

    @mcp.prompt(
        name="construction_pipeline",
        description=(
            "Summarise the Australian construction pipeline across engineering, "
            "residential, and non-residential activity."
        ),
    )
    def construction_pipeline(last_n: int = 8) -> str:
        return (
            f"Build a snapshot of the Australian construction pipeline using "
            f"the last {last_n} quarters of activity data.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            f'1. Call `get_abs_data` with dataflow_id="CWD", last_n={last_n} '
            "for total construction work done.\n"
            f'2. Call `get_abs_data` with dataflow_id="EWD", last_n={last_n} '
            "for engineering construction work done (infrastructure and "
            "resources investment).\n"
            f'3. Call `get_abs_data` with dataflow_id="BUILDING_ACTIVITY", '
            f"last_n={last_n} for residential and non-residential building.\n"
            "\n"
            "Then write a tight summary covering:\n"
            "- the latest quarterly value for each series and the "
            "year-ended change,\n"
            "- which pipeline component is strongest and which is weakest,\n"
            "- one sentence on what this mix implies for near-term "
            "construction employment and materials demand.\n"
            "\n"
            "Report real values only. If a series is sparse or missing, "
            "say so plainly."
        )

    @mcp.prompt(
        name="labour_slack_snapshot",
        description=(
            "Summarise Australian labour-market slack using the unemployment and "
            "underemployment rates over a recent window."
        ),
    )
    def labour_slack_snapshot(last_n: int = 12) -> str:
        return (
            "The user wants a clear read on Australian labour-market slack over "
            f"the last {last_n} monthly observations.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            f'1. Call `get_economic_series` with concept="unemployment_rate", last_n={last_n}.\n'
            f'2. Call `get_economic_series` with concept="underemployment_rate", '
            f"last_n={last_n}.\n"
            "\n"
            "Then write 3-5 sentences covering:\n"
            "- the latest unemployment rate and its observation date,\n"
            "- the latest underemployment rate and its observation date,\n"
            "- the combined underutilisation signal and whether slack is "
            "tightening or loosening,\n"
            "- one sentence of context on what that implies for wages pressure.\n"
            "\n"
            "Use only the values returned by the tools."
        )

    @mcp.prompt(
        name="yield_curve_snapshot",
        description=(
            "Compare the 3-year and 10-year Australian Government Security yields "
            "over a recent window to describe the curve shape."
        ),
    )
    def yield_curve_snapshot(last_n: int = 60) -> str:
        return (
            f"Build a snapshot of the Australian Government Security yield curve "
            f"using the last {last_n} daily observations.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            f'1. Call `get_economic_series` with concept="government_bond_yield_3y", '
            f"last_n={last_n}.\n"
            f'2. Call `get_economic_series` with concept="government_bond_yield_10y", '
            f"last_n={last_n}.\n"
            "\n"
            "Then write 3-5 sentences covering:\n"
            "- the latest 3y and 10y yields and their observation date,\n"
            "- the 10y-minus-3y spread and whether the curve is positively "
            "sloped, flat, or inverted,\n"
            "- how the curve has shifted over the window shown.\n"
            "\n"
            "Report only the values the tools return."
        )

    @mcp.prompt(
        name="discover_dataset",
        description=(
            "Find and recommend the best ABS datasets or RBA tables for a given economic topic."
        ),
    )
    def discover_dataset(topic: str) -> str:
        return (
            f"The user wants to analyse Australian economic data on the topic: {topic!r}.\n"
            "\n"
            "Do the following using tools from this MCP server:\n"
            f"1. Call `search_datasets` with query={topic!r}.\n"
            "2. If the top results are RBA tables, also call `list_rba_tables` with a "
            '`category` argument that matches the topic (for example, "inflation", '
            '"monetary_policy", "labour"). Leave `include_discontinued` as the default.\n'
            "3. Inspect the top candidates and pick the two most relevant.\n"
            "\n"
            "Return a short recommendation:\n"
            "- name each candidate with its id and source,\n"
            "- explain in one sentence why each is relevant to the topic,\n"
            "- suggest the next tool call the user should make (usually "
            "`get_abs_dataset_structure` for ABS candidates, or `get_rba_table` for RBA "
            "candidates)."
        )

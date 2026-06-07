from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import respx
from httpx import Response

from ausecon_mcp.releases import (
    ABS_RELEASE_URL,
    RBA_RELEASE_URL,
    ReleaseProvider,
    build_apra_release_events,
    filter_release_events,
    parse_abs_release_events,
    parse_rba_release_events,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_abs_release_events_extracts_future_release_rows() -> None:
    html = (FIXTURES / "abs_release_calendar_sample.html").read_text(encoding="utf-8")

    events = parse_abs_release_events(
        html,
        source_url="https://www.abs.gov.au/release-calendar/future-releases",
    )

    assert events[0] == {
        "source": "abs",
        "event_kind": "official_calendar",
        "date_source": "official_page",
        "release_name": "Consumer Price Index, Australia",
        "release_datetime": "2026-05-27T11:30:00",
        "timezone": "Australia/Canberra",
        "reference_period": "April 2026",
        "matched_catalogue_ids": ["CPI"],
        "upstream_url": "https://www.abs.gov.au/release-calendar/future-releases",
    }


def test_parse_rba_release_events_extracts_schedule_rows() -> None:
    html = (FIXTURES / "rba_release_schedule_sample.html").read_text(encoding="utf-8")

    events = parse_rba_release_events(
        html,
        source_url="https://www.rba.gov.au/schedules-events/",
        today=date(2026, 5, 23),
    )

    assert events[0]["source"] == "rba"
    assert events[0]["event_kind"] == "official_calendar"
    assert events[0]["date_source"] == "official_page"
    assert events[0]["release_name"] == "Reserve Bank of Australia Balance Sheet"
    assert events[0]["release_datetime"] == "2026-05-29T16:30:00"
    assert events[0]["timezone"] == "Australia/Sydney"
    assert events[0]["matched_catalogue_ids"] == ["a1"]


def test_build_apra_release_events_uses_curated_cadence_and_seed_freshness() -> None:
    catalogue = {
        "ADI_MONTHLY": {
            "id": "ADI_MONTHLY",
            "name": "Monthly Authorised Deposit-taking Institution Statistics",
            "frequency": "Monthly",
            "audit": {
                "upstream_url": "https://www.apra.gov.au/monthly-test",
                "last_audited": "2026-05-18",
            },
        }
    }

    events = build_apra_release_events(
        catalogue,
        today=date(2026, 5, 23),
        seed_checked_at="2026-05-20T00:00:00Z",
    )

    assert events == [
        {
            "source": "apra",
            "event_kind": "expected_release",
            "date_source": "cadence_estimate",
            "release_name": "Monthly Authorised Deposit-taking Institution Statistics",
            "release_datetime": "2026-05-29T00:00:00",
            "timezone": "Australia/Sydney",
            "reference_period": "Monthly cadence; seed checked 2026-05-20T00:00:00Z",
            "cadence": "Monthly",
            "seed_checked_at": "2026-05-20T00:00:00Z",
            "audit_last_audited": "2026-05-18",
            "governance_status": "ok",
            "governance_issues": [],
            "matched_catalogue_ids": ["ADI_MONTHLY"],
            "upstream_url": "https://www.apra.gov.au/monthly-test",
        }
    ]


def test_filter_release_events_applies_source_query_dates_and_limit() -> None:
    events = [
        {
            "source": "abs",
            "release_name": "Consumer Price Index, Australia",
            "release_datetime": "2026-05-27T11:30:00",
            "timezone": "Australia/Canberra",
            "reference_period": "April 2026",
            "matched_catalogue_ids": ["CPI"],
            "upstream_url": "https://www.abs.gov.au/release-calendar/future-releases",
        },
        {
            "source": "rba",
            "release_name": "Reserve Bank of Australia Balance Sheet",
            "release_datetime": "2026-05-29T16:30:00",
            "timezone": "Australia/Sydney",
            "reference_period": None,
            "matched_catalogue_ids": ["a1"],
            "upstream_url": "https://www.rba.gov.au/schedules-events/",
        },
    ]

    filtered = filter_release_events(
        events,
        source="rba",
        query="balance sheet",
        start_date="2026-05-28",
        end_date="2026-05-31",
        limit=1,
    )

    assert filtered == [events[1]]


@pytest.mark.asyncio
async def test_release_provider_fetches_official_abs_and_rba_pages_and_caches_results() -> None:
    abs_html = (FIXTURES / "abs_release_calendar_sample.html").read_text(encoding="utf-8")
    rba_html = (FIXTURES / "rba_release_schedule_sample.html").read_text(encoding="utf-8")
    provider = ReleaseProvider(today=date(2026, 5, 23))

    try:
        with respx.mock(assert_all_called=True) as router:
            abs_route = router.get(ABS_RELEASE_URL).mock(return_value=Response(200, text=abs_html))
            rba_route = router.get(RBA_RELEASE_URL).mock(return_value=Response(200, text=rba_html))

            first = await provider.list_events()
            second = await provider.list_events()
    finally:
        await provider.aclose()

    assert first == second
    assert abs_route.call_count == 1
    assert rba_route.call_count == 1
    assert any(
        event["source"] == "abs"
        and event["event_kind"] == "official_calendar"
        and event["date_source"] == "official_page"
        and event["release_name"] == "Consumer Price Index, Australia"
        and event["reference_period"] == "April 2026"
        for event in first
    )
    assert any(
        event["source"] == "rba"
        and event["release_name"] == "Reserve Bank of Australia Balance Sheet"
        for event in first
    )
    assert any(
        event["source"] == "apra"
        and event["event_kind"] == "expected_release"
        and event["date_source"] == "cadence_estimate"
        and event["governance_status"] in {"ok", "stale"}
        for event in first
    )


@pytest.mark.asyncio
async def test_release_provider_stamps_apra_rows_with_bundled_seed_freshness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    abs_html = (FIXTURES / "abs_release_calendar_sample.html").read_text(encoding="utf-8")
    rba_html = (FIXTURES / "rba_release_schedule_sample.html").read_text(encoding="utf-8")
    provider = ReleaseProvider(today=date(2026, 5, 23))
    monkeypatch.setattr(
        "ausecon_mcp.releases.apra_seed_checked_at",
        lambda: "2026-05-21T00:00:00Z",
        raising=False,
    )

    try:
        with respx.mock(assert_all_called=True) as router:
            router.get(ABS_RELEASE_URL).mock(return_value=Response(200, text=abs_html))
            router.get(RBA_RELEASE_URL).mock(return_value=Response(200, text=rba_html))

            events = await provider.list_events()
    finally:
        await provider.aclose()

    apra_reference_periods = [
        event["reference_period"] for event in events if event["source"] == "apra"
    ]
    assert apra_reference_periods
    assert all(
        reference_period.endswith("; seed checked 2026-05-21T00:00:00Z")
        for reference_period in apra_reference_periods
    )
    assert all(
        event["seed_checked_at"] == "2026-05-21T00:00:00Z"
        for event in events
        if event["source"] == "apra"
    )

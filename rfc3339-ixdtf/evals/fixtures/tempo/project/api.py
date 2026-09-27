"""Tempo event API: JSON serialization of scheduled events.

Run ``python3 api.py`` to print a sample ``GET /v1/events`` response.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import timeutil


@dataclass
class Event:
    id: str
    title: str
    start: datetime
    end: datetime
    reminder: timedelta = timedelta(minutes=15)
    all_day: date | None = None
    calendar: str | None = None
    source_seen_epoch: float | None = None
    created_at: datetime = field(default_factory=datetime.now)


def serialize(event: Event, received_at: datetime) -> dict:
    doc = {
        "id": event.id,
        "title": event.title,
        "start": timeutil.format_ixdtf(event.start, calendar=event.calendar),
        "start_utc": timeutil.format_utc(event.start),
        "end": timeutil.format_offset(event.end),
        "reminder_at": timeutil.format_reminder(event.start - event.reminder),
        "created_at": event.created_at.isoformat(timespec="seconds"),
        "received_at": timeutil.format_instant(received_at),
    }
    if event.all_day is not None:
        doc["all_day_date"] = event.all_day.isoformat()
    if event.source_seen_epoch is not None:
        doc["source_seen_at"] = timeutil.format_epoch(event.source_seen_epoch)
    return doc


def ingest(item: dict) -> Event:
    """Build an Event from a partner-feed record."""
    start = timeutil.parse_ixdtf(item["start"])
    end = timeutil.parse_ixdtf(item["end"])
    tz = ZoneInfo(start.zone) if start.zone else start.instant.tzinfo
    return Event(
        id=item["id"],
        title=item["title"],
        start=start.instant.astimezone(tz),
        end=end.instant.astimezone(tz),
        calendar=start.calendar,
        source_seen_epoch=item.get("seen"),
    )


PARTNER_FEED = [
    {
        "id": "evt_feed_0091",
        "title": "Berlin meetup",
        "start": "2026-04-02T18:00:00+02:00[Europe/Berlin]",
        "end": "2026-04-02T20:30:00+02:00[Europe/Berlin]",
        "seen": 1774540800.0,
    },
    {
        "id": "evt_feed_0092",
        "title": "Rosh Hashanah dinner",
        "start": "2026-09-11T19:00:00-07:00[America/Los_Angeles][u-ca=hebrew]",
        "end": "2026-09-11T22:00:00-07:00[America/Los_Angeles]",
        "seen": 1788000000.0,
    },
]


def sample_events() -> list[Event]:
    ny = ZoneInfo("America/New_York")
    ist = timezone(timedelta(hours=5, minutes=30))
    events = [
        Event(
            id="evt_0001",
            title="Quarterly planning",
            start=datetime(2026, 3, 14, 9, 30, tzinfo=ny),
            end=datetime(2026, 3, 14, 11, 0, tzinfo=ny),
        ),
        Event(
            id="evt_0002",
            title="Bangalore standup",
            start=datetime(2026, 5, 4, 10, 0, tzinfo=ist),
            end=datetime(2026, 5, 4, 10, 15, tzinfo=ist),
            reminder=timedelta(minutes=5),
        ),
        Event(
            id="evt_0003",
            title="Company offsite",
            start=datetime(2026, 6, 19, 0, 0, tzinfo=ny),
            end=datetime(2026, 6, 20, 0, 0, tzinfo=ny),
            all_day=date(2026, 6, 19),
        ),
    ]
    events.extend(ingest(item) for item in PARTNER_FEED)
    return events


def main() -> None:
    received_at = datetime.now(timezone.utc)
    body = {"events": [serialize(e, received_at) for e in sample_events()]}
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()

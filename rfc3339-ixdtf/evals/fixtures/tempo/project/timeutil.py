"""Timestamp helpers for the Tempo event scheduling service.

Producers use the ``format_*`` helpers; the ingest path uses
``parse_timestamp`` / ``parse_ixdtf`` for partner feeds.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

RFC3339_FMT = "%Y-%m-%dT%H:%M:%S%z"
REMINDER_FMT = "%Y-%m-%dT%H:%M"

LOCAL_TZ = datetime.now().astimezone().tzinfo

KNOWN_SUFFIX_KEYS = frozenset({"u-ca"})

_TS_RE = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
    r"[Tt]"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<frac>[0-9]+))?"
    r"(?P<offset>[Zz]|[+-][0-9]{2}:[0-9]{2})?$"
)
_TAG_RE = re.compile(r"\[(?P<crit>!?)(?P<key>[^\[\]=!]+)(?:=(?P<value>[^\[\]]+))?\]")


@dataclass(frozen=True)
class Stamp:
    instant: datetime
    zone: str | None = None
    calendar: str | None = None


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------

def format_instant(dt: datetime) -> str:
    """Render an aware datetime as a UTC instant with millisecond precision."""
    if dt.tzinfo is None:
        raise ValueError("format_instant requires an aware datetime")
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"


def format_utc(dt: datetime) -> str:
    """Second-precision UTC form used for sort keys and ``start_utc``."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_offset(dt: datetime) -> str:
    """Render a datetime with its own numeric UTC offset."""
    return dt.strftime(RFC3339_FMT)


def format_reminder(dt: datetime) -> str:
    """Reminders fire on minute boundaries, so drop sub-minute detail."""
    return dt.strftime(REMINDER_FMT) + dt.isoformat()[-6:]


def format_epoch(seconds: float) -> str:
    """Render a POSIX timestamp reported by an upstream feed."""
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(timespec="seconds")


def zone_label(tz: tzinfo) -> str:
    return getattr(tz, "key", None) or str(tz)


def format_ixdtf(dt: datetime, *, calendar: str | None = None) -> str:
    """Render ``dt`` with its offset plus a time-zone (and calendar) suffix."""
    if dt.tzinfo is None:
        raise ValueError("format_ixdtf requires an aware datetime")
    parts = [dt.isoformat(timespec="seconds"), f"[{zone_label(dt.tzinfo)}]"]
    if calendar:
        parts.append(f"[u-ca={calendar}]")
    return "".join(parts)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def _offset(text: str) -> tzinfo:
    if text in ("Z", "z"):
        return timezone.utc
    sign = -1 if text[0] == "-" else 1
    hours, minutes = int(text[1:3]), int(text[4:6])
    if hours > 23 or minutes > 59:
        raise ValueError(f"offset out of range: {text!r}")
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def parse_timestamp(text: str, default_tz: tzinfo | None = None) -> datetime:
    """Parse an RFC 3339 date-time into an aware datetime."""
    m = _TS_RE.match(text)
    if m is None:
        raise ValueError(f"invalid timestamp: {text!r}")
    micro = int((m["frac"] or "0")[:6].ljust(6, "0"))
    naive = datetime(
        int(m["year"]), int(m["month"]), int(m["day"]),
        int(m["hour"]), int(m["minute"]), int(m["second"]), micro,
    )
    if m["offset"] is None:
        return naive.replace(tzinfo=default_tz or LOCAL_TZ)
    return naive.replace(tzinfo=_offset(m["offset"]))


def parse_ixdtf(text: str) -> Stamp:
    """Parse an RFC 9557 (IXDTF) string: date-time plus optional suffix."""
    cut = text.find("[")
    head, tail = (text, "") if cut < 0 else (text[:cut], text[cut:])
    instant = parse_timestamp(head)

    zone: str | None = None
    zone_critical = False
    tags: dict[str, str] = {}
    pos = 0
    while pos < len(tail):
        m = _TAG_RE.match(tail, pos)
        if m is None:
            raise ValueError(f"malformed suffix in {text!r}")
        pos = m.end()
        critical, key, value = m["crit"] == "!", m["key"], m["value"]
        if value is None:
            if zone is not None or tags:
                raise ValueError(f"time zone must be the first suffix: {text!r}")
            zone, zone_critical = key, critical
            continue
        if key not in KNOWN_SUFFIX_KEYS:
            raise ValueError(f"unsupported suffix key {key!r}")
        tags.setdefault(key, value)

    if zone is not None:
        try:
            tz = _offset(zone) if zone[:1] in "+-" else ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError):
            if zone_critical:
                raise ValueError(f"unknown critical time zone {zone!r}") from None
            zone = None
        else:
            offset_known = head[-1] not in "Zz" and not head.endswith("-00:00")
            if zone_critical and offset_known:
                if instant.utcoffset() != instant.astimezone(tz).utcoffset():
                    raise ValueError(f"offset inconsistent with [!{zone}]")
    return Stamp(instant=instant, zone=zone, calendar=tags.get("u-ca"))

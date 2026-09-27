#!/usr/bin/env python3
"""Instant check for adapters that return a bare instant, not as-written fields.

Foundation's Date (and protobuf Timestamp, SQL timestamptz) keeps no offset, so the adapter
cannot report the vector "fields". Instead it adds "utc": "YYYY-MM-DDTHH:MM:SS.ffffff" to its
JSON answer. This script reads a run_vectors.py --json report and, for every ACCEPTED vector that
rfcdt can parse (valid or not), compares that UTC instant with the instant rfcdt derives from the
string (wall time minus offset). A leap second (second 60) matches either :59 (the value kept
as the last representable second) or the next second (rolled over); both are counted as
"leap-mapped", not as a wrong value, because the target type cannot hold second 60.

    python3 instant_check.py report.json [--tolerance-us 1000]

Output: one line per mismatch, then a summary. Differences below the tolerance are reported as
"lossy" (the target's precision), larger ones as WRONG VALUE.
"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import rfcdt  # noqa: E402

EPOCH = datetime(1970, 1, 1)


def expected_us(s):
    """Microseconds since 1970 (proleptic Gregorian) for the date-time part of s, or None."""
    for opts in ({}, {"allow_space_separator": True}):
        try:
            r = rfcdt.check(s, **opts) if opts else rfcdt.check(s)
        except TypeError:
            continue
        f = r.fields or {}
        if all(k in f for k in ("year", "month", "day", "hour", "minute", "second")) and "offset_minutes" in f:
            break
    else:
        return None
    try:
        y = f["year"]
        base = datetime(max(y, 1), f["month"], f["day"], f["hour"], f["minute"], min(f["second"], 59))
    except (ValueError, TypeError):
        return None
    us = int((base - EPOCH).total_seconds()) * 1_000_000
    if y == 0:
        us -= 366 * 86400 * 1_000_000
    frac = (f.get("secfrac") or "")[:6].ljust(6, "0")
    us += int(frac)
    us -= (f["offset_minutes"] or 0) * 60 * 1_000_000
    return us, f["second"] == 60


def parse_utc(u):
    neg = u.startswith("-")
    body = u[1:] if neg else u
    date, time = body.split("T")
    y, mo, d = (int(x) for x in date.split("-"))
    hms, _, frac = time.partition(".")
    h, mi, s = (int(x) for x in hms.split(":"))
    y = -y if neg else y
    # days from civil (proleptic Gregorian), valid for any year
    yy = y - (mo <= 2)
    era = (yy if yy >= 0 else yy - 399) // 400
    yoe = yy - era * 400
    doy = (153 * (mo + (-3 if mo > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    days = era * 146097 + doe - 719468
    return ((days * 86400 + h * 3600 + mi * 60 + s) * 1_000_000) + int(frac[:6].ljust(6, "0") or 0)


def main():
    path = sys.argv[1]
    tol = 1000
    if "--tolerance-us" in sys.argv:
        tol = int(sys.argv[sys.argv.index("--tolerance-us") + 1])
    rep = json.load(open(path))
    n = wrong = lossy = leapm = 0
    for r in rep["results"]:
        out = r.get("output") or {}
        if not out.get("ok") or "utc" not in out:
            continue
        e = expected_us(r["input"])
        if e is None:
            continue
        exp, leap = e
        n += 1
        got = parse_utc(out["utc"])
        diff = got - exp
        if leap and (0 <= diff < tol or 0 <= diff - 1_000_000 < tol):
            leapm += 1
            continue
        if diff == 0:
            continue
        kind = "lossy" if abs(diff) < tol else "WRONG VALUE"
        if kind == "lossy":
            lossy += 1
        else:
            wrong += 1
        print(f"{kind:11} {r['id']:16} [{r['status']}] {json.dumps(r['input'])} -> {out['utc']}Z (diff {diff/1e6:+.6f} s)")
    print(f"instant check: {n} accepted vectors compared, {wrong} WRONG VALUE, {lossy} lossy (< {tol} us), "
          f"{leapm} leap seconds mapped to :59 or the next second")


if __name__ == "__main__":
    main()

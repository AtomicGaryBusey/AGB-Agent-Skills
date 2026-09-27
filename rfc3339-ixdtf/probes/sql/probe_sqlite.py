#!/usr/bin/env python3
"""Probe SQLite's date/time functions (through Python's sqlite3) against RFC 3339.

    TZ=America/New_York python3 probe_sqlite.py probe    > consumers.jsonl
    TZ=America/New_York python3 probe_sqlite.py produce  > producers.jsonl
    python3 probe_sqlite.py adapter datetime|strftime|julianday|unixepoch|strict
        (run_vectors.py adapter: one string on stdin, or JSON lines with RFCDT_BATCH=1)
    python3 probe_sqlite.py list     (adapter keys: <key>\t<target-kind>)

SQLite has no timestamp type.  Its functions read "time values" (ISO-8601-like
text, Julian day numbers, or unix seconds with a modifier), apply any offset,
and return UTC.  NULL means "not a time value".  The adapter prints
{"ok": ..., "utc": "<engine UTC>"}; "utc" is an extra key that instant_check.py
compares with the true instant.  Standard library only.
"""
import json
import sqlite3
import sys

from common import classify, compare_instant, expected_utc, load_inputs, rfcdt_fields, serve_adapter, effective_cat

CON = sqlite3.connect(":memory:")

# name -> (SQL, how to turn the result into a UTC ISO text, precision digits)
APIS = {
    "datetime": ("SELECT datetime(?)", lambda v: v, 0),
    "strftime": ("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', ?)", lambda v: v[:-1], 3),
    "julianday": ("SELECT julianday(?)", None, 3),
    "unixepoch": ("SELECT unixepoch(?, 'subsec')", None, 3),
}
LABEL = {
    "datetime": "SQLite `datetime(s)`",
    "strftime": "SQLite `strftime('%Y-%m-%dT%H:%M:%fZ', s)`",
    "julianday": "SQLite `julianday(s)`",
    "unixepoch": "SQLite `unixepoch(s, 'subsec')`",
}


def run(api, s):
    sql, conv, prec = APIS[api]
    try:
        v = CON.execute(sql, (s,)).fetchone()[0]
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if v is None:
        return {"ok": False, "value": None}
    if conv is None:
        # numeric result: let SQLite render it back to UTC text (millisecond precision)
        fn = "julianday" if api == "julianday" else "unixepoch"
        mod = "" if api == "julianday" else ", 'unixepoch'"
        utc = CON.execute(f"SELECT strftime('%Y-%m-%dT%H:%M:%f', ?{mod})", (v,)).fetchone()[0]
    else:
        utc = conv(v)
    return {"ok": True, "value": v, "utc": utc.replace(" ", "T") if utc else None, "prec": prec}


def probe():
    for inp in load_inputs():
        f = rfcdt_fields(inp["s"], "ixdtf" if inp["cat"].startswith("ixdtf") else "rfc3339")
        exp, frac = expected_utc(f)
        for api in APIS:
            r = run(api, inp["s"])
            cmp = compare_instant(exp, frac, r.get("utc"), r.get("prec", 0)) if r["ok"] else None
            # datetime() has whole-second precision by design: count only whole-second differences
            if api == "datetime" and cmp == "WRONG" and exp and r.get("utc") and exp[:19] == r["utc"][:19]:
                cmp = "lossy"
            print(json.dumps({"api": LABEL[api], "id": inp["id"], "s": inp["s"], "cat": inp["cat"],
                              "expected_utc": exp, "cmp": cmp,
                              "verdict": classify(effective_cat(inp), r["ok"], cmp), **r}, ensure_ascii=False))


PRODUCERS = [
    ("datetime('now')", "SELECT datetime('now')"),
    ("strftime('%Y-%m-%dT%H:%M:%SZ','now')", "SELECT strftime('%Y-%m-%dT%H:%M:%SZ','now')"),
    ("strftime('%Y-%m-%dT%H:%M:%fZ','now')", "SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')"),
    ("CURRENT_TIMESTAMP", "SELECT CURRENT_TIMESTAMP"),
    ("datetime('now','localtime')", "SELECT datetime('now','localtime')"),
    ("strftime('%Y-%m-%dT%H:%M:%SZ','now','localtime') (literal Z on local time)",
     "SELECT strftime('%Y-%m-%dT%H:%M:%SZ','now','localtime')"),
    ("datetime('2026-09-24T14:00:00+02:00')", "SELECT datetime('2026-09-24T14:00:00+02:00')"),
    ("strftime('%Y-%m-%dT%H:%M:%fZ','2026-09-24T12:00:00.123456Z')",
     "SELECT strftime('%Y-%m-%dT%H:%M:%fZ','2026-09-24T12:00:00.123456Z')"),
    ("strftime('%Y-%m-%dT%H:%M:%fZ','2026-09-24T12:00:00.9999Z') (rounding?)",
     "SELECT strftime('%Y-%m-%dT%H:%M:%fZ','2026-09-24T12:00:00.9999Z')"),
    ("datetime('2026-09-24T24:00:00Z')", "SELECT datetime('2026-09-24T24:00:00Z')"),
    ("strftime('%Y-%m-%dT%H:%M:%SZ','2026-09-24T24:00:00Z')",
     "SELECT strftime('%Y-%m-%dT%H:%M:%SZ','2026-09-24T24:00:00Z')"),
    ("datetime('2024-02-30T12:00:00Z')", "SELECT datetime('2024-02-30T12:00:00Z')"),
    ("strftime('%Y-%m-%dT%H:%M:%SZ', 1790251200, 'unixepoch')",
     "SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 1790251200, 'unixepoch')"),
    ("datetime(253402300800, 'unixepoch') (year 10000)", "SELECT datetime(253402300800, 'unixepoch')"),
    ("datetime('9999-12-31T23:59:59Z', '+1 second')", "SELECT datetime('9999-12-31T23:59:59Z', '+1 second')"),
    ("datetime('0001-01-01T00:00:00Z', '-1 day')", "SELECT datetime('0001-01-01T00:00:00Z', '-1 day')"),
    ("datetime('0000-01-01T00:00:00Z')", "SELECT datetime('0000-01-01T00:00:00Z')"),
    ("strftime('%Y-%m-%dT%H:%M:%S%z', 'now') (%z)", "SELECT strftime('%Y-%m-%dT%H:%M:%S%z', 'now')"),
    ("datetime('now','subsec')", "SELECT datetime('now','subsec')"),
    ("datetime('2026-09-24T12:00:00Z', 'auto')", "SELECT datetime('2026-09-24T12:00:00Z', 'auto')"),
]


def produce():
    for label, sql in PRODUCERS:
        try:
            v = CON.execute(sql).fetchone()[0]
            err = None
        except Exception as e:  # noqa: BLE001
            v, err = None, f"{type(e).__name__}: {e}"
        print(json.dumps({"call": label, "output": v, "error": err}, ensure_ascii=False))


STRICT_RE = None


KINDS = {"datetime": "rfc3339", "strftime": "rfc3339", "julianday": "rfc3339",
         "unixepoch": "rfc3339", "strict": "rfc3339"}


def answer(api, s):
    """One run_vectors.py answer for SQLite function `api` (or the "strict" guard)."""
    import re
    if api == "strict":
        # the recommended guard: strict regex, then SQLite for the day-of-month check
        global STRICT_RE
        if STRICT_RE is None:
            STRICT_RE = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3])"
                                   r":[0-5][0-9]:[0-5][0-9](\.[0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])")
        if not STRICT_RE.fullmatch(s):
            return {"ok": False, "error": "regex"}
        s = s[:10] + "T" + s[11:-1] + s[-1].upper()  # SQLite rejects a lower-case t
        r = run("strftime", s)
        # SQLite rolls Feb 30 over to Mar 1: reject when the date part changed in a no-offset re-read
        same = CON.execute("SELECT date(?) = ?", (s[:10], s[:10])).fetchone()[0]
        r["ok"] = bool(r["ok"] and same)
        out = {"ok": r["ok"]}
        if r["ok"] and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}", r["utc"] or ""):
            out["utc"] = r["utc"]
        elif r["ok"]:
            out["malformed_output"] = r.get("value")
        return out
    try:
        r = run(api, s)
    except Exception as e:  # noqa: BLE001  (e.g. surrogates)
        r = {"ok": False, "error": str(e)}
    out = {"ok": r["ok"]}
    if r.get("utc") and re.fullmatch(r"-?[0-9]{4,}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?", r["utc"]):
        out["utc"] = r["utc"]
    elif r.get("ok"):
        out["malformed_output"] = r.get("value")  # e.g. strftime '%f' printing '  null'
    if r.get("error"):
        out["error"] = r["error"]
    return out


def adapter(api):
    if api not in KINDS:
        sys.exit(f"unknown adapter key {api!r}; see: probe_sqlite.py list")
    serve_adapter(lambda s: answer(api, s))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if cmd == "probe":
        print(json.dumps({"sqlite_version": sqlite3.sqlite_version}), file=sys.stderr)
        probe()
    elif cmd == "produce":
        produce()
    elif cmd == "adapter":
        adapter(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "list":
        for k, kind in KINDS.items():
            print(f"{k}\t{kind}")
    else:
        sys.exit(__doc__)

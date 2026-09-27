#!/usr/bin/env python3
"""Probe PostgreSQL date/time input and output against RFC 3339.

Needs a server reached through the usual libpq variables (PGHOST, PGPORT, PGUSER,
PGDATABASE; defaults here: 127.0.0.1, 54329, postgres) and psycopg 3
(`pip install 'psycopg[binary]'`) or, without it, the `psql` client: each
connection is then one `psql` session and every query runs inside a PL/pgSQL
wrapper that turns SQL errors into data.  A throwaway cluster:

    initdb -D "$PGDATA" -U postgres --auth=trust -E UTF8
    pg_ctl -D "$PGDATA" -o "-p 54329 -k '' -c listen_addresses=127.0.0.1" start
    export PGHOST=127.0.0.1 PGPORT=54329 PGUSER=postgres
    TZ=America/New_York python3 probe_pg.py probe    > pg-consumers.jsonl
    TZ=America/New_York python3 probe_pg.py specials > pg-specials.jsonl
    TZ=America/New_York python3 probe_pg.py produce  > pg-producers.jsonl
    python3 probe_pg.py adapter tstz|tstz-utc|ts|to_timestamp|jsonpath|jsonpath-tz|strict
        (run_vectors.py adapter: one string on stdin, or JSON lines with RFCDT_BATCH=1)
    python3 probe_pg.py list      (adapter keys: <key>\t<target-kind>)
    python3 probe_pg.py ping      (exit 0 when the server answers)

(-k '' avoids the 103-byte Unix-socket path limit when PGDATA is deep.)
The adapter prints {"ok": ..., "utc": "<engine instant in UTC>"}; "utc" is an
extra key that instant_check.py compares with the true instant.
"""
import json
import os
import secrets
import shutil
import subprocess
import sys

try:
    import psycopg
except ImportError:  # fall back to the psql client (PsqlConnection below)
    psycopg = None

from common import classify, compare_instant, expected_utc, load_inputs, rfcdt_fields, serve_adapter, effective_cat

for _k, _v in (("PGHOST", "127.0.0.1"), ("PGPORT", "54329"), ("PGUSER", "postgres")):
    os.environ.setdefault(_k, _v)

# Runs one query with parameter $1 and returns its first row as a JSON array, or
# {"error": ...} (SQL errors become data, so the psql session never desyncs).
_WRAPPER = """CREATE FUNCTION pg_temp.probe(q text, s text, n int) RETURNS text LANGUAGE plpgsql AS $f$
DECLARE r text;
BEGIN
  EXECUTE 'SELECT json_build_array(' || (SELECT string_agg('x.c' || i, ',') FROM generate_series(1, n) i)
       || ')::text FROM (' || q || ') AS x(' || (SELECT string_agg('c' || i, ',') FROM generate_series(1, n) i)
       || ')' INTO r USING s;
  RETURN coalesce(r, 'null');
EXCEPTION WHEN others THEN
  RETURN json_build_object('error', SQLSTATE || ' ' || SQLERRM)::text;
END $f$;"""


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class PsqlError(Exception):
    pass


class PsqlConnection:
    """Just enough of a psycopg connection (execute(sql, params).fetchone()) over one psql session."""

    MARK = "@@probe-end@@"

    def __init__(self):
        if not shutil.which("psql"):
            raise PsqlError("neither psycopg nor psql is available")
        self.p = subprocess.Popen(["psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=0"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        self._send(_WRAPPER)

    def _send(self, sql):
        self.p.stdin.write(sql + "\n\\echo " + self.MARK + "\n")
        self.p.stdin.flush()
        lines = []
        while True:
            ln = self.p.stdout.readline()
            if not ln:
                raise PsqlError("psql exited: " + " ".join(lines)[-300:])
            if ln.rstrip("\n") == self.MARK:
                return lines
            lines.append(ln.rstrip("\n"))

    @staticmethod
    def _quote(v):
        tag = "q" + secrets.token_hex(6)
        while f"${tag}$" in v:
            tag = "q" + secrets.token_hex(6)
        return f"${tag}${v}${tag}$"

    def execute(self, sql, params=None):
        if not params:
            lines = self._send(sql + ";")
            errs = [ln for ln in lines if "ERROR:" in ln]
            if errs:
                raise PsqlError(errs[0].split("ERROR:", 1)[1].strip())
            return _Result(tuple(lines[0].split("|")) if lines else None)
        (s,) = params
        if "\0" in s:
            raise PsqlError("string contains NUL (not representable in PostgreSQL text)")
        s.encode("utf-8")  # lone surrogates: UnicodeEncodeError, reported as a client error
        q = sql.replace("%s", "$1")
        # every APIS query selects 3 columns (value text, UTC text, BC flag)
        lines = self._send(f"SELECT pg_temp.probe({self._quote(q)}, {self._quote(s)}, 3);")
        if len(lines) != 1:
            raise PsqlError("psql: " + " ".join(lines)[-300:])
        out = json.loads(lines[0])
        if out is None:
            return _Result(None)
        if isinstance(out, dict):
            raise PsqlError(out["error"])
        return _Result(tuple(out))

UTC_TEXT = "to_char({v} AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US')"
TSUTC_TEXT = "to_char({v}, 'YYYY-MM-DD\"T\"HH24:MI:SS.US')"

# name -> (label, session TimeZone, SQL producing (text value, utc text, bc flag))
APIS = {
    "tstz": ("PostgreSQL `s::timestamptz` (TimeZone=America/New_York)", "America/New_York",
             "SELECT v::text, " + UTC_TEXT.format(v="v") + ", to_char(v AT TIME ZONE 'UTC','BC') "
             "FROM (SELECT %s::text::timestamptz v) x"),
    "tstz-utc": ("PostgreSQL `s::timestamptz` (TimeZone=UTC)", "UTC",
                 "SELECT v::text, " + UTC_TEXT.format(v="v") + ", to_char(v AT TIME ZONE 'UTC','BC') "
                 "FROM (SELECT %s::text::timestamptz v) x"),
    "ts": ("PostgreSQL `s::timestamp` (without time zone)", "America/New_York",
           "SELECT v::text, " + TSUTC_TEXT.format(v="v") + ", to_char(v,'BC') "
           "FROM (SELECT %s::text::timestamp v) x"),
    "to_timestamp": ("PostgreSQL `to_timestamp(s, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')`", "America/New_York",
                     "SELECT v::text, " + UTC_TEXT.format(v="v") + ", to_char(v AT TIME ZONE 'UTC','BC') "
                     "FROM (SELECT to_timestamp(%s::text, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM') v) x"),
    "jsonpath": ("PostgreSQL `jsonb_path_query(to_jsonb(s), '$.datetime()')`", "America/New_York",
                 "SELECT j #>> '{}', " + UTC_TEXT.format(v="(j #>> '{}')::timestamptz") + ", '' "
                 "FROM (SELECT jsonb_path_query(to_jsonb(%s::text), '$.datetime()') j) x"),
    "jsonpath-tz": ("PostgreSQL `jsonb_path_query(to_jsonb(s), '$.timestamp_tz()')`", "America/New_York",
                    "SELECT j #>> '{}', " + UTC_TEXT.format(v="(j #>> '{}')::timestamptz") + ", '' "
                    "FROM (SELECT jsonb_path_query_tz(to_jsonb(%s::text), '$.timestamp_tz()') j) x"),
}


def _connect():
    return psycopg.connect(autocommit=True) if psycopg else PsqlConnection()


def connect(tz):
    con = _connect()
    con.execute(f"SET TimeZone = '{tz}'")
    con.execute("SET DateStyle = 'ISO, MDY'")
    return con


_CONS = {}


def run(api, s):
    label, tz, sql = APIS[api]
    con = _CONS.get(tz) or _CONS.setdefault(tz, connect(tz))
    try:
        row = con.execute(sql, (s,)).fetchone()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {str(e).splitlines()[0]}"}
    if row is None:
        return {"ok": False, "error": "no row"}
    v, utc, bc = row
    if utc and (bc == "BC" or (bc == "" and isinstance(v, str) and v.endswith(" BC"))):
        # astronomical year = 1 - BC year (1 BC = year 0), as instant_check.py expects
        y, rest = utc.split("-", 1)
        astro = 1 - int(y)
        utc = (f"-{-astro:04d}" if astro < 0 else f"{astro:04d}") + "-" + rest
    return {"ok": True, "value": v, "utc": utc, "prec": 6}


def probe():
    for inp in load_inputs():
        f = rfcdt_fields(inp["s"], "ixdtf" if inp["cat"].startswith("ixdtf") else "rfc3339")
        exp, frac = expected_utc(f)
        for api, (label, _, _) in APIS.items():
            r = run(api, inp["s"])
            cmp = compare_instant(exp, frac, r.get("utc"), 6) if r["ok"] else None
            print(json.dumps({"api": label, "id": inp["id"], "s": inp["s"], "cat": inp["cat"],
                              "expected_utc": exp, "cmp": cmp,
                              "verdict": classify(effective_cat(inp), r["ok"], cmp), **r}, ensure_ascii=False))


SPECIALS = ["epoch", "now", "today", "tomorrow", "infinity", "-infinity", "allballs",
            "2026-09-24T12:00:00 Europe/Paris", "2026-09-24T12:00:00 PST", "2026-09-24T12:00:00 UTC",
            "2026-09-24T12:00:00+02:00 Europe/Paris", "Thu Sep 24 12:00:00 2026 PST",
            "September 24, 2026 12:00 pm", "2026-09-24T12:00:00+05:30:15", "2026-09-24T12:00:00+15:59",
            "2026-09-24T12:00:00+16:00", "J2461308", "2026-09-24T12:00:00.1234565Z",
            "2026-09-24T12:00:00.1234575Z", "2026-09-24T12:00:00.9999995Z", "2026-09-24T23:59:60.5Z",
            "2026-09-24T24:00:00.1Z", "2026-09-24T24:00:01Z", "294277-01-01T00:00:00Z", "4714-11-24T00:00:00Z BC",
            "4714-11-23T00:00:00Z BC", "12026-09-24T12:00:00Z", "26-09-24T12:00:00Z", "2026-09-24T12:00:00z",
            "2026-09-24t12:00:00Z", "2026-09-24T12:00:00Z\t", "  2026-09-24T12:00:00Z  "]


def specials():
    for s in SPECIALS:
        for api in ("tstz", "ts", "jsonpath"):
            r = run(api, s)
            print(json.dumps({"api": APIS[api][0], "s": s, **r}, ensure_ascii=False))


# (label, TimeZone, DateStyle, SQL)
V = "'2026-09-24T12:00:00Z'::timestamptz"
PRODUCERS = [
    ("v::text, DateStyle ISO", "America/New_York", "ISO, MDY", f"SELECT {V}::text"),
    ("v::text, DateStyle ISO", "UTC", "ISO, MDY", f"SELECT {V}::text"),
    ("v::text, DateStyle ISO", "Asia/Kolkata", "ISO, MDY", f"SELECT {V}::text"),
    ("v::text, DateStyle ISO", "America/St_Johns", "ISO, MDY", f"SELECT {V}::text"),
    ("v::text, DateStyle ISO, Africa/Monrovia 1970-01-01T12:00:00Z", "Africa/Monrovia", "ISO, MDY",
     "SELECT '1970-01-01T12:00:00Z'::timestamptz::text"),
    ("v::text, DateStyle ISO, Europe/Paris 1850-01-01 00:00 local (LMT)", "Europe/Paris", "ISO, MDY",
     "SELECT '1850-01-01 00:00:00'::timestamptz::text"),
    ("v::text, fraction .5", "UTC", "ISO, MDY", "SELECT '2026-09-24T12:00:00.5Z'::timestamptz::text"),
    ("v::text, fraction .123456", "UTC", "ISO, MDY", "SELECT '2026-09-24T12:00:00.123456Z'::timestamptz::text"),
    ("v::text, fraction .1234567 (7 digits in)", "UTC", "ISO, MDY",
     "SELECT '2026-09-24T12:00:00.1234567Z'::timestamptz::text"),
    ("v::text, year 0001", "UTC", "ISO, MDY", "SELECT '0001-01-01T00:00:00Z'::timestamptz::text"),
    ("v::text, year 9999", "UTC", "ISO, MDY", "SELECT '9999-12-31T23:59:59Z'::timestamptz::text"),
    ("v::text, year 10000", "UTC", "ISO, MDY", "SELECT ('9999-12-31T23:59:59Z'::timestamptz + interval '1 day')::text"),
    ("v::text, 1 BC", "UTC", "ISO, MDY", "SELECT ('0001-01-01T00:00:00Z'::timestamptz - interval '1 day')::text"),
    ("v::text, infinity", "UTC", "ISO, MDY", "SELECT 'infinity'::timestamptz::text"),
    ("v::text, DateStyle SQL", "America/New_York", "SQL, MDY", f"SELECT {V}::text"),
    ("v::text, DateStyle Postgres", "America/New_York", "Postgres, MDY", f"SELECT {V}::text"),
    ("v::text, DateStyle German", "America/New_York", "German", f"SELECT {V}::text"),
    ("timestamp (no tz) ::text", "UTC", "ISO, MDY", "SELECT '2026-09-24T12:00:00Z'::timestamp::text"),
    ("now()::text (TimeZone America/New_York)", "America/New_York", "ISO, MDY", "SELECT now()::text"),
    ("to_json(v)", "America/New_York", "ISO, MDY", f"SELECT to_json({V})::text"),
    ("to_json(v)", "UTC", "ISO, MDY", f"SELECT to_json({V})::text"),
    ("to_json(v)", "Asia/Kolkata", "ISO, MDY", f"SELECT to_json({V})::text"),
    ("to_json(v), Africa/Monrovia 1970", "Africa/Monrovia", "ISO, MDY",
     "SELECT to_json('1970-01-01T12:00:00Z'::timestamptz)::text"),
    ("to_json(v), Europe/Paris 1850 (LMT)", "Europe/Paris", "ISO, MDY",
     "SELECT to_json('1850-01-01 00:00:00'::timestamptz)::text"),
    ("to_json(v), DateStyle German (to_json ignores DateStyle?)", "America/New_York", "German",
     f"SELECT to_json({V})::text"),
    ("to_json(v), year 10000", "UTC", "ISO, MDY",
     "SELECT to_json('9999-12-31T23:59:59Z'::timestamptz + interval '1 day')::text"),
    ("to_json(v), 1 BC", "UTC", "ISO, MDY",
     "SELECT to_json('0001-01-01T00:00:00Z'::timestamptz - interval '1 day')::text"),
    ("to_json(v), infinity", "UTC", "ISO, MDY", "SELECT to_json('infinity'::timestamptz)::text"),
    ("to_json(v), fraction .5", "UTC", "ISO, MDY", "SELECT to_json('2026-09-24T12:00:00.5Z'::timestamptz)::text"),
    ("to_jsonb(v)", "America/New_York", "ISO, MDY", f"SELECT to_jsonb({V})::text"),
    ("json_build_object('t', v)", "America/New_York", "ISO, MDY", f"SELECT json_build_object('t', {V})::text"),
    ("row_to_json(row(v))", "UTC", "ISO, MDY", f"SELECT row_to_json(row({V}))::text"),
    ("to_json(timestamp without tz)", "UTC", "ISO, MDY", "SELECT to_json('2026-09-24T12:00:00Z'::timestamp)::text"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SS.USOF')", "America/New_York", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MI:SS.USOF')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SS.USOF')", "Asia/Kolkata", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MI:SS.USOF')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')", "America/New_York", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')", "UTC", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')", "America/St_Johns", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM'), Monrovia 1970", "Africa/Monrovia", "ISO, MDY",
     "SELECT to_char('1970-01-01T12:00:00Z'::timestamptz, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') (literal Z, session local)", "America/New_York", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')"),
    ("to_char(v AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')", "America/New_York", "ISO, MDY",
     f"SELECT to_char({V} AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"),
    ("to_char(v AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.MS\"Z\"'), year 10000", "UTC", "ISO, MDY",
     "SELECT to_char(('9999-12-31T23:59:59Z'::timestamptz + interval '1 day') AT TIME ZONE 'UTC', "
     "'YYYY-MM-DD\"T\"HH24:MI:SS.MS\"Z\"')"),
    ("to_char(v AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'), 1 BC", "UTC", "ISO, MDY",
     "SELECT to_char(('0001-01-01T00:00:00Z'::timestamptz - interval '1 day') AT TIME ZONE 'UTC', "
     "'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH:MI:SSOF') (HH = 12-hour)", "UTC", "ISO, MDY",
     "SELECT to_char('2026-09-24T15:00:00Z'::timestamptz, 'YYYY-MM-DD\"T\"HH:MI:SSOF')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MM:SSOF') (MM = month)", "UTC", "ISO, MDY",
     f"SELECT to_char({V}, 'YYYY-MM-DD\"T\"HH24:MM:SSOF')"),
    ("to_char(v, 'IYYY-MM-DD\"T\"HH24:MI:SSOF'), 2026-12-31 (ISO week year)", "UTC", "ISO, MDY",
     "SELECT to_char('2029-12-31T12:00:00Z'::timestamptz, 'IYYY-MM-DD\"T\"HH24:MI:SSOF')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SSOF'), year 0001 Monrovia (LMT)", "Africa/Monrovia", "ISO, MDY",
     "SELECT to_char('0001-01-01T12:00:00Z'::timestamptz, 'YYYY-MM-DD\"T\"HH24:MI:SSOF')"),
    ("to_char(v, 'YYYY-MM-DD\"T\"HH24:MI:SS.FF9OF')", "UTC", "ISO, MDY",
     "SELECT to_char('2026-09-24T12:00:00.123456Z'::timestamptz, 'YYYY-MM-DD\"T\"HH24:MI:SS.FF6OF')"),
    ("jsonb_path_query(to_jsonb(v), '$.datetime()') round trip", "America/New_York", "ISO, MDY",
     "SELECT jsonb_path_query_tz(to_jsonb('2026-09-24T12:00:00Z'::text), '$.datetime()')::text"),
]


def produce():
    for label, tz, ds, sql in PRODUCERS:
        con = _connect()
        con.execute(f"SET TimeZone = '{tz}'")
        con.execute(f"SET DateStyle = '{ds}'")
        try:
            v, err = con.execute(sql).fetchone()[0], None
        except Exception as e:  # noqa: BLE001
            v, err = None, f"{type(e).__name__}: {str(e).splitlines()[0]}"
        if psycopg:
            con.close()
        else:
            con.p.stdin.close()
            con.p.wait()
        print(json.dumps({"call": label, "timezone": tz, "datestyle": ds, "output": v, "error": err},
                         ensure_ascii=False))


KINDS = {"tstz": "rfc3339", "tstz-utc": "rfc3339", "ts": "rfc3339", "to_timestamp": "rfc3339",
         "jsonpath": "rfc3339", "jsonpath-tz": "rfc3339", "strict": "rfc3339"}
STRICT_RE = None


def answer(api, s):
    if api == "strict":
        import re
        global STRICT_RE
        STRICT_RE = STRICT_RE or re.compile(
            r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3])"
            r":[0-5][0-9]:[0-5][0-9](\.[0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])")
        if not STRICT_RE.fullmatch(s):
            return {"ok": False, "error": "regex"}
        api = "tstz-utc"
    try:
        r = run(api, s)
    except Exception as e:  # noqa: BLE001  (NUL, surrogates)
        r = {"ok": False, "error": f"client: {type(e).__name__}: {e}"}
    out = {"ok": r["ok"]}
    for k in ("utc", "error"):
        if r.get(k):
            out[k] = r[k]
    return out


def adapter(api):
    if api not in KINDS:
        sys.exit(f"unknown adapter key {api!r}; see: probe_pg.py list")
    serve_adapter(lambda s: answer(api, s))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if cmd == "probe":
        con = _connect()
        print(json.dumps({"server": con.execute("SELECT version()").fetchone()[0],
                          "psycopg": psycopg.__version__ if psycopg else "none (psql)"}), file=sys.stderr)
        probe()
    elif cmd == "list":
        for k, kind in KINDS.items():
            print(f"{k}\t{kind}")
    elif cmd == "ping":
        try:
            print(_connect().execute("SELECT version()").fetchone()[0])
        except Exception as e:  # noqa: BLE001
            sys.exit(f"no PostgreSQL server: {e}")
    elif cmd == "specials":
        specials()
    elif cmd == "produce":
        produce()
    elif cmd == "adapter":
        adapter(sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        sys.exit(__doc__)

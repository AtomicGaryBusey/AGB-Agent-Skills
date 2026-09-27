#!/usr/bin/env python3
"""RFC 3339 / RFC 9557 conformance probe for Python date-time APIs.

Usage:
  TZ=America/New_York python3 probe_python.py [probe] > results/python.jsonl
  python3 probe_python.py list            # adapter keys: <key>\t<target-kind>
  python3 probe_python.py adapter <key>   # scripts/run_vectors.py adapter (per-process + batch)
  run_vectors.py --target 'python3 probes/probe_python.py adapter fromisoformat' --batch \
      --target-kind rfc3339 --target-options fixed --target-has-tzdata yes

Optional libs (pydantic, dateutil, jsonschema+rfc3339-validator) are probed
only if importable (their adapter keys are listed only then).  Probe output:
one JSON object per line.  Adapter output: run_vectors.py protocol, with the
LOCAL fields of the returned datetime (a naive result reports no offset).
"""
import json, os, sys, time
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LANG = "python"


def load_inputs(path=os.path.join(HERE, "inputs.json")):
    """probes/inputs.json schema 2 (inputs + legacy) or the old list form."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc if isinstance(doc, list) else doc["inputs"] + doc.get("legacy", [])


def utc_of(dt):
    if isinstance(dt, datetime):
        if dt.tzinfo is None or dt.utcoffset() is None:
            return "naive:" + dt.isoformat()
        u = dt.astimezone(timezone.utc)
        return u.strftime("%Y-%m-%dT%H:%M:%S") + ".%06d" % u.microsecond
    return None


def emit(kind, api, rec=None, **kw):
    d = {"lang": LANG, "kind": kind, "api": api}
    if rec:
        d.update(id=rec["id"], input=rec["s"])
    d.update(kw)
    print(json.dumps(d, ensure_ascii=False))


# key, probe API name, target kind, function(s) -> datetime | "valid"
APIS = [
    ("fromisoformat", "datetime.fromisoformat", "rfc3339", datetime.fromisoformat),
    ("strptime-z", "strptime('%Y-%m-%dT%H:%M:%S%z')", "rfc3339",
     lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")),
    ("strptime-f-z", "strptime('%Y-%m-%dT%H:%M:%S.%f%z')", "rfc3339",
     lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%z")),
    ("strptime-literal-z", "strptime('%Y-%m-%dT%H:%M:%SZ')", "rfc3339",
     lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")),
]
try:
    from dateutil import parser as du
    APIS += [("dateutil-isoparse", "dateutil.parser.isoparse", "rfc3339", du.isoparse),
             ("dateutil-parse", "dateutil.parser.parse", "rfc3339", du.parse)]
except ImportError:
    pass
try:
    from pydantic import TypeAdapter, AwareDatetime
    _ta = TypeAdapter(datetime)
    _taa = TypeAdapter(AwareDatetime)
    APIS += [("pydantic-datetime", "pydantic TypeAdapter(datetime).validate_python", "rfc3339",
              _ta.validate_python),
             ("pydantic-aware-json", "pydantic TypeAdapter(AwareDatetime).validate_json", "rfc3339",
              lambda s: _taa.validate_json(json.dumps(s)))]
except ImportError:
    pass
try:
    import jsonschema  # without the library this finds the probes/jsonschema/ directory
    _fc = jsonschema.FormatChecker()
    if "date-time" in _fc.checkers:
        def _js(s):
            jsonschema.validate(s, {"type": "string", "format": "date-time"}, format_checker=_fc)
            return "valid"
        APIS.append(("jsonschema-formatchecker", "jsonschema FormatChecker date-time (rfc3339-validator)",
                     "rfc3339", _js))
except (ImportError, AttributeError):
    pass


def parse_probe(api, fn, inputs):
    for rec in inputs:
        try:
            r = fn(rec["s"])
            emit("parse", api, rec, ok=True, out=repr(r) if not isinstance(r, str) else r, utc=utc_of(r))
        except Exception as e:
            emit("parse", api, rec, ok=False, err=f"{type(e).__name__}: {e}"[:160])


def adapter_answer(fn, s):
    """One run_vectors.py answer: ok + the fields the returned datetime exposes."""
    try:
        d = fn(s)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
    if not isinstance(d, datetime):
        return {"ok": True}
    f = {"year": d.year, "month": d.month, "day": d.day, "hour": d.hour,
         "minute": d.minute, "second": d.second, "leap_second": False}
    if d.microsecond:  # a zero fraction is omitted (".0" and no fraction look the same)
        f["secfrac"] = "%06d" % d.microsecond
    off = d.utcoffset()
    # A naive result has no offset at all: null, so a vector expecting 0 (Z) shows WRONG VALUE.
    f["offset_minutes"] = None if off is None else int(off.total_seconds() // 60)
    return {"ok": True, "fields": f, "utc": utc_of(d)}


def adapter(key):
    fns = {k: fn for k, _, _, fn in APIS}
    if key not in fns:
        print(f"unknown adapter key {key!r}; see: probe_python.py list", file=sys.stderr)
        return 2
    fn = fns[key]
    if os.environ.get("RFCDT_BATCH") == "1":
        for line in sys.stdin:
            if line.strip():
                req = json.loads(line)
                print(json.dumps({"id": req["id"], **adapter_answer(fn, req["input"])}), flush=True)
    else:
        print(json.dumps(adapter_answer(fn, sys.stdin.read())))
    return 0


if len(sys.argv) > 1 and sys.argv[1] == "list":
    for k, _, kind, _ in APIS:
        print(f"{k}\t{kind}")
    sys.exit(0)
if len(sys.argv) > 1 and sys.argv[1] == "adapter":
    sys.exit(adapter(sys.argv[2] if len(sys.argv) > 2 else ""))
if len(sys.argv) > 1 and sys.argv[1] != "probe":
    print(__doc__, file=sys.stderr)
    sys.exit(2)

INPUTS = load_inputs()
for _key, _api, _kind, _fn in APIS:
    parse_probe(_api, _fn, INPUTS)

# ---------------- formatter probes ----------------
UTC = timezone.utc
fmt_cases = []
def F(api, thunk):
    try:
        emit("format", api, out=thunk())
    except Exception as e:
        emit("format", api, out=None, err=f"{type(e).__name__}: {e}"[:160])

F("datetime(..., tzinfo=utc).isoformat()", lambda: datetime(2026, 9, 24, 12, 0, 0, tzinfo=UTC).isoformat())
F("datetime(..., microsecond=123000, tzinfo=utc).isoformat()", lambda: datetime(2026, 9, 24, 12, 0, 0, 123000, tzinfo=UTC).isoformat())
F("naive datetime(...).isoformat()", lambda: datetime(2026, 9, 24, 12, 0, 0).isoformat())
F("datetime.utcnow().isoformat()  [naive]", lambda: datetime.utcnow().isoformat())
F("str(aware datetime)", lambda: str(datetime(2026, 9, 24, 12, tzinfo=UTC)))
F("aware.isoformat(timespec='minutes')", lambda: datetime(2026, 9, 24, 12, tzinfo=UTC).isoformat(timespec="minutes"))
F("aware.isoformat(sep=' ')", lambda: datetime(2026, 9, 24, 12, tzinfo=UTC).isoformat(sep=" "))
F("timezone(timedelta(seconds=30)) .isoformat()", lambda: datetime(2026, 9, 24, 12, tzinfo=timezone(timedelta(seconds=30))).isoformat())
try:
    from zoneinfo import ZoneInfo
    F("datetime(1850,1,1,tzinfo=ZoneInfo('Europe/Paris')).isoformat()  [LMT]", lambda: datetime(1850, 1, 1, tzinfo=ZoneInfo("Europe/Paris")).isoformat())
    F("datetime(2026,9,24,14,tzinfo=ZoneInfo('Europe/Paris')).isoformat()", lambda: datetime(2026, 9, 24, 14, tzinfo=ZoneInfo("Europe/Paris")).isoformat())
except Exception:
    pass
F("aware.strftime('%Y-%m-%dT%H:%M:%S%z')", lambda: datetime(2026, 9, 24, 12, tzinfo=timezone(timedelta(hours=2))).strftime("%Y-%m-%dT%H:%M:%S%z"))
F("aware.strftime('%Y-%m-%dT%H:%M:%S%:z')", lambda: datetime(2026, 9, 24, 12, tzinfo=timezone(timedelta(hours=2))).strftime("%Y-%m-%dT%H:%M:%S%:z"))
F("time.strftime('%Y-%m-%dT%H:%M:%S%z') [local]", lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(1790251200)))
F("naive local datetime(...).strftime('%Y-%m-%dT%H:%M:%SZ')  [lies about Z]", lambda: datetime.fromtimestamp(1790251200).strftime("%Y-%m-%dT%H:%M:%SZ"))
F("datetime(1,1,1,tzinfo=utc).isoformat()", lambda: datetime(1, 1, 1, tzinfo=UTC).isoformat())
F("datetime(999,1,1,tzinfo=utc).strftime('%Y-%m-%dT%H:%M:%SZ')", lambda: datetime(999, 1, 1, tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
try:
    from pydantic import TypeAdapter
    F("pydantic TypeAdapter(datetime).dump_json(aware utc)", lambda: TypeAdapter(datetime).dump_json(datetime(2026, 9, 24, 12, tzinfo=UTC)).decode())
    F("pydantic TypeAdapter(datetime).dump_json(naive)", lambda: TypeAdapter(datetime).dump_json(datetime(2026, 9, 24, 12)).decode())
except ImportError:
    pass
try:
    json.dumps(datetime(2026, 9, 24, tzinfo=UTC))
except TypeError as e:
    emit("format", "json.dumps(datetime)", out=None, err=str(e)[:120])
F("json.dumps(datetime, default=str)", lambda: json.loads(json.dumps(datetime(2026, 9, 24, 12, tzinfo=UTC), default=str)))

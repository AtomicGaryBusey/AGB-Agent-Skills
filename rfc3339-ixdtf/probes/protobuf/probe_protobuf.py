#!/usr/bin/env python3
"""Probe Python `protobuf` google.protobuf.Timestamp JSON mapping against RFC 3339.

Needs `pip install protobuf` (a venv is fine).  Run with TZ=America/New_York.

    python probe_protobuf.py probe   <../inputs.json > consumers-py.jsonl
    python probe_protobuf.py produce                 > producers-py.jsonl
    python probe_protobuf.py list                      (adapter keys: <key>\t<target-kind>)
    python probe_protobuf.py adapter fromjson|parse   (run_vectors.py adapter, per-process
                                                       and batch: RFCDT_BATCH=1 JSON lines)

probe reads probes/inputs.json schema 2 ({"inputs","legacy"}) or the old list.

APIs: Timestamp.FromJsonString(s) and json_format.Parse('"<s>"', Timestamp()).
Adapters print ok plus seconds/nanos (protobuf keeps no offset, so no RFC
`fields` are returned; compare instants with compare_instants.py).
"""
import datetime
import json
import os
import sys

if len(sys.argv) > 1 and sys.argv[1] == "list":  # needs no protobuf library
    print("fromjson\trfc3339\nparse\trfc3339")
    sys.exit(0)

from google.protobuf import __version__ as PB_VERSION
from google.protobuf import json_format
from google.protobuf.internal import api_implementation
from google.protobuf.timestamp_pb2 import Timestamp


def from_json(s):
    t = Timestamp()
    t.FromJsonString(s)
    return t


def parse(s):
    t = Timestamp()
    json_format.Parse(json.dumps(s), t)
    return t


APIS = {"fromjson": ("Timestamp.FromJsonString", from_json),
        "parse": ("json_format.Parse(Timestamp)", parse)}

EXTRA = [
    ("pb-off-big", "2026-09-24T12:00:00+99:99", "invalid"),
    ("pb-off-1digit", "2026-09-24T12:00:00+2:0", "invalid"),
    ("pb-off-underscore", "2026-09-24T12:00:00+0_2:00", "invalid"),
    ("pb-off-space", "2026-09-24T12:00:00+ 2:00", "invalid"),
    ("pb-off-trail-ws", "2026-09-24T12:00:00+02:00\n", "invalid"),
    ("pb-h1", "2026-09-24T1:00:00Z", "invalid"),
    ("pb-min-off", "0001-01-01T00:00:00+01:00", "valid"),
    ("pb-max-off", "9999-12-31T23:59:59-01:00", "valid"),
    ("pb-max-frac", "9999-12-31T23:59:59.999999999Z", "valid"),
    ("pb-frac10", "2026-09-24T12:00:00.1234567890Z", "valid"),
    ("pb-frac-plus", "2026-09-24T12:00:00.+5Z", "invalid"),
    ("pb-frac-exp", "2026-09-24T12:00:00.1e3Z", "invalid"),
    ("pb-frac-us", "2026-09-24T12:00:00.1_2Z", "invalid"),
    ("pb-Z-then-off", "2026-09-24T12:00:00Z+01:00", "invalid"),
    ("pb-frac-exp-neg", "2026-09-24T12:00:00.1e-3Z", "invalid"),
    ("pb-frac-exp-E", "2026-09-24T12:00:00.5E-1Z", "invalid"),
    ("pb-off-min-neg", "2026-09-24T12:00:00+01:-30", "invalid"),
    ("pb-off-plus-neg", "2026-09-24T12:00:00+-1:00", "invalid"),
    ("pb-off-min-plus", "2026-09-24T12:00:00+01:+30", "invalid"),
    ("pb-off-arabic", "2026-09-24T12:00:00+\u0661:\u0660\u0660", "invalid"),
    ("pb-off-sec", "2026-09-24T12:00:00+01:00:00", "invalid"),
]


def run(fn, s):
    try:
        t = fn(s)
    except Exception as e:  # noqa: BLE001 -- any exception is a reject
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
    r = {"ok": True, "seconds": t.seconds, "nanos": t.nanos}
    try:
        r["reemit"] = t.ToJsonString()
    except Exception as e:  # noqa: BLE001
        r["reemit"] = f"ERR {e}"
    return r


def probe():
    doc = json.load(sys.stdin)
    inputs = doc if isinstance(doc, list) else doc["inputs"] + doc.get("legacy", [])
    rows = [(i["id"], i["s"], i["cat"]) for i in inputs] + EXTRA
    for key, (name, fn) in APIS.items():
        for id_, s, cat in rows:
            print(json.dumps({"api": f"python {name}", "id": id_, "s": s, "cat": cat, "result": run(fn, s)}))


def produce():
    base = 1790251200  # 2026-09-24T12:00:00Z
    cases = [
        ("nanos 0", base, 0), ("nanos 100000000 (0.1 s)", base, 100000000),
        ("nanos 123000000", base, 123000000), ("nanos 123456000", base, 123456000),
        ("nanos 123456789", base, 123456789), ("nanos 1", base, 1),
        ("zero value Timestamp()", 0, 0),
        ("seconds -62135596800 (min)", -62135596800, 0),
        ("seconds 253402300799 (max), nanos 999999999", 253402300799, 999999999),
        ("seconds -62135596801 (below min)", -62135596801, 0),
        ("seconds 253402300800 (above max)", 253402300800, 0),
        ("nanos -1", base, -1), ("nanos 1000000000", base, 1000000000),
    ]
    for label, secs, nanos in cases:
        row = {"label": label, "seconds": secs, "nanos": nanos}
        try:
            t = Timestamp(seconds=secs, nanos=nanos)
        except Exception as e:  # noqa: BLE001
            row["construct"] = f"ERR {e}"
            print(json.dumps(row)); continue
        for name, f in (("ToJsonString", lambda: t.ToJsonString()),
                        ("json_format.MessageToJson", lambda: json.loads(json_format.MessageToJson(t)))):
            try:
                row[name] = f()
            except Exception as e:  # noqa: BLE001
                row[name] = f"ERR {type(e).__name__}: {e}"[:160]
        print(json.dumps(row))
    # FromDatetime with naive and aware datetimes (host TZ=America/New_York).
    dts = [
        ("FromDatetime(aware UTC 12:00)", datetime.datetime(2026, 9, 24, 12, tzinfo=datetime.timezone.utc)),
        ("FromDatetime(aware +02:00 14:00)", datetime.datetime(2026, 9, 24, 14, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))),
        ("FromDatetime(naive local 08:00 = 12:00Z on a New York host)", datetime.datetime(2026, 9, 24, 8)),
        ("FromDatetime(datetime.now()) vs now(timezone.utc)", None),
    ]
    for label, dt in dts:
        t = Timestamp()
        if dt is None:
            t.FromDatetime(datetime.datetime.now())
            t2 = Timestamp(); t2.FromDatetime(datetime.datetime.now(datetime.timezone.utc))
            print(json.dumps({"label": label, "ToJsonString": t.ToJsonString(), "true": t2.ToJsonString(),
                              "delta_s": t.seconds - t2.seconds}))
            continue
        t.FromDatetime(dt)
        print(json.dumps({"label": label, "ToJsonString": t.ToJsonString()}))
    t = Timestamp(seconds=base)
    print(json.dumps({"label": "ToDatetime() (no tzinfo arg)", "value": repr(t.ToDatetime())}))


def adapter(which):
    fn = APIS[which][1]
    if os.environ.get("RFCDT_BATCH") == "1":
        for line in sys.stdin:
            if line.strip():
                req = json.loads(line)
                print(json.dumps({"id": req["id"], **run(fn, req["input"])}), flush=True)
        return
    s = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
    print(json.dumps(run(fn, s)))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "probe":
        print(json.dumps({"meta": {"protobuf": PB_VERSION, "backend": api_implementation.Type(),
                                   "python": sys.version.split()[0]}}))
        probe()
    elif cmd == "produce":
        produce()
    elif cmd == "adapter":
        adapter(sys.argv[2])
    else:
        sys.exit(__doc__)

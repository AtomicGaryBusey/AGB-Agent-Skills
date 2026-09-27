#!/usr/bin/env python3
"""Compare protobuf Timestamp consumers with rfcdt: verdict and instant.

protobuf Timestamp keeps only (seconds, nanos) in UTC, so run_vectors.py
cannot compare RFC `fields`.  This script runs an adapter command (same
protocol as run_vectors.py: stdin = string, stdout = {"ok", "seconds",
"nanos"}) over a JSON list of strings, and for each ACCEPTED string that
rfcdt also accepts it compares the instant with the one rfcdt's fields denote
(nanos truncated to 9 digits; a leap second 60 is compared as :59 and noted).

    compare_instants.py --target 'CMD' --inputs ../inputs.json   # probe inputs
    compare_instants.py --target 'CMD' --vectors                 # rfc3339 vectors
Prints JSON lines: id, s, rfcdt_ok, target_ok, target instant, expected instant, verdict.
"""
import argparse
import calendar
import json
import os
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import rfcdt  # noqa: E402


def expected_instant(f):
    sec = f["second"]
    leap = sec == 60
    if leap:
        sec = 59
    epoch = calendar.timegm((f["year"], f["month"], f["day"], f["hour"], f["minute"], sec)) \
        if f["year"] >= 1 else None
    if epoch is None:
        return None, leap
    epoch -= f.get("offset_minutes", 0) * 60
    frac = (f.get("secfrac") or "")[:9].ljust(9, "0")
    return (epoch, int(frac or 0)), leap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--inputs")
    ap.add_argument("--vectors", action="store_true")
    a = ap.parse_args()
    if a.vectors:
        with open(os.path.join(HERE, "..", "..", "vectors", "vectors.json"), encoding="utf-8") as fh:
            doc = json.load(fh)
        vs = doc["vectors"] if isinstance(doc, dict) else doc
        rows = [(v["id"], v["input"]) for v in vs if v["profile"] == "rfc3339" and not v.get("options")]
    else:
        with open(a.inputs, encoding="utf-8") as fh:
            doc = json.load(fh)  # schema 2 {"inputs","legacy"} or the old list
            rows = [(i["id"], i["s"]) for i in
                    (doc if isinstance(doc, list) else doc["inputs"] + doc.get("legacy", []))]
    cmd = shlex.split(a.target)
    for id_, s in rows:
        p = subprocess.run(cmd, input=s.encode("utf-8"), capture_output=True, timeout=30)
        try:
            t = json.loads(p.stdout.decode().strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            t = {"ok": None, "error": p.stderr.decode()[:200]}
        r = rfcdt.check(s)
        row = {"id": id_, "s": s, "rfcdt_ok": r.ok, "target_ok": t.get("ok")}
        if t.get("ok"):
            row["got"] = [t.get("seconds"), t.get("nanos")]
            row["reemit"] = t.get("reemit")
        else:
            row["error"] = t.get("error")
        if r.ok and t.get("ok"):
            exp, leap = expected_instant(r.fields)
            row["expected"] = list(exp) if exp else None
            if exp is None:
                row["verdict"] = "n/a (year 0)"
            elif tuple(row["got"]) == exp:
                row["verdict"] = "same instant" + (" (leap :60 read as :59)" if leap else "")
            else:
                row["verdict"] = "WRONG VALUE" + (" (leap second)" if leap else "")
        elif r.ok and not t.get("ok"):
            row["verdict"] = "rejected valid"
        elif not r.ok and t.get("ok"):
            row["verdict"] = "accepted invalid"
        else:
            row["verdict"] = "both reject"
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()

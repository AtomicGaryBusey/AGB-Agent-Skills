#!/usr/bin/env python3
"""Run JSON Schema `format` validators (adapters) over the probe inputs and print verdict tables.

  python3 probe_all.py --set date-time --target 'go: v6 AssertFormat=<cmd>' [--target ...] \
      --jsonl results.jsonl > tables.md

--set date-time : ../inputs.json (schema 2: inputs + legacy) + extras.json["date-time"]
--set date|time : extras.json["date"|"time"]
Each <cmd> is a run_vectors.py adapter: the string goes to stdin, one JSON object comes back.
A validator returns only accept/reject, so verdicts are grammar verdicts (no instant is compared).
"""
import argparse, json, os, shlex, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def verdict(cat, ok):
    if ok is None:
        return "ERROR"
    return {
        "valid": ("conforming", "TOO STRICT"),
        "ext": ("lenient (allowed local ext.)", "conforming"),
        "range": ("conforming", "too strict (range limit)"),
        "leap-real": ("conforming", "too strict (no leap second)"),
        "leap-fake": ("TOO LENIENT", "conforming"),
        "invalid": ("TOO LENIENT", "conforming"),
        # `format: date-time` is RFC 3339 date-time: any RFC 9557 suffix is outside it
        "ixdtf-ok": ("TOO LENIENT (suffix)", "conforming"),
        "ixdtf-may": ("TOO LENIENT (suffix)", "conforming"),
        "ixdtf-reject": ("TOO LENIENT (suffix)", "conforming"),
        "either": ("interpretation (accepted)", "interpretation (rejected)"),
        "option": ("n/a (non-default option)", "n/a (non-default option)"),
    }[cat][0 if ok else 1]


def load_inputs(path=os.path.join(HERE, "..", "inputs.json")):
    """probes/inputs.json schema 2 (inputs + legacy; tools/gen_probe_inputs.py) or the old list."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc if isinstance(doc, list) else doc["inputs"] + doc.get("legacy", [])


def show(s):
    return "`" + json.dumps(s, ensure_ascii=False)[1:-1].replace("|", "\\|").replace("`", "'") + "`"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="date-time", choices=["date-time", "date", "time"])
    ap.add_argument("--target", action="append", required=True, help="NAME=CMD")
    ap.add_argument("--jsonl")
    ap.add_argument("--matrix", action="store_true", help="also print an input x target matrix")
    a = ap.parse_args()
    extras = json.load(open(os.path.join(HERE, "extras.json"), encoding="utf-8"))
    inputs = (load_inputs() if a.set == "date-time" else []) + extras[a.set]
    out = open(a.jsonl, "w", encoding="utf-8") if a.jsonl else None
    table = {}
    for t in a.target:
        name, cmd = t.split("=", 1)
        rows = []
        for rec in inputs:
            p = subprocess.run(shlex.split(cmd), input=rec["s"].encode(), capture_output=True, timeout=60)
            try:
                r = json.loads(p.stdout.decode().strip().splitlines()[-1])
            except Exception:
                r = {"ok": None, "error": "adapter: " + p.stdout.decode()[-200:] + p.stderr.decode()[-200:]}
            cat = rec["cat"]
            if cat.startswith("ixdtf") and "[" not in rec["s"]:  # IXDTF-profile vector without a suffix
                cat = {"ixdtf-ok": "valid", "ixdtf-reject": "invalid", "ixdtf-may": "either"}[cat]
            v = verdict(cat, r.get("ok"))
            rows.append((rec, r, v))
            if out:
                out.write(json.dumps({"api": name, "set": a.set, "id": rec["id"], "s": rec["s"], "cat": rec["cat"],
                                      "ok": r.get("ok"), "error": r.get("error"), "verdict": v}, ensure_ascii=False) + "\n")
        table[name] = rows
        good = sum(v in ("conforming",) for _, _, v in rows)
        print(f"#### {name} — format `{a.set}`\n")
        print(f"{good} of {len(rows)} probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:\n")
        print("| Input | Result | RFC verdict |\n|---|---|---|")
        for rec, r, v in rows:
            if v != "conforming":
                res = "accepted" if r.get("ok") else "rejected" + (": " + str(r.get("error"))[:90].replace("|", "/") if r.get("error") else "")
                print(f"| {show(rec['s'])} | {res} | {v} |")
        print()
    if a.matrix:
        names = list(table)
        print("| id | input | " + " | ".join(names) + " |")
        print("|---|---|" + "---|" * len(names))
        abbrev = {"conforming": "✓", "TOO LENIENT": "**L**", "TOO STRICT": "**S**", "TOO LENIENT (suffix)": "**L**",
                  "lenient (allowed local ext.)": "L", "too strict (range limit)": "s", "too strict (no leap second)": "s"}
        for i, rec in enumerate(inputs):
            print(f"| {rec['id']} | {show(rec['s'])} | " + " | ".join(abbrev.get(table[n][i][2], table[n][i][2]) for n in names) + " |")


if __name__ == "__main__":
    main()

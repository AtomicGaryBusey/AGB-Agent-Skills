#!/usr/bin/env python3
"""Run ste_check.py on the Kestrel eval project and record a finding summary.

This file is outside the skill (scripts/ and references/ do not refer to the
Kestrel fixture). It does not read the answer key.

Output: evals/regression/kestrel-summary.json with the counts by rule, by
severity, the number of groups, and the STE-1.6 word groups.

Usage: python3 evals/regression/kestrel_summary.py [--dictionary FILE] [--out FILE]
Exit status: 0 on success, 2 if the checker could not run.
"""

import argparse
import json
import os
import subprocess
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CHECKER = os.path.join(ROOT, "scripts", "ste_check.py")
PROJECT = os.path.join(ROOT, "evals", "fixtures", "kestrel", "project")
DEFAULT_OUT = os.path.join(HERE, "kestrel-summary.json")


def run_checker(extra, dictionary=None):
    cmd = [sys.executable, CHECKER, "--json"] + extra
    if dictionary:
        cmd[3:3] = ["--dictionary", dictionary]
    cmd.append(os.path.relpath(PROJECT, ROOT))
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if p.returncode not in (0, 1):
        raise RuntimeError("ste_check.py failed (%d): %s" % (p.returncode, p.stderr.strip()))
    return json.loads(p.stdout)


def summarize(dictionary=None):
    data = run_checker([], dictionary)
    unknown = run_checker(["--unknown-words"], dictionary)
    s = data["summary"]
    rel = lambda f: os.path.relpath(os.path.join(ROOT, f), PROJECT)  # noqa: E731
    out = OrderedDict()
    out["checker_version"] = data["meta"]["version"]
    out["dictionary_loaded"] = data["meta"]["dictionary"]["loaded"]
    out["terms"] = OrderedDict([("path", data["meta"]["terms"]["path"] and
                                 rel(data["meta"]["terms"]["path"])),
                                ("count", data["meta"]["terms"]["count"])])
    out["files"] = [rel(f) for f in data["meta"]["files"]]
    out["skipped"] = [rel(f) for f in data["meta"].get("skipped", [])]
    out["findings"] = s["findings"]
    out["groups"] = s["groups"]
    out["by_severity"] = s["by_severity"]
    out["by_rule"] = OrderedDict(sorted(s["by_rule"].items()))
    out["groups_by_rule"] = OrderedDict(sorted(s.get("groups_by_rule", {}).items()))
    out["warn_findings"] = [
        OrderedDict([("file", rel(loc["file"])), ("line", loc["line"]), ("col", loc["col"]),
                     ("rule", f["rule"]), ("message", f["message"])])
        for f in data["findings"] if f["severity"] == "warn" for loc in f["locations"]]
    out["unknown_words"] = [OrderedDict([("word", r["word"]), ("count", r["count"]),
                                         ("tag", r["tag"])]) for r in unknown]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dictionary", help="dictionary cache (default: the checker default)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output JSON file")
    args = ap.parse_args(argv)
    try:
        out = summarize(args.dictionary)
    except (RuntimeError, ValueError) as exc:
        print("kestrel_summary.py: %s" % exc, file=sys.stderr)
        return 2
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("%s: %d findings (%d warn, %d info), %d groups" % (
        os.path.relpath(args.out, ROOT), out["findings"], out["by_severity"]["warn"],
        out["by_severity"]["info"], out["groups"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

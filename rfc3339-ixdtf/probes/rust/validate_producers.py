"""Validate every producer output in probes/results/rust.jsonl with rfcdt.py check --json."""
import json, subprocess, sys, os
RFCDT = os.path.expanduser("~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py")
out = []
for line in open("probes/results/rust.jsonl"):
    r = json.loads(line)
    if r.get("kind") != "format":
        continue
    s = r.get("out")
    if s is None:
        out.append({"api": r["api"], "out": None, "err": r.get("err"), "rfcdt": None}); continue
    if s.startswith('"') and s.endswith('"'):
        s = json.loads(s)
    prof = "ixdtf" if "[" in s else "rfc3339"
    p = subprocess.run([sys.executable, RFCDT, "check", "--json", "--profile", prof, "--", s], capture_output=True, text=True)
    j = json.loads(p.stdout)
    out.append({"api": r["api"], "out": s, "profile": prof, "ok": j["ok"],
                "errors": [e["code"] for e in j["errors"]], "warnings": [w["code"] for w in j["warnings"]]})
json.dump(out, open("producers_rfcdt.json", "w"), indent=1)
for o in out:
    if o["out"] is None:
        print(f'{o["api"][:80]:<81} ERR  {o["err"]}')
    else:
        print(f'{o["api"][:80]:<81} {"OK " if o["ok"] else "BAD"} {o["out"]!r} {o["errors"]} {o["warnings"]}')

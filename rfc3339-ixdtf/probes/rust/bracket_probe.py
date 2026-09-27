"""Re-probe jiff Zoned with each plain probe input given a consistent bracket suffix,
so that the syntax of the RFC 3339 part (not the missing annotation) decides the verdict."""
import json, re, subprocess
A = "./target/release/adapter"
rows = []
_doc = json.load(open("probes/inputs.json", encoding="utf-8"))  # schema 2 (inputs + legacy) or old list
for rec in (_doc if isinstance(_doc, list) else _doc["inputs"] + _doc.get("legacy", [])):
    s = rec["s"]
    if "[" in s:
        continue
    m = re.search(r"([+-−])(\d\d):?(\d\d)?$", s.rstrip("\n"))
    if s.rstrip("\n").endswith(("Z", "z")) or not m:
        sfx = "[Europe/Paris]" if s.rstrip("\n").endswith(("Z","z")) else "[Europe/Paris]"
    else:
        sfx = f"[{m.group(1)}{m.group(2)}:{m.group(3) or '00'}]"
    if s.endswith("\n"):
        t = s[:-1] + sfx + "\n"
    else:
        t = s + sfx
    out = json.loads(subprocess.run([A, "jiff-zoned"], input=t.encode(), capture_output=True).stdout)
    rows.append({"id": rec["id"], "cat": rec["cat"], "input": t, "ok": out.get("ok"), "zoned": out.get("zoned"), "err": out.get("error", "")[:90]})
for r in rows:
    print(f'{r["id"]:<12} {r["cat"]:<9} {"ACCEPT" if r["ok"] else "reject"} {json.dumps(r["input"]):<52} {r["zoned"] or r["err"]}')
json.dump(rows, open("reports/jiff-zoned-bracketed-probes.json", "w"), indent=1)

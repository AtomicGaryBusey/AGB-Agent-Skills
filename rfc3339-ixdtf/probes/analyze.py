#!/usr/bin/env python3
"""Turn probe results (results/*.jsonl) into RFC-verdict tables.

  python3 analyze.py            -> Markdown per-API tables on stdout
  python3 analyze.py --matrix   -> compact API x input verdict matrix (for review)

Verdict rules (consumer side):
  cat=valid      accept+same instant -> conforming; accept+different -> WRONG VALUE / lossy; reject -> too strict
  cat=ext        (space separator; RFC 3339 §5.6 NOTE lets applications choose it) accept -> lenient (allowed ext); reject -> conforming
  cat=range      (year 0000: grammar-valid)                     reject -> too strict (range)
  cat=leap-real  accept -> conforming; reject -> too strict (no leap second)
  cat=leap-fake  accept -> too lenient; reject -> conforming
  cat=invalid    accept -> too lenient; reject -> conforming
  cat=ixdtf-ok   mode 3339: accept -> too lenient (suffix); reject -> conforming
                 mode ixdtf: accept -> conforming; reject -> too strict
  cat=ixdtf-reject accept -> too lenient (mode ixdtf: VIOLATES RFC 9557 MUST); reject -> conforming
  cat=ixdtf-may  either -> conforming (MAY act); records which value won
  cat=either     RFC permits both verdicts -> interpretation (records the choice)
  cat=option     vector needs a non-default option -> n/a (grade with run_vectors.py)
Inputs: probes/inputs.json schema 2 (inputs + legacy; tools/gen_probe_inputs.py).
Producer side: output is checked against the RFC 3339 date-time ABNF + RFC 9557 suffix ABNF.
"""
import json, os, re, sys, glob
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))


def load_inputs(path=os.path.join(HERE, "inputs.json")):
    """Probe inputs: schema 2 ({"inputs", "legacy"}; tools/gen_probe_inputs.py) or the old list."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc if isinstance(doc, list) else doc["inputs"] + doc.get("legacy", [])


_ALL = load_inputs()
INPUTS = {r["id"]: r for r in _ALL}
ORDER = [r["id"] for r in _ALL]

D = "[0-9]"
RFC3339 = re.compile(
    rf"^(?P<y>{D}{{4}})-(?P<mo>{D}{{2}})-(?P<d>{D}{{2}})[Tt](?P<h>{D}{{2}}):(?P<mi>{D}{{2}}):(?P<s>{D}{{2}})"
    rf"(?P<f>\.{D}+)?(?P<off>[Zz]|[+-]{D}{{2}}:{D}{{2}})")
TZPART = r"(?:[A-Za-z._][A-Za-z._0-9+\-]*)"
SUFFIX = re.compile(
    rf"^(?:\[!?(?:{TZPART}(?:/{TZPART})*|[+-]{D}{{2}}:{D}{{2}})\])?(?:\[!?[a-z_][a-z_0-9\-]*=[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\])*$")


def ref_utc(s):
    """Expected UTC instant (YYYY-MM-DDTHH:MM:SS.fffffffff-ish) for the RFC 3339 part, or None."""
    m = RFC3339.match(s)
    if not m:
        return None
    y, mo, d, h, mi, sec = (int(m[k]) for k in ("y", "mo", "d", "h", "mi", "s"))
    frac = (m["f"] or ".")[1:]
    try:
        base = datetime(max(y, 1), mo, d, h, mi, min(sec, 59))
    except ValueError:
        return None
    off = m["off"]
    if off not in ("Z", "z"):
        sign = 1 if off[0] == "+" else -1
        base -= sign * timedelta(hours=int(off[1:3]), minutes=int(off[4:6]))
    return base.strftime("%Y-%m-%dT%H:%M:%S").replace(f"{max(y,1):04d}", f"{y:04d}", 1) if y == 0 else base.strftime("%Y-%m-%dT%H:%M:%S"), frac


NORM = re.compile(r"^(naive:)?([+-]?\d{4,6})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d+))?Z?$")


def norm(u):
    if u is None:
        return None
    m = NORM.match(u.strip())
    if not m:
        return None
    y = int(m[2])
    return (bool(m[1]), f"{y:04d}-{m[3]}-{m[4]}T{m[5]}:{m[6]}:{m[7]}", (m[8] or "").rstrip("0"))


def value_check(rec, res):
    """Compare API's instant to the reference instant for an accepted, grammar-valid input."""
    exp = ref_utc(rec["s"])
    got = norm(res.get("utc"))
    if exp is None or got is None:
        return ""
    naive, ts, frac = got
    ets, efrac = exp[0], exp[1].rstrip("0")
    if naive:
        return "offset discarded (naive result)"
    if ts != ets:
        return f"instant differs: got {ts}Z, expected {ets}Z"
    if frac != efrac:
        if efrac.startswith(frac):
            return f"fraction truncated to {len(frac) if frac else 0}→ precision"
        n = len(frac)
        if n and n < len(efrac) and int(frac) == round(int(efrac[:n + 1]) / 10):
            return f"fraction rounded to {n}→ precision"
        return f"fraction changed: .{frac or '0'} vs .{efrac}"
    return ""


def verdict(rec, res):
    cat, ok, mode = rec["cat"], res.get("ok"), res.get("mode") or "3339"
    if cat == "option":
        return "n/a (non-default option: grade with run_vectors.py)"
    if cat == "either":
        return "interpretation (" + ("accepted" if ok else "rejected") + ")"
    api = res["api"]
    if res.get("out") == "valid" and res.get("utc") is None:  # validator
        mode = "validator"
    if cat == "valid":
        if not ok:
            if mode == "ixdtf-zoned" and "annotation" in (res.get("err") or "").lower():
                return "n/a (API requires [zone])"
            if rec["id"] == "off-2359":
                return "too strict (offset range)"
            return "TOO STRICT"
        vc = value_check(rec, res) if mode != "validator" else ""
        if vc.startswith(("fraction truncated", "fraction rounded")):
            return "conforming (lossy: " + vc.replace("→ precision", " digits") + ")"
        return "WRONG VALUE: " + vc if vc else "conforming"
    if cat == "ext":
        return "lenient (allowed local ext.)" if ok else "conforming (strict ABNF)"
    if cat == "range":
        if ok:
            return "conforming"
        return "n/a (API requires [zone])" if mode == "ixdtf-zoned" and "annotation" in (res.get("err") or "").lower() else "too strict (range limit)"
    if cat == "leap-real":
        if ok:
            return "conforming (→ " + (norm(res.get("utc")) or (0, "?", ""))[1][11:] + ")" if res.get("utc") else "conforming"
        if mode == "ixdtf-zoned" and "annotation" in (res.get("err") or "").lower():
            return "n/a (API requires [zone])"
        return "too strict (no leap second)"
    if cat == "leap-fake":
        return "TOO LENIENT" if ok else "conforming"
    if cat == "invalid":
        if not ok:
            return "conforming"
        extra = ""
        g = norm(res.get("utc"))
        if g and g[0]:
            extra = " (naive/local result)"
        elif rec["id"] == "no-off" and g:
            extra = " (as host-local time)" if g[1].endswith("16:00:00") else " (as UTC)" if g[1].endswith("12:00:00") else ""
        elif rec["id"].startswith(("feb", "apr")) and g:
            extra = f" (rolled over to {g[1][:10]})"
        elif rec["id"] == "h24" and g:
            extra = f" (→ {g[1][:10]} {g[1][11:]})"
        return "TOO LENIENT" + extra
    if cat == "ixdtf-ok":
        if mode in ("ixdtf", "ixdtf-zoned"):
            if ok:
                return "conforming"
            if mode == "ixdtf-zoned" and "annotation" in (res.get("err") or "").lower():
                return "n/a (API requires [zone])"
            return "TOO STRICT (vs RFC 9557)"
        return "lenient (accepts suffix)" if ok else "conforming (3339-only)"
    if cat == "ixdtf-reject":
        if not ok:
            return "conforming"
        if "offset:'use'" in api and rec["id"].startswith("x-incons"):
            return "conforming (caller opted into offset:'use' = programmed resolution, §3.4)"
        return "VIOLATES 9557 MUST (accepted)" if mode in ("ixdtf", "ixdtf-zoned") else "TOO LENIENT (suffix)"
    if cat == "ixdtf-may":
        if not ok:
            return "conforming (rejects; MAY)"
        g = norm(res.get("utc"))
        if g and g[1] == "2025-12-31T19:00:00":
            return "conforming (MAY; offset wins)"
        if g and g[1] == "2025-12-31T23:00:00":
            return "conforming (MAY; zone wins, local time kept)"
        return "conforming (MAY)" if mode != "3339" else "lenient (accepts suffix)"
    return "?"


FMT_OVERRIDE = [  # semantic defects a grammar check cannot see (true instant is 2026-09-24T12:00:00Z unless noted)
    ("lies", "WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z)"),
    ("[default TZ!]", "WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z)"),
    ('"o") CurrentCulture=th-TH', "conforming (\"o\" is culture-invariant)"),
    ("th-TH", "WRONG VALUE (Thai Buddhist calendar year from culture)"),
    ("ar-SA", "WRONG VALUE (Um Al-Qura calendar date from culture)"),
    ("week-year", "WRONG VALUE (week-based year: 2026-12-28 printed as 2027)"),
    ("week-based-year", "WRONG VALUE (week-based year: 2026-12-28 printed as 2027)"),
    ("+00:00:30", "WRONG VALUE (offset seconds dropped: string denotes 12:00:30Z, true instant 12:00:00Z)"),
    ("1850 Europe/Paris, LMT) #toString", "grammar-valid, lossy (LMT +00:09:21 rounded to +00:09: string instant off by 21 s)"),
]


def fmt_verdict(out, api=""):
    if out is None:
        return "n/a"
    for key, v in FMT_OVERRIDE:
        if key in api:
            return v
    s = str(out)
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    m = RFC3339.match(s)
    if m and SUFFIX.match(s[m.end():]):
        if m.group("off") == "z" or "t" in s[10:11]:
            return "conforming (but SHOULD use upper case)"
        if s[m.end():]:
            return "conforming (RFC 9557)"
        return "conforming"
    why = []
    if re.match(r"^[+-]\d{4,}-|^\d{5,}-", s): why.append("expanded/signed year")
    if re.match(r"^\d{4}-\d\d-\d\d \d", s): why.append("space separator")
    if re.match(r"^[+-]?\d+-\d\d-\d\dT\d\d:\d\d(?!:)", s): why.append("no seconds")
    if re.search(r"[+-]\d\d:\d\d:\d\d(\[|$)", s): why.append("offset has seconds")
    if re.search(r"T[\d:.]+[+-]\d{4}$", s): why.append("offset without colon")
    if re.search(r"T\d\d\.\d\d", s): why.append("'.' time separator (culture)")
    if re.match(r"^[+-]?\d+-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?$", s): why.append("no offset")
    if re.search(r"\d{2}:\d{2}:\d{2} UTC$", s): why.append("' UTC' suffix")
    if not re.match(r"^[+-]?\d", s): why.append("not ISO-shaped")
    if re.match(r"^\d+/\d+/\d+", s): why.append("culture format")
    return "WRONG OUTPUT (" + (", ".join(why) or "grammar") + ")"


SKIP_TABLE = {"Temporal.PlainDateTime.from"}  # not an instant parser; discussed in prose


def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "results", "*.jsonl"))):
        for line in open(f):
            line = line.strip()
            if line.startswith("{"):
                r = json.loads(line)
                if r.get("api") not in SKIP_TABLE and r.get("kind") in ("parse", "format"):
                    rows.append(r)
    return rows


def esc(x):
    return str(x).replace("|", "\\|").replace("\n", "\\n")


def show_input(s):
    return "`" + esc(json.dumps(s, ensure_ascii=True)[1:-1]) + "`"


def main():
    rows = load()
    apis = {}
    for r in rows:
        apis.setdefault((r["lang"], r["kind"], r["api"]), []).append(r)
    if "--glance" in sys.argv:
        cols = ["lc-z", "space", "off-minus0", "off-nocolon", "no-sec", "no-off", "comma", "h24", "leap-real", "leap-fake",
                "feb30-2024", "frac12", "trail-ws", "y+10000", "x-tz", "x-unk!", "x-incons!"]
        def sym(v):
            if v.startswith("n/a"): return "–"
            if v.startswith("VIOLATES"): return "**!!**"
            if v.startswith("WRONG"): return "**W**"
            if "lossy" in v: return "✓~"
            if v.startswith("conforming"): return "✓"
            if v.startswith(("TOO LENIENT", "lenient")): return "L" if v.startswith("lenient") else "**L**"
            if v.lower().startswith("too strict"): return "s" if v.startswith("too strict") else "**S**"
            return "?"
        print("| API | " + " | ".join(f"`{c}`" for c in cols) + " |")
        print("|---|" + "---|" * len(cols))
        for (lang, kind, api), rs in apis.items():
            if kind != "parse":
                continue
            by = {r["id"]: r for r in rs}
            print(f"| {lang}: `{esc(api)}` | " + " | ".join(sym(verdict(INPUTS[c], by[c])) if c in by else " " for c in cols) + " |")
        return
    if "--deviations" in sys.argv:
        # Compact form for the catalog: per API, only rows that are not plain "conforming".
        for (lang, kind, api), rs in apis.items():
            if kind != "parse":
                continue
            rs = sorted(rs, key=lambda r: ORDER.index(r["id"]))
            dev = []
            for r in rs:
                v = verdict(INPUTS[r["id"]], r)
                if v == "conforming" or v.startswith(("conforming (3339-only)", "conforming (rejects; MAY)", "conforming (strict ABNF)", "n/a")):
                    continue
                dev.append((r, v))
            na = sum(1 for r in rs if verdict(INPUTS[r["id"]], r).startswith("n/a"))
            quiet = len(rs) - len(dev) - na
            print(f"#### {lang} — `{api}`\n")
            extra = f" {na} plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation (by design; n/a)." if na else ""
            if not dev:
                print(f"All {quiet} applicable probe inputs behaved as the RFCs require.{extra}\n")
                continue
            print(f"{quiet} of {len(rs)} probe inputs behaved as the RFCs require (not listed).{extra} Deviations and notable behaviour:\n")
            print("| Input | Result | RFC verdict |\n|---|---|---|")
            for r, v in dev:
                if r.get("ok"):
                    res = r.get("utc") if r.get("utc") else r.get("out")
                    res = "accepted → " + (f"UTC {res}" if r.get("utc") else str(res))
                else:
                    res = "rejected: " + (r.get("err") or "").split("\n")[0]
                print(f"| {show_input(r['input'])} | {esc(res[:90])} | {v} |")
            print()
        for lang in sorted({k[0] for k in apis}):
            fm = [r for (l, kind, api), rs in apis.items() if l == lang and kind == "format" for r in rs]
            if fm:
                print(f"#### {lang} — formatters (producer side)\n")
                print("| Call | Output | RFC verdict |\n|---|---|---|")
                for r in fm:
                    out = show_input(r.get("out")) if r.get("out") is not None else "✗ " + esc(r.get("err", ""))
                    print(f"| `{esc(r['api'])}` | {out} | {fmt_verdict(r.get('out'), r['api'])} |")
                print()
        return
    if "--summary" in sys.argv:
        for (lang, kind, api), rs in apis.items():
            if kind != "parse":
                continue
            bad = {}
            for r in rs:
                v = verdict(INPUTS[r["id"]], r)
                if not v.startswith("conforming") or "lossy" in v:
                    bad.setdefault(v.split(" (")[0].split(":")[0], []).append(r["id"])
            print(f"{lang}::{api}")
            for k, ids in bad.items():
                print(f"    {k}: {' '.join(ids)}")
        return
    if "--matrix" in sys.argv:
        for (lang, kind, api), rs in apis.items():
            if kind != "parse":
                continue
            print(f"\n== {lang} :: {api}")
            for r in rs:
                v = verdict(INPUTS[r["id"]], r)
                if v.startswith("conforming") and "lossy" not in v and "→" not in v and "wins" not in v:
                    continue
                print(f"   {r['id']:<13} {v:<45} {(r.get('utc') or r.get('err') or '')[:70]}")
        for (lang, kind, api), rs in apis.items():
            if kind == "format":
                for r in rs:
                    print(f"FMT {lang:<10} {api[:70]:<70} {r.get('out')!r:<45} {fmt_verdict(r.get('out'), r['api'])}")
        return
    langs = {}
    for (lang, kind, api), rs in apis.items():
        langs.setdefault(lang, []).append((kind, api, rs))
    for lang, items in langs.items():
        print(f"\n### {lang}\n")
        for kind, api, rs in items:
            if kind == "parse":
                print(f"#### `{api}` (parse)\n")
                print("| Input | Result | RFC verdict |\n|---|---|---|")
                for r in sorted(rs, key=lambda r: ORDER.index(r["id"])):
                    res = (r.get("out") if r.get("ok") else "✗ " + (r.get("err") or ""))
                    if r.get("ok") and r.get("utc") and r.get("utc") != r.get("out"):
                        res = f"{r.get('out')} ⇒ UTC {r.get('utc')}"
                    print(f"| {show_input(r['input'])} | {esc(str(res)[:110])} | {verdict(INPUTS[r['id']], r)} |")
                print()
        fmts = [r for kind, api, rs in items if kind == "format" for r in rs]
        if fmts:
            print(f"#### {lang} formatters (produce)\n")
            print("| Call | Output | RFC verdict |\n|---|---|---|")
            for r in fmts:
                print(f"| `{esc(r['api'])}` | {show_input(r.get('out')) if r.get('out') is not None else '✗ ' + esc(r.get('err', ''))} | {fmt_verdict(r.get('out'), r['api'])} |")
            print()


if __name__ == "__main__":
    main()

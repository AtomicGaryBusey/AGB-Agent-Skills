#!/usr/bin/env python3
"""Generate probes/inputs.json from vectors/vectors.json (build helper).

    python3 tools/gen_probe_inputs.py            # write probes/inputs.json
    python3 tools/gen_probe_inputs.py --check    # exit 1 if probes/inputs.json is stale
    python3 tools/gen_probe_inputs.py --out PATH # write elsewhere

Why: the ecosystem verdict tables were first made from 59 hand-picked probe
strings, not from the conformance vectors.  This file makes the vectors the
single source: every vector becomes a probe input that carries the vector's
expect / profile / options / requires / checks, so a legacy probe program
(probes/probe_*.{py,mjs,rb,cs,java}, go, rust, swift, sql, protobuf,
jsonschema) reads the same strings that run_vectors.py grades.

Schema (``"schema": 2``)::

    {"schema": 2, "description": ..., "vectors_sha256": ...,
     "categories": {cat: meaning},
     "inputs": [ {"id", "s", "cat", "note", "vector", "profile", "expect",
                  "reason", "section", "checks", ["options"], ["requires"],
                  ["interpretation"], ["resolvable"], ["fields"]} ...],
     "legacy": [ {"id", "s", "cat", "note", "legacy_reason", "rfcdt_reason",
                  "related_vectors"} ...]}

* ``inputs``: one entry per vector, in vectors.json order.  ``s`` is the
  vector's ``input``.  When one of the original 59 probe strings is
  byte-identical to a vector input, that entry keeps the original probe
  ``id``/``cat``/``note`` (``vector`` gives the vector id); otherwise ``id``
  is the vector id and ``cat`` is derived (see ``categories``).
* ``legacy``: original probe strings with no byte-identical vector.  They
  stay so the ecosystem tables' column ids remain reproducible.
  ``rfcdt_reason`` is rfcdt's code for the string (fixed here, so the output
  does not depend on host tz data); ``related_vectors`` lists up to 5
  vectors of the same profile with that code (none for plain "ok").

Legacy probe programs should read ``inputs + legacy`` (helper: every probe
accepts the old list form too).  run_vectors.py adapters do not read this
file at all: they get the vectors on stdin.
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORS = os.path.join(ROOT, "vectors", "vectors.json")
OUT = os.path.join(ROOT, "probes", "inputs.json")

# The original 59 probe strings (2026-09-24 ecosystem run): id, string, category,
# note, and rfcdt's reason code for the string under its natural profile
# (ixdtf when it has a suffix).  Fixed here so the generator is host-independent.
LEGACY = [
    ("base", "2026-09-24T12:00:00Z", "valid", "canonical", "ok"),
    ("lc-t", "2026-09-24t12:00:00Z", "valid", "lowercase t (§5.6 NOTE)", "R3339-5.6/lowercase-letter"),
    ("lc-z", "2026-09-24T12:00:00z", "valid", "lowercase z (§5.6 NOTE)", "R3339-5.6/lowercase-letter"),
    ("space", "2026-09-24 12:00:00Z", "ext", "space separator (§5.6 NOTE: applications may choose)",
     "R3339-5.6/date-time-separator"),
    ("off-plus0", "2026-09-24T12:00:00+00:00", "valid", "+00:00", "ok"),
    ("off-minus0", "2026-09-24T12:00:00-00:00", "valid", "-00:00 (=Z per RFC 9557 §2)",
     "R9557-2.3/negative-zero-offset"),
    ("off-2359", "2026-09-24T12:00:00+23:59", "valid", "max legal offset", "ok"),
    ("off-0530", "2026-09-24T12:00:00+05:30", "valid", "half-hour offset", "ok"),
    ("off-2400", "2026-09-24T12:00:00+24:00", "invalid", "offset hour 24", "R3339-5.6/time-numoffset-hour"),
    ("off-2360", "2026-09-24T12:00:00+23:60", "invalid", "offset minute 60", "R3339-5.6/time-numoffset-minute"),
    ("off-nocolon", "2026-09-24T12:00:00+0200", "invalid", "offset without colon", "R3339-5.6/time-numoffset"),
    ("off-hh", "2026-09-24T12:00:00+02", "invalid", "offset hours only", "R3339-5.6/time-numoffset"),
    ("h24", "2026-09-24T24:00:00Z", "invalid", "hour 24", "R3339-5.7/time-hour-24"),
    ("leap-real", "2016-12-31T23:59:60Z", "leap-real", "real leap second", "ok"),
    ("leap-realoff", "2016-12-31T18:59:60-05:00", "leap-real", "real leap second at -05:00", "ok"),
    ("leap-fake", "2026-09-24T23:59:60Z", "leap-fake", "60 on a non-leap date", "R3339-5.7/leap-second-position"),
    ("leap-mid", "2026-09-24T12:00:60Z", "leap-fake", "60 mid-day (never legal)", "R3339-5.7/leap-second-position"),
    ("frac1", "2026-09-24T12:00:00.1Z", "valid", "1 frac digit", "ok"),
    ("frac3", "2026-09-24T12:00:00.123Z", "valid", "3 frac digits", "ok"),
    ("frac6", "2026-09-24T12:00:00.123456Z", "valid", "6 frac digits", "ok"),
    ("frac7", "2026-09-24T12:00:00.1234567Z", "valid", "7 frac digits", "ok"),
    ("frac9", "2026-09-24T12:00:00.123456789Z", "valid", "9 frac digits", "ok"),
    ("frac12", "2026-09-24T12:00:00.123456789012Z", "valid", "12 frac digits (grammar: 1*DIGIT)", "ok"),
    ("frac-empty", "2026-09-24T12:00:00.Z", "invalid", "dot with no digits", "R3339-5.6/time-secfrac"),
    ("comma", "2026-09-24T12:00:00,5Z", "invalid", "comma decimal sign", "R3339-5.6/time-secfrac"),
    ("no-sec", "2026-09-24T12:00Z", "invalid", "no seconds", "R3339-5.6/time-second"),
    ("no-off", "2026-09-24T12:00:00", "invalid", "no offset (local time)", "R3339-5.6/time-offset"),
    ("date-only", "2026-09-24", "invalid", "full-date only (not date-time)", "R3339-5.6/date-time-separator"),
    ("basic", "20260924T120000Z", "invalid", "ISO 8601 basic format", "R3339-5.6/date-separator"),
    ("week", "2026-W39-4T12:00:00Z", "invalid", "ISO week date", "R3339-5.6/date-month"),
    ("ordinal", "2026-267T12:00:00Z", "invalid", "ISO ordinal date", "R3339-5.6/date-month"),
    ("one-digit", "2026-9-24T12:00:00Z", "invalid", "1-digit month", "R3339-5.6/date-month"),
    ("lead-ws", " 2026-09-24T12:00:00Z", "invalid", "leading space", "R3339-5.6/date-fullyear"),
    ("trail-ws", "2026-09-24T12:00:00Z\n", "invalid", "trailing newline", "R3339-5.6/trailing-characters"),
    ("arabic-dig", "٢٠٢٦-09-24T12:00:00Z", "invalid", "non-ASCII digits (ABNF DIGIT = %x30-39)",
     "R3339-5.6/date-fullyear"),
    ("y0000", "0000-01-01T00:00:00Z", "range", "year 0000 (grammar-valid; range local)", "ok"),
    ("y0001", "0001-01-01T00:00:00Z", "valid", "year 0001", "ok"),
    ("y9999", "9999-12-31T23:59:59Z", "valid", "year 9999", "ok"),
    ("y10000", "10000-01-01T00:00:00Z", "invalid", "5-digit year", "R3339-5.6/date-separator"),
    ("y+10000", "+10000-01-01T00:00:00Z", "invalid", "signed 5-digit year", "R3339-5.6/date-fullyear"),
    ("y+6", "+002026-09-24T12:00:00Z", "invalid", "ISO expanded 6-digit year", "R3339-5.6/date-fullyear"),
    ("y-0001", "-0001-01-01T00:00:00Z", "invalid", "negative year", "R3339-5.6/date-fullyear"),
    ("feb29-2026", "2026-02-29T12:00:00Z", "invalid", "Feb 29 non-leap year", "R3339-5.7/date-mday"),
    ("feb30-2024", "2024-02-30T12:00:00Z", "invalid", "Feb 30", "R3339-5.7/date-mday"),
    ("feb29-2024", "2024-02-29T12:00:00Z", "valid", "Feb 29 leap year", "ok"),
    ("apr31", "2026-04-31T12:00:00Z", "invalid", "Apr 31", "R3339-5.7/date-mday"),
    ("x-tz", "2026-09-24T14:00:00+02:00[Europe/Paris]", "ixdtf-ok", "elective IANA zone, consistent", "ok"),
    ("x-tz!", "2026-09-24T14:00:00+02:00[!Europe/Paris]", "ixdtf-ok", "critical IANA zone, consistent", "ok"),
    ("x-Ztz", "2026-09-24T12:00:00Z[Europe/Paris]", "ixdtf-ok", "Z + zone (no inconsistency, §3.4 Fig 2)", "ok"),
    ("x-Ztz!", "2026-09-24T12:00:00Z[!Europe/Paris]", "ixdtf-ok", "Z + critical zone", "ok"),
    ("x-cal", "2026-09-24T12:00:00Z[u-ca=hebrew]", "ixdtf-ok", "elective calendar tag", "ok"),
    ("x-unk", "2026-09-24T12:00:00Z[x-foo=bar]", "ixdtf-ok", "elective unknown tag (ignore)",
     "R9557-3.3/elective-unknown-key"),
    ("x-unk!", "2026-09-24T12:00:00Z[!x-foo=bar]", "ixdtf-reject", "critical unknown tag: MUST treat as error (§3.3)",
     "R9557-3.3/critical-unknown-key"),
    ("x-incons", "2026-01-01T00:00:00+05:00[Europe/Paris]", "ixdtf-may", "inconsistent offset, elective zone: MAY act (§3.4)",
     "R9557-3.4/elective-inconsistency"),
    ("x-incons!", "2026-01-01T00:00:00+05:00[!Europe/Paris]", "ixdtf-reject",
     "inconsistent offset, critical zone: MUST act (§3.4)", "R9557-3.4/critical-inconsistency"),
    ("x-offzone", "2026-09-24T14:00:00+02:00[+02:00]", "ixdtf-ok", "offset time zone (discouraged)",
     "R9557-1.2/offset-time-zone"),
    ("x-dupcal!", "2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]", "ixdtf-reject",
     "conflicting duplicate key, one critical (§3.3)", "R9557-3.3/critical-inconsistent-duplicate"),
    ("x-badzone", "2026-09-24T12:00:00Z[!Mars/Olympus]", "ixdtf-reject", "unknown critical zone name",
     "R9557-4.1/critical-unknown-time-zone"),
    ("x-upkey", "2026-09-24T12:00:00Z[U-CA=hebrew]", "invalid", "uppercase suffix key (grammar: lcalpha)",
     "R9557-4.1/suffix-key"),
]

CATEGORIES = {
    "valid": "grammar-valid RFC 3339 date-time; accept with the same instant",
    "invalid": "invalid; accept = too lenient",
    "ext": "space separator: RFC 3339 §5.6 NOTE lets applications choose it (legacy)",
    "range": "grammar-valid but outside many engines' range (year 0000); reject = too strict (range)",
    "leap-real": "a real leap second; reject = too strict (no leap second)",
    "leap-fake": "second 60 where no leap second can be; accept = too lenient",
    "ixdtf-ok": "valid IXDTF suffix; an RFC 3339-only consumer should reject",
    "ixdtf-reject": "IXDTF string a consumer MUST reject",
    "ixdtf-may": "RFC 9557 permits either verdict (suffix); records the target's choice",
    "either": "RFC permits either verdict (see interpretation); records the target's choice",
    "option": "verdict depends on a non-default option (see options); legacy analyzers skip it",
}

VECTOR_KEYS = ("options", "requires", "interpretation", "resolvable", "fields")


def derive_cat(vec):
    if vec.get("options"):
        return "option"
    exp, prof, reason = vec["expect"], vec["profile"], vec.get("reason", "")
    if exp == "either":
        return "ixdtf-may" if prof == "ixdtf" else "either"
    leap = "leap-second" in reason
    if prof == "ixdtf" and "[" in vec["input"]:
        return "ixdtf-ok" if exp == "valid" else "ixdtf-reject"
    # ixdtf-profile vectors with no suffix grade like plain RFC 3339 strings
    if exp == "valid":
        return "leap-real" if ":60" in vec["input"][11:20] else "valid"
    return "leap-fake" if leap else "invalid"


def build(vectors_path=VECTORS):
    with open(vectors_path, "rb") as fh:
        raw = fh.read()
    vectors = json.loads(raw)["vectors"]
    legacy_by_s = {}
    for rec in LEGACY:
        legacy_by_s.setdefault(rec[1], rec)
    used = set()
    inputs = []
    for vec in vectors:
        leg = legacy_by_s.get(vec["input"])
        # A legacy string that matches vectors of both profiles attaches to the first.
        if leg and leg[0] not in used:
            used.add(leg[0])
            pid, cat, note = leg[0], leg[2], leg[3]
        else:
            pid, cat, note = vec["id"], derive_cat(vec), vec.get("notes", "")
        ent = {"id": pid, "s": vec["input"], "cat": cat, "note": note, "vector": vec["id"],
               "profile": vec["profile"], "expect": vec["expect"], "reason": vec["reason"],
               "section": vec["section"], "checks": vec["checks"]}
        for k in VECTOR_KEYS:
            if k in vec:
                ent[k] = vec[k]
        inputs.append(ent)
    legacy = []
    for pid, s, cat, note, code in LEGACY:
        if pid in used:
            continue
        prof = "ixdtf" if cat.startswith("ixdtf") or "[" in s else "rfc3339"
        related = [] if code == "ok" else [
            v["id"] for v in vectors if v["profile"] == prof and v["reason"] == code][:5]
        legacy.append({"id": pid, "s": s, "cat": cat, "note": note,
                       "legacy_reason": "no vector in vectors/vectors.json has this exact input "
                                        "string; kept so the ecosystem tables' column ids stay "
                                        "reproducible (grade with related_vectors)",
                       "rfcdt_reason": code, "profile": prof, "related_vectors": related})
    ids = [e["id"] for e in inputs + legacy]
    assert len(ids) == len(set(ids)), "duplicate probe ids"
    return {
        "schema": 2,
        "description": "Probe inputs generated by tools/gen_probe_inputs.py from "
                       "vectors/vectors.json (do not edit by hand). 'inputs' has one entry per "
                       "vector ('vector' = vector id; 's' = input string; expect/profile/"
                       "options/requires/checks copied from the vector); 'legacy' keeps the "
                       "original 2026-09-24 probe strings that have no byte-identical vector. "
                       "Legacy probe programs read inputs + legacy; run_vectors.py adapters "
                       "(probes/README.md) get the vectors directly.",
        "vectors_sha256": hashlib.sha256(raw).hexdigest(),
        "categories": CATEGORIES,
        "inputs": inputs,
        "legacy": legacy,
    }


def render(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vectors", default=VECTORS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="write nothing; exit 1 if --out differs from what would be generated")
    a = ap.parse_args(argv)
    text = render(build(a.vectors))
    if a.check:
        try:
            with open(a.out, encoding="utf-8") as fh:
                cur = fh.read()
        except OSError:
            cur = None
        if cur != text:
            print(f"{os.path.relpath(a.out, ROOT)} is stale: run python3 tools/gen_probe_inputs.py",
                  file=sys.stderr)
            return 1
        print(f"{os.path.relpath(a.out, ROOT)} is up to date")
        return 0
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    doc = json.loads(text)
    print(f"wrote {os.path.relpath(a.out, ROOT)}: {len(doc['inputs'])} vector inputs, "
          f"{len(doc['legacy'])} legacy")
    return 0


if __name__ == "__main__":
    sys.exit(main())

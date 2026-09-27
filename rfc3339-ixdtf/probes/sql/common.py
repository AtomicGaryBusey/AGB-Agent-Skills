"""Shared helpers for the SQL probes (SQLite, PostgreSQL).

Expected instants come from rfcdt (the skill's reference parser), never from the
engine under test.  Paths are relative to this file, so the directory can be
copied anywhere inside the skill.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import rfcdt  # noqa: E402

INPUTS = os.path.join(SKILL, "probes", "inputs.json")
VECTORS = os.path.join(SKILL, "vectors", "vectors.json")


def load_inputs():
    """probes/inputs.json schema 2 (inputs + legacy; tools/gen_probe_inputs.py) or the old list."""
    with open(INPUTS, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc if isinstance(doc, list) else doc["inputs"] + doc.get("legacy", [])


def effective_cat(rec):
    """Category for an RFC 3339-only consumer: an IXDTF-profile vector with no suffix is
    graded like the plain RFC 3339 string it is."""
    cat = rec["cat"]
    if cat.startswith("ixdtf") and "[" not in rec["s"]:
        return {"ixdtf-ok": "valid", "ixdtf-reject": "invalid", "ixdtf-may": "either"}[cat]
    return cat


def serve_adapter(answer):
    """run_vectors.py adapter loop: batch (RFCDT_BATCH=1, JSON lines) or one string on stdin.

    answer(s) -> dict with at least "ok"."""
    if os.environ.get("RFCDT_BATCH") == "1":
        for line in sys.stdin:
            if line.strip():
                req = json.loads(line)
                print(json.dumps({"id": req["id"], **answer(req["input"])}, ensure_ascii=False),
                      flush=True)
    else:
        s = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
        print(json.dumps(answer(s), ensure_ascii=False))


def rfcdt_fields(s, profile="rfc3339"):
    """rfcdt fields for s, or None when rfcdt rejects it (profile default options)."""
    r = rfcdt.check(s, profile=profile)
    ok = r.ok if hasattr(r, "ok") else r["ok"]
    fields = r.fields if hasattr(r, "fields") else r["fields"]
    return fields if ok else None


def expected_utc(fields):
    """True UTC instant (ISO text, microsecond precision, no suffix) from rfcdt fields.

    Returns (text, digits) where digits is the full secfrac string, or (None, None)
    when it cannot be computed (leap second, year outside datetime's range).
    """
    if not fields or fields.get("offset_minutes") is None:
        return None, None
    sec = fields["second"]
    if sec == 60:
        return None, None
    frac = fields.get("secfrac") or ""
    us = int((frac + "000000")[:6])
    try:
        local = _dt.datetime(fields["year"], fields["month"], fields["day"],
                             fields["hour"], fields["minute"], sec, us)
        utc = local - _dt.timedelta(minutes=fields["offset_minutes"])
    except (ValueError, OverflowError):
        return None, None
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%f").rjust(26, "0"), frac


def compare_instant(expected, frac, got, precision_digits):
    """Compare engine UTC text (YYYY-MM-DDTHH:MM:SS[.fff]) with the expected one.

    Returns "same", "lossy" (differs only below the engine precision), or "WRONG".
    """
    if expected is None or got is None:
        return None
    def norm(t):
        t = t.replace(" ", "T")
        if "." not in t:
            t += ".000000"
        head, f = t.split(".", 1)
        return head, (f + "000000")[:6]
    eh, ef = norm(expected)
    gh, gf = norm(got)
    if (eh, ef) == (gh, gf) and len(frac or "") <= precision_digits:
        return "same"
    e = _dt.datetime.fromisoformat(eh + "." + ef)
    try:
        g = _dt.datetime.fromisoformat(gh + "." + gf)
    except ValueError:
        return "WRONG"
    # full-precision expected value (can carry more than 6 digits)
    exact = e.timestamp() + float("0." + (frac or "0")) - e.microsecond / 1e6
    if abs(g.timestamp() - exact) < 10 ** (-precision_digits) + 1e-9:
        return "same" if len((frac or "").rstrip("0")) <= precision_digits else "lossy"
    return "WRONG"


def classify(cat, ok, cmp=None, suffix_note=""):
    """Map an inputs.json category + outcome to an ecosystem.md verdict."""
    if cat in ("valid",):
        if not ok:
            return "TOO STRICT"
        if cmp == "WRONG":
            return "WRONG VALUE"
        if cmp == "lossy":
            return "conforming (lossy)"
        return "conforming"
    if cat == "ext":
        return "lenient (allowed local ext.)" if ok else "conforming"
    if cat == "either":
        return "interpretation (" + ("accepted" if ok else "rejected") + ")"
    if cat == "option":
        return "n/a (non-default option: grade with run_vectors.py)"
    if cat == "invalid":
        return "TOO LENIENT" if ok else "conforming"
    if cat == "leap-real":
        return "too strict (no leap second)" if not ok else (
            "WRONG VALUE" if cmp == "WRONG" else "conforming")
    if cat == "leap-fake":
        return "TOO LENIENT" if ok else "conforming"
    if cat == "range":
        return "too strict (range limit)" if not ok else "conforming"
    if cat.startswith("ixdtf"):
        # every SQL engine here is an RFC 3339-only consumer
        return "lenient (accepts suffix)" if ok else "conforming"
    return "?"

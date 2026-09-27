#!/usr/bin/env python3
"""Run the RFC 3339 / RFC 9557 conformance vectors against rfcdt or a TARGET parser.

Usage
-----
    run_vectors.py                                  # built-in rfcdt, in process
    run_vectors.py --target 'node adapter.js'       # any language, via adapter
    run_vectors.py --target 'java -jar a.jar' --mode argv --profile rfc3339
    run_vectors.py --target './a' --target-has-tzdata no   # target has no tz database
    run_vectors.py --target 'node ixdtf_adapter.mjs' --target-kind ixdtf --target-options fixed
    run_vectors.py --json                           # machine-readable report (+ meta)
    run_vectors.py --report md                      # Markdown findings-table skeleton
    run_vectors.py --target 'node batch.js' --batch # one process, JSON lines (fast)
    run_vectors.py --target 'java -jar a.jar' --jobs 8        # 8 processes in parallel
    run_vectors.py --target 'node a.js' --tz-matrix UTC,America/St_Johns,Asia/Kathmandu

Adapter protocol (for auditing a TARGET parser in any language)
---------------------------------------------------------------
The runner starts the ``--target`` command once per vector (per-process
mode, the default; ``--jobs N`` runs N at a time), or once in total with
``--batch`` (see "Batch mode" below).

Input
    * ``--mode stdin`` (default, PREFERRED): the vector string is written to
      stdin as UTF-8 with NO trailing newline, then stdin is closed.  Read
      all of stdin; do not strip whitespace (some vectors test trailing
      whitespace, CR, CRLF and NUL).
    * ``--mode argv``: the runner appends ``--`` and then the string as the
      last argument, so a value such as ``-0001-01-01T00:00:00Z`` is not
      taken for an option.  The adapter must accept (and drop) that ``--``.
      NUL cannot be passed in argv, so vectors containing NUL are reported
      as skipped in this mode; use stdin for full coverage.
    * Environment: ``RFCDT_PROFILE`` = ``rfc3339`` or ``ixdtf``;
      ``RFCDT_OPTIONS`` = JSON object of non-default options for that vector
      (keys: allow_space_separator, leap_seconds, tzdata, experimental_keys,
      production); ``RFCDT_VECTOR_ID`` = vector id.

Output (stdout, one JSON object)
    ``{"ok": true}``   the target ACCEPTED the string
    ``{"ok": false}``  the target REJECTED it (exceptions count as rejects:
                       catch them in the adapter and print ok=false)
    ``{"ok": true, "resolved": true}``
                       the target detected a critical inconsistency and
                       RESOLVED it by explicit programmed behaviour (RFC 9557
                       §3.4 "resolving the inconsistency via ... programmed
                       behavior").  Counted as INTERPRETATION, not TOO
                       LENIENT, for vectors marked ``"resolvable": true``.
    ``{"skip": true}`` the target does not support this profile/option.
                       The vector is reported as skipped, not failed.  An
                       adapter SHOULD print this for every ``RFCDT_OPTIONS``
                       key it does not implement (e.g. a target with a fixed
                       leap-second policy skips ``leap_seconds``); otherwise
                       one root cause is counted once per option vector.
                       Alternatively run with ``--target-options fixed``.
    ``{"ok": true, "fields": {...}}``
                       EFFECTIVE FIELDS: what the target made of the string
                       (read them from the target's result, never re-parse
                       the input in the adapter).  See "Fields" below.
    The whole stdout, or else its last line, is parsed as JSON.
    Extra keys (e.g. "reasons", "error") are shown in the report.
    Exit status is ignored.  Non-JSON output, a missing "ok", or a timeout
    is reported as ADAPTER ERROR.

Fields (names follow ``rfcdt.check(...).fields`` / ``rfcdt.py adapter``)
    Return any subset; only the keys you return are compared (a key you omit
    is never a failure), so report only what the target really exposes.
    ``year`` ``month`` ``day`` ``hour`` ``minute`` ``second``
        integers, the LOCAL (as-written) wall-clock fields.  ``second`` is
        60 for a leap second.  E.g. derive them from the target's instant plus
        its offset; a Date.UTC two-digit-year remap then shows as year 1950.
    ``secfrac``
        fraction digits as a string without the '.', or null.  Compared as a
        decimal: trailing zeros are ignored, and a SHORTER value that equals
        the expected digits truncated, rounded half-up or rounded half-even
        to its length is accepted (a target storing milliseconds may report
        "520" for ".52", "000" for ".000000000001", and "1234568" is accepted
        for ".12345678..." at 7 digits).  Report at least as many digits as
        you store.  (Rounding that carries into the seconds is not accepted.)
    ``offset``          the offset text as written ("Z", "z", "+05:30").
    ``offset_minutes``  signed minutes east of UTC (Z and -00:00 -> 0).
    ``offset_unknown``  true for Z / -00:00 (RFC 9557 §2), false otherwise.
    ``separator``       "T", "t" or " ".
    ``leap_second``     true when second == 60.
    ``time_zone``       null or {"kind": "name"|"offset", "name": str,
                        "critical": bool}; only the sub-keys you return are
                        compared.
    ``tags``            list of {"key", "value", "values", "critical"} in
                        input order; only the sub-keys you return are compared.
    ``effective_tags``  {key: value} after duplicate handling.  RFC 9557 §3.3:
                        the FIRST occurrence wins.  Every expected key must be
                        present with the expected value (a dropped or
                        last-wins tag is a mismatch).
    Unknown names are ignored, and so is a known name whose value has a
    different container shape (e.g. ``tags`` as an object instead of a list:
    a name clash, not a value).  A non-object ``fields`` (e.g. a repr string)
    is ignored and counted as "fields not compared" in the summary.

Batch mode (``--batch``)
    Starting a JVM, .NET or Node process per vector takes minutes; a batch
    adapter is started ONCE.  The runner sets ``RFCDT_BATCH=1`` (and not
    ``RFCDT_PROFILE``/``RFCDT_OPTIONS``/``RFCDT_VECTOR_ID``), writes one JSON
    object per line to stdin, then closes stdin::

        {"id": "3339-5.6-001", "input": "...", "profile": "rfc3339", "options": {}}

    Lines are ASCII (``json.dumps`` escapes NUL, CR, LF and non-ASCII), so
    split on "\\n" and ``JSON.parse`` each line; the vector string is
    ``input``.  ``--mode`` is ignored (the string is never in argv).
    The adapter writes exactly ONE result line per input line, in the SAME
    ORDER, each the same object as in per-process mode; echo ``"id"`` so the
    runner can detect a lost or reordered line (a mismatch is an ADAPTER
    ERROR for that vector).  Blank output lines are ignored.  Flush stdout
    (or write it at the end); the whole batch has a time limit of
    ``--timeout`` x the number of vectors.
    An adapter that does not implement batch mode prints ``{"batch": false}``
    as its first line when ``RFCDT_BATCH=1``; the runner then falls back to
    per-process mode (``--jobs`` applies) and says so in the report header.
    ``python3 run_vectors.py --rfcdt-adapter`` is a batch-capable adapter
    for the built-in engine (reference implementation of both modes).

Minimal adapters (both modes)::

    # Python -- auditing datetime.fromisoformat
    import sys, os, json, datetime
    def one(s):
        try:
            d = datetime.datetime.fromisoformat(s)
            off = d.utcoffset()
            return {"ok": True, "fields": {
                "year": d.year, "month": d.month, "day": d.day, "hour": d.hour,
                "minute": d.minute, "second": d.second,
                "offset_minutes": None if off is None else int(off.total_seconds() // 60)}}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    if os.environ.get("RFCDT_BATCH") == "1":
        for line in sys.stdin:
            if line.strip():
                req = json.loads(line)
                print(json.dumps({"id": req["id"], **one(req["input"])}), flush=True)
    else:
        print(json.dumps(one(sys.stdin.read())))

    // Node -- auditing Date.parse
    const one = s => ({ok: !Number.isNaN(Date.parse(s))});
    const all = require('fs').readFileSync(0, 'utf8');
    if (process.env.RFCDT_BATCH === '1') {
      const out = all.split('\\n').filter(l => l.trim()).map(l => {
        const req = JSON.parse(l); return JSON.stringify({id: req.id, ...one(req.input)}); });
      process.stdout.write(out.join('\\n') + '\\n');
    } else console.log(JSON.stringify(one(all)));

    # rfcdt itself as an external target (reference adapter, returns fields):
    run_vectors.py --target 'python3 rfcdt.py adapter'                  # per-process
    run_vectors.py --target 'python3 run_vectors.py --rfcdt-adapter' --batch

Host time zone (``--tz-matrix TZ1,TZ2,...``)
    A parser that falls back to the host's local time passes under
    ``TZ=UTC``.  With ``--tz-matrix`` the whole run is repeated with the
    ``TZ`` environment variable set to each zone (the built-in engine runs
    in process under ``time.tzset()``).  The first zone's results are
    classified as usual; a vector whose verdict (ok/skip/error/resolved) or
    returned ``fields`` differ between zones is reported as HOST-TZ
    DEPENDENT (a failure) with the per-zone values.

Report
------
Results are grouped by the vector's ``section``.  A failure is classified:

* TOO LENIENT: expected invalid, target accepted (the dangerous direction for
  consumers: garbage gets in).
* TOO STRICT: expected valid, target rejected (interop failure).
* WRONG VALUE: the target accepted, and a field it returned differs from the
  vector's ``fields`` (see "Fields").  This is a failure on ``either``
  vectors too: e.g. 9557-3.3-015 ``[u-ca=chinese][u-ca=japanese]`` may be
  rejected, but if accepted the effective calendar MUST be chinese.
* REASON MISMATCH (built-in engine only): rfcdt's reason code or documented
  default verdict differs from the vector.
* HOST-TZ DEPENDENT (``--tz-matrix`` only): verdict or fields change with the
  host ``TZ``.
* ADAPTER ERROR: no usable answer (non-JSON, missing "ok", timeout, lost
  batch line).

INTERPRETATION (never a failure): vectors with ``"expect": "either"`` (the
RFC permits both verdicts; the vector's ``interpretation`` says why),
``"resolved": true`` answers on ``"resolvable"`` vectors, and the
"leap-second representation": on a valid leap-second vector (expected
``second`` 60 or ``leap_second`` true) a target that returns second 59 of the
same minute, or second 0 of the next minute with the date/time correctly
rolled over (``leap_second`` false or absent), cannot store :60 -- a
representation limit, not a WRONG VALUE.  Any other value stays WRONG VALUE.  The report lists
the target's choice for each.  Pass percentages and the pass/fail totals
exclude this bucket.

With the built-in engine the runner also checks that the vector's reason
code appears among rfcdt's error (rejected) or warning (accepted) codes, and
that rfcdt's verdict on an ``either`` vector equals the documented
``rfcdt_default``.

Scoping options
    ``--target-kind rfc3339|ixdtf|both`` (default both) says which profile(s)
    the target implements.  ``rfc3339``: ixdtf-profile vectors are skipped
    (not applicable).  ``ixdtf`` (a consumer with only a suffix-aware
    parser): rfc3339-profile vectors run normally, EXCEPT those whose only
    invalidity is a suffix not allowed in the rfc3339 profile (reason
    ``R3339-5.6/trailing-characters`` and valid under the ixdtf profile),
    which are skipped as not applicable.
    ``--target-options fixed`` says the target has one fixed policy: vectors
    with non-default ``options`` are skipped and the summary says so.
    ``--default-options-only`` is an alias.
    ``--profile P`` drops (does not report) vectors of the other profile.

Vectors marked ``"requires": ["tzdata"]`` need a target that looks up IANA
time zones.  ``--target-has-tzdata yes|no|auto`` says whether the target has
one; ``auto`` (default) assumes yes for an external target and, for the
built-in engine, uses rfcdt's own ``zoneinfo`` availability.  With ``no``
those vectors are skipped (a target without tz data cannot detect RFC 9557
§3.4 inconsistencies; it MUST reject critical named zones per §3.3).
``--no-tzdata`` is an alias for ``--target-has-tzdata no``.

Output formats
    ``--report text`` (default): per-section table, then the failures and
    interpretation choices.  The header line gives the run's meta data.
    ``--report json`` (alias ``--json``): ``{"meta", "target", "totals",
    "sections", "results"}``.  ``meta`` = runner version, vectors file and
    sha256, python, platform, host TZ, tzdata version, tz-matrix, date (UTC),
    target command, mode, batch, jobs and elapsed seconds.
    ``--report md``: a Markdown skeleton for the audit report -- a findings
    table (Severity guess | Check ID(s) | Section | Vector | input -> target
    output | expected) grouped by root cause (status + the vector's reason
    code), then the interpretation-choice table.  The severity guess follows
    SKILL.md rule 1 from the vector's check levels (MUST/grammar ->
    Nonconformity, SHOULD -> Deviation, other -> Advisory; WRONG VALUE and
    HOST-TZ DEPENDENT -> Nonconformity); refine it by role before reporting.
    Each vector's ``checks`` lists the check IDs (references/check-index.md)
    it exercises.

Exit status: 0 when no failures/errors, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_VECTORS = os.path.join(HERE, "..", "vectors", "vectors.json")
DEFAULT_CHECK_INDEX = os.path.join(HERE, "..", "references", "check-index.md")
RUNNER_VERSION = "0.4.0"
sys.path.insert(0, HERE)

import rfcdt  # noqa: E402


def load_vectors(path=DEFAULT_VECTORS):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc["vectors"] if isinstance(doc, dict) else doc


def load_check_index(path=DEFAULT_CHECK_INDEX):
    """Parse references/check-index.md -> {id: {title, level, roles, judgment, file}}."""
    out = OrderedDict()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("| R"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if len(cells) < 6:
                continue
            cid, title, level, roles, judgment, fname = cells[:6]
            out[cid] = {"title": title, "level": level,
                        "roles": [r.strip() for r in roles.split("(")[0].split(",") if r.strip()],
                        "judgment": judgment, "file": fname}
    return out


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _tzdata_info():
    """Best-effort IANA tz version the HOST (and the built-in engine) uses."""
    try:
        import tzdata  # type: ignore
        return {"source": "tzdata package", "version": tzdata.IANA_VERSION}
    except Exception:  # noqa: BLE001 -- optional package
        pass
    try:
        import zoneinfo
        paths = list(zoneinfo.TZPATH)
    except Exception:  # noqa: BLE001
        paths = []
    for base in paths:
        for name, rx in (("+VERSION", r"(\S+)"), ("tzdata.zi", r"#\s*version\s+(\S+)")):
            try:
                with open(os.path.join(base, name), encoding="utf-8") as fh:
                    m = re.match(rx, fh.readline())
            except OSError:
                continue
            if m:
                return {"source": os.path.join(base, name), "version": m.group(1)}
    return {"source": None, "version": None}


def _display_path(path):
    ap = os.path.abspath(path)
    return os.path.relpath(ap, ROOT) if ap.startswith(ROOT + os.sep) else os.path.basename(ap)


def build_meta(vectors_path=DEFAULT_VECTORS, target=None, tz_matrix=None, info=None,
               vector_count=None):
    """The ``meta`` block of --json output (and the text/md header)."""
    info = info or {}
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return OrderedDict([
        ("runner", "run_vectors.py"),
        ("runner_version", RUNNER_VERSION),
        ("vectors", _display_path(vectors_path)),
        ("vectors_sha256", _sha256(vectors_path)),
        ("vector_count", vector_count),
        ("python", sys.version.split()[0]),
        ("platform", sys.platform),
        ("host_tz", os.environ.get("TZ") or None),
        ("host_tzname", list(time.tzname)),
        ("tzdata", _tzdata_info()),
        ("tz_matrix", list(tz_matrix) if tz_matrix else None),
        ("date", now.isoformat().replace("+00:00", "Z")),
        ("target", target or "rfcdt (built-in)"),
        ("mode", info.get("mode")),
        ("batch", info.get("batch")),
        ("jobs", info.get("jobs")),
        ("elapsed_s", info.get("elapsed_s")),
    ])


def format_meta(meta):
    sha = (meta.get("vectors_sha256") or "")[:12]
    tzd = meta.get("tzdata") or {}
    parts = [f"runner {meta['runner_version']}",
             f"vectors {meta['vectors']} sha256:{sha} ({meta.get('vector_count')})",
             f"python {meta['python']} ({meta['platform']})",
             f"host TZ {meta['host_tz'] or '<unset>'} ({'/'.join(meta['host_tzname'])})",
             f"tzdata {tzd.get('version') or 'unknown'}",
             f"tz-matrix {','.join(meta['tz_matrix']) if meta['tz_matrix'] else '-'}",
             f"mode {meta.get('mode')}, batch {meta.get('batch')}, jobs {meta.get('jobs')}",
             f"{meta['date']}"]
    if meta.get("elapsed_s") is not None:
        parts.append(f"{meta['elapsed_s']:.2f}s")
    return " | ".join(parts)


# Nested objects whose sub-keys are compared only when the target returned
# them; ``effective_tags`` is a data map, so every expected key must be there.
_PARTIAL_OBJECTS = ("time_zone", "tags")


def _round_digits(digits, n, mode):
    """``digits`` (a decimal fraction's digit string) reduced to ``n`` digits by
    ``mode`` = "truncate" | "half-up" | "half-even".  Returns None when rounding
    carries into the seconds (e.g. ".9996" to 3 digits): that is not a value the
    fraction alone can express."""
    head, rest = digits[:n], digits[n:]
    if mode == "truncate" or not rest:
        return head
    first, tail = rest[0], rest[1:]
    if first > "5" or (first == "5" and tail.strip("0")):
        up = True                               # more than half
    elif first == "5":                          # exactly half
        up = mode == "half-up" or (bool(head) and int(head[-1]) % 2 == 1)
    else:
        up = False
    if not up:
        return head
    if not head or head == "9" * n:
        return None                             # carries into the seconds
    return str(int(head) + 1).zfill(n)


def _secfrac_match(expected, actual):
    """Fraction digits compared as decimals (trailing zeros ignored).  A SHORTER
    ``actual`` (a target storing fewer digits) passes when it equals the exact
    fraction truncated, rounded half-up or rounded half-even to its length."""
    if expected is None or actual is None:
        return expected == actual
    if not isinstance(actual, str):
        return False
    e, a = expected.rstrip("0"), actual.rstrip("0")
    if e == a:
        return True
    if len(actual) >= len(expected):
        return False
    n = len(actual)
    return any(r is not None and r.rstrip("0") == a
               for r in (_round_digits(expected, n, m) for m in ("truncate", "half-up", "half-even")))


# Leap-second representation (references/interpretation.md, "Grading vector
# results"): a target that cannot store second 60 and maps a VALID leap second
# to :59 of the same minute or to :00 of the next minute (all fields rolled
# over) has a representation limit, not a wrong value.
_WALL = ("year", "month", "day", "hour", "minute", "second")
LEAP_NOTE = "leap-second representation"


def _is_leap_vector(vec):
    f = vec.get("fields") or {}
    return f.get("second") == 60 or f.get("leap_second") is True


def _leap_wall_fields(vec):
    """The vector's full expected local wall-clock fields (year..second, second
    60), from the vector's own ``fields`` completed by the built-in engine."""
    wall = {}
    try:
        r = rfcdt.check(vec["input"], vec["profile"], **dict(vec.get("options") or {}))
        wall.update({k: v for k, v in (r.fields or {}).items() if k in _WALL})
    except Exception:  # noqa: BLE001 -- best effort; the vector's fields still apply
        pass
    wall.update({k: v for k, v in (vec.get("fields") or {}).items() if k in _WALL})
    return wall if len(wall) == len(_WALL) and wall["second"] == 60 else None


def leap_representation(vec, actual, mismatches):
    """Return ":59" or ":00 next minute" when every mismatch in ``mismatches``
    (from compare_fields) is explained by that leap-second representation, else
    None.  Only for vectors whose expected fields have second 60 / leap_second."""
    if not mismatches or not _is_leap_vector(vec) or not isinstance(actual, dict):
        return None
    if any(k not in _WALL and k != "leap_second" for k, _, _ in mismatches):
        return None
    if "leap_second" in actual and actual["leap_second"] not in (False, None):
        return None                             # a mismatch other than "false"
    wall = _leap_wall_fields(vec)
    if wall is None:
        return None
    from datetime import datetime as _dt, timedelta as _td
    y, mo, d, h, mi = (wall[k] for k in _WALL[:5])
    same = dict(wall, second=59)
    alts = [(":59", same)]
    try:
        nxt = _dt(y, mo, d, h, mi, 59) + _td(seconds=1)
        alts.append((":00 next minute", {"year": nxt.year, "month": nxt.month, "day": nxt.day,
                                         "hour": nxt.hour, "minute": nxt.minute, "second": 0}))
    except (ValueError, OverflowError):
        pass
    returned = [k for k in _WALL if k in actual]
    if "second" not in returned:
        return None                             # nothing shows which representation
    for label, alt in alts:
        if all(actual[k] == alt[k] for k in returned):
            return label
    return None


def _partial_match(expected, actual):
    """Match where dict sub-keys missing from ``actual`` are not compared."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(_partial_match(v, actual[k]) for k, v in expected.items() if k in actual)
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(expected) == len(actual)
                and all(_partial_match(e, a) for e, a in zip(expected, actual)))
    return expected == actual


def _strict_match(expected, actual):
    """Recursive subset match: every key in expected must equal actual's."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and _strict_match(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(expected) == len(actual)
                and all(_strict_match(e, a) for e, a in zip(expected, actual)))
    return expected == actual


def compare_fields(expected, actual):
    """Compare a vector's ``fields`` with a target's.  Returns ``None`` when
    nothing could be compared (no dict, or no shared key), else a list of
    ``(key, expected, actual)`` mismatches (empty = all compared keys match).
    Only top-level keys the target returned are compared."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return None
    # A key whose container shape differs (object vs list) is a name clash
    # with an adapter's own structure, not a value: it is not compared.
    keys = [k for k in expected if k in actual
            and not (isinstance(expected[k], (dict, list)) and actual[k] is not None
                     and type(expected[k]) is not type(actual[k]))]
    if not keys:
        return None
    bad = []
    for k in keys:
        e, a = expected[k], actual[k]
        if k == "secfrac":
            ok = _secfrac_match(e, a)
        elif k in _PARTIAL_OBJECTS:
            ok = _partial_match(e, a)
        else:
            ok = _strict_match(e, a)
        if not ok:
            bad.append((k, e, a))
    return bad


# Backwards-compatible name used by older callers/tests.
_fields_match = _strict_match


# ---------------------------------------------------------------------------
# Execution backends
# ---------------------------------------------------------------------------
def run_builtin(vec):
    opts = dict(vec.get("options") or {})
    r = rfcdt.check(vec["input"], vec["profile"], **opts)
    notes = []
    reason = vec.get("reason", "ok")
    if vec["expect"] == "either" and vec.get("rfcdt_default"):
        got = "valid" if r.ok else "invalid"
        if got != vec["rfcdt_default"]:
            notes.append(f"rfcdt verdict {got} != documented rfcdt_default "
                         f"{vec['rfcdt_default']}")
    if reason and reason != "ok":
        pool = r.error_codes if not r.ok else r.warning_codes
        if reason not in pool:
            notes.append(f"reason {reason} not in {pool}")
    return {"ok": r.ok, "reasons": r.error_codes, "warnings": r.warning_codes,
            "fields": r.fields}, notes


def _parse_output_obj(out, stderr=b""):
    """Parse one adapter answer (whole output, else its last line)."""
    try:
        obj = json.loads(out)
    except ValueError:
        try:
            obj = json.loads(out.splitlines()[-1] if out else "")
        except (ValueError, IndexError):
            return {"error": f"non-JSON output: {out[:120]!r} stderr={stderr[:120]!r}"}
    if not isinstance(obj, dict) or ("ok" not in obj and not obj.get("skip")):
        return {"error": f"missing 'ok': {out[:120]!r}"}
    return obj


def _env(tz=None):
    env = dict(os.environ)
    if tz is not None:
        env["TZ"] = tz
    return env


def run_target(vec, cmd, mode, timeout, tz=None):
    env = _env(tz)
    env["RFCDT_PROFILE"] = vec["profile"]
    env["RFCDT_OPTIONS"] = json.dumps(vec.get("options") or {})
    env["RFCDT_VECTOR_ID"] = vec["id"]
    env.pop("RFCDT_BATCH", None)
    argv = shlex.split(cmd)
    data = vec["input"].encode("utf-8")
    if mode == "argv":
        if "\x00" in vec["input"]:
            return {"skip": True, "reason": "NUL cannot be passed via argv (use --mode stdin)"}, []
        argv = argv + ["--", vec["input"]]
        data = b""
    try:
        cp = subprocess.run(argv, input=data, capture_output=True, timeout=timeout, env=env,
                            cwd=os.getcwd())
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}, []
    except OSError as e:
        return {"error": f"cannot run target: {e}"}, []
    out = cp.stdout.decode("utf-8", errors="replace").strip()
    return _parse_output_obj(out, cp.stderr), []


def batch_request_line(vec):
    return json.dumps({"id": vec["id"], "input": vec["input"], "profile": vec["profile"],
                       "options": vec.get("options") or {}}, ensure_ascii=True)


def run_target_batch(vecs, cmd, timeout, tz=None):
    """Run ``vecs`` through one batch-mode adapter process.  Returns a list of
    ``(out, notes)`` in input order, or ``None`` if the adapter declined with
    ``{"batch": false}`` (the caller then falls back to per-process mode)."""
    env = _env(tz)
    env["RFCDT_BATCH"] = "1"
    for k in ("RFCDT_PROFILE", "RFCDT_OPTIONS", "RFCDT_VECTOR_ID"):
        env.pop(k, None)
    data = "".join(batch_request_line(v) + "\n" for v in vecs).encode("ascii")
    limit = timeout * max(1, len(vecs))
    try:
        cp = subprocess.run(shlex.split(cmd), input=data, capture_output=True, timeout=limit,
                            env=env, cwd=os.getcwd())
    except subprocess.TimeoutExpired:
        return [({"error": f"timeout (batch, {limit:g}s for {len(vecs)} vectors)"}, [])
                for _ in vecs]
    except OSError as e:
        return [({"error": f"cannot run target: {e}"}, []) for _ in vecs]
    lines = [ln for ln in cp.stdout.decode("utf-8", errors="replace").splitlines()
             if ln.strip()]
    if lines:
        try:
            first = json.loads(lines[0])
        except ValueError:
            first = None
        if isinstance(first, dict) and first.get("batch") is False:
            return None
    results = []
    for i, vec in enumerate(vecs):
        if i >= len(lines):
            results.append(({"error": f"batch: no result line for input {i + 1} "
                                      f"(adapter wrote {len(lines)} of {len(vecs)}) "
                                      f"stderr={cp.stderr[:120]!r}"}, []))
            continue
        obj = _parse_output_obj(lines[i].strip())
        if "error" not in obj or "ok" in obj or obj.get("skip"):
            rid = obj.get("id")
            if rid is not None and rid != vec["id"]:
                obj = {"error": f"batch: result line {i + 1} has id {rid!r}, expected "
                                f"{vec['id']!r} (lost or reordered line)"}
        results.append((obj, []))
    if len(lines) > len(vecs):
        for out, _ in results[-1:]:
            out.setdefault("adapter_note", f"{len(lines) - len(vecs)} extra output line(s)")
    return results


class _HostTZ:
    """Context manager: set TZ (and tzset) for in-process runs."""

    def __init__(self, tz):
        self.tz, self.old = tz, None

    def __enter__(self):
        if self.tz is not None:
            self.old = os.environ.get("TZ")
            os.environ["TZ"] = self.tz
            if hasattr(time, "tzset"):
                time.tzset()
        return self

    def __exit__(self, *exc):
        if self.tz is not None:
            if self.old is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = self.old
            if hasattr(time, "tzset"):
                time.tzset()
        return False


def _execute(vecs, target, mode, timeout, batch, jobs, tz, info):
    """Run ``vecs`` once under host zone ``tz``; returns [(out, notes)]."""
    if not target:
        with _HostTZ(tz):
            return [run_builtin(v) for v in vecs]
    if batch and vecs:
        res = run_target_batch(vecs, target, timeout, tz)
        if res is not None:
            info["batch"] = "yes"
            return res
        info["batch"] = "fallback (adapter replied {\"batch\": false})"
    if jobs and jobs > 1 and len(vecs) > 1:
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            return list(ex.map(lambda v: run_target(v, target, mode, timeout, tz), vecs))
    return [run_target(v, target, mode, timeout, tz) for v in vecs]


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def _has_tzdata(target, target_has_tzdata):
    if target_has_tzdata == "yes":
        return True
    if target_has_tzdata == "no":
        return False
    return rfcdt.tzdata_available() if not target else True  # auto


TARGET_KINDS = ("rfc3339", "ixdtf", "both")
TARGET_OPTIONS = ("configurable", "fixed")


def _suffix_only_invalid(vec):
    """True if an rfc3339-profile vector is invalid ONLY because a suffix is
    not allowed in that profile (valid under the ixdtf profile)."""
    if vec["profile"] != "rfc3339" or vec["expect"] != "invalid":
        return False
    if vec.get("reason") != "R3339-5.6/trailing-characters":
        return False
    try:
        return rfcdt.check(vec["input"], "ixdtf", **dict(vec.get("options") or {})).ok
    except ValueError:  # option not defined for ixdtf (partial productions)
        return False


def _not_applicable(vec, target_kind, fixed_options):
    """Return (skip_kind, detail) or None."""
    if target_kind == "rfc3339" and vec["profile"] == "ixdtf":
        return "target-kind", "not applicable: --target-kind rfc3339 (no IXDTF parser)"
    if target_kind == "ixdtf" and _suffix_only_invalid(vec):
        return "target-kind", ("not applicable: --target-kind ixdtf; invalid only because "
                               "the rfc3339 profile forbids the suffix")
    if fixed_options and vec.get("options"):
        return "options", ("non-default options " + json.dumps(vec["options"], ensure_ascii=False)
                           + " (--target-options fixed)")
    return None


def _classify(vec, rec, out, notes):
    rec["output"] = out
    # ``skip`` wins over ``error``: an adapter may explain a skip with an
    # "error" key ({"skip": true, "error": "..."}).
    if out.get("skip"):
        rec["status"] = "skip"
        rec["skip_kind"] = "target"
        rec["detail"] = out.get("reason") or out.get("error") or "target skipped"
        return
    if "error" in out and "ok" not in out:
        rec["status"] = "error"
        rec["detail"] = out["error"]
        return
    got_valid = bool(out["ok"])
    rec["choice"] = "accepted" if got_valid else "rejected"
    wrong = leap = None
    if got_valid and vec.get("fields"):
        cmp = compare_fields(vec["fields"], out.get("fields"))
        rec["fields_compared"] = cmp is not None
        if cmp:
            wrong = "; ".join(f"{k}: expected {json.dumps(e, ensure_ascii=False)}, got "
                              f"{json.dumps(a, ensure_ascii=False)}" for k, e, a in cmp)
            if vec["expect"] != "invalid":
                leap = leap_representation(vec, out.get("fields"), cmp)
    if leap:
        rec["choice"] = f"accepted ({LEAP_NOTE}: {leap})"
        rec["status"] = "interpretation"
        rec["interpretation"] = (LEAP_NOTE + ": the target stores the valid leap second as "
                                 + leap + " (a representation limit, not a wrong value)")
        rec["detail"] = f"{LEAP_NOTE} ({leap}): {wrong}"
        return
    if vec["expect"] == "either":
        if wrong:
            rec["status"] = "wrong-value"
            rec["detail"] = f"accepted (permitted) but {wrong}"
        else:
            rec["status"] = "fail-reason" if notes else "interpretation"
            rec["detail"] = "; ".join(notes) or f"target {rec['choice']}"
    elif (got_valid and vec["expect"] == "invalid" and out.get("resolved")
          and vec.get("resolvable")):
        rec["choice"] = "accepted (resolved by programmed behaviour)"
        rec["status"] = "interpretation"
        rec["detail"] = f"target {rec['choice']}"
    elif got_valid == (vec["expect"] == "valid"):
        if wrong:
            rec["status"] = "wrong-value"
            rec["detail"] = wrong
        else:
            rec["status"] = "fail-reason" if notes else "pass"
            rec["detail"] = "; ".join(notes)
    else:
        rec["status"] = "too-lenient" if got_valid else "too-strict"
        rec["detail"] = f"expected {vec['expect']} ({vec.get('reason')})"
        if got_valid and out.get("resolved"):
            rec["detail"] += "; 'resolved' only counts on resolvable vectors"


def _verdict(out):
    if out.get("skip"):
        return "skipped"
    if "error" in out and "ok" not in out:
        return "error"
    v = "accepted" if out.get("ok") else "rejected"
    return v + (" (resolved)" if out.get("ok") and out.get("resolved") else "")


def _tz_diff(zones, outs):
    """Differences between per-zone outputs of one vector ([] = identical)."""
    diffs = []
    verdicts = [_verdict(o) for o in outs]
    if len(set(verdicts)) > 1:
        diffs.append("verdict: " + ", ".join(f"{z}={v}" for z, v in zip(zones, verdicts)))
    fl = [o.get("fields") if isinstance(o.get("fields"), dict) else None for o in outs]
    keys = []
    for f in fl:
        for k in (f or {}):
            if k not in keys:
                keys.append(k)
    missing = object()
    for k in keys:
        vals = [(f or {}).get(k, missing) for f in fl]
        canon = [json.dumps(v, sort_keys=True, default=str) if v is not missing else "<absent>"
                 for v in vals]
        if len(set(canon)) > 1:
            diffs.append(f"fields.{k}: " + ", ".join(
                f"{z}={c}" for z, c in zip(zones, canon)))
    return diffs


def run(vectors, target=None, mode="stdin", timeout=10.0, profile=None, no_tzdata=False,
        default_options_only=False, target_has_tzdata="auto", target_kind="both",
        target_options="configurable", *, batch=False, jobs=1, tz_matrix=None, info=None):
    """Run ``vectors``; returns one result record per reported vector.

    ``batch``: use the batch adapter protocol (one process); ``jobs``: parallel
    processes in per-process mode; ``tz_matrix``: list of TZ values -- the run
    is repeated per zone and differences are reported as ``tz-dependent``.
    ``info`` (dict, optional) receives execution details (batch, jobs, mode,
    elapsed_s)."""
    if no_tzdata:
        target_has_tzdata = "no"
    if target_kind not in TARGET_KINDS:
        raise ValueError(f"target_kind must be one of {TARGET_KINDS}")
    if target_options not in TARGET_OPTIONS:
        raise ValueError(f"target_options must be one of {TARGET_OPTIONS}")
    if jobs is not None and jobs < 1:
        raise ValueError("jobs must be >= 1")
    info = info if info is not None else {}
    info.update({"mode": "in-process" if not target else ("stdin" if batch else mode),
                 "batch": ("no" if not batch else "yes") if target else "n/a",
                 "jobs": (jobs or 1) if target else "n/a"})
    fixed_options = default_options_only or target_options == "fixed"
    have_tz = _has_tzdata(target, target_has_tzdata)
    if not target and have_tz and not rfcdt.tzdata_available():
        raise ValueError("--target-has-tzdata yes, but rfcdt has no zoneinfo data")
    zones = list(tz_matrix) if tz_matrix else [None]
    results, pending = [], []
    for vec in vectors:
        if profile and vec["profile"] != profile:
            continue
        rec = {"id": vec["id"], "section": vec["section"], "input": vec["input"],
               "profile": vec["profile"], "expect": vec["expect"],
               "reason": vec.get("reason"), "checks": list(vec.get("checks") or []),
               "notes": vec.get("notes", "")}
        if vec.get("interpretation"):
            rec["interpretation"] = vec["interpretation"]
        na = _not_applicable(vec, target_kind, fixed_options)
        if na is None and "tzdata" in (vec.get("requires") or []) and not have_tz:
            na = ("tzdata", "requires tzdata")
        if na:
            rec["status"] = "skip"
            rec["skip_kind"], rec["detail"] = na
        else:
            pending.append((vec, rec))
        results.append(rec)
    t0 = time.perf_counter()
    per_zone = [_execute([v for v, _ in pending], target, mode, timeout, batch, jobs, z, info)
                for z in zones]
    info["elapsed_s"] = round(time.perf_counter() - t0, 3)
    for i, (vec, rec) in enumerate(pending):
        out, notes = per_zone[0][i]
        _classify(vec, rec, out, notes)
        if len(zones) > 1:
            outs = [pz[i][0] for pz in per_zone]
            diffs = _tz_diff(zones, outs)
            if diffs:
                rec["base_status"] = rec["status"]
                rec["status"] = "tz-dependent"
                rec["detail"] = "; ".join(diffs)
                rec["tz_outputs"] = {z: {"verdict": _verdict(o), "fields": o.get("fields")}
                                     for z, o in zip(zones, outs)}
    return results


STATUSES = ("pass", "too-lenient", "too-strict", "wrong-value", "tz-dependent", "fail-reason",
            "error", "interpretation", "skip")
FAILURES = ("too-lenient", "too-strict", "wrong-value", "tz-dependent", "fail-reason", "error")
SKIP_KINDS = {"options": "non-default options (--target-options fixed: target has a fixed "
                         "policy)",
              "target-kind": "not applicable to --target-kind",
              "tzdata": "require tzdata (--target-has-tzdata no)",
              "target": "skipped by the adapter ({\"skip\": true})"}
LABELS = OrderedDict([
    ("too-lenient", "TOO LENIENT (accepted, should reject)"),
    ("too-strict", "TOO STRICT (rejected, should accept)"),
    ("wrong-value", "WRONG VALUE (accepted, but effective fields differ)"),
    ("tz-dependent", "HOST-TZ DEPENDENT (verdict or fields change with the host TZ)"),
    ("fail-reason", "REASON MISMATCH"),
    ("error", "ADAPTER ERROR"),
])


def summarize(results):
    """Per-section and total counts.  ``total`` counts every vector; ``scored``
    excludes skipped and INTERPRETATION results (the base for percentages)."""
    groups = OrderedDict()
    for r in sorted(results, key=lambda r: r["section"]):
        g = groups.setdefault(r["section"], dict.fromkeys(("total",) + STATUSES, 0))
        g["total"] += 1
        g[r["status"]] += 1
    tot = {k: sum(g[k] for g in groups.values()) for k in ("total",) + STATUSES}
    tot["scored"] = tot["total"] - tot["skip"] - tot["interpretation"]
    skips = OrderedDict()
    for r in results:
        if r["status"] == "skip":
            k = r.get("skip_kind", "target")
            skips[k] = skips.get(k, 0) + 1
    tot["skipped_by"] = dict(skips)
    with_fields = [r for r in results if "fields_compared" in r]
    tot["fields_checked"] = sum(1 for r in with_fields if r["fields_compared"])
    tot["fields_not_compared"] = sum(1 for r in with_fields if not r["fields_compared"])
    return groups, tot


def _show(s, limit=100):
    """repr() of an input, shortened for reports (5000-tag vectors)."""
    r = repr(s)
    if len(r) <= limit:
        return r
    return repr(s[:limit - 40]) + f"...(+{len(s) - (limit - 40)} chars)"


def print_report(results, target, out=None, meta=None):
    groups, tot = summarize(results)
    w = (out or sys.stdout).write
    w(f"Conformance report -- target: {target or 'rfcdt (built-in)'}\n")
    if meta:
        w(f"  {format_meta(meta)}\n")
    w(f"{'section':34} {'pass':>5} {'lenient':>8} {'strict':>7} {'wrong':>6} {'tzdep':>6} "
      f"{'reason':>7} {'error':>6} {'interp':>7} {'skip':>5} {'total':>6}\n")
    for sec, g in list(groups.items()) + [("TOTAL", tot)]:
        w(f"{sec:34} {g['pass']:5d} {g['too-lenient']:8d} {g['too-strict']:7d} "
          f"{g['wrong-value']:6d} {g['tz-dependent']:6d} {g['fail-reason']:7d} {g['error']:6d} "
          f"{g['interpretation']:7d} {g['skip']:5d} {g['total']:6d}\n")
    for status, label in LABELS.items():
        bad = [r for r in results if r["status"] == status]
        if not bad:
            continue
        w(f"\n{label}: {len(bad)}\n")
        for r in bad:
            w(f"  {r['id']:16} [{r['section']}] {_show(r['input'])}\n      {r['detail']}"
              f" -- {r['notes']}\n")
    interp = [r for r in results if r["status"] == "interpretation"]
    if interp:
        w(f"\nINTERPRETATION (RFC permits either verdict, or a leap-second representation; "
          f"not a failure): {len(interp)}\n")
        for r in interp:
            w(f"  {r['id']:16} [{r['section']}] {_show(r['input'])}\n      target "
              f"{r['choice'].upper()} -- {r.get('interpretation', '')}\n")
    ran = tot["scored"]
    pct = 100.0 * tot["pass"] / ran if ran else 0.0
    w(f"\n{tot['pass']}/{ran} passed ({pct:.1f}%), {tot['interpretation']} interpretation "
      f"(excluded), {tot['skip']} skipped\n")
    for k, n in tot["skipped_by"].items():
        w(f"  skipped: {n} {SKIP_KINDS.get(k, k)}\n")
    if tot["fields_checked"] or tot["fields_not_compared"]:
        w(f"  fields: {tot['fields_checked']} accepted vectors compared, "
          f"{tot['wrong-value']} WRONG VALUE")
        if tot["fields_not_compared"]:
            w(f"; {tot['fields_not_compared']} not compared (no 'fields' object, or none "
              f"of the vector's field names)")
        w("\n")


# ---------------------------------------------------------------------------
# Markdown findings skeleton (--report md)
# ---------------------------------------------------------------------------
SEVERITY_ORDER = ("Nonconformity", "Deviation", "Advisory", "Review")
_GRAMMAR_REASON = re.compile(r"^R(3339-5\.[67]|9557-4\.1)/")


def severity_guess(rec, index):
    """SKILL.md rule 1, from the vector's check levels (a starting point only)."""
    status = rec["status"]
    if status in ("wrong-value", "tz-dependent"):
        return "Nonconformity"  # well-formed but wrong instant / fields
    if status in ("error", "fail-reason"):
        return "Review"
    levels = [index.get(c, {}).get("level", "") for c in rec.get("checks") or []]
    if (any("MUST" in lv or "grammar" in lv for lv in levels)
            or _GRAMMAR_REASON.match(rec.get("reason") or "")):
        return "Nonconformity"
    if any("SHOULD" in lv for lv in levels):
        return "Deviation"
    return "Advisory"


def _md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def _md_code(s, limit=80):
    return "`" + _md(_show(s, limit)).replace("`", "'") + "`"


def _target_output(r):
    out = r.get("output") or {}
    if r["status"] == "tz-dependent":
        return r["detail"]
    if r["status"] == "error":
        return "ADAPTER ERROR: " + str(r.get("detail"))
    txt = _verdict(out)
    if r["status"] == "wrong-value":
        txt += "; " + r["detail"]
    extra = out.get("error") or out.get("reasons")
    if extra and r["status"] in ("too-strict", "fail-reason"):
        txt += f" ({extra if isinstance(extra, str) else ', '.join(map(str, extra))})"
    return txt


def _root_cause(r):
    reason = r.get("reason") or "ok"
    if reason == "ok":
        reason = "valid: " + ((r.get("checks") or ["?"])[0])
    return f"{LABELS.get(r['status'], r['status']).split(' (')[0]} -- {reason}"


def markdown_report(results, target, meta=None, index=None, out=None):
    index = index if index is not None else load_check_index()
    w = (out or sys.stdout).write
    groups, tot = summarize(results)
    w(f"# Vector findings -- {target or 'rfcdt (built-in)'}\n\n")
    if meta:
        w(f"Run: {format_meta(meta)}\n\n")
    ran = tot["scored"]
    w(f"Evidence: vectors per adapter ({tot['pass']}/{ran}; {tot['too-lenient']} too lenient, "
      f"{tot['too-strict']} too strict, {tot['wrong-value']} wrong value, "
      f"{tot['tz-dependent']} host-TZ dependent, {tot['error']} adapter errors, "
      f"{tot['interpretation']} interpretation, {tot['skip']} skipped)\n\n")
    bad = [r for r in results if r["status"] in FAILURES]
    by = OrderedDict()
    for r in sorted(bad, key=lambda r: (FAILURES.index(r["status"]), r.get("reason") or "",
                                        r["id"])):
        by.setdefault(_root_cause(r), []).append(r)
    sev_count = OrderedDict((s, 0) for s in SEVERITY_ORDER)
    w("## Findings (skeleton; grouped by root cause)\n\n")
    if not by:
        w("No failing vectors.\n\n")
    for cause, rows in by.items():
        sevs = [severity_guess(r, index) for r in rows]
        top = min(sevs, key=SEVERITY_ORDER.index)
        sev_count[top] += 1
        checks = sorted({c for r in rows for c in r.get("checks") or []})
        w(f"### {_md(cause)} ({len(rows)} vector{'s' if len(rows) != 1 else ''}; "
          f"root-cause severity guess: {top})\n\n")
        w(f"Check IDs: {', '.join(checks) or '-'}\n\n")
        w("| Severity (guess) | Check ID(s) | Section | Vector | input → target output "
          "| expected |\n|---|---|---|---|---|---|\n")
        for r, sev in zip(rows, sevs):
            w(f"| {sev} | {_md(', '.join(r.get('checks') or []))} | {_md(r['section'])} | "
              f"{r['id']} | {_md_code(r['input'])} → {_md(_target_output(r))} | "
              f"{_md(r['expect'])} ({_md(r.get('reason'))}) |\n")
        w("\n")
    w("Summary (root causes): " + ", ".join(f"{n} {s}" for s, n in sev_count.items())
      + ". Severity is guessed from the check level (SKILL.md rule 1); adjust by role "
        "(documented leniency or a general-purpose parser -> Advisory).\n\n")
    interp = [r for r in results if r["status"] == "interpretation"]
    w("## Interpretation choices (not failures)\n\n")
    if interp:
        w("| Vector | Section | Check ID(s) | Input | Target choice | Interpretation |\n"
          "|---|---|---|---|---|---|\n")
        for r in interp:
            w(f"| {r['id']} | {_md(r['section'])} | {_md(', '.join(r.get('checks') or []))} | "
              f"{_md_code(r['input'])} | {_md(r['choice'])} | "
              f"{_md(r.get('interpretation', ''))} |\n")
    else:
        w("None.\n")
    w("\n## Not run\n\n")
    if tot["skipped_by"]:
        for k, n in tot["skipped_by"].items():
            w(f"- {n} vectors: {SKIP_KINDS.get(k, k)}\n")
    else:
        w("- none\n")


# ---------------------------------------------------------------------------
# Built-in engine as an adapter (per-process and batch)
# ---------------------------------------------------------------------------
def _rfcdt_answer(s, profile, options):
    try:
        r = rfcdt.check(s, profile, **(options or {}))
    except (ValueError, TypeError) as e:
        return {"ok": False, "skip": True, "reason": str(e)}
    return {"ok": r.ok, "reasons": r.error_codes, "warnings": r.warning_codes,
            "fields": r.fields}


def rfcdt_adapter(argv=None, stdin=None, stdout=None):
    """``run_vectors.py --rfcdt-adapter``: rfcdt behind the adapter protocol,
    in both per-process and batch (``RFCDT_BATCH=1``) mode."""
    argv = list(argv or [])
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    if os.environ.get("RFCDT_BATCH") == "1":
        for line in stdin:
            if not line.strip():
                continue
            req = json.loads(line)
            ans = _rfcdt_answer(req["input"], req.get("profile", "rfc3339"), req.get("options"))
            stdout.write(json.dumps({"id": req.get("id"), **ans}, ensure_ascii=False) + "\n")
        stdout.flush()
        return 0
    if "--" in argv:
        s = argv[argv.index("--") + 1]
    else:
        buf = getattr(stdin, "buffer", None)
        s = (buf.read().decode("utf-8", errors="surrogateescape") if buf is not None
             else stdin.read())
    ans = _rfcdt_answer(s, os.environ.get("RFCDT_PROFILE") or "rfc3339",
                        json.loads(os.environ.get("RFCDT_OPTIONS") or "{}"))
    stdout.write(json.dumps(ans, ensure_ascii=False) + "\n")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--rfcdt-adapter"]:
        return rfcdt_adapter(argv[1:])
    ap = argparse.ArgumentParser(description="Run RFC 3339/9557 conformance vectors.")
    ap.add_argument("--vectors", default=DEFAULT_VECTORS)
    ap.add_argument("--target", help="adapter command (see module docstring)")
    ap.add_argument("--mode", choices=("stdin", "argv"), default="stdin")
    ap.add_argument("--timeout", type=float, default=10.0,
                    help="seconds per vector (batch mode: x number of vectors)")
    ap.add_argument("--profile", choices=rfcdt.PROFILES, help="only run this profile")
    ap.add_argument("--target-kind", choices=TARGET_KINDS, default="both",
                    help="profiles the target implements: rfc3339 = skip ixdtf vectors; "
                         "ixdtf = skip rfc3339 vectors that are invalid only because of a "
                         "suffix; both (default) = run everything")
    ap.add_argument("--target-options", choices=TARGET_OPTIONS, default="configurable",
                    help="fixed = the target has one fixed policy: skip vectors with "
                         "non-default options (reported in the summary)")
    ap.add_argument("--target-has-tzdata", choices=("yes", "no", "auto"), default="auto",
                    help="does the target look up IANA time zones? no = skip vectors that "
                         "require tzdata; auto (default) = yes for --target, rfcdt's own "
                         "zoneinfo for the built-in engine")
    ap.add_argument("--no-tzdata", action="store_true",
                    help="alias for --target-has-tzdata no")
    ap.add_argument("--default-options-only", action="store_true",
                    help="alias for --target-options fixed")
    ap.add_argument("--batch", action="store_true",
                    help="batch adapter protocol: start the target once and exchange JSON "
                         "lines (falls back to per-process if it replies {\"batch\": false})")
    ap.add_argument("--jobs", type=int, default=1,
                    help="per-process mode: run N target processes in parallel")
    ap.add_argument("--tz-matrix", metavar="TZ1,TZ2,...",
                    help="repeat the run with TZ set to each zone; verdict/field differences "
                         "are reported as HOST-TZ DEPENDENT failures")
    ap.add_argument("--report", choices=("text", "json", "md"), default="text")
    ap.add_argument("--json", action="store_true", help="alias for --report json")
    a = ap.parse_args(argv)
    tz_matrix = [z.strip() for z in a.tz_matrix.split(",") if z.strip()] if a.tz_matrix else None
    if a.tz_matrix and not tz_matrix:
        ap.error("--tz-matrix needs at least one zone")
    vectors = load_vectors(a.vectors)
    info = {}
    try:
        results = run(vectors, a.target, a.mode, a.timeout, a.profile,
                      a.no_tzdata, a.default_options_only, a.target_has_tzdata,
                      a.target_kind, a.target_options, batch=a.batch, jobs=a.jobs,
                      tz_matrix=tz_matrix, info=info)
    except ValueError as e:
        ap.error(str(e))
    meta = build_meta(a.vectors, a.target, tz_matrix, info, vector_count=len(vectors))
    report = "json" if a.json else a.report
    if report == "json":
        groups, tot = summarize(results)
        print(json.dumps({"meta": meta, "target": a.target or "rfcdt", "totals": tot,
                          "sections": groups, "results": results}, indent=1,
                         ensure_ascii=False))
    elif report == "md":
        markdown_report(results, a.target, meta)
    else:
        print_report(results, a.target, meta=meta)
    _, tot = summarize(results)
    bad = sum(tot[k] for k in FAILURES)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

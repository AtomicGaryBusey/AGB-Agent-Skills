#!/usr/bin/env python3
"""rfcdt -- strict reference validator/parser for RFC 3339 and RFC 9557 (IXDTF).

Python 3 standard library only (``zoneinfo`` is used when time-zone data is
present; everything else works without it).

Grounding
---------
* RFC 3339 §5.6 (ABNF), §5.7 (restrictions), §4.3 (unknown local offset),
  Appendix C (leap years), Appendix D (leap-second table).
* RFC 9557 §2 (update to RFC 3339 §4.3: "Z" now means the same as "-00:00":
  "the time in UTC is known, but the offset to local time is unknown"),
  §3.2 (experimental keys), §3.3 (elective vs critical), §3.4 (offset / time
  zone inconsistency), §4.1 (ABNF).
* Errata.  RFC 3339 Verified errata (293, 1584, 3710, 4110) touch only
  Appendix A (the informational ISO 8601 grammar), §5.1 prose, or a URL, so
  none changes the §5.6 profile implemented here.  Held-for-document-update
  errata 5783 (space separator) and 5624 (use of partial productions) are
  exposed as opt-in options (``allow_space_separator``, ``production``) and
  are never on by default.  RFC 9557 erratum 8192 is Rejected (editorial
  hyphenation) and has no effect.

Result model
------------
``check()`` returns a :class:`Result` with ``ok``, ``errors`` (reason codes
that make the string invalid), ``warnings`` (codes for accepted-but-notable
conditions) and ``fields``.  Reason codes have the form
``R<rfc>-<section>/<slug>``, for example ``R3339-5.7/date-mday`` or
``R9557-3.3/critical-unknown-key``.

Leap seconds (``leap_seconds`` option)
--------------------------------------
§5.7: time-second "may have the value "60" at the end of months in which a
leap second occurs -- to date: June ... or December"; "in time zones other
than "Z", the leap second point is shifted by the zone offset".  Appendix D
quotes the CCIR rule: "first preference is given to the opportunities at the
end of December and June, and second preference to those at the end of March
and September".  UTC leap seconds began in 1972 (the Appendix D table starts
at 1972-06-30).  Every mode except ``grammar`` first applies the §5.7
positional rule: the instant, normalised to UTC by subtracting the offset,
must be 23:59:60 on the last day of a month.

* ``iers-months`` (DEFAULT): positional rule, plus the UTC month must be
  March, June, September or December (the Appendix D opportunities) and the
  UTC year must be >= 1972.  No table is needed, so it never goes stale.
  Codes: ``R3339-AppD/leap-second-month``, ``R3339-AppD/leap-second-pre-1972``.
* ``table``: positional rule, plus the UTC date must be in
  :data:`LEAP_SECONDS` (known insertions through 2016-12-31).  This is the
  literal §5.7 reading ("months in which a leap second occurs") but it
  rejects any future insertion the table does not know.
* ``any-month-end``: positional rule only (any month end; ITU-R TF.460 lets
  the IERS use any month as a last resort).
* ``grammar``: ABNF comment only ("00-60"); 60 is accepted at any time.

The RFC permits a validator to accept or reject an end-of-quarter leap second
that did not really occur (it cannot know without a table), so vectors for
such inputs are marked ``"expect": "either"``; rfcdt's default verdict for
them comes from ``iers-months``.

:data:`LEAP_SECONDS` is the RFC 3339 Appendix D table (1972-06-30 ..
1998-12-31) extended with the later IERS Bulletin C insertions
2005-12-31, 2008-12-31, 2012-06-30, 2015-06-30 and 2016-12-31.  TABLE CUTOFF:
2016-12-31 (TAI-UTC = 37 s).  No leap second has been inserted after that
date as far as this table's author could verify; any later insertion is
unknown to this table and ``table`` mode will reject it.  Negative leap
seconds (§5.7: maximum second "58") have never occurred and are not modelled.

Time zones (``tzdata`` option)
------------------------------
``auto`` uses ``zoneinfo.available_timezones()`` when non-empty; ``off`` (or
missing data) skips name lookup and offset consistency and sets
``fields['tz_checked']`` False.  RFC 9557 §3.3: for a critical tag the
recipient "MUST NOT act on the IXDTF string unless it can process the suffix
tag as specified".  So a CRITICAL named time zone that cannot be processed
(no tz data, name unknown to the tz data, or instant outside the range the
tz code supports) is the error ``R9557-3.3/critical-unprocessable``.  An
ELECTIVE one gets the warning ``R9557-3.4/time-zone-unchecked`` (or
``R9557-4.1/elective-unknown-time-zone``).

Sub-minute zone offsets (``lmt_tolerance`` option)
-------------------------------------------------
Before standard time, zones used local mean time with offsets in seconds
(Paris +00:09:21; Monrovia -00:44:30 until 1972).  time-numoffset has no
seconds, and RFC 3339 §4.2 NOTE / §5.8 have such offsets written as a
representable hh:mm.  ``nearest`` (DEFAULT) accepts only the zone offset
rounded to the nearest minute, and both neighbours on an exact :30 tie
(|difference| <= 30 s): Paris 1900 accepts +00:09 and rejects +00:10;
Monrovia accepts -00:44 and -00:45.  ``any-sub-minute`` accepts any hh:mm
less than 60 s from the zone offset (the behaviour before 1.1).  The RFCs do
not fix this choice, so the +00:10 vector is ``"expect": "either"``.

Default policy where the RFC permits a choice
---------------------------------------------
The vectors mark these inputs ``"expect": "either"``.  rfcdt still returns
one definite verdict, as follows:

* Elective inconsistency (§3.4 "MAY act"), elective unknown key, value or
  time zone (§3.3 "free to ignore"; §4.1 unknown zone = inconsistency):
  ACCEPT with a warning.
* Repeated elective key (§3.3): ACCEPT; the first value is used
  (``fields['effective_tags']``), warning ``R9557-3.3/duplicate-elective-key``.
* ``Z`` or ``-00:00`` with an offset time zone such as ``[+01:00]``: ACCEPT.
  The date-time asserts no local offset (§2, §3.4 Figure 2), so there is no
  inconsistency to act on.
* Time-zone-name case (``[!europe/paris]``): ACCEPT with warning
  ``R9557-4.1/time-zone-name-case`` after a case-insensitive lookup.
* Leap second at a month end with no real insertion: ``iers-months`` above.
* Critical inconsistency (§3.4 "MUST act"): REJECT.  rfcdt has no programmed
  resolution.  (A target that resolves it by explicit programmed behaviour is
  conformant; see ``run_vectors.py``, ``"resolved": true``.)

CLI
---
    rfcdt.py check [options] [--json] [--] STRING
        options: [--profile rfc3339|ixdtf] [--allow-space-separator]
                 [--leap-seconds iers-months|table|any-month-end|grammar]
                 [--tzdata auto|off] [--experimental-key KEY ...]
                 [--production P] [--lmt-tolerance nearest|any-sub-minute]
    rfcdt.py adapter [same options]     # read one string on stdin, print JSON
    rfcdt.py scan PATH [PATH ...] [--json] [--include-dist] [--max-bytes N]
    rfcdt.py selfcheck [--json] [--leap-file PATH] [--zoneinfo DIR ...]
                       [--node BIN] [--calendars a,b,...] [--today YYYY-MM-DD]
    rfcdt.py --version

``check --json`` adds a ``meta`` block (rfcdt version, Python, tz source and
release, host TZ, UTC date).  ``scan --json`` prints ``{"meta", "summary",
"findings"}``; ``summary`` is the scan denominator: files seen / scanned /
skipped, skips by reason (too-large = over --max-bytes, default 2000000,
0 = no limit; binary = NUL in the first 8 KiB; extension = media, archive and
object files, not read; unreadable), directories pruned by name, and counts
by extension, including the extensions that only the language-neutral
patterns cover.  The text output ends with the same summary.  An audit must
not call a file clean when the summary says it was not scanned.

``scan`` prunes dist, node_modules, build, vendor, target, venv and VCS
directories found while walking; ``--include-dist`` keeps dist.  Explicit file
and directory arguments are always scanned.  A statement split over several
lines (open parenthesis, trailing operator, leading ``.``/``+``) is joined
before matching and reported at its first line.

``selfcheck`` compares :data:`LEAP_SECONDS` with the host tzdata
``leapseconds`` (or ``leap-seconds.list``) and its expiry date, compares
:data:`KNOWN_CALENDARS` with ICU (``node``:
``Intl.supportedValuesOf('calendar')``), and checks the age of the tz
release.  Each line is OK, WARN or SKIP (source unavailable).

Put ``--`` before a STRING that starts with ``-``.  The adapter (stdin) is
preferred: argv cannot carry NUL.

Exit status: check/adapter 0 = valid, 1 = invalid, 2 = usage error;
scan 0 = no findings, 1 = findings; selfcheck 0 = no WARN, 1 = any WARN,
2 = usage error.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import re
import stat
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

__version__ = "1.1.0"

# ---------------------------------------------------------------------------
# Static-scan pattern table (``scan`` mode).  Each row:
#   (id, check reason code, file extensions ("*" = all), line regex, exclude
#    regex or None, severity, message, safe replacement)
# Rows listed in ``_SCAN_CONTEXT`` also need a file/nearby-line condition
# (see there).  Patterns are heuristics: every hit is a lead to verify, not a
# verdict.  Heuristics worth knowing:
#   * SCAN-JS-DATE-PARSE flags ``new Date(x)`` only when ``x`` is a string or
#     template literal, a name that suggests a string (…str/…string/…text/
#     input/raw/iso/json/header/param/query/line, or exactly ``s``), or
#     req/request/ctx .body/.query/.params/.headers.  ``new Date(epochMs)``,
#     ``new Date(Date.now())`` and ``new Date(y, m, d)`` are not flagged.
#   * SCAN-PY-REGEX-DOLLAR: a ``$"`` string end, in a file that calls
#     ``.match(``/``.search(``, with a ``{4}`` / ``(?P<year>`` component in the
#     same statement (the line, plus up to 8 string-literal continuation lines
#     directly above it and the line that opens them).
#   * SCAN-JS-REGEXP-NO-CARET: ``new RegExp(`` in a file that contains a
#     4-digit date component, where the first string literal in the call does
#     not start with ``^`` (constants such as ``DATE + TIME`` are not
#     resolved).
#   * SCAN-PY-TZ-STR: ``str(<…tz…>)`` / ``.tzname()`` in a file that builds a
#     bracketed suffix (``f"[{"`` or ``"[" +``).
#   * SCAN-TAG-LAST-WINS: keyed assignment into a variable named like
#     tags/suffix/annotations/ext (``out.tags[key] = value``).
#   * SCAN-GO-JSON-V1-TIME: a ``time.Time`` struct field with a ``json:``
#     tag, in a file that does not import ``encoding/json/v2``.
#   * SCAN-GO-OFFSET-SECONDS: ``time.LoadLocation(`` always (info);
#     ``time.FixedZone(name, N)`` only when N is not an integer literal (or a
#     product of them) or is not a whole number of minutes / is >= 24 h;
#     ``Format(time.RFC3339…)`` / ``MarshalJSON`` / ``MarshalText`` only in a
#     file that also calls LoadLocation/FixedZone and not after ``.UTC()``.
#   * SCAN-GO-STRING: ``.String()`` on a name that looks like a time value
#     (t, ts, tm, now, …Time, …At, …Date, time.Now()).
#   * SCAN-GO-NANO-SORT: ``time.RFC3339Nano`` on a line that mentions
#     sort/key/file name/path/cursor/order.
#   * SCAN-RS-SERDE-CHRONO / SCAN-RS-TIME-SERDE-DEFAULT: a struct field typed
#     ``DateTime<Utc|FixedOffset|Local>`` (in a file that mentions
#     ``Deserialize``) or ``OffsetDateTime`` / ``PrimitiveDateTime`` (in a
#     file that mentions ``Serialize``) whose ``#[…]`` attribute lines directly
#     above carry no ``serde(with`` / ``deserialize_with`` / ``serialize_with``.
#   * SCAN-RS-DISPLAY: ``.to_string()`` / ``format!("{}", x)`` on a name
#     that looks like a date-time (dt, ts, now, …_at, …_time, Utc::now(), …);
#     jiff ``Timestamp``/``Zoned`` Display is conforming, so check the type.
#   * SCAN-JS-LOCAL-DATE-PARTS: ``new Date(a, b, c, …)`` with 3+ top-level
#     arguments (followed over up to 8 lines; comment lines skipped), first
#     argument not a string literal.  ``new Date(Date.UTC(…))`` has one argument.
#   * SCAN-JS-FLOOR-MOD-SPLIT: ``Math.floor(x / N)`` and ``x % N`` within one
#     line of each other, unless ``((x % N) + N) % N``, ``x < 0`` or
#     ``Math.abs``/``Math.sign`` appears nearby.
#   * SCAN-JS-INTL-HOUR-OFFSET: ``…Hour - 12`` in a file that uses
#     ``hour12: false``.
#   * SCAN-SN-STRING-SURGERY / -DISPLAY-VALUE-OUT / -GDT-UNCHECKED: only in
#     files with a Glide marker (GlideDateTime, GlideRecord, gs.x(), sn_ws,
#     RESTMessageV2, current.x).  DISPLAY-VALUE-OUT also needs an outbound call
#     (RESTMessageV2, setRequestBody, setBody, JSON.stringify, …) within 20
#     lines and, for getDisplayValue(), a date-like name on the line.
#     GDT-UNCHECKED skips copies (current./gr./…gdt) and calls with isValid()
#     within 3 lines above / 6 below.  SN-T-TO-SPACE needs a Glide or Fluent
#     marker.
#   * SCAN-JS-DATE-PARSE also flags ``new Date(obj.created_at)`` when the
#     argument is a member / key named …_at, createdAt, updatedAt,
#     publishedAt, published, timestamp or date (``obj.get('created_at')``,
#     ``obj['date']``); ``new Date(x + 'Z')`` is SCAN-JS-APPEND-Z instead.
#   * SCAN-RB-ISO8601 skips string-literal arguments; SCAN-RB-TO-DATETIME needs a
#     receiver that looks like untrusted text (hash lookup, params, …str/text/
#     value/param/input/raw/json name); a string literal receiver is not flagged.  dayjs / moment / arrow.get: one argument only.
#   * SCAN-PY-DATEUTIL: a bare ``parse(`` counts only in a file that imports
#     ``from dateutil.parser import parse``.
#   * SCAN-SWIFT-ISO8601-DEFAULT: only in files that never set formatOptions;
#     SCAN-SWIFT-POSIX-LOCALE: files that set .dateFormat without en_US_POSIX.
#   * SCAN-EX-NAIVE: ``timestamps()`` only in files that mention Ecto.
#   * SCAN-APEX-*: .cls files that are not LaTeX classes (\ProvidesClass …).
#   * SCAN-SQL-TO-CHAR-OFFSET: the to_char format literal (quoted "text"
#     removed) contains TZ / tz (not TZH/TZM) or OF.
#   * Every pattern is also tried on the joined multi-line statement (see
#     ``_logical_line``); such a hit is reported at the statement's first line.
#   * SCAN-SN-FLUENT-DT-VALUE / -TIME-NO-ZONE: only in files that import
#     ``@servicenow/sdk…`` or use ``Now.ID[``.  SCHEDULE-FLOATING needs an
#     enclosing ``ScheduledScript(`` call without a non-floating ``timeZone``
#     (info: the SDK serializes floating/omitted as UTC).  HOST-ZONE-CONVERT
#     fires on SDK helper calls with one argument or a 'floating' zone.
# ---------------------------------------------------------------------------
_PY = (".py", ".pyi")
_JS = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte")
_JAVA = (".java", ".kt", ".kts", ".scala", ".groovy")
_NET = (".cs", ".vb", ".fs")
_GO = (".go",)
_RS = (".rs",)
_PHP = (".php",)
_RB = (".rb", ".erb", ".rake", ".haml", ".jbuilder")
_C = (".c", ".h", ".cc", ".cpp", ".hpp")
_EX = (".ex", ".exs")
_DART = (".dart",)
_PROTO = (".proto",)
_APEX = (".cls", ".trigger")
_SQL = (".sql",)
_SWIFT = (".swift",)
_SCHEMA = (".json", ".yaml", ".yml")
_ANY = ("*",)

# A member / key whose name suggests a wire timestamp string (JSON API
# objects): obj.created_at, obj?.published, obj.get('updated_at'), obj['date'].
_JS_DATEISH_NAME = r"(?:[\w$]*_at|createdAt|updatedAt|publishedAt|published|timestamp|date)"
_JS_STRINGY_ARG = (r"(?:['\"`]"
                   r"|(?:req|request|ctx|event)\.(?:body|query|params|headers)\b"
                   r"|(?:[A-Za-z_$][\w$]*\.)*[A-Za-z_$]?[\w$]*(?:[Ss]tr(?:ing)?|[Tt]e?xt|[Ii]nput"
                   r"|[Rr]aw|[Ii]so|ISO|[Jj]son|JSON|[Hh]eader|[Pp]aram|[Qq]uery|[Ll]ine)[\w$]*\s*\)"
                   r"|(?:[A-Za-z_$][\w$]*!?(?:\?\.|\.))+" + _JS_DATEISH_NAME + r"!?\s*\)"
                   r"|(?:[A-Za-z_$][\w$]*!?(?:\?\.|\.))*[A-Za-z_$][\w$]*(?:\?\.|\.)get\(\s*['\"]"
                   + _JS_DATEISH_NAME + r"['\"]\s*\)\s*\)"
                   r"|(?:[A-Za-z_$][\w$]*!?(?:\?\.|\.))*[A-Za-z_$][\w$]*\[\s*['\"]"
                   + _JS_DATEISH_NAME + r"['\"]\s*\]\s*\)"
                   r"|s\s*\))")
# One call argument (no top-level comma), allowing one level of nested parens.
_ONE_ARG = r"\s*(?!\))(?:[^,()]|\([^()]*\))+\)"

SCAN_PATTERNS = (
    ("SCAN-STRFTIME-Z", "R3339-5.6/time-numoffset", _ANY,
     r"%S(?:\.%[0-9]*[fLN]|%\.?[0-9]*f)?%z|strftime\([^)]*%z"
     r"|\[offset_hour[^\]]*\]\[offset_minute", None, "error",
     "strftime %z emits +HHMM (e.g. +0000) without the colon required by "
     "time-numoffset",
     "%:z (Python 3.12+, GNU date) or dt.isoformat(timespec='seconds') on an aware value"),
    ("SCAN-LITERAL-Z", "R9557-2.2/z-means-utc-known", _ANY,
     r"%S(?:\.%f|%\.?[0-9]*f)?Z['\"]|ss(?:\.[SfF]+)?'Z'|15:04:05(?:\.[09]+)?Z[\"`]"
     r"|\[second\](?:\[subsecond[^\]]*\])?Z",
     r"(?i)utc|gmt|gmtime|toISOString", "warn",
     "literal 'Z' appended to a formatted time: valid only if the value is "
     "really UTC (RFC 9557 §2: Z = UTC known); local time labelled Z is wrong",
     "convert to UTC first (dt.astimezone(timezone.utc)) or emit the real offset (%:z / XXX)"),
    ("SCAN-ISOFORMAT-PLUS-Z", "R9557-2.2/z-means-utc-known", _PY,
     r"isoformat\([^)]*\)\s*\+\s*['\"]Z['\"]", None, "warn",
     "isoformat() + 'Z': naive local time gets labelled UTC, aware values "
     "get a double offset",
     "dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')"),
    ("SCAN-PY-NAIVE-ISOFORMAT", "R3339-5.6/time-offset", _PY,
     r"\b(?:utcnow|now|today)\(\s*\)\.isoformat\(", None, "warn",
     "naive datetime.isoformat() has no time-offset; not an RFC 3339 date-time",
     "datetime.now(timezone.utc).isoformat()"),
    ("SCAN-PY-NAIVE-NOW", "R3339-5.6/time-offset", _PY,
     r"default_factory\s*=\s*(?:datetime\.)?(?:now|utcnow|today)\b(?!\s*\()"
     r"|\bdatetime\.(?:now|utcnow|today)\(\s*\)(?!\s*\.(?:astimezone|isoformat)\b)",
     None, "warn",
     "naive timestamp source: datetime.now()/utcnow()/today() without tz= (or "
     "default_factory=datetime.now) yields a naive value; a later isoformat() "
     "has no time-offset (§5.6 requires one; §4.4 unqualified local time)",
     "datetime.now(timezone.utc); dataclass: field(default_factory=lambda: "
     "datetime.now(timezone.utc))"),
    ("SCAN-PY-FROMISOFORMAT", "R3339-5.6/lenient-parser", _PY,
     r"\bfromisoformat\s*\(", None, "warn",
     "datetime.fromisoformat (3.11+) accepts much more than RFC 3339 "
     "(basic format, missing offset/seconds, space, ',' fraction) and "
     "rejects second=60; do not use on untrusted RFC 3339 input without a "
     "strict pre-check",
     "validate with a strict \\A…\\Z [0-9] regex (or rfcdt.check) first, then parse"),
    ("SCAN-PY-DATEUTIL", "R3339-5.6/lenient-parser", _PY,
     r"\bdateutil\b.*\bparse\b|\bparser\.parse\s*\(|\bisoparse\s*\(|\bpendulum\.parse\s*\("
     r"|(?<![\w.])parse\s*\(",
     None, "warn", "dateutil parser.parse / isoparse and pendulum.parse are fuzzy parsers, far "
     "more lenient than RFC 3339 (parse: free text, day/month guessing, missing offset -> "
     "naive; isoparse: basic format, week dates, date-only, missing offset -> naive)",
     "strict pre-validation (rfcdt.check or an anchored [0-9] regex), then parse"),
    ("SCAN-PY-ARROW-GET", "R3339-5.6/lenient-parser", _PY,
     r"\barrow\.get\(" + _ONE_ARG, None, "warn",
     "arrow.get(string) without a format parses ISO 8601 loosely (basic format, date-only, "
     "missing seconds) and reads a value without an offset as UTC -- not an RFC 3339 check",
     "strict anchored regex (or rfcdt.check) first, then arrow.get(s, 'YYYY-MM-DDTHH:mm:ssZZ')"),
    ("SCAN-PY-PANDAS-TO-DATETIME", "R3339-5.6/lenient-parser", _PY,
     r"\b(?:pd|pandas)\.to_datetime\s*\(", r"\bformat\s*=", "warn",
     "pd.to_datetime without format= infers a format (mixed formats, day-first guessing, "
     "values without an offset stay tz-naive); errors='coerce' turns bad input into NaT "
     "silently",
     "pd.to_datetime(s, format='ISO8601', utc=True, errors='raise') behind a strict regex"),
    ("SCAN-PY-REGEX-DOLLAR", "R3339-5.6/trailing-characters", _PY,
     r"(?<!\\)\$['\"]", r"\\Z|fullmatch", "error",
     "date-time regex ends in '$' and is used with re.match/re.search: Python '$' "
     "also matches before a final '\\n', so '...Z\\n' is accepted",
     "end the pattern with \\Z, or call pattern.fullmatch(text)"),
    ("SCAN-JS-DATE-PARSE", "R3339-5.6/lenient-parser", _JS,
     r"\bDate\.parse\s*\(|\bnew\s+Date\s*\(\s*" + _JS_STRINGY_ARG,
     r"\}Z`\s*\)|\+\s*['\"]Z['\"]\s*\)", "warn",
     "Date.parse/new Date(string) fall back to implementation-defined "
     "formats and cannot represent second=60",
     "match an anchored /^…$/ RFC 3339 regex first (or Temporal.Instant.from), then "
     "build the value with Date.UTC + setUTCFullYear"),
    ("SCAN-JS-REGEXP-NO-CARET", "R3339-5.6/regex-anchor", _JS,
     r"\bnew\s+RegExp\s*\(", None, "warn",
     "date-time RegExp built by concatenation without a leading '^': exec/test "
     "match a timestamp embedded in junk ('junk2024-01-01T00:00:00Z')",
     "new RegExp('^' + DATE + TIME + OFFSET + '$') (anchor both ends)"),
    ("SCAN-JS-DATE-UTC-YEAR", "R3339-5.6/date-fullyear", _JS,
     r"\bDate\.UTC\s*\(\s*(?![0-9])[A-Za-z_$(]", r"setUTCFullYear", "error",
     "Date.UTC(year, …) maps years 0-99 to 1900-1999: '0050-06-01T00:00:00Z' "
     "becomes 1950 (wrong instant)",
     "const d = new Date(Date.UTC(2000, m - 1, day, h, mi, s, ms)); d.setUTCFullYear(year, m - 1, day)"),
    ("SCAN-TAG-LAST-WINS", "R9557-3.3/duplicate-elective-key", _JS + _PY,
     r"\b(?:[\w$]+\.)*[\w$]*(?:[Tt]ags?|[Ss]uffix\w*|[Aa]nnotations?|ext)\s*\[\s*[\w$.'\"]+\s*\]\s*=(?!=)",
     None, "warn",
     "keyed assignment in suffix-tag parsing keeps the LAST repeated key; RFC 9557 "
     "§3.3 requires the FIRST ('[u-ca=chinese][u-ca=japanese]' -> chinese)",
     "JS: if (!(key in tags)) tags[key] = value;  Python: tags.setdefault(key, value); "
     "reject differing duplicates when any copy is critical"),
    ("SCAN-JS-MOMENT-LENIENT", "R3339-5.6/lenient-parser", _JS,
     r"\bmoment(?:\.utc|\.parseZone)?\s*\(" + _ONE_ARG, r"\bmoment(?:\.utc)?\(\s*[0-9]+\s*\)",
     "warn",
     "moment(string) without a format and strict=true is a forgiving parser (falls back to "
     "new Date(string); no offset -> host-local time)",
     "moment(s, moment.ISO_8601, true) plus an anchored RFC 3339 regex"),
    ("SCAN-JS-APPEND-Z", "R9557-2.2/z-means-utc-known", _JS,
     r"\b(?:new\s+Date|Date\.parse|dayjs(?:\.utc)?|moment(?:\.utc)?|parseISO|DateTime\.fromISO)"
     r"\s*\(\s*[^()]*?\+\s*['\"]Z['\"]\s*\)"
     r"|\b(?:new\s+Date|Date\.parse)\s*\(\s*`[^`]*\}Z`\s*\)", None, "warn",
     "'Z' appended to a string before parsing (new Date(x + 'Z')): asserts the text is UTC "
     "wall time; a value that already has an offset or 'Z' becomes Invalid Date, and "
     "local wall time is shifted by the host offset (RFC 9557 §2: Z = UTC known)",
     "send / store an RFC 3339 string with its offset and parse that (anchored regex first); "
     "if the source is known UTC wall time, document it and validate the shape before adding Z"),
    ("SCAN-JS-DAYJS", "R3339-5.6/lenient-parser", _JS,
     r"\bdayjs(?:\.utc)?\s*\(" + _ONE_ARG, r"\bdayjs(?:\.utc)?\(\s*[0-9]+\s*\)", "warn",
     "dayjs(string) without a format: its parse regex accepts 1-digit fields, '/' separators, "
     "missing time/seconds and no offset (-> host-local time); other strings go to "
     "new Date(string); an invalid date is not an error",
     "dayjs(s, 'YYYY-MM-DDTHH:mm:ssZ', true) (customParseFormat, strict) behind an anchored "
     "RFC 3339 regex; check .isValid()"),
    ("SCAN-JS-PARSEISO", "R3339-5.6/lenient-parser", _JS,
     r"\bparseISO\s*\(", None, "warn",
     "date-fns parseISO accepts ISO 8601 beyond RFC 3339 (basic format, week/ordinal dates, "
     "date-only, missing seconds) and reads a value without an offset as host-local time; "
     "bad input gives Invalid Date, not an error",
     "anchored RFC 3339 regex first, then parseISO(s); check isValid(d)"),
    ("SCAN-JS-LUXON-FROMISO", "R3339-5.6/lenient-parser", _JS,
     r"\bDateTime\.from(?:ISO|SQL)\s*\(", None, "warn",
     "Luxon DateTime.fromISO accepts ISO 8601 beyond RFC 3339 (basic format, week/ordinal "
     "dates, date-only, ',' fraction) and reads a value without an offset in the default "
     "(host) zone; fromSQL takes a space separator and no offset; bad input returns an "
     "invalid DateTime, not an error",
     "anchored RFC 3339 regex first, then DateTime.fromISO(s, { setZone: true }); check .isValid"),
    ("SCAN-NET-PARSE", "R3339-5.6/lenient-parser", _NET,
     r"\bDateTime(?:Offset)?\.(?:Try)?Parse\s*\(|\bConvert\.ToDateTime\s*\(", None, "warn",
     "DateTime(Offset).Parse without an exact format is culture-sensitive and lenient",
     "DateTimeOffset.ParseExact(s, \"yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK\", "
     "CultureInfo.InvariantCulture)"),
    ("SCAN-NET-SORTABLE-Z", "R9557-2.2/z-means-utc-known", _NET,
     r"\.ToString\(\s*\"(?:s|yyyy-MM-ddTHH:mm:ss(?:\.[fF]+)?)\"\s*(?:,[^()]*)?\)\s*\+\s*\"Z\""
     r"|\{[\w.]+:(?:s|yyyy-MM-ddTHH:mm:ss(?:\.[fF]+)?)\}Z",
     r"(?i)ToUniversalTime|UtcNow|UtcDateTime|\.Utc\b", "warn",
     "ToString(\"s\") + \"Z\": the sortable 's' format has no offset, so appending 'Z' labels "
     "the value UTC even when its Kind is Local or Unspecified (a DateTimeOffset's own offset "
     "is dropped)",
     "dto.UtcDateTime.ToString(\"yyyy-MM-dd'T'HH:mm:ss.FFFFFFF'Z'\", CultureInfo.InvariantCulture) "
     "or dto.ToString(\"o\")"),
    ("SCAN-NET-SHORT-OFFSET", "R3339-5.6/time-numoffset", _NET,
     r"ss(?:\.[fF]+)?z{1,2}[\"']", None, "error",
     ".NET 'z'/'zz' offset specifier emits +1 / +01 (no minutes)",
     "'zzz' or 'K'"),
    ("SCAN-JAVA-TOSTRING", "R3339-5.6/time-second", _JAVA,
     r"\b(?:ZonedDateTime|OffsetDateTime|LocalDateTime)\b.*\.toString\(\)", None, "warn",
     "java.time toString() omits ':00' seconds (\"2020-01-01T00:00Z\"); "
     "ZonedDateTime adds a [Region] suffix (IXDTF, not RFC 3339); LocalDateTime has no offset",
     "DateTimeFormatter.ofPattern(\"uuuu-MM-dd'T'HH:mm:ss[.SSSSSSSSS]XXX\")"),
    ("SCAN-JAVA-ISO-ZONED", "R3339-5.6/trailing-characters", _JAVA,
     r"\bISO_(?:ZONED_DATE_TIME|DATE_TIME|LOCAL_DATE_TIME)\b", None, "warn",
     "ISO_ZONED_DATE_TIME/ISO_DATE_TIME may add [Region] (RFC 9557 syntax); "
     "ISO_LOCAL_DATE_TIME has no offset -- neither is plain RFC 3339",
     "ISO_OFFSET_DATE_TIME with seconds forced (ofPattern ... ss ... XXX)"),
    ("SCAN-JAVA-LENIENT-PARSE", "R3339-5.6/lenient-parser", _JAVA,
     r"\b(?:ZonedDateTime|OffsetDateTime)\.parse\s*\(\s*[^,()]+\)", None, "warn",
     "java.time ISO parsers accept missing seconds and reject second=60",
     "anchored RFC 3339 regex pre-check, then OffsetDateTime.parse with an explicit formatter"),
    ("SCAN-JAVA-OFFSET-PATTERN", "R3339-5.6/time-numoffset", _JAVA + _JS + _SWIFT + _APEX,
     r"ss(?:\.S+)?(?:Z{1,2}|X{1,2}|x{1,2})[\"']", None, "error",
     "pattern letter Z/X/XX/x/xx emits +0000 or +00 (no colon); RFC 3339 needs XXX",
     "XXX (or xxx when Z is not wanted for zero)"),
    ("SCAN-PHP-ISO8601", "R3339-5.6/time-numoffset", _PHP,
     r"\bDATE_ISO8601\b|::ISO8601\b(?!_)", None, "error",
     "PHP DATE_ISO8601 emits +0000 (no colon)",
     "DATE_RFC3339 / DATE_RFC3339_EXTENDED"),
    ("SCAN-PHP-STRTOTIME", "R3339-5.6/lenient-parser", _PHP,
     r"\bstrtotime\s*\(|\bdate_create\s*\(|new\s+\\?DateTime(?:Immutable)?\s*\(\s*\$", None, "warn",
     "strtotime/DateTime(string) accept free-form input",
     "DateTimeImmutable::createFromFormat(DATE_RFC3339_EXTENDED, $s) after a strict regex"),
    ("SCAN-RB-PARSE", "R3339-5.6/lenient-parser", _RB,
     r"\b(?:Time|DateTime|Date)\.parse\s*\(|\bTime\.zone\.parse\s*\(", None, "warn",
     "Time/DateTime.parse and Time.zone.parse are heuristic: free-form text, no offset -> "
     "host / Time.zone local time, DateTime.parse rounds ':60' down to ':59' (probed); "
     "Time.zone.parse returns nil for text it cannot read",
     "Time.rfc3339(s) / DateTime.rfc3339(s) behind an anchored \\A…\\z [0-9] regex "
     "(check +24:00 handling)"),
    ("SCAN-RB-ISO8601", "R3339-5.6/lenient-parser", _RB,
     r"\b(?:DateTime|Date|Time)\.(?:iso8601|xmlschema)\s*\(\s*(?!['\"\)])", None, "warn",
     "DateTime/Time.iso8601 on untrusted input accept ISO 8601 forms outside RFC 3339: "
     "DateTime.iso8601(\"2024\") is TODAY at 20:24 (read as hhmm), ':60' becomes ':59' "
     "(DateTime) or rolls over (Time), basic format and '+0200' are accepted, and a missing "
     "offset is read as +00:00 (DateTime) or host-local time (Time) (probed, Ruby 3.4)",
     "anchored \\A…\\z [0-9] RFC 3339 regex (or rfcdt.check) first, then Time.rfc3339(s) / "
     "DateTime.rfc3339(s)"),
    ("SCAN-RB-TO-DATETIME", "R3339-5.6/lenient-parser", _RB,
     r"(?:\[\s*(?::\w+|['\"][^'\"]*['\"])\s*\]|\bparams\b"
     r"|\b\w*(?:str|string|text|param|value|input|raw|json)\b)\s*&?\.\s*to_(?:datetime|time)\b",
     None, "warn",
     "String#to_datetime / #to_time (ActiveSupport) call DateTime.parse: any date-like text "
     "is accepted, a missing offset becomes +00:00 (to_datetime) or host-local time "
     "(to_time), ':60' becomes ':59'; on JSON input (e.g. ActivityPub 'published') this is "
     "not a validation",
     "anchored RFC 3339 regex first, then Time.rfc3339(s) (rescue ArgumentError)"),
    ("SCAN-TWO-DIGIT-YEAR", "R3339-5.6/date-fullyear", _ANY,
     r"%y-%m-%d|(?<![yY])yy-MM-dd", None, "error",
     "two-digit year; RFC 3339 date-fullyear is 4DIGIT (§3: MUST be fully qualified)",
     "%Y / yyyy (uuuu in java.time)"),
    ("SCAN-12-HOUR", "R3339-5.6/time-hour", _ANY,
     r"%[Yy]-%m-%d[T ]%I:|dd'T'hh:mm|dd[T ]hh:mm:ss", None, "error",
     "12-hour clock field in an RFC 3339 pattern; time-hour is 00-23",
     "%H / HH"),
    ("SCAN-NO-SECONDS", "R3339-5.6/time-second", _ANY,
     r"%d[Tt ]%H:%M(?:%:?z|Z)?['\"]|dd'T'HH:mm(?:XXX|xxx|X|Z|'Z')?[\"']", None, "error",
     "date-time format without seconds (%H:%M / HH:mm): time-second is mandatory "
     "in partial-time",
     "%H:%M:%S (HH:mm:ss); truncate the value to the minute instead of dropping the field"),
    ("SCAN-PY-TZ-STR", "R9557-4.1/time-zone-name", _PY,
     r"\bstr\(\s*[\w.]*(?:tz|tzinfo|zone)\w*\s*\)|\.tzname\(\s*[\w.]*\s*\)", None, "warn",
     "str(tzinfo)/tzname() used for a [time-zone] suffix: gives 'UTC', 'UTC+05:30', "
     "'EST' or 'CET' -- abbreviations or labels, not IANA names; '[UTC+05:30]' is not "
     "a valid time-zone-name and '[EST]' names a different zone",
     "use ZoneInfo.key for IANA zones; for fixed offsets omit the suffix (RFC 9557 §1.2 "
     "discourages offset zones)"),
    ("SCAN-PY-UTC-ISOFORMAT", "R9557-2.2/utc-plus-zero", _PY,
     r"astimezone\(\s*(?:(?:datetime\.)?timezone\.utc|UTC|pytz\.utc|ZoneInfo\(['\"]UTC['\"]\))\s*\)"
     r"\.isoformat\(|fromtimestamp\([^()]*tz\s*=\s*(?:(?:datetime\.)?timezone\.utc|UTC)\s*\)"
     r"\.isoformat\(", None, "info",
     "isoformat() on a value converted to UTC emits '+00:00', which (RFC 9557 §2) "
     "claims UTC is the preferred local reference; for an instant whose local offset "
     "is unknown or irrelevant, 'Z' is the right suffix (advisory)",
     ".isoformat().replace('+00:00', 'Z') (or strftime('%Y-%m-%dT%H:%M:%SZ') on the UTC value)"),
    ("SCAN-REGEX-UNANCHORED", "R3339-5.6/regex-anchor", _ANY,
     r"(?:\\{1,2}d|\[0-9\])\{4\}-(?:\\{1,2}d|\[0-9\])",
     r"\^|\\\\?A|\\\\?[zZ]|\$[\"'/)]|fullmatch|\.matches\(|\bmatch\(|anchor", "warn",
     "date-time regex without ^/$ (or \\A/\\Z) anchors matches substrings of junk input",
     "anchor both ends: \\A…\\Z / fullmatch (Python), ^…$ (JS/Java without MULTILINE)"),
    ("SCAN-REGEX-SHORT-FIELD", "R3339-5.6/regex-field-width", _ANY,
     r"^(?=.*(?:\\{1,2}d|\[0-9\])\{4\}).*?(?:\\{1,2}d\{1,2\}|\[0-9\]\{1,2\}|\\{1,2}d\?\\{1,2}d|\\{1,2}d\+[-:T])",
     None, "error",
     "date-time regex allows 1-digit or unbounded fields; every §5.6 field is exactly 2DIGIT",
     "[0-9]{2} for month, day, hour, minute, second and offset fields"),
    ("SCAN-REGEX-UNICODE-DIGIT", "R3339-5.6/ascii-digit", _PY,
     r"re\.compile\(\s*r?['\"][^'\"]*\\d\{4\}", r"re\.A(?:SCII)?\b|\(\?a\)", "warn",
     "Python str regex \\d matches any Unicode digit (e.g. '٢٠٢٤')",
     "[0-9] or re.ASCII"),
    # --- Go (probed: eval-go/GO.md §3, Go 1.27.1) ---------------------------
    ("SCAN-GO-PARSE-LENIENT", "R3339-5.6/lenient-parser", _GO,
     r"\btime\.Parse(?:InLocation)?\(\s*time\.RFC3339(?:Nano)?\b|\.Unmarshal(?:JSON|Text)\(",
     None, "warn",
     "time.Parse(RFC3339…) / UnmarshalJSON / UnmarshalText accept +24:00, +23:60 (as +24:00), "
     "+24:60 (as +25:00), ',5' and a 1-digit hour ('T1:00:00Z'); they reject t/z and every :60. "
     "Calling (*Time).UnmarshalJSON directly on bytes also skips JSON unescaping",
     "anchored strict RFC 3339 regex ([0-9], ^…$) before time.Parse(time.RFC3339Nano, s); "
     "for JSON use encoding/json/v2 or a custom UnmarshalJSON that calls the strict helper"),
    ("SCAN-GO-JSON-V1-TIME", "R3339-5.6/lenient-parser", _GO,
     r"\btime\.Time\b[^`]*`[^`]*json:\"", None, "warn",
     "time.Time field decoded by encoding/json v1: its UnmarshalJSON is lenient "
     "(+24:00, ',5', 1-digit hour accepted)",
     "encoding/json/v2 Unmarshal (strict except t/z/:60), or a wrapper type whose "
     "UnmarshalJSON runs the strict regex first"),
    ("SCAN-GO-OFFSET-SECONDS", "R3339-5.6/time-numoffset", _GO,
     r"\btime\.(?:LoadLocation|FixedZone)\(|\.Format\(\s*time\.RFC3339(?:Nano)?\s*\)"
     r"|\.Marshal(?:JSON|Text)\(", r"\.UTC\(\)", "info",
     "offset with seconds (LMT / pre-1972 zones, FixedZone with seconds): Format/MarshalJSON "
     "keep the wall time and drop the offset seconds -- a WRONG instant (Monrovia 1970: "
     "11:15:30-00:44 for 11:59:30Z); FixedZone >= 24 h prints +24:00; Format has no error "
     "for years outside 0000-9999 (advisory heuristic)",
     "t.UTC().Format(time.RFC3339Nano) for the wire/storage, or check "
     "_, off := t.Zone(); off%60 != 0 || off <= -86400 || off >= 86400 and convert to UTC"),
    ("SCAN-GO-OFFSET-NO-COLON", "R3339-5.6/time-numoffset", _GO,
     r"05(?:\.[09]+)?\s?[-Z]07(?:00)?[\"`]", None, "error",
     "Go layout -0700 / Z0700 prints +0200 (no colon); -07 / Z07 prints +02",
     "Z07:00 / time.RFC3339"),
    ("SCAN-GO-NON-RFC-LAYOUT", "R3339-5.6/date-time", _GO,
     r"\btime\.(?:DateTime|UnixDate|ANSIC|RubyDate|Stamp(?:Milli|Micro|Nano)?)\b"
     r"|[\"`]2006-01-02 15:04:05", None, "warn",
     "not an RFC 3339 layout: time.DateTime has a space and no offset; "
     "'2006-01-02 15:04:05Z07:00' has a space separator",
     "time.RFC3339 / time.RFC3339Nano"),
    ("SCAN-GO-STRING", "R3339-5.6/date-time", _GO,
     r"(?:\btime\.Now\(\)|\b(?:t|ts|tm|now|\w*(?:Time|Timestamp|At|Date))\b)\.String\(\)",
     None, "warn",
     "time.Time.String() is for debugging: '2026-09-24 12:00:00 +0000 UTC' (plus "
     "' m=+0.0001' for time.Now()) -- not RFC 3339",
     "t.Format(time.RFC3339Nano) (or t.UTC().Format(...))"),
    ("SCAN-GO-NANO-SORT", "R3339-5.1/sortable", _GO,
     r"(?i:sort|key|filename|file_name|path|cursor|order).*\btime\.RFC3339Nano\b"
     r"|\btime\.RFC3339Nano\b.*(?i:sort|key|filename|file_name|path|cursor|order)",
     None, "info",
     "RFC3339Nano trims trailing zeros ('.123', no fraction when ns = 0), so string order "
     "is not time order (§5.1) when used as a sort key / file name / text column",
     "t.UTC().Format(\"2006-01-02T15:04:05.000000000Z07:00\") (format only; as a parse "
     "layout it rejects other fraction lengths)"),
    ("SCAN-GO-ZERO-OMITEMPTY", "R3339-5.6/sentinel-value", _GO,
     r"\btime\.Time\b.*omitempty", r"\*\s*time\.Time\b|omitzero", "warn",
     "json v1 omitempty never omits a zero time.Time: '0001-01-01T00:00:00Z' is sent as if "
     "it were a real instant (check t.IsZero())",
     "`json:\",omitzero\"` (Go >= 1.24) or *time.Time"),
    ("SCAN-GO-ZONELESS-PARSE", "R3339-5.6/time-offset", _GO,
     r"\btime\.Parse(?:InLocation)?\(\s*[\"`]2006-01-02T15:04:05(?:\.[09]+)?[\"`]", None, "warn",
     "zone-less parse layout: time.Parse assumes UTC, ParseInLocation(…, time.Local) assumes "
     "host-local time; RFC 3339 requires an offset",
     "time.Parse(time.RFC3339, s) (requires an offset)"),
    ("SCAN-GO-FIXED-FRACTION-PARSE", "R3339-5.6/time-secfrac", _GO,
     r"\btime\.Parse(?:InLocation)?\(\s*[\"`][^\"`]*\.0+[^\"`]*[\"`]", None, "warn",
     "fixed '.000' parse layout rejects ':00Z' and any other number of fraction digits "
     "(too strict)",
     "time.Parse(time.RFC3339Nano, s) (any fraction length) behind the strict regex"),
    # --- Rust: chrono / time / jiff (probed: eval-rust/RUST.md §3) ----------
    ("SCAN-RS-CHRONO-FROMSTR", "R3339-5.6/lenient-parser", _RS,
     r"\.parse::<\s*(?:chrono::)?DateTime<|\bDateTime::<[\w:]+>::from_str\("
     r"|\bDateTime<[^>]*>.*\.parse\(\s*\)|\.parse\(\s*\).*\bDateTime<",
     r"parse_from_rfc3339", "warn",
     "chrono DateTime FromStr (and serde Deserialize) accepts +0100, 1-digit fields, "
     "year '24', '…:00UTC', '…:00 Z', surrounding whitespace incl. '\\n', +10000/-0001 years "
     "and :60 anywhere",
     "DateTime::parse_from_rfc3339(s) behind an anchored [0-9] RFC 3339 regex"),
    ("SCAN-RS-SERDE-CHRONO", "R3339-5.6/lenient-parser", _RS,
     r"^\s*(?:pub(?:\([^)]*\))?\s+)?\w+\s*:\s*(?:Option<\s*)?(?:chrono::)?DateTime<\s*"
     r"(?:chrono::)?(?:Utc|FixedOffset|Local)\s*>", None, "warn",
     "serde Deserialize for chrono DateTime<…> uses the lenient FromStr parser",
     "#[serde(deserialize_with = \"…\")] calling DateTime::parse_from_rfc3339 behind the strict regex"),
    ("SCAN-RS-CHRONO-TO-RFC3339", "R3339-5.6/time-numoffset", _RS,
     r"\.to_rfc3339(?:_opts)?\(|\bFixedOffset::(?:east|west)(?:_opt)?\(",
     r"with_timezone\(\s*&\s*(?:chrono::)?Utc\s*\)", "info",
     "chrono to_rfc3339 on a FixedOffset with seconds (LMT, east_opt(n) with n % 60 != 0) "
     "rounds the offset and keeps the wall time: -00:44:30 -> 11:15:30-00:45 (30 s WRONG); "
     "to_rfc3339() prints +00:00, not Z, for UTC (advisory heuristic)",
     "dt.with_timezone(&Utc).to_rfc3339_opts(SecondsFormat::AutoSi, true)"),
    ("SCAN-RS-DISPLAY", "R3339-5.6/date-time", _RS,
     r"\b(?:dt|ts|odt|ndt|now|timestamp|datetime|date_time|\w+_(?:at|time|ts))\s*\.to_string\(\)"
     r"|\b(?:Utc|Local)::now\(\)\s*\.to_string\(\)|\bOffsetDateTime::now_(?:utc|local)\(\)[^;]*\.to_string\(\)"
     r"|format!\(\s*\"\{\}\"\s*,\s*(?:dt|ts|odt|ndt|now|timestamp|datetime|\w+_(?:at|time|ts))\b",
     r"\.format\(|to_rfc3339", "warn",
     "Display/.to_string() on a date-time: chrono prints '2026-09-24 12:00:00 UTC', time "
     "prints '2026-09-24 12:00:00.0 +00:00:00' -- not RFC 3339 (jiff Timestamp/Zoned Display "
     "is conforming)",
     "chrono dt.to_rfc3339_opts(SecondsFormat::AutoSi, true); time t.format(&Rfc3339)"),
    ("SCAN-RS-TIME-ISO8601", "R3339-5.6/lenient-parser", _RS,
     r"\bIso8601::DEFAULT\b|\bwell_known::Iso8601\b", None, "warn",
     "time Iso8601 is ISO 8601, not RFC 3339: parsing accepts +24:00, +0200, +02, ',5', "
     "'T12:00Z', basic/week/ordinal dates and rejects t/z; formatting prints a 6-digit "
     "signed year",
     "time::format_description::well_known::Rfc3339"),
    ("SCAN-RS-TIME-SERDE-DEFAULT", "R3339-5.6/date-time", _RS,
     r"^\s*(?:pub(?:\([^)]*\))?\s+)?\w+\s*:\s*(?:Option<\s*)?(?:time::)?"
     r"(?:OffsetDateTime|PrimitiveDateTime)\b", None, "warn",
     "time's default serde form is a JSON array ([2026,267,12,0,0,0,0,0,0]), not an "
     "RFC 3339 string",
     "#[serde(with = \"time::serde::rfc3339\")] (::option for Option<…>)"),
    ("SCAN-RS-TIME-RFC3339-VALIDATOR", "R3339-5.6/date-time", _RS,
     r"\bOffsetDateTime::parse\([^,]+,\s*&(?:[\w:]*::)?Rfc3339\s*\)|\btime::serde::rfc3339\b",
     None, "info",
     "time Rfc3339 parsing is exact except the date/time separator: any byte is accepted "
     "('X', '_', '-', '\\n', NUL, a digit); do not use it alone as a validator",
     "check s.as_bytes()[10] is b'T' or b't' (or the strict regex) before parsing"),
    ("SCAN-RS-JIFF-TIMESTAMP-PARSE", "R9557-3.4/critical-suffix", _RS,
     r"\.parse::<\s*(?:jiff::)?Timestamp\s*>\(|\bTimestamp::from_str\("
     r"|\bjiff::Timestamp\b.*\.parse\(\s*\)",
     None, "warn",
     "jiff Timestamp parsing ignores the [time-zone] annotation even when critical "
     "('+05:00[!Europe/Paris]', 'Z[!Mars/Olympus]' accepted: violates RFC 9557 MUST); also "
     "accepts +02, +0200, +24:00, ',5', 'T12:00Z', basic format and :60 anywhere",
     "strict RFC 3339 regex first for plain RFC 3339; when a suffix may be present parse "
     "with Zoned::from_str (default Reject) or reject a '[!' suffix explicitly"),
    # --- Generic JS/TS: host-zone and sign bugs (SN-LOCAL §5: missed before) --
    ("SCAN-JS-LOCAL-DATE-PARTS", "R3339-4.4/local-time", _JS,
     r"\bnew\s+Date\s*\(", None, "warn",
     "new Date(y, m, d, …) with 3+ components builds the value in the HOST's time zone: "
     "the instant (and any UTC string made from it) depends on TZ of the machine; "
     "new Date(1970, 0, 1, …) is not the epoch outside UTC",
     "new Date(Date.UTC(2000, m - 1, d, h, mi, s)) then setUTCFullYear(y, m - 1, d); "
     "or Temporal.PlainDateTime / ZonedDateTime with an explicit zone"),
    ("SCAN-JS-FLOOR-MOD-SPLIT", "R3339-5.6/time-numoffset", _JS,
     r"\bMath\.floor\(\s*\(?\s*([A-Za-z_$][\w$.]*)\s*\)?\s*/\s*([0-9]+)\s*\)", None, "warn",
     "Math.floor(x / N) with x % N on the same or an adjacent line: for negative x floor "
     "rounds down but % keeps the sign (-30 -> -1 h and -30 min = -90 min), so negative "
     "offsets/minutes split wrongly (heuristic)",
     "q = Math.floor(x / N); r = ((x % N) + N) % N  (or Math.trunc for both, or divmod)"),
    ("SCAN-JS-INTL-HOUR-OFFSET", "R3339-5.6/time-numoffset", _JS,
     r"\b[\w$]*[Hh]our[\w$]*\s*-\s*12\b", None, "info",
     "zone offset derived from an Intl/toLocaleString hour string ('(tzHour - 12)' from a "
     "12:00 UTC reference): wrong for offsets beyond ±12 h, for dates other than the reference "
     "(DST, historic offsets) and hour12:false can give '24' (advisory)",
     "Intl.DateTimeFormat(…, {timeZoneName: 'longOffset'}) on the actual instant, or "
     "Temporal.ZonedDateTime.from({…, timeZone}).offset"),
    # --- ServiceNow Glide server scripts (SN-DOCS §7; gated on Glide markers) ---
    ("SCAN-SN-STRING-SURGERY", "R9557-2.2/z-means-utc-known", _JS,
     r"\b(?:getValue|getDisplayValue(?:Internal)?|toString)\(\s*(?:['\"][\w.]*['\"])?\s*\)"
     r"(?:\s*\.[\w$]+\([^()]*\))*\s*\+\s*['\"][TZ]['\"]"
     r"|['\"]T['\"]\s*\+\s*[\w$.]*\bget(?:Value|DisplayValue\w*)\("
     r"|\.replace\(\s*(?:['\"] ['\"]|/ /g?|/\\s/g?)\s*,\s*['\"]T['\"]\s*\)",
     None, "warn",
     "RFC 3339 built by string surgery on a Glide value ('T'/'Z' glued to getValue()/"
     "getDisplayValue(), or .replace(' ', 'T')): getValue() is UTC only if "
     "glide.sys.internal.tz is UTC; display values are in the session user's zone and "
     "format, so 'Z' labels local time as UTC",
     "new Date(Number(String(gdt.getNumericValue()))).toISOString() (toRfc3339 helper)"),
    ("SCAN-SN-DISPLAY-VALUE-OUT", "R3339-5.6/time-offset", _JS,
     r"\bgetDisplayValue(?:Internal)?\(\s*\)|\bgs\.(?:nowDateTime|now)\(\s*\)", None, "warn",
     "display value / gs.nowDateTime() in integration code (RESTMessageV2, setRequestBody, "
     "JSON.stringify, response.setBody): user time zone and user format, no offset -- the "
     "output changes with the user (heuristic)",
     "toRfc3339(gdt) from getNumericValue() (UTC, 'Z')"),
    ("SCAN-SN-GDT-UNCHECKED", "R3339-5.6/lenient-parser", _JS,
     r"\bnew\s+GlideDateTime\(\s*([A-Za-z_$][\w.$]*)\s*\)"
     r"|\b[\w$]*(?i:gdt|date|time|_on|_at)\.setValue\(\s*([A-Za-z_$][\w.$]*)\s*\)",
     None, "warn",
     "new GlideDateTime(value) / gdt.setValue(value) on external input: ISO 'T…Z' forms are "
     "documented as unsupported and a failed parse is silent (isValid() false, earlier "
     "value kept); no isValid() check nearby",
     "fromRfc3339(s) (strict regex, then setNumericValue), and check gdt.isValid()"),
    ("SCAN-SN-T-TO-SPACE", "R3339-5.6/time-offset", _JS,
     r"\.replace\(\s*(?:['\"]T['\"]|/T/g?)\s*,\s*['\"] ['\"]\s*\)", r"toISOString", "warn",
     "replace('T', ' ') turns an RFC 3339 string into Glide format but keeps/garbles the "
     "offset or silently drops it: '…T12:00:00+02:00' is read as 12:00 UTC (WRONG VALUE)",
     "fromRfc3339(s): parse, subtract the offset via epoch ms, setNumericValue"),
    ("SCAN-SN-SYSPARM-DISPLAY", "R3339-5.6/time-offset", _ANY,
     r"sysparm_(?:input_)?display_value\s*(?:=|['\"]?\s*:\s*)['\"]?(?:true|all)\b", None, "info",
     "sysparm_display_value=true/all (or sysparm_input_display_value=true): date-times are "
     "read/written in the API user's profile zone and format, not UTC (advisory)",
     "sysparm_display_value=false (default): yyyy-MM-dd HH:mm:ss in UTC, convert on the client"),
    ("SCAN-SN-FLOW-Z-FORMAT", "R9557-2.2/z-means-utc-known", _ANY,
     r"yyyy-MM-dd'T'HH:mm:ss(?:\.S+)?'Z'", None, "info",
     "Flow/Fluent date format with a literal 'Z': correct only when the value is UTC "
     "(Date/Time pills are UTC at runtime; a String pill is returned untransformed) (advisory)",
     "keep it on Date/Time pills only, and add a Flow test that asserts the 'Z' output"),
    # --- ServiceNow Fluent (.now.ts; gated on an @servicenow/sdk import) -------
    ("SCAN-SN-FLUENT-DT-VALUE", "R3339-5.6/date-time", _JS,
     r"['\"][0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt][0-9]|[ ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?"
     r"(?:[Zz]|[+-][0-9]{2}:?[0-9]{2}))"
     r"|\b(?![Tt]ime[Zz]one\b)[\w$]*(?i:date|time|_on|_at|dt|due|start|end)[\w$]*['\"]?\s*:"
     r"\s*[^,}]*\bas\s+(?:any|unknown)\b"
     r"|@ts-(?:ignore|expect-error)",
     None, "warn",
     "Fluent date-time field value with 'T'/'Z'/an offset, or forced past the type with "
     "'as any' / @ts-ignore: the string goes into glide_date_time XML verbatim (no build "
     "check); the platform expects UTC 'yyyy-MM-dd HH:mm:ss'",
     "convert before writing the source: Temporal.Instant.from(s).toString().slice(0, 19)"
     ".replace('T', ' ') (UTC), and keep literals typed"),
    ("SCAN-SN-SCHEDULE-FLOATING", "R3339-4.4/local-time", _JS,
     r"\bexecution(?:Start|End)\s*:", None, "info",
     "ScheduledScript executionStart/End with timeZone 'floating' or no timeZone: the SDK "
     "build serializes the value as UTC (scheduled-script-plugin maps both to 'UTC'); confirm "
     "the literal was meant as UTC wall time (advisory)",
     "give an explicit IANA timeZone (e.g. 'UTC' or the zone the literal is written in)"),
    ("SCAN-SN-HOST-ZONE-CONVERT", "R3339-4.4/local-time", _JS,
     r"\b(?:dateTimeFieldToXML|convertXMLToDateTime|timeFieldToXML)\)?\s*\(", None, "warn",
     "SDK helper dateTimeFieldToXML/convertXMLToDateTime/timeFieldToXML called with "
     "timeZone 'floating' or no zone: it converts with the HOST's zone "
     "(Intl.DateTimeFormat().resolvedOptions().timeZone / local Date), so output depends on "
     "the machine that runs it",
     "pass an explicit IANA zone ('UTC'), or run with TZ=UTC"),
    ("SCAN-SN-TIME-NO-ZONE", "R3339-4.4/local-time", _JS,
     r"(?<![\w$.])Time\(\s*(?:\{|$)", None, "warn",
     "Fluent Time({…}) without a zone argument is converted with the BUILD HOST's zone",
     "Time({…}, 'UTC') with a UTC-computed time (or build with TZ=UTC)"),
    # --- Elixir ---------------------------------------------------------------
    ("SCAN-EX-NAIVE", "R3339-5.6/time-offset", _EX,
     r"\bNaiveDateTime\.(?:to_iso8601|utc_now|local_now)\b"
     r"|\bfield\(?\s*:\w+\s*,\s*:naive_datetime(?:_usec)?\b|\btimestamps\(\s*\)", None, "warn",
     "NaiveDateTime has no offset: to_iso8601 emits '2024-01-01T12:00:00' (not RFC 3339); "
     "Ecto :naive_datetime fields and timestamps() (default type) store no zone",
     "DateTime.utc_now() |> DateTime.to_iso8601(); Ecto: :utc_datetime_usec / "
     "timestamps(type: :utc_datetime_usec)"),
    ("SCAN-EX-FROM-ISO8601", "R3339-5.6/lenient-parser", _EX,
     r"\b(?:DateTime|NaiveDateTime)\.from_iso8601!?\s*\(", None, "info",
     "Elixir from_iso8601 is an ISO 8601 parser: it accepts forms RFC 3339 excludes (e.g. a "
     "space separator) and rejects second=60; NaiveDateTime.from_iso8601 discards the offset "
     "(advisory)",
     "anchored RFC 3339 regex first, then DateTime.from_iso8601(s) (keeps the offset)"),
    # --- Dart -----------------------------------------------------------------
    ("SCAN-DART-PARSE", "R3339-5.6/lenient-parser", _DART,
     r"\bDateTime\.(?:parse|tryParse)\s*\(", None, "warn",
     "Dart DateTime.parse accepts far more than RFC 3339: space separator, date-only, missing "
     "seconds, basic format, '+HHMM' / '+HH' offsets and no offset at all (-> LOCAL time)",
     "anchored RFC 3339 RegExp first (require the offset), then DateTime.parse(s)"),
    ("SCAN-DART-ISO-STRING", "R3339-5.6/time-offset", _DART,
     r"\.toIso8601String\(\s*\)", r"toUtc\(\)|isUtc|DateTime\.utc\(|\.now\(\)\.toUtc", "warn",
     "toIso8601String() on a LOCAL DateTime has no offset ('2024-01-01T12:00:00.000'); only "
     "UTC values get 'Z'",
     "dt.toUtc().toIso8601String()"),
    # --- Protocol Buffers -----------------------------------------------------
    ("SCAN-PROTO-STRING-TIME", "R3339-5.6/schema-format", _PROTO,
     r"^\s*(?:optional\s+|repeated\s+)?string\s+(?i:\w*(?:_at|time|date|timestamp)\w*)\s*=\s*[0-9]+",
     r"(?i)string\s+\w*(?:zone|format|unit|type|kind)\w*\s*=", "warn",
     "timestamp carried as a proto string: the format is not enforced by the schema (any "
     "producer may send '2024-01-01 12:00', '+0200', local time)",
     "google.protobuf.Timestamp (proto3 JSON mapping is RFC 3339 with 'Z'); if a string must "
     "stay, document the RFC 3339 profile and validate it"),
    ("SCAN-PROTO-ISO8601-COMMENT", "R3339-5.6/schema-format", _PROTO,
     r"(?://|/\*|^\s*\*).*\bISO[ _-]?8601\b", None, "info",
     "comment promises 'ISO 8601' for a field: ISO 8601 allows basic format, week dates, "
     "missing offset and more -- the contract is not RFC 3339 (advisory)",
     "google.protobuf.Timestamp, or state the RFC 3339 profile (T, seconds, Z or ±hh:mm)"),
    # --- Salesforce Apex (.cls / .trigger) --------------------------------------
    ("SCAN-APEX-VALUEOF", "R3339-5.6/time-offset", _APEX,
     r"(?i)\bdatetime\.valueof\s*\(\s*(?!['\"])", None, "warn",
     "Datetime.valueOf(string) parses 'yyyy-MM-dd HH:mm:ss' in the running user's time zone: "
     "no 'T', no offset; an RFC 3339 string throws or loses its offset",
     "(Datetime) JSON.deserialize('\"' + s + '\"', Datetime.class) behind an anchored RFC 3339 "
     "regex, or Datetime.valueOfGmt for UTC wall time"),
    ("SCAN-APEX-FORMAT-LOCAL-Z", "R9557-2.2/z-means-utc-known", _APEX,
     r"(?i)\.format\(\s*'(?:[^'\\]|\\.)*?\\'Z\\'", None, "warn",
     "Datetime.format(\"…'Z'\") formats in the user's time zone, so the literal 'Z' labels "
     "local time as UTC",
     "dt.formatGmt('yyyy-MM-dd\\'T\\'HH:mm:ss.SSS\\'Z\\'')"),
    # --- SQL ------------------------------------------------------------------
    ("SCAN-SQL-TO-CHAR-Z", "R9557-2.2/z-means-utc-known", _SQL,
     r"(?i)\bto_char\s*\([^;]*(?:\"Z\"|SS(?:\.(?:US|MS|FF[1-6]))?Z')",
     r"(?i)at\s+time\s+zone\s+'(?:utc|gmt|z|etc/utc|\+?00:?00)'|timezone\(\s*'utc'", "warn",
     "Postgres to_char(… '\"Z\"') labels the value UTC, but to_char formats timestamptz in the "
     "SESSION TimeZone (timestamp as stored): without AT TIME ZONE 'UTC' the 'Z' can be wrong",
     "to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"),
    ("SCAN-SQL-TO-CHAR-OFFSET", "R3339-5.6/time-numoffset", _SQL,
     r"(?i)\bto_char\s*\(", None, "error",
     "Postgres to_char offset: TZ/tz print an abbreviation ('CEST'), OF prints '+02' (no "
     "minutes when they are zero); neither is time-numoffset",
     "TZH:TZM ('YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM'), or AT TIME ZONE 'UTC' plus \"Z\""),
    ("SCAN-SQL-MYSQL-FORMAT-Z", "R9557-2.2/z-means-utc-known", _SQL,
     r"\b(?i:date_format)\s*\([^;]*%[sfT]Z['\"]",
     r"(?i)utc_timestamp|convert_tz\([^)]*'(?:\+00:00|utc)'", "warn",
     "MySQL DATE_FORMAT has no offset specifier: a literal 'Z' is right only if the value is "
     "UTC (TIMESTAMP is shown in the session time_zone; DATETIME stores no zone)",
     "DATE_FORMAT(CONVERT_TZ(ts, @@session.time_zone, '+00:00'), '%Y-%m-%dT%H:%i:%s.%fZ')"),
    ("SCAN-SQL-TEXT-CAST", "R3339-5.6/date-time", _SQL,
     r"(?i)(?:\bnow\(\)|\bcurrent_timestamp\b|\blocaltimestamp\b"
     r"|\b[\w.\"]*(?:_at|time|timestamp|_ts)\"?)\s*::\s*(?:text|varchar|character\s+varying)\b"
     r"|\bcast\s*\(\s*(?:now\(\)|[\w.\"]*(?:_at|time|timestamp|_ts)\"?)\s+as\s+(?:text|varchar)\b",
     None, "warn",
     "timestamptz::text depends on DateStyle and the session TimeZone: '2024-01-01 "
     "12:00:00+02' (space, hour-only offset; LMT gives '+00:09:21'); timestamp::text has no "
     "offset -- not RFC 3339 for API output",
     "to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"),
    # --- Swift / Foundation (probed, macOS 27 Foundation) -----------------------
    ("SCAN-SWIFT-ISO8601-DEFAULT", "R3339-5.6/time-secfrac", _SWIFT,
     r"\bISO8601DateFormatter\(\s*\)", None, "warn",
     "ISO8601DateFormatter() with default formatOptions (.withInternetDateTime) returns nil "
     "for a fractional second ('…:00.5Z'), second=60 and lower-case t/z: valid RFC 3339 "
     "input is rejected",
     "try [.withInternetDateTime] then [.withInternetDateTime, .withFractionalSeconds] behind "
     "an anchored RFC 3339 regex (or a strict hand parser)"),
    ("SCAN-SWIFT-FRACTIONAL-ONLY", "R3339-5.6/time-secfrac", _SWIFT,
     r"\.withFractionalSeconds\b", None, "warn",
     "with .withFractionalSeconds an ISO8601DateFormatter returns nil for input WITHOUT a "
     "fraction ('…:00Z') and always emits exactly 3 digits; time-secfrac is optional",
     "parse with and without .withFractionalSeconds (two formatters), strict regex first"),
    ("SCAN-SWIFT-POSIX-LOCALE", "R3339-5.6/date-time", _SWIFT,
     r"\bDateFormatter\(\s*\)", None, "warn",
     "DateFormatter with a fixed dateFormat but no en_US_POSIX locale: the user's calendar, "
     "12/24-hour setting and numbering system change the text (Buddhist year 2567, 'HH' as "
     "12-hour, non-ASCII digits)",
     "df.locale = Locale(identifier: \"en_US_POSIX\"); df.timeZone = TimeZone(identifier: "
     "\"UTC\") (or ISO8601DateFormatter)"),
    ("SCAN-SCHEMA-DATE-TIME", "R3339-5.6/schema-format", _SCHEMA,
     r"[\"']?format[\"']?\s*:\s*[\"']?date-time\b", None, "info",
     "schema format date-time: confirm the validator in use against the vectors "
     "(lowercase t/z, second=60, -00:00, space separator)",
     "run the vectors against the schema validator (adapter) and document its profile"),
)

_YEAR_COMPONENT = re.compile(r"\{4\}|\(\?P<year>")
_JS_YEAR_COMPONENT = re.compile(r"\\{1,2}d\{4\}|\[0-9\]\{4\}")
_PY_MATCH_CALL = re.compile(r"\.(?:match|search)\s*\(")
_JS_STRING_LIT = re.compile(r"(['\"`])((?:\\.|(?!\1).)*)\1")
_SUFFIX_BUILD = re.compile(r"\[\{|['\"]\[['\"]\s*\+")


_PY_STR_CONT = re.compile(r"""\s*(?:[rRbBfFuU]{1,2})?['"]""")


def _ctx_py_regex_dollar(lines, i, text):
    # The statement: this line plus the string-literal continuation lines
    # directly above it (implicit concatenation) and the line that opens them.
    j = i
    while j > 0 and i - j < 8 and _PY_STR_CONT.match(lines[j]):
        j -= 1
    window = "\n".join(lines[j:i + 1])
    return bool(_YEAR_COMPONENT.search(window) and _PY_MATCH_CALL.search(text))


def _ctx_js_regexp_no_caret(lines, i, text):
    if not _JS_YEAR_COMPONENT.search(text):
        return False
    args = lines[i][re.search(r"\bnew\s+RegExp\s*\(", lines[i]).end():]
    m = _JS_STRING_LIT.search(args)
    if m is None:
        return "+" in args  # concatenation of constants, no literal to inspect
    return not m.group(2).startswith("^")


def _ctx_py_tz_str(lines, i, text):
    return bool(_SUFFIX_BUILD.search(text))


def _ctx_go_json_v1(lines, i, text):
    return "encoding/json/v2" not in text


_GO_FIXEDZONE = re.compile(r"\btime\.FixedZone\(\s*[^,]*,\s*([^)]*)\)")
_GO_ZONE_SRC = re.compile(r"\btime\.(?:LoadLocation|FixedZone)\(")


def _ctx_go_offset_seconds(lines, i, text):
    line = lines[i]
    if "LoadLocation(" in line:
        return True
    m = _GO_FIXEDZONE.search(line)
    if m:
        expr = m.group(1).strip()
        if re.fullmatch(r"-?\s*[0-9]+(?:\s*\*\s*[0-9]+)*", expr):
            n = 1
            for part in expr.replace("-", "").split("*"):
                n *= int(part)
            return n % 60 != 0 or n >= 86400
        return True  # computed offset: cannot tell
    # Format(RFC3339…) / Marshal…: only when the file builds such zones.
    return bool(_GO_ZONE_SRC.search(text))


def _rs_field_attrs_have(lines, i, needles):
    j = i - 1
    while j >= 0 and i - j <= 6 and lines[j].lstrip().startswith(("#[", "///", "//")):
        if any(n in lines[j] for n in needles):
            return True
        j -= 1
    return any(n in lines[i] for n in needles)


def _ctx_rs_serde_chrono(lines, i, text):
    return ("Deserialize" in text
            and not _rs_field_attrs_have(lines, i, ("deserialize_with", "serde(with")))


def _ctx_rs_time_serde(lines, i, text):
    return ("Serialize" in text
            and not _rs_field_attrs_have(lines, i, ("serialize_with", "serde(with")))


_LINE_COMMENT = re.compile(r"//[^'\"`]*$")
_OPEN = {"(": ")", "[": "]", "{": "}"}


def _call_args(lines, i, pos, max_lines=6):
    """Split the arguments of the call whose '(' is at ``lines[i][pos]``.

    Follows the call over up to ``max_lines`` further lines (dropping trailing
    ``//`` comments) and returns the top-level argument texts, or None when the
    closing parenthesis is not found."""
    buf = lines[i][pos + 1:]
    for k in range(1, max_lines + 1):
        if i + k >= len(lines):
            break
        buf = _LINE_COMMENT.sub("", buf) + "\n" + lines[i + k]
    args, cur, stack, quote, esc = [], [], [], None, False
    for ch in buf:
        if quote:
            cur.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in "'\"`":
            quote = ch
        elif ch in _OPEN:
            stack.append(_OPEN[ch])
        elif ch in ")]}":
            if not stack:
                if ch != ")":
                    return None
                args.append("".join(cur).strip())
                return [a for a in args if a] if args != [""] else []
            stack.pop()
        elif ch == "," and not stack:
            args.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    return None


_NEW_DATE = re.compile(r"\bnew\s+Date\s*\(")


def _ctx_js_local_date_parts(lines, i, text):
    if lines[i].lstrip().startswith(("//", "*", "/*")):
        return False  # prose in a comment
    for m in _NEW_DATE.finditer(lines[i]):
        args = _call_args(lines, i, m.end() - 1, max_lines=8)
        if args and len(args) >= 3 and not args[0].startswith(("'", '"', "`")):
            return True
    return False


_FLOOR_DIV = re.compile(r"\bMath\.floor\(\s*\(?\s*([A-Za-z_$][\w$.]*)\s*\)?\s*/\s*([0-9]+)\s*\)")


def _ctx_js_floor_mod(lines, i, text):
    for m in _FLOOR_DIV.finditer(lines[i]):
        var, div = re.escape(m.group(1)), m.group(2)
        window = "\n".join(lines[max(0, i - 1):i + 2])
        guard = "\n".join(lines[max(0, i - 3):i + 2])
        if not re.search(r"(?<![\w$.])" + var + r"\s*%\s*" + div + r"\b", window):
            continue
        if re.search(r"\+\s*" + div + r"\s*\)\s*%\s*" + div + r"\b", window):
            continue  # ((x % N) + N) % N: already non-negative
        if re.search(r"(?<![\w$.])" + var + r"\s*<=?\s*0\b|Math\.(?:abs|sign)\(", guard):
            continue  # sign handled explicitly
        return True
    return False


def _ctx_js_intl_hour(lines, i, text):
    return bool(re.search(r"hour12\s*:\s*false", text))


# ServiceNow gates: Glide server-script markers and Fluent (.now.ts) markers.
_SN_GLIDE = re.compile(r"\bGlide(?:DateTime|Record|Date|Time|Duration|Aggregate|System)\b"
                       r"|\bgs\.\w+\(|\bsn_ws\b|\bRESTMessageV2\b|\bcurrent\.\w+")
_SN_FLUENT = re.compile(r"@servicenow/sdk(?:/[\w-]+)?['\"]|\bNow\.ID\[")
_SN_OUTBOUND = re.compile(r"\bRESTMessageV2\b|\bSOAPMessageV2\b|\bsetRequestBody\(|\bsetBody\("
                          r"|\bJSON\.stringify\(|\bsn_ws\.|\bsetStringParameter(?:NoEscape)?\("
                          r"|\bresponse\.set\w+\(")
_DATEISH = re.compile(r"(?i)gdt|date|time|_on\b|_at\b|created|updated|opened|closed|due|"
                      r"start|end|when")


def _ctx_sn_glide(lines, i, text):
    return bool(_SN_GLIDE.search(text))


def _ctx_sn_any(lines, i, text):
    return bool(_SN_GLIDE.search(text) or _SN_FLUENT.search(text))


def _ctx_sn_display_out(lines, i, text):
    if not _SN_GLIDE.search(text):
        return False
    line = lines[i]
    if "getDisplayValue" in line and not _DATEISH.search(line):
        return False  # getDisplayValue() on a reference/choice field
    return bool(_SN_OUTBOUND.search("\n".join(lines[max(0, i - 20):i + 21])))


_GDT_ARG = re.compile(r"\bnew\s+GlideDateTime\(\s*([A-Za-z_$][\w.$]*)\s*\)"
                      r"|\.setValue\(\s*([A-Za-z_$][\w.$]*)\s*\)")


def _ctx_sn_gdt_unchecked(lines, i, text):
    if not _SN_GLIDE.search(text):
        return False
    m = _GDT_ARG.search(lines[i])
    arg = (m.group(1) or m.group(2)) if m else ""
    if re.match(r"(?i)(?:current|previous|gr|grs?\w*)\.|.*gdt|.*glidedatetime", arg):
        return False  # copy of another GlideDateTime / GlideElement, not external text
    return "isValid(" not in "\n".join(lines[max(0, i - 3):i + 7])


def _ctx_sn_flow_format(lines, i, text):
    return bool(re.search(r"dateToString|stringToDate|servicenow|\bGlide|sys_hub", text))


_TS_IGNORE = re.compile(r"@ts-(?:ignore|expect-error)")
_FLUENT_DATE_LINE = re.compile(r"['\"][0-9]{4}-[0-9]{2}-[0-9]{2}|(?i:date|time|_on\b|_at\b|due)")


def _ctx_sn_fluent_dt(lines, i, text):
    if not _SN_FLUENT.search(text):
        return False
    line = lines[i]
    if _TS_IGNORE.search(line) and not re.search(r"['\"][0-9]{4}-|\bas\s+(?:any|unknown)\b", line):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        return bool(_FLUENT_DATE_LINE.search(nxt))
    return True


_SCHED_CALL = re.compile(r"\bScheduledScript\s*\(")
_SCHED_TZ = re.compile(r"\btimeZone\s*:\s*(['\"`])(?!floating\1)")


def _ctx_sn_schedule_floating(lines, i, text):
    for j in range(i, max(-1, i - 60), -1):
        ms = list(_SCHED_CALL.finditer(lines[j]))
        if not ms:
            continue
        m = ms[-1]
        if j == i and m.start() > lines[i].find("execution"):
            ms = ms[:-1]
            if not ms:
                continue
            m = ms[-1]
        args = _call_args(lines, j, m.end() - 1, max_lines=80)
        block = ",".join(args) if args is not None else "\n".join(lines[j:i + 40])
        return not _SCHED_TZ.search(block)
    return False


_HOST_ZONE_HELPER = re.compile(r"\b(?:dateTimeFieldToXML|convertXMLToDateTime|timeFieldToXML)"
                               r"\)?\s*\(")


def _ctx_sn_host_zone_convert(lines, i, text):
    line = lines[i].lstrip()
    if line.startswith(("//", "*", "/*")) or re.match(r"(?:export\s+)?(?:declare\s+)?function\b", line):
        return False
    for m in _HOST_ZONE_HELPER.finditer(lines[i]):
        args = _call_args(lines, i, m.end() - 1)
        if args is None:
            continue
        if len(args) == 1 or (len(args) >= 2 and args[1] in ("'floating'", '"floating"',
                                                             "`floating`", "undefined", "null")):
            return True
    return False


_TIME_CALL = re.compile(r"(?<![\w$.])Time\(\s*(?:\{|$)")


def _ctx_sn_time_no_zone(lines, i, text):
    if not _SN_FLUENT.search(text):
        return False
    for m in _TIME_CALL.finditer(lines[i]):
        args = _call_args(lines, i, lines[i].index("(", m.start()))
        if args is not None and len(args) == 1 and args[0].startswith("{"):
            return True
    return False


_PY_DATEUTIL_MAIN = re.compile(r"\bdateutil\b.*\bparse\b|\bparser\.parse\s*\(|\bisoparse\s*\("
                               r"|\bpendulum\.parse\s*\(")
_PY_DATEUTIL_IMPORT = re.compile(r"\bfrom\s+dateutil\.parser\s+import\s+[^\n]*\bparse\b")


def _ctx_py_dateutil(lines, i, text):
    # A bare parse(...) call counts only in a file that imports dateutil's parse.
    return bool(_PY_DATEUTIL_MAIN.search(lines[i]) or _PY_DATEUTIL_IMPORT.search(text))


def _ctx_ex_naive(lines, i, text):
    if re.search(r"\btimestamps\(\s*\)", lines[i]) and not re.search(
            r"NaiveDateTime\.|:naive_datetime", lines[i]):
        return "Ecto" in text  # Ecto schema / migration default type
    return True


_SQL_FMT_LIT = re.compile(r"'((?:[^']|'')*)'")


def _ctx_sql_to_char_offset(lines, i, text):
    window = " ".join(lines[i:i + 6])
    for m in re.finditer(r"(?i)\bto_char\s*\(", window):
        args = _call_args([window], 0, m.end() - 1, max_lines=0)
        if not args or len(args) < 2:
            continue
        for lit in _SQL_FMT_LIT.findall(args[1]):
            bare = re.sub(r'"[^"]*"', "", lit)  # drop quoted literal text
            if re.search(r"(?:TZ|tz)(?![HMhm])|OF", bare):
                return True
    return False


def _ctx_swift_iso_default(lines, i, text):
    return "formatOptions" not in text


def _ctx_swift_posix(lines, i, text):
    return bool(re.search(r"\.dateFormat\s*=", text)) and "en_US_POSIX" not in text


_TEX_CLASS = re.compile(r"\\(?:ProvidesClass|NeedsTeXFormat|documentclass|LoadClass)\b")


def _ctx_apex(lines, i, text):
    return not _TEX_CLASS.search(text)  # .cls is also a LaTeX class file


# id -> predicate(lines, index, whole_text): extra condition for a line hit.
_SCAN_CONTEXT = {
    "SCAN-PY-DATEUTIL": _ctx_py_dateutil,
    "SCAN-EX-NAIVE": _ctx_ex_naive,
    "SCAN-SQL-TO-CHAR-OFFSET": _ctx_sql_to_char_offset,
    "SCAN-SWIFT-ISO8601-DEFAULT": _ctx_swift_iso_default,
    "SCAN-SWIFT-POSIX-LOCALE": _ctx_swift_posix,
    "SCAN-APEX-VALUEOF": _ctx_apex,
    "SCAN-APEX-FORMAT-LOCAL-Z": _ctx_apex,
    "SCAN-PY-REGEX-DOLLAR": _ctx_py_regex_dollar,
    "SCAN-JS-REGEXP-NO-CARET": _ctx_js_regexp_no_caret,
    "SCAN-PY-TZ-STR": _ctx_py_tz_str,
    "SCAN-GO-JSON-V1-TIME": _ctx_go_json_v1,
    "SCAN-GO-OFFSET-SECONDS": _ctx_go_offset_seconds,
    "SCAN-RS-SERDE-CHRONO": _ctx_rs_serde_chrono,
    "SCAN-RS-TIME-SERDE-DEFAULT": _ctx_rs_time_serde,
    "SCAN-JS-LOCAL-DATE-PARTS": _ctx_js_local_date_parts,
    "SCAN-JS-FLOOR-MOD-SPLIT": _ctx_js_floor_mod,
    "SCAN-JS-INTL-HOUR-OFFSET": _ctx_js_intl_hour,
    "SCAN-SN-STRING-SURGERY": _ctx_sn_glide,
    "SCAN-SN-DISPLAY-VALUE-OUT": _ctx_sn_display_out,
    "SCAN-SN-GDT-UNCHECKED": _ctx_sn_gdt_unchecked,
    "SCAN-SN-T-TO-SPACE": _ctx_sn_any,
    "SCAN-SN-FLOW-Z-FORMAT": _ctx_sn_flow_format,
    "SCAN-SN-FLUENT-DT-VALUE": _ctx_sn_fluent_dt,
    "SCAN-SN-SCHEDULE-FLOATING": _ctx_sn_schedule_floating,
    "SCAN-SN-TIME-NO-ZONE": _ctx_sn_time_no_zone,
    "SCAN-SN-HOST-ZONE-CONVERT": _ctx_sn_host_zone_convert,
}


# ---------------------------------------------------------------------------
# Data tables
# ---------------------------------------------------------------------------
LEAP_SECONDS = frozenset({
    # RFC 3339 Appendix D (from USNO tai-utc.dat), TAI-UTC after insertion
    (1972, 6, 30), (1972, 12, 31), (1973, 12, 31), (1974, 12, 31),   # 11-14
    (1975, 12, 31), (1976, 12, 31), (1977, 12, 31), (1978, 12, 31),  # 15-18
    (1979, 12, 31), (1981, 6, 30), (1982, 6, 30), (1983, 6, 30),     # 19-22
    (1985, 6, 30), (1987, 12, 31), (1989, 12, 31), (1990, 12, 31),   # 23-26
    (1992, 6, 30), (1993, 6, 30), (1994, 6, 30), (1995, 12, 31),     # 27-30
    (1997, 6, 30), (1998, 12, 31),                                   # 31-32
    # Later IERS Bulletin C announcements (after RFC 3339 was published)
    (2005, 12, 31), (2008, 12, 31), (2012, 6, 30), (2015, 6, 30),    # 33-36
    (2016, 12, 31),                                                  # 37
})
LEAP_SECONDS_CUTOFF = "2016-12-31"

KNOWN_SUFFIX_KEYS = frozenset({"u-ca"})  # IANA "Timestamp Suffix Tag Keys" (RFC 9557 Table 1)

# Unicode BCP 47 "ca" key values (CLDR bcp47/calendar.xml snapshot), plus the
# long alias ethiopic-amete-alem and deprecated islamicc.  RFC 9557 §5 defers
# to [TR35]; this list is a snapshot and may lag CLDR.
KNOWN_CALENDARS = frozenset({
    "buddhist", "chinese", "coptic", "dangi", "ethioaa", "ethiopic",
    "ethiopic-amete-alem", "gregory", "hebrew", "indian", "islamic",
    "islamic-civil", "islamic-rgsa", "islamic-tbla", "islamic-umalqura",
    "islamicc", "iso8601", "japanese", "persian", "roc",
})

PROFILES = ("rfc3339", "ixdtf")
PRODUCTIONS = ("date-time", "full-date", "full-time", "partial-time")
LEAP_MODES = ("iers-months", "table", "any-month-end", "grammar")
DEFAULT_LEAP_MODE = "iers-months"
LEAP_MONTHS = frozenset({3, 6, 9, 12})  # Appendix D (CCIR) opportunities
FIRST_LEAP_YEAR = 1972                   # first UTC leap second: 1972-06-30
TZDATA_MODES = ("auto", "off")
LMT_MODES = ("nearest", "any-sub-minute")
DEFAULT_LMT_MODE = "nearest"

_DIGITS = frozenset("0123456789")
_TZ_PART = re.compile(r"[A-Za-z._][A-Za-z._0-9+\-]*")
_SUFFIX_KEY = re.compile(r"[a-z_][a-z_0-9\-]*")
_SUFFIX_VALUES = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
_NUMOFFSET = re.compile(r"([+-])([0-9]{2}):([0-9]{2})")


def is_leap_year(year: int) -> bool:
    """RFC 3339 Appendix C."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year: int, month: int) -> int:
    """RFC 3339 §5.7 table."""
    if month == 2:
        return 29 if is_leap_year(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def _shift_day(y: int, m: int, d: int, delta: int):
    """Move a proleptic-Gregorian date by -1, 0 or +1 day (no year bounds)."""
    if delta < 0:
        if d > 1:
            return y, m, d - 1
        if m > 1:
            return y, m - 1, days_in_month(y, m - 1)
        return y - 1, 12, 31
    if delta > 0:
        if d < days_in_month(y, m):
            return y, m, d + 1
        if m < 12:
            return y, m + 1, 1
        return y + 1, 1, 1
    return y, m, d


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
@dataclass
class Issue:
    code: str
    message: str

    def to_dict(self):
        return {"code": self.code, "message": self.message}


@dataclass
class Result:
    input: str
    profile: str
    ok: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    fields: dict | None = None
    options: dict = field(default_factory=dict)

    @property
    def error_codes(self):
        return [e.code for e in self.errors]

    @property
    def warning_codes(self):
        return [w.code for w in self.warnings]

    def to_dict(self):
        return {
            "ok": self.ok,
            "input": self.input,
            "profile": self.profile,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "fields": self.fields,
            "options": self.options,
        }


class _Fail(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class _Cursor:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def at_end(self):
        return self.i >= len(self.s)

    def digits(self, n, code, what):
        chunk = self.s[self.i:self.i + n]
        if len(chunk) != n or any(ch not in _DIGITS for ch in chunk):
            raise _Fail(code, f"{what}: expected {n} ASCII digits at offset {self.i}, "
                              f"found {chunk!r}")
        self.i += n
        return int(chunk)

    def lit(self, chars, code, what):
        ch = self.peek()
        if ch and ch in chars:
            self.i += 1
            return ch
        raise _Fail(code, f"{what}: expected {chars!r} at offset {self.i}, "
                          f"found {ch!r}" if ch else f"{what}: expected {chars!r}, "
                                                     f"found end of input")


@functools.lru_cache(maxsize=1)
def _zone_names():
    try:
        import zoneinfo
        names = zoneinfo.available_timezones()
    except Exception:  # pragma: no cover - platform without zoneinfo
        return None
    if not names:
        return None
    return frozenset(names), {n.lower(): n for n in names}


def tzdata_available() -> bool:
    return _zone_names() is not None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _parse_full_date(c, f, deferred):
    """Parse full-date.  The §5.7 day-of-month limit is semantic: it is put in
    ``deferred`` and reported only if the whole string is syntactically valid,
    so that e.g. '2023-02-30Tgarbage' reports the syntax error."""
    f["year"] = c.digits(4, "R3339-5.6/date-fullyear", "date-fullyear")
    c.lit("-", "R3339-5.6/date-separator", "full-date")
    mo = c.digits(2, "R3339-5.6/date-month", "date-month")
    if not 1 <= mo <= 12:
        raise _Fail("R3339-5.6/date-month", f"date-month {mo:02d} not in 01-12")
    f["month"] = mo
    c.lit("-", "R3339-5.6/date-separator", "full-date")
    d = c.digits(2, "R3339-5.6/date-mday", "date-mday")
    if not 1 <= d <= 31:
        raise _Fail("R3339-5.6/date-mday", f"date-mday {d:02d} not in 01-31")
    dim = days_in_month(f["year"], mo)
    if d > dim:
        deferred.append(Issue("R3339-5.7/date-mday",
                              f"date-mday {d:02d} exceeds {dim} for {f['year']:04d}-{mo:02d} "
                              f"(§5.7 table, Appendix C leap-year rule)"))
    f["day"] = d


def _parse_partial_time(c, f):
    h = c.digits(2, "R3339-5.6/time-hour", "time-hour")
    if h == 24:
        raise _Fail("R3339-5.7/time-hour-24",
                    "hour 24 is not allowed: §5.7 'only allows values between \"00\" and \"23\"'")
    if h > 23:
        raise _Fail("R3339-5.6/time-hour", f"time-hour {h:02d} not in 00-23")
    c.lit(":", "R3339-5.6/time-separator", "partial-time")
    mi = c.digits(2, "R3339-5.6/time-minute", "time-minute")
    if mi > 59:
        raise _Fail("R3339-5.6/time-minute", f"time-minute {mi:02d} not in 00-59")
    if c.peek() != ":":
        raise _Fail("R3339-5.6/time-second",
                    "time-second is mandatory in partial-time (hh:mm:ss)")
    c.i += 1
    sec = c.digits(2, "R3339-5.6/time-second", "time-second")
    if sec > 60:
        raise _Fail("R3339-5.6/time-second", f"time-second {sec:02d} not in 00-60")
    frac = None
    if c.peek() == ",":
        raise _Fail("R3339-5.6/time-secfrac",
                    "time-secfrac must use '.', not ',' (',' is only in Appendix A ISO grammar)")
    if c.peek() == ".":
        c.i += 1
        start = c.i
        while c.peek() and c.peek() in _DIGITS:
            c.i += 1
        if c.i == start:
            raise _Fail("R3339-5.6/time-secfrac", "time-secfrac needs at least one DIGIT after '.'")
        frac = c.s[start:c.i]
    f.update(hour=h, minute=mi, second=sec, secfrac=frac)


def _parse_offset(c, f, warnings):
    ch = c.peek()
    if ch in ("Z", "z") and ch:
        c.i += 1
        if ch == "z":
            warnings.append(Issue("R3339-5.6/lowercase-letter",
                                  "lower-case 'z' is valid, but generators SHOULD use upper case"))
        f.update(offset=ch, offset_minutes=0, offset_unknown=True)
        return
    if ch in ("+", "-") and ch:
        c.i += 1
        start = c.i - 1
        oh = c.digits(2, "R3339-5.6/time-numoffset", "time-numoffset hour")
        if oh > 23:
            raise _Fail("R3339-5.6/time-numoffset-hour",
                        f"time-numoffset hour {oh:02d} not in 00-23 (uses time-hour)")
        c.lit(":", "R3339-5.6/time-numoffset", "time-numoffset")
        om = c.digits(2, "R3339-5.6/time-numoffset", "time-numoffset minute")
        if om > 59:
            raise _Fail("R3339-5.6/time-numoffset-minute",
                        f"time-numoffset minute {om:02d} not in 00-59 (uses time-minute)")
        if c.peek() == ":":
            # "+01:00:00" / "-00:44:30": ISO 8601 / LMT-style offset seconds.
            # time-numoffset is exactly ("+" / "-") time-hour ":" time-minute.
            raise _Fail("R3339-5.6/time-numoffset",
                        f"offset-has-seconds: time-numoffset is +hh:mm only; found "
                        f"{c.s[start:c.i + 3]!r} (sub-minute offsets must be rounded, §4.2/§5.8)")
        raw = c.s[start:c.i]
        minutes = (oh * 60 + om) * (1 if ch == "+" else -1)
        unknown = raw == "-00:00"
        if unknown:
            warnings.append(Issue("R9557-2.3/negative-zero-offset",
                                  "-00:00 is valid and means the same as Z (RFC 9557 §2), "
                                  "but ISO 8601:2000 forbids it; Z is preferred"))
        f.update(offset=raw, offset_minutes=minutes, offset_unknown=unknown)
        return
    raise _Fail("R3339-5.6/time-offset",
                f"time-offset must be 'Z' or ('+'/'-') hh:mm, found {ch!r}" if ch
                else "time-offset is mandatory (found end of input)")


def _parse_suffix(c, f):
    s = c.s
    tz = None
    tags = []
    while not c.at_end():
        if c.peek() != "[":
            raise _Fail("R9557-4.1/suffix-syntax",
                        f"unexpected {c.peek()!r} at offset {c.i}; only [..] suffixes may follow")
        j = s.find("]", c.i + 1)
        if j < 0:
            raise _Fail("R9557-4.1/suffix-syntax", f"unterminated '[' at offset {c.i}")
        body = s[c.i + 1:j]
        c.i = j + 1
        critical = body.startswith("!")
        if critical:
            body = body[1:]
        if "=" in body:
            key, _, val = body.partition("=")
            if not _SUFFIX_KEY.fullmatch(key):
                hint = " (keys are lowercase only, §3.1)" if _SUFFIX_KEY.fullmatch(key.lower()) else ""
                raise _Fail("R9557-4.1/suffix-key", f"invalid suffix-key {key!r}{hint}")
            if not _SUFFIX_VALUES.fullmatch(val):
                raise _Fail("R9557-4.1/suffix-value",
                            f"invalid suffix-values {val!r} (1*alphanum *(\"-\" 1*alphanum))")
            tags.append({"key": key, "value": val, "values": val.split("-"),
                         "critical": critical})
            continue
        if tz is not None or tags:
            raise _Fail("R9557-4.1/time-zone-position",
                        f"time-zone suffix [{body}] must be the first suffix and appear at most once")
        if body[:1] in ("+", "-") and body:
            m = _NUMOFFSET.fullmatch(body)
            if not m or int(m.group(2)) > 23 or int(m.group(3)) > 59:
                raise _Fail("R9557-4.1/time-zone-offset",
                            f"invalid offset time zone {body!r} (time-numoffset)")
            mins = (int(m.group(2)) * 60 + int(m.group(3))) * (1 if m.group(1) == "+" else -1)
            tz = {"kind": "offset", "name": body, "critical": critical, "offset_minutes": mins}
        else:
            parts = body.split("/")
            for p in parts:
                if not _TZ_PART.fullmatch(p) or p in (".", ".."):
                    raise _Fail("R9557-4.1/time-zone-name",
                                f"invalid time-zone-name {body!r} (part {p!r})")
            tz = {"kind": "name", "name": body, "critical": critical}
    f["time_zone"] = tz
    f["tags"] = tags


# ---------------------------------------------------------------------------
# Semantic checks
# ---------------------------------------------------------------------------
def _check_leap_second(f, mode, production, errors, warnings):
    if f.get("second") != 60:
        f["leap_second"] = False
        return
    f["leap_second"] = True
    if mode == "grammar":
        return
    h, mi = f["hour"], f["minute"]
    if production == "partial-time":
        warnings.append(Issue("R3339-5.7/leap-second-unverifiable",
                              "second=60 without date/offset cannot be checked against §5.7"))
        return
    off = f["offset_minutes"]
    local_mod = h * 60 + mi
    utc_mod = local_mod - off
    delta = -1 if utc_mod < 0 else (1 if utc_mod >= 1440 else 0)
    utc_mod %= 1440
    has_date = "year" in f
    if has_date:
        uy, um, ud = _shift_day(f["year"], f["month"], f["day"], delta)
        end_of_month = ud == days_in_month(uy, um)
        local_eom = f["day"] == days_in_month(f["year"], f["month"])
    else:
        end_of_month = local_eom = True
    if utc_mod != 1439 or not end_of_month:
        if off != 0 and local_mod == 1439 and local_eom:
            errors.append(Issue("R3339-5.7/leap-second-offset",
                                f"23:59:60 local with offset {f['offset']} is not a leap second: "
                                f"§5.7 'the leap second point is shifted by the zone offset'"))
        else:
            errors.append(Issue("R3339-5.7/leap-second-position",
                                "second=60 only at 23:59:60 UTC on the last day of a month (§5.7)"))
        return
    if mode == "any-month-end":
        return
    if not has_date:
        warnings.append(Issue("R3339-5.7/leap-second-unverifiable",
                              f"{mode} mode needs a date; positional check only"))
        return
    if mode == "table":
        if (uy, um, ud) not in LEAP_SECONDS:
            errors.append(Issue("R3339-AppD/leap-second-table",
                                f"no leap second at {uy:04d}-{um:02d}-{ud:02d}T23:59:60Z in the "
                                f"embedded table (Appendix D + IERS, cutoff {LEAP_SECONDS_CUTOFF})"))
        return
    # iers-months
    if uy < FIRST_LEAP_YEAR:
        errors.append(Issue("R3339-AppD/leap-second-pre-1972",
                            f"leap second in {uy:04d}: UTC leap seconds began in 1972 "
                            f"(Appendix D table starts 1972-06-30)"))
    elif um not in LEAP_MONTHS:
        errors.append(Issue("R3339-AppD/leap-second-month",
                            f"leap second at end of UTC month {um:02d}: Appendix D opportunities "
                            f"are end of June/December (first) and March/September (second); "
                            f"§5.7 allows 60 only in 'months in which a leap second occurs'"))


def _zone_offset_minutes(f, name):
    """Return the zone's UTC offset (timedelta) at the string's instant, or None."""
    import zoneinfo
    try:
        local = datetime(f["year"], f["month"], f["day"], f["hour"], f["minute"],
                         min(f["second"], 59),
                         tzinfo=timezone(timedelta(minutes=f["offset_minutes"])))
        utc = local.astimezone(timezone.utc)
        return utc.astimezone(zoneinfo.ZoneInfo(name)).utcoffset()
    except (OverflowError, ValueError):
        return None


def _fmt_offset_seconds(total):
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    return f"{sign}{h:02d}:{m:02d}" + (f":{sec:02d}" if sec else "")


def _offset_matches_zone(zone_s, stated_min, lmt_tolerance):
    """RFC 3339 §4.2 NOTE / §5.8: a zone offset with seconds (LMT) is written
    as a representable hh:mm.  ``nearest``: only the offset rounded to the
    nearest minute (|diff| <= 30 s, so both neighbours on a :30 tie such as
    Monrovia -00:44:30); ``any-sub-minute``: any hh:mm less than 60 s away."""
    diff = abs(zone_s - stated_min * 60)
    return diff <= 30 if lmt_tolerance == "nearest" else diff < 60


def _check_suffix(f, experimental_keys, tzdata, errors, warnings, lmt_tolerance=DEFAULT_LMT_MODE):
    tags = f["tags"]
    # §3.2 experimental keys
    for t in tags:
        if t["key"].startswith("_") and t["key"] not in experimental_keys:
            errors.append(Issue("R9557-3.2/experimental-key",
                                f"experimental key {t['key']!r}: 'MUST be rejected by "
                                f"implementations not specifically configured' for the experiment"))
    groups = {}
    for t in tags:
        groups.setdefault(t["key"], []).append(t)
    effective = {}
    for key, group in groups.items():
        effective[key] = group[0]["value"]  # §3.3: first suffix with that key wins
        any_crit = any(t["critical"] for t in group)
        if len({t["value"] for t in group}) > 1 and any_crit:
            errors.append(Issue("R9557-3.3/critical-inconsistent-duplicate",
                                f"key {key!r} repeated with different values and a critical flag"))
        elif len(group) > 1 and not any_crit:
            # §3.3: an app that "does not want to perform additional processing"
            # on duplicate elective keys "MUST choose the first".
            warnings.append(Issue("R9557-3.3/duplicate-elective-key",
                                  f"key {key!r} repeated; first value {group[0]['value']!r} used"))
        if key.startswith("_"):
            continue  # already rejected, or configured as understood
        if key not in KNOWN_SUFFIX_KEYS:
            if any_crit:
                errors.append(Issue("R9557-3.3/critical-unknown-key",
                                    f"critical suffix key {key!r} is not understood"))
            else:
                warnings.append(Issue("R9557-3.3/elective-unknown-key",
                                      f"elective suffix key {key!r} not understood; ignored"))
            continue
        if key == "u-ca":
            for t in group:
                if t["value"] in KNOWN_CALENDARS:
                    continue
                if t["critical"]:
                    errors.append(Issue("R9557-3.3/critical-unknown-value",
                                        f"critical u-ca value {t['value']!r} not a known calendar"))
                else:
                    warnings.append(Issue("R9557-3.3/elective-unknown-value",
                                          f"elective u-ca value {t['value']!r} not a known calendar"))
    f["effective_tags"] = effective

    tz = f["time_zone"]
    f["tz_checked"] = None
    if tz is None:
        return
    crit = tz["critical"]

    def inconsistent(msg):
        if crit:
            errors.append(Issue("R9557-3.4/critical-inconsistency", msg + " (critical: MUST act)"))
        else:
            warnings.append(Issue("R9557-3.4/elective-inconsistency", msg + " (elective: MAY act)"))

    if tz["kind"] == "offset":
        warnings.append(Issue("R9557-1.2/offset-time-zone",
                              "offset time zones are 'strongly discouraged' (RFC 9557 §1.2)"))
        f["tz_checked"] = True
        if not f["offset_unknown"] and tz["offset_minutes"] != f["offset_minutes"]:
            inconsistent(f"offset {f['offset']} does not repeat offset time zone [{tz['name']}]")
        return

    def unprocessable(why):
        # §3.3: critical -> "MUST NOT act on the IXDTF string unless it can
        # process the suffix tag as specified"; elective -> free to ignore.
        f["tz_checked"] = False
        if crit:
            errors.append(Issue("R9557-3.3/critical-unprocessable",
                                f"critical time zone [!{tz['name']}] cannot be processed: {why}"))
        else:
            warnings.append(Issue("R9557-3.4/time-zone-unchecked",
                                  f"elective time zone not checked: {why}"))

    zones = _zone_names() if tzdata == "auto" else None
    if zones is None:
        unprocessable("no time-zone data (tzdata off or unavailable)")
        return
    exact, lower = zones
    name = tz["name"]
    if name not in exact:
        canon = lower.get(name.lower())
        if canon is None:
            f["tz_checked"] = True
            if crit:
                errors.append(Issue("R9557-4.1/critical-unknown-time-zone",
                                    f"critical time zone {name!r} not in local tz database"))
                errors.append(Issue("R9557-3.3/critical-unprocessable",
                                    f"critical time zone [!{name}] cannot be processed: "
                                    f"unknown to the local tz database"))
            else:
                warnings.append(Issue("R9557-4.1/elective-unknown-time-zone",
                                      f"elective time zone {name!r} not in local tz database"))
            return
        warnings.append(Issue("R9557-4.1/time-zone-name-case",
                              f"time zone {name!r} matched {canon!r} case-insensitively"))
        name = canon
    tz["canonical_name"] = name
    # Resolve the zone at the instant even for Z / -00:00: a critical zone
    # must be processable (local time computable) to be acted on.
    zoff = _zone_offset_minutes(f, name)
    if zoff is None:
        unprocessable("instant outside the range supported by the tz code")
        return
    f["tz_checked"] = True
    if f["offset_unknown"]:
        return  # Z / -00:00 assert no local offset (§3.4 Figure 2): no inconsistency
    # RFC 3339 §4.2 NOTE / §5.8: sub-minute historical offsets are written as
    # the closest representable hh:mm (see _offset_matches_zone).
    total = int(zoff.total_seconds())
    if not _offset_matches_zone(total, f["offset_minutes"], lmt_tolerance):
        msg = f"offset {f['offset']} but {name} is {_fmt_offset_seconds(total)} at that instant"
        if total % 60:
            lo = total // 60
            near = [lo, lo + 1] if total % 60 == 30 else [round(total / 60)]
            msg += (" (nearest representable: "
                    + " or ".join(_fmt_offset_seconds(n * 60) for n in near)
                    + f"; lmt_tolerance={lmt_tolerance})")
        inconsistent(msg)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def check(s: str, profile: str = "rfc3339", *, allow_space_separator: bool = False,
          leap_seconds: str = DEFAULT_LEAP_MODE, tzdata: str = "auto",
          experimental_keys=(), production: str = "date-time",
          lmt_tolerance: str = DEFAULT_LMT_MODE) -> Result:
    """Validate ``s``; never raises for bad input (only for bad options)."""
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of {PROFILES}")
    if production not in PRODUCTIONS:
        raise ValueError(f"production must be one of {PRODUCTIONS}")
    if profile == "ixdtf" and production != "date-time":
        raise ValueError("IXDTF (RFC 9557 §4.1 date-time-ext) is defined only on date-time")
    if leap_seconds not in LEAP_MODES:
        raise ValueError(f"leap_seconds must be one of {LEAP_MODES}")
    if tzdata not in TZDATA_MODES:
        raise ValueError(f"tzdata must be one of {TZDATA_MODES}")
    if lmt_tolerance not in LMT_MODES:
        raise ValueError(f"lmt_tolerance must be one of {LMT_MODES}")
    experimental_keys = frozenset(experimental_keys or ())
    opts = {"allow_space_separator": allow_space_separator, "leap_seconds": leap_seconds,
            "tzdata": tzdata, "experimental_keys": sorted(experimental_keys),
            "production": production, "lmt_tolerance": lmt_tolerance}
    res = Result(input=s, profile=profile, options=opts)
    if not isinstance(s, str):
        res.ok = False
        res.errors.append(Issue("R3339-5.6/not-a-string", "input must be a str"))
        return res
    c = _Cursor(s)
    f = {}
    warnings = res.warnings
    deferred = []  # semantic errors found while parsing; reported after syntax
    try:
        if production in ("date-time", "full-date"):
            _parse_full_date(c, f, deferred)
        if production == "date-time":
            ch = c.peek()
            if ch in ("T", "t") and ch:
                if ch == "t":
                    warnings.append(Issue("R3339-5.6/lowercase-letter",
                                          "lower-case 't' is valid, but generators SHOULD use upper case"))
                c.i += 1
            elif ch == " " and allow_space_separator:
                warnings.append(Issue("R3339-5.6/space-separator",
                                      "space separator accepted by option (§5.6 NOTE; erratum 5783 "
                                      "Held for Document Update); the ABNF requires 'T'"))
                c.i += 1
            else:
                raise _Fail("R3339-5.6/date-time-separator",
                            f"expected 'T' between full-date and full-time, found {ch!r}"
                            if ch else "expected 'T' and full-time, found end of input")
            f["separator"] = ch
        if production in ("date-time", "full-time", "partial-time"):
            _parse_partial_time(c, f)
        if production in ("date-time", "full-time"):
            _parse_offset(c, f, warnings)
        if profile == "ixdtf":
            _parse_suffix(c, f)
        elif not c.at_end():
            raise _Fail("R3339-5.6/trailing-characters",
                        f"unexpected trailing text {s[c.i:]!r} at offset {c.i}")
    except _Fail as e:
        res.ok = False
        res.errors.append(Issue(e.code, e.message))
        res.fields = f or None
        return res

    errors = res.errors
    if deferred:  # syntax is valid; now the semantic date error
        errors.extend(deferred)
        res.fields = f
        res.ok = False
        return res
    if "second" in f:
        _check_leap_second(f, leap_seconds, production, errors, warnings)
    if profile == "ixdtf":
        _check_suffix(f, experimental_keys, tzdata, errors, warnings, lmt_tolerance)
    res.fields = f
    res.ok = not errors
    return res


def parse(s: str, profile: str = "rfc3339", **kw) -> dict:
    """Return parsed fields or raise ``ValueError`` carrying the first reason code."""
    r = check(s, profile, **kw)
    if not r.ok:
        raise ValueError(f"{r.errors[0].code}: {r.errors[0].message}")
    return r.fields


def is_valid(s: str, profile: str = "rfc3339", **kw) -> bool:
    return check(s, profile, **kw).ok


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------
_COMPILED = None
_SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".tox", ".mypy_cache", "target", "vendor"}


def _compiled_patterns():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = [(pid, code, exts, re.compile(rx), re.compile(ex) if ex else None, sev, msg,
                      fix, _SCAN_CONTEXT.get(pid))
                     for pid, code, exts, rx, ex, sev, msg, fix in SCAN_PATTERNS]
    return _COMPILED


DEFAULT_MAX_BYTES = 2_000_000
# Extensions that are never source text (media, fonts, archives, compiled
# objects, databases): skipped without being read, counted as "extension".
_SKIP_EXTS = frozenset(
    ".png .jpg .jpeg .gif .webp .avif .bmp .ico .icns .tif .tiff .psd .heic .svgz "
    ".woff .woff2 .ttf .otf .eot .mp3 .mp4 .m4a .m4v .wav .ogg .oga .opus .flac .webm .mov "
    ".avi .mkv .zip .gz .tgz .bz2 .xz .zst .7z .rar .tar .jar .war .ear .class .pyc .pyo "
    ".so .dylib .dll .exe .o .a .obj .lib .bin .pdf .sqlite .sqlite3 .db .wasm .keystore "
    ".p12 .der".split())


def _language_exts():
    exts = set()
    for p in SCAN_PATTERNS:
        exts.update(e for e in p[2] if e != "*")
    return frozenset(exts)


# --- iCloud / dataless files (T4-14) ------------------------------------------
# Reading a file that iCloud Drive (or another File Provider) has evicted
# blocks until the download finishes, which can take forever at 0% CPU.  Such
# files carry SF_DATALESS in st_flags (<sys/stat.h>: 0x40000000); a regular
# file with st_size > 0 but st_blocks == 0 is treated as a likely placeholder
# too (unless it is UF_COMPRESSED, whose data lives in an xattr).  ``.icloud``
# files are iCloud's own stubs for evicted files and are never read.
SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)
_UF_COMPRESSED = getattr(stat, "UF_COMPRESSED", 0x20)
NOT_LOCAL = "not-local (iCloud/dataless)"
READ_TIMEOUT = "read-timeout"
DEFAULT_FILE_TIMEOUT = 10.0


def _is_icloud_stub(path):
    return os.path.basename(path).endswith(".icloud")


def _is_dataless(path, dir_ok=False):
    """True when ``path`` is (likely) not stored locally.  Only ``stat`` is
    used, which never triggers a download.  For directories only the
    SF_DATALESS flag counts (``dir_ok``)."""
    try:
        st = os.stat(path)
    except OSError:
        return False
    flags = getattr(st, "st_flags", 0) or 0
    if flags & SF_DATALESS:
        return True
    if dir_ok or not stat.S_ISREG(st.st_mode) or flags & _UF_COMPRESSED:
        return False
    blocks = getattr(st, "st_blocks", None)
    return blocks == 0 and st.st_size > 0


class ReadTimeout(OSError):
    """A file read did not finish within the per-file budget."""


def _read_file(path, timeout=DEFAULT_FILE_TIMEOUT):
    """Return the bytes of ``path``; with ``timeout`` (seconds, > 0) the read
    runs in a daemon worker thread and :class:`ReadTimeout` is raised when it
    does not finish in time.  The blocked thread cannot be cancelled: it
    lingers (as a daemon, so it never keeps the process alive) until the OS
    read returns."""
    if not timeout:
        with open(path, "rb") as fh:
            return fh.read()
    box = {}

    def work():
        try:
            with open(path, "rb") as fh:
                box["data"] = fh.read()
        except BaseException as e:  # noqa: BLE001 - re-raised in the caller
            box["err"] = e

    t = threading.Thread(target=work, name="rfcdt-read", daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise ReadTimeout(f"read did not finish in {timeout:g}s")
    if "err" in box:
        raise box["err"]
    return box["data"]


def _walk(paths, include_dist=False, excluded=None, include_evicted=False,
          not_local_dirs=None):
    """Yield files under ``paths``.  An explicit file is always yielded, and an
    explicit directory is always walked (even one named dist or node_modules);
    only directories found *below* it are pruned by :data:`_SKIP_DIRS`.
    ``include_dist`` stops pruning ``dist`` (node_modules etc. stay pruned).
    Pruned directories are counted by name in ``excluded`` (a dict).
    Dataless (iCloud-evicted) directories below a root are not entered unless
    ``include_evicted``; their paths are appended to ``not_local_dirs``."""
    skip = _SKIP_DIRS - {"dist"} if include_dist else _SKIP_DIRS
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        if not include_evicted and _is_dataless(p, dir_ok=True):
            if not_local_dirs is not None:
                not_local_dirs.append(p)
            continue
        for root, dirs, files in os.walk(p):
            keep = []
            for d in sorted(dirs):
                if d in skip:
                    if excluded is not None:
                        excluded[d] = excluded.get(d, 0) + 1
                elif not include_evicted and _is_dataless(os.path.join(root, d), dir_ok=True):
                    if not_local_dirs is not None:
                        not_local_dirs.append(os.path.join(root, d))
                else:
                    keep.append(d)
            dirs[:] = keep
            for name in sorted(files):
                yield os.path.join(root, name)


def _iter_files(paths, include_dist=False):
    """Backward-compatible alias of :func:`_walk` without the counters."""
    return _walk(paths, include_dist)


# --- multi-line statements (T3-14) --------------------------------------------
# A physical line is joined with the lines that continue its statement: while
# ( or [ is open, after a trailing operator (+ = . && || ( [ \ &.), or when
# the next line starts with . / &. / + (method chain, concatenation).  Every
# pattern is then also tried on the joined text; a joined hit counts only when
# the match starts on the first line and ends beyond it (so a hit wholly inside
# a later line is reported there, once), and it is reported at the first line.
_JOIN_MAX_LINES = 8
_JOIN_MAX_CHARS = 4000
_STR_LIT = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`")
_TRAILING_OP = re.compile(r"(?:[+=(\[\\]|&&|\|\||&\.|(?<![.\d])\.)\s*$")
_LEADING_CONT = re.compile(r"\s*(?:&?\.(?!\.)|\+(?!\+))")
_SLASH_COMMENT_EXTS = frozenset(_JS + _JAVA + _NET + _GO + _RS + _PHP + _C + _SWIFT + _DART
                                + _APEX + _PROTO)


def _paren_depth(code):
    code = _STR_LIT.sub("''", code)
    return code.count("(") + code.count("[") - code.count(")") - code.count("]")


def _logical_line(lines, i, slash_comments):
    """Return (joined text, length of the first line's part, index of the last
    joined line), or None when line ``i`` does not continue onto the next line."""
    def clean(s):
        return _LINE_COMMENT.sub("", s).rstrip() if slash_comments else s.rstrip()

    first = clean(lines[i])
    if len(first) > _JOIN_MAX_CHARS:
        return None
    cur, depth, j = first, _paren_depth(first), i
    while j + 1 < len(lines) and j - i < _JOIN_MAX_LINES:
        nxt = lines[j + 1]
        if not (depth > 0 or _TRAILING_OP.search(cur) or _LEADING_CONT.match(nxt)):
            break
        part = clean(nxt).strip()
        # no space around a split member access (Time\n  .zone\n  .parse)
        glue = "" if part.startswith((".", "&.")) or cur.endswith(".") else " "
        cur = cur + glue + part
        depth += _paren_depth(part)
        j += 1
        if len(cur) > _JOIN_MAX_CHARS:
            break
    if j == i:
        return None
    return cur, len(first), j


def scan_text(text: str, filename: str = "<text>"):
    ext = os.path.splitext(filename)[1].lower()
    out = []
    pats = [p for p in _compiled_patterns() if "*" in p[2] or ext in p[2]]
    lines = text.splitlines()
    slash = ext in _SLASH_COMMENT_EXTS
    for idx, line in enumerate(lines):
        if "rfcdt: ignore" in line:
            continue
        joined = None  # computed lazily: (text, first-line length) or False
        for pid, code, _exts, rx, ex, sev, msg, fix, ctx in pats:
            if rx.search(line):
                if (ex and ex.search(line)) or not (ctx is None or ctx(lines, idx, text)):
                    continue
            else:
                if joined is None:
                    joined = _logical_line(lines, idx, slash) or False
                if not joined:
                    continue
                jtext, flen, last = joined
                if not any(m.start() < flen < m.end() for m in rx.finditer(jtext)):
                    continue
                if any(rx.search(lines[k]) for k in range(idx + 1, last + 1)):
                    continue  # the hit belongs to a continuation line: reported there
                if ex and ex.search(jtext):
                    continue
                if ctx is not None:
                    jl = list(lines)
                    jl[idx] = jtext
                    if not ctx(jl, idx, text):
                        continue
            out.append({"file": filename, "line": idx + 1, "id": pid, "check": code,
                        "severity": sev, "message": msg, "fix": fix,
                        "text": line.strip()[:200]})
    return out


_SKIPPED_FILES_CAP = 200


def _new_summary(max_bytes, file_timeout=DEFAULT_FILE_TIMEOUT, include_evicted=False):
    return {"files_seen": 0, "files_scanned": 0, "files_skipped": 0,
            "skipped": {"too-large": 0, "binary": 0, "extension": 0, "unreadable": 0,
                        NOT_LOCAL: 0, READ_TIMEOUT: 0},
            "excluded_dirs": {}, "not_local_dirs": [], "scanned_by_ext": {},
            "skipped_by_ext": {}, "generic_only_by_ext": {}, "skipped_files": [],
            "skipped_files_omitted": 0, "max_bytes": max_bytes,
            "file_timeout": file_timeout, "include_evicted": include_evicted}


def _ext_key(path):
    return os.path.splitext(path)[1].lower() or "(none)"


def scan_paths(paths, max_bytes=DEFAULT_MAX_BYTES, include_dist=False, summary=None,
               include_evicted=False, file_timeout=DEFAULT_FILE_TIMEOUT):
    """Scan files under ``paths``; return the list of findings.

    ``max_bytes``: files larger than this are skipped (0 or None = no limit).
    ``summary``: optional dict filled with the scan denominator (T4-3): files
    seen / scanned / skipped, skips by reason (too-large, binary, extension,
    unreadable), pruned directories by name, and per-extension counts.
    ``generic_only_by_ext`` counts scanned files whose extension has no
    language-specific patterns (only the language-neutral ones ran).

    T4-14: files that are not stored locally (iCloud-evicted / SF_DATALESS,
    or size > 0 with no allocated blocks) and ``.icloud`` stubs are skipped
    with reason ``not-local (iCloud/dataless)`` before they are opened, unless
    ``include_evicted`` (``.icloud`` stubs are always skipped).  Each read has a
    budget of ``file_timeout`` seconds (0/None = none); a read that overruns
    is skipped as ``read-timeout`` and its daemon worker thread is left behind."""
    fresh = _new_summary(max_bytes, file_timeout, include_evicted)
    s = summary if summary is not None else fresh
    for k, v in fresh.items():
        s.setdefault(k, v)
    for k, v in fresh["skipped"].items():
        s["skipped"].setdefault(k, v)
    lang = _language_exts()
    findings = []

    def skip(path, reason, size=None):
        s["files_skipped"] += 1
        s["skipped"][reason] += 1
        e = _ext_key(path)
        s["skipped_by_ext"][e] = s["skipped_by_ext"].get(e, 0) + 1
        if reason in ("too-large", "unreadable", NOT_LOCAL, READ_TIMEOUT):
            if len(s["skipped_files"]) < _SKIPPED_FILES_CAP:
                s["skipped_files"].append({"file": path, "reason": reason, "bytes": size})
            else:
                s["skipped_files_omitted"] += 1

    for path in _walk(paths, include_dist, s["excluded_dirs"], include_evicted,
                      s["not_local_dirs"]):
        s["files_seen"] += 1
        e = _ext_key(path)
        if _is_icloud_stub(path):
            skip(path, NOT_LOCAL)
            continue
        if e in _SKIP_EXTS:
            skip(path, "extension")
            continue
        if not include_evicted and _is_dataless(path):
            skip(path, NOT_LOCAL)
            continue
        try:
            size = os.path.getsize(path)
            if max_bytes and size > max_bytes:
                skip(path, "too-large", size)
                continue
            data = _read_file(path, file_timeout)
        except ReadTimeout:
            skip(path, READ_TIMEOUT)
            continue
        except OSError:
            skip(path, "unreadable")
            continue
        if b"\x00" in data[:8192]:
            skip(path, "binary", len(data))
            continue
        s["files_scanned"] += 1
        s["scanned_by_ext"][e] = s["scanned_by_ext"].get(e, 0) + 1
        if e not in lang:
            s["generic_only_by_ext"][e] = s["generic_only_by_ext"].get(e, 0) + 1
        findings.extend(scan_text(data.decode("utf-8", errors="replace"), path))
    return findings


def format_scan_summary(s, top=12):
    """Human-readable scan denominator (printed after the findings)."""
    def top_exts(d):
        items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))
        text = ", ".join(f"{k} {v}" for k, v in items[:top])
        return text + (f", … (+{len(items) - top} more)" if len(items) > top else "")

    sk = s["skipped"]
    cap = f">{s['max_bytes']} bytes" if s["max_bytes"] else "no limit"
    lines = [f"scan summary: {s['files_scanned']} file(s) scanned, {s['files_skipped']} "
             f"skipped of {s['files_seen']} seen",
             f"  skipped: too-large {sk['too-large']} ({cap}), binary {sk['binary']}, "
             f"extension {sk['extension']}, unreadable {sk['unreadable']}, "
             f"{NOT_LOCAL} {sk.get(NOT_LOCAL, 0)}, {READ_TIMEOUT} {sk.get(READ_TIMEOUT, 0)}"]
    if s.get("not_local_dirs"):
        lines.append(f"  not-local (iCloud/dataless) dirs, not entered: "
                     f"{len(s['not_local_dirs'])} (use --include-evicted to read them)")
        for d in s["not_local_dirs"][:20]:
            lines.append(f"  NOT ENTERED {NOT_LOCAL}: {d}")
    if sk.get(NOT_LOCAL) and not s.get("include_evicted"):
        lines.append("  not-local files were not opened (reading would trigger a download); "
                     "use --include-evicted to force")
    if sk.get(READ_TIMEOUT):
        lines.append(f"  read-timeout: reads over {s.get('file_timeout')}s were abandoned "
                     "(worker threads may linger until the OS read returns)")
    if s["excluded_dirs"]:
        lines.append("  excluded dirs (pruned, files not counted): " + ", ".join(
            f"{k} x{v}" for k, v in sorted(s["excluded_dirs"].items())))
    if s["scanned_by_ext"]:
        lines.append("  scanned by extension: " + top_exts(s["scanned_by_ext"]))
    if s["generic_only_by_ext"]:
        lines.append("  generic patterns only (no language rules): "
                     + top_exts(s["generic_only_by_ext"]))
    if s["skipped_by_ext"]:
        lines.append("  skipped by extension: " + top_exts(s["skipped_by_ext"]))
    for f in s["skipped_files"][:20]:
        size = f" ({f['bytes']} bytes)" if f.get("bytes") is not None else ""
        lines.append(f"  NOT SCANNED {f['reason']}: {f['file']}{size}")
    more = len(s["skipped_files"]) - 20 + s.get("skipped_files_omitted", 0)
    if more > 0:
        lines.append(f"  … {more} more not scanned (--json lists the first "
                     f"{_SKIPPED_FILES_CAP})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Environment meta data (T4-4) and self-check (T4-5)
# ---------------------------------------------------------------------------
def _tzpath():
    try:
        import zoneinfo
        return list(zoneinfo.TZPATH)
    except Exception:  # pragma: no cover
        return []


def _tz_dir_version(d):
    """tz release of a compiled zoneinfo directory: '+VERSION' or tzdata.zi."""
    for name, rx in (("+VERSION", r"\s*(\S+)"), ("tzdata.zi", r"#\s*version\s+(\S+)")):
        try:
            with open(os.path.join(d, name), encoding="utf-8") as fh:
                m = re.match(rx, fh.readline())
        except OSError:
            continue
        if m:
            return m.group(1), os.path.join(d, name)
    return None, None


def tz_info(tzpath=None):
    """Which tz database ``zoneinfo`` uses, and its release.

    zoneinfo searches ``zoneinfo.TZPATH`` first and falls back to the
    ``tzdata`` PyPI package, so the source is the first TZPATH directory that
    holds compiled zones (a ``UTC`` file), else the package."""
    dirs = _tzpath() if tzpath is None else list(tzpath)
    pkg_version = None
    try:
        import tzdata  # type: ignore
        pkg_version = getattr(tzdata, "IANA_VERSION", None)
    except Exception:
        pass
    info = {"source": None, "path": None, "version": None, "version_file": None,
            "tzdata_package": pkg_version, "tzpath": dirs}
    for d in dirs:
        if os.path.isfile(os.path.join(d, "UTC")):
            ver, vfile = _tz_dir_version(d)
            info.update(source="system", path=d, version=ver, version_file=vfile)
            return info
    if pkg_version:
        info.update(source="tzdata-package", version=pkg_version)
    return info


def _host_tz():
    import time
    local = None
    if os.path.lexists("/etc/localtime"):
        real = os.path.realpath("/etc/localtime")
        m = re.search(r"zoneinfo(?:\.default)?/(.+)$", real)
        local = m.group(1) if m else real
    return {"TZ": os.environ.get("TZ"), "tzname": list(time.tzname), "localtime": local}


def build_meta():
    """The ``meta`` block of ``check --json``, ``scan --json`` and ``selfcheck --json``."""
    import platform
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return {"tool": "rfcdt", "version": __version__,
            "python": platform.python_version(), "platform": sys.platform,
            "tz": dict(tz_info(), available=tzdata_available()), "host_tz": _host_tz(),
            "leap_seconds_cutoff": LEAP_SECONDS_CUTOFF,
            "date": now.isoformat().replace("+00:00", "Z")}


_MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
_NTP_EPOCH = datetime(1900, 1, 1)


def parse_leap_file(path):
    """Read a tzdata ``leapseconds`` file or an IERS/NTP ``leap-seconds.list``.

    Returns ``(dates, expires, negative)``: the set of (y, m, d) days that end
    with an inserted leap second, the expiry date (``datetime.date`` or None)
    and the set of days with a deleted (negative) leap second."""
    dates, negative, expires = set(), set(), None
    ntp_rows = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            m = re.match(r"#?\s*Expires\s+([0-9]{4})\s+([A-Z][a-z]{2})\s+([0-9]{1,2})\b", line)
            if m:
                expires = datetime(int(m.group(1)), _MONTHS[m.group(2)], int(m.group(3))).date()
                continue
            m = re.match(r"Leap\s+([0-9]{4})\s+([A-Z][a-z]{2})\s+([0-9]{1,2})\s+\S+\s+([+-])", line)
            if m:
                day = (int(m.group(1)), _MONTHS[m.group(2)], int(m.group(3)))
                (dates if m.group(4) == "+" else negative).add(day)
                continue
            m = re.match(r"#@\s*([0-9]+)", line)
            if m:
                expires = (_NTP_EPOCH + timedelta(seconds=int(m.group(1)))).date()
                continue
            m = re.match(r"([0-9]{9,})\s+([0-9]+)", line)
            if m:
                ntp_rows.append((int(m.group(1)), int(m.group(2))))
    # leap-seconds.list: each row is the first instant with the new TAI-UTC;
    # the leap second ended the day before.  The first row (10 s) is the start.
    for (t, off), (_t0, prev) in zip(ntp_rows[1:], ntp_rows):
        day = (_NTP_EPOCH + timedelta(seconds=t) - timedelta(days=1)).date()
        (dates if off > prev else negative).add((day.year, day.month, day.day))
    return dates, expires, negative


_LEAP_FILE_NAMES = ("leapseconds", "leap-seconds.list")
# Aliases kept in KNOWN_CALENDARS that ICU does not list (CLDR aliases).
CALENDAR_ALIASES = frozenset({"ethiopic-amete-alem", "islamicc"})


def _find_leap_file(dirs):
    for d in dirs:
        for n in _LEAP_FILE_NAMES:
            p = os.path.join(d, n)
            if os.path.isfile(p):
                return p
    return None


def _icu_calendars(node="node"):
    import subprocess
    try:
        cp = subprocess.run([node, "-e", "console.log(JSON.stringify("
                                         "Intl.supportedValuesOf('calendar')))"],
                            capture_output=True, timeout=20, text=True)
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    try:
        return set(json.loads(cp.stdout))
    except ValueError:
        return None


def _fmt_days(days):
    return ", ".join(f"{y:04d}-{m:02d}-{d:02d}" for y, m, d in sorted(days))


def selfcheck(leap_file=None, zoneinfo_dirs=None, node="node", calendars=None, today=None,
              tz_max_age_years=1):
    """Compare the embedded tables with the host (T4-5).

    Returns a list of ``{"check", "status", "detail"}`` with status OK, WARN or
    SKIP.  ``leap_file`` / ``zoneinfo_dirs`` / ``calendars`` / ``today``
    override the host lookups (tests inject tampered copies); ``node=None``
    skips the ICU query.  tz-version WARNs when the release year is more than
    ``tz_max_age_years`` before ``today``'s year."""
    today = today or datetime.now(timezone.utc).date()
    dirs = list(zoneinfo_dirs) if zoneinfo_dirs is not None else (
        _tzpath() + ["/usr/share/zoneinfo", "/usr/share/zoneinfo.default"])
    out = []

    def add(name, status, detail):
        out.append({"check": name, "status": status, "detail": detail})

    # 1. leap seconds (embedded table vs tzdata leapseconds / leap-seconds.list)
    path = leap_file or _find_leap_file(dirs)
    parsed = None
    if not path:
        add("leap-seconds", "SKIP", "no leapseconds / leap-seconds.list file found in "
            + ", ".join(dirs))
    else:
        try:
            parsed = parse_leap_file(path)
        except OSError as e:
            add("leap-seconds", "WARN", f"cannot read {path}: {e}")
    if parsed is not None:
        dates, expires, negative = parsed
        missing, extra = dates - LEAP_SECONDS, LEAP_SECONDS - dates
        base = os.path.basename(path)
        if not dates:
            add("leap-seconds", "WARN", f"{path}: no leap-second rows parsed")
        elif missing or extra or negative:
            parts = []
            if missing:
                parts.append(f"in {base} but not in LEAP_SECONDS: {_fmt_days(missing)} "
                             f"(embedded table is stale; 'table' mode rejects them)")
            if extra:
                parts.append(f"in LEAP_SECONDS but not in {base}: {_fmt_days(extra)}")
            if negative:
                parts.append(f"negative leap second(s), not modelled: {_fmt_days(negative)}")
            add("leap-seconds", "WARN", f"{path}: " + "; ".join(parts))
        else:
            add("leap-seconds", "OK", f"{len(dates)} insertions match {path} "
                f"(embedded cutoff {LEAP_SECONDS_CUTOFF})")
        if expires is None:
            add("leap-seconds-expiry", "WARN", f"{path}: no expiry date found")
        elif expires <= today:
            add("leap-seconds-expiry", "WARN",
                f"{path} EXPIRED on {expires.isoformat()}: a leap second announced since "
                f"then would be unknown; update tzdata / leap-seconds.list")
        else:
            add("leap-seconds-expiry", "OK",
                f"{path} valid until {expires.isoformat()} ({(expires - today).days} days)")

    # 2. u-ca values vs ICU (node's Intl)
    icu = set(calendars) if calendars is not None else (_icu_calendars(node) if node else None)
    if icu is None:
        add("calendars", "SKIP", "ICU calendar list unavailable (node not found or failed)")
    else:
        only_icu = sorted(icu - KNOWN_CALENDARS)
        only_known = sorted(KNOWN_CALENDARS - icu - CALENDAR_ALIASES)
        if only_icu or only_known:
            parts = []
            if only_icu:
                parts.append("ICU calendars missing from KNOWN_CALENDARS: " + ", ".join(only_icu))
            if only_known:
                parts.append("KNOWN_CALENDARS not in ICU: " + ", ".join(only_known))
            add("calendars", "WARN", "; ".join(parts))
        else:
            add("calendars", "OK", f"all {len(icu)} ICU calendars known (KNOWN_CALENDARS also "
                "keeps the aliases " + ", ".join(sorted(CALENDAR_ALIASES)) + ")")

    # 3. tz database release
    tzi = tz_info(zoneinfo_dirs) if zoneinfo_dirs is not None else tz_info()
    ver = tzi.get("version")
    m = re.match(r"([0-9]{4})([a-z]*)$", ver or "")
    where = f"{tzi.get('source')} {tzi.get('path') or ''}".strip()
    if not ver:
        add("tz-version", "WARN", f"tz source {where or 'none found'}; release unknown")
    elif not m:
        add("tz-version", "WARN", f"unrecognised tz release {ver!r} ({where})")
    elif int(m.group(1)) < today.year - tz_max_age_years:
        add("tz-version", "WARN", f"tz {ver} ({where}) is more than {tz_max_age_years} "
            f"year(s) old: recent offset and DST changes are missing")
    else:
        add("tz-version", "OK", f"tz {ver} ({where})")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _add_check_opts(p):
    p.add_argument("--profile", choices=PROFILES, default="rfc3339")
    p.add_argument("--allow-space-separator", action="store_true",
                   help="accept a single SP instead of T (§5.6 NOTE; erratum 5783)")
    p.add_argument("--leap-seconds", choices=LEAP_MODES, default=DEFAULT_LEAP_MODE,
                   help="iers-months (default): 23:59:60 UTC only at the end of Mar/Jun/"
                        "Sep/Dec from 1972 (§5.7 'months in which a leap second occurs'; "
                        "App. D preferences; leap seconds began 1972). table: only known "
                        "insertions through " + LEAP_SECONDS_CUTOFF + ". any-month-end: "
                        "§5.7 positional rule only. grammar: ABNF 00-60 only, no date rule")
    p.add_argument("--tzdata", choices=TZDATA_MODES, default="auto")
    p.add_argument("--experimental-key", action="append", default=[], metavar="KEY",
                   help="treat this _key as part of a configured experiment (§3.2)")
    p.add_argument("--production", choices=PRODUCTIONS, default="date-time",
                   help="RFC 3339 production to validate (erratum 5624); default date-time")
    p.add_argument("--lmt-tolerance", choices=LMT_MODES, default=DEFAULT_LMT_MODE,
                   help="sub-minute zone offsets (LMT, e.g. Paris +00:09:21) against the "
                        "written hh:mm: nearest (default) accepts only the offset rounded to "
                        "the nearest minute (both on a :30 tie, e.g. -00:44:30); "
                        "any-sub-minute accepts any hh:mm less than 60 s away")


def _kw(a):
    return dict(allow_space_separator=a.allow_space_separator, leap_seconds=a.leap_seconds,
                tzdata=a.tzdata, experimental_keys=a.experimental_key, production=a.production,
                lmt_tolerance=a.lmt_tolerance)


def _print_result(r, as_json):
    if as_json:
        d = r.to_dict()
        d["meta"] = build_meta()
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return
    print(("VALID" if r.ok else "INVALID") + f"  [{r.profile}]  {r.input!r}")
    for e in r.errors:
        print(f"  error   {e.code}: {e.message}")
    for w in r.warnings:
        print(f"  warning {w.code}: {w.message}")
    if r.fields:
        for k, v in r.fields.items():
            print(f"  {k:15} {json.dumps(v, ensure_ascii=False)}")


def _max_bytes(v):
    n = int(v)
    if n < 0:
        raise argparse.ArgumentTypeError("--max-bytes must be >= 0 (0 = no limit)")
    return n


def _file_timeout(v):
    try:
        n = float(v)
    except ValueError:
        raise argparse.ArgumentTypeError("--file-timeout must be a number of seconds")
    if n < 0 or n != n:
        raise argparse.ArgumentTypeError("--file-timeout must be >= 0 (0 = no limit)")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rfcdt", description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=f"rfcdt {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("check", help="validate one string")
    pc.add_argument("string", help="value to check; put '--' before it if it starts with '-'")
    _add_check_opts(pc)
    pc.add_argument("--json", action="store_true", help="JSON result with a meta block")
    pa = sub.add_parser("adapter", help="adapter protocol: read stdin, print JSON")
    _add_check_opts(pa)
    ps = sub.add_parser("scan", help="static scan of source files for risky patterns")
    ps.add_argument("paths", nargs="+")
    ps.add_argument("--json", action="store_true",
                    help='print {"meta", "summary", "findings"}')
    ps.add_argument("--include-dist", action="store_true",
                    help="also walk directories named dist (built/bundled JS, e.g. an SDK's "
                         "dist/); node_modules and the other skipped directories stay "
                         "skipped unless given as explicit paths")
    ps.add_argument("--max-bytes", type=_max_bytes, default=DEFAULT_MAX_BYTES, metavar="N",
                    help=f"skip (and report) files larger than N bytes; default "
                         f"{DEFAULT_MAX_BYTES}; 0 = no limit")
    ps.add_argument("--include-evicted", action="store_true",
                    help="read files that are not stored locally (iCloud-evicted / "
                         "dataless); this triggers downloads and can block for a long time")
    ps.add_argument("--file-timeout", type=_file_timeout, default=DEFAULT_FILE_TIMEOUT,
                    metavar="SECONDS",
                    help=f"per-file read budget; a slower read is skipped as read-timeout "
                         f"(default {DEFAULT_FILE_TIMEOUT:g}; 0 = no limit)")
    pk = sub.add_parser("selfcheck", help="compare embedded leap-second / calendar tables and "
                                          "the tz release with the host")
    pk.add_argument("--json", action="store_true")
    pk.add_argument("--leap-file", metavar="PATH",
                    help="tzdata leapseconds or leap-seconds.list to compare (default: first "
                         "found in the zoneinfo directories)")
    pk.add_argument("--zoneinfo", action="append", metavar="DIR",
                    help="zoneinfo directory to use instead of zoneinfo.TZPATH (repeatable)")
    pk.add_argument("--node", default="node", help="node binary for the ICU calendar list "
                                                   "('' = skip)")
    pk.add_argument("--calendars", metavar="LIST",
                    help="comma-separated calendar list to use instead of asking node")
    pk.add_argument("--today", metavar="YYYY-MM-DD", help="date for expiry/age checks")
    pk.add_argument("--tz-max-age-years", type=int, default=1, metavar="N",
                    help="WARN when the tz release year is more than N years old (default 1)")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        try:
            r = check(a.string, a.profile, **_kw(a))
        except ValueError as e:
            print(f"rfcdt: {e}", file=sys.stderr)
            return 2
        _print_result(r, a.json)
        return 0 if r.ok else 1
    if a.cmd == "adapter":
        data = sys.stdin.buffer.read().decode("utf-8", errors="surrogateescape")
        env_opts = json.loads(os.environ.get("RFCDT_OPTIONS") or "{}")
        profile = os.environ.get("RFCDT_PROFILE") or a.profile
        kw = _kw(a)
        kw.update(env_opts)
        try:
            r = check(data, profile, **kw)
        except ValueError as e:
            print(json.dumps({"ok": False, "skip": True, "reason": str(e)}))
            return 2
        out = {"ok": r.ok, "reasons": r.error_codes, "warnings": r.warning_codes,
               "fields": r.fields}
        print(json.dumps(out, ensure_ascii=False))
        return 0 if r.ok else 1
    if a.cmd == "selfcheck":
        try:
            today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else None
        except ValueError:
            print("rfcdt: --today must be YYYY-MM-DD", file=sys.stderr)
            return 2
        cals = [c.strip() for c in a.calendars.split(",") if c.strip()] if a.calendars else None
        res = selfcheck(leap_file=a.leap_file, zoneinfo_dirs=a.zoneinfo, node=a.node or None,
                        calendars=cals, today=today, tz_max_age_years=a.tz_max_age_years)
        status = "WARN" if any(r["status"] == "WARN" for r in res) else "OK"
        if a.json:
            print(json.dumps({"meta": build_meta(), "status": status, "checks": res},
                             indent=2, ensure_ascii=False))
        else:
            for r in res:
                print(f"{r['status']:4}  {r['check']}: {r['detail']}")
            print(f"selfcheck: {status}")
        return 1 if status == "WARN" else 0
    summary = _new_summary(a.max_bytes, a.file_timeout, a.include_evicted)
    findings = scan_paths(a.paths, max_bytes=a.max_bytes, include_dist=a.include_dist,
                          summary=summary, include_evicted=a.include_evicted,
                          file_timeout=a.file_timeout)
    if a.json:
        print(json.dumps({"meta": build_meta(), "summary": summary, "findings": findings},
                         indent=2, ensure_ascii=False))
    else:
        for x in findings:
            print(f"{x['file']}:{x['line']}: {x['id']} [{x['check']}] {x['severity']}: "
                  f"{x['message']}\n    {x['text']}\n    fix: {x['fix']}")
        print(format_scan_summary(summary))
        print(f"{len(findings)} finding(s)", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

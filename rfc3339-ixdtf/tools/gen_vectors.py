#!/usr/bin/env python3
"""Generate vectors/vectors.json (build helper; run from anywhere: python3 tools/gen_vectors.py)."""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "vectors", "vectors.json")

V = []
S56 = "RFC3339 §5.6"
S57 = "RFC3339 §5.7"
S58 = "RFC3339 §5.8"
SAPD = "RFC3339 App. D"
S43 = "RFC3339 §4.3 / RFC9557 §2"
ER = "RFC3339 errata"
X12 = "RFC9557 §1.2"
X32 = "RFC9557 §3.2"
X33 = "RFC9557 §3.3"
X34 = "RFC9557 §3.4"
X41 = "RFC9557 §4.1"
X42 = "RFC9557 §4.2"


def v(section, inp, expect, reason, notes, profile="rfc3339", fields=None, options=None,
      requires=None, interp=None, rfcdt=None, checks=None):
    """expect "either": the RFC permits both verdicts.  interp (short reason +
    section) and rfcdt (rfcdt's default verdict, "valid"/"invalid") are then
    required; reason is rfcdt's code for its own verdict.  checks: extra check
    IDs (references/check-index.md) added to those derive_checks() infers."""
    prefix = {"rfc3339": "3339", "ixdtf": "9557"}[profile]
    sec = section.split("§")[1].split()[0] if "§" in section else section.split()[-1]
    assert expect in ("valid", "invalid", "either"), expect
    assert (expect == "either") == bool(interp and rfcdt), (inp, expect)
    rec = {"id": None, "input": inp, "profile": profile, "expect": expect, "reason": reason,
           "section": section, "checks": list(checks or ()), "notes": notes}
    if interp:
        rec["interpretation"] = interp
        rec["rfcdt_default"] = rfcdt
    if fields:
        rec["fields"] = fields
    if options:
        rec["options"] = options
    if requires:
        rec["requires"] = requires
    rec["_p"] = f"{prefix}-{sec}"
    V.append(rec)


OK = "ok"
X = "ixdtf"
TZ = ["tzdata"]
E = "either"
I_ELECTIVE = ("§3.4: elective inconsistency -- the app 'MAY act on the inconsistency' "
              "(reject or resolve) or ignore the suffix (§3.3)")
I_UNKNOWN = ("§3.3: elective tags may be ignored, but apps 'MAY also perform additional "
             "processing on inconsistent or unrecognized elective suffix tags'")
I_UNKNOWN_TZ = ("§4.1: an unknown time-zone-name is treated 'as any other inconsistency'; "
                "elective -> MAY act (§3.4)")
I_DUP = ("§3.3: duplicate elective key -- the first value MUST be used only by an app that "
         "'does not want to perform additional processing'; additional processing may reject")
I_ZOFF = ("§2/§3.4: Z (= -00:00) asserts no local offset, so by the letter there is no "
          "inconsistency; but an offset time zone asserts one, and an app MAY treat the "
          "pair as inconsistent (and, if critical, MUST then act)")
I_CASE = ("§4.1: time-zone-name is 'intended to be the name of an IANA Time Zone'; the RFC "
          "does not say whether lookup is case-sensitive (IANA names are case-sensitive "
          "identifiers, most platforms look up case-insensitively)")
I_LEAP = ("§5.7: 60 only 'at the end of months in which a leap second occurs'; no leap second "
          "occurred here, but a validator without a leap-second table cannot know. App. D: "
          "Jun/Dec first, Mar/Sep second preference")
I_RESOLVE = ("§3.3/§3.4: critical -> MUST act: 'reject the data or perform some other error "
             "handling' / 'resolving the inconsistency via ... programmed behavior'. An "
             "adapter that resolves it may report {\"ok\": true, \"resolved\": true}")
RESOLVABLE = {"R9557-3.4/critical-inconsistency", "R9557-3.3/critical-inconsistent-duplicate",
              "R9557-4.1/critical-unknown-time-zone"}

# ---------------- RFC 3339 §5.8 examples ----------------
v(S58, "1985-04-12T23:20:50.52Z", "valid", OK, "§5.8 example 1",
  fields={"year": 1985, "month": 4, "day": 12, "hour": 23, "minute": 20, "second": 50,
          "secfrac": "52", "offset": "Z", "offset_unknown": True})
v(S58, "1996-12-19T16:39:57-08:00", "valid", OK, "§5.8 example 2",
  fields={"offset": "-08:00", "offset_minutes": -480, "offset_unknown": False})
v(S58, "1990-12-31T23:59:60Z", "valid", OK, "§5.8 leap second at end of 1990",
  fields={"second": 60, "leap_second": True})
v(S58, "1990-12-31T15:59:60-08:00", "valid", OK,
  "§5.8: same leap second in PST -- offset-shifted leap second point (§5.7)",
  fields={"hour": 15, "second": 60, "leap_second": True})
v(S58, "1937-01-01T12:00:27.87+00:20", "valid", OK,
  "§5.8 closest representable offset for +00:19:32.13")

# ---------------- RFC 3339 §5.6 valid ----------------
v(S56, "2024-01-01t00:00:00z", "valid", "R3339-5.6/lowercase-letter",
  "§5.6 NOTE: 't'/'z' may be lower case; generators SHOULD use upper case (warning only)",
  fields={"separator": "t", "offset": "z", "offset_unknown": True})
v(S56, "2024-01-01T00:00:00z", "valid", "R3339-5.6/lowercase-letter", "lowercase z only")
v(S56, "2024-01-01t00:00:00Z", "valid", "R3339-5.6/lowercase-letter", "lowercase t only")
v(S56, "0000-01-01T00:00:00Z", "valid", OK, "date-fullyear = 4DIGIT admits 0000",
  fields={"year": 0})
v(S56, "9999-12-31T23:59:59Z", "valid", OK, "max 4DIGIT year")
v(S56, "2024-01-01T00:00:00.000000000001Z", "valid", OK,
  "time-secfrac = \".\" 1*DIGIT: no upper bound on digits",
  fields={"secfrac": "000000000001"})
v(S56, "2024-01-01T00:00:00.0Z", "valid", OK, "single fraction digit")
v(S56, "2024-01-01T12:00:00.5Z", "valid", OK,
  "fraction without leading zero requirement in §5.6 (erratum 4110 concerns App. A only)")
v(S56, "2024-01-01T00:00:00+23:59", "valid", OK,
  "time-numoffset uses time-hour/time-minute: +23:59 is the maximum",
  fields={"offset_minutes": 1439})
v(S56, "2024-01-01T00:00:00-23:59", "valid", OK, "minimum offset")
v(S56, "2024-01-01T00:00:00+14:00", "valid", OK, "real-world max offset")
v(S56, "2024-01-01T00:00:00+05:45", "valid", OK, "45-minute offset")
v(S56, "2024-01-01T23:59:59.999999999Z", "valid", OK, "nanosecond fraction")
v(S56, "2024-01-01T12:00:00.123456789-03:30", "valid", OK, "fraction + negative half-hour offset")

# ---------------- RFC 3339 §5.6 invalid ----------------
v(S56, "2024-01-01 12:00:00Z", "invalid", "R3339-5.6/date-time-separator",
  "ABNF requires T/t; the §5.6 NOTE about a space is permissive prose (erratum 5783, Held)")
v(S56, "2024-01-01 12:00:00Z", "valid", "R3339-5.6/space-separator",
  "same input with allow_space_separator option", options={"allow_space_separator": True},
  fields={"separator": " "})
v(S56, "2024-01-01  12:00:00Z", "invalid", "R3339-5.6/time-hour",
  "only a single SP is accepted even with the option", options={"allow_space_separator": True})
v(S56, "2024-01-01_12:00:00Z", "invalid", "R3339-5.6/date-time-separator", "underscore separator")
v(S56, "2024-01-0112:00:00Z", "invalid", "R3339-5.6/date-time-separator", "separator omitted")
v(S56, "2024-01-01", "invalid", "R3339-5.6/date-time-separator",
  "full-date alone is not a date-time")
v(S56, "2024-01-01T12:00Z", "invalid", "R3339-5.6/time-second", "seconds are mandatory")
v(S56, "2024-01-01T12:00:00", "invalid", "R3339-5.6/time-offset",
  "time-offset mandatory; unqualified local time (§4.4)")
v(S56, "2024-01-01T12:00:00+0100", "invalid", "R3339-5.6/time-numoffset", "offset without colon")
v(S56, "2024-01-01T12:00:00+01", "invalid", "R3339-5.6/time-numoffset", "hour-only offset")
v(S56, "2024-01-01T12:00:00+1:00", "invalid", "R3339-5.6/time-numoffset", "1-digit offset hour")
v(S56, "2024-01-01T12:00:00+24:00", "invalid", "R3339-5.6/time-numoffset-hour",
  "offset hour uses time-hour 00-23")
v(S56, "2024-01-01T12:00:00+01:60", "invalid", "R3339-5.6/time-numoffset-minute",
  "offset minute uses time-minute 00-59")
v(S56, "2024-01-01T12:00:00−05:00", "invalid", "R3339-5.6/time-offset",
  "U+2212 MINUS SIGN is not '-'")
v(S56, "2024-01-01T12:00:00 Z", "invalid", "R3339-5.6/time-offset", "space before Z")
v(S56, "2024-01-01T12:00:00UTC", "invalid", "R3339-5.6/time-offset", "alphabetic zone (§4.2)")
v(S56, "2024-01-01T12:00:00GMT+1", "invalid", "R3339-5.6/time-offset", "alphabetic zone")
v(S56, "2024-01-01T12:00:00.Z", "invalid", "R3339-5.6/time-secfrac", "'.' needs 1*DIGIT")
v(S56, "2024-01-01T12:00:00,5Z", "invalid", "R3339-5.6/time-secfrac",
  "comma fraction is only in App. A ISO grammar")
v(S56, "2024-01-01T12:00:00.5.5Z", "invalid", "R3339-5.6/time-offset", "two fractions")
v(S56, "24-01-01T12:00:00Z", "invalid", "R3339-5.6/date-fullyear", "2-digit year (§3 Y2K)")
v(S56, "12024-01-01T12:00:00Z", "invalid", "R3339-5.6/date-separator",
  "5-digit year: 4DIGIT then '-' expected")
v(S56, "+2024-01-01T12:00:00Z", "invalid", "R3339-5.6/date-fullyear", "ISO expanded year sign")
v(S56, "-0001-01-01T00:00:00Z", "invalid", "R3339-5.6/date-fullyear", "negative year")
v(S56, "2024-1-01T12:00:00Z", "invalid", "R3339-5.6/date-month", "1-digit month")
v(S56, "2024-01-1T12:00:00Z", "invalid", "R3339-5.6/date-mday", "1-digit day")
v(S56, "2024-00-10T00:00:00Z", "invalid", "R3339-5.6/date-month", "month 00")
v(S56, "2024-13-10T00:00:00Z", "invalid", "R3339-5.6/date-month", "month 13")
v(S56, "2024-01-00T00:00:00Z", "invalid", "R3339-5.6/date-mday", "day 00")
v(S56, "2024-01-32T00:00:00Z", "invalid", "R3339-5.6/date-mday", "day 32")
v(S56, "2024-01-01T1:00:00Z", "invalid", "R3339-5.6/time-hour", "1-digit hour")
v(S56, "2024-01-01T25:00:00Z", "invalid", "R3339-5.6/time-hour", "hour 25")
v(S56, "2024-01-01T12:60:00Z", "invalid", "R3339-5.6/time-minute", "minute 60")
v(S56, "2024-01-01T12:0:00Z", "invalid", "R3339-5.6/time-minute", "1-digit minute")
v(S56, "2024-01-01T12:00:61Z", "invalid", "R3339-5.6/time-second", "second 61 (ABNF 00-60)")
v(S56, "2024-01-01T12:00:99Z", "invalid", "R3339-5.6/time-second", "second 99")
v(S56, "2024/01/01T12:00:00Z", "invalid", "R3339-5.6/date-separator", "slash date")
v(S56, "20240101T120000Z", "invalid", "R3339-5.6/date-separator", "ISO basic format")
v(S56, "2024-001T12:00:00Z", "invalid", "R3339-5.6/date-month", "ISO ordinal date ('00' month)")
v(S56, "2024-W01-1T12:00:00Z", "invalid", "R3339-5.6/date-month", "ISO week date")
v(S56, "2024-01-01T12:00:00Z\n", "invalid", "R3339-5.6/trailing-characters",
  "trailing newline (regex $ pitfall)")
v(S56, "2024-01-01T12:00:00Z ", "invalid", "R3339-5.6/trailing-characters", "trailing space")
v(S56, " 2024-01-01T12:00:00Z", "invalid", "R3339-5.6/date-fullyear", "leading space")
v(S56, "2024-01-01T12:00:00ZZ", "invalid", "R3339-5.6/trailing-characters", "double Z")
v(S56, "２０２４-01-01T12:00:00Z", "invalid", "R3339-5.6/date-fullyear",
  "fullwidth digits: DIGIT is %x30-39 only")
v(S56, "٢٠٢٤-01-01T12:00:00Z", "invalid", "R3339-5.6/date-fullyear",
  "Arabic-Indic digits (Python \\d / str.isdigit pitfall)")
v(S56, "", "invalid", "R3339-5.6/date-fullyear", "empty string")
v(S56, "2022-07-08T00:14:07Z[Europe/Paris]", "invalid", "R3339-5.6/trailing-characters",
  "IXDTF suffix is not RFC 3339 date-time (profile rfc3339)")
v(S56, "2024-01-01T12:00:00+01:00:00", "invalid", "R3339-5.6/time-numoffset",
  "offset with seconds (offset-has-seconds): time-numoffset is +hh:mm only")

# ---------------- RFC 3339 §5.7 ----------------
v(S57, "2024-01-01T24:00:00Z", "invalid", "R3339-5.7/time-hour-24",
  "§5.7 forbids hour 24 (erratum 293 changes App. A only)")
v(S57, "2023-02-29T00:00:00Z", "invalid", "R3339-5.7/date-mday", "Feb 29 in common year")
v(S57, "2024-02-29T00:00:00Z", "valid", OK, "leap year (divisible by 4)")
v(S57, "1900-02-29T00:00:00Z", "invalid", "R3339-5.7/date-mday", "century non-leap (App. C)")
v(S57, "2000-02-29T00:00:00Z", "valid", OK, "divisible by 400 (App. C)")
v(S57, "2100-02-29T00:00:00Z", "invalid", "R3339-5.7/date-mday", "2100 is not leap")
v(S57, "0000-02-29T00:00:00Z", "valid", OK, "year 0000: 0 % 400 == 0 per App. C code")
v(S57, "2024-02-30T00:00:00Z", "invalid", "R3339-5.7/date-mday", "Feb 30")
v(S57, "2023-02-28T00:00:00Z", "valid", OK, "Feb 28 common year")
for mo in ("04", "06", "09", "11"):
    v(S57, f"2024-{mo}-31T00:00:00Z", "invalid", "R3339-5.7/date-mday", f"month {mo} has 30 days")
    v(S57, f"2024-{mo}-30T00:00:00Z", "valid", OK, f"month {mo} day 30")
for mo in ("01", "03", "05", "07", "08", "10", "12"):
    v(S57, f"2024-{mo}-31T00:00:00Z", "valid", OK, f"month {mo} has 31 days")

# leap seconds (default leap_seconds=grammar)
v(S57, "2016-12-31T23:59:60Z", "valid", OK, "real leap second (IERS Bulletin C 52)",
  fields={"leap_second": True})
v(S57, "2016-12-31T23:59:60z", "valid", "R3339-5.6/lowercase-letter", "leap second, lowercase z")
v(S57, "2016-12-31T23:59:60.999Z", "valid", OK, "fraction within leap second")
v(S57, "2016-12-31T23:59:60+00:00", "valid", OK, "+00:00 leap second")
v(S57, "2016-12-31T23:59:60-00:00", "valid", "R9557-2.3/negative-zero-offset",
  "-00:00 leap second")
v(S57, "2017-01-01T00:59:60+01:00", "valid", OK,
  "§5.7: leap second point shifted by +01:00 -> next local day 00:59:60")
v(S57, "2016-12-31T18:59:60-05:00", "valid", OK, "shifted by -05:00")
v(S57, "2017-01-01T05:29:60+05:30", "valid", OK, "shifted by +05:30")
v(S57, "2016-12-31T23:59:60+01:00", "invalid", "R3339-5.7/leap-second-offset",
  "local 23:59:60 with +01:00 is 22:59:60Z: §5.7 says the point is shifted by the offset")
v(S57, "2016-12-31T23:59:60-05:00", "invalid", "R3339-5.7/leap-second-offset",
  "unshifted local 23:59:60 with -05:00")
v(S57, "2016-12-30T23:59:60Z", "invalid", "R3339-5.7/leap-second-position", "not end of month")
v(S57, "2016-12-31T23:58:60Z", "invalid", "R3339-5.7/leap-second-position", "not 23:59")
v(S57, "2016-12-31T12:00:60Z", "invalid", "R3339-5.7/leap-second-position", "midday")
v(S57, "2015-06-30T23:59:60Z", "valid", OK, "real June leap second")
v(S57, "2016-06-30T23:59:60Z", E, OK,
  "June month end, no real leap second (iers-months accepts, table rejects)",
  interp=I_LEAP, rfcdt="valid")
v(S57, "2016-03-31T23:59:60Z", E, OK,
  "March month end: App. D second-preference opportunity, no real leap second",
  interp=I_LEAP, rfcdt="valid")
v(S57, "2016-12-31T12:00:60Z", "valid", OK, "leap_seconds=grammar: ABNF-only reading",
  options={"leap_seconds": "grammar"})

# ---------------- Appendix D table mode ----------------
T = {"leap_seconds": "table"}
for d in ("1972-06-30", "1998-12-31", "2005-12-31", "2008-12-31", "2012-06-30",
          "2015-06-30", "2016-12-31"):
    v(SAPD, f"{d}T23:59:60Z", "valid", OK, "in embedded leap-second table", options=T)
v(SAPD, "1990-12-31T15:59:60-08:00", "valid", OK, "table + offset shift", options=T)
v(SAPD, "2016-06-30T23:59:60Z", "invalid", "R3339-AppD/leap-second-table",
  "no leap second at mid-2016", options=T)
v(SAPD, "1971-12-31T23:59:60Z", "invalid", "R3339-AppD/leap-second-table",
  "UTC leap seconds start 1972", options=T)
v(SAPD, "2024-12-31T23:59:60Z", "invalid", "R3339-AppD/leap-second-table",
  "after table cutoff 2016-12-31; none announced since", options=T)
v(SAPD, "2016-12-31T23:59:60+01:00", "invalid", "R3339-5.7/leap-second-offset",
  "positional rule applies before table lookup", options=T)

# ---------------- §4.3 as updated by RFC 9557 §2 ----------------
v(S43, "2024-06-01T12:00:00Z", "valid", OK, "Z: UTC known, local offset unknown (RFC 9557 §2)",
  fields={"offset_unknown": True, "offset_minutes": 0})
v(S43, "2024-06-01T12:00:00-00:00", "valid", "R9557-2.3/negative-zero-offset",
  "-00:00 same meaning as Z; not deprecated (§2.3)", fields={"offset_unknown": True})
v(S43, "2024-06-01T12:00:00+00:00", "valid", OK, "+00:00: UTC is preferred reference (§2.3)",
  fields={"offset_unknown": False})

# ---------------- Errata-shaped ----------------
v(ER, "2024-01-01T120000Z", "invalid", "R3339-5.6/time-separator",
  "erratum 1584 (Verified, App. A): mixed basic/extended is App. A only; §5.6 is extended")
v(ER, "2024-02-29", "valid", OK, "erratum 5624 (Held): full-date production used alone",
  options={"production": "full-date"})
v(ER, "2024-02-30", "invalid", "R3339-5.7/date-mday", "full-date production still applies §5.7",
  options={"production": "full-date"})
v(ER, "12:00:00Z", "valid", OK, "full-time production", options={"production": "full-time"})
v(ER, "12:00:00", "invalid", "R3339-5.6/time-offset", "full-time needs time-offset",
  options={"production": "full-time"})
v(ER, "12:00:00.5", "valid", OK, "partial-time production", options={"production": "partial-time"})
v(ER, "00:59:60+01:00", "valid", OK, "full-time leap second, shifted",
  options={"production": "full-time"})
v(ER, "23:59:60+01:00", "invalid", "R3339-5.7/leap-second-offset",
  "full-time leap second not shifted", options={"production": "full-time"})

# ---------------- RFC 9557 §4.2 examples ----------------
v(X42, "1996-12-19T16:39:57-08:00", "valid", OK, "Figure 4: suffix is optional", profile=X)
v(X42, "1996-12-19T16:39:57-08:00[America/Los_Angeles]", "valid", OK, "Figure 5", profile=X,
  fields={"time_zone": {"kind": "name", "name": "America/Los_Angeles", "critical": False}})
v(X42, "1996-12-19T16:39:57-08:00[America/Los_Angeles][u-ca=hebrew]", "valid", OK,
  "Figure 6", profile=X, fields={"effective_tags": {"u-ca": "hebrew"}})
v(X42, "1996-12-19T16:39:57-08:00[_foo=bar][_baz=bat]", "invalid",
  "R9557-3.2/experimental-key",
  "Figure 7 is only meaningful inside a configured experiment; §3.2 MUST reject otherwise",
  profile=X)
v(X42, "1996-12-19T16:39:57-08:00[_foo=bar][_baz=bat]", "valid", OK,
  "Figure 7 with both keys configured as experimental", profile=X,
  options={"experimental_keys": ["_foo", "_baz"]})

# ---------------- §1.2 ----------------
v(X12, "2022-07-08T00:14:07+08:45[+08:45]", "valid", "R9557-1.2/offset-time-zone",
  "offset time zone: allowed but strongly discouraged", profile=X)
v(X12, "2020-01-01T00:00+01:00[Europe/Paris]", "invalid", "R3339-5.6/time-second",
  "§1.2 prose example omits seconds; the imported date-time ABNF requires them", profile=X)
v(X12, "2020-01-01T00:00:00+01:00[Europe/Paris]", "valid", OK,
  "§1.2 example with seconds restored", profile=X)

# ---------------- §3.2 ----------------
v(X32, "2022-07-08T00:14:07Z[_foo=bar]", "invalid", "R9557-3.2/experimental-key",
  "elective experimental key still MUST be rejected", profile=X)
v(X32, "2022-07-08T00:14:07Z[!_foo=bar]", "invalid", "R9557-3.2/experimental-key",
  "critical experimental key", profile=X)
v(X32, "2022-07-08T00:14:07Z[_foo=bar]", "valid", OK, "configured experiment", profile=X,
  options={"experimental_keys": ["_foo"]})

# ---------------- §3.3 ----------------
v(X33, "2022-07-08T00:14:07+01:00[knort=blargel]", E, "R9557-3.3/elective-unknown-key",
  "§3.3 example: unknown elective key 'may be entirely ignored'", profile=X,
  interp=I_UNKNOWN, rfcdt="valid")
v(X33, "2022-07-08T00:14:07Z[!knort=blargel]", "invalid", "R9557-3.3/critical-unknown-key",
  "§3.3 example: critical unknown key MUST be treated as erroneous", profile=X)
v(X33, "2022-07-08T00:14:07Z[!u-ca=chinese][u-ca=japanese]", "invalid",
  "R9557-3.3/critical-inconsistent-duplicate", "§3.3 example", profile=X)
v(X33, "2022-07-08T00:14:07Z[u-ca=chinese][!u-ca=japanese]", "invalid",
  "R9557-3.3/critical-inconsistent-duplicate", "§3.3 example (critical on second)", profile=X)
v(X33, "2022-07-08T00:14:07Z[u-ca=chinese][u-ca=japanese]", E,
  "R9557-3.3/duplicate-elective-key", "§3.3 example: repeated elective key", profile=X,
  interp=I_DUP, rfcdt="valid")
v(X33, "2022-07-08T00:14:07Z[!u-ca=hebrew][!u-ca=hebrew]", "valid", OK,
  "identical critical duplicates are not inconsistent", profile=X)
v(X33, "2022-07-08T00:14:07Z[!u-ca=gregory]", "valid", OK, "critical known key/value", profile=X,
  fields={"tags": [{"key": "u-ca", "value": "gregory", "values": ["gregory"], "critical": True}]})
v(X33, "2022-07-08T00:14:07Z[u-ca=islamic-umalqura]", "valid", OK,
  "multi-item suffix-values", profile=X,
  fields={"tags": [{"key": "u-ca", "value": "islamic-umalqura",
                    "values": ["islamic", "umalqura"], "critical": False}]})
v(X33, "2022-07-08T00:14:07Z[!u-ca=klingon]", "invalid", "R9557-3.3/critical-unknown-value",
  "critical tag whose value cannot be processed", profile=X)
v(X33, "2022-07-08T00:14:07Z[u-ca=klingon]", E, "R9557-3.3/elective-unknown-value",
  "elective unknown value is ignorable", profile=X, interp=I_UNKNOWN, rfcdt="valid")
v(X33, "2022-07-08T00:14:07Z[u-ca=Hebrew]", E, "R9557-3.3/elective-unknown-value",
  "values case-sensitive (§3.1): 'Hebrew' is not 'hebrew'", profile=X,
  interp=I_UNKNOWN, rfcdt="valid")
v(X33, "2022-07-08T00:14:07Z[a-b_c9=x][u-ca=hebrew]", E, "R9557-3.3/elective-unknown-key",
  "key-char mix of lcalpha, '_', DIGIT, '-' (syntax valid; unknown elective key)", profile=X,
  interp=I_UNKNOWN, rfcdt="valid")

# ---------------- §3.4 ----------------
v(X34, "2022-07-08T00:14:07+01:00[Europe/Paris]", E, "R9557-3.4/elective-inconsistency",
  "§3.3 example: inconsistent but elective -> may treat as plain RFC 3339", profile=X,
  requires=TZ, interp=I_ELECTIVE, rfcdt="valid")
v(X34, "2022-07-08T00:14:07+01:00[!Europe/Paris]", "invalid", "R9557-3.4/critical-inconsistency",
  "§3.3 example: critical inconsistency MUST be acted on", profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07Z[Europe/Paris]", "valid", OK,
  "§3.3 note: Z asserts no local offset, so no inconsistency", profile=X, requires=TZ)
v(X34, "2022-07-08T02:14:07+02:00[Europe/Paris]", "valid", OK, "§3.3 note equivalent", profile=X,
  requires=TZ)
v(X34, "2022-07-08T00:14:07+00:00[!Europe/London]", "invalid",
  "R9557-3.4/critical-inconsistency", "Figure 1 (critical)", profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07+00:00[Europe/London]", E, "R9557-3.4/elective-inconsistency",
  "Figure 1 (elective)", profile=X, requires=TZ, interp=I_ELECTIVE, rfcdt="valid")
v(X34, "2022-07-08T00:14:07Z[!Europe/London]", "valid", OK, "Figure 2 (critical)", profile=X,
  requires=TZ)
v(X34, "2022-07-08T00:14:07Z[Europe/London]", "valid", OK, "Figure 2 (elective)", profile=X,
  requires=TZ)
v(X34, "2022-07-08T00:14:07-00:00[!Europe/London]", "valid", "R9557-2.3/negative-zero-offset",
  "§3.4: -00:00 may be used instead of Z", profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07+08:45[!+08:45]", "valid", "R9557-1.2/offset-time-zone",
  "consistent critical offset time zone", profile=X)
v(X34, "2022-07-08T00:14:07+08:45[+08:00]", E, "R9557-3.4/elective-inconsistency",
  "§1.2: offset not repeated -> inconsistent (elective)", profile=X,
  interp=I_ELECTIVE, rfcdt="valid")
v(X34, "2022-07-08T00:14:07+08:45[!+08:00]", "invalid", "R9557-3.4/critical-inconsistency",
  "critical offset time zone mismatch", profile=X)
v(X34, "2022-07-08T00:14:07Z[!+08:45]", E, "R9557-1.2/offset-time-zone",
  "Z with a critical offset time zone", profile=X, interp=I_ZOFF, rfcdt="valid")
v(X34, "2022-07-08T00:14:07-05:00[!Etc/GMT+5]", "valid", OK,
  "POSIX-style Etc/GMT+5 is UTC-5: consistent", profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07+05:00[!Etc/GMT+5]", "invalid", "R9557-3.4/critical-inconsistency",
  "sign trap: Etc/GMT+5 is -05:00", profile=X, requires=TZ)
v(X34, "2022-11-06T01:30:00-04:00[!America/New_York]", "valid", OK,
  "repeated hour, first occurrence (EDT)", profile=X, requires=TZ)
v(X34, "2022-11-06T01:30:00-05:00[!America/New_York]", "valid", OK,
  "repeated hour, second occurrence (EST)", profile=X, requires=TZ)
v(X34, "2022-03-13T02:30:00-05:00[!America/New_York]", "invalid",
  "R9557-3.4/critical-inconsistency", "instant 07:30Z is after the gap: NY is -04:00",
  profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07+05:30[!Asia/Kolkata]", "valid", OK, "consistent half-hour zone",
  profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07Z[!Mars/Olympus_Mons]", "invalid",
  "R9557-4.1/critical-unknown-time-zone",
  "§4.1: unknown tz name treated like any other inconsistency", profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07Z[Mars/Olympus_Mons]", E,
  "R9557-4.1/elective-unknown-time-zone", "elective unknown tz name", profile=X, requires=TZ,
  interp=I_UNKNOWN_TZ, rfcdt="valid")
v(X34, "2022-07-08T00:14:07Z[!europe/paris]", E, "R9557-4.1/time-zone-name-case",
  "rfcdt: case-insensitive tz lookup accepted with warning", profile=X, requires=TZ,
  interp=I_CASE, rfcdt="valid")
v(X34, "2016-12-31T23:59:60Z[!Europe/London]", "valid", OK, "leap second with tz suffix",
  profile=X, requires=TZ)
v(X34, "2017-01-01T00:59:60+01:00[!Europe/Paris]", "valid", OK,
  "shifted leap second, consistent zone", profile=X, requires=TZ)
v(X34, "2016-12-31T23:59:60+01:00[Europe/Paris]", "invalid", "R3339-5.7/leap-second-offset",
  "§5.7 still applies inside IXDTF", profile=X)

# ---------------- §4.1 grammar ----------------
v(X41, "2022-07-08t00:14:07z[Europe/Paris]", "valid", "R3339-5.6/lowercase-letter",
  "lowercase t/z in imported date-time", profile=X)
v(X41, "2022-07-08T00:14:07Z[America/Argentina/Buenos_Aires]", "valid", OK,
  "three time-zone-parts", profile=X, requires=TZ)
v(X41, "2022-07-08T00:14:07Z[Etc/GMT+5]", "valid", OK, "'+' and DIGIT in time-zone-char",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[_Custom/Zone-1.x]", E, None,
  "'_' initial, '-' and '.' chars (syntax valid); unknown elective name", profile=X,
  interp=I_UNKNOWN_TZ, rfcdt="valid")
v(X41, "2022-07-08T00:14:07Z[.hidden]", E, None,
  "'.' is a time-zone-initial; only exact '.'/'..' parts are excluded (syntax valid); "
  "unknown elective name", profile=X, interp=I_UNKNOWN_TZ, rfcdt="valid")
v(X41, "2022-07-08T00:14:07Z[+05:00]", E, "R9557-1.2/offset-time-zone",
  "offset time zone with Z", profile=X, interp=I_ZOFF, rfcdt="valid")
v(X41, "2022-07-08T00:14:07Z[-00:00]", E, "R9557-1.2/offset-time-zone",
  "time-numoffset admits -00:00 in brackets", profile=X, interp=I_ZOFF, rfcdt="valid")
v(X41, "2022-07-08T00:14:07Z[+5:00]", "invalid", "R9557-4.1/time-zone-offset",
  "1-digit offset hour in brackets", profile=X)
v(X41, "2022-07-08T00:14:07Z[+24:00]", "invalid", "R9557-4.1/time-zone-offset",
  "offset hour 24 in brackets", profile=X)
v(X41, "2022-07-08T00:14:07Z[+0500]", "invalid", "R9557-4.1/time-zone-offset",
  "no colon in bracketed offset", profile=X)
v(X41, "2022-07-08T00:14:07Z[]", "invalid", "R9557-4.1/time-zone-name", "empty brackets",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[!]", "invalid", "R9557-4.1/time-zone-name", "flag only", profile=X)
v(X41, "2022-07-08T00:14:07Z[!!Europe/Paris]", "invalid", "R9557-4.1/time-zone-name",
  "double critical flag", profile=X)
v(X41, "2022-07-08T00:14:07Z[ Europe/Paris]", "invalid", "R9557-4.1/time-zone-name",
  "space inside brackets", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe//Paris]", "invalid", "R9557-4.1/time-zone-name",
  "empty part", profile=X)
v(X41, "2022-07-08T00:14:07Z[/Europe]", "invalid", "R9557-4.1/time-zone-name",
  "leading slash", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/]", "invalid", "R9557-4.1/time-zone-name",
  "trailing slash", profile=X)
v(X41, "2022-07-08T00:14:07Z[.]", "invalid", "R9557-4.1/time-zone-name",
  "'.' part excluded", profile=X)
v(X41, "2022-07-08T00:14:07Z[..]", "invalid", "R9557-4.1/time-zone-name",
  "'..' part excluded", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/../Paris]", "invalid", "R9557-4.1/time-zone-name",
  "path traversal part", profile=X)
v(X41, "2022-07-08T00:14:07Z[1Europe/Paris]", "invalid", "R9557-4.1/time-zone-name",
  "DIGIT cannot start a part", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/París]", "invalid", "R9557-4.1/time-zone-name",
  "non-ASCII letter", profile=X)
v(X41, "2022-07-08T00:14:07Z[U-CA=hebrew]", "invalid", "R9557-4.1/suffix-key",
  "keys are lowercase only (§3.1)", profile=X)
v(X41, "2022-07-08T00:14:07Z[1a=b]", "invalid", "R9557-4.1/suffix-key", "DIGIT key-initial",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[-a=b]", "invalid", "R9557-4.1/suffix-key", "'-' key-initial",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[=b]", "invalid", "R9557-4.1/suffix-key", "empty key", profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=]", "invalid", "R9557-4.1/suffix-value", "empty value",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=hebrew-]", "invalid", "R9557-4.1/suffix-value",
  "trailing '-'", profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=-hebrew]", "invalid", "R9557-4.1/suffix-value",
  "leading '-'", profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=a--b]", "invalid", "R9557-4.1/suffix-value", "empty item",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=a_b]", "invalid", "R9557-4.1/suffix-value",
  "'_' is not alphanum", profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=héb]", "invalid", "R9557-4.1/suffix-value",
  "non-ASCII value", profile=X)
v(X41, "2022-07-08T00:14:07Z[a=b=c]", "invalid", "R9557-4.1/suffix-value",
  "second '=' inside value", profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=hebrew][Europe/Paris]", "invalid",
  "R9557-4.1/time-zone-position", "suffix = [time-zone] *suffix-tag: tz must be first",
  profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/Paris][America/New_York]", "invalid",
  "R9557-4.1/time-zone-position", "at most one time-zone", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/Paris]x", "invalid", "R9557-4.1/suffix-syntax",
  "junk after suffix", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/Paris", "invalid", "R9557-4.1/suffix-syntax",
  "unterminated bracket", profile=X)
v(X41, "2022-07-08T00:14:07Z [u-ca=hebrew]", "invalid", "R9557-4.1/suffix-syntax",
  "space before suffix", profile=X)
v(X41, "2022-07-08T00:14:07Z[u-ca=hebrew]\n", "invalid", "R9557-4.1/suffix-syntax",
  "trailing newline", profile=X)
v(X41, "2022-07-08T00:14:07[Europe/Paris]", "invalid", "R3339-5.6/time-offset",
  "IXDTF still requires the RFC 3339 offset", profile=X)
v(X41, "2022-07-08T00:14:07Z[Z]", E, None,
  "'Z' is syntactically a time-zone-name (syntax valid); unknown elective name", profile=X,
  interp=I_UNKNOWN_TZ, rfcdt="valid")

# ---------------- Review additions (appended so existing ids stay stable) ----------------
# leap seconds
v(S57, "2016-01-31T23:59:60Z", E, "R3339-AppD/leap-second-month",
  "month end outside Mar/Jun/Sep/Dec: no App. D opportunity, no real leap second",
  interp=I_LEAP, rfcdt="invalid")
v(S57, "2016-01-31T23:59:60Z", "valid", OK, "any-month-end mode: positional rule only",
  options={"leap_seconds": "any-month-end"})
v(S57, "2016-01-31T23:59:60Z", "invalid", "R3339-AppD/leap-second-table",
  "table mode: no leap second in January 2016", options={"leap_seconds": "table"})
v(S57, "1971-12-31T23:59:60Z", E, "R3339-AppD/leap-second-pre-1972",
  "pre-1972: UTC leap seconds began 1972-06-30 (App. D table)",
  interp=I_LEAP + "; UTC leap seconds began in 1972", rfcdt="invalid")
v(S57, "1971-12-31T23:59:60Z", "valid", OK, "any-month-end mode ignores the year",
  options={"leap_seconds": "any-month-end"})
v(S57, "2024-12-31T23:59:60Z", E, OK,
  "December month end after the table cutoff; no insertion announced",
  interp=I_LEAP, rfcdt="valid")
v(S57, "2016-12-30T23:59:60Z", "invalid", "R3339-5.7/leap-second-position",
  "any-month-end mode still applies the positional rule",
  options={"leap_seconds": "any-month-end"})
v(S57, "2016-12-30T23:59:60Z", "valid", OK, "grammar mode: ABNF 00-60 only",
  options={"leap_seconds": "grammar"})
v(S57, "2023-02-30Tgarbage", "invalid", "R3339-5.6/time-hour",
  "syntax error is reported before the semantic date-mday error")
v(S57, "2023-02-30T00:00:00Zjunk", "invalid", "R3339-5.6/trailing-characters",
  "syntax error is reported before the semantic date-mday error")

# control / look-alike characters and long fractions
v(S56, "2024-01-01T00:00:00Z\x00", "invalid", "R3339-5.6/trailing-characters",
  "trailing NUL (C-string truncation pitfall); cannot be passed via argv")
v(S56, "2024-01-01T00:00\x00:00Z", "invalid", "R3339-5.6/time-second", "embedded NUL")
v(S56, "2024-01-01T00:00:00Z\r", "invalid", "R3339-5.6/trailing-characters", "trailing CR")
v(S56, "2024-01-01T00:00:00Z\r\n", "invalid", "R3339-5.6/trailing-characters", "trailing CRLF")
v(S56, "﻿2024-01-01T00:00:00Z", "invalid", "R3339-5.6/date-fullyear",
  "leading BOM U+FEFF")
v(S56, "2024-01-01Ｔ00:00:00Z", "invalid", "R3339-5.6/date-time-separator",
  "fullwidth T U+FF34 (NFKC folds it to 'T')")
v(S56, "2024-01-01T00：00:00Z", "invalid", "R3339-5.6/time-separator",
  "fullwidth colon U+FF1A")
v(S56, "2024-01-01 00:00:00Z", "invalid", "R3339-5.6/date-time-separator",
  "NBSP U+00A0 is not SP")
v(S56, "2024-01-01 00:00:00Z", "invalid", "R3339-5.6/date-time-separator",
  "NBSP is not SP even with the space-separator option",
  options={"allow_space_separator": True})
v(S56, "2024-01-01T00:00:00." + "1234567890" * 105 + "Z", "valid", OK,
  "1050-digit fraction: time-secfrac = '.' 1*DIGIT has no upper bound",
  fields={"secfrac": "1234567890" * 105})
v(S56, "2024-01-01T00:00:00." + "0" * 1050 + "+01:00", "valid", OK,
  "1050-digit all-zero fraction with numeric offset")

# RFC 9557 suffixes
v(X34, "0000-01-01T00:00:00+01:00[!Europe/Paris]", "invalid", "R9557-3.3/critical-unprocessable",
  "year 0000 is outside most tz implementations' range: a critical zone that cannot be "
  "processed MUST NOT be acted on (§3.3)", profile=X)
v(X34, "2022-07-08T00:14:07+01:00[!+01:00]", "valid", "R9557-1.2/offset-time-zone",
  "critical offset time zone repeating the offset: consistent", profile=X)
v(X34, "2022-07-08T00:14:07-00:00[+01:00]", E, "R9557-1.2/offset-time-zone",
  "-00:00 (= Z) with an offset time zone", profile=X, interp=I_ZOFF, rfcdt="valid")
v(X34, "2022-07-08T00:14:07+00:00[!UTC]", "valid", OK, "+00:00 consistent with UTC zone",
  profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07+01:00[!UTC]", "invalid", "R9557-3.4/critical-inconsistency",
  "+01:00 inconsistent with UTC zone", profile=X, requires=TZ)
v(X34, "2022-07-08T00:14:07Z[!Europe/Paris]", "valid", OK,
  "critical zone known to tzdata: processable", profile=X, requires=TZ)
v(X41, "2022-07-08T00:14:07Z[u-ca]", E, "R9557-4.1/elective-unknown-time-zone",
  "'u-ca' without '=' is a time-zone-name (§4.1 note), not a suffix-tag", profile=X,
  requires=TZ, interp=I_UNKNOWN_TZ, rfcdt="valid",
  fields={"time_zone": {"kind": "name", "name": "u-ca", "critical": False}, "tags": []})
v(X41, "2022-07-08T00:14:07Z[!u-ca]", "invalid", "R9557-4.1/critical-unknown-time-zone",
  "critical time-zone-name 'u-ca' is not a known zone", profile=X, requires=TZ)
v(X41, "2022-07-08T00:14:07Z[Abcdefghijklmnopqrst/Uvwxyzabcdefghij]", E,
  "R9557-4.1/elective-unknown-time-zone",
  "time-zone-parts of 20 and 16 chars: valid syntax; §4.1 note: TZDB naming limits a part "
  "to 14 chars but the production is 'deliberately permissive' (lookup decides)",
  profile=X, requires=TZ, interp=I_UNKNOWN_TZ, rfcdt="valid")
v(X33, "2022-07-08T00:14:07Z[a=b][a=b]", E, "R9557-3.3/duplicate-elective-key",
  "identical repeated elective unknown key", profile=X, interp=I_DUP, rfcdt="valid")
v(X33, "2022-07-08T00:14:07Z[!a=b][a=b]", "invalid", "R9557-3.3/critical-unknown-key",
  "critical unknown key (duplicate values identical, so not an inconsistent duplicate)",
  profile=X)
v(X33, "2022-07-08T00:14:07Z[u-ca=chinese][u-ca=japanese]", E,
  "R9557-3.3/duplicate-elective-key",
  "IF accepted without additional processing, the first value MUST be used (§3.3): "
  "fields checked only when accepted", profile=X, interp=I_DUP, rfcdt="valid",
  fields={"effective_tags": {"u-ca": "chinese"}})
v(X32, "2022-07-08T00:14:07Z[!_foo=bar]", "valid", OK,
  "critical experimental key inside a configured experiment", profile=X,
  options={"experimental_keys": ["_foo"]})
v(X41, "2022-07-08[Europe/Paris]", "invalid", "R3339-5.6/date-time-separator",
  "date-time-ext = date-time suffix: a suffix on a bare full-date is not IXDTF", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/Paris\x00]", "invalid", "R9557-4.1/time-zone-name",
  "NUL inside brackets", profile=X)
v(X41, "2022-07-08T00:14:07Z[Europe/Paris]\r\n", "invalid", "R9557-4.1/suffix-syntax",
  "trailing CRLF after suffix", profile=X)

# ---------------- Audit-driven additions (appended so existing ids stay stable) ----------------
# Effective-field checks: years 0000-0099 must keep their value (JS Date.UTC maps 0-99 to
# 1900-1999), offsets and fractions must survive.  Runners compare these with adapter fields.
v(S56, "0050-06-01T00:00:00Z", "valid", OK,
  "year 50 must stay year 50 (Date.UTC / two-digit-year remap gives 1950)",
  fields={"year": 50, "month": 6, "day": 1, "hour": 0, "offset_minutes": 0})
v(S56, "0099-12-31T23:59:59Z", "valid", OK, "year 99 (two-digit-year remap gives 1999)",
  fields={"year": 99, "month": 12, "day": 31, "hour": 23, "minute": 59, "second": 59})
v(S56, "0001-01-01T00:00:00Z", "valid", OK, "year 1: first day of the proleptic calendar",
  fields={"year": 1, "month": 1, "day": 1})
v(S56, "0050-06-01T00:30:00+01:00", "valid", OK,
  "year 50 with an offset; the UTC instant is 0050-05-31T23:30Z",
  fields={"year": 50, "month": 6, "day": 1, "hour": 0, "minute": 30, "offset_minutes": 60})
v(S56, "2024-01-01T12:00:00-00:30", "valid", OK,
  "negative sub-hour offset: sign applies to the minutes too (-00:30 = -30, not +30)",
  fields={"offset": "-00:30", "offset_minutes": -30, "offset_unknown": False})
v(S56, "2024-01-01T12:00:00.5+05:45", "valid", OK, "fraction and +05:45 offset",
  fields={"hour": 12, "second": 0, "secfrac": "5", "offset_minutes": 345})
v(S56, "2024-01-01T12:00:00.123-03:30", "valid", OK, "millisecond fraction, -03:30 offset",
  fields={"secfrac": "123", "offset_minutes": -210})
v(S56, "2024-01-01T12:00:00.052Z", "valid", OK,
  "leading zero in fraction must be kept (.052 is not .52)",
  fields={"secfrac": "052", "second": 0})
# junk prefix and offset seconds
v(S56, "junk2024-01-01T00:00:00Z", "invalid", "R3339-5.6/date-fullyear",
  "alphabetic junk prefix (unanchored regex / exec without '^')")
v(S56, "2024-01-01T00:00:00-00:44:30", "invalid", "R3339-5.6/time-numoffset",
  "offset with seconds (LMT-style -00:44:30); sub-minute offsets must be rounded (§4.2, §5.8)")
v(X41, "junk2022-07-08T00:14:07Z[Europe/Paris]", "invalid", "R3339-5.6/date-fullyear",
  "alphabetic junk prefix before an IXDTF string", profile=X)
v(X41, "2022-07-08T00:14:07-00:44:30[Europe/Dublin]", "invalid", "R3339-5.6/time-numoffset",
  "offset with seconds is not time-numoffset in IXDTF either", profile=X)
v(X41, "2022-07-08T00:14:07+01:00[!+01:00junk]", "invalid", "R9557-4.1/time-zone-offset",
  "junk after a bracketed offset time zone", profile=X)
v(X41, "2022-07-08T00:14:07Z[+01:00:00]", "invalid", "R9557-4.1/time-zone-offset",
  "bracketed offset with seconds (time-numoffset is +hh:mm)", profile=X)
v(X41, "2022-07-08T00:14:07Z[!+01:00:00]", "invalid", "R9557-4.1/time-zone-offset",
  "critical bracketed offset with seconds", profile=X)
v(X33, "2022-07-08T00:14:07Z[u-ca=hebrew][u-ca=hebrew]", E,
  "R9557-3.3/duplicate-elective-key", "identical repeated u-ca: effective calendar hebrew",
  profile=X, interp=I_DUP, rfcdt="valid", fields={"effective_tags": {"u-ca": "hebrew"}})

# ---------------- Check-coverage additions (T2-6; appended so existing ids stay stable) --------
SAPA = "RFC3339 App. A"
S54 = "RFC3339 §5.4"
S1 = "RFC3339 §1"
X72 = "RFC9557 §7.2"
X5 = "RFC9557 §5"
I_NEGLEAP = ("§5.7: 'It is also possible for a leap second to be subtracted, at which times the "
             "maximum value of time-second is \"58\"'. None has ever been subtracted, so 23:59:59 "
             "is valid at every past month end; beyond the validity of any leap-second table a "
             "validator cannot know whether one will be, and may accept (none announced) or "
             "flag the value")
I_HARDEN = ("§3.3 grammar '*suffix-tag' has no upper bound, and repeated/unknown elective tags "
            "may be ignored or given additional processing; §7.2 parser hardening lets an "
            "implementation bound the number of tags and reject beyond it")
I_LINK = ("§4.1/§3.3: backward-compatibility link names (US/Pacific, Europe/Kiev) resolve to "
          "their canonical zone where the IANA 'backward' file is installed; builds without it "
          "(e.g. Debian's 2023 tzdata-legacy split) or tz releases before 2022b (Europe/Kyiv) "
          "do not know the name, and a critical unknown zone MUST then be rejected (§3.3/§4.1)")
I_LMT = ("RFC 3339 §4.2 NOTE / §5.8: a sub-minute historical offset (Paris LMT +00:09:21) must "
         "be 'converted to a representable time zone'; the closest is +00:09.  The RFCs do not "
         "say whether a §3.4 consistency check must require the nearest minute (+00:10 is then "
         "inconsistent) or may tolerate any written offset within a minute of the zone's")

# Appendix A ISO forms and errata 4110: fraction always follows 2DIGIT seconds
v(SAPA, "2024-01-01T12:00.5Z", "invalid", "R3339-5.6/time-second",
  "decimal fraction of a minute: allowed by the App. A ISO grammar (timespec-base "
  "[time-fraction]), never by §5.6 (seconds mandatory)", checks=["R3339-A-01"])
v(SAPA, "2024-01-01T12:00,5Z", "invalid", "R3339-5.6/time-second",
  "comma fraction of a minute (App. A time-fraction = (\",\" / \".\") 1*DIGIT)",
  checks=["R3339-A-01"])
v(SAPA, "2024-01-01T12:00:.5Z", "invalid", "R3339-5.6/time-second",
  "fraction with no seconds digits: invalid even in App. A (':' must be followed by "
  "time-second); errata 4110")
v(SAPA, "2020-01-01T00:00:0.5Z", "invalid", "R3339-5.6/time-second",
  "one zero before the fraction: errata 4110 notes the grammar 'never allowed just one zero'")
v(SAPA, "2020-01-01T00:00:05.Z", "invalid", "R3339-5.6/time-secfrac",
  "fraction point with no digits after 2DIGIT seconds (errata 4110)")
v(SAPA, "2024-01-01T12.5Z", "invalid", "R3339-5.6/time-separator",
  "decimal fraction of an hour (App. A ISO form)", checks=["R3339-A-01"])
v(SAPA, "2020-01-01T00:00:00.5Z", "valid", OK,
  "fraction after full 2-digit seconds (errata 4110 positive case)",
  fields={"second": 0, "secfrac": "5"})

# §5.7 negative leap second: max time-second 58 only when a leap second is subtracted
v(S57, "2016-12-31T23:59:58Z", "valid", OK,
  "58 is always a valid time-second (a negative leap second makes it the last second)",
  checks=["R3339-5.7-05"])
v(S57, "2016-12-31T23:59:59Z", "valid", OK,
  "no negative leap second has ever been subtracted: 59 is valid at every past month end",
  checks=["R3339-5.7-05"])
v(S57, "2016-12-31T23:59:59Z", "valid", OK,
  "table mode: 59 at a positive-leap month end is still valid (only a subtracted leap second "
  "removes it)", options={"leap_seconds": "table"}, checks=["R3339-5.7-05"])
v(S57, "2035-06-30T23:59:59Z", E, OK,
  "future month end beyond any leap-second table: a subtracted leap second cannot be ruled "
  "out (or in)", interp=I_NEGLEAP, rfcdt="valid", checks=["R3339-5.7-05"])

# §5.4 / App. B: no day of week in the format
v(S54, "Fri, 1985-04-12T23:20:50Z", "invalid", "R3339-5.6/date-fullyear",
  "§5.4: 'the day of week should not be included'; the grammar has no place for it")
v(S54, "1985-04-12T23:20:50Z Fri", "invalid", "R3339-5.6/trailing-characters",
  "trailing day of week")
v(S54, "Sat, 1985-04-12T23:20:50Z", "invalid", "R3339-5.6/date-fullyear",
  "weekday that disagrees with the date (1985-04-12 was a Friday): a lenient parser must not "
  "silently pick either field (App. B)", checks=["R3339-B-02"])

# §1: instants only; intervals, durations and repeating intervals are not date-times
v(S1, "P1D", "invalid", "R3339-5.6/date-fullyear", "ISO 8601 duration")
v(S1, "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z", "invalid", "R3339-5.6/trailing-characters",
  "ISO 8601 interval (start/end)")
v(S1, "2024-01-01T00:00:00Z/P1D", "invalid", "R3339-5.6/trailing-characters",
  "ISO 8601 interval (start/duration)")
v(S1, "R2/2024-01-01T00:00:00Z/PT1H", "invalid", "R3339-5.6/date-fullyear",
  "ISO 8601 repeating interval")

# RFC 9557 §5: u-ca is presentation only
v(X5, "2022-07-08T00:14:07+01:00[u-ca=hebrew]", "valid", OK,
  "u-ca does not change the instant or the (Gregorian) RFC 3339 fields", profile=X,
  fields={"year": 2022, "month": 7, "day": 8, "hour": 0, "minute": 14, "second": 7,
          "offset_minutes": 60, "effective_tags": {"u-ca": "hebrew"}})

# RFC 9557 §7.2 parser hardening
v(X72, "2022-07-08T00:14:07Z" + "[a=b]" * 5000, E, "R9557-3.3/duplicate-elective-key",
  "5000 repeated elective unknown tags: must be handled in bounded time (accept or reject)",
  profile=X, interp=I_HARDEN, rfcdt="valid")
v(X72, "2022-07-08T00:14:07Z[Europe/Paris]" + "[u-ca=hebrew]" * 5000, E,
  "R9557-3.3/duplicate-elective-key",
  "5000 identical u-ca tags after a zone; if accepted the first value is effective",
  profile=X, requires=TZ, interp=I_HARDEN, rfcdt="valid",
  fields={"effective_tags": {"u-ca": "hebrew"}})
v(X72, "2022-07-08T00:14:07Z" + "[a=b]" * 5000 + "[!knort=x]", "invalid",
  "R9557-3.3/critical-unknown-key",
  "critical unknown key after 5000 elective tags: a tag limit must reject, never truncate "
  "and accept", profile=X, checks=["R9557-3.3-03"])
v(X72, "2022-07-08T00:14:07Z[", "invalid", "R9557-4.1/suffix-syntax", "lone unmatched '['",
  profile=X, checks=["R9557-4.1-09"])
v(X72, "2022-07-08T00:14:07Z[u-ca=hebrew", "invalid", "R9557-4.1/suffix-syntax",
  "unterminated suffix tag", profile=X, checks=["R9557-4.1-09"])
v(X72, "2022-07-08T00:14:07Z]", "invalid", "R9557-4.1/suffix-syntax", "stray ']'", profile=X,
  checks=["R9557-4.1-09"])
v(X72, "2022-07-08T00:14:07Z" + "[" * 5000, "invalid", "R9557-4.1/suffix-syntax",
  "5000 unmatched '[' (recursive-descent / backtracking depth)", profile=X,
  checks=["R9557-4.1-09"])
v(X72, "2022-07-08T00:14:07Z" + "[" * 5000 + "]" * 5000, "invalid", "R9557-4.1/time-zone-name",
  "5000-deep nested brackets: brackets do not nest", profile=X, checks=["R9557-4.1-03"])

# Backward-link zone names (tz-dependent)
v(X34, "2022-07-08T00:14:07-07:00[!US/Pacific]", E, OK,
  "backward link to America/Los_Angeles, consistent (PDT)", profile=X, requires=TZ,
  interp=I_LINK, rfcdt="valid", checks=["R9557-4.1-06"])
v(X34, "2022-01-08T00:14:07-08:00[US/Pacific]", E, OK,
  "elective backward link, consistent (PST)", profile=X, requires=TZ,
  interp=I_LINK, rfcdt="valid", checks=["R9557-4.1-06"])
v(X34, "2022-07-08T00:14:07+01:00[!US/Pacific]", "invalid", "R9557-3.4/critical-inconsistency",
  "inconsistent with the link target, or unknown without the link: invalid either way",
  profile=X, requires=TZ, checks=["R9557-4.1-06"])
v(X34, "2022-07-08T00:14:07+03:00[!Europe/Kiev]", E, OK,
  "Europe/Kiev: canonical before tz 2022b, a backward link to Europe/Kyiv since", profile=X,
  requires=TZ, interp=I_LINK, rfcdt="valid", checks=["R9557-4.1-06"])
v(X34, "2022-07-08T00:14:07+03:00[!Europe/Kyiv]", E, OK,
  "Europe/Kyiv exists only from tz 2022b", profile=X, requires=TZ, interp=I_LINK,
  rfcdt="valid", checks=["R9557-4.1-06"])
v(X34, "2022-07-08T00:14:07+02:00[!Europe/Kiev]", "invalid", "R9557-3.4/critical-inconsistency",
  "Kyiv is +03:00 in July 2022: inconsistent if known, unknown if not -- invalid either way",
  profile=X, requires=TZ, checks=["R9557-4.1-06"])

# Historical sub-minute (LMT) offsets
v(X34, "1900-01-01T00:00:00+00:09[!Europe/Paris]", "valid", OK,
  "Paris LMT is +00:09:21; +00:09 is the nearest representable offset (§4.2 NOTE)", profile=X,
  requires=TZ, checks=["R3339-4.2-03"], fields={"offset_minutes": 9})
v(X34, "1900-01-01T00:00:00+00:10[!Europe/Paris]", E, "R9557-3.4/critical-inconsistency",
  "+00:10 is within a minute of +00:09:21 but not the nearest minute", profile=X, requires=TZ,
  interp=I_LMT, rfcdt="invalid", checks=["R3339-4.2-03"])
v(S56, "1900-01-01T00:00:00+00:09:21", "invalid", "R3339-5.6/time-numoffset",
  "unconverted LMT offset with seconds")


# ---------------- Check IDs (references/check-index.md) ----------------
CHECK_INDEX = os.path.join(ROOT, "references", "check-index.md")

# reason code -> check IDs it exercises
REASON_CHECKS = {
    "R3339-5.6/date-fullyear": ["R3339-5.6-02"],
    "R3339-5.6/date-month": ["R3339-5.6-03"],
    "R3339-5.6/date-mday": ["R3339-5.6-04"],
    "R3339-5.6/date-separator": ["R3339-5.6-19"],
    "R3339-5.6/time-separator": ["R3339-5.6-19"],
    "R3339-5.6/date-time-separator": ["R3339-5.6-11"],
    "R3339-5.6/space-separator": ["R3339-5.6-11", "R3339-5.6-15"],
    "R3339-5.6/time-hour": ["R3339-5.6-05"],
    "R3339-5.6/time-minute": ["R3339-5.6-06"],
    "R3339-5.6/time-second": ["R3339-5.6-07"],
    "R3339-5.6/time-secfrac": ["R3339-5.6-08"],
    "R3339-5.6/time-offset": ["R3339-5.6-10"],
    "R3339-5.6/time-numoffset": ["R3339-5.6-09"],
    "R3339-5.6/time-numoffset-hour": ["R3339-5.6-09"],
    "R3339-5.6/time-numoffset-minute": ["R3339-5.6-09"],
    "R3339-5.6/trailing-characters": ["R3339-5.6-16"],
    "R3339-5.6/lowercase-letter": ["R3339-5.6-12"],
    "R3339-5.7/date-mday": ["R3339-5.7-01"],
    "R3339-5.7/time-hour-24": ["R3339-5.7-08", "R3339-A-01"],
    "R3339-5.7/leap-second-offset": ["R3339-5.7-04", "R3339-D-02"],
    "R3339-5.7/leap-second-position": ["R3339-5.7-03"],
    "R3339-AppD/leap-second-table": ["R3339-D-01"],
    "R3339-AppD/leap-second-month": ["R3339-5.7-06"],
    "R3339-AppD/leap-second-pre-1972": ["R3339-D-03"],
    "R9557-2.3/negative-zero-offset": ["R3339-4.3-02", "R9557-2-03"],
    "R9557-1.2/offset-time-zone": ["R9557-1.2-02", "R9557-4.1-05"],
    "R9557-3.2/experimental-key": ["R9557-3.2-01"],
    "R9557-3.3/elective-unknown-key": ["R9557-3.3-02"],
    "R9557-3.3/elective-unknown-value": ["R9557-3.3-02", "R9557-5-01"],
    "R9557-3.3/critical-unknown-key": ["R9557-3.3-03"],
    "R9557-3.3/critical-unknown-value": ["R9557-3.3-03", "R9557-5-01"],
    "R9557-3.3/critical-unprocessable": ["R9557-3.3-03"],
    "R9557-3.3/duplicate-elective-key": ["R9557-3.3-05"],
    "R9557-3.3/critical-inconsistent-duplicate": ["R9557-3.3-06"],
    "R9557-3.4/critical-inconsistency": ["R9557-3.4-01"],
    "R9557-3.4/elective-inconsistency": ["R9557-3.4-02"],
    "R9557-4.1/time-zone-name": ["R9557-4.1-03"],
    "R9557-4.1/time-zone-name-case": ["R9557-4.1-03"],
    "R9557-4.1/time-zone-offset": ["R9557-4.1-05"],
    "R9557-4.1/time-zone-position": ["R9557-4.1-02"],
    "R9557-4.1/suffix-key": ["R9557-4.1-07"],
    "R9557-4.1/suffix-value": ["R9557-4.1-08"],
    "R9557-4.1/suffix-syntax": ["R9557-4.1-09"],
    "R9557-4.1/critical-unknown-time-zone": ["R9557-4.1-06", "R9557-3.4-01"],
    "R9557-4.1/elective-unknown-time-zone": ["R9557-4.1-06", "R9557-3.4-02"],
}
# section -> check IDs for every vector in it
SECTION_CHECKS = {
    S58: ["R3339-5.8-01"],
    SAPA: ["R3339-A-03"],
    S54: ["R3339-5.4-01"],
    S1: ["R3339-1-04"],
    X72: ["R9557-7.2-01"],
    X5: ["R9557-5-02", "R9557-5-01"],
}
_ALPHA_ZONE = ("UTC", "GMT", "−")


def derive_checks(rec):
    """Infer check IDs from a vector's reason, section, options, fields and input."""
    s, sec, reason = rec["input"], rec["section"], rec["reason"]
    fields = rec.get("fields") or {}
    opts = rec.get("options") or {}
    ixdtf = rec["profile"] == "ixdtf"
    out = set(rec["checks"])
    out.update(REASON_CHECKS.get(reason, ()))
    out.update(SECTION_CHECKS.get(sec, ()))
    head = s.split("[", 1)[0]
    # -- years, digits, whitespace and junk
    if reason == "R3339-5.6/date-fullyear":
        if s[:1] in "+-" or s[:5].isdigit():
            out.add("R3339-1-01")
        if any(ch.isdigit() and not ch.isascii() for ch in s):
            out.add("R3339-5.6-17")
        if s[:1].isspace() or s[:1] == "﻿" or s[:1].isalpha():
            out.add("R3339-5.6-16")
        if s[:2].isdigit() and s[2:3] == "-":
            out.add("R3339-3-02")
    if reason == "R3339-5.6/date-separator" and s[:5].isdigit() and s[5:6] == "-":
        out.add("R3339-1-01")
    if head[:4] in ("0000", "9999") or fields.get("year", 100) < 100:
        out.update(("R3339-1-01", "R3339-5.6-02"))
    if head.startswith("0000-0") and head[5:7] in ("01", "02"):
        out.add("R3339-B-01")  # Zeller sample breaks before 0000-03-01
    # -- ISO forms outside the §5.6 profile (App. A)
    if ("W" in head or reason == "R3339-5.6/date-month" and head[4:9] == "-001T"
            or head[:8].isdigit()):
        out.update(("R3339-5.5-01", "R3339-A-01"))
    if ",5" in head or head.endswith("+01") or "T12:00:00+0100" in head:
        out.add("R3339-A-01")
    if (reason == "R3339-5.6/time-separator" and head[11:17].isdigit()) or "+0100" in head:
        out.add("R3339-A-02")
    if any(ch in head for ch in "Ｔ： ") and not ixdtf:
        out.add("R3339-5.6-19" if "：" in head else "R3339-5.6-11")
    # -- offsets
    if reason == "R3339-5.6/time-offset" and any(z in head for z in _ALPHA_ZONE):
        out.add("R3339-4.2-01")
    if reason == "R3339-5.6/time-offset" and re.search(r":\d\d(\.\d+)?$", head):
        out.add("R3339-1-02")  # no offset at all: no stated UTC relationship
    if reason == "R3339-5.6/time-numoffset" and head.count(":") >= 4:
        out.add("R3339-4.2-03")
    if "offset_minutes" in fields:
        out.add("R3339-4.2-02")
    if rec["expect"] == "valid" and head[-6:-5] in ("+", "-") and head[-3:-2] == ":":
        out.add("R3339-5.6-09")
    if "offset_unknown" in fields:
        out.update(("R3339-2-02", "R9557-2-01"))
    if fields.get("offset") in ("Z", "z"):
        out.add("R3339-2-02")
    if head.endswith("-00:00"):
        out.update(("R3339-4.3-02", "R9557-2-03"))
    # -- fraction
    if "secfrac" in fields or ("." in head and rec["expect"] == "valid"):
        out.update(("R3339-5.3-01", "R3339-5.6-08"))
    if "secfrac" in fields:
        out.add("R3339-5.8-02")
    if "+00:20" in head:
        out.add("R3339-4.2-03")
    # -- dates and leap years
    if sec == S57 and reason in (OK, "R3339-5.7/date-mday") and head[5:10] == "02-29":
        out.update(("R3339-5.7-02", "R3339-2-01", "R3339-C-01"))
    if sec == S57 and reason == OK and head[8:10] in ("30", "31") and head[17:19] != "60":
        out.add("R3339-5.7-01")
    if head[5:10] in ("02-28", "02-30") and reason in (OK, "R3339-5.7/date-mday"):
        out.add("R3339-5.7-01")
    if reason == "R3339-5.7/date-mday" and head[5:7] == "02":
        out.update(("R3339-5.7-02", "R3339-2-01"))
    # -- leap seconds
    if re.search(r"(^|T)\d\d:\d\d:60", head):
        out.add("R3339-5.7-03")
        off = head[-6:]
        if off[:1] in "+-" and off not in ("+00:00", "-00:00"):
            out.update(("R3339-5.7-04", "R3339-D-02"))
        if opts.get("leap_seconds") == "table":
            out.add("R3339-D-01")
            if head.startswith("1972-06-30") or head.startswith("1971"):
                out.add("R3339-D-03")
        if opts.get("leap_seconds") in ("any-month-end",) or head[5:7] not in ("06", "12"):
            out.add("R3339-5.7-06")
        if rec["expect"] == "either":
            out.add("R3339-5.7-06")
    # -- sub-productions (errata 5624)
    if opts.get("production", "date-time") != "date-time":
        out.add("R3339-5.6-18")
    # -- RFC 9557
    if ixdtf:
        if "[" not in s:
            out.add("R9557-1.1-01")
        if reason.startswith("R3339-5.6/") and "[" in s:
            out.add("R9557-4.1-01")
            if reason == "R3339-5.6/time-offset":
                out.add("R9557-1.1-02")
        if reason.startswith("R3339-5.7/") or reason == "R3339-5.6/lowercase-letter":
            out.add("R9557-4.1-01")
        tz = fields.get("time_zone")
        if tz or (reason == OK and "[" in s and "=" not in s.split("]", 1)[0]):
            out.add("R9557-4.1-03")
        if "[" in s and "=" in s:
            out.update(("R9557-4.1-07", "R9557-4.1-08"))
        if "u-ca=" in s and reason in (OK, "R9557-3.3/duplicate-elective-key"):
            out.add("R9557-5-01")
        if "[!" in s:
            out.add("R9557-3.3-04")
        if reason == "R9557-4.1/time-zone-name" and "!" in s:
            out.add("R9557-3.3-04")
        if reason == "R9557-4.1/time-zone-name" and ("[]" in s or "[ " in s):
            out.add("R9557-4.1-09")
        if reason == "R9557-4.1/suffix-key" and any(c.isupper() for c in s.split("[", 1)[1]):
            out.add("R9557-3.1-01")
        if "effective_tags" in fields or "tags" in fields:
            out.add("R9557-3.3-05" if s.count("[") - s.count("[!") > 2
                    or reason == "R9557-3.3/duplicate-elective-key" else "R9557-4.1-08")
        if head.endswith(("Z", "z", "-00:00")) and "[" in s and "=" not in s.split("]", 1)[0] \
                and reason in (OK, "R9557-2.3/negative-zero-offset", "R9557-1.2/offset-time-zone"):
            out.add("R9557-3.4-03")
        if reason in ("R9557-4.1/elective-unknown-time-zone",) and "Abcdefghijklmnopqrst" in s:
            out.add("R9557-4.1-04")
        if reason == "R9557-3.4/critical-inconsistency" and "[!+" in s:
            out.add("R9557-1.2-02")
        if reason == OK and "[" in s and "=" not in s.split("]", 1)[0] and "!" in s \
                and not head.endswith("Z"):
            out.add("R9557-3.4-01")  # consistent critical zone: must be checked, not rejected
    return sorted(out)


def _known_checks():
    with open(CHECK_INDEX, encoding="utf-8") as fh:
        return set(re.findall(r"^\| (R(?:3339|9557)-[^ |]+) \|", fh.read(), re.M))


def main(argv=None):
    """Write vectors/vectors.json.  --out PATH writes elsewhere; --check writes
    nothing and exits 1 if the committed file differs from what this script
    generates."""
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    counters = Counter()
    known = _known_checks()
    for rec in V:
        p = rec.pop("_p")
        counters[p] += 1
        rec["id"] = f"{p}-{counters[p]:03d}"
        if rec["reason"] is None:
            rec["reason"] = OK
        if rec["expect"] == "invalid" and rec["reason"] in RESOLVABLE:
            rec["resolvable"] = True
            rec["interpretation"] = I_RESOLVE
        rec["checks"] = derive_checks(rec)
        unknown = set(rec["checks"]) - known
        assert rec["checks"] and not unknown, (rec["id"], rec["checks"], unknown)
    ids = [r["id"] for r in V]
    assert len(ids) == len(set(ids))
    doc = {
        "description": "Conformance vectors for RFC 3339 date-time and RFC 9557 IXDTF. "
                       "'expect' is judged with default options unless 'options' is present. "
                       "'requires': ['tzdata'] marks vectors whose outcome or reason depends on "
                       "IANA tz data. 'reason' is the rfcdt reason code (error for invalid, "
                       "warning or 'ok' for valid). 'expect': 'either' means the RFC permits "
                       "both verdicts ('interpretation' cites why; 'rfcdt_default' is rfcdt's "
                       "own verdict and 'reason' its code); runners report these in an "
                       "INTERPRETATION bucket that is never a failure. 'fields' on an either "
                       "vector apply only if the target accepts. 'resolvable': true marks "
                       "critical inconsistencies a target may resolve by programmed behaviour "
                       "(adapter output {'ok': true, 'resolved': true}).",
        "defaults": {"allow_space_separator": False, "leap_seconds": "iers-months",
                     "tzdata": "auto", "experimental_keys": [], "production": "date-time"},
        "vectors": V,
    }
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        with open(a.out, encoding="utf-8") as fh:
            same = fh.read() == text
        print(f"{a.out}: {'up to date' if same else 'DIFFERS from generator output'}")
        return 0 if same else 1
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    by = Counter(r["section"] for r in V)
    print(len(V), "vectors;", sum(r["expect"] == "either" for r in V), "either;",
          sum("tzdata" in r.get("requires", []) for r in V), "requires tzdata;",
          sum(bool(r.get("resolvable")) for r in V), "resolvable")
    for k, n in sorted(by.items()):
        print(f"  {n:3d}  {k}")


if __name__ == "__main__":
    sys.exit(main())

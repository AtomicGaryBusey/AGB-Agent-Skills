"""Markdown producer tables from producers_rfcdt.json (rfcdt verdict + semantic overrides)."""
import json
rows = json.load(open("producers_rfcdt.json"))
LMT = "WRONG VALUE (offset rounded to {r}, wall time kept: string denotes {d}, true instant {t})"
OV = {
 "chrono Local naive_local().format(\"%Y-%m-%dT%H:%M:%SZ\") [lies]": "WRONG VALUE (New York wall time labelled Z; true instant 12:00:00Z)",
 "time format(\"[year]-[month]-[day]T[hour]:[minute]:[second]Z\") [lies on +02:00]": "WRONG VALUE (+02:00 wall time labelled Z; true instant 12:00:00Z)",
 "chrono to_rfc3339() [FixedOffset -00:44:30]": LMT.format(r="-00:45", d="12:00:30Z", t="12:00:00Z"),
 "chrono to_rfc3339_opts(Secs,true) [FixedOffset -00:44:30]": LMT.format(r="-00:45", d="12:00:30Z", t="12:00:00Z"),
 "chrono serde_json [FixedOffset -00:44:30]": LMT.format(r="-00:45", d="12:00:30Z", t="12:00:00Z"),
 "chrono to_rfc3339() [FixedOffset +00:00:30]": LMT.format(r="+00:01", d="11:59:30Z", t="12:00:00Z"),
 "jiff Timestamp::display_with_offset(-00:44:30)": LMT.format(r="-00:45", d="12:00:30Z", t="12:00:00Z"),
 "jiff Zoned Display [TimeZone::fixed(-00:44:30)]": LMT.format(r="-00:45 (suffix too)", d="12:00:30Z", t="12:00:00Z"),
 "jiff Zoned Display [1970 Africa/Monrovia]": LMT.format(r="-00:45", d="1970-01-01T00:00:30Z", t="1970-01-01T00:00:00Z") + "; jiff `Zoned` re-parse recovers the instant from the zone, jiff `Timestamp` re-parse does not",
 "jiff Zoned.timestamp().display_with_offset(zoned.offset()) [1970 Monrovia]": LMT.format(r="-00:45", d="1970-01-01T00:00:30Z", t="1970-01-01T00:00:00Z"),
 "jiff Zoned Display [1850 Europe/Paris, LMT]": LMT.format(r="+00:09", d="1850-01-01T00:00:21Z", t="1850-01-01T00:00:00Z"),
 "time serde_json default Serialize (no well-known attr)": "WRONG OUTPUT (JSON array, not a string)",
 "chrono DateTime<Utc> Display (to_string)": "WRONG OUTPUT (space separator, ' UTC' suffix)",
 "chrono Display [FixedOffset -00:44:30]": "WRONG OUTPUT (space separators, offset has seconds)",
 "time OffsetDateTime Display": "WRONG OUTPUT (space separators, offset has seconds)",
 "time OffsetDateTime Display [+02:00]": "WRONG OUTPUT (space separators, offset has seconds)",
 "chrono DateTime<FixedOffset> Display": "WRONG OUTPUT (space separators)",
 "jiff Zoned Display after parsing [!Europe/Paris] (round trip)": "conforming (RFC 9557), but the `!` is dropped",
 "jiff Zoned Display after parsing [u-ca=hebrew] (round trip)": "conforming (RFC 9557), but the tag is dropped",
 "jiff Zoned Display after parsing Z[Europe/Paris] (round trip)": "conforming (RFC 9557, §3.4 Fig. 2); `Z` becomes `+02:00`",
 "jiff DateTimePrinter::new().lowercase(true).timestamp_to_string": "conforming (but SHOULD use upper case)",
 "chrono to_rfc3339_opts(Secs,true) [leap-nanos on 2026-09-24 12:00:59]": "WRONG OUTPUT (:60 outside a leap-second position, §5.7)",
 "chrono to_rfc3339_opts(Secs, true) [+02:00, use_z ignored]": "conforming (`use_z` only affects offset 0)",
}

for inp, z in (("2026-09-24T12:00:00Z","Z"),("2026-09-24T12:00:00+00:00","+00:00"),("2026-09-24T12:00:00-00:00","-00:00")):
    OV[f"chrono parse_from_rfc3339({inp}).to_rfc3339() [round trip]"] = "conforming" if z=="+00:00" else f"conforming; Advisory: `{z}` (offset unknown) rewritten to `+00:00` (rule 2)"
    OV[f"chrono serde_json DateTime<FixedOffset> from {inp} [round trip]"] = "conforming; Advisory: `+00:00` rewritten to `Z` (rule 2)" if z=="+00:00" else "conforming"
    OV[f"time parse+format(&Rfc3339) {inp} [round trip]"] = "conforming; Advisory: `+00:00` rewritten to `Z` (rule 2)" if z=="+00:00" else "conforming"
    OV[f"jiff Timestamp parse+Display {inp} [round trip]"] = "conforming; Advisory: `+00:00` rewritten to `Z` (rule 2)" if z=="+00:00" else "conforming"
OV['jiff Zoned parse("1969-12-31T23:15:30-00:45[Africa/Monrovia]").timestamp() Display'] = "consumer note: `Zoned` re-reads its own output as the true instant (offset matched after rounding the zone's -00:44:30)"
OV['jiff Timestamp parse("1969-12-31T23:15:30-00:45[Africa/Monrovia]") Display'] = "consumer note: the same string read by `Timestamp` is 30 s later than the `Zoned` reading"
ERRV = {"offset_second": "n/a (returns `Err`: refuses offset seconds; safe)", "year component": "n/a (returns `Err`: refuses year < 0; safe)"}
def verdict(r):
    if r["api"] in OV: return OV[r["api"]]
    if r["out"] is None:
        for k, v in ERRV.items():
            if k in (r["err"] or ""): return v
        return "error"
    if "[round trip]" in r["api"]:
        inp = r["api"].split(" ")[-3] if "from" in r["api"] else r["api"].split("(")[1].split(")")[0] if "parse_from_rfc3339(" in r["api"] else r["api"].split(" ")[-3]
        return "conforming" + ("" if r["ok"] else "?")
    if r["ok"]:
        if any("offset-time-zone" in w for w in r["warnings"]): return "conforming (RFC 9557); Advisory: offset time zone copied from the offset (§1.2)"
        return "conforming (RFC 9557)" if r["profile"] == "ixdtf" else "conforming"
    codes = ", ".join(e.split("/")[1] for e in r["errors"])
    return f"WRONG OUTPUT ({codes})"
def esc(s): return s.replace("|", "\\|")
for lib in ("chrono", "time", "jiff"):
    print(f"#### rust — {lib} formatters (producer side)\n\n| Call | Output | RFC verdict |\n|---|---|---|")
    for r in rows:
        if r["api"].split(" ")[0] != lib: continue
        out = f'`{esc(r["out"])}`' if r["out"] is not None else f'✗ `{esc(r["err"])}`'
        print(f'| `{esc(r["api"])}` | {out} | {verdict(r)} |')
    print()

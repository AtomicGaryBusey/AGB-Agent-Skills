//! run_vectors.py adapter for Rust date-time crates.
//! Usage: adapter list | adapter adapter <api> | adapter <api>
//!   (per-process: string on stdin, no trailing newline; RFCDT_BATCH=1: run_vectors.py JSON lines)
//!   api = chrono | chrono-fromstr | chrono-serde | time | jiff-timestamp[-both] | jiff-zoned
//!         | jiff-zoned-{reject,always-offset,always-timezone,prefer-offset} (policy in the key; no-zone rejections -> skip)
//! jiff-zoned reads JIFF_OFFSET_CONFLICT = reject (default) | always-offset | always-timezone | prefer-offset,
//! and JIFF_SKIP_NO_TZ=1 (report "missing [time-zone] annotation" rejections as skip / n/a).
//! Prints {"ok":bool,"fields":{...}} with rfcdt field names (see run_vectors.py docstring).
use chrono::{DateTime, Datelike, FixedOffset, Timelike, Utc};
use jiff::fmt::temporal::{DateTimeParser, PiecesOffset, TimeZoneAnnotationKind};
use jiff::tz::{OffsetConflict, TimeZone};
use serde_json::{json, Map, Value};
use std::io::{Read, Write};
use time::format_description::well_known::Rfc3339;

fn secfrac(n: u32) -> Option<String> {
    if n == 0 { None } else { Some(format!("{:09}", n)) }
}

fn put_frac(m: &mut Map<String, Value>, n: u32) {
    // A zero fraction is omitted (the target cannot tell ".0" from no fraction).
    if let Some(f) = secfrac(n) { m.insert("secfrac".into(), json!(f)); }
}

fn chrono_fields(d: &DateTime<FixedOffset>) -> Value {
    let n = d.nanosecond();
    let leap = n >= 1_000_000_000;
    let mut m = Map::new();
    m.insert("year".into(), json!(d.year()));
    m.insert("month".into(), json!(d.month()));
    m.insert("day".into(), json!(d.day()));
    m.insert("hour".into(), json!(d.hour()));
    m.insert("minute".into(), json!(d.minute()));
    m.insert("second".into(), json!(if leap { 60 } else { d.second() }));
    m.insert("leap_second".into(), json!(leap));
    put_frac(&mut m, n % 1_000_000_000);
    m.insert("offset_minutes".into(), json!(d.offset().local_minus_utc() / 60));
    Value::Object(m)
}

fn time_fields(d: &time::OffsetDateTime) -> Value {
    let mut m = Map::new();
    m.insert("year".into(), json!(d.year()));
    m.insert("month".into(), json!(d.month() as u8));
    m.insert("day".into(), json!(d.day()));
    m.insert("hour".into(), json!(d.hour()));
    m.insert("minute".into(), json!(d.minute()));
    m.insert("second".into(), json!(d.second()));
    m.insert("leap_second".into(), json!(false));
    put_frac(&mut m, d.nanosecond());
    m.insert("offset_minutes".into(), json!(d.offset().whole_seconds() / 60));
    Value::Object(m)
}

/// Fields for jiff: the instant comes from the target's Timestamp/Zoned; the as-written
/// offset, Z-ness and the zone annotation come from jiff's own parse (DateTimeParser::parse_pieces),
/// because Timestamp keeps no offset and Zoned keeps neither Z-ness nor the `!` flag.
fn jiff_fields(ts: &jiff::Timestamp, s: &str) -> (Value, Option<i32>) {
    let mut m = Map::new();
    let mut off_secs = None;
    if let Ok(p) = DateTimeParser::new().parse_pieces(s) {
        match p.offset() {
            Some(PiecesOffset::Zulu) => {
                off_secs = Some(0);
                m.insert("offset_unknown".into(), json!(true));
            }
            Some(PiecesOffset::Numeric(n)) => {
                let secs = n.offset().seconds();
                off_secs = Some(secs);
                m.insert("offset_unknown".into(), json!(secs == 0 && n.is_negative()));
            }
            _ => {}
        }
        if let Some(a) = p.time_zone_annotation() {
            let tz = match a.kind() {
                TimeZoneAnnotationKind::Named(n) => json!({"kind":"name","name":n.as_str(),"critical":a.is_critical()}),
                TimeZoneAnnotationKind::Offset(o) => json!({"kind":"offset","critical":a.is_critical(),"offset_minutes":o.seconds()/60}),
                #[allow(unreachable_patterns)]
                _ => json!({"critical":a.is_critical()}),
            };
            m.insert("time_zone".into(), tz);
        }
    }
    if let Some(secs) = off_secs {
        if let Ok(o) = jiff::tz::Offset::from_seconds(secs) {
            let dt = ts.to_zoned(TimeZone::fixed(o)).datetime();
            m.insert("year".into(), json!(dt.year()));
            m.insert("month".into(), json!(dt.month()));
            m.insert("day".into(), json!(dt.day()));
            m.insert("hour".into(), json!(dt.hour()));
            m.insert("minute".into(), json!(dt.minute()));
            m.insert("second".into(), json!(dt.second()));
            m.insert("leap_second".into(), json!(false));
            put_frac(&mut m, dt.subsec_nanosecond() as u32);
            m.insert("offset_minutes".into(), json!(secs / 60));
        }
    }
    (Value::Object(m), off_secs)
}

/// One run_vectors.py answer for `api` on `s`.
fn answer(api: &str, s: &str) -> Value {
    // Distinct keys for the jiff Zoned offset-conflict policies (no env needed); a
    // "missing [time-zone] annotation" rejection is reported as skip (n/a) for them.
    let (api, zoned_policy, zoned_skip) = match api {
        "jiff-zoned-reject" => ("jiff-zoned", Some("reject"), true),
        "jiff-zoned-always-offset" => ("jiff-zoned", Some("always-offset"), true),
        "jiff-zoned-always-timezone" => ("jiff-zoned", Some("always-timezone"), true),
        "jiff-zoned-prefer-offset" => ("jiff-zoned", Some("prefer-offset"), true),
        "jiff-timestamp-both" => ("jiff-timestamp", None, false),
        a => (a, None, std::env::var("JIFF_SKIP_NO_TZ").as_deref() == Ok("1")),
    };
    match api {
        "chrono" => match DateTime::parse_from_rfc3339(s) {
            Ok(d) => json!({"ok": true, "fields": chrono_fields(&d)}),
            Err(e) => json!({"ok": false, "error": e.to_string()}),
        },
        "chrono-fromstr" => match s.parse::<DateTime<FixedOffset>>() {
            Ok(d) => json!({"ok": true, "fields": chrono_fields(&d)}),
            Err(e) => json!({"ok": false, "error": e.to_string()}),
        },
        "chrono-serde" => match serde_json::from_str::<DateTime<Utc>>(&serde_json::to_string(s).unwrap()) {
            // DateTime<Utc> keeps no offset: report UTC fields only when they equal the written ones is
            // impossible to know, so report just the leap flag and fraction.
            Ok(d) => {
                let n = d.nanosecond();
                let mut m = Map::new();
                m.insert("leap_second".into(), json!(n >= 1_000_000_000));
                put_frac(&mut m, n % 1_000_000_000);
                json!({"ok": true, "fields": Value::Object(m), "utc": d.to_rfc3339()})
            }
            Err(e) => json!({"ok": false, "error": e.to_string()}),
        },
        "time" => match time::OffsetDateTime::parse(s, &Rfc3339) {
            Ok(d) => json!({"ok": true, "fields": time_fields(&d)}),
            Err(e) => json!({"ok": false, "error": e.to_string()}),
        },
        "jiff-timestamp" => match s.parse::<jiff::Timestamp>() {
            Ok(ts) => {
                let (f, _) = jiff_fields(&ts, s);
                json!({"ok": true, "fields": f, "utc": ts.to_string()})
            }
            Err(e) => json!({"ok": false, "error": e.to_string()}),
        },
        "jiff-zoned" => {
            let env_policy = std::env::var("JIFF_OFFSET_CONFLICT").ok();
            let oc = match zoned_policy.or(env_policy.as_deref()).ok_or(()) {
                Ok("always-offset") => OffsetConflict::AlwaysOffset,
                Ok("always-timezone") => OffsetConflict::AlwaysTimeZone,
                Ok("prefer-offset") => OffsetConflict::PreferOffset,
                _ => OffsetConflict::Reject,
            };
            match DateTimeParser::new().offset_conflict(oc).parse_zoned(s) {
                Ok(z) => {
                    let (mut f, off) = jiff_fields(&z.timestamp(), s);
                    // Offset that jiff actually used vs. the one written: a difference on a
                    // non-Z input means jiff resolved an inconsistency (programmed behaviour).
                    let used = z.offset().seconds();
                    let resolved = matches!(off, Some(w) if w != used)
                        && !matches!(f.get("offset_unknown"), Some(Value::Bool(true)));
                    if let Some(name) = z.time_zone().iana_name() {
                        f.as_object_mut().unwrap().insert("resolved_zone".into(), json!(name));
                    }
                    let mut o = json!({"ok": true, "fields": f, "zoned": z.to_string()});
                    if resolved { o["resolved"] = json!(true); }
                    o
                }
                // Zoned requires a [time-zone] annotation by design. With JIFF_SKIP_NO_TZ=1 such
                // rejections are reported as n/a (skip), like Temporal.ZonedDateTime in ecosystem.md.
                Err(e) if zoned_skip
                    && e.to_string().contains("failed to find time zone annotation") =>
                {
                    json!({"skip": true, "reason": format!("n/a (Zoned requires [time-zone]): {e}")})
                }
                Err(e) => json!({"ok": false, "error": e.to_string()}),
            }
        }
        _ => json!({"ok": false, "error": format!("unknown api {api:?}")}),
    }
}

/// Adapter keys and their run_vectors.py --target-kind.
const KEYS: &[(&str, &str)] = &[
    ("chrono", "rfc3339"),
    ("chrono-fromstr", "rfc3339"),
    ("chrono-serde", "rfc3339"),
    ("time", "rfc3339"),
    ("jiff-timestamp", "rfc3339"),
    ("jiff-timestamp-both", "both"),
    ("jiff-zoned-reject", "ixdtf"),
    ("jiff-zoned-always-offset", "ixdtf"),
    ("jiff-zoned-always-timezone", "ixdtf"),
    ("jiff-zoned-prefer-offset", "ixdtf"),
];

fn main() {
    let args: Vec<String> = std::env::args().collect();
    // `adapter list` | `adapter adapter <key>` (run_vector_probes.py) | `adapter <key>` (old form)
    let api = match args.get(1).map(String::as_str) {
        Some("list") => {
            for (k, kind) in KEYS { println!("{k}\t{kind}"); }
            return;
        }
        Some("adapter") => args.get(2).cloned().unwrap_or_default(),
        Some(a) => a.to_string(),
        None => String::new(),
    };
    let mut buf = Vec::new();
    std::io::stdin().read_to_end(&mut buf).unwrap();
    if std::env::var("RFCDT_BATCH").as_deref() == Ok("1") {
        let text = String::from_utf8_lossy(&buf);
        let mut out = std::io::stdout().lock();
        for line in text.split('\n') {
            if line.trim().is_empty() { continue; }
            let req: Value = match serde_json::from_str(line) {
                Ok(v) => v,
                Err(e) => { writeln!(out, "{}", json!({"ok": false, "error": format!("bad batch line: {e}")})).unwrap(); continue; }
            };
            let mut r = answer(&api, req["input"].as_str().unwrap_or(""));
            r["id"] = req["id"].clone();
            writeln!(out, "{}", r).unwrap();
        }
        out.flush().unwrap();
        return;
    }
    let out = match String::from_utf8(buf) {
        Ok(s) => answer(&api, &s),
        Err(_) => json!({"ok": false, "error": "not UTF-8"}),
    };
    println!("{}", out);
}

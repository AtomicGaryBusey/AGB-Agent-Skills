//! RFC 3339 / RFC 9557 probe for Rust date-time crates.
//! Usage: TZ=America/New_York probe <inputs.json> > results/rust.jsonl
//! Output lines follow probes/analyze.py: {lang, kind, api, id, input, ok, out, utc, err, mode}.
use chrono::{DateTime, FixedOffset, Local, NaiveDate, NaiveDateTime, SecondsFormat, TimeZone, Utc};
use jiff::fmt::temporal::{DateTimeParser, DateTimePrinter};
use jiff::tz::{self, OffsetConflict};
use rfc_eval::*;
use serde_json::{json, Value};
use time::format_description::well_known::{Iso8601, Rfc3339};

fn emit(v: Value) {
    println!("{}", v);
}

type ParseFn = Box<dyn Fn(&str) -> Result<(String, String), String>>;

fn chrono_ok(d: DateTime<FixedOffset>) -> Result<(String, String), String> {
    Ok((format!("{:?}", d), chrono_utc(&d)))
}

#[derive(serde::Deserialize)]
struct TimeRfc(#[serde(with = "time::serde::rfc3339")] time::OffsetDateTime);

fn parsers() -> Vec<(&'static str, &'static str, ParseFn)> {
    let mut v: Vec<(&'static str, &'static str, ParseFn)> = vec![];
    // ---------------- chrono ----------------
    v.push(("chrono DateTime::parse_from_rfc3339", "3339", Box::new(|s| {
        DateTime::parse_from_rfc3339(s).map_err(|e| e.to_string()).and_then(chrono_ok)
    })));
    v.push(("chrono DateTime::<FixedOffset>::from_str", "3339", Box::new(|s| {
        s.parse::<DateTime<FixedOffset>>().map_err(|e| e.to_string()).and_then(chrono_ok)
    })));
    v.push(("chrono DateTime::<Utc>::from_str", "3339", Box::new(|s| {
        s.parse::<DateTime<Utc>>().map_err(|e| e.to_string()).and_then(|d| chrono_ok(d.fixed_offset()))
    })));
    v.push(("chrono serde_json::from_str::<DateTime<Utc>>", "3339", Box::new(|s| {
        serde_json::from_str::<DateTime<Utc>>(&json_str(s)).map_err(|e| e.to_string()).and_then(|d| chrono_ok(d.fixed_offset()))
    })));
    v.push(("chrono serde_json::from_str::<DateTime<FixedOffset>>", "3339", Box::new(|s| {
        serde_json::from_str::<DateTime<FixedOffset>>(&json_str(s)).map_err(|e| e.to_string()).and_then(chrono_ok)
    })));
    v.push(("chrono DateTime::parse_from_str(s, \"%Y-%m-%dT%H:%M:%S%.f%:z\")", "3339", Box::new(|s| {
        DateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f%:z").map_err(|e| e.to_string()).and_then(chrono_ok)
    })));
    v.push(("chrono DateTime::parse_from_str(s, \"%+\")", "3339", Box::new(|s| {
        DateTime::parse_from_str(s, "%+").map_err(|e| e.to_string()).and_then(chrono_ok)
    })));
    v.push(("chrono NaiveDateTime::parse_from_str(s, \"%Y-%m-%dT%H:%M:%SZ\")", "3339", Box::new(|s| {
        NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%SZ")
            .map(|n| (format!("{:?}", n), format!("naive:{}", n.format("%Y-%m-%dT%H:%M:%S%.9f"))))
            .map_err(|e| e.to_string())
    })));
    // ---------------- time ----------------
    v.push(("time OffsetDateTime::parse(s, &Rfc3339)", "3339", Box::new(|s| {
        time::OffsetDateTime::parse(s, &Rfc3339).map(|d| (format!("{:?}", d), time_utc(&d))).map_err(|e| e.to_string())
    })));
    v.push(("time serde_json (time::serde::rfc3339)", "3339", Box::new(|s| {
        serde_json::from_str::<TimeRfc>(&json_str(s)).map(|TimeRfc(d)| (format!("{:?}", d), time_utc(&d))).map_err(|e| e.to_string())
    })));
    v.push(("time OffsetDateTime::parse(s, &Iso8601::DEFAULT)", "3339", Box::new(|s| {
        time::OffsetDateTime::parse(s, &Iso8601::DEFAULT).map(|d| (format!("{:?}", d), time_utc(&d))).map_err(|e| e.to_string())
    })));
    // ---------------- jiff ----------------
    v.push(("jiff Timestamp::from_str", "ixdtf", Box::new(|s| {
        s.parse::<jiff::Timestamp>().map(|t| (t.to_string(), jiff_utc(&t))).map_err(|e| e.to_string())
    })));
    v.push(("jiff Zoned::from_str [offset_conflict=Reject, default]", "ixdtf-zoned", Box::new(|s| {
        s.parse::<jiff::Zoned>().map(|z| (z.to_string(), jiff_utc(&z.timestamp()))).map_err(|e| e.to_string())
    })));
    for (name, oc) in [
        ("jiff DateTimeParser.offset_conflict(AlwaysOffset).parse_zoned", OffsetConflict::AlwaysOffset),
        ("jiff DateTimeParser.offset_conflict(AlwaysTimeZone).parse_zoned", OffsetConflict::AlwaysTimeZone),
        ("jiff DateTimeParser.offset_conflict(PreferOffset).parse_zoned", OffsetConflict::PreferOffset),
    ] {
        v.push((name, "ixdtf-zoned", Box::new(move |s| {
            let p = DateTimeParser::new().offset_conflict(oc);
            p.parse_zoned(s).map(|z| (z.to_string(), jiff_utc(&z.timestamp()))).map_err(|e| e.to_string())
        })));
    }
    v
}

fn fmt_row(api: &str, out: Result<String, String>) {
    match out {
        Ok(o) => emit(json!({"lang":"rust","kind":"format","api":api,"out":o})),
        Err(e) => emit(json!({"lang":"rust","kind":"format","api":api,"out":null,"err":e})),
    }
}

fn producers() {
    let fo = |secs: i32| FixedOffset::east_opt(secs).unwrap();
    let utc = Utc.with_ymd_and_hms(2026, 9, 24, 12, 0, 0).unwrap();
    let utc_frac = utc + chrono::Duration::milliseconds(120);
    let paris = utc.with_timezone(&fo(7200));
    let lmt = utc.with_timezone(&fo(-2670)); // -00:44:30
    let secs30 = utc.with_timezone(&fo(30));
    let y0 = Utc.with_ymd_and_hms(0, 1, 1, 0, 0, 0).unwrap();
    let y10000 = Utc.with_ymd_and_hms(10000, 1, 1, 0, 0, 0).unwrap();
    let yneg = Utc.with_ymd_and_hms(-1, 1, 1, 0, 0, 0).unwrap();
    let y50 = Utc.with_ymd_and_hms(50, 1, 1, 0, 0, 0).unwrap();
    let leap = NaiveDate::from_ymd_opt(2016, 12, 31).unwrap().and_hms_nano_opt(23, 59, 59, 1_500_000_000).unwrap().and_utc();
    let leap0 = NaiveDate::from_ymd_opt(2016, 12, 31).unwrap().and_hms_nano_opt(23, 59, 59, 1_000_000_000).unwrap().and_utc();
    let leap_bogus = NaiveDate::from_ymd_opt(2026, 9, 24).unwrap().and_hms_nano_opt(12, 0, 59, 1_000_000_000).unwrap().and_utc();

    // chrono ------------------------------------------------------------
    fmt_row("chrono DateTime<Utc>::to_rfc3339()", Ok(utc.to_rfc3339()));
    fmt_row("chrono DateTime<Utc>::to_rfc3339() [120ms]", Ok(utc_frac.to_rfc3339()));
    for (nm, sf) in [("Secs", SecondsFormat::Secs), ("Millis", SecondsFormat::Millis), ("Micros", SecondsFormat::Micros), ("Nanos", SecondsFormat::Nanos), ("AutoSi", SecondsFormat::AutoSi)] {
        for z in [true, false] {
            fmt_row(&format!("chrono to_rfc3339_opts(SecondsFormat::{nm}, use_z={z}) [120ms UTC]"), Ok(utc_frac.to_rfc3339_opts(sf, z)));
        }
    }
    fmt_row("chrono to_rfc3339_opts(Secs, true) [+02:00, use_z ignored]", Ok(paris.to_rfc3339_opts(SecondsFormat::Secs, true)));
    fmt_row("chrono DateTime<Utc> Display (to_string)", Ok(utc.to_string()));
    fmt_row("chrono DateTime<FixedOffset> Display", Ok(paris.to_string()));
    fmt_row("chrono DateTime<Utc> Debug", Ok(format!("{:?}", utc)));
    fmt_row("chrono DateTime<FixedOffset> Debug", Ok(format!("{:?}", paris)));
    fmt_row("chrono serde_json::to_string(DateTime<Utc>)", serde_json::to_string(&utc).map_err(|e| e.to_string()));
    fmt_row("chrono serde_json::to_string(DateTime<FixedOffset>)", serde_json::to_string(&paris).map_err(|e| e.to_string()));
    fmt_row("chrono serde_json::to_string(DateTime<Utc>) [120ms]", serde_json::to_string(&utc_frac).map_err(|e| e.to_string()));
    fmt_row("chrono serde_json::to_string(NaiveDateTime)", serde_json::to_string(&utc.naive_utc()).map_err(|e| e.to_string()));
    fmt_row("chrono NaiveDateTime Display", Ok(utc.naive_utc().to_string()));
    fmt_row("chrono format(\"%+\") [UTC]", Ok(utc.format("%+").to_string()));
    fmt_row("chrono format(\"%Y-%m-%dT%H:%M:%S%z\")", Ok(paris.format("%Y-%m-%dT%H:%M:%S%z").to_string()));
    fmt_row("chrono format(\"%Y-%m-%dT%H:%M:%S%:z\")", Ok(paris.format("%Y-%m-%dT%H:%M:%S%:z").to_string()));
    fmt_row("chrono Local naive_local().format(\"%Y-%m-%dT%H:%M:%SZ\") [lies]", Ok(utc.with_timezone(&Local).naive_local().format("%Y-%m-%dT%H:%M:%SZ").to_string()));
    fmt_row("chrono DateTime<Local>::to_rfc3339()", Ok(utc.with_timezone(&Local).to_rfc3339()));
    fmt_row("chrono to_rfc3339() [FixedOffset -00:44:30]", Ok(lmt.to_rfc3339()));
    fmt_row("chrono to_rfc3339() [FixedOffset +00:00:30]", Ok(secs30.to_rfc3339()));
    fmt_row("chrono to_rfc3339_opts(Secs,true) [FixedOffset -00:44:30]", Ok(lmt.to_rfc3339_opts(SecondsFormat::Secs, true)));
    fmt_row("chrono serde_json [FixedOffset -00:44:30]", serde_json::to_string(&lmt).map_err(|e| e.to_string()));
    fmt_row("chrono Display [FixedOffset -00:44:30]", Ok(lmt.to_string()));
    fmt_row("chrono to_rfc3339() [year 0]", Ok(y0.to_rfc3339()));
    fmt_row("chrono to_rfc3339() [year 50]", Ok(y50.to_rfc3339()));
    fmt_row("chrono to_rfc3339() [year 10000]", Ok(y10000.to_rfc3339()));
    fmt_row("chrono to_rfc3339() [year -1]", Ok(yneg.to_rfc3339()));
    fmt_row("chrono serde_json [year 10000]", serde_json::to_string(&y10000).map_err(|e| e.to_string()));
    fmt_row("chrono serde_json [year -1]", serde_json::to_string(&yneg).map_err(|e| e.to_string()));
    fmt_row("chrono to_rfc3339() [leap 2016-12-31 23:59:59 + 1.5e9 ns]", Ok(leap.to_rfc3339()));
    fmt_row("chrono to_rfc3339_opts(Secs,true) [leap 2016-12-31, nanos=1e9]", Ok(leap0.to_rfc3339_opts(SecondsFormat::Secs, true)));
    fmt_row("chrono to_rfc3339_opts(Secs,true) [leap-nanos on 2026-09-24 12:00:59]", Ok(leap_bogus.to_rfc3339_opts(SecondsFormat::Secs, true)));
    fmt_row("chrono to_rfc3339_opts(Secs,true) [leap on 2016-12-31 at +01:00]", Ok(leap0.with_timezone(&fo(3600)).to_rfc3339_opts(SecondsFormat::Secs, true)));
    fmt_row("chrono serde_json [leap 2016-12-31, 1.5e9 ns]", serde_json::to_string(&leap).map_err(|e| e.to_string()));

    // time --------------------------------------------------------------
    use time::macros::{datetime, offset};
    let t_utc = datetime!(2026-09-24 12:00:00 UTC);
    let t_frac = datetime!(2026-09-24 12:00:00.120 UTC);
    let t_paris = t_utc.to_offset(offset!(+2));
    let t_lmt = t_utc.to_offset(time::UtcOffset::from_hms(0, -44, -30).unwrap());
    let t_s30 = t_utc.to_offset(time::UtcOffset::from_hms(0, 0, 30).unwrap());
    let t_y0 = datetime!(0000-01-01 0:00 UTC);
    let t_yneg = datetime!(-0001-01-01 0:00 UTC);
    let t_y50 = datetime!(0050-01-01 0:00 UTC);
    let f = |d: time::OffsetDateTime| d.format(&Rfc3339).map_err(|e| e.to_string());
    fmt_row("time format(&Rfc3339) [UTC]", f(t_utc));
    fmt_row("time format(&Rfc3339) [120ms]", f(t_frac));
    fmt_row("time format(&Rfc3339) [+02:00]", f(t_paris));
    fmt_row("time format(&Rfc3339) [offset -00:44:30]", f(t_lmt));
    fmt_row("time format(&Rfc3339) [offset +00:00:30]", f(t_s30));
    fmt_row("time format(&Rfc3339) [year 0]", f(t_y0));
    fmt_row("time format(&Rfc3339) [year 50]", f(t_y50));
    fmt_row("time format(&Rfc3339) [year -1]", f(t_yneg));
    fmt_row("time format(&Iso8601::DEFAULT) [UTC]", t_utc.format(&Iso8601::DEFAULT).map_err(|e| e.to_string()));
    fmt_row("time format(&Iso8601::DEFAULT) [+02:00]", t_paris.format(&Iso8601::DEFAULT).map_err(|e| e.to_string()));
    fmt_row("time OffsetDateTime Display", Ok(t_utc.to_string()));
    fmt_row("time OffsetDateTime Display [+02:00]", Ok(t_paris.to_string()));
    #[derive(serde::Serialize)]
    struct W(#[serde(with = "time::serde::rfc3339")] time::OffsetDateTime);
    fmt_row("time serde_json (time::serde::rfc3339) [UTC]", serde_json::to_string(&W(t_utc)).map_err(|e| e.to_string()));
    fmt_row("time serde_json (time::serde::rfc3339) [offset -00:44:30]", serde_json::to_string(&W(t_lmt)).map_err(|e| e.to_string()));
    fmt_row("time serde_json default Serialize (no well-known attr)", serde_json::to_string(&t_utc).map_err(|e| e.to_string()));
    fmt_row("time format(\"[year]-[month]-[day]T[hour]:[minute]:[second]Z\") [lies on +02:00]", t_paris.format(time::macros::format_description!("[year]-[month]-[day]T[hour]:[minute]:[second]Z")).map_err(|e| e.to_string()));
    fmt_row("time format(\"...[offset_hour sign:mandatory][offset_minute]\") [no colon]", t_paris.format(time::macros::format_description!("[year]-[month]-[day]T[hour]:[minute]:[second][offset_hour sign:mandatory][offset_minute]")).map_err(|e| e.to_string()));

    // jiff --------------------------------------------------------------
    let ts: jiff::Timestamp = "2026-09-24T12:00:00Z".parse().unwrap();
    let ts_frac: jiff::Timestamp = "2026-09-24T12:00:00.120Z".parse().unwrap();
    let z_paris = ts.in_tz("Europe/Paris").unwrap();
    let z_utc = ts.in_tz("UTC").unwrap();
    let z_etc = ts.in_tz("Etc/UTC").unwrap();
    let z_fixed = ts.to_zoned(tz::TimeZone::fixed(tz::Offset::from_seconds(-2670).unwrap()));
    let z_fixed_min = ts.to_zoned(tz::TimeZone::fixed(tz::offset(5)));
    let z_monrovia = "1970-01-01T00:00:00Z".parse::<jiff::Timestamp>().unwrap().in_tz("Africa/Monrovia").unwrap();
    let z_paris1850 = "1850-01-01T00:00:00Z".parse::<jiff::Timestamp>().unwrap().in_tz("Europe/Paris").unwrap();
    let ts_y0 = jiff::civil::date(0, 1, 1).at(0, 0, 0, 0).to_zoned(tz::TimeZone::UTC).unwrap();
    let ts_yneg = jiff::civil::date(-1, 1, 1).at(0, 0, 0, 0).to_zoned(tz::TimeZone::UTC).unwrap();
    let ts_y50 = jiff::civil::date(50, 1, 1).at(0, 0, 0, 0).to_zoned(tz::TimeZone::UTC).unwrap();
    fmt_row("jiff Timestamp Display", Ok(ts.to_string()));
    fmt_row("jiff Timestamp Display [120ms]", Ok(ts_frac.to_string()));
    fmt_row("jiff Timestamp Display {:.3} [120ms]", Ok(format!("{:.3}", ts_frac)));
    fmt_row("jiff Timestamp Display {:.0} [120ms]", Ok(format!("{:.0}", ts_frac)));
    fmt_row("jiff Timestamp::display_with_offset(+02)", Ok(ts.display_with_offset(tz::offset(2)).to_string()));
    fmt_row("jiff Timestamp::display_with_offset(-00:44:30)", Ok(ts.display_with_offset(tz::Offset::from_seconds(-2670).unwrap()).to_string()));
    fmt_row("jiff Timestamp Display [year 0]", Ok(ts_y0.timestamp().to_string()));
    fmt_row("jiff Timestamp Display [year -1]", Ok(ts_yneg.timestamp().to_string()));
    fmt_row("jiff Timestamp Display [year 50]", Ok(ts_y50.timestamp().to_string()));
    fmt_row("jiff Timestamp Display [Timestamp::MAX]", Ok(jiff::Timestamp::MAX.to_string()));
    fmt_row("jiff Timestamp Display [Timestamp::MIN]", Ok(jiff::Timestamp::MIN.to_string()));
    fmt_row("jiff Zoned Display [Europe/Paris]", Ok(z_paris.to_string()));
    fmt_row("jiff Zoned Display [UTC]", Ok(z_utc.to_string()));
    fmt_row("jiff Zoned Display [Etc/UTC]", Ok(z_etc.to_string()));
    fmt_row("jiff Zoned Display [TimeZone::UTC]", Ok(ts.to_zoned(tz::TimeZone::UTC).to_string()));
    fmt_row("jiff Zoned Display [TimeZone::fixed(-00:44:30)]", Ok(z_fixed.to_string()));
    fmt_row("jiff Zoned Display [TimeZone::fixed(+05)]", Ok(z_fixed_min.to_string()));
    fmt_row("jiff Zoned Display [1970 Africa/Monrovia]", Ok(z_monrovia.to_string()));
    fmt_row("jiff Zoned Display [1850 Europe/Paris, LMT]", Ok(z_paris1850.to_string()));
    fmt_row("jiff Zoned.timestamp().display_with_offset(zoned.offset()) [1970 Monrovia]", Ok(z_monrovia.timestamp().display_with_offset(z_monrovia.offset()).to_string()));
    fmt_row("jiff Zoned Display [year 0 UTC]", Ok(ts_y0.to_string()));
    fmt_row("jiff Zoned Display [year -1 UTC]", Ok(ts_yneg.to_string()));
    fmt_row("jiff Zoned Display [Paris, 120ms]", Ok(ts_frac.in_tz("Europe/Paris").unwrap().to_string()));
    fmt_row("jiff Zoned Display {:.0} [Paris]", Ok(format!("{:.0}", z_paris)));
    let crit: jiff::Zoned = "2026-09-24T14:00:00+02:00[!Europe/Paris]".parse().unwrap();
    fmt_row("jiff Zoned Display after parsing [!Europe/Paris] (round trip)", Ok(crit.to_string()));
    let cal: jiff::Zoned = "2026-09-24T14:00:00+02:00[Europe/Paris][u-ca=hebrew]".parse().unwrap();
    fmt_row("jiff Zoned Display after parsing [u-ca=hebrew] (round trip)", Ok(cal.to_string()));
    let zz: jiff::Zoned = "2026-09-24T12:00:00Z[Europe/Paris]".parse().unwrap();
    fmt_row("jiff Zoned Display after parsing Z[Europe/Paris] (round trip)", Ok(zz.to_string()));
    fmt_row("jiff DateTimePrinter::new().lowercase(true).timestamp_to_string", Ok(DateTimePrinter::new().lowercase(true).timestamp_to_string(&ts)));
    fmt_row("jiff DateTimePrinter::new().separator(b' ').zoned_to_string", Ok(DateTimePrinter::new().separator(b' ').zoned_to_string(&z_paris)));
    fmt_row("jiff Zoned::strftime(\"%Y-%m-%dT%H:%M:%S%z\")", Ok(z_paris.strftime("%Y-%m-%dT%H:%M:%S%z").to_string()));
    fmt_row("jiff Zoned::strftime(\"%Y-%m-%dT%H:%M:%S%:z\")", Ok(z_paris.strftime("%Y-%m-%dT%H:%M:%S%:z").to_string()));
    fmt_row("jiff civil::DateTime Display [no offset]", Ok(z_paris.datetime().to_string()));
    fmt_row("jiff Zoned::strftime(\"%Y-%m-%dT%H:%M:%S%:z\") [1970 Monrovia]", Ok(z_monrovia.strftime("%Y-%m-%dT%H:%M:%S%:z").to_string()));

    // Z / +00:00 / -00:00 round trips (RFC 9557 §2, SKILL rule 2) --------------------
    for inp in ["2026-09-24T12:00:00Z", "2026-09-24T12:00:00+00:00", "2026-09-24T12:00:00-00:00"] {
        let c = DateTime::parse_from_rfc3339(inp).unwrap();
        fmt_row(&format!("chrono parse_from_rfc3339({inp}).to_rfc3339() [round trip]"), Ok(c.to_rfc3339()));
        fmt_row(&format!("chrono serde_json DateTime<FixedOffset> from {inp} [round trip]"), serde_json::to_string(&c).map_err(|e| e.to_string()));
        let t = time::OffsetDateTime::parse(inp, &Rfc3339).unwrap();
        fmt_row(&format!("time parse+format(&Rfc3339) {inp} [round trip]"), t.format(&Rfc3339).map_err(|e| e.to_string()));
        let j: jiff::Timestamp = inp.parse().unwrap();
        fmt_row(&format!("jiff Timestamp parse+Display {inp} [round trip]"), Ok(j.to_string()));
    }
    let mon: jiff::Zoned = "1969-12-31T23:15:30-00:45[Africa/Monrovia]".parse().unwrap();
    fmt_row("jiff Zoned parse(\"1969-12-31T23:15:30-00:45[Africa/Monrovia]\").timestamp() Display", Ok(mon.timestamp().to_string()));
    let mts: jiff::Timestamp = "1969-12-31T23:15:30-00:45[Africa/Monrovia]".parse().unwrap();
    fmt_row("jiff Timestamp parse(\"1969-12-31T23:15:30-00:45[Africa/Monrovia]\") Display", Ok(mts.to_string()));
}

fn main() {
    let path = std::env::args().nth(1).expect("inputs.json path");
    // probes/inputs.json schema 2 ({"inputs", "legacy"}: inputs + legacy) or the old list form.
    let doc: Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    let inputs: Vec<Value> = match doc {
        Value::Array(a) => a,
        d => d["inputs"].as_array().into_iter().chain(d["legacy"].as_array()).flatten().cloned().collect(),
    };
    for (api, mode, f) in parsers() {
        for rec in &inputs {
            let s = rec["s"].as_str().unwrap();
            let id = rec["id"].as_str().unwrap();
            match f(s) {
                Ok((out, utc)) => emit(json!({"lang":"rust","kind":"parse","api":api,"id":id,"input":s,"ok":true,"out":out,"utc":utc,"mode":mode})),
                Err(e) => emit(json!({"lang":"rust","kind":"parse","api":api,"id":id,"input":s,"ok":false,"err":e,"mode":mode})),
            }
        }
    }
    producers();
    // environment facts
    emit(json!({"lang":"rust","kind":"env","jiff_tz_db": format!("{:?}", jiff::tz::db()), "local_tz": format!("{:?}", jiff::tz::TimeZone::system().iana_name())}));
}

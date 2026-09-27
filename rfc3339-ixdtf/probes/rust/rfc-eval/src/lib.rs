//! Shared helpers for the probe and the vector adapter.
use chrono::{DateTime, Datelike, FixedOffset, Timelike, Utc};

/// Render an instant as `YYYY-MM-DDTHH:MM:SS.fffffffff` (UTC). `leap` prints second 60.
pub fn utc_string(secs: i64, nanos: u32) -> String {
    // chrono carries a leap second as nanos >= 1e9
    let (n, leap) = if nanos >= 1_000_000_000 { (nanos - 1_000_000_000, true) } else { (nanos, false) };
    match DateTime::<Utc>::from_timestamp(secs, n) {
        Some(d) => {
            let y = d.year();
            let ys = if y < 0 { format!("-{:04}", -y) } else { format!("{:04}", y) };
            format!(
                "{}-{:02}-{:02}T{:02}:{:02}:{:02}.{:09}",
                ys,
                d.month(),
                d.day(),
                d.hour(),
                d.minute(),
                if leap { 60 } else { d.second() },
                n
            )
        }
        None => format!("<out of chrono range: {secs}s {nanos}ns>"),
    }
}

pub fn chrono_utc(d: &DateTime<FixedOffset>) -> String {
    utc_string(d.timestamp(), d.timestamp_subsec_nanos())
}

pub fn time_utc(d: &time::OffsetDateTime) -> String {
    utc_string(d.unix_timestamp(), d.nanosecond())
}

pub fn jiff_utc(t: &jiff::Timestamp) -> String {
    let s = t.as_second();
    let n = t.subsec_nanosecond();
    // subsec is negative for pre-epoch instants in jiff
    if n < 0 { utc_string(s - 1, (n + 1_000_000_000) as u32) } else { utc_string(s, n as u32) }
}

/// JSON-encode a string (so serde deserializers see a JSON string).
pub fn json_str(s: &str) -> String {
    serde_json::to_string(s).unwrap()
}

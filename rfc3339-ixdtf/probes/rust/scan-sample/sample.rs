fn a(dt: chrono::DateTime<chrono::Local>) -> String { dt.naive_local().format("%Y-%m-%dT%H:%M:%SZ").to_string() }
fn b(dt: chrono::DateTime<chrono::Local>) -> String { dt.naive_local().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string() }
fn c(dt: chrono::DateTime<chrono::Local>) -> String { dt.format("%Y-%m-%dT%H:%M:%S%z").to_string() }
fn d(t: time::OffsetDateTime) -> String { t.format(format_description!("[year]-[month]-[day]T[hour]:[minute]:[second]Z")).unwrap() }
fn e(dt: chrono::DateTime<chrono::FixedOffset>) -> String { dt.to_string() }
fn f(s: &str) -> chrono::DateTime<chrono::Utc> { s.parse().unwrap() }
fn g(s: &str) -> time::OffsetDateTime { time::OffsetDateTime::parse(s, &Iso8601::DEFAULT).unwrap() }
fn h(s: &str) -> jiff::Timestamp { s.parse().unwrap() }

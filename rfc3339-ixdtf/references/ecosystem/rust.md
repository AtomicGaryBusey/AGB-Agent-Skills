# Rust (chrono, time, jiff): RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-25.** Rust 1.98.1 with chrono 0.4.45 (+ `serde`), time 0.3.55 (`parsing`, `formatting`, `serde-well-known`, `macros`; no `large-dates`), jiff 0.2.37 (default features; reads the system tz database) and serde_json 1.0.151. macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **chrono `parse_from_rfc3339`** is the strictest Rust consumer on syntax (0 TOO STRICT, 7 TOO LENIENT in 147
  scored vectors). It accepts `T`, `t` or a space, and a **U+2212 MINUS SIGN** as the offset sign
  (`2024-01-01T12:00:00−05:00` → offset −05:00). It accepts `:60` on **any** date, minute and offset
  (`2026-09-24T12:00:60Z`, and `2016-12-31T23:59:60+01:00` without the §5.7 shift) and keeps it as a leap
  second (nanosecond field ≥ 1 000 000 000). It truncates fractions to 9 digits.
- **chrono `FromStr` / serde `Deserialize`** (the default path for `DateTime<Utc>` fields in JSON) is much
  more lenient than `parse_from_rfc3339`: 23 TOO LENIENT vectors. It accepts `+0100`, 1-digit
  month/day/hour/minute, a 1-digit second (`2020-01-01T00:00:0.5Z` → 00:00:00.5, vector 3339-A-004), a 2-digit year (`24-01-01…` → year **24**), leading and trailing whitespace including
  `\n`, `\r` and `\r\n`, `…12:00:00 Z`, `…12:00:00UTC`, `+2024-…`, `+10000-…` and `-0001-…`.
- **chrono `NaiveDateTime::parse_from_str(s, "…%SZ")`** makes `Z` a literal: it gives a naive value (offset
  discarded) and rejects `+00:00`, `-00:00`, lower-case `z` and every fraction.
- **time `Rfc3339`** is the only Rust parser with a correct §5.7 leap-second check: it accepts `23:59:60` only at
  the end of a month, shifted by the offset (`1990-12-31T15:59:60-08:00` accepted,
  `2016-12-31T23:59:60+01:00` rejected), and maps it to `23:59:59.999999999` (graded INTERPRETATION,
  "leap-second representation", on vectors 3339-5.8-003/004 and 3339-5.7-025). Its date/time separator is
  **any single byte** (source comment: "RFC3339 allows any separator"): `2024-01-01X12:00:00Z`,
  `2024-01-01_12…`, `2024-01-01-12…`, `2024-01-01Z12…`, a newline, NUL and even a digit
  (`2024-01-01112:00:00Z`) were all accepted as 12:00Z.
- **time `Iso8601::DEFAULT`** parses ISO 8601, not RFC 3339: it accepts `+24:00` (as a 24 h offset), `+0200`,
  `+02`, `,5`, `T12:00Z`, the basic format, week and ordinal dates, and `+002026`. It rejects `t`/`z`.
- **jiff `Timestamp::from_str`** parses the Temporal grammar. It accepts `+02`, `+0200`, `+24:00` up to
  `+25:59`, offsets with seconds (`-00:44:30`, vector 3339-5.6-084; the LMT offset `1900-01-01T00:00:00+00:09:21`,
  vector 3339-5.6-085, gives 1899-12-31T23:50:39Z: the seconds are kept in the instant), `T12:00Z`, `,5`, the basic format and `+002026`. It maps any
  `:60` to `:59` (so two different strings give the same instant; on valid leap seconds the vector runner grades
  this INTERPRETATION, "leap-second representation"). It rejects more than 9 fraction digits and
  `9999-12-31T23:59:59Z` (`Timestamp::MAX` is `9999-12-30T22:00:00.999999999Z`). It **parses the RFC 9557
  suffix but ignores the time zone, even a critical one**: it accepted `…+05:00[!Europe/Paris]`,
  `…Z[!Mars/Olympus]`, `…+08:45[!+08:00]`, and critical zones given by a deprecated link name
  (`…+01:00[!US/Pacific]`, `…+02:00[!Europe/Kiev]`, vectors 9557-3.4-034/-037) (**VIOLATES 9557 MUST**, the same defect as `Temporal.Instant.from`).
  It does reject critical tags (`[!x-foo=bar]`).
- **jiff `Zoned::from_str`** (`OffsetConflict::Reject` by default) rejects every offset/zone inconsistency,
  elective or critical, and rejects unknown zones. `Z[zone]` never conflicts. But:
  - It reads **`-00:00` as `+00:00`**, not as `Z` (RFC 9557 §2): `…-00:00[!Europe/London]` in July is rejected
    (**TOO STRICT**). With `AlwaysTimeZone` or `PreferOffset`, `…T00:14:07-00:00[Europe/London]` became
    `00:14:07+01:00` = 23:14:07Z, **one hour off** the instant the string denotes (**WRONG VALUE**). Only
    `AlwaysOffset` gets it right.
  - The RFC 3339 part is as lenient as `Timestamp` (see above) and, in addition, the offset may be missing
    (`2022-07-08T00:14:07[Europe/Paris]`) or the time too (`2022-07-08[Europe/Paris]` → midnight). An
    offset time zone may be `[+24:00]` or `[+0500]`.
  - Tags: elective tags are syntax-checked and then **dropped** (there is no API to read them, so first-wins cannot
    be observed). **Every critical tag is rejected**, including `[!u-ca=gregory]` and `[!u-ca=iso8601]`, which
    jiff could honour. An **experimental elective key is accepted** (`[Europe/Paris][_foo=bar]`), where §3.2
    requires rejection. `[!_foo=bar]` is rejected.
  - Zone names are looked up case-insensitively (`[!europe/paris]` accepted). jiff's built-in `Etc/Unknown`
    (not in tzdata 2026c) is accepted, even as `Z[!Etc/Unknown]`, and prints back as `Z[Etc/Unknown]`.
  - `OffsetConflict` is the §3.4 switch, but it **ignores the critical flag**: `Reject` = "act" for both
    elective (MAY) and critical (MUST) zones, which conforms. `AlwaysOffset`, `AlwaysTimeZone` and
    `PreferOffset` silently resolve **critical** inconsistencies as well. That is permitted as programmed
    resolution (§3.4), but the caller cannot see that it happened: `Zoned` keeps neither the `!` nor the
    written offset. Use `fmt::temporal::Pieces::parse` if you need `TimeZoneAnnotation::is_critical()`.
- **Doc claims checked.** chrono's `parse_from_rfc3339` doc says it "Parses all valid RFC 3339 values": confirmed
  (0 TOO STRICT in 147 scored vectors; a 1050-digit fraction is accepted and truncated), but the doc does not list the
  leniencies above. jiff's docs say RFC 3339 and RFC 9557 "are supported in their entirety": **partly refuted**.
  jiff rejects valid input (more than 9 fraction digits, `9999-12-31T23:59:59Z`, `-00:00[!Europe/London]`,
  `[!u-ca=gregory]`), accepts many invalid forms (the same doc calls its format a "hybrid"), and `Timestamp`
  ignores critical zones. jiff's comment "Jiff basically always behaves as if `critical` is true" is refuted for `Timestamp`.

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict "conforming".

### `chrono DateTime::parse_from_rfc3339`

53 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | too lenient (space; OK only under a stated profile) |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |

### `chrono DateTime::<FixedOffset>::from_str` = `DateTime::<Utc>::from_str` = serde `Deserialize` for `DateTime<Utc>` / `DateTime<FixedOffset>`

46 of 59 probe inputs behaved as the RFCs require (not listed). The four APIs gave identical verdicts on all 59 inputs (serde `Deserialize` calls `FromStr`). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `+10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT — legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT — legacy probe only |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |

### `chrono DateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f%:z")`

Legacy probe only: no vector adapter key runs this API (`probes/rust/rfc-eval` covers `parse_from_rfc3339`, `FromStr`, serde, time `Rfc3339`, jiff). 43 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24t12:00:00Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: input contains invalid characters | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T12:00:00.1Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.1234567Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: input contains invalid characters | TOO STRICT |
| `0000-01-01T00:00:00Z` | rejected: input contains invalid characters | too strict (range limit) |
| `0001-01-01T00:00:00Z` | rejected: input contains invalid characters | TOO STRICT |
| `9999-12-31T23:59:59Z` | rejected: input contains invalid characters | TOO STRICT |
| `2024-02-29T12:00:00Z` | rejected: input contains invalid characters | TOO STRICT |

### `chrono DateTime::parse_from_str(s, "%+")`

Legacy probe only: no vector adapter key runs this API (`probes/rust/rfc-eval` covers `parse_from_rfc3339`, `FromStr`, serde, time `Rfc3339`, jiff). 47 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `+10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |

### `chrono NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%SZ")`

Legacy probe only: no vector adapter key runs this API (`probes/rust/rfc-eval` covers `parse_from_rfc3339`, `FromStr`, serde, time `Rfc3339`, jiff). 34 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00.000000000 | WRONG VALUE: offset discarded (naive result) |
| `2026-09-24t12:00:00Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00+00:00` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00-00:00` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: input contains invalid characters | too strict (offset range) |
| `2026-09-24T12:00:00+05:30` | rejected: input contains invalid characters | TOO STRICT |
| `2016-12-31T23:59:60Z` | accepted → UTC naive:2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | rejected: input contains invalid characters | too strict (no leap second) |
| `2026-09-24T23:59:60Z` | accepted → UTC naive:2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC naive:2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.1234567Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: input contains invalid characters | TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00.000000000 | TOO LENIENT (naive/local result) |
| ` 2026-09-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00.000000000 | TOO LENIENT (naive/local result) |
| `0001-01-01T00:00:00Z` | accepted → UTC naive:0001-01-01T00:00:00.000000000 | WRONG VALUE: offset discarded (naive result) |
| `9999-12-31T23:59:59Z` | accepted → UTC naive:9999-12-31T23:59:59.000000000 | WRONG VALUE: offset discarded (naive result) |
| `+10000-01-01T00:00:00Z` | accepted → UTC naive:+10000-01-01T00:00:00.000000000 | TOO LENIENT (naive/local result) |
| `+002026-09-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00.000000000 | TOO LENIENT (naive/local result) |
| `-0001-01-01T00:00:00Z` | accepted → UTC naive:-0001-01-01T00:00:00.000000000 | TOO LENIENT (naive/local result) |
| `2024-02-29T12:00:00Z` | accepted → UTC naive:2024-02-29T12:00:00.000000000 | WRONG VALUE: offset discarded (naive result) |

### `time OffsetDateTime::parse(s, &Rfc3339)` = `#[serde(with = "time::serde::rfc3339")]`

55 of 59 probe inputs behaved as the RFCs require (not listed). Both gave identical verdicts. The probe inputs do not show its worst leniency: the date/time separator is **any single byte** (see Notes). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | too lenient (space; OK only under a stated profile) |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59.999999999 | conforming (leap-second representation → :59.999999999; vector 3339-5.7-025: INTERPRETATION) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59.999999999 | conforming (leap-second representation → :59.999999999; vector 3339-5.7-031) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |

### `time OffsetDateTime::parse(s, &Iso8601::DEFAULT)`

Legacy probe only: no vector adapter key runs this API (`probes/rust/rfc-eval` covers `parse_from_rfc3339`, `FromStr`, serde, time `Rfc3339`, jiff). 45 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: unexpected trailing characters; the end of input was expected | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: unexpected trailing characters; the end of input was expected | TOO STRICT |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-W39-4T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-267T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |

### `jiff Timestamp::from_str`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59.000000000 | conforming (leap-second representation → :59; vector 3339-5.7-025: INTERPRETATION) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59.000000000 | conforming (leap-second representation → :59; vector 3339-5.7-031) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:59.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:59.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains  | TOO STRICT |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `9999-12-31T23:59:59Z` | rejected: failed to convert civil datetime to timestamp with offset +00 (Timestamp::MAX is 9999-12-30T22:00:00.999999999Z) | too strict (range limit) |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT — legacy probe only |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000 | conforming (MAY; offset wins) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000 | VIOLATES 9557 MUST (accepted) |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00.000000000 | VIOLATES 9557 MUST (accepted) |

### `jiff Zoned::from_str [offset_conflict=Reject, default]`

38 of 59 probe inputs behaved as the RFCs require (not listed). 20 plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation (by design; n/a). See the bracketed re-probe below: with a consistent suffix added, it accepts `+02`, `+0200`, `+24:00`, `T12:00Z`, `,5`, the basic format, `+002026` and `:60` on any date. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00.123456789012Z` | rejected: parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains  | TOO STRICT |

### `jiff DateTimeParser.offset_conflict(AlwaysOffset).parse_zoned`

36 of 59 probe inputs behaved as the RFCs require (not listed). 20 plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation (by design; n/a). See the bracketed re-probe below: with a consistent suffix added, it accepts `+02`, `+0200`, `+24:00`, `T12:00Z`, `,5`, the basic format, `+002026` and `:60` on any date. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00.123456789012Z` | rejected: parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains  | TOO STRICT |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000 | conforming (MAY; offset wins) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000 | conforming (caller opted into programmed resolution, §3.4; jiff applies it to elective and critical zones alike) |

### `jiff DateTimeParser.offset_conflict(AlwaysTimeZone).parse_zoned`

36 of 59 probe inputs behaved as the RFCs require (not listed). 20 plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation (by design; n/a). See the bracketed re-probe below: with a consistent suffix added, it accepts `+02`, `+0200`, `+24:00`, `T12:00Z`, `,5`, the basic format, `+002026` and `:60` on any date. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00.123456789012Z` | rejected: parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains  | TOO STRICT |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T23:00:00.000000000 | conforming (MAY; zone wins, local time kept) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T23:00:00.000000000 | conforming (caller opted into programmed resolution, §3.4; jiff applies it to elective and critical zones alike) |

### `jiff DateTimeParser.offset_conflict(PreferOffset).parse_zoned`

36 of 59 probe inputs behaved as the RFCs require (not listed). 20 plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation (by design; n/a). See the bracketed re-probe below: with a consistent suffix added, it accepts `+02`, `+0200`, `+24:00`, `T12:00Z`, `,5`, the basic format, `+002026` and `:60` on any date. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00.123456789012Z` | rejected: parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains  | TOO STRICT |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T23:00:00.000000000 | conforming (MAY; zone wins, local time kept) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T23:00:00.000000000 | conforming (caller opted into programmed resolution, §3.4; jiff applies it to elective and critical zones alike) |

### `jiff Zoned::from_str` re-probed with a consistent `[zone]` suffix (default `Reject`)

30 of 44 bracketed inputs behaved as the RFCs require (not listed; `no-off`/`date-only` covered by vectors 9557-4.1-040/045). The vector runs skip every RFC 3339 vector without a `[time-zone]` for `Zoned` (n/a), so the RFC 3339-part leniencies below are legacy probe only unless a vector is named. Deviations:

| Input (probe + suffix) | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z[Europe/Paris]` | accepted → 2026-09-24T14:00:00+02:00[Europe/Paris] | too lenient (space; OK only under a stated profile) — legacy probe only |
| `2026-09-24T12:00:00+24:00[+24:00]` | accepted → 2026-09-24T12:00:00+24:00[+24:00] | TOO LENIENT (cf. vector 9557-4.1-009) |
| `2026-09-24T12:00:00+0200[+02:00]` | accepted → 2026-09-24T12:00:00+02:00[+02:00] | TOO LENIENT — legacy probe only |
| `2026-09-24T12:00:00+02[+02:00]` | accepted → 2026-09-24T12:00:00+02:00[+02:00] | TOO LENIENT — legacy probe only |
| `2016-12-31T23:59:60Z[Europe/Paris]` | accepted → 2017-01-01T00:59:59+01:00[Europe/Paris] | conforming (leap-second representation → :59) |
| `2016-12-31T18:59:60-05:00[-05:00]` | accepted → 2016-12-31T18:59:59-05:00[-05:00] | conforming (leap-second representation → :59) |
| `2026-09-24T23:59:60Z[Europe/Paris]` | accepted → 2026-09-25T01:59:59+02:00[Europe/Paris] | TOO LENIENT (→ :59) (same missing §5.7 check as vector 9557-3.4-025) |
| `2026-09-24T12:00:60Z[Europe/Paris]` | accepted → 2026-09-24T14:00:59+02:00[Europe/Paris] | TOO LENIENT (→ :59) (same missing §5.7 check as vector 9557-3.4-025) |
| `2026-09-24T12:00:00.123456789012Z[Europe/Paris]` | rejected: parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z | TOO STRICT |
| `2026-09-24T12:00:00,5Z[Europe/Paris]` | accepted → 2026-09-24T14:00:00.5+02:00[Europe/Paris] | TOO LENIENT — legacy probe only |
| `2026-09-24T12:00Z[Europe/Paris]` | accepted → 2026-09-24T14:00:00+02:00[Europe/Paris] | TOO LENIENT (cf. vector 9557-1.2-002) |
| `20260924T120000Z[Europe/Paris]` | accepted → 2026-09-24T14:00:00+02:00[Europe/Paris] | TOO LENIENT — legacy probe only |
| `9999-12-31T23:59:59Z[Europe/Paris]` | rejected: error converting datetime to instant in time zone Europe/Paris: conver | too strict (range limit) |
| `+002026-09-24T12:00:00Z[Europe/Paris]` | accepted → 2026-09-24T14:00:00+02:00[Europe/Paris] | TOO LENIENT — legacy probe only |
| `2022-07-08T00:14:07[Europe/Paris]` (vector 9557-4.1-040) | accepted (offset taken from the zone) | TOO LENIENT |
| `2022-07-08[Europe/Paris]` (vector 9557-4.1-045) | accepted (midnight) | TOO LENIENT |
| `2022-07-08T00:14:07-00:00[!Europe/London]` (vector 9557-3.4-009) | rejected: offset conflict (`-00:00` read as `+00:00`) | TOO STRICT |
| `2026-09-24T14:00:00+02:00[Europe/Paris][_foo=bar]` | accepted | TOO LENIENT (experimental key, §3.2) — legacy probe only |
| `2026-09-24T14:00:00+02:00[Europe/Paris][!u-ca=iso8601]` | rejected: unsupported critical annotation | too strict (jiff processes no `u-ca`; defensible; vector 9557-3.3-007 `[!u-ca=gregory]` is graded TOO STRICT) |

## Producers (formatters)

### chrono formatters (producer side)

| Call | Output | RFC verdict |
|---|---|---|
| `chrono DateTime<Utc>::to_rfc3339()` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono DateTime<Utc>::to_rfc3339() [120ms]` | `2026-09-24T12:00:00.120+00:00` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Secs, use_z=true) [120ms UTC]` | `2026-09-24T12:00:00Z` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Secs, use_z=false) [120ms UTC]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Millis, use_z=true) [120ms UTC]` | `2026-09-24T12:00:00.120Z` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Millis, use_z=false) [120ms UTC]` | `2026-09-24T12:00:00.120+00:00` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Micros, use_z=true) [120ms UTC]` | `2026-09-24T12:00:00.120000Z` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Micros, use_z=false) [120ms UTC]` | `2026-09-24T12:00:00.120000+00:00` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Nanos, use_z=true) [120ms UTC]` | `2026-09-24T12:00:00.120000000Z` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::Nanos, use_z=false) [120ms UTC]` | `2026-09-24T12:00:00.120000000+00:00` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::AutoSi, use_z=true) [120ms UTC]` | `2026-09-24T12:00:00.120Z` | conforming |
| `chrono to_rfc3339_opts(SecondsFormat::AutoSi, use_z=false) [120ms UTC]` | `2026-09-24T12:00:00.120+00:00` | conforming |
| `chrono to_rfc3339_opts(Secs, true) [+02:00, use_z ignored]` | `2026-09-24T14:00:00+02:00` | conforming (`use_z` only affects offset 0) |
| `chrono DateTime<Utc> Display (to_string)` | `2026-09-24 12:00:00 UTC` | WRONG OUTPUT (space separator, ' UTC' suffix) |
| `chrono DateTime<FixedOffset> Display` | `2026-09-24 14:00:00 +02:00` | WRONG OUTPUT (space separators) |
| `chrono DateTime<Utc> Debug` | `2026-09-24T12:00:00Z` | conforming |
| `chrono DateTime<FixedOffset> Debug` | `2026-09-24T14:00:00+02:00` | conforming |
| `chrono serde_json::to_string(DateTime<Utc>)` | `2026-09-24T12:00:00Z` | conforming |
| `chrono serde_json::to_string(DateTime<FixedOffset>)` | `2026-09-24T14:00:00+02:00` | conforming |
| `chrono serde_json::to_string(DateTime<Utc>) [120ms]` | `2026-09-24T12:00:00.120Z` | conforming |
| `chrono serde_json::to_string(NaiveDateTime)` | `2026-09-24T12:00:00` | WRONG OUTPUT (time-offset) |
| `chrono NaiveDateTime Display` | `2026-09-24 12:00:00` | WRONG OUTPUT (date-time-separator) |
| `chrono format("%+") [UTC]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono format("%Y-%m-%dT%H:%M:%S%z")` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (time-numoffset) |
| `chrono format("%Y-%m-%dT%H:%M:%S%:z")` | `2026-09-24T14:00:00+02:00` | conforming |
| `chrono Local naive_local().format("%Y-%m-%dT%H:%M:%SZ") [lies]` | `2026-09-24T08:00:00Z` | WRONG VALUE (New York wall time labelled Z; true instant 12:00:00Z) |
| `chrono DateTime<Local>::to_rfc3339()` | `2026-09-24T08:00:00-04:00` | conforming |
| `chrono to_rfc3339() [FixedOffset -00:44:30]` | `2026-09-24T11:15:30-00:45` | WRONG VALUE (offset rounded to -00:45, wall time kept: string denotes 12:00:30Z, true instant 12:00:00Z) |
| `chrono to_rfc3339() [FixedOffset +00:00:30]` | `2026-09-24T12:00:30+00:01` | WRONG VALUE (offset rounded to +00:01, wall time kept: string denotes 11:59:30Z, true instant 12:00:00Z) |
| `chrono to_rfc3339_opts(Secs,true) [FixedOffset -00:44:30]` | `2026-09-24T11:15:30-00:45` | WRONG VALUE (offset rounded to -00:45, wall time kept: string denotes 12:00:30Z, true instant 12:00:00Z) |
| `chrono serde_json [FixedOffset -00:44:30]` | `2026-09-24T11:15:30-00:45` | WRONG VALUE (offset rounded to -00:45, wall time kept: string denotes 12:00:30Z, true instant 12:00:00Z) |
| `chrono Display [FixedOffset -00:44:30]` | `2026-09-24 11:15:30 -00:44:30` | WRONG OUTPUT (space separators, offset has seconds) |
| `chrono to_rfc3339() [year 0]` | `0000-01-01T00:00:00+00:00` | conforming |
| `chrono to_rfc3339() [year 50]` | `0050-01-01T00:00:00+00:00` | conforming |
| `chrono to_rfc3339() [year 10000]` | `+10000-01-01T00:00:00+00:00` | WRONG OUTPUT (date-fullyear) |
| `chrono to_rfc3339() [year -1]` | `-0001-01-01T00:00:00+00:00` | WRONG OUTPUT (date-fullyear) |
| `chrono serde_json [year 10000]` | `+10000-01-01T00:00:00Z` | WRONG OUTPUT (date-fullyear) |
| `chrono serde_json [year -1]` | `-0001-01-01T00:00:00Z` | WRONG OUTPUT (date-fullyear) |
| `chrono to_rfc3339() [leap 2016-12-31 23:59:59 + 1.5e9 ns]` | `2016-12-31T23:59:60.500+00:00` | conforming |
| `chrono to_rfc3339_opts(Secs,true) [leap 2016-12-31, nanos=1e9]` | `2016-12-31T23:59:60Z` | conforming |
| `chrono to_rfc3339_opts(Secs,true) [leap-nanos on 2026-09-24 12:00:59]` | `2026-09-24T12:00:60Z` | WRONG OUTPUT (:60 outside a leap-second position, §5.7) |
| `chrono to_rfc3339_opts(Secs,true) [leap on 2016-12-31 at +01:00]` | `2017-01-01T00:59:60+01:00` | conforming |
| `chrono serde_json [leap 2016-12-31, 1.5e9 ns]` | `2016-12-31T23:59:60.500Z` | conforming |
| `chrono parse_from_rfc3339(2026-09-24T12:00:00Z).to_rfc3339() [round trip]` | `2026-09-24T12:00:00+00:00` | conforming; Advisory: `Z` (offset unknown) rewritten to `+00:00` (rule 2) |
| `chrono serde_json DateTime<FixedOffset> from 2026-09-24T12:00:00Z [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `chrono parse_from_rfc3339(2026-09-24T12:00:00+00:00).to_rfc3339() [round trip]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono serde_json DateTime<FixedOffset> from 2026-09-24T12:00:00+00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming; Advisory: `+00:00` rewritten to `Z` (rule 2) |
| `chrono parse_from_rfc3339(2026-09-24T12:00:00-00:00).to_rfc3339() [round trip]` | `2026-09-24T12:00:00+00:00` | conforming; Advisory: `-00:00` (offset unknown) rewritten to `+00:00` (rule 2) |
| `chrono serde_json DateTime<FixedOffset> from 2026-09-24T12:00:00-00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |

### time formatters (producer side)

| Call | Output | RFC verdict |
|---|---|---|
| `time format(&Rfc3339) [UTC]` | `2026-09-24T12:00:00Z` | conforming |
| `time format(&Rfc3339) [120ms]` | `2026-09-24T12:00:00.12Z` | conforming |
| `time format(&Rfc3339) [+02:00]` | `2026-09-24T14:00:00+02:00` | conforming |
| `time format(&Rfc3339) [offset -00:44:30]` | ✗ `The offset_second component cannot be formatted into the requested format.` | refuses (safe: returns `Err` for offset seconds) |
| `time format(&Rfc3339) [offset +00:00:30]` | ✗ `The offset_second component cannot be formatted into the requested format.` | refuses (safe: returns `Err` for offset seconds) |
| `time format(&Rfc3339) [year 0]` | `0000-01-01T00:00:00Z` | conforming |
| `time format(&Rfc3339) [year 50]` | `0050-01-01T00:00:00Z` | conforming |
| `time format(&Rfc3339) [year -1]` | ✗ `The year component cannot be formatted into the requested format.` | refuses (safe: returns `Err` for year < 0) |
| `time format(&Iso8601::DEFAULT) [UTC]` | `2026-09-24T12:00:00.000000000Z` | conforming |
| `time format(&Iso8601::DEFAULT) [+02:00]` | `2026-09-24T14:00:00.000000000+02:00` | conforming |
| `time OffsetDateTime Display` | `2026-09-24 12:00:00.0 +00:00:00` | WRONG OUTPUT (space separators, offset has seconds) |
| `time OffsetDateTime Display [+02:00]` | `2026-09-24 14:00:00.0 +02:00:00` | WRONG OUTPUT (space separators, offset has seconds) |
| `time serde_json (time::serde::rfc3339) [UTC]` | `2026-09-24T12:00:00Z` | conforming |
| `time serde_json (time::serde::rfc3339) [offset -00:44:30]` | ✗ `The offset_second component cannot be formatted into the requested format.` | refuses (safe: returns `Err` for offset seconds) |
| `time serde_json default Serialize (no well-known attr)` | `[2026,267,12,0,0,0,0,0,0]` | WRONG OUTPUT (JSON array, not a string) |
| `time format("[year]-[month]-[day]T[hour]:[minute]:[second]Z") [lies on +02:00]` | `2026-09-24T14:00:00Z` | WRONG VALUE (+02:00 wall time labelled Z; true instant 12:00:00Z) |
| `time format("...[offset_hour sign:mandatory][offset_minute]") [no colon]` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (time-numoffset) |
| `time parse+format(&Rfc3339) 2026-09-24T12:00:00Z [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `time parse+format(&Rfc3339) 2026-09-24T12:00:00+00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming; Advisory: `+00:00` rewritten to `Z` (rule 2) |
| `time parse+format(&Rfc3339) 2026-09-24T12:00:00-00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |

### jiff formatters (producer side)

| Call | Output | RFC verdict |
|---|---|---|
| `jiff Timestamp Display` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp Display [120ms]` | `2026-09-24T12:00:00.12Z` | conforming |
| `jiff Timestamp Display {:.3} [120ms]` | `2026-09-24T12:00:00.120Z` | conforming |
| `jiff Timestamp Display {:.0} [120ms]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp::display_with_offset(+02)` | `2026-09-24T14:00:00+02:00` | conforming |
| `jiff Timestamp::display_with_offset(-00:44:30)` | `2026-09-24T11:15:30-00:45` | WRONG VALUE (offset rounded to -00:45, wall time kept: string denotes 12:00:30Z, true instant 12:00:00Z) |
| `jiff Timestamp Display [year 0]` | `0000-01-01T00:00:00Z` | conforming |
| `jiff Timestamp Display [year -1]` | `-000001-01-01T00:00:00Z` | WRONG OUTPUT (date-fullyear) |
| `jiff Timestamp Display [year 50]` | `0050-01-01T00:00:00Z` | conforming |
| `jiff Timestamp Display [Timestamp::MAX]` | `9999-12-30T22:00:00.999999999Z` | conforming |
| `jiff Timestamp Display [Timestamp::MIN]` | `-009999-01-02T01:59:59Z` | WRONG OUTPUT (date-fullyear) |
| `jiff Zoned Display [Europe/Paris]` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display [UTC]` | `2026-09-24T12:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [Etc/UTC]` | `2026-09-24T12:00:00+00:00[Etc/UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [TimeZone::UTC]` | `2026-09-24T12:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [TimeZone::fixed(-00:44:30)]` | `2026-09-24T11:15:30-00:45[-00:45]` | WRONG VALUE (offset rounded to -00:45 (suffix too), wall time kept: string denotes 12:00:30Z, true instant 12:00:00Z) |
| `jiff Zoned Display [TimeZone::fixed(+05)]` | `2026-09-24T17:00:00+05:00[+05:00]` | conforming (RFC 9557); Advisory: offset time zone copied from the offset (§1.2) |
| `jiff Zoned Display [1970 Africa/Monrovia]` | `1969-12-31T23:15:30-00:45[Africa/Monrovia]` | WRONG VALUE (offset rounded to -00:45, wall time kept: string denotes 1970-01-01T00:00:30Z, true instant 1970-01-01T00:00:00Z); jiff `Zoned` re-parse recovers the instant from the zone, jiff `Timestamp` re-parse does not |
| `jiff Zoned Display [1850 Europe/Paris, LMT]` | `1850-01-01T00:09:21+00:09[Europe/Paris]` | WRONG VALUE (offset rounded to +00:09, wall time kept: string denotes 1850-01-01T00:00:21Z, true instant 1850-01-01T00:00:00Z) |
| `jiff Zoned.timestamp().display_with_offset(zoned.offset()) [1970 Monrovia]` | `1969-12-31T23:15:30-00:45` | WRONG VALUE (offset rounded to -00:45, wall time kept: string denotes 1970-01-01T00:00:30Z, true instant 1970-01-01T00:00:00Z) |
| `jiff Zoned Display [year 0 UTC]` | `0000-01-01T00:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [year -1 UTC]` | `-000001-01-01T00:00:00+00:00[UTC]` | WRONG OUTPUT (date-fullyear) |
| `jiff Zoned Display [Paris, 120ms]` | `2026-09-24T14:00:00.12+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display {:.0} [Paris]` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display after parsing [!Europe/Paris] (round trip)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557), but the `!` is dropped |
| `jiff Zoned Display after parsing [u-ca=hebrew] (round trip)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557), but the tag is dropped |
| `jiff Zoned Display after parsing Z[Europe/Paris] (round trip)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557, §3.4 Fig. 2); `Z` becomes `+02:00` |
| `jiff DateTimePrinter::new().lowercase(true).timestamp_to_string` | `2026-09-24t12:00:00z` | conforming (but SHOULD use upper case) |
| `jiff DateTimePrinter::new().separator(b' ').zoned_to_string` | `2026-09-24 14:00:00+02:00[Europe/Paris]` | WRONG OUTPUT (date-time-separator) |
| `jiff Zoned::strftime("%Y-%m-%dT%H:%M:%S%z")` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (time-numoffset) |
| `jiff Zoned::strftime("%Y-%m-%dT%H:%M:%S%:z")` | `2026-09-24T14:00:00+02:00` | conforming |
| `jiff civil::DateTime Display [no offset]` | `2026-09-24T14:00:00` | WRONG OUTPUT (time-offset) |
| `jiff Zoned::strftime("%Y-%m-%dT%H:%M:%S%:z") [1970 Monrovia]` | `1969-12-31T23:15:30-00:44:30` | WRONG OUTPUT (time-numoffset) |
| `jiff Timestamp parse+Display 2026-09-24T12:00:00Z [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp parse+Display 2026-09-24T12:00:00+00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming; Advisory: `+00:00` rewritten to `Z` (rule 2) |
| `jiff Timestamp parse+Display 2026-09-24T12:00:00-00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Zoned parse("1969-12-31T23:15:30-00:45[Africa/Monrovia]").timestamp() Display` | `1970-01-01T00:00:00Z` | consumer note: `Zoned` re-reads its own output as the true instant (offset matched after rounding the zone's -00:44:30) |
| `jiff Timestamp parse("1969-12-31T23:15:30-00:45[Africa/Monrovia]") Display` | `1970-01-01T00:00:30Z` | consumer note: the same string read by `Timestamp` is 30 s later than the `Zoned` reading |

## Conformance vectors (`run_vectors.py`, 310-vector set, 2026-09-26)

All runs: `probes/run_vector_probes.py --lang rust` (`--batch --target-options fixed --target-has-tzdata yes`,
`TZ=America/New_York`). "Scored" excludes skips and interpretations. Report:
`evals/baselines/probes/vector-runs/rust.txt`. (The 2026-09-25 runs used the 274-vector set; those reports stay in
`evals/baselines/probes/rust-reports/`.)

| Adapter (`adapter <api>`) | `--target-kind` | Pass / scored | Too lenient | Too strict | Wrong value | Interp. | Skipped |
|---|---|---|---|---|---|---|---|
| `chrono` (`parse_from_rfc3339`) | rfc3339 | 140 / 147 (95.2%) | 7 | 0 | 0 | 6 | 157 |
| `chrono-fromstr` (`DateTime<FixedOffset>::from_str`) | rfc3339 | 124 / 147 (84.4%) | 23 | 0 | 0 | 6 | 157 |
| `chrono-serde` (`serde_json` → `DateTime<Utc>`) | rfc3339 | 124 / 147 (84.4%) | 23 | 0 | 0 | 6 | 157 |
| `time` (`OffsetDateTime::parse(&Rfc3339)`) | rfc3339 | 142 / 144 (98.6%) | 2 | 0 | 0 | 9 ³ | 157 |
| `jiff-timestamp` (`Timestamp::from_str`) | rfc3339 | 123 / 144 (85.4%) | 17 | 4 | 0 | 9 ³ | 157 |
| `jiff-timestamp-both` (supplementary: it parses suffixes) | both | 196 / 240 (81.7%) | 38 | 6 | 0 | 38 ³ | 32 |
| `jiff-zoned-reject` (`OffsetConflict::Reject`, default) | ixdtf | 151 / 163 (92.6%) | 6 | 6 | 0 | 20 | 127 |
| `jiff-zoned-always-offset` | ixdtf | 142 / 155 (91.6%) | 8 | 5 | 0 | 28 | 127 |
| `jiff-zoned-always-timezone` | ixdtf | 142 / 155 (91.6%) | 8 | 5 | 0 ¹ | 28 | 127 |
| `jiff-zoned-prefer-offset` | ixdtf | 142 / 155 (91.6%) | 8 | 5 | 0 ¹ | 28 | 127 |

Skips: 128 ixdtf-profile vectors for `--target-kind rfc3339`, and 29 or 32 non-default-option vectors. For
`jiff-zoned-*`, the adapter reports the 94 vectors that `Zoned` rejects only because they have no `[time-zone]` as
`{"skip": true}` (n/a by design, like Temporal `ZonedDateTime` in `javascript.md`).
¹ The vector for `-00:00[zone]` (9557-3.4-009) has no `fields`, so the runner counted it as a pass. The
semantic probe shows a 1 h wrong instant with these two policies (see the notes at the top of this file).
³ Includes the 3 valid leap-second vectors (3339-5.8-003/004, 3339-5.7-025), graded INTERPRETATION
("leap-second representation"): `time` stores them as `23:59:59.999999999`, jiff as `:59`. In the 274-vector
reports they were counted as 3 WRONG VALUE.

**Why each failure happened:**

- **chrono** (7 lenient): space separator (3339-5.6-015); U+2212 minus (3339-5.6-028); `:60` at an unshifted
  offset (3339-5.7-033/034); `:60` not at month end or not at 23:59 (3339-5.7-035/036/037).
- **chrono-fromstr / chrono-serde** (23 lenient): the 7 above plus `+0100`, `…:00 Z`, `…:00UTC`, 2-digit year,
  `+2024`, `-0001`, 1-digit month/day/hour/minute, trailing `\n`/space/`\r`/`\r\n`, leading space, and (new in the
  310-vector set) a 1-digit second `2020-01-01T00:00:0.5Z` (3339-A-004, read as 00:00:00.5).
- **time** (2 lenient): space and `_` separator (3339-5.6-015/018; any byte, see the notes at the top of this
  file). No wrong values: the leap seconds are interpretations (³).
- **jiff-timestamp** (17 lenient, 4 strict): space, `T12:00Z`, `+0100`, `+01`, `+24:00`, `,5`, basic format,
  `T120000`, offsets with seconds (3: `+01:00:00`, `-00:44:30` 3339-5.6-084, and the LMT offset `+00:09:21`
  3339-5.6-085, new: accepted as 1899-12-31T23:50:39Z), a suffix in the rfc3339 profile, `:60` anywhere (5). Too
  strict: `9999-12-31T23:59:59Z` (range) and >9 fraction digits (3). In the `both` run, add 21 lenient: critical
  inconsistent, unknown or unprocessable zones accepted (11, e.g. `+01:00[!Europe/Paris]`, `Z[!Mars/Olympus_Mons]`,
  `Z[!u-ca]`, and, new, critical zones named by a deprecated link, `+01:00[!US/Pacific]` 9557-3.4-034 and
  `+02:00[!Europe/Kiev]` 9557-3.4-037), experimental `_foo` keys (2), `[.]`, `[..]`, `[Europe/../Paris]` (3),
  `[+24:00]`, `[+0500]`, `-00:44:30[Europe/Dublin]`, `T00:00+01:00[…]` (no seconds) and an unshifted leap second;
  and 2 too strict: `[!u-ca=gregory]`, `[!u-ca=hebrew][!u-ca=hebrew]`. `Zoned` with `Reject` rejects
  9557-3.4-034/-037 (pass); the other policies resolve them (interpretation).
- **jiff-zoned reject** (6 lenient, 6 strict): no seconds, no offset, bare date + zone, `[+24:00]`, `[+0500]`,
  unshifted leap second. Too strict: `-00:00[!Europe/London]`, `[!u-ca=gregory]`,
  `[!u-ca=hebrew][!u-ca=hebrew]`, >9 fraction digits (3).
- **jiff-zoned other policies**: `-00:00[!Europe/London]` now passes. The 8 critical-inconsistency vectors
  (including 9557-3.4-034/-037) become interpretations ("resolved by programmed behaviour").
  `0000-01-01T00:00:00+01:00[!Europe/Paris]` and `…-00:44:30[Europe/Dublin]` are accepted (2 extra too lenient).

**Interpretation choices (recorded, not graded):**

| Choice | chrono | time | jiff Timestamp | jiff Zoned (Reject) |
|---|---|---|---|---|
| Leap-second policy | grammar only (`:60` anywhere, kept as leap) | `any-month-end` with offset shift, → `:59.999999999` | grammar only, → `:59` | grammar only, → `:59` |
| Unknown elective tag / `u-ca=klingon` | n/a (rejects all suffixes) | n/a | ignored | ignored ² |
| Duplicate elective keys | n/a | n/a | accepted; value not exposed | accepted; value not exposed ² |
| Elective inconsistent zone (`+01:00[Europe/Paris]`) | n/a | n/a | ignored (offset wins) | rejected |
| Unknown elective zone (`Z[Mars/Olympus_Mons]`) | n/a | n/a | accepted (zone ignored) | rejected |
| Zone-name case (`[!europe/paris]`) | n/a | n/a | accepted | accepted (case-insensitive) |
| `Z[!+08:45]`, `Z[+05:00]` | n/a | n/a | accepted | accepted (`Z` never conflicts) |
| `-00:00[+01:00]` | n/a | n/a | accepted | rejected (`-00:00` read as `+00:00`) |

² Probed with a zone (`…+02:00[Europe/Paris][u-ca=chinese][u-ca=japanese]` accepted); the vector forms have no
zone and are n/a for `Zoned`.

**Fields:** the adapter prints `year…second`, `secfrac`, `offset_minutes` and `leap_second` from the target's
value (chrono, time), or from the target's instant re-expressed at the offset jiff parsed (jiff).
`offset_unknown` and `time_zone` (with `critical`) come from jiff's own `DateTimeParser::parse_pieces`,
because `Timestamp` and `Zoned` keep neither. `effective_tags` is **not accessible** in jiff (it drops
non-zone annotations after the syntax check) and does not exist in chrono or time.

Raw per-input results: `probes/rust/tables-full.md`. Probe source: `probes/rust/` (`rfc-eval/` adapters, `bracket_probe.py`, `validate_producers.py`, `producer_table.py`).

## Detect in code

Grep patterns (ERE). A hit is a lead: confirm it with the probe named in "Why". `rfcdt.py scan` now has 8 Rust rules
(`SCAN-RS-*`, added after this probe). Before them, on a Rust sample it caught `.format("…%SZ")` and `%z`, but missed chrono
`"%S%.3fZ"`, time `"[second]Z"`, `.to_string()`, `.parse::<DateTime<…>>()`, `Iso8601::DEFAULT` and jiff
`Timestamp` parsing (`probes/rust/scan-sample/sample.rs`).

**Strict check in Rust:** run the portable regex (`README.md`, "Portable strict check") on `&str` before the parser. Use `[0-9]`, not `\d`
(the `regex` crate's `\d` is Unicode unless you use `(?-u)`), and anchor with `^…$` or `\A…\z`. *(regex-crate
behaviour: from docs, not probed here; the `regex` crate was not in the pinned set.)* Then:
`DateTime::parse_from_rfc3339(s)` (chrono), or `OffsetDateTime::parse(s, &Rfc3339)` (time; its §5.7 leap
check is correct), or for IXDTF, `s.parse::<jiff::Zoned>()` with the default `Reject`.

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `\.parse::<\s*(chrono::)?DateTime<` · `DateTime::<[A-Za-z]+>::from_str\(` · `DateTime<(Utc\|FixedOffset\|Local)>` fields in `#[derive(Deserialize)]` structs | `FromStr` (and so serde) accepts `+0100`, 1-digit fields, `24-01-01…` (year 24), `…:00UTC`, `…:00 Z`, leading/trailing whitespace incl. `\n`, `+10000`, `-0001`, and `:60` anywhere | `DateTime::parse_from_rfc3339` behind the strict regex. For serde: `#[serde(deserialize_with = "…")]` that calls it |
| `DateTime::parse_from_rfc3339\(` used as a *validator* | Accepts a space, U+2212 `−` as the sign, and `:60` on any date and minute and at an unshifted offset | the strict regex + your own leap-second rule |
| `parse_from_str\([^)]*%(z\|:z\|\+)` | `%:z` rejects `Z` and `z` (**TOO STRICT** on `…12:00:00Z`) and accepts `+0200`. `%+` is as lenient as `FromStr` | `parse_from_rfc3339` |
| `NaiveDateTime::parse_from_str\([^)]*Z['"]` | A literal `Z`: the offset is discarded (naive result). It rejects `+00:00`, `z` and fractions | `parse_from_rfc3339(s)?.with_timezone(&Utc)` |
| `\.to_rfc3339\(\)` | Prints `+00:00` for UTC (`Z` only with `to_rfc3339_opts(_, true)`). With a sub-minute `FixedOffset` it rounds the offset but keeps the wall time: `-00:44:30` → `11:15:30-00:45`, **30 s wrong** | `dt.with_timezone(&Utc).to_rfc3339_opts(SecondsFormat::AutoSi, true)` |
| `FixedOffset::(east\|west)(_opt)?\([^)]*[0-9]` where the seconds are not a multiple of 60 · `local_minus_utc\(\) % 60` | Same rounding in `to_rfc3339`, `to_rfc3339_opts` and serde (**WRONG VALUE**). `Display` prints `-00:44:30` (outside the grammar) | convert to `Utc` before serializing |
| `\.to_string\(\)\|format!\("\{\}"` on `DateTime`, `NaiveDateTime`, `OffsetDateTime`, `Zoned` | chrono: `2026-09-24 12:00:00 UTC`. time: `2026-09-24 12:00:00.0 +00:00:00`. jiff `Zoned`/`Timestamp`: conforming (but see LMT below) | chrono `to_rfc3339_opts`, time `format(&Rfc3339)` |
| `NaiveDateTime` in `#[derive(Serialize)]` structs · `naive_utc\(\)\|naive_local\(\)` before `.format(` | serde prints `2026-09-24T12:00:00` (no offset) | `DateTime<Utc>` fields |
| `\.format\("[^"]*%z"` · jiff `strftime\("[^"]*%z"` · time `\[offset_hour[^]]*\]\[offset_minute` | `+0200` without a colon | `%:z`, or the RFC 3339 formatters |
| `\.format\("[^"]*%S(%\.?[0-9]?f)?Z"` · time `\[second\](\[subsecond[^]]*\])?Z` | A literal `Z` on local or offset wall time: `08:00:00Z` for 12:00Z (New York); time printed `14:00:00Z` for a `+02:00` value | chrono `to_rfc3339_opts(_, true)` on a `DateTime<Utc>`; time `to_offset(UtcOffset::UTC).format(&Rfc3339)` |
| `OffsetDateTime::parse\([^,]+,\s*&(well_known::)?Rfc3339\)` · `time::serde::rfc3339` | Correct except the separator: **any byte** is accepted (`X`, `_`, `-`, `\n`, NUL, a digit) | the strict regex, or check `s.as_bytes()[10]` is `T`/`t` |
| `Iso8601::DEFAULT` · `well_known::Iso8601` on the parse side | ISO 8601, not RFC 3339: `+24:00`, `+0200`, `+02`, `,5`, `T12:00Z`, basic, week and ordinal dates. Rejects `t`/`z` | `Rfc3339` |
| `#\[derive\([^)]*Serialize` with an `OffsetDateTime` field and no `#\[serde\(with = "time::serde::rfc3339"` | Default serde form is a JSON array `[2026,267,12,0,0,0,0,0,0]` | `#[serde(with = "time::serde::rfc3339")]` |
| `format\(&Rfc3339\)` / `time::serde::rfc3339` on values with offset seconds or year < 0 | Returns `Err` (safe) but can fail at runtime for LMT offsets or negative years | `to_offset(UtcOffset::UTC)` first, and a year range check |
| `\.parse::<\s*(jiff::)?Timestamp>\(\|Timestamp::from_str\(` · `jiff::Timestamp` fields deserialized from IXDTF | Ignores the zone annotation even when critical (`+05:00[!Europe/Paris]`, `Z[!Mars/Olympus]` accepted: **VIOLATES 9557 MUST**). Also accepts `+02`, `+0200`, `+24:00`–`+25:59`, `-00:44:30`, `T12:00Z`, `,5`, basic format, `+002026`, `:60` anywhere | Plain RFC 3339: the strict regex first. When a suffix may be present: `Zoned::from_str` |
| `\.parse::<\s*(jiff::)?Zoned>\(\|parse_zoned\(` on untrusted input | Grammar leniencies as for `Timestamp`, plus a missing offset (`…T00:14:07[Europe/Paris]`) and a bare date. `-00:00[zone]` is rejected. Experimental `[_k=v]` accepted | the strict regex on the part before `[`, and reject `[_…=…]` unless configured |
| `offset_conflict\(\s*OffsetConflict::(AlwaysOffset\|AlwaysTimeZone\|PreferOffset)` | Silently resolves **critical** inconsistencies too. `AlwaysTimeZone`/`PreferOffset` put `-00:00[Europe/London]` **1 h off** | keep the default `Reject`. If you must resolve, check `Pieces::parse(s)?.time_zone_annotation()?.is_critical()` first |
| jiff `Zoned` `Display`/`to_string()` · `display_with_offset\(` for historical instants or `TimeZone::fixed` with seconds | Offsets are rounded to the minute and the wall time is kept: `1969-12-31T23:15:30-00:45[Africa/Monrovia]` is 1970-01-01T00:00:30Z to any RFC 3339 reader (jiff's own `Timestamp::from_str` included). jiff `Zoned` re-reads it correctly | send `zdt.timestamp()` (UTC, `Z`) to RFC 3339 consumers |
| jiff `Zoned` `Display` as a round-trip format | Drops the `!` and all tags (`[u-ca=hebrew]`) | keep the original string if the tags matter |
| `DateTimePrinter::new\(\)[^;]*\.(lowercase\(true\)\|separator\(b' '\))` | Prints `t`/`z` (SHOULD be upper case) or a space separator (outside the grammar) | the default printer |
| `TimeZone::fixed\(` then `Zoned` `Display` | Prints `…+05:00[+05:00]`: an offset time zone copied from the offset (Advisory, §1.2) | `zdt.timestamp().display_with_offset(zdt.offset())` for plain RFC 3339 |
| Year range: chrono `to_rfc3339`/serde, jiff `Display` | chrono prints `+10000-…` and `-0001-…`. jiff prints `-000001-…` (**WRONG OUTPUT**). time refuses (Err) | range-check the year to 0000–9999 |

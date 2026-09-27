# Ecosystem: how common date-time APIs deviate from RFC 3339 / RFC 9557

Reference for the skill's code hotspots (`references/hotspots.md`). It says which library calls are likely to
break RFC 3339 §5.6/§5.7 or RFC 9557 §3–4, what they actually do (probed), and what to use in their place.
Read this file first, then only the file for the target's language.

**Evidence rule.** Every verdict comes from a probe that was run: 2026-09-24 for Python, Node, Java, .NET and Ruby;
2026-09-25 for Go, Rust, Swift, SQLite, PostgreSQL, protobuf and the JSON Schema validators. Claims that could
not be run are marked **unverified (from docs)** with the URL that was read. Re-probe the target's actual version
before you rely on a row. The probe programs are in `probes/` and read the same inputs, `probes/inputs.json`
(59 strings). Rule numbers ("rule 1", "rule 2") refer to `references/interpretation.md`.

**Common environment:** macOS arm64, host `TZ=America/New_York` (a non-UTC zone shows the "silently local"
defaults), system tzdata 2026c.

## File map

| File | Covers | Versions probed |
|---|---|---|
| `python.md` | `datetime`, `strptime`, dateutil, pydantic, jsonschema + rfc3339-validator | Python 3.13.9, python-dateutil 2.9.0.post0, pydantic 2.13.5, jsonschema 4.26.0, rfc3339-validator 0.1.4 |
| `javascript.md` | `Date`, `Temporal` (`Instant`, `ZonedDateTime`, `PlainDateTime`), ajv-formats | Node 26.8.1 / V8 14.6 (native Temporal), ajv 8.20.0, ajv-formats 3.0.1 |
| `java.md` | `java.time` (`OffsetDateTime`, `ZonedDateTime`, `Instant`, `ofPattern`), `SimpleDateFormat` | Temurin 25.0.1 |
| `dotnet.md` | `DateTime(Offset).Parse/ParseExact`, `System.Text.Json`, `XmlConvert`, format strings | .NET SDK 10.0.300 / runtime 10.0.8 |
| `ruby.md` | `Time.iso8601/parse/strptime/new`, `DateTime` | Ruby 3.4.7 |
| `go.md` | `time.Parse`, `UnmarshalJSON/Text`, `encoding/json` v1 and v2, `Format` layouts; vector runs | Go 1.27.1 (standard library) |
| `rust.md` | chrono, time, jiff (`Timestamp`, `Zoned`, `OffsetConflict`); vector runs | Rust 1.98.1, chrono 0.4.45, time 0.3.55, jiff 0.2.37, serde_json 1.0.151 |
| `swift.md` | `ISO8601DateFormatter`, `Date.ISO8601FormatStyle`, `JSONDecoder/Encoder`, `DateFormatter`; vector runs | Swift 6.4, macOS 27.0 Foundation |
| `sql.md` | SQLite date functions; PostgreSQL `timestamptz`/`timestamp`, `to_char`, `to_timestamp`, `to_json`, SQL/JSON `.datetime()`; MySQL (unverified) | SQLite 3.51.0, PostgreSQL 17.11 (psycopg 3.3.6) |
| `protobuf.md` | `google.protobuf.Timestamp` JSON mapping as a stated profile; Go `protojson`, Python `json_format` | protobuf (Python) 7.36.2, `google.golang.org/protobuf` v1.36.12 |
| `jsonschema.md` | `format: date-time/date/time` assertion in 4 validators; openapi-generator client defaults | santhosh-tekuri/jsonschema v6.0.3, networknt 3.0.7 (+ itu 1.14.0), JsonSchema.Net 9.4.0, jsonschema 4.26.0, openapi-generator 7.25.0 |
| `servicenow.md` | Pointer to `references/servicenow.md` (Glide, REST, Fluent SDK) | Fluent SDK 4.13.0 (offline); instance rows unverified |

Each language file has: notes the matrix cannot show, per-API consumer tables, producer (formatter) tables, grep
patterns with safe replacements ("Detect in code"), and conformance-vector results. Every language was re-run on
2026-09-26 against the current 310 vectors (`probes/run_vector_probes.py`; baselines in
`evals/baselines/probes/vector-runs/<lang>.txt`), and the vector counts in those files are for that set (earlier
Go/Rust runs used 274). Vector results are graded by `references/interpretation.md` "Grading vector results": a
space separator without a stated profile is too lenient, a leap second stored as :59 or as :00 of the next minute
is an INTERPRETATION (leap-second representation), and a fraction truncated or rounded to the API's precision
passes. A table row whose input no vector covers is marked "legacy probe only".

## How to read the verdicts

The verdicts are for a component that claims to handle an RFC 3339 `date-time`. For bracket-aware APIs
(Temporal, Java `ZonedDateTime`, `ISO_DATE_TIME`, jiff `Timestamp` and `Zoned`), the verdicts are for an RFC 9557
(IXDTF) consumer.

| Verdict | Meaning |
|---|---|
| conforming | Accepts a grammar-valid input and gives the same instant, or rejects an input that is not valid. |
| conforming (lossy: …) | Accepts, but the value is truncated or rounded to the API's precision. The RFC puts no limit on precision (`time-secfrac = "." 1*DIGIT`), so this is a local matter. Record it. |
| **TOO LENIENT** | Accepts a string that is not an RFC 3339 `date-time`. The notes in parentheses tell you what value it made (for example, host-local time or a rolled-over date). |
| too lenient (space; OK only under a stated profile) | Accepts the space separator with no stated profile. The space is outside the ABNF; the §5.6 NOTE lets an application *profile* choose it, and erratum 5783 is Held. Without such a profile it is TOO LENIENT (rule 1 grades the severity). |
| lenient (accepts suffix) | A parser that knows only RFC 3339 accepts an RFC 9557 suffix. For an RFC 3339 `date-time` this is TOO LENIENT (trailing characters; vector 3339-5.6-062), shown as **L** in the matrix; it is worse when the suffix is silently dropped. |
| **TOO STRICT** | Rejects a grammar-valid string. |
| too strict (offset range / range limit / no leap second) | Rejects a grammar-valid value because of a platform range limit: offsets above ±14 h or ±18 h, year 0000, or second 60. These are common and are usually accepted as a documented limitation. |
| **WRONG VALUE** | Accepts, but gives a different instant. For a producer: the string does not denote the true instant. |
| **WRONG OUTPUT** | The producer's string does not match the RFC 3339 / RFC 9557 ABNF. |
| **VIOLATES 9557 MUST** | An IXDTF consumer accepted a critical (`!`) suffix that it must treat as an error (§3.3, §3.4). |
| n/a | The API requires a `[time-zone]` annotation by design (Temporal `ZonedDateTime`, jiff `Zoned`). |
| refuses (safe) | A producer returns an error instead of printing an invalid or wrong string (Go `MarshalJSON` for year 10000, the Rust `time` crate for offset seconds). The caller must handle the error. |

Category decisions used for the inputs:
- Lowercase `t`/`z` are **valid** (§5.6 NOTE).
- `-00:00` is valid. RFC 9557 §2 makes it equal to `Z`.
- Offsets up to `+23:59` are valid by grammar. `+24:00` and `+23:60` are invalid.
- `T24:00:00` is invalid (`time-hour` is 00–23).
- Second `60` is valid only at the end of a month that has a leap second, shifted by the offset (§5.7).
  `2016-12-31T23:59:60Z` and `2016-12-31T18:59:60-05:00` are real leap seconds. `2026-09-24T23:59:60Z` is not.
- Any count of fraction digits is valid. A comma decimal sign is invalid.
- A missing seconds field, a missing offset, the basic format, week dates, ordinal dates, 5-digit years and signed years are invalid.
- Year `0000` is grammar-valid, so rejecting it gets "range limit".
- An RFC 9557 elective inconsistency (`+05:00[Europe/Paris]` in January) is a **MAY** (§3.4). The critical form is a **MUST act**.

## At a glance (consumers)

`✓` conforming · `✓~` lossy · **L** too lenient (in the `space` column: OK only under a stated profile) · **S** too strict · s range/leap-second limit ·
**W** wrong value · **!!** violates RFC 9557 MUST · – n/a. Columns are probe IDs from `inputs.json`:
`lc-z`=`…12:00:00z`, `space`=`2026-09-24 12:00:00Z`, `off-nocolon`=`+0200`, `no-sec`=`T12:00Z`,
`no-off`=`T12:00:00` (no offset), `comma`=`,5`, `h24`=`T24:00:00Z`, `leap-real`=`2016-12-31T23:59:60Z`,
`leap-fake`=`2026-09-24T23:59:60Z`, `feb30-2024`, `frac12`=12 fraction digits, `trail-ws`=trailing `\n`,
`y+10000`=`+10000-01-01…`, `x-tz`=`+02:00[Europe/Paris]`, `x-unk!`=`Z[!x-foo=bar]`,
`x-incons!`=`2026-01-01T00:00:00+05:00[!Europe/Paris]`.

| API | `lc-z` | `space` | `off-minus0` | `off-nocolon` | `no-sec` | `no-off` | `comma` | `h24` | `leap-real` | `leap-fake` | `feb30-2024` | `frac12` | `trail-ws` | `y+10000` | `x-tz` | `x-unk!` | `x-incons!` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dotnet: `DateTime.Parse(s, Invariant)` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | s | ✓ | ✓ | ✓~ | **L** | ✓ | ✓ | ✓ | ✓ |
| dotnet: `DateTime.Parse(s, Invariant, RoundtripKind)` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | s | ✓ | ✓ | ✓~ | **L** | ✓ | ✓ | ✓ | ✓ |
| dotnet: `DateTimeOffset.Parse(s, Invariant)` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | s | ✓ | ✓ | ✓~ | **L** | ✓ | ✓ | ✓ | ✓ |
| dotnet: `DateTimeOffset.ParseExact(s, "o")` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| dotnet: `DateTimeOffset.ParseExact(s, "yyyy-MM-dd'T'HH:mm:ssK")` | **S** | ✓ | ✓ | **L** | ✓ | **L** | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| dotnet: `DateTimeOffset.ParseExact(s, "yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK")` | **S** | ✓ | ✓ | **L** | ✓ | **L** | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| dotnet: `JsonSerializer.Deserialize<DateTimeOffset>` | **S** | ✓ | ✓ | ✓ | **L** | **L** | ✓ | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| dotnet: `JsonSerializer.Deserialize<DateTime>` | **S** | ✓ | ✓ | ✓ | **L** | **L** | ✓ | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| dotnet: `XmlConvert.ToDateTimeOffset (xsd:dateTime)` | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | s | ✓ | ✓ | ✓~ | **L** | ✓ | ✓ | ✓ | ✓ |
| java: `OffsetDateTime.parse (ISO_OFFSET_DATE_TIME)` | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `ZonedDateTime.parse (ISO_ZONED_DATE_TIME)` | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `Instant.parse (ISO_INSTANT)` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | **L** | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `DateTimeFormatter.ISO_DATE_TIME -> Instant.from` | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX") [SMART]` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | s | ✓ | **L** | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `ofPattern("uuuu-MM-dd'T'HH:mm:ss[.SSSSSSSSS]XXX").STRICT` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'") -> LocalDateTime` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | **L** | s | ✓ | **L** | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| java: `SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX") [lenient default]` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | **S** | **L** | ✓ | **L** | **L** | **L** |
| java: `SimpleDateFormat.parse, then check ParsePosition==len` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| javascript: `Date.parse / new Date(s)` | ✓ | **L** | ✓ | **L** | **L** | **L** | ✓ | **L** | s | ✓ | **L** | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| javascript: `Temporal.Instant.from` | ✓ | **L** | ✓ | **L** | **L** | ✓ | **L** | ✓ | ✓ | **L** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | **!!** |
| javascript: `Temporal.ZonedDateTime.from` (b) | – | ✓ | – | ✓ | **L** | **L** | ✓ | ✓ | – | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| javascript: `Temporal.ZonedDateTime.from({offset:'reject'}) [default]` (b) | – | ✓ | – | ✓ | **L** | **L** | ✓ | ✓ | – | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| javascript: `Temporal.ZonedDateTime.from({offset:'use'})` (b) | – | ✓ | – | ✓ | **L** | **L** | ✓ | ✓ | – | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| javascript: `ajv-formats format:date-time (full)` | ✓ | **L** | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| javascript: `ajv-formats format:date-time (mode:'fast')` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `datetime.fromisoformat` | **S** | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `strptime('%Y-%m-%dT%H:%M:%S%z')` | **S** | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `strptime('%Y-%m-%dT%H:%M:%S.%f%z')` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `strptime('%Y-%m-%dT%H:%M:%SZ')` | **W** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `dateutil.parser.isoparse` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | **L** | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `dateutil.parser.parse` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | s | ✓ | ✓ | ✓~ | **L** | ✓ | ✓ | ✓ | ✓ |
| python: `pydantic TypeAdapter(datetime).validate_python` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `pydantic TypeAdapter(AwareDatetime).validate_json` | ✓ | **L** | ✓ | **L** | **L** | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: `jsonschema FormatChecker date-time (rfc3339-validator)` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ |
| ruby: `Time.iso8601 / Time.xmlschema` | ✓ | ✓ | ✓ | **L** | ✓ | **L** | ✓ | **L** | ✓ | **L** | **L** | ✓ | **L** | ✓ | ✓ | ✓ | ✓ |
| ruby: `DateTime.rfc3339` | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | **L** | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ |
| ruby: `DateTime.iso8601` | ✓ | ✓ | ✓ | **L** | **L** | **L** | **L** | **L** | ✓ | **L** | ✓ | ✓ | **L** | **L** | ✓ | ✓ | ✓ |
| ruby: `Time.parse` | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | **L** | ✓ | **L** | **L** | ✓ | **L** | **L** | **L** | **L** | **L** |
| ruby: `Time.strptime('%Y-%m-%dT%H:%M:%S%z')` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | **S** | **L** | **L** | **L** | **L** | **L** |
| ruby: `Time.new(s) [Ruby 3.2+ string form]` | **S** | **L** | ✓ | **L** | ✓ | **L** | ✓ | **L** | ✓ | **L** | **L** | ✓~ | ✓ | **L** | ✓ | ✓ | ✓ |
| go: `time.Parse(time.RFC3339)` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| go: `time.Parse(time.RFC3339Nano)` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| go: `time.ParseInLocation(time.RFC3339, s, time.Local)` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| go: `(*time.Time).UnmarshalJSON` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| go: `(*time.Time).UnmarshalText` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| go: `json.Unmarshal into struct{T time.Time}` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| go: `encoding/json/v2 Unmarshal into struct{T time.Time}` | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `chrono DateTime::parse_from_rfc3339` | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `chrono DateTime::<Tz>::from_str` / serde `Deserialize` `DateTime<Utc\|FixedOffset>` | ✓ | L | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓~ | **L** | **L** | ✓ | ✓ | ✓ |
| rust: `chrono DateTime::parse_from_str(s, "%+")` | ✓ | **L** | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓~ | ✓ | **L** | ✓ | ✓ | ✓ |
| rust: `chrono DateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f%:z")` | **S** | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `chrono NaiveDateTime::parse_from_str(s, "…%SZ")` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| rust: `time OffsetDateTime::parse(s, &Rfc3339)` / `time::serde::rfc3339` | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `time OffsetDateTime::parse(s, &Iso8601::DEFAULT)` | **S** | ✓ | ✓ | **L** | **L** | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `jiff Timestamp::from_str` | ✓ | **L** | ✓ | **L** | **L** | ✓ | **L** | ✓ | ✓ | **L** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | **!!** |
| rust: `jiff Zoned::from_str` (default `OffsetConflict::Reject`) (b) | ✓ | **L** | **S** | **L** | **L** | **L** | **L** | ✓ | ✓ | **L** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `jiff DateTimeParser.offset_conflict(AlwaysOffset).parse_zoned` (b) | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | ✓ | ✓ | **L** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| rust: `jiff …offset_conflict(AlwaysTimeZone \| PreferOffset).parse_zoned` (b) | ✓ | L | **W** | **L** | **L** | **L** | **L** | ✓ | ✓ | **L** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `ISO8601DateFormatter() [default: .withInternetDateTime]` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | s | ✓ | **L** | **S** | **L** | ✓ | **L** | **L** | **L** |
| swift: `ISO8601DateFormatter [.withInternetDateTime, .withFractionalSeconds]` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **W** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `ISO8601DateFormatter: try .withFractionalSeconds, then default` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | s | ✓ | **L** | **W** | **L** | ✓ | **L** | **L** | **L** |
| swift: `Date(s, strategy: .iso8601)` / `JSONDecoder .iso8601` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | **S** | **L** | ✓ | **L** | **L** | **L** |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX")` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX")` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX", isLenient=true)` | ✓ | **L** | ✓ | **L** | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss'Z'") [default TZ]` | **S** | ✓ | **S** | ✓ | ✓ | **L** | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(th_TH, "yyyy-MM-dd'T'HH:mm:ssXXXXX") [no en_US_POSIX]` | **W** | ✓ | **W** | **L** | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `parseRFC3339Strict` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| json-schema (go): santhosh-tekuri/jsonschema/v6 `AssertFormat()` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| json-schema (java): networknt 3.0.7 (itu, default) | ✓ | L | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **S** | **L** | ✓ | ✓ | **L** | ✓ |
| json-schema (java): networknt 3.0.7 (no itu: `OffsetDateTime.parse`) | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ |
| json-schema (dotnet): JsonSchema.Net `RequireFormatValidation` | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ |
| json-schema (python): jsonschema `FORMAT_CHECKER` + rfc3339-validator | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ |
| json-schema (python): jsonschema `FORMAT_CHECKER`, no rfc3339-validator | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | **L** | ✓ | **L** | **L** | ✓ | **L** | **L** | **L** | **L** | **L** |

`(b)` on a jiff `Zoned` or Temporal `ZonedDateTime` row: that API requires a `[time-zone]`, so the cell is for
the probe string with a consistent suffix added (`…Z[Europe/Paris]`, `…+02:00[+02:00]`). For `ZonedDateTime` the
`no-sec` and `no-off` cells come from the vectors: it accepts `…T12:00[…]` (9557-1.2-002) and `…T12:00:00[…]` with
no offset (9557-4.1-040), and also a date only (9557-4.1-045); see `javascript.md`. jiff `Timestamp` parses the
suffix, so it is graded as an IXDTF consumer.

Swift rows (2026-09-25): every Foundation parser also reads dates before 1582-10-15 in the Julian calendar
(`0001-01-01T00:00:00Z` → 2 days early), a column not shown here; see `swift.md`. `json-schema` rows (2026-09-25):
validators with format assertion turned on. A validator only accepts or rejects, so any accepted suffix is
**L** (a suffix is outside `date-time`). SQL engines and protobuf have no matrix rows; see `sql.md` and
`protobuf.md`.

## Portable strict check (use it in front of any lenient parser)

The grammar is RFC 3339 §5.6. Use ASCII `[0-9]`, not `\d`, and match the whole string: use `fullmatch`, `\A…\z`,
or `^…$` in JavaScript without the `m` flag. In Python, `$` also matches before a final `\n`.

```
[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])
```

After the regex:
1. Check the day of the month against month and year (§5.7).
2. Allow `:60` only at 23:59 UTC on a leap-second date (after you apply the offset), or document that you reject leap seconds.
3. Then call the platform parser.

This regex matched exactly the grammar-valid probe strings. For an IXDTF, first remove the suffix
`(\[!?[^\]=]+\]|\[!?[a-z_][a-z0-9_-]*=[A-Za-z0-9]+(-[A-Za-z0-9]+)*\])*` and handle it separately (critical flags!).

## Top 10 real-world defects (all languages)

Ranked by harm (a wrong instant, or bad input silently accepted at a boundary, first) and by how often the API is
used. Grades follow `references/interpretation.md` rule 1. Each item names the language files with the evidence.

1. **Timestamps sent with no offset.** Naive or "unspecified" values serialized as `2026-09-24T12:00:00` (the
   `time-offset` is mandatory). Python `naive.isoformat()` / `utcnow()`, pydantic `dump_json(naive)`, protobuf
   `ToDatetime()` then `isoformat()`; .NET `DateTime(Unspecified).ToString("o")`, `System.Text.Json` and the
   openapi-generator C# converter; Java `LocalDateTime` / `ISO_DATE_TIME`; Temporal `PlainDateTime`; Go
   `Format(time.DateTime)`; chrono `NaiveDateTime`, jiff `civil::DateTime`; PostgreSQL `timestamp` `::text` and
   `to_json(v AT TIME ZONE 'UTC')`; SQLite `datetime()` / `CURRENT_TIMESTAMP`.
2. **The offset is invented or thrown away on input: a wrong instant.** A missing offset read as host-local time:
   JS `Date.parse` and openapi `typescript-fetch`, .NET `DateTimeOffset.Parse` / `ParseExact(…K)` / `XmlConvert`,
   Ruby `Time.iso8601` / `Time.new`, Go `ParseInLocation(zone-less layout, time.Local)`, Swift `DateFormatter`
   with a literal `'Z'` (12:00Z read as 16:00Z). Read as the **session** zone: PostgreSQL `::timestamptz`,
   `to_timestamp`, `.timestamp_tz()`. Read as UTC: SQLite, openapi C# `AssumeUniversal`, protobuf Python
   `FromDatetime(naive)`. Discarded: PostgreSQL `timestamp` without time zone keeps the wall time of
   `…+05:30` (15 wrong-instant vectors), Temporal `PlainDateTime.from`, chrono `NaiveDateTime` with `…%SZ`.
3. **Validation that is weaker than its name.**
   - JSON Schema `format` is annotation-only in 2020-12: all four validators accepted `"not a date"` without an
     assertion option, and moving a schema from draft-07 to 2020-12 silently turns the check off in Go and Java.
     python-jsonschema without `rfc3339-validator` checks nothing even with `FORMAT_CHECKER` (88 of 147 vectors
     too lenient). networknt + itu accepts **any text after `Z`**; santhosh-tekuri accepts signed fields
     (`T+1:00:00Z`); rfc3339-validator, JsonSchema.Net and itu accept `…Z\n`, and a `^…$` `pattern` does not stop it
     on Python or .NET (`jsonschema.md`).
   - Go: the strict RFC 3339 checks are dead code (issue 54580), so `time.Parse(time.RFC3339)`,
     `UnmarshalJSON/Text`, `encoding/json` v1 and `protojson` accept `+24:00`, `+23:60`, `+24:60` (as +25:00), `,5`
     and `T1:00:00Z`. Only `encoding/json/v2` is strict (`go.md`, `protobuf.md`).
   - chrono serde / `FromStr` accepts 23 invalid vector forms (of 147 scored); the time crate `Rfc3339` accepts any byte as the
     separator (`rust.md`).
   - Swift `ISO8601DateFormatter` and `Date(s, strategy: .iso8601)` ignore trailing text (`…Zgarbage`); the
     formatter reads `+24:00` as `+02:00` and `12024-…` as year 2024 (`swift.md`).
   - protobuf Python parses the offset with `int()` and the fraction with `float()`: `+-1:00` gives a
     sign-inverted instant, `+99:99` and `.1e-3` are accepted (`protobuf.md`).
   - PostgreSQL `::timestamptz` (41 too-lenient vectors) and SQLite `datetime(s) IS NOT NULL` used as validators
     (`sql.md`); Python `strptime` and Ruby `Time.parse` accept Arabic-Indic digits.
   - Precision limits are uneven and mostly silent: .NET `ParseExact("o")` needs exactly 7 digits, `%f` and SQL/JSON
     `.datetime()` take at most 6 (and `.datetime()` reads `.0000001Z`…`.000000000001Z` as `.000001`, a wrong
     value; 3339-5.6-006), Java, Temporal, jiff and Swift `ISO8601FormatStyle` at most 9; Go, chrono, time,
     .NET, PostgreSQL (µs) and SQLite (ms) truncate or round without a signal.
4. **Format patterns that label or compute the wrong date** (Nonconformity: well-formed but wrong).
   - A literal `Z` on local or offset wall time: Python `strftime('…%SZ')`, .NET `ToString("…ssZ")`, Java
     `'Z'`, a Go layout ending `05Z"`, chrono `…%SZ`, the time crate `[second]Z`, Swift `DateFormatter "…ss'Z'"`,
     PostgreSQL `to_char(v, '…"Z"')` without `AT TIME ZONE 'UTC'`, SQLite `strftime('…Z', …, 'localtime')`.
   - Week-based or ISO-week years: `YYYY` in Java, Swift `DateFormatter`; `IYYY` in PostgreSQL. Wrong letters:
     PostgreSQL `HH` (12-hour), `MM` (month) for minutes.
   - Locale calendars and digits: .NET without `InvariantCulture` (Thai `2569`, Hijri), Swift `DateFormatter`
     without `en_US_POSIX` (`th_TH` prints `2569-…` and parses 2026 as 1483 CE).
   - Julian calendar before 1582: Java `SimpleDateFormat`, Ruby `DateTime`, and **every** Swift Foundation parser
     and formatter (`0001-01-01` is 2 days off; 1 BC prints as year 1). PostgreSQL `to_char` `YYYY` drops the era.
5. **Offsets that are not whole minutes give an invalid string or a wrong instant.** LMT and other pre-1972
   zones, and fixed offsets with seconds.
   - **Wrong instant:** the offset is truncated (Go `Format` / `MarshalJSON`, PostgreSQL `to_char` `TZH:TZM`) or
     rounded (chrono `to_rfc3339` / serde, jiff `Zoned`, Temporal) to the minute but the wall time is kept
     (Monrovia 1970: 30 s off; Paris 1850: 21 s). Ruby `xmlschema` drops the seconds.
   - **Invalid output:** Python `isoformat()`, Java `toString()`, chrono/time `Display`, jiff `%:z`, Swift
     `ISO8601DateFormatter` (`-00:44:30`), Swift `ISO8601FormatStyle` (`-004430`), PostgreSQL `::text` and
     `to_json` (`-00:44:30`).
   - **Safe:** the time crate `format(&Rfc3339)` returns `Err`. Swift `DateFormatter XXXXX` and
     `ISO8601DateFormatter` with a `secondsFromGMT` zone move the wall time with the rounding (right instant).
   Fix: convert to UTC before you serialize.
6. **Formatters that produce text outside the grammar.**
   - Seconds dropped: Java `OffsetDateTime` / `ZonedDateTime.toString()`.
   - No colon: `%z` (Python, Ruby, chrono, jiff), `SimpleDateFormat Z`, Go `-0700`, Swift `ISO8601FormatStyle`
     with any non-UTC zone (default `timeZoneSeparator: .omitted`), Swift `DateFormatter Z`; hour-only offsets from
     PostgreSQL `::text` and `to_char … OF` (`-04`).
   - Space separator: Python `str(dt)`, .NET `"u"`, Ruby `to_s`, Go `String()` / `time.DateTime`, chrono/time
     `Display`, Swift `description`, PostgreSQL `::text`, SQLite `datetime()`.
   - Signed or 5-digit years: `toISOString`, `Instant.toString`, `xmlschema`, Go `Format`, chrono, jiff, Swift,
     PostgreSQL `to_json` (`10000-…`, `… BC`, `"infinity"`).
   - Not a string at all: Swift `JSONEncoder()` default (`811944000`), the time crate's default serde (an array).
   - Out-of-range fields: Go `Format` prints offset hour 24 or 25 (`+24:00`), even for a value its own parser
     accepted from `+23:60`; chrono prints `:60` outside a leap-second position; SQLite echoes `24:00:00`.
7. **Invalid dates and times are silently normalized, not rejected.** V8 `Date.parse` (`2024-02-30` → `03-01`,
   `T24:00` → next day), Java `ofPattern` SMART (clamps to `02-29`), Ruby `Time.iso8601` (`04-31` → `05-01`),
   Swift Foundation (`02-30` → `03-01`; `ISO8601FormatStyle` also rolls `12:60`, `:61`, `:99`), SQLite
   (`02-30` → `03-01`, `24:00:00` echoed), PostgreSQL (`T24:00` → next day, `:60` → next second), Go (`+23:60` →
   `+24:00`, `+24:60` → `+25:00`), Ruby `DateTime.rfc3339` (`+24:00` → `+00:00`), ajv-formats `fast` (no range
   checks).
8. **RFC 9557 suffixes silently dropped, critical ones included** (a Nonconformity for any consumer that claims
   RFC 9557, §3.3/§3.4 MUST). `Temporal.Instant.from` and jiff `Timestamp::from_str` parse the suffix but ignore
   the zone even when critical (`+05:00[!Europe/Paris]`, `Z[!Mars/Olympus]`, and the link names
   `+01:00[!US/Pacific]`, `+02:00[!Europe/Kiev]`: 9557-3.4-034/-037). RFC 3339-only parsers that ignore
   trailing text drop any suffix: Swift `ISO8601DateFormatter` / `.iso8601`, networknt + itu (after `Z`), Ruby
   `Time.parse` / `strptime`, `SimpleDateFormat`, PostgreSQL `to_timestamp`. The zone-aware parsers
   (`Temporal.ZonedDateTime.from`, jiff `Zoned`, default reject policy) reject them; Go, SQLite, protobuf and
   PostgreSQL `::timestamptz` reject every suffix (correct for an RFC 3339 consumer).
9. **Leap seconds are handled one of two wrong ways.** Most parsers reject a real `2016-12-31T23:59:60Z` (Python,
   .NET, most of Java, JS `Date`, rfc3339-validator, every Go API, Swift `ISO8601DateFormatter`, SQLite, SQL/JSON,
   protobuf by profile). Others accept `:60` on **any** date without the §5.7 check: Java `Instant.parse` (a
   local 23:59:60 at any offset, while it rejects the real offset-shifted leap seconds; 3339-5.7-033/-034,
   3339-5.8-004), lenient `SimpleDateFormat` (any minute, rolled over), Temporal, Ruby, ajv, chrono, jiff, Swift `ISO8601FormatStyle`, PostgreSQL (any minute), and the Go and .NET
   JSON Schema validators (23:59 UTC on any date). Only the Rust time crate `Rfc3339` does the §5.7 check with the
   offset shift.
10. **Other RFC 9557 suffix and `Z` handling is inconsistent.** Java `ZonedDateTime.parse` rejects any `!` and
    every elective `[key=value]` tag. jiff `Zoned` reads `-00:00` as `+00:00` (1 h wrong with `AlwaysTimeZone` /
    `PreferOffset`), accepts experimental `[_foo=bar]`, rejects every critical tag. Temporal and jiff drop the `!`
    when they print again. networknt + itu rejects `-00:00` (valid; equal to `Z` under RFC 9557 §2). Producers
    that never emit `Z` for an unknown local offset (PostgreSQL `to_json` under UTC gives `+00:00`) or always emit
    `Z` (protobuf, by profile) are Advisories under rule 2.

## Not probed: unverified (from docs)

| Ecosystem | Claim | Where |
|---|---|---|
| MySQL / MariaDB | `DATETIME`/`TIMESTAMP` accept offsets only since 8.0.19 and discard them after converting; output is `YYYY-MM-DD hh:mm:ss` (space, no offset). **unverified (from docs)** | `sql.md`; https://dev.mysql.com/doc/refman/8.4/en/date-and-time-literals.html |
| Foundation on older OS releases, iOS, Linux | `.iso8601` decoding used `ISO8601DateFormatter` and rejected fractions. **unverified (from docs and issue reports)** | `swift.md` |
| openapi-generator libraries other than the defaults, and server generators | Not run. **unverified** | `jsonschema.md` |
| Rust `regex` crate | `\d` is Unicode unless `(?-u)`. **unverified (from docs)** | `rust.md` |
| ServiceNow instance behaviour | Every runtime claim is documented or "unverified (needs instance)" | `references/servicenow.md` |

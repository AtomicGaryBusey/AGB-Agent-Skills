# protobuf `google.protobuf.Timestamp` (ProtoJSON): RFC 3339 / RFC 9557 behaviour

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts). A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Environment and method

**Probed 2026-09-25**, macOS arm64, host `TZ=America/New_York`. Python 3.13.9 + `protobuf` 7.36.2 (pip; backend
`upb`, `api_implementation.Type()`; the pure-Python backend, `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`, gave
identical results on every input, because the Timestamp JSON code is Python in both) · Go 1.27.1 +
`google.golang.org/protobuf` v1.36.12 (`encoding/protojson`, `types/known/timestamppb`). Probe source:
`probes/protobuf/` (`probe_protobuf.py`, `go/main.go`, `compare_instants.py`). Probe inputs: `probes/inputs.json`
(59) plus protobuf-specific extras (`pb-*`, listed in the probe sources).

## The stated profile

**The stated profile.** protobuf is a declared *profile* of RFC 3339, not a general RFC 3339 consumer. The
contract is the comment on `message Timestamp` in `timestamp.proto` (read from
`types/known/timestamppb/timestamp.pb.go` v1.36.12):

> In JSON format, the Timestamp type is encoded as a string in the RFC 3339 format. That is, the format is
> "{year}-{month}-{day}T{hour}:{min}:{sec}[.{frac_sec}]Z" where {year} is always expressed using four digits while
> {month}, {day}, {hour}, {min}, and {sec} are zero-padded to two digits each. The fractional seconds, which can go
> up to 9 digits (i.e. up to 1 nanosecond resolution), are optional. The "Z" suffix indicates the timezone ("UTC");
> the timezone is required. A ProtoJSON serializer should always use UTC (as indicated by "Z") when printing the
> Timestamp type and a ProtoJSON parser should be able to accept both UTC and other timezones (as indicated by an
> offset).

`seconds` "Must be between -62135596800 and 253402300799 inclusive (which corresponds to 0001-01-01T00:00:00Z to
9999-12-31T23:59:59Z)"; `nanos` "Must be between 0 and 999,999,999 inclusive"; "All minutes are 60 seconds long.
Leap seconds are "smeared"". The range applies to the **instant**, after the offset is applied. The generated-code
comments in both runtimes add "Z-normalized … uses 0, 3, 6 or 9 fractional digits" for output.

So these RFC 3339 deviations are **profile-permitted** (grade them as documented limitations, not
Nonconformities): rejecting more than 9 fraction digits, rejecting `:60` (not representable), rejecting year `0000`
and any instant outside 0001-01-01T00:00:00Z … 9999-12-31T23:59:59.999999999Z (so `0001-01-01T00:00:00+01:00` and
`9999-12-31T23:59:59-01:00` are rejected, correctly), and rejecting lowercase `t`/`z` (the template spells `T` and
`Z`; this is a reading of the template, so it is a Review note, not a finding). Accepting input that the
template excludes (1-digit fields, a comma, an out-of-range offset) is **not** permitted by the profile either.

The Timestamp keeps only `(seconds, nanos)` in UTC. The input offset is discarded, and output is always `Z`
(Advisory, `interpretation.md` rule 2: `+00:00` and every other offset become `Z` on a round trip; the profile does this by
design, so a field that must keep the local offset needs a separate offset or zone field).

## Conformance vectors (`run_vectors.py`)

`vectors/vectors.json` with 310 vectors (2026-09-25 22:37 set), run with `run_vectors.py --target-kind rfc3339
--target-options fixed --target-has-tzdata yes` (147 scored, 6 interpretation, 157 skipped). The adapters return no `fields` (the target has no local fields or offset), so
WRONG VALUE was checked separately: `compare_instants.py --vectors` compared the instant of every accepted
grammar-valid vector with the instant rfcdt derives. **0 wrong instants** in 41 accepted valid vectors per
target; fractions up to 9 digits are exact. `probes/run_vector_probes.py --lang protobuf` now also runs
`probes/swift/instant_check.py` on the Go report (the `seconds`/`nanos` answer converted to a UTC instant): Go
`protojson`: **41 compared, 0 wrong, 0 lossy, 0 leap** (it rejects every `:60`), baseline
`evals/baselines/probes/vector-runs/protobuf.txt`. The Python rows are from the 2026-09-25 run: the current
baseline skips `protobuf-py` because the `protobuf` package was not installed on the re-run host.

| Target | pass/scored | TOO LENIENT | TOO STRICT | WRONG VALUE | Of the TOO STRICT: profile-permitted |
|---|---|---|---|---|---|
| go: `protojson.Unmarshal` → `timestamppb.Timestamp` | 124/147 (84.4%) | 4 | 19 | 0 | 19 (3 lowercase 3339-5.6-001…003, 2 year 0000 3339-5.6-004 / 3339-5.7-007, 3 fractions of more than 9 digits 3339-5.6-006 / -073 / -074, 11 leap seconds incl. `…60z` 3339-5.7-026) |
| python: `Timestamp.FromJsonString` | 116/147 (78.9%) | 12 | 19 | 0 | 19 (same set) |
| python: `json_format.Parse` into `Timestamp` | 116/147 (78.9%) | 12 | 19 | 0 | 19 (identical report: it calls `FromJsonString`) |

Graded against the stated profile, every TOO STRICT row is permitted, and the TOO LENIENT rows remain: Go 4
(`+24:00`, `+01:60`, `,5`, `T1:00:00Z`: 3339-5.6-026, -027, -033, -045), Python 12 (`+1:00`, `+24:00`, `+01:60`, `.Z` and `05.Z`, 1-digit month, day, hour,
minute and second (`00:00:0.5Z`), fullwidth and Arabic-Indic digits). The leap-second "either" vectors were all rejected.

## Consumers: per-API results

### go: `protojson.Unmarshal` into `timestamppb.Timestamp`

50 of 59 probe inputs behaved as the RFCs require (not listed). Every RFC 9557 suffix is rejected (correct for an
RFC 3339-only consumer). The parser is `time.Parse(time.RFC3339Nano, s)` (so it inherits the Go leniencies in
`go.md`, "`time.Parse(time.RFC3339Nano)`"), then a range check on the instant, then a check that the text between the
last `.` and the last `Z`/`+`/`-` has at most 9 digits.

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` / `2026-09-24T12:00:00z` | rejected: `invalid google.protobuf.Timestamp value` | TOO STRICT (Review note under the profile template) |
| `2026-09-24T12:00:00+00:00` / `-00:00` | accepted → 12:00:00Z; re-emitted as `2026-09-24T12:00:00Z` | conforming (Advisory, rule 2: offset discarded, always `Z`) |
| `2026-09-24T12:00:00+24:00` | accepted → `2026-09-23T12:00:00Z` | TOO LENIENT |
| `2026-09-24T12:00:00+23:60` | accepted → `2026-09-23T12:00:00Z` (read as +24:00) | TOO LENIENT |
| `2026-09-24T12:00:00+24:60` (extra) | accepted → `2026-09-23T11:00:00Z` (read as +25:00) | TOO LENIENT (legacy probe only) |
| `2026-09-24T1:00:00Z` (extra) | accepted → `2026-09-24T01:00:00Z` | TOO LENIENT (3339-5.6-045) |
| `2026-09-24T12:00:00,5Z` | accepted → `12:00:00.500Z` | TOO LENIENT |
| `2026-09-24T12:00:00,1234567891234Z` (extra, 13 digits) | accepted → `12:00:00.123456789Z` | TOO LENIENT (the comma also bypasses protojson's 9-digit check, which looks only for `.`; 4 digits silently truncated) (legacy probe only) |
| `2016-12-31T23:59:60Z` / `2016-12-31T18:59:60-05:00` | rejected | too strict (no leap second; profile-permitted: smeared) |
| `2026-09-24T12:00:00.123456789012Z` (also `.1234567890Z`) | rejected | TOO STRICT (profile-permitted: "up to 9 digits") |
| `0000-01-01T00:00:00Z` | rejected: `value out of range` | too strict (range limit; profile-permitted) |
| `0001-01-01T00:00:00+01:00` / `9999-12-31T23:59:59-01:00` (extra) | rejected: `value out of range` | too strict (range limit on the instant; profile-permitted) (legacy probe only) |
| `9999-12-31T23:59:59.999999999Z` (extra) | accepted → same | conforming (legacy probe only) |

### python: `Timestamp.FromJsonString` / `json_format.Parse`

48 of 59 probe inputs behaved as the RFCs require (not listed). Both APIs gave identical results on every input
(`json_format.Parse` calls `FromJsonString` and wraps `ValueError` as `ParseError`). Every RFC 9557 suffix is
rejected. The parser is hand-written (`internal/well_known_types.py`): it finds the offset with
`find('Z')`, else `find('+')`, else `rfind('-')`; parses the date-time with `strptime('%Y-%m-%dT%H:%M:%S')`;
computes nanos with `round(float('0.' + frac) * 1e9)`; and parses the offset with
`int(hh)`/`int(mm)` split on the first `:`. `strptime`, `float()` and `int()` are all more lenient than the ABNF.

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: `lowercase 't' is not accepted` (explicit check) | TOO STRICT (Review note under the profile template) |
| `2026-09-24T12:00:00z` | rejected (`find('Z')` misses, `rfind('-')` then cuts the string at the date) | TOO STRICT (Review note) |
| `2026-09-24T12:00:00+00:00` / `-00:00` | accepted → re-emitted as `…12:00:00Z` | conforming (Advisory, rule 2) |
| `2026-09-24T12:00:00+24:00` / `+23:60` | accepted → `2026-09-23T12:00:00Z` | TOO LENIENT |
| `2026-09-24T12:00:00+99:99` (extra) | accepted → `2026-09-20T07:21:00Z` (−100 h 39 min) | TOO LENIENT (any integer offset is accepted) (legacy probe only) |
| `2026-09-24T12:00:00+-1:00` (extra) | accepted → `2026-09-24T13:00:00Z` | TOO LENIENT (sign inverted: `+` then `int('-1')`) (legacy probe only) |
| `2026-09-24T12:00:00+01:-30` / `+01:+30` (extra) | accepted → `11:30:00Z` / `10:30:00Z` | TOO LENIENT (signed offset minute) (legacy probe only) |
| `2026-09-24T12:00:00+2:0` / `+0_2:00` / `+ 2:00` (extra) | accepted → `10:00:00Z` | TOO LENIENT (`int()` accepts 1 digit, `_` and spaces) (legacy probe only) |
| `2026-09-24T12:00:00+02:00\n` (extra) | accepted → `10:00:00Z` | TOO LENIENT (trailing whitespace after a numeric offset; after `Z` it is rejected) (legacy probe only) |
| `2026-09-24T12:00:00+١:٠٠` (extra, Arabic-Indic offset digits) | accepted → `11:00:00Z` | TOO LENIENT (legacy probe only) |
| `2026-09-24T12:00:00.Z` | accepted → `12:00:00Z` | TOO LENIENT (empty fraction) |
| `2026-09-24T12:00:00.1e-3Z` / `.5E-1Z` / `.1_2Z` (extra) | accepted → `.000100Z` / `.050Z` / `.120Z` | TOO LENIENT (`float()` syntax in the fraction) (legacy probe only) |
| `2026-9-24T12:00:00Z` (also 1-digit day, hour, minute, second) | accepted → `2026-09-24T12:00:00Z` | TOO LENIENT |
| `٢٠٢٦-09-24T12:00:00Z` (also fullwidth digits) | accepted → `2026-09-24T12:00:00Z` | TOO LENIENT (`strptime` matches Unicode `\d`) |
| `2016-12-31T23:59:60Z` / `2016-12-31T18:59:60-05:00` | rejected: `second must be in 0..59` | too strict (no leap second; profile-permitted) |
| `2026-09-24T12:00:00.123456789012Z` (also `.1234567890Z`) | rejected: `more than 9 fractional digits` | TOO STRICT (profile-permitted) |
| `0000-01-01T00:00:00Z` | rejected: `year 0 is out of range` | too strict (range limit; profile-permitted) |
| `0001-01-01T00:00:00+01:00` / `9999-12-31T23:59:59-01:00` (extra) | rejected: `Seconds … must be in range` | too strict (range limit on the instant; profile-permitted) (legacy probe only) |
| `2026-09-24T12:00:00,5Z`, `+0200`, `+02`, `T24:00:00Z`, `T12:00Z`, no offset, trailing `\n` after `Z` | rejected | conforming |

## Producers (formatters)

Every output was checked with `rfcdt.py check --json`. Go `protojson.Marshal` and Python `ToJsonString` /
`json_format.MessageToJson` gave the same text in every row, so rows are merged. Base instant
2026-09-24T12:00:00Z (`seconds` 1790251200).

| Call | Output | RFC verdict |
|---|---|---|
| `protojson.Marshal` / `ToJsonString` / `MessageToJson`, nanos 0 | `2026-09-24T12:00:00Z` | conforming |
| same, nanos 100 000 000 | `2026-09-24T12:00:00.100Z` | conforming (fixed 0/3/6/9 digits, as the profile states) |
| same, nanos 123 000 000 / 123 456 000 / 123 456 789 / 1 | `….123Z` / `….123456Z` / `….123456789Z` / `….000000001Z` | conforming (exact, no loss) |
| same, zero value | `1970-01-01T00:00:00Z` | conforming (Advisory: an unset Timestamp field is omitted, but a set zero value is a real instant) |
| same, seconds −62135596800 (min) / 253402300799 + nanos 999 999 999 (max) | `0001-01-01T00:00:00Z` / `9999-12-31T23:59:59.999999999Z` | conforming |
| same, seconds −62135596801 or 253402300800 | ✗ Go `seconds out of range`; Python `ValueError: Timestamp is not valid` | refuses (safe) |
| same, nanos −1 or 1 000 000 000 | ✗ Go `nanos out of range`; Python `ValueError` (its message says "range [0, 999999]"; the check is `< 1e9`) | refuses (safe) |
| go: `ts.AsTime().Format(time.RFC3339Nano)` on an invalid Timestamp (no `CheckValid`) | seconds 253402300800 → `10000-01-01T00:00:00Z`; nanos 1e9 → `…12:00:01Z`; nanos −1 → `…11:59:59.999999999Z` | WRONG OUTPUT (5-digit year) / silently normalized; `CheckValid()` returns an error for all of them |
| python: `FromDatetime(aware)` then `ToJsonString` (UTC, or `+02:00` 14:00) | `2026-09-24T12:00:00Z` | conforming |
| python: `FromDatetime(datetime(2026,9,24,8,0))` (naive local, New York) | `2026-09-24T08:00:00Z` | WRONG VALUE (naive is "assumed to be in UTC", per its docstring; true 12:00:00Z, −4 h) |
| python: `FromDatetime(datetime.now())` | `…01:35:37.502634Z` vs true `…05:35:37.502652Z` | WRONG VALUE (host offset, −4 h) |
| python: `ToDatetime()` (no `tzinfo`) | `datetime(2026, 9, 24, 12, 0)`: naive UTC | Advisory (its later `isoformat()` has no offset: defect "sent with no offset") |

The producers match the profile exactly. The spec comment itself recommends two non-protobuf producers: Python
`strftime('%Y-%m-%dT%H:%M:%S.%fZ')` (a literal `Z`: WRONG VALUE on non-UTC values, see `python.md`, producers) and JS
`toISOString()` (prints `+010000-…` outside the range, see `javascript.md`, producers).

## Detect in code

`rfcdt.py scan` flags `.proto` files with `SCAN-PROTO-STRING-TIME` (a `string *_at`/`*_time` field: prefer
`google.protobuf.Timestamp`) and `SCAN-PROTO-ISO8601-COMMENT`. The runtime greps below are for the code that uses the
messages. ERE, tested with macOS `grep -nE` on a sample file: each row hits its risky lines and not the safe forms.

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `\.FromJsonString\(\|json_format\.Parse(Dict)?\(` (Python, messages with a `Timestamp` field) | Accepts `+24:00`, `+99:99`, `+-1:00` (**sign inverted**: 13:00Z for 12:00+-1:00), `+01:-30`, `+2:0`, `+0_2:00`, `.Z`, `.1e-3`, 1-digit fields, Arabic-Indic/fullwidth digits, and `\n` after a numeric offset. Rejects `t`/`z`, `:60`, > 9 digits. | Check the string with the strict regex (`README.md`, "Portable strict check"; add a 9-digit fraction limit if you want the profile) before `FromJsonString`, or in a pre-pass over the JSON before `json_format.Parse` |
| `FromDatetime\(\s*(datetime\.)+now\(\s*\)` · `\.FromDatetime\(` with a naive `datetime` | Naive input is treated as UTC: on a New York host `datetime.now()` gives a timestamp 4 h early (**WRONG VALUE**) | `ts.GetCurrentTime()`, or `FromDatetime(datetime.now(timezone.utc))` / any aware datetime |
| `\.ToDatetime\(\s*\)` | Returns a naive UTC `datetime`; a later `isoformat()` or `str()` has no offset | `ToDatetime(tzinfo=timezone.utc)` |
| `protojson\.Unmarshal\(\|UnmarshalOptions\{` (Go, messages with `timestamppb.Timestamp`) | `time.Parse(RFC3339Nano)` underneath: accepts `+24:00`, `+23:60` (as +24:00), `+24:60` (as +25:00), `,5`, `T1:00:00Z`; the comma form also skips the 9-digit check and truncates silently | Validate untrusted JSON strings with the strict regex before `protojson.Unmarshal`, or accept the leniency and document it |
| `\.AsTime\(\)` without a nearby `CheckValid\(\)` | `AsTime` never fails: out-of-range seconds give `10000-…` from `Format`, bad nanos are normalized into the next or previous second | `if err := ts.CheckValid(); err != nil { … }` first (protojson `Marshal` already refuses) |

## Top defects (protobuf)

1. **Python offset parsing is `int()` on split text** (Nonconformity for an ingest boundary: TOO LENIENT and a
   false instant). `+-1:00` gives the sign-inverted instant, `+99:99` shifts by 100 h 39 min, and `+24:00`, `+2:0`,
   `+0_2:00`, `+ 2:00` and Arabic-Indic digits are accepted. Neither the profile template nor RFC 3339 allows any
   of them.
2. **Python fraction parsing is `float()`**: `.Z`, `.1e-3`, `.5E-1`, `.1_2` are accepted as real fractions.
3. **Python date-time parsing is `strptime`**: 1-digit month/day/hour/minute and non-ASCII digits are accepted.
4. **Go inherits `time.Parse` leniency** (`+24:00`, `+23:60`, `+24:60` as +25:00, `,5`, 1-digit hour), and the
   comma bypasses protojson's own "at most 9 fraction digits" check.
5. **Naive datetimes at the Python boundary**: `FromDatetime(naive)` assumes UTC (4 h wrong from `datetime.now()`
   on a New York host); `ToDatetime()` returns naive UTC.
6. **Profile limits** (documented, not defects, but consumers of protobuf-produced JSON must know them): no
   lowercase `t`/`z`, no leap second, no year 0000, at most 9 fraction digits, the instant must be inside
   0001-01-01…9999-12-31 UTC, and every offset is normalized to `Z` (the local offset is lost; Advisory, rule 2).
   Producers (`protojson.Marshal`, `ToJsonString`) are fully conforming and refuse out-of-range values.

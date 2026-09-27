# Go: RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-25.** Go 1.27.1 (default `GOEXPERIMENT`, incl. `jsonv2`; standard library only). macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **Go `time.Parse(time.RFC3339 | RFC3339Nano)`** and every API built on it (`ParseInLocation`, `Time.UnmarshalJSON`,
  `Time.UnmarshalText`, `encoding/json` v1 `Unmarshal`) gave **the same verdict, instant and offset for all 69 inputs**.
  `RFC3339` and `RFC3339Nano` are the same parser on input (a fraction is accepted after the seconds field either way).
  The matrix does not show these:
  - It accepts offset hour 24 and offset minute 60. `+24:00`, `+23:60` (read as +24:00), `+24:59` and `+24:60`
    (read as **+25:00**) are accepted. `+25:00` is rejected. The source says this is on purpose:
    "some people do write offsets of 24 hours or 60 minutes" (`src/time/format.go:1271-1278`).
  - It accepts a 1-digit hour: `2026-09-24T1:00:00Z` gives 01:00Z.
  - A value that it accepted can fail to serialize. `Parse("…+23:60")` then `Format(time.RFC3339)` gives
    `2026-09-24T12:00:00+24:00` (**not RFC 3339**), and `MarshalJSON` returns
    `Time.MarshalJSON: timezone hour outside of range [0,23]`.
  - The "strict" RFC 3339 checks in `parseStrictRFC3339` are **dead code** (`case true: return t, nil`,
    `src/time/format_rfc3339.go:168-170`, "TODO(https://go.dev/issue/54580): Strict parsing is disabled for now").
    `UnmarshalJSON`/`UnmarshalText` are therefore exactly `time.Parse(time.RFC3339, …)`. No GODEBUG turns them on.
- **Go `encoding/json/v2`** with its default options is the only strict stdlib entry point. It rejects `,5`, a
  1-digit hour and offset hour ≥ 24 / minute ≥ 60 (`src/encoding/json/v2/arshal_time.go:394-424`). It still rejects
  `t`/`z` and every `:60`. The v1 package passes `ParseTimeWithLooseRFC3339(true)` to v2, so `json.Unmarshal`
  stays loose. `jsonv2.Unmarshal(b, &v, json.DefaultOptionsV1(), json.ParseTimeWithLooseRFC3339(false))` gives v1
  semantics with strict times. `encoding/json/v2` does not build with `GOEXPERIMENT=nojsonv2`.
- **Go rejects `t` and `z` in every API** (the fast path tests `s[10] == 'T'` and `s[0] == 'Z'`, and the layout
  engine matches literals by case). **Go rejects every `:60`**, including real leap seconds: "second out of range".
  `time.Time` cannot represent second 60. `time.Date(2016,12,31,23,59,60,0,UTC)` silently normalizes to
  `2017-01-01T00:00:00Z`.
- A fraction longer than 9 digits is **truncated**, not rounded: `2026-12-31T23:59:59.9999999999Z` stays on
  2026-12-31 (`…59.999999999`).
- `ParseInLocation(time.RFC3339, s, loc)` differs from `Parse` only in which `*Location` it attaches when the offset
  matches `loc` (the instant is the same). With a zone-less layout it is not the same:
  `Parse("2006-01-02T15:04:05", "2026-09-24T12:00:00")` gives **12:00Z (UTC assumed)**, and
  `ParseInLocation(same, …, time.Local)` gives **16:00Z (host-local)**. `time.Parse(time.RFC3339, …)` rejects a
  missing offset.
- Calling `(*Time).UnmarshalJSON(raw)` directly does **not decode JSON escapes** ("TODO(https://go.dev/issue/47353)",
  `src/time/time.go:1608`): `"2026-09-24T12:00:00\u005a"` (valid JSON for `…Z`) is rejected. `json.Unmarshal` into
  a struct decodes the escape first and accepts it (tested with the default build and with `GOEXPERIMENT=nojsonv2`).
- Go has **no RFC 9557 parser** in the standard library. Every API rejects every suffix with `extra text: "[…]"`.
  This is correct for an RFC 3339 consumer, and it never drops a critical suffix silently.

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict "conforming".

### common results (all seven Go consumers)

Every Go consumer read `-00:00`, `+23:59`, `+05:30`, `0000-01-01T00:00:00Z`, `0001-…`, `9999-12-31T23:59:59Z`,
`2024-02-29` and 1–9 fraction digits as the correct instant. It rejected `+0200`, `+02`, `T12:00Z`, a missing offset,
date only, basic format, week and ordinal dates, 1-digit month, leading space, trailing `\n`, NBSP, Arabic-Indic
digits, 5-digit, signed and negative years, `T24:00:00Z`, `.Z`, Feb 29 2026, Feb 30, Apr 31, `:60` on a non-leap
date, and every `[…]` suffix.

### `time.Parse(time.RFC3339)`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t12:00:0 | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as "Z | TOO STRICT |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | TOO LENIENT |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | TOO LENIENT |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | TOO LENIENT (vector 3339-5.6-045) |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | TOO LENIENT — legacy probe only |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | TOO LENIENT — legacy probe only |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming — legacy probe only |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | TOO LENIENT — legacy probe only |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | TOO LENIENT |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as  | TOO STRICT |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming (cf. vector 3339-5.6-084) |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot parse " | conforming — legacy probe only |

### `time.Parse(time.RFC3339Nano)`

Identical to `time.Parse(time.RFC3339)` on all 69 inputs: same verdicts, instants and offsets. Only the layout
name in the error text differs. There is no reason to prefer `RFC3339Nano` for parsing.

### `time.ParseInLocation(time.RFC3339, s, time.Local)`

Identical to `time.Parse(time.RFC3339)` on all 69 inputs. `2026-09-24T08:00:00-04:00` gets `Location()==time.Local`
because the offset matches the host zone. The instant is the same.

### `(*time.Time).UnmarshalJSON`

Identical to `time.Parse(time.RFC3339)` on all 69 inputs (the strict checks are disabled, see the notes at the top of this file). Also, called
directly on raw bytes it rejects any JSON escape inside the string (`\u005a`; `\n` arrives as a backslash and `n`).

### `(*time.Time).UnmarshalText`

Identical to `time.Parse(time.RFC3339)` on all 69 inputs.

### `json.Unmarshal into struct{T time.Time}` (encoding/json v1)

Identical to `time.Parse(time.RFC3339)` on all 69 inputs. It decodes JSON string escapes before parsing.

### `encoding/json/v2 Unmarshal into struct{T time.Time}`

54 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: json: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t1 | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: json: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" | TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: json: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: json: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | rejected: json: parsing time "2026-09-24T1:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "1"  | conforming (vector 3339-5.6-045) |
| `2026-09-24T12:00:00+24:59` | rejected: json: parsing time "2026-09-24T12:00:00+24:59": timezone hour out of range | conforming — legacy probe only |
| `2026-09-24T12:00:00+24:60` | rejected: json: parsing time "2026-09-24T12:00:00+24:60": timezone hour out of range | conforming — legacy probe only |
| `2026-09-24T12:00:00+25:00` | rejected: json: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming — legacy probe only |
| `2026-09-24T12:00:00.5+23:60` | rejected: json: parsing time "2026-09-24T12:00:00.5+23:60": timezone minute out of range | conforming — legacy probe only |
| `2026-09-24T12:00:00,123456789123Z` | rejected: json: parsing time "2026-09-24T12:00:00,123456789123Z" as "2006-01-02T15:04:05Z07:00": can | conforming |
| `2026-09-24T12:00:00.5z` | rejected: json: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse " | TOO STRICT |
| `2026-09-24T12:00:00+00:44:30` | rejected: json: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming (cf. vector 3339-5.6-084) |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: json: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot p | conforming — legacy probe only |

## Producers (formatters)

Every output was checked with `rfcdt.py check --json`. "Denotes" is the instant the string means under RFC 3339,
compared with the true instant of the `time.Time`. `Format(RFC3339)`, `Format(RFC3339Nano)`, `MarshalJSON`,
`MarshalText` and `json.Marshal` (v1) gave the same text in every row where no error is shown, so rows are merged.

| Call | Output | RFC verdict |
|---|---|---|
| `t.UTC().Format(time.RFC3339)` / `MarshalJSON` / `MarshalText` / `json.Marshal` | `2026-09-24T12:00:00Z` | conforming |
| same, `t.In(time.Local)` (New York) | `2026-09-24T08:00:00-04:00` | conforming |
| same, `Europe/London` in January (offset 0 but known) | `2026-01-15T12:00:00Z` | conforming (Advisory, rule 2: Go always prints `Z` for offset 0 and never `+00:00`) |
| same, value from `Parse("…+00:00")` or `Parse("…-00:00")` | `2026-09-24T12:00:00Z` | conforming (Advisory, rule 2: `+00:00` becomes `Z` on round trip) |
| `Format(time.RFC3339Nano)` / `MarshalJSON` / `MarshalText`, 123 456 789 ns | `2026-09-24T12:00:00.123456789Z` | conforming |
| same, 123 000 000 ns | `2026-09-24T12:00:00.123Z` | conforming (trailing zeros trimmed: variable length, §5.1 string sort breaks; documented in the `time` package doc) |
| same, 0 ns | `2026-09-24T12:00:00Z` | conforming (no fraction at all) |
| `Format(time.RFC3339)`, 123 456 789 ns | `2026-09-24T12:00:00Z` | conforming (lossy: fraction dropped, truncated) |
| `Format("2006-01-02T15:04:05.000000000Z07:00")`, 123 000 000 ns | `2026-09-24T12:00:00.123000000Z` | conforming (fixed width) |
| all five, `time.Time{}` (zero value) | `0001-01-01T00:00:00Z` | conforming (Advisory: v1 `omitempty` does not omit it; `omitzero` does) |
| all five, year 0 / year 12 / year 9999 | `0000-01-01T00:00:00Z` / `0012-…` / `9999-12-31T23:59:59Z` | conforming |
| all five, `time.Date(2016,12,31,23,59,60,…)` | `2017-01-01T00:00:00Z` | conforming (a leap second cannot be represented; `Date` normalizes it to the next minute) |
| **all five**, `time.FixedZone("x", -2670)` (−00:44:30) | `2026-09-24T11:15:30-00:44` | WRONG VALUE (denotes 11:59:30Z; true 12:00:00Z, −30 s) |
| **all five**, `Africa/Monrovia`, 1970-01-01T12:00:00Z (MMT −00:44:30) | `1970-01-01T11:15:30-00:44` | WRONG VALUE (denotes 11:59:30Z, −30 s) |
| **all five**, `Europe/Paris`, 1850-01-01 00:00 local (LMT +00:09:21) | `1850-01-01T00:00:00+00:09` | WRONG VALUE (denotes 1849-12-31T23:51:00Z; true 23:50:39Z, +21 s) |
| **all five**, `time.FixedZone("", 30)` (+00:00:30) | `2026-09-24T12:00:30+00:00` | WRONG VALUE (denotes 12:00:30Z, +30 s) |
| `Format(time.RFC3339 / RFC3339Nano)`, `time.FixedZone("", 24*3600)` | `2026-09-25T12:00:00+24:00` | WRONG OUTPUT (offset hour 24) |
| same, `FixedZone("", 25*3600)` | `2026-09-25T13:00:00+25:00` | WRONG OUTPUT (offset hour 25) |
| `MarshalJSON` / `MarshalText` / `json.Marshal`, offset ≥ 24 h | ✗ `Time.MarshalJSON: timezone hour outside of range [0,23]` | refuses (safe) |
| `Format(time.RFC3339 / RFC3339Nano)`, year 10000 (also `AddDate(8000,0,0)` from 2026) | `10000-01-01T00:00:00Z` | WRONG OUTPUT (5-digit year) |
| same, year −1 | `-0001-01-01T00:00:00Z` | WRONG OUTPUT (signed year) |
| `MarshalJSON` / `MarshalText` / `json.Marshal`, year 10000 or −1 | ✗ `Time.MarshalJSON: year outside of range [0,9999]` | refuses (safe) |
| `t.String()` (also `fmt` `%v`) | `2026-09-24 12:00:00 +0000 UTC`; `time.Now()` adds ` m=+0.000094501` | WRONG OUTPUT (space separator, `+0000`, zone name; debug format by its own doc) |
| `Local t.Format("2006-01-02T15:04:05Z")` (literal Z) | `2026-09-24T08:00:00Z` | WRONG VALUE (local wall time labelled Z; true 12:00:00Z, −4 h) |
| `t.Format("2006-01-02T15:04:05-0700")` or `…Z0700` (Paris) | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (offset without colon) |
| `t.Format(time.DateTime)` | `2026-09-24 14:00:00` | WRONG OUTPUT (space separator, no offset) |
| `t.Format(time.DateTime + "Z07:00")` | `2026-09-24 14:00:00+02:00` | WRONG OUTPUT (space separator) |
| `t.Format("…05Z07:00:00")` (Monrovia 1970) | `1970-01-01T11:15:30-00:44:30` | WRONG OUTPUT (offset with seconds; the instant is right) |

The WRONG VALUE rows come from `appendFormatRFC3339` (`src/time/format_rfc3339.go:49-58`): it computes
`zone := offset / 60` (truncates the offset seconds) but keeps the local wall-clock time. `appendStrictRFC3339`
(used by `MarshalJSON`/`MarshalText`) checks only the year width and the offset hour, so it does not catch this.
The layout engine (`Z07:00`) does the same truncation.

## Conformance vectors (`run_vectors.py`, 310-vector set, 2026-09-26)

All runs: `probes/run_vector_probes.py --lang go` (`--batch --target-kind rfc3339 --target-options fixed
--target-has-tzdata yes`, `TZ=America/New_York`). "Scored" excludes skips and interpretations. Report:
`evals/baselines/probes/vector-runs/go.txt`. (The 2026-09-25 runs used the 274-vector set; those reports stay in
`evals/baselines/probes/go-vectors/`. The failing vectors are the same.)

Go (`--target-kind rfc3339`; 157 skipped: 128 IXDTF-only, 29 non-default options):

| Adapter | Pass/scored | Too lenient | Too strict | Wrong value | Interpretation choices (6 vectors: 5 leap-second policy, 1 negative-leap-second future date) |
|---|---|---|---|---|---|
| `time.Parse(time.RFC3339)` | 129/147 (87.8%) | 4 | 14 | 0 | rejected all 5 `:60`; accepted `2035-06-30T23:59:59Z` (3339-5.7-055) |
| `time.Parse(time.RFC3339Nano)` | 129/147 | 4 | 14 | 0 | identical to RFC3339 (per vector) |
| `time.ParseInLocation(time.RFC3339, s, time.Local)` | 129/147 | 4 | 14 | 0 | identical |
| `(*Time).UnmarshalJSON` | 129/147 | 4 | 14 | 0 | identical |
| `(*Time).UnmarshalText` | 129/147 | 4 | 14 | 0 | identical |
| `json.Unmarshal` (v1) into `struct{T time.Time}` | 129/147 | 4 | 14 | 0 | identical |
| `encoding/json/v2` `Unmarshal` into `struct{T time.Time}` | 133/147 (90.5%) | 0 | 14 | 0 | rejected all 5 `:60`; accepted 3339-5.7-055 |
| `ParseRFC3339Strict` (`probes/go/strict.go`, safe replacement) | 147/147 (100%) | 0 | 0 | 0 | accepted `2016-06-30`, `2016-03-31`, `2024-12-31` 23:59:60Z and 3339-5.7-055; rejected `2016-01-31`, `1971-12-31` (iers-months policy) |

- **Too lenient (4):** `3339-5.6-026` `+24:00`, `3339-5.6-027` `+01:60`, `3339-5.6-033` `,5Z`, `3339-5.6-045`
  `T1:00:00Z`. json/v2 rejects all four.
- **Too strict (14):** 3 lower-case (`3339-5.6-001/002/003`) and 11 real or leap-position `:60` (`3339-5.8-003/004`,
  `3339-5.7-025…032`, `3339-5.7-038`; `3339-5.7-026` is also lower-case `z`).
- **Wrong value: 0.** Every accepted vector that carries `fields` gave the expected local fields, fraction and offset
  (the 1050-digit fraction 3339-5.6-073 is truncated to 9 digits, which passes).

Raw per-input results: `probes/go/results/tables.md` (69 inputs: `inputs.json` plus 10 Go extras). Probe source: `probes/go/` (`main.go`, `strict.go`, `cmd/`; commands in the file headers).

See also `protobuf.md` (`protojson` uses `time.Parse(time.RFC3339Nano)`) and `jsonschema.md` (santhosh-tekuri/jsonschema; openapi-generator `go`).

## Detect in code

`rfcdt.py scan` now has 10 Go rules (`SCAN-GO-*`, added after this probe). The grep patterns below are the fuller
list. Use them (ERE; tested with macOS `grep -nE` on
`probes/go/testdata/risky_go.txt`: each row hits its sample lines, and none hits the correct `Z07:00` layout).

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `time\.Parse(InLocation)?\(\s*time\.RFC3339(Nano)?\b` · `\.Unmarshal(JSON\|Text)\(` · `` \btime\.Time\b[^`]*`[^`]*json:" `` (fields decoded by `encoding/json` v1) | It accepts `+24:00`, `+23:60` (as +24:00), `+24:60` (as **+25:00**), `,5` and a 1-digit hour (`T1:00:00Z`). It rejects `t`/`z` (**TOO STRICT**) and every `:60`, including real leap seconds. The accepted `+24:00` value later fails `MarshalJSON` or re-emits `+24:00` through `Format`. | the strict regex (below) in front: `ParseRFC3339Strict` in `probes/go/strict.go` passed 147/147 scored vectors. For JSON, `encoding/json/v2` `Unmarshal` (strict except `t`/`z`/`:60`), or a custom `UnmarshalJSON` that calls the strict helper |
| `\.UnmarshalJSON\(` called directly on bytes | It does not decode JSON escapes: `"…\u005a"` is rejected (issue 47353) | `json.Unmarshal` into the field, or unquote with `strconv.Unquote`/`json.Unmarshal` into a `string` first |
| `\.Format\(\s*time\.RFC3339(Nano)?\s*\)` · `\.Marshal(JSON\|Text)\(` · `json\.Marshal` of `time.Time` · `time\.(LoadLocation\|FixedZone)\(` | A zone offset that is not whole minutes (LMT and other pre-1972 zones, `FixedZone` with seconds) gives a **WRONG VALUE**: the wall time is kept and the offset seconds are dropped (−30 s for Monrovia 1970, +21 s for Paris 1850). `MarshalJSON` does not catch it. `FixedZone` ≥ 24 h makes `Format` print `+24:00`/`+25:00`. | `t.UTC().Format(time.RFC3339Nano)` for storage and the wire, or check `_, off := t.Zone(); off%60 != 0 \|\| off <= -86400 \|\| off >= 86400` and convert to UTC |
| `\.Format\(\s*time\.RFC3339(Nano)?\s*\)` on years from user input or date arithmetic (`AddDate`) | `Format` has no error path: year 10000 prints `10000-…` and year −1 prints `-0001-…` (**WRONG OUTPUT**). `MarshalJSON`/`MarshalText` return an error instead. | range-check `0 <= t.Year() && t.Year() <= 9999`, or use `t.MarshalText()` and handle the error |
| `` 15:04:05(\.[09]+)?Z["`] `` | A literal `Z` in the layout: local wall time is labelled UTC (`08:00:00Z` for 12:00Z, 4 h off). On parse it accepts only `Z` and rejects `+02:00`. | `Z07:00` (prints `Z` only for offset 0), or `t.UTC().Format(time.RFC3339)` |
| `` [-Z]07(00)?["`] `` | `-0700` and `Z0700` print `+0200` (no colon); `-07`/`Z07` print `+02` (**WRONG OUTPUT**) | `Z07:00` / `time.RFC3339` |
| `time\.(DateTime\|UnixDate\|ANSIC\|RFC1123Z?\|RFC822Z?\|Stamp[A-Za-z]*)\b\|"2006-01-02 15:04:05\|\.String\(\)` on the wire | `time.DateTime` has a space and no offset. `DateTime+"Z07:00"` has a space. `String()` gives `2026-09-24 12:00:00 +0000 UTC` (plus `m=±…` for `time.Now()`). | `time.RFC3339` / `RFC3339Nano` |
| `time\.RFC3339Nano\b` used for sort keys, file names or DB text columns | It trims trailing zeros (`.123`, and no fraction when ns = 0), so string order ≠ time order (§5.1) | fixed layout `"2006-01-02T15:04:05.000000000Z07:00"` on `t.UTC()` (for **formatting only**: as a parse layout it rejects any other fraction length) |
| `time\.Parse(InLocation)?\(\s*"2006-01-02T15:04:05(\.[09]+)?"` | A zone-less layout: `Parse` assumes **UTC**, `ParseInLocation(…, time.Local)` assumes **host-local** (12:00 became 16:00Z on a New York host) | `time.RFC3339` (it requires an offset) |
| `time\.Parse(InLocation)?\(\s*"[^"]*\.0+[^"]*"` | A fixed `.000` parse layout rejects `…:00Z` and any other number of fraction digits (**TOO STRICT**) | `time.RFC3339` (it accepts any fraction length) behind the strict regex |
| `\btime\.Time\b.*omitempty` | v1 `omitempty` never omits a zero `time.Time`: `{"T":"0001-01-01T00:00:00Z"}` is sent as if it were a real instant | `omitzero` (Go ≥ 1.24) or `*time.Time` |

Portable strict check in Go (RE2 has no `\d` Unicode issue, and `$` means end of text unless `(?m)` is set):

```go
var rfc3339Re = regexp.MustCompile(`^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$`)
```

After a match, upper-case `s[10]` and a final `z`, then call `time.Parse(time.RFC3339Nano, s)` (it does the
day-of-month check). For `:60`, decide the policy: reject and document it, or do as `probes/go/strict.go` does (accept 23:59:60
UTC at the end of Mar/Jun/Sep/Dec from 1972, return :59 plus a leap flag).

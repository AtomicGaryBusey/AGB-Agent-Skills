# .NET (C#): RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-24.** .NET SDK 10.0.300 / runtime 10.0.8. macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Probe program: `probes/probe_dotnet.cs` (reads `probes/inputs.json`, 59 strings; `probes/analyze.py` turns its JSON-lines results into the tables below). The raw result tables of the 2026-09-24 run were not committed: re-run the probe to regenerate them.

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **.NET `DateTime.Parse` / `DateTimeOffset.Parse`** accept almost anything that looks like a date. They do not accept
  offsets above ±14 h. `DateTime.Parse` without `RoundtripKind` converts to `Kind=Local`, so the original offset is lost.
  For `0001-01-01T00:00:00Z` it gave `0001-01-01T19:03:00-04:57`, which is UTC `0001-01-02T00:00Z`: **one day off**.
- **.NET `ParseExact(s, "o")`** accepts only 7 fraction digits and a numeric or `Z` form that `"o"` itself would print.
  It rejected `2026-09-24T12:00:00Z`. Do not use `"o"` to parse external input.

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict "conforming".

### `DateTime.Parse(s, Invariant)`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+23:59` | rejected: FormatException: The time zone offset of string '2026-09-24T12:00:00+23:59' must | too strict (offset range) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: FormatException: The DateTime represented by the string '2016-12-31T23:59:60Z' i | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: The DateTime represented by the string '2016-12-31T18:59:60-05: | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.5000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00.0000000 | TOO LENIENT (naive/local result) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00.0000000 | TOO LENIENT (naive/local result) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: FormatException: The DateTime represented by the string '0000-01-01T00:00:00Z' i | too strict (range limit) |
| `0001-01-01T00:00:00Z` | accepted → UTC 0001-01-02T00:00:00.0000000 | WRONG VALUE: instant differs: got 0001-01-02T00:00:00Z, expected 0001-01-01T00:00:00Z (3339-5.6-077: the vector run shows `utc` 0001-01-02T00:00:00 but grades it pass, because a `Kind=Local` result reports no fields) |

### `DateTime.Parse(s, Invariant, RoundtripKind)`

43 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+23:59` | rejected: FormatException: The time zone offset of string '2026-09-24T12:00:00+23:59' must | too strict (offset range) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: FormatException: The DateTime represented by the string '2016-12-31T23:59:60Z' i | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: The DateTime represented by the string '2016-12-31T18:59:60-05: | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.5000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00.0000000 | TOO LENIENT (naive/local result) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00.0000000 | TOO LENIENT (naive/local result) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: FormatException: The DateTime represented by the string '0000-01-01T00:00:00Z' i | too strict (range limit) |

### `DateTimeOffset.Parse(s, Invariant)`

43 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+23:59` | rejected: FormatException: The time zone offset of string '2026-09-24T12:00:00+23:59' must | too strict (offset range) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: FormatException: The DateTime represented by the string '2016-12-31T23:59:60Z' i | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: The DateTime represented by the string '2016-12-31T18:59:60-05: | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.5000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.0000000 | TOO LENIENT (as host-local time) |
| `2026-09-24` | accepted → UTC 2026-09-24T04:00:00.0000000 | TOO LENIENT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: FormatException: The DateTime represented by the string '0000-01-01T00:00:00Z' i | too strict (range limit) |

### `DateTimeOffset.ParseExact(s, "o")`

41 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | rejected: FormatException: String '2026-09-24T12:00:00Z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24t12:00:00Z` | rejected: FormatException: String '2026-09-24t12:00:00Z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: FormatException: String '2026-09-24T12:00:00z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24T12:00:00+00:00` | rejected: FormatException: String '2026-09-24T12:00:00+00:00' was not recognized as a vali | TOO STRICT |
| `2026-09-24T12:00:00-00:00` | rejected: FormatException: String '2026-09-24T12:00:00-00:00' was not recognized as a vali | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: FormatException: String '2026-09-24T12:00:00+23:59' was not recognized as a vali | too strict (offset range) |
| `2026-09-24T12:00:00+05:30` | rejected: FormatException: String '2026-09-24T12:00:00+05:30' was not recognized as a vali | TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: FormatException: String '2016-12-31T23:59:60Z' was not recognized as a valid Dat | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: String '2016-12-31T18:59:60-05:00' was not recognized as a vali | too strict (no leap second) |
| `2026-09-24T12:00:00.1Z` | rejected: FormatException: String '2026-09-24T12:00:00.1Z' was not recognized as a valid D | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: FormatException: String '2026-09-24T12:00:00.123Z' was not recognized as a valid | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456Z' was not recognized as a va | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456789Z' was not recognized as a | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456789012Z' was not recognized a | TOO STRICT |
| `0000-01-01T00:00:00Z` | rejected: FormatException: String '0000-01-01T00:00:00Z' was not recognized as a valid Dat | too strict (range limit) |
| `0001-01-01T00:00:00Z` | rejected: FormatException: String '0001-01-01T00:00:00Z' was not recognized as a valid Dat | TOO STRICT |
| `9999-12-31T23:59:59Z` | rejected: FormatException: String '9999-12-31T23:59:59Z' was not recognized as a valid Dat | TOO STRICT |
| `2024-02-29T12:00:00Z` | rejected: FormatException: String '2024-02-29T12:00:00Z' was not recognized as a valid Dat | TOO STRICT |

### `DateTimeOffset.ParseExact(s, "yyyy-MM-dd'T'HH:mm:ssK")`

45 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: FormatException: String '2026-09-24t12:00:00Z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: FormatException: String '2026-09-24T12:00:00z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: FormatException: The time zone offset of string '2026-09-24T12:00:00+23:59' must | too strict (offset range) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: FormatException: The DateTime represented by the string '2016-12-31T23:59:60Z' i | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: The DateTime represented by the string '2016-12-31T18:59:60-05: | too strict (no leap second) |
| `2026-09-24T12:00:00.1Z` | rejected: FormatException: String '2026-09-24T12:00:00.1Z' was not recognized as a valid D | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: FormatException: String '2026-09-24T12:00:00.123Z' was not recognized as a valid | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456Z' was not recognized as a va | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: FormatException: String '2026-09-24T12:00:00.1234567Z' was not recognized as a v | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456789Z' was not recognized as a | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456789012Z' was not recognized a | TOO STRICT |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.0000000 | TOO LENIENT (as host-local time) |
| `0000-01-01T00:00:00Z` | rejected: FormatException: The DateTime represented by the string '0000-01-01T00:00:00Z' i | too strict (range limit) |

### `DateTimeOffset.ParseExact(s, "yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK")`

48 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: FormatException: String '2026-09-24t12:00:00Z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: FormatException: String '2026-09-24T12:00:00z' was not recognized as a valid Dat | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: FormatException: The time zone offset of string '2026-09-24T12:00:00+23:59' must | too strict (offset range) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: FormatException: The DateTime represented by the string '2016-12-31T23:59:60Z' i | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: The DateTime represented by the string '2016-12-31T18:59:60-05: | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456789Z' was not recognized as a | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: FormatException: String '2026-09-24T12:00:00.123456789012Z' was not recognized a | TOO STRICT |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.0000000 | TOO LENIENT (as host-local time) |
| `0000-01-01T00:00:00Z` | rejected: FormatException: The DateTime represented by the string '0000-01-01T00:00:00Z' i | too strict (range limit) |

### `JsonSerializer.Deserialize<DateTimeOffset>`

46 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: JsonException: The JSON value could not be converted to System.DateTimeOffset. P | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: JsonException: The JSON value could not be converted to System.DateTimeOffset. P | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: JsonException: The JSON value could not be converted to System.DateTimeOffset. P | too strict (offset range) |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: JsonException: The JSON value could not be converted to System.DateTimeOffset. P | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: JsonException: The JSON value could not be converted to System.DateTimeOffset. P | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.1234567 | conforming (lossy: fraction truncated to 7 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.1234567 | conforming (lossy: fraction truncated to 7 digits) |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.0000000 | TOO LENIENT (as host-local time) |
| `2026-09-24` | accepted → UTC 2026-09-24T04:00:00.0000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: JsonException: The JSON value could not be converted to System.DateTimeOffset. P | too strict (range limit) |

### `JsonSerializer.Deserialize<DateTime>`

46 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: JsonException: The JSON value could not be converted to System.DateTime. Path: $ | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: JsonException: The JSON value could not be converted to System.DateTime. Path: $ | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: JsonException: The JSON value could not be converted to System.DateTime. Path: $ | too strict (offset range) |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.0000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: JsonException: The JSON value could not be converted to System.DateTime. Path: $ | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: JsonException: The JSON value could not be converted to System.DateTime. Path: $ | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.1234567 | conforming (lossy: fraction truncated to 7 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.1234567 | conforming (lossy: fraction truncated to 7 digits) |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00.0000000 | TOO LENIENT (naive/local result) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00.0000000 | TOO LENIENT (naive/local result) |
| `0000-01-01T00:00:00Z` | rejected: JsonException: The JSON value could not be converted to System.DateTime. Path: $ | too strict (range limit) |

### `XmlConvert.ToDateTimeOffset (xsd:dateTime)`

48 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: FormatException: The string '2026-09-24t12:00:00Z' is not a valid AllXsd value. | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: ArgumentOutOfRangeException: Offset must be within plus or minus 14 hours. (Para | too strict (offset range) |
| `2016-12-31T23:59:60Z` | rejected: FormatException: The string '2016-12-31T23:59:60Z' is not a valid AllXsd value. | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: FormatException: The string '2016-12-31T18:59:60-05:00' is not a valid AllXsd va | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.1234568 | conforming (lossy: fraction rounded to 7 digits) |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.0000000 | TOO LENIENT (as host-local time) |
| `2026-09-24` | accepted → UTC 2026-09-24T04:00:00.0000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.0000000 | TOO LENIENT |
| `2024-01-01T12:00:00+01:60` (3339-5.6-027) | accepted → offset +02:00 | TOO LENIENT (offset minute 60 rolled over) |
| `…Z ` / `…Z\r` / `…Z\r\n` (3339-5.6-056, -066, -067) | accepted | TOO LENIENT (trailing space, CR, CRLF) |
| `0000-01-01T00:00:00Z` | rejected: FormatException: The string '0000-01-01T00:00:00Z' is not a valid AllXsd value. | too strict (range limit) |

## Vector runs (310 vectors)

**Probed 2026-09-26** (.NET SDK 10.0.300) with `probes/run_vector_probes.py` (`run_vectors.py --batch --target-kind rfc3339
--target-options fixed`, host `TZ=America/New_York`); full reports in `evals/baselines/probes/vector-runs/dotnet.txt`.
147 vectors are scored per key (128 IXDTF vectors and 29 option vectors are skipped; 6 either-verdict leap-second vectors
are interpretations).

| Key (API) | pass | too lenient | too strict | wrong value | pass % |
|---|---|---|---|---|---|
| `datetime-parse` (`DateTime.Parse(s, Invariant)`) | 111 | 21 | 15 | 0 | 75.5 |
| `datetime-parse-roundtrip` (`…, RoundtripKind`) | 111 | 21 | 15 | 0 | 75.5 |
| `dto-parse` (`DateTimeOffset.Parse(s, Invariant)`) | 111 | 21 | 15 | 0 | 75.5 |
| `dto-parseexact-o` (`ParseExact(s, "o")`) | 88 | 0 | 59 | 0 | 59.9 |
| `dto-parseexact-ssK` (`"yyyy-MM-dd'T'HH:mm:ssK"`) | 113 | 3 | 31 | 0 | 76.9 |
| `dto-parseexact-FFFFFFFK` (`"…ss.FFFFFFFK"`) | 119 | 5 | 23 | 0 | 81.0 |
| `stj-dto` (`JsonSerializer.Deserialize<DateTimeOffset>`) | 121 | 6 | 20 | 0 | 82.3 |
| `stj-datetime` (`JsonSerializer.Deserialize<DateTime>`) | 121 | 6 | 20 | 0 | 82.3 |
| `xmlconvert-dto` (`XmlConvert.ToDateTimeOffset`) | 122 | 8 | 17 | 0 | 83.0 |

Fractions: a target that keeps fewer digits passes when its value is the exact fraction truncated or rounded
(`references/interpretation.md`, "Grading vector results"). `Parse` and `XmlConvert` round to 7 digits (ticks): the
1050-digit fraction 3339-5.6-073 gives `1234568` and now passes (it was graded WRONG VALUE before the rule). The
rounding can carry: `2024-01-01T23:59:59.999999999Z` (3339-5.6-013) becomes `2024-01-02T00:00:00` with `Parse` and
`XmlConvert` (lossy, 1 ns; `System.Text.Json` truncates to `.9999999`).

Behaviour found by the vectors that the 59-string probe did not show:

- **`Parse` (all three keys)**, TOO LENIENT on 21 vectors: space separator (3339-5.6-015), date only (-020), `T12:00Z`
  (-021), no offset (-022, host-local for `DateTimeOffset`), `+0100` (-023), `+01` (-024), **`+1:00`** (-025), a
  **space before `Z`** (-029), `,5` (-033), 1-digit month or day (-039, -040), **slashes** `2024/01/01T…` (-051),
  trailing `\n`, space, **NUL**, **CR** and CRLF (-055, -056, -064, -066, -067), a leading space (-057), **NBSP** as the
  separator (-071), and a **weekday prefix** `Fri, 1985-04-12T23:20:50Z`, even with the wrong weekday `Sat, …`
  (3339-5.4-001, -003). TOO STRICT on 15: every valid leap second (3339-5.8-003/-004, 3339-5.7-025…-032, -038), year
  0000 (3339-5.6-004, 3339-5.7-007) and offsets ±23:59 (3339-5.6-009/-010).
- **`ParseExact("o")`**: TOO STRICT on 59 valid vectors, including plain `…Z` (3339-4.3-001), `+00:00`/`-00:00`
  (3339-4.3-002/-003) and every fraction that is not 7 digits. No too-lenient result.
- **`ParseExact(…ssK)`**: accepts no offset (-022), `+0100` (-023) and `+1:00` (-025); rejects every fraction (-008,
  -080…-082, 3339-A-007), `t`/`z` (3339-5.6-001…-003), leap seconds, year 0000 and ±23:59.
- **`ParseExact(…FFFFFFFK)`**: also accepts an empty fraction `.Z` (3339-5.6-032, 3339-A-005); rejects more than 7
  fraction digits (3339-5.6-006, -013, -014, -073, -074).
- **`System.Text.Json`** (both keys): TOO LENIENT on date only, `T12:00Z`, no offset, `+01` and `.Z` (3339-5.6-020,
  -021, -022, -024, -032, 3339-A-005). **TOO STRICT on very long fractions**: it accepts 12 and 15 digits
  (3339-5.6-006, -014) but rejects the 1051- and 1056-digit fractions (3339-5.6-073, -074). Also rejects `t`/`z`, leap
  seconds, year 0000 and ±23:59.
- **`XmlConvert.ToDateTimeOffset`**: TOO LENIENT on 8: date only (-020), no offset (-022), **`+01:60` read as `+02:00`**
  (3339-5.6-027), trailing `\n`, **space**, **CR**, CRLF (-055, -056, -066, -067) and a leading space (-057). It accepts
  lower-case `z` but rejects lower-case `t` (3339-5.6-001, -003).
- `DateTime.Parse` without `RoundtripKind` still gives `0001-01-02T00:00:00Z` for `0001-01-01T00:00:00Z` (3339-5.6-077,
  `utc` in the report). The run grades it pass because a `Kind=Local` result carries no fields to compare; the WRONG
  VALUE verdict in the table above stands.

## Producers (formatters)

| Call | Output | RFC verdict |
|---|---|---|
| `DateTime(Utc).ToString("o")` | `2026-09-24T12:00:00.0000000Z` | conforming |
| `DateTime(Unspecified).ToString("o")` | `2026-09-24T12:00:00.0000000` | WRONG OUTPUT (no offset) |
| `DateTime(Local).ToString("o")` | `2026-09-24T08:00:00.0000000-04:00` | conforming |
| `DateTime.ToString("s")` | `2026-09-24T12:00:00` | WRONG OUTPUT (no offset) |
| `DateTime.ToString("u")` | `2026-09-24 12:00:00Z` | WRONG OUTPUT (space separator) |
| `DateTimeOffset.ToString("o")` | `2026-09-24T14:00:00.0000000+02:00` | conforming |
| `DateTimeOffset.ToString("u")` | `2026-09-24 12:00:00Z` | WRONG OUTPUT (space separator) |
| `DateTime(Local).ToString("yyyy-MM-ddTHH:mm:ssZ")  [literal Z, lies]` | `2026-09-24T08:00:00Z` | WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z) |
| `DateTime(Unspecified).ToString("yyyy-MM-dd'T'HH:mm:ssK")` | `2026-09-24T12:00:00` | WRONG OUTPUT (no offset) |
| `DateTimeOffset.ToString("yyyy-MM-dd'T'HH:mm:sszzz")` | `2026-09-24T14:00:00+02:00` | conforming |
| `DateTimeOffset.ToString("yyyy-MM-ddTHH:mm:sszzz") CurrentCulture=th-TH` | `2569-09-24T14:00:00+02:00` | WRONG VALUE (Thai Buddhist calendar year from culture) |
| `DateTimeOffset.ToString("yyyy-MM-ddTHH:mm:sszzz") CurrentCulture=ar-SA` | `1448-04-13T14:00:00+02:00` | WRONG VALUE (Um Al-Qura calendar date from culture) |
| `DateTimeOffset.ToString("yyyy-MM-ddTHH:mm:sszzz") CurrentCulture=fi-FI` | `2026-09-24T14.00.00+02:00` | WRONG OUTPUT ('.' time separator (culture)) |
| `DateTimeOffset.ToString("o") CurrentCulture=th-TH` | `2026-09-24T14:00:00.0000000+02:00` | conforming ("o" is culture-invariant) |
| `JsonSerializer.Serialize(DateTime Utc)` | `2026-09-24T12:00:00Z` | conforming |
| `JsonSerializer.Serialize(DateTime Unspecified)` | `2026-09-24T12:00:00` | WRONG OUTPUT (no offset) |
| `JsonSerializer.Serialize(DateTime Local)` | `2026-09-24T08:00:00-04:00` | conforming |
| `JsonSerializer.Serialize(DateTimeOffset)` | `2026-09-24T14:00:00+02:00` | conforming |
| `DateTime.ToString() [current culture]` | `9/24/2026 12:00:00\u202fPM` | WRONG OUTPUT (culture format) |
| `XmlConvert.ToString(DateTimeOffset)` | `2026-09-24T14:00:00+02:00` | conforming |

See also `jsonschema.md` (JsonSchema.Net `RequireFormatValidation`; the openapi-generator C# `DateTimeJsonConverter`, probed).

## Detect in code

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `DateTime(Offset)?\.(Try)?Parse\(\|Convert\.ToDateTime\(` | Very lenient: it accepts a space, `+0200`, `+02`, `+1:00`, a space before `Z`, `,5`, `T12:00Z`, a 1-digit month, `/` date separators, a weekday prefix, NBSP, NUL, CR, whitespace and a missing offset (read as host-local). `DateTime.Parse` converts to `Kind=Local` (wrong by one day at year 1). It rounds fraction digits past 7. | the strict regex, then `DateTimeOffset.Parse(s, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)` |
| `ParseExact\([^,]+,\s*"o"` | **TOO STRICT**: it rejects `…12:00:00Z` and any fraction that is not 7 digits | the strict regex + `Parse` (above) |
| `ParseExact\([^)]*K"` · `ParseExact\([^)]*FFFFFFF` | `K` accepts `+0200` and **no offset** (host-local). `.FFFFFFF` accepts an empty `.` and rejects more than 7 digits. | the strict regex first |
| `ToString\("o"\)` / `ToString\("[^"]*K"\)` on `DateTime` · `DateTimeKind\.Unspecified\|SpecifyKind` | A value with Unspecified kind prints **no offset** | use `DateTimeOffset`, or `DateTime.SpecifyKind(x, DateTimeKind.Utc)` |
| `ToString\("[su]"\)` | `"s"` has no offset. `"u"` uses a space separator. | `"o"` on `DateTimeOffset` / UTC `DateTime` |
| `ToString\("yyyy[^"]*"\)` without `CultureInfo.InvariantCulture` | The culture calendar and time separator leak: th-TH gives `2569-…`, ar-SA gives `1448-04-13…`, fi-FI gives `14.00.00` | pass `CultureInfo.InvariantCulture`, or quote `':'` |
| `ToString\("[^"]*ssZ"\)` | `Z` is a literal: local wall time labelled Z | `"yyyy-MM-dd'T'HH:mm:ssK"` on UTC, or `"o"` |
| `JsonSerializer\.(Serialize\|Deserialize)<DateTime>` · `DateTime` properties in DTOs | Unspecified prints no offset. It accepts `T12:00Z`, `+02`, `.Z` and a missing offset. It rejects `t`/`z` and very long fractions (1051 digits, 3339-5.6-073). | `DateTimeOffset` properties + a strict `JsonConverter` |
| `XmlConvert\.ToDateTime(Offset)?\(` | xsd:dateTime rules: it accepts a missing offset (host-local), `+01:60` (as `+02:00`), leading or trailing whitespace (space, `\n`, CR) and date-only input | the strict regex first |

# Ruby: RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-24** (probe strings); **vector runs 2026-09-26** (310 vectors, runner 0.4.0). Ruby 3.4.7. macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Probe program: `probes/probe_ruby.rb` (reads `probes/inputs.json`, 59 strings; `probes/analyze.py` turns its JSON-lines results into the tables below). The raw result tables of the 2026-09-24 run were not committed: re-run the probe to regenerate them.

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **Ruby `DateTime.rfc3339`** accepted `+24:00` and gave offset **+00:00** (a silent wrong value). `Time.parse` read
  `٢٠٢٦-09-24T12:00:00Z` (Arabic-Indic year) as **2026-09-09**.
- **Java `SimpleDateFormat`** and **Ruby `DateTime`** use the Julian calendar before 1582.
  `0001-01-01T00:00:00Z` came back as UTC `0000-12-30`, which is **2 days off**. `SimpleDateFormat` also accepted
  Arabic-Indic digits, a leading space and a 1-digit month, even when the probe checked `ParsePosition`.
  In the vector runs `DateTime.rfc3339` and `DateTime.iso8601` give 5 **WRONG VALUE** results, all Julian dates
  before 1582: `0000-01-01` → `-0001-12-30` (3339-5.6-004), `0050-06-01` → `0050-05-30` (3339-5.6-075, and
  3339-5.6-078 with `+01:00`), `0099-12-31` → `0099-12-29` (3339-5.6-076), `0001-01-01` → `0000-12-30`
  (3339-5.6-077). `Time` uses the proleptic Gregorian calendar and passes them.
- **`Time.new(s)` keeps invalid fields.** `Time.new("2024-02-30T00:00:00Z")` is accepted. `day` returns 30 and
  `xmlschema` prints `2024-02-30T00:00:00Z` again, but the instant (`to_i`) is 2024-03-01 (3339-5.7-008). A leap
  second on any date works the same way: `Time.new("2016-12-30T23:59:60Z").sec` is 60 (3339-5.7-035).

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict "conforming".
The probe strings are the legacy `inputs.json` strings (no vector has the exact same string). The **Vectors** column
names the vectors of the 2026-09-26 run that give the same verdict for the same API (see "Vector runs" below).
"legacy probe only" means that no vector covers the row. "differs" names a related vector with another result.

### `Time.iso8601 / Time.xmlschema`

44 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vectors |
|---|---|---|---|
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-023 |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-024 |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001 |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-025 |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-031 |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT | 3339-5.7-035 |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00.000000000000000 | TOO LENIENT | 3339-5.7-037 |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.000000000000000 | TOO LENIENT (as host-local time) | 3339-5.6-022 |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-057 |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-055, 3339-5.6-056, 3339-5.6-066, 3339-5.6-067 |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-036 |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-038 |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-03-01) | 3339-5.7-002 |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2024-03-01) | 3339-5.7-008 |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-05-01) | 3339-5.7-010 |

### `DateTime.rfc3339`

47 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vectors |
|---|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | too lenient (space; OK only under a stated profile) | 3339-5.6-015 |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-026 |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-027 |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001 |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59.000000000000000 | leap-second representation (→ :59; INTERPRETATION) | 3339-5.7-025 |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59.000000000000000 | leap-second representation (→ :59; INTERPRETATION) | 3339-5.7-031 |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:59.000000000000000 | TOO LENIENT | 3339-5.7-035 |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:59.000000000000000 | TOO LENIENT | 3339-5.7-037 |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-057 |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-055, 3339-5.6-056, 3339-5.6-066, 3339-5.6-067 |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000000000000 | WRONG VALUE: instant differs: got 0000-12-30T00:00:00Z, expected 0001-01-01T00:00:00Z | 3339-5.6-077 |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0002-12-30T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-038 |

### `DateTime.iso8601`

36 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vectors |
|---|---|---|---|
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-026 |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-027 |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-023 |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-024 |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001 |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59.000000000000000 | leap-second representation (→ :59; INTERPRETATION) | 3339-5.7-025 |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59.000000000000000 | leap-second representation (→ :59; INTERPRETATION) | 3339-5.7-031 |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:59.000000000000000 | TOO LENIENT | 3339-5.7-035 |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:59.000000000000000 | TOO LENIENT | 3339-5.7-037 |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000000000 | TOO LENIENT | 3339-5.6-033 |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-021 |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (as UTC) | 3339-5.6-022 |
| `2026-09-24` | accepted → UTC 2026-09-24T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-020 |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-052 |
| `2026-W39-4T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-054 |
| `2026-267T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-053 |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-057 |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-055, 3339-5.6-056, 3339-5.6-066, 3339-5.6-067 |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000000000000 | WRONG VALUE: instant differs: got 0000-12-30T00:00:00Z, expected 0001-01-01T00:00:00Z | 3339-5.6-077 |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-036 |
| `+10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0002-12-30T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-038 |

### `Time.parse`

20 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vectors |
|---|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | too lenient (space; OK only under a stated profile) | 3339-5.6-015 |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-023 |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-024 |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001 |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-025 |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-031 |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT | 3339-5.7-035 |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00.000000000000000 | TOO LENIENT | 3339-5.7-037 |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-032 |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000000000 | TOO LENIENT | 3339-5.6-033 |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-021 |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.000000000000000 | TOO LENIENT (as host-local time) | 3339-5.6-022 |
| `2026-09-24` | accepted → UTC 2026-09-24T04:00:00.000000000000000 | TOO LENIENT | 3339-5.6-020 |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-052 |
| `2026-W39-4T12:00:00Z` | accepted → UTC 2026-09-25T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-054 |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-039, 3339-5.6-040 |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-057 |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-055, 3339-5.6-056, 3339-5.6-066, 3339-5.6-067 |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-09T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-060 |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-036 |
| `+10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-038 |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-03-01) | 3339-5.7-002 |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2024-03-01) | 3339-5.7-008 |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-05-01) | 3339-5.7-010 |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000000000 | TOO LENIENT (suffix dropped; the offset wins) | 3339-5.6-062 |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-09-24T14:00:00+02:00[+02:00]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-062 |

### `Time.strptime('%Y-%m-%dT%H:%M:%S%z')`

23 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vectors |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24t12:00:00Z' '%Y-%m-% | TOO STRICT | 3339-5.6-003 |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-023 |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-024 |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001 |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-025 |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-031 |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT | 3339-5.7-035 |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00.000000000000000 | TOO LENIENT | 3339-5.7-037 |
| `2026-09-24T12:00:00.1Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24T12:00:00.1Z' '%Y-%m | TOO STRICT | 3339-5.6-008, 3339-A-007 |
| `2026-09-24T12:00:00.123Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24T12:00:00.123Z' '%Y- | TOO STRICT | 3339-5.6-082, 3339-5.6-081 |
| `2026-09-24T12:00:00.123456Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24T12:00:00.123456Z' ' | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24T12:00:00.1234567Z'  | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24T12:00:00.123456789Z | TOO STRICT | 3339-5.6-013, 3339-5.6-014 |
| `2026-09-24T12:00:00.123456789012Z` | rejected: ArgumentError: invalid date or strptime format - '2026-09-24T12:00:00.1234567890 | TOO STRICT | 3339-5.6-006 |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-039, 3339-5.6-040 |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-055, 3339-5.6-056, 3339-5.6-066, 3339-5.6-067 |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-036 |
| `+10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-038 |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-03-01) | 3339-5.7-002 |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2024-03-01) | 3339-5.7-008 |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-05-01) | 3339-5.7-010 |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000000000 | TOO LENIENT (suffix dropped; the offset wins) | 3339-5.6-062 |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-09-24T14:00:00+02:00[+02:00]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix dropped) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT (suffix) | 3339-5.6-062 |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-062 |

### `Time.new(s) [Ruby 3.2+ string form]`

40 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vectors |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: ArgumentError: "+HH:MM", "-HH:MM", "UTC" or "A".."I","K".."Z" expected for utc_o | TOO STRICT | 3339-5.6-003 |
| `2026-09-24T12:00:00z` | rejected: ArgumentError: "+HH:MM", "-HH:MM", "UTC" or "A".."I","K".."Z" expected for utc_o | TOO STRICT | 3339-5.6-002 |
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | too lenient (space; OK only under a stated profile) | 3339-5.6-015 |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-023 |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000000000000 | TOO LENIENT | 3339-5.6-024 |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001 |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | conforming (`sec` returns 60; the instant is the next second) | 3339-5.7-025 |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00.000000000000000 | leap-second representation (→ :00 of the next minute; INTERPRETATION) | 3339-5.7-031 |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00.000000000000000 | TOO LENIENT | 3339-5.7-035 |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00.000000000000000 | TOO LENIENT | 3339-5.7-037 |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789000000 | conforming (lossy: fraction truncated to 9 digits) | 3339-5.6-006 |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.000000000000000 | TOO LENIENT (as host-local time) | 3339-5.6-022 |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-036 |
| `+10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000000000000 | TOO LENIENT | 3339-5.6-037 |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00.000000000000000 | TOO LENIENT | 3339-5.6-038 |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-03-01) | 3339-5.7-002 |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2024-03-01) | 3339-5.7-008 |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000000000000 | TOO LENIENT (rolled over to 2026-05-01) | 3339-5.7-010 |

## Vector runs (310 vectors)

`probes/run_vector_probes.py --lang ruby` (Ruby 3.4.7, 2026-09-26; baseline
`evals/baselines/probes/vector-runs/ruby.txt`). Every key is an RFC 3339 target (`--target-kind rfc3339`), so the
157 RFC 9557 and option vectors are skipped. Pass % = pass / (total − skip − interpretation).

| Key (API) | pass | too lenient | too strict | wrong value | interpretation | pass % |
|---|---|---|---|---|---|---|
| `time-iso8601` (`Time.iso8601`) | 118 | 26 | 0 | 0 | 9 | 81.9 |
| `datetime-rfc3339` (`DateTime.rfc3339`) | 122 | 15 | 2 | 5 | 9 | 84.7 |
| `datetime-iso8601` (`DateTime.iso8601`) | 111 | 26 | 2 | 5 | 9 | 77.1 |
| `time-parse` (`Time.parse`) | 67 | 75 | 2 | 0 | 9 | 46.5 |
| `time-strptime-z` (`Time.strptime('%Y-%m-%dT%H:%M:%S%z')`) | 86 | 42 | 16 | 0 | 9 | 59.7 |
| `time-new` (`Time.new(s)`) | 116 | 26 | 4 | 0 | 7 | 79.5 |

**Leap seconds (INTERPRETATION, not WRONG VALUE).** No Ruby type stores a leap second in its instant. `DateTime`
returns :59 of the same minute. `Time.iso8601`, `Time.parse` and `Time.strptime` return :00 of the next minute,
with the date rolled over (`1990-12-31T23:59:60Z` → `1991-01-01T00:00:00Z`). The runner grades these as
"leap-second representation" (3339-5.8-003, 3339-5.8-004, 3339-5.7-025). `Time.new` keeps `sec` = 60 for a UTC leap
second (3339-5.7-025 passes) and rolls over the offset-shifted one (3339-5.8-004). The other interpretation results
are the leap-second policy vectors (3339-5.7-039, -040, -042, -045, -047) and 3339-5.7-055.

Non-pass results by key (vector IDs):

- **`Time.iso8601`** (26 too lenient): missing offset read as host-local time (3339-5.6-022); `+0100`, `+01`
  (3339-5.6-023, -024); `+01:60` read as `+02:00` (3339-5.6-027); a **2-digit year** `24-01-01…` read as year 24
  (3339-5.6-035); `12024-…` and `-0001-…` (3339-5.6-036, -038); **trailing whitespace** `\n`, space, `\r`,
  `\r\n` and a leading space (3339-5.6-055, -056, -066, -067, -057); `T24:00` → next day (3339-5.7-001); impossible
  dates rolled over (3339-5.7-002 … -016, 8 vectors); `:60` at a **non-UTC** leap-second position
  (`23:59:60+01:00`, `23:59:60-05:00`: 3339-5.7-033, -034) and on other dates or minutes (3339-5.7-035, -036, -037),
  all rolled to the next minute.
- **`DateTime.rfc3339`** (15 too lenient, 2 too strict, 5 wrong value): the space separator (3339-5.6-015);
  `+24:00` and `+01:60` read as `+00:00` (3339-5.6-026, -027); `-0001-…` (3339-5.6-038); trailing and leading
  whitespace (3339-5.6-055, -056, -057, -066, -067); `T24:00` (3339-5.7-001); `:60` without the §5.7 check
  (3339-5.7-033 … -037). **Too strict:** the 1050-digit fraction vectors (3339-5.6-073, -074; 1071 and 1076
  characters) fail with `ArgumentError: string length (…) exceeds the limit 128`; `Date` refuses strings longer
  than 128 characters (`limit:` keyword). Wrong values: the Julian dates above.
- **`DateTime.iso8601`**: as `DateTime.rfc3339`, but it rejects the space and also accepts the ISO 8601 forms:
  date only, `T12:00Z`, no offset (read as UTC), `+0100`, `+01`, `,5`, 2-digit year, `12024-`, `+2024-`, basic
  format, ordinal and week dates (3339-5.6-020 … -024, -033, -035 … -037, -052 … -054).
- **`Time.parse`** (75 too lenient): nearly every malformed vector, among them `_`, fullwidth and NBSP separators
  (3339-5.6-018, -069, -071); `+1:00`, `U+2212` minus and `GMT+1` read as **host-local** time (3339-5.6-025, -028,
  -031); `2024-01-01T120000Z` read as local midnight (3339-errata-001); fullwidth and Arabic-Indic digits read
  as **2026-09-01** (3339-5.6-059, -060); `junk2024-…` (3339-5.6-083); a week date read as today (3339-5.6-054);
  NUL, BOM (3339-5.6-064, -065, -068); weekday prefixes and suffixes (3339-5.4-001 … -003); intervals and
  repeating intervals (3339-1-002 … -004); the suffix `Z[Europe/Paris]` dropped (3339-5.6-062); Appendix A
  fractional minutes and hours (3339-A-001 … -006); offsets with seconds (3339-5.6-063, -084, -085).
  Too strict: the 1050-digit fractions (3339-5.6-073, -074; the same 128-character limit).
- **`Time.strptime('%Y-%m-%dT%H:%M:%S%z')`** (42 too lenient, 16 too strict): every string with a fraction is
  rejected (14 vectors: 3339-5.8-001, -005, 3339-5.6-006, -007, -008, -013, -014, -073, -074, -080, -081, -082,
  3339-5.7-027, 3339-A-007); lowercase `t` (3339-5.6-001, -003). It accepts
  `UTC`, `GMT+1`, `+1:00`, 1-digit fields, a 2-digit year (read as year 24), trailing text (`ZZ`, `Z Fri`,
  `Z/P1D`, `Zjunk`, `Z[Europe/Paris]`, NUL, CR/LF) and offsets with seconds (3339-5.6-025, -030, -031, -035,
  -039, -040, -045, -048, -058, -062, -063, -064, -084, -085, 3339-5.4-002, 3339-1-002, -003, 3339-5.7-051).
- **`Time.new(s)`** (26 too lenient, 4 too strict): rejects lowercase `t`/`z` (3339-5.6-001, -002, -003,
  3339-5.7-026). Accepts a space before `Z` and a **`UTC`** suffix in place of `Z` (`12:00:00 Z`, `12:00:00UTC`:
  3339-5.6-029, -030), the space separator (3339-5.6-015), a missing offset as host-local time (3339-5.6-022),
  `+0100`, `+01` (3339-5.6-023, -024), offsets with seconds `+01:00:00`, `-00:44:30`, `+00:09:21`
  (3339-5.6-063, -084, -085), `12024-`, `+2024-`, `-0001-` (3339-5.6-036 … -038), `T24:00` (3339-5.7-001),
  impossible dates (3339-5.7-002 … -016) and `:60` anywhere (3339-5.7-033 … -037).

## Producers (formatters)

| Call | Output | RFC verdict |
|---|---|---|
| `Time#xmlschema / #iso8601 (utc)` | `2026-09-24T12:00:00Z` | conforming |
| `Time#xmlschema(3)` | `2026-09-24T12:00:00.123Z` | conforming |
| `Time#xmlschema (local)` | `2026-09-24T08:00:00-04:00` | conforming |
| `Time#to_s` | `2026-09-24 12:00:00 UTC` | WRONG OUTPUT (space separator, ' UTC' suffix) |
| `Time#inspect` | `2026-09-24 12:00:00 UTC` | WRONG OUTPUT (space separator, ' UTC' suffix) |
| `DateTime#rfc3339` | `2026-09-24T14:00:00+02:00` | conforming |
| `Time#to_json (json gem, no ActiveSupport)` | `2026-09-24 12:00:00 UTC` | WRONG OUTPUT (space separator, ' UTC' suffix) |
| `Time#strftime('%Y-%m-%dT%H:%M:%S%z')` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (offset without colon) |
| `Time#strftime('%FT%T%:z')` | `2026-09-24T14:00:00+02:00` | conforming |
| `Time.utc(10000).xmlschema` | `10000-01-01T00:00:00Z` | WRONG OUTPUT (expanded/signed year) |
| `Time.utc(-1).xmlschema` | `-0001-01-01T00:00:00Z` | WRONG OUTPUT (expanded/signed year) |
| `Time.utc(12).xmlschema` | `0012-01-01T00:00:00Z` | conforming |
| `Time#getlocal('+00:00:30').xmlschema` | `2026-09-24T12:00:30+00:00` | WRONG VALUE (offset seconds dropped: string denotes 12:00:30Z, true instant 12:00:00Z) |

## Detect in code

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `Time\.parse\(\|DateTime\.parse\(\|Date\._parse` | It accepts nearly everything and silently drops `[!…]` suffixes. It read an Arabic-Indic year as **2026-09-09**. | the strict regex + `Time.iso8601` |
| `Time\.(iso8601\|xmlschema)\(` | It accepts a missing offset (host-local), `+0200`, `+02`, `+01:60` (as `+02:00`), a 2-digit year (year 24), leading and trailing whitespace and 5-digit years. It **rolls** `2026-04-31` to `05-01`, `:60` on any date to the next minute, and `T24:00` to the next day. | the strict regex first |
| `DateTime\.(rfc3339\|iso8601)\(\|DateTime\.new` | It accepts `+24:00` and reads it as **+00:00**. It accepts `T24:00` and a space. It uses the Julian calendar before 1582 (2 days off at year 1). It rejects strings longer than 128 characters (long fractions). | `Time.iso8601` behind the strict regex. Avoid `DateTime`. |
| `Time\.new\(\s*[a-z_]\w*\s*\)` (string form) | It rejects `t`/`z` (**TOO STRICT**). It accepts a missing offset, ` Z`, `UTC`, offsets with seconds and invalid dates (the accessors keep `02-30` and `:60`; the instant rolls over). | the same |
| `\.to_s\b\|\.to_json\b\|\.inspect\b` on `Time` for the wire (no ActiveSupport) | `2026-09-24 12:00:00 UTC` | `time.utc.iso8601(3)` / `xmlschema` |
| `strftime\([^)]*%z` | `+0200` has no colon | `%:z` or `xmlschema` |
| `getlocal\(['"][+-][0-9]{2}:[0-9]{2}:[0-9]{2}` · `utc_offset` that is not a multiple of 60 | `xmlschema` drops the offset seconds but keeps the local wall time: 12:00:00Z prints as `12:00:30+00:00` (**WRONG VALUE**) | convert to UTC before you serialize |

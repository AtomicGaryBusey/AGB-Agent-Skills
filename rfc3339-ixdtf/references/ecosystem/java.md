# Java: RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-24.** Java Temurin 25.0.1. macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Probe program: `probes/Probe.java` (reads `probes/inputs.json`, 59 strings; `probes/analyze.py` turns its JSON-lines results into the tables below). The raw result tables of the 2026-09-24 run were not committed: re-run the probe to regenerate them.

**Vector runs, probed 2026-09-26** (Temurin 25.0.1, 310 vectors): `Probe.java adapter <key>` under
`probes/run_vector_probes.py`; baseline `evals/baselines/probes/vector-runs/java.txt`. See
[Vector runs](#vector-runs-310-vectors). The "Vector" column of each consumer table gives the vector of the same
category and its result for that API; "legacy probe only" means no vector covers that input.

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **Java `ofPattern(...)`** uses the `SMART` resolver by default. It **clamps** instead of rejecting:
  `2024-02-30` became `2024-02-29`, `2026-02-29` became `2026-02-28`, `2026-04-31` became `2026-04-30`, and `T24:00`
  became the next day.
- **Java `SimpleDateFormat`** and **Ruby `DateTime`** use the Julian calendar before 1582.
  `0001-01-01T00:00:00Z` came back as UTC `0000-12-30`, which is **2 days off** (vectors 3339-5.6-075..078, and
  3339-5.6-004 in lenient mode: instant check, all 2 days early). `SimpleDateFormat` also accepted Arabic-Indic and
  fullwidth digits, a leading space, a 2-digit year, a 5-digit year, 1-digit month/day/hour/minute and a space
  before `Z`, even when the probe checked `ParsePosition` (3339-5.6-029, -035, -036, -039, -040, -045, -048, -057,
  -059, -060).
- **Java `Instant.parse`** accepted `T24:00:00Z` (as the next day, 3339-5.7-001). It accepts `:60` only as a
  **local** `23:59:60`, on any date and with any offset, and maps it to `:59`: `2016-12-31T23:59:60+01:00` and
  `…-05:00` (3339-5.7-033/034, not a leap second at those offsets) and `2016-12-30T23:59:60Z` (3339-5.7-035) are
  accepted. It rejects `23:58:60` and `12:00:60`, and it rejects the real offset-shifted leap seconds
  `2016-12-31T18:59:60-05:00`, `2017-01-01T00:59:60+01:00`, `2017-01-01T05:29:60+05:30` and
  `1990-12-31T15:59:60-08:00` (3339-5.7-030..032, 3339-5.8-004).
- **Offsets with seconds:** `OffsetDateTime.parse`, `ZonedDateTime.parse`, `Instant.parse`, `ISO_DATE_TIME` and
  lenient `SimpleDateFormat` accept `+01:00:00`, `-00:44:30` and `+00:09:21` (3339-5.6-063, -084, -085; also
  9557-4.1-049 with a zone) and use the seconds in the instant. The `XXX` patterns and `ParsePosition`-checked
  `SimpleDateFormat` reject them.
- **Java `ZonedDateTime.parse`** reads a pre-RFC 9557 bracket dialect. It rejects every `!` (13 valid critical
  zones, e.g. 9557-3.4-007, -019, -031; 9557-3.3-006/007) and every `key=value` tag, including known elective ones
  (`[u-ca=hebrew]`, 9557-5-001, 9557-3.3-008, 9557-4.2-003: **TOO STRICT**) and unknown ones (9557-3.3-001: an
  interpretation, but rejecting every elective tag is an Advisory). It accepts a bracketed offset with seconds
  `Z[+01:00:00]` (9557-4.1-051), a missing seconds field `2020-01-01T00:00+01:00[Europe/Paris]` (9557-1.2-002) and
  `+01` (3339-5.6-024). It silently takes the offset when the offset and zone are inconsistent (elective case,
  9557-3.4-001/033). This is permitted, but no error is raised.

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict "conforming".

### `OffsetDateTime.parse (ISO_OFFSET_DATE_TIME)`

49 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed: Zo | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00Z | TOO LENIENT | 3339-5.6-024: TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: DateTimeParseException: Text '2016-12-31T23:59:60Z' could not be parsed: Invalid | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed: In | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-032: TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-021: TOO LENIENT |
| `+10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-038: TOO LENIENT |

### `ZonedDateTime.parse (ISO_ZONED_DATE_TIME)`

44 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed: Zo | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00Z | TOO LENIENT | 3339-5.6-024: TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: DateTimeParseException: Text '2016-12-31T23:59:60Z' could not be parsed: Invalid | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed: In | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-032: TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-021: TOO LENIENT |
| `+10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-038: TOO LENIENT |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | rejected: DateTimeParseException: Text '2026-09-24T14:00:00+02:00[!Europe/Paris]' could no | TOO STRICT (vs RFC 9557) | 9557-3.4-019: TOO STRICT |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00Z[!Europe/Paris]' could not be  | TOO STRICT (vs RFC 9557) | 9557-3.4-031: TOO STRICT |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00Z[u-ca=hebrew]' could not be pa | TOO STRICT (vs RFC 9557) | 9557-5-001: TOO STRICT |
| `2026-09-24T12:00:00Z[x-foo=bar]` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00Z[x-foo=bar]' could not be pars | interpretation (rejects every elective tag: Advisory, rule 4) | 9557-3.3-001: interpretation (rejected) |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | interpretation (MAY; offset wins) | 9557-3.4-001: interpretation (accepted) |

### `Instant.parse (ISO_INSTANT)`

49 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed at  | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00Z | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001: TOO LENIENT |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59Z | conforming (leap-second representation: :59) | 3339-5.7-025: pass |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed at  | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:59Z | TOO LENIENT | 3339-5.7-035: TOO LENIENT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-032: TOO LENIENT |
| `+10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-038: TOO LENIENT |

### `DateTimeFormatter.ISO_DATE_TIME -> Instant.from`

45 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed: Zo | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: DateTimeParseException: Text '2016-12-31T23:59:60Z' could not be parsed: Invalid | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed: In | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-032: TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-021: TOO LENIENT |
| `+10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-038: TOO LENIENT |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | rejected: DateTimeParseException: Text '2026-09-24T14:00:00+02:00[!Europe/Paris]' could no | TOO STRICT (vs RFC 9557) | 9557-3.4-019: TOO STRICT |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00Z[!Europe/Paris]' could not be  | TOO STRICT (vs RFC 9557) | 9557-3.4-031: TOO STRICT |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00Z[u-ca=hebrew]' could not be pa | TOO STRICT (vs RFC 9557) | 9557-5-001: TOO STRICT |
| `2026-09-24T12:00:00Z[x-foo=bar]` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00Z[x-foo=bar]' could not be pars | interpretation (rejects every elective tag: Advisory, rule 4) | 9557-3.3-001: interpretation (rejected) |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | interpretation (MAY; offset wins) | 9557-3.4-001: interpretation (accepted) |

### `ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX") [SMART]`

41 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: DateTimeParseException: Text '2026-09-24t12:00:00Z' could not be parsed at index | TOO STRICT | 3339-5.6-003: TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00z' could not be parsed at index | TOO STRICT | 3339-5.6-002: TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed: Zo | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00Z | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001: TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: DateTimeParseException: Text '2016-12-31T23:59:60Z' could not be parsed: Invalid | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed: In | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.1Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.1Z' could not be parsed at ind | TOO STRICT | 3339-5.6-008: TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123Z' could not be parsed at i | TOO STRICT | 3339-5.6-082: TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456Z' could not be parsed a | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.1234567Z' could not be parsed  | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789Z' could not be parse | TOO STRICT | 3339-5.6-013: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `0000-01-01T00:00:00Z` | rejected: DateTimeParseException: Text '0000-01-01T00:00:00Z' could not be parsed: Invalid | too strict (range limit) | 3339-5.6-004: TOO STRICT |
| `+10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-02-28T12:00:00Z | TOO LENIENT (rolled over to 2026-02-28) | 3339-5.7-002: TOO LENIENT |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-02-29T12:00:00Z | TOO LENIENT (rolled over to 2024-02-29) | 3339-5.7-008: TOO LENIENT |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-04-30T12:00:00Z | TOO LENIENT (rolled over to 2026-04-30) | 3339-5.7-010: TOO LENIENT |

### `ofPattern("uuuu-MM-dd'T'HH:mm:ss[.SSSSSSSSS]XXX").STRICT`

46 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: DateTimeParseException: Text '2026-09-24t12:00:00Z' could not be parsed at index | TOO STRICT | 3339-5.6-003: TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00z' could not be parsed at index | TOO STRICT | 3339-5.6-002: TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed: Zo | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: DateTimeParseException: Text '2016-12-31T23:59:60Z' could not be parsed: Invalid | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed: In | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.1Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.1Z' could not be parsed at ind | TOO STRICT | 3339-5.6-008: TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123Z' could not be parsed at i | TOO STRICT | 3339-5.6-082: TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456Z' could not be parsed a | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.1234567Z' could not be parsed  | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `+10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0001-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-038: TOO LENIENT |

### `ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'") -> LocalDateTime`

37 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: DateTimeParseException: Text '2026-09-24t12:00:00Z' could not be parsed at index | TOO STRICT | 3339-5.6-003: TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00z' could not be parsed at index | TOO STRICT | 3339-5.6-002: TOO STRICT |
| `2026-09-24T12:00:00+00:00` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+00:00' could not be parsed at  | TOO STRICT | 3339-4.3-003: TOO STRICT |
| `2026-09-24T12:00:00-00:00` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00-00:00' could not be parsed at  | TOO STRICT | 3339-4.3-002: TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+23:59' could not be parsed at  | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2026-09-24T12:00:00+05:30` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00+05:30' could not be parsed at  | TOO STRICT | 3339-5.6-012: TOO STRICT |
| `2026-09-24T24:00:00Z` | accepted → UTC naive:2026-09-25T00:00 | TOO LENIENT | 3339-5.7-001: TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: DateTimeParseException: Text '2016-12-31T23:59:60Z' could not be parsed: Invalid | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: DateTimeParseException: Text '2016-12-31T18:59:60-05:00' could not be parsed at  | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.1Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.1Z' could not be parsed at ind | TOO STRICT | 3339-5.6-008: TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123Z' could not be parsed at i | TOO STRICT | 3339-5.6-082: TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456Z' could not be parsed a | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.1234567Z' could not be parsed  | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789Z' could not be parse | TOO STRICT | 3339-5.6-013: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: DateTimeParseException: Text '2026-09-24T12:00:00.123456789012Z' could not be pa | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `0000-01-01T00:00:00Z` | rejected: DateTimeParseException: Text '0000-01-01T00:00:00Z' could not be parsed: Invalid | too strict (range limit) | 3339-5.6-004: TOO STRICT |
| `9999-12-31T23:59:59Z` | accepted → UTC naive:9999-12-31T23:59:59 | conforming value, naive result (`'Z'` is a literal: the offset is never read) | 3339-5.6-005: pass |
| `+10000-01-01T00:00:00Z` | accepted → UTC naive:+10000-01-01T00:00 | TOO LENIENT | legacy probe only |
| `+002026-09-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00 | TOO LENIENT | legacy probe only |
| `2026-02-29T12:00:00Z` | accepted → UTC naive:2026-02-28T12:00 | TOO LENIENT | 3339-5.7-002: TOO LENIENT |
| `2024-02-30T12:00:00Z` | accepted → UTC naive:2024-02-29T12:00 | TOO LENIENT | 3339-5.7-008: TOO LENIENT |
| `2026-04-31T12:00:00Z` | accepted → UTC naive:2026-04-30T12:00 | TOO LENIENT | 3339-5.7-010: TOO LENIENT |

### `SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX") [lenient default]`

23 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: RuntimeException: Unparseable date: "2026-09-24t12:00:00Z" | TOO STRICT | 3339-5.6-003: TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00z" | TOO STRICT | 3339-5.6-002: TOO STRICT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00Z | TOO LENIENT (→ 2026-09-25 00:00:00) | 3339-5.7-001: TOO LENIENT |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00Z | conforming (leap-second representation: next minute) | 3339-5.7-025: pass |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00Z | conforming (leap-second representation: next minute) | 3339-5.7-031: pass |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00Z | TOO LENIENT | 3339-5.7-035: TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00Z | TOO LENIENT | 3339-5.7-037: TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00.1Z" | TOO STRICT | 3339-5.6-008: TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00.123Z" | TOO STRICT | 3339-5.6-082: TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00.123456Z" | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00.1234567Z" | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00.123456789Z" | TOO STRICT | 3339-5.6-013: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: RuntimeException: Unparseable date: "2026-09-24T12:00:00.123456789012Z" | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-039: TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-057: TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-055: TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-060: TOO LENIENT |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00Z | WRONG VALUE: instant differs: got 0000-12-30T00:00:00Z, expected 0001-01-01T00:00:00Z | 3339-5.6-077: WRONG VALUE (instant check; the runner gets no fields) |
| `10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-036: TOO LENIENT |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0002-12-30T00:00:00Z | TOO LENIENT | 3339-5.6-038: TOO LENIENT |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00Z | TOO LENIENT (rolled over to 2026-03-01) | 3339-5.7-002: TOO LENIENT |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00Z | TOO LENIENT (rolled over to 2024-03-01) | 3339-5.7-008: TOO LENIENT |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00Z | TOO LENIENT (rolled over to 2026-05-01) | 3339-5.7-010: TOO LENIENT |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00Z | lenient (accepts suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00Z | lenient (accepts suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT (suffix dropped) | 3339-5.6-062: TOO LENIENT |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00Z | lenient (accepts suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | accepted → UTC 2026-09-24T12:00:00Z | lenient (accepts suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00Z | lenient (accepts suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT (suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | conforming (MAY; offset wins) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | TOO LENIENT (suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T14:00:00+02:00[+02:00]` | accepted → UTC 2026-09-24T12:00:00Z | lenient (accepts suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT (suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT (suffix) | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | legacy probe only (IXDTF vectors not run on an RFC 3339 parser) |

### `SimpleDateFormat.parse, then check ParsePosition==len`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict | Vector (2026-09-26) |
|---|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: RuntimeException: unparsed at 0/10 | TOO STRICT | 3339-5.6-003: TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | 3339-5.6-002: TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: RuntimeException: unparsed at 0/25 | too strict (offset range) | 3339-5.6-009: TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: RuntimeException: unparsed at 0/20 | too strict (no leap second) | 3339-5.7-025: TOO STRICT |
| `2016-12-31T18:59:60-05:00` | rejected: RuntimeException: unparsed at 0/25 | too strict (no leap second) | 3339-5.7-031: TOO STRICT |
| `2026-09-24T12:00:00.1Z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | 3339-5.6-008: TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | 3339-5.6-082: TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | 3339-5.6-013: TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: RuntimeException: unparsed at 0/20 | TOO STRICT | 3339-5.6-006: TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-039: TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-057: TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT | 3339-5.6-060: TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: RuntimeException: unparsed at 0/20 | too strict (range limit) | 3339-5.6-004: TOO STRICT |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00Z | WRONG VALUE: instant differs: got 0000-12-30T00:00:00Z, expected 0001-01-01T00:00:00Z | 3339-5.6-077: WRONG VALUE (instant check; the runner gets no fields) |
| `10000-01-01T00:00:00Z` | accepted → UTC +10000-01-01T00:00:00Z | TOO LENIENT | 3339-5.6-036: TOO LENIENT |

## Vector runs (310 vectors)

Probed 2026-09-26 (Temurin 25.0.1). `--target-kind` is `ixdtf` for the two bracket-aware APIs, else `rfc3339`
(157 IXDTF vectors skipped); 29 option vectors skipped (`--target-options fixed`). The Java adapters return the
UTC instant, not as-written fields, so the runner cannot see a wrong value: the WRONG VALUE counts come from
`probes/swift/instant_check.py` run on each key's JSON report.

| Key (API) | pass | too lenient | too strict | wrong value (instant check) | interp. | pass % |
|---|---|---|---|---|---|---|
| `offsetdatetime` (`OffsetDateTime.parse`) | 123 | 8 | 16 | 0 | 6 | 83.7 |
| `zoneddatetime` (`ZonedDateTime.parse`, ixdtf) | 197 | 11 | 34 | 0 | 35 | 81.4 |
| `instant` (`Instant.parse`) | 128 | 10 | 9 | 0 (15 leap seconds → `:59`) | 6 | 87.1 |
| `iso-date-time` (`ISO_DATE_TIME` → `Instant.from`, ixdtf) | 198 | 10 | 34 | 0 | 35 | 81.8 |
| `pattern-smart` (`ofPattern(…XXX)` SMART) | 107 | 9 | 31 | 0 | 6 | 72.8 |
| `pattern-strict` (`ofPattern(uuuu…[.SSSSSSSSS]XXX)` STRICT) | 119 | 1 | 27 | 0 | 6 | 81.0 |
| `pattern-literal-z` (`ofPattern(…'Z'")` → `LocalDateTime`) | 100 | 9 | 38 | not compared (naive) | 6 | 68.0 |
| `sdf-lenient` (`SimpleDateFormat`, lenient) | 82 | 47 | 18 | **5** (Julian) | 6 | 55.8 |
| `sdf-strict-pos` (`SimpleDateFormat` + `ParsePosition`) | 106 | 10 | 31 | **4** (Julian) | 6 | 72.1 |

What the vectors add to the tables above (vector IDs in parentheses):

- **Every `java.time` ISO parser** (`offsetdatetime`, `zoneddatetime`, `instant`, `iso-date-time`): too strict on
  more than 9 fraction digits (3339-5.6-006, -073, -074) and on `±23:59` (3339-5.6-009/010, range limit ±18 h);
  too lenient on an empty fraction `.Z` (3339-5.6-032, 3339-A-005), `-0001` (3339-5.6-038) and offsets with
  seconds (above). They reject `+2024-…` (4-digit signed year, 3339-5.6-037) and `12024-…` (3339-5.6-036).
- **`OffsetDateTime` / `ISO_DATE_TIME` / `ZonedDateTime`:** accept `T12:00Z` (no seconds, 3339-5.6-021); reject
  every leap second (3339-5.7-025..032, -038, 3339-5.8-003/004: no leap second). `OffsetDateTime` and
  `ZonedDateTime` accept `+01` (3339-5.6-024); `ISO_DATE_TIME` rejects it.
- **`Instant.parse`:** see the leap-second note above; 10 too lenient = empty fraction ×2, `-0001`, offset seconds
  ×3, `T24:00`, local `23:59:60` at `+01:00`/`-05:00`/on 12-30.
- **`ofPattern` SMART and `'Z'` literal:** too lenient only by resolving: `T24:00` (3339-5.7-001) and 8 invalid days
  clamped to the month end (3339-5.7-002, -004, -006, -008, -010, -012, -014, -016). Too strict on any fraction,
  lower-case `t`/`z`, year 0000, `0000-02-29` (3339-5.7-007), leap seconds; the `'Z'` literal also rejects every
  numeric offset, `+00:00` and `-00:00` included (3339-4.3-002/003, 3339-5.8-002).
- **`ofPattern(…).STRICT`:** 1 too lenient (`-0001`, 3339-5.6-038); too strict only on lower case, fractions other
  than 9 digits (e.g. `.5`, `.052`, 3339-5.6-008, -082), `±23:59` and leap seconds.
- **`SimpleDateFormat` lenient (47 too lenient):** every field overflow rolls over (`2024-13-10`, `01-32`, `T25:00`,
  `12:60`, `:61`, `:99`, 3339-5.6-041..050), invalid days roll into the next month (3339-5.7-002..016), `:60`
  anywhere rolls into the next minute (3339-5.7-033..037), trailing text is ignored (`
`, space, `ZZ`, ` `, CR,
  CRLF, ` Fri`, `/P1D`, a suffix: 3339-5.6-055..067, 3339-5.4-002, 3339-1-002/003, 3339-5.7-051), plus the
  digit and width forms above and offset seconds. The real leap seconds `23:59:60Z` and `18:59:60-05:00` pass as
  the next minute (leap-second representation); `23:59:60z` and `23:59:60.999Z` are rejected (3339-5.7-026/027).
  It rejects every fraction (`.5`, `.52`, `.052`: too strict).
- **`SimpleDateFormat` + `ParsePosition` (10 too lenient):** the non-lenient form (`setLenient(false)`) still
  accepts the width and digit forms (3339-5.6-029, -035, -036, -039, -040, -045, -048, -057, -059, -060) but
  rejects overflows, invalid days, trailing text, offset seconds and every leap second.
- **Interpretations** (IXDTF keys, 35): elective inconsistent offsets are accepted with the offset
  (9557-3.4-001, -006, -011, -033); `Z[+05:00]`, `Z[-00:00]`, `Z[Z]` are accepted (9557-4.1-006/007/041); every
  unknown elective tag, repeated tag and unknown zone is rejected (e.g. 9557-3.3-001, -005, -013, 9557-3.4-021).

## Producers (formatters)

| Call | Output | RFC verdict |
|---|---|---|
| `OffsetDateTime.toString() [:00 seconds]` | `2026-09-24T12:00Z` | WRONG OUTPUT (no seconds) |
| `OffsetDateTime.toString() [120ms]` | `2026-09-24T12:00:05.120Z` | conforming |
| `ZonedDateTime.toString() [Europe/Paris, :00 seconds]` | `2026-09-24T14:00+02:00[Europe/Paris]` | WRONG OUTPUT (no seconds) |
| `ZonedDateTime.toString() [ZoneId.of("UTC")]` | `2026-09-24T12:00Z[UTC]` | WRONG OUTPUT (no seconds) |
| `ZonedDateTime.toString() [ZoneOffset.UTC]` | `2026-09-24T12:00Z` | WRONG OUTPUT (no seconds) |
| `ZonedDateTime.toString() [1850 Europe/Paris, LMT]` | `1850-01-01T00:00+00:09:21[Europe/Paris]` | WRONG OUTPUT (no seconds, offset has seconds) |
| `ISO_OFFSET_DATE_TIME.format(1850 Paris LMT)` | `1850-01-01T00:00:00+00:09:21` | WRONG OUTPUT (offset has seconds) |
| `ISO_ZONED_DATE_TIME.format(ZDT Paris)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `ISO_OFFSET_DATE_TIME.format(ODT UTC)` | `2026-09-24T12:00:00Z` | conforming |
| `ISO_DATE_TIME.format(LocalDateTime) [no offset]` | `2026-09-24T12:00:00` | WRONG OUTPUT (no offset) |
| `Instant.toString()` | `2026-09-24T12:00:00Z` | conforming |
| `Instant.toString() [year 10000]` | `+10000-01-01T00:00:00Z` | WRONG OUTPUT (expanded/signed year) |
| `Instant.toString() [year -1]` | `-0001-01-01T00:00:00Z` | WRONG OUTPUT (expanded/signed year) |
| `java.util.Date.toString()` | `Thu Sep 24 08:00:00 EDT 2026` | WRONG OUTPUT (not ISO-shaped) |
| `SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ")` | `2026-09-24T12:00:00+0000` | WRONG OUTPUT (offset without colon) |
| `SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'") [default TZ!]` | `2026-09-24T08:00:00Z` | WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z) |
| `SimpleDateFormat("YYYY-MM-dd'T'HH:mm:ssXXX") [week-year YYYY, 2026-12-28]` | `2027-12-28T12:00:00Z` | WRONG VALUE (week-based year: 2026-12-28 printed as 2027) |
| `ofPattern("YYYY-MM-dd'T'HH:mm:ssXXX") [week-based-year, 2026-12-28]` | `2027-12-28T12:00:00Z` | WRONG VALUE (week-based year: 2026-12-28 printed as 2027) |

See also `jsonschema.md` (networknt `json-schema-validator` with and without itu; openapi-generator `java`/`kotlin` adapters).

## Detect in code

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `(OffsetDateTime\|ZonedDateTime\|LocalDateTime)[^;]*\.toString\(\)` or implicit string concatenation to the wire | It **omits `:00` seconds** (`2026-09-24T12:00Z`, `…14:00+02:00[Europe/Paris]`). `ZoneId.of("UTC")` gives `Z[UTC]`. LMT offsets give `+00:09:21`. | `DateTimeFormatter.ISO_OFFSET_DATE_TIME.format(x)` (always prints seconds), or `ISO_ZONED_DATE_TIME` for IXDTF |
| `Instant[^;]*\.toString\(\)` | Correct for years 0000–9999. Prints `+10000-…` / `-0001-…` outside that range. | range-check the year |
| `ofPattern\("[^"]*YYYY` · `SimpleDateFormat\("[^"]*YYYY` | Week-based year: `2026-12-28` prints as `2027-12-28` | `uuuu` (java.time) / `yyyy` |
| `ofPattern\(` without `withResolverStyle\(ResolverStyle\.STRICT\)` | SMART clamps `2024-02-30` to `02-29` and reads `T24:00` as the next day | `.withResolverStyle(ResolverStyle.STRICT)` + `uuuu` |
| `'Z'` inside a pattern string | Formatting prints local wall time labelled Z (`08:00:00Z` for 12:00Z). Parsing ignores the offset. | `XXX` / `ISO_OFFSET_DATE_TIME` |
| `new SimpleDateFormat\(\|java\.util\.Date` | Lenient by default: it accepts `:60` on any date, Feb 30, Arabic-Indic digits and garbage suffixes. It uses the Julian calendar before 1582 (2 days off at year 1). `Z` gives `+0000`. | java.time |
| `OffsetDateTime\.parse\(\|ISO_OFFSET_DATE_TIME\|ISO_DATE_TIME` | It accepts `T12:00Z` (no seconds), `+02`, `.Z` (empty fraction), offsets with seconds (`+01:00:00`, `-00:44:30`) and signed or 5-digit years. It rejects more than 9 fraction digits, offsets above ±18 h and every leap second. | the strict regex first |
| `Instant\.parse\(\|ISO_INSTANT` | It also accepts `T24:00:00Z` and a local `23:59:60` on any date and at any offset (mapped to `:59`), but rejects the real offset-shifted leap seconds (`18:59:60-05:00`) | the strict regex + a leap-second policy |
| `ZonedDateTime\.parse\(\|ISO_ZONED_DATE_TIME` on IXDTF input | It rejects `[!…]` and every `[key=value]` tag, including elective ones (**TOO STRICT vs RFC 9557**). It accepts `Z[+01:00:00]` and a missing seconds field. It silently lets the offset win on an elective conflict. | parse the suffix yourself, then `ZonedDateTime.ofStrict` or compare offsets |
| `LocalDateTime\.parse\(` on timestamps | It rejects `Z`/offsets, or it drops them with a `'Z'` literal pattern | `OffsetDateTime` / `Instant` |

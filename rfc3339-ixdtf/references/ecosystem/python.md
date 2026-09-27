# Python: RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-24.** Python 3.13.9 (+ python-dateutil 2.9.0.post0, pydantic 2.13.5, jsonschema 4.26.0 + rfc3339-validator 0.1.4). macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Probe program: `probes/probe_python.py (and `probe_jsonschema_nodep.py` for jsonschema without its extra)` (reads `probes/inputs.json`, 59 strings; `probes/analyze.py` turns its JSON-lines results into the tables below). The raw result tables of the 2026-09-24 run were not committed: re-run the probe to regenerate them.

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **Python**:
  - `strptime` with `%Y` or `%z` accepts non-ASCII digits (`\d` is Unicode) and 1-digit months. `%f` accepts at most 6 digits.
  - `fromisoformat` accepts `t` but not `z`. It also accepts week dates and the basic format.
  - `fromisoformat` takes **any** single character as the date-time separator (space, `_`, fullwidth `Ｔ`, NBSP),
    accepts a trailing NUL, a space before `Z`, `+01:60` (as `+02:00`), and offsets with seconds. See
    "Vector runs" for the vector IDs.
  - `rfc3339-validator` (used by jsonschema) accepts a trailing `\n`. This is the Python `re` `$` behaviour.
  - Without the optional `rfc3339-validator` package, **jsonschema does not check `format: date-time`**, even with a
    `FormatChecker`: `"not a date"` passed (`probe_jsonschema_nodep.py`, clean venv with jsonschema 4.26.0).

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict "conforming".
The tables come from the 59 legacy probe strings (2026 dates). In the four sections with a vector adapter
(`fromisoformat` and the three `strptime` formats), the ID in parentheses is the conformance vector with the same
form that got the same verdict in the 2026-09-26 vector run (see "Vector runs" below). "legacy probe only" means
that no vector has that form. `dateutil`, pydantic and jsonschema have no vector adapter: every row in their
sections is legacy probe only.

### `datetime.fromisoformat`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00z` | rejected: ValueError: Invalid isoformat string: '2026-09-24T12:00:00z' | TOO STRICT (3339-5.6-002) |
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT (3339-5.6-023) |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT (3339-5.6-024) |
| `2016-12-31T23:59:60Z` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) (3339-5.7-025) |
| `2016-12-31T18:59:60-05:00` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) (3339-5.7-031) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) — legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) (3339-5.6-013) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) (3339-5.6-006) |
| `2026-09-24T12:00:00.Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (3339-5.6-032) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000 | TOO LENIENT (3339-5.6-033) |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (3339-5.6-021) |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00 | TOO LENIENT (naive/local result) (3339-5.6-022) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00 | TOO LENIENT (naive/local result) (3339-5.6-020) |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (3339-5.6-052) |
| `2026-W39-4T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (3339-5.6-054) |
| `0000-01-01T00:00:00Z` | rejected: ValueError: year 0 is out of range | too strict (range limit) (3339-5.6-004) |

### `strptime('%Y-%m-%dT%H:%M:%S%z')`

46 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00z` | rejected: ValueError: time data '2026-09-24T12:00:00z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-5.6-002) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT (3339-5.6-023) |
| `2016-12-31T23:59:60Z` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) (3339-5.7-025) |
| `2016-12-31T18:59:60-05:00` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) (3339-5.7-031) |
| `2026-09-24T12:00:00.1Z` | rejected: ValueError: time data '2026-09-24T12:00:00.1Z' does not match format '%Y-%m-%dT% | TOO STRICT (3339-5.6-008) |
| `2026-09-24T12:00:00.123Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123Z' does not match format '%Y-%m-%d | TOO STRICT (3339-5.6-082) |
| `2026-09-24T12:00:00.123456Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456Z' does not match format '%Y-%m | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: ValueError: time data '2026-09-24T12:00:00.1234567Z' does not match format '%Y-% | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456789Z' does not match format '%Y | TOO STRICT (3339-5.6-013) |
| `2026-09-24T12:00:00.123456789012Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456789012Z' does not match format  | TOO STRICT (3339-5.6-006) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (3339-5.6-039) |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (3339-5.6-060) |
| `0000-01-01T00:00:00Z` | rejected: ValueError: year 0 is out of range | too strict (range limit) (3339-5.6-004) |

### `strptime('%Y-%m-%dT%H:%M:%S.%f%z')`

43 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | rejected: ValueError: time data '2026-09-24T12:00:00Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-4.3-001) |
| `2026-09-24t12:00:00Z` | rejected: ValueError: time data '2026-09-24t12:00:00Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-5.6-003) |
| `2026-09-24T12:00:00z` | rejected: ValueError: time data '2026-09-24T12:00:00z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-5.6-002) |
| `2026-09-24T12:00:00+00:00` | rejected: ValueError: time data '2026-09-24T12:00:00+00:00' does not match format '%Y-%m-% | TOO STRICT (3339-4.3-003) |
| `2026-09-24T12:00:00-00:00` | rejected: ValueError: time data '2026-09-24T12:00:00-00:00' does not match format '%Y-%m-% | TOO STRICT (3339-4.3-002) |
| `2026-09-24T12:00:00+23:59` | rejected: ValueError: time data '2026-09-24T12:00:00+23:59' does not match format '%Y-%m-% | TOO STRICT (the format needs a fraction) (3339-5.6-009) |
| `2026-09-24T12:00:00+05:30` | rejected: ValueError: time data '2026-09-24T12:00:00+05:30' does not match format '%Y-%m-% | TOO STRICT (3339-5.7-032) |
| `2016-12-31T23:59:60Z` | rejected: ValueError: time data '2016-12-31T23:59:60Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (the format needs a fraction; no leap second either) (3339-5.7-025) |
| `2016-12-31T18:59:60-05:00` | rejected: ValueError: time data '2016-12-31T18:59:60-05:00' does not match format '%Y-%m-% | TOO STRICT (the format needs a fraction; no leap second either) (3339-5.7-031) |
| `2026-09-24T12:00:00.1234567Z` | rejected: ValueError: time data '2026-09-24T12:00:00.1234567Z' does not match format '%Y-% | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456789Z' does not match format '%Y | TOO STRICT (3339-5.6-013) |
| `2026-09-24T12:00:00.123456789012Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456789012Z' does not match format  | TOO STRICT (3339-5.6-006) |
| `0000-01-01T00:00:00Z` | rejected: ValueError: time data '0000-01-01T00:00:00Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (the format needs a fraction; year 0 is also out of range) (3339-5.6-004) |
| `0001-01-01T00:00:00Z` | rejected: ValueError: time data '0001-01-01T00:00:00Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-5.6-077) |
| `9999-12-31T23:59:59Z` | rejected: ValueError: time data '9999-12-31T23:59:59Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-5.6-005) |
| `2024-02-29T12:00:00Z` | rejected: ValueError: time data '2024-02-29T12:00:00Z' does not match format '%Y-%m-%dT%H: | TOO STRICT (3339-5.7-003) |

### `strptime('%Y-%m-%dT%H:%M:%SZ')`

38 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00 | WRONG VALUE: offset discarded (naive result) (3339-4.3-001) |
| `2026-09-24t12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00 | WRONG VALUE: offset discarded (naive result) (vector 3339-5.6-003 has no offset field to compare; the same loss is WRONG VALUE on 3339-4.3-001) |
| `2026-09-24T12:00:00z` | accepted → UTC naive:2026-09-24T12:00:00 | WRONG VALUE: offset discarded (naive result) (vector 3339-5.6-002 has no offset field to compare; the same loss is WRONG VALUE on 3339-4.3-001) |
| `2026-09-24T12:00:00+00:00` | rejected: ValueError: time data '2026-09-24T12:00:00+00:00' does not match format '%Y-%m-% | TOO STRICT (3339-4.3-003) |
| `2026-09-24T12:00:00-00:00` | rejected: ValueError: time data '2026-09-24T12:00:00-00:00' does not match format '%Y-%m-% | TOO STRICT (3339-4.3-002) |
| `2026-09-24T12:00:00+23:59` | rejected: ValueError: time data '2026-09-24T12:00:00+23:59' does not match format '%Y-%m-% | TOO STRICT (the format needs a literal `Z`) (3339-5.6-009) |
| `2026-09-24T12:00:00+05:30` | rejected: ValueError: time data '2026-09-24T12:00:00+05:30' does not match format '%Y-%m-% | TOO STRICT (3339-5.7-032) |
| `2016-12-31T23:59:60Z` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) (3339-5.7-025) |
| `2016-12-31T18:59:60-05:00` | rejected: ValueError: time data '2016-12-31T18:59:60-05:00' does not match format '%Y-%m-% | TOO STRICT (the format needs a literal `Z`; no leap second either) (3339-5.7-031) |
| `2026-09-24T12:00:00.1Z` | rejected: ValueError: time data '2026-09-24T12:00:00.1Z' does not match format '%Y-%m-%dT% | TOO STRICT (3339-5.6-008) |
| `2026-09-24T12:00:00.123Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123Z' does not match format '%Y-%m-%d | TOO STRICT (3339-5.6-082) |
| `2026-09-24T12:00:00.123456Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456Z' does not match format '%Y-%m | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | rejected: ValueError: time data '2026-09-24T12:00:00.1234567Z' does not match format '%Y-% | TOO STRICT — legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456789Z' does not match format '%Y | TOO STRICT (3339-5.6-013) |
| `2026-09-24T12:00:00.123456789012Z` | rejected: ValueError: time data '2026-09-24T12:00:00.123456789012Z' does not match format  | TOO STRICT (3339-5.6-006) |
| `2026-9-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00 | TOO LENIENT (naive/local result) (3339-5.6-039) |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC naive:2026-09-24T12:00:00 | TOO LENIENT (naive/local result) (3339-5.6-060) |
| `0000-01-01T00:00:00Z` | rejected: ValueError: year 0 is out of range | too strict (range limit) (3339-5.6-004) |
| `0001-01-01T00:00:00Z` | accepted → UTC naive:0001-01-01T00:00:00 | WRONG VALUE: offset discarded (naive result) (vector 3339-5.6-077 has no offset field to compare; the same loss is WRONG VALUE on 3339-4.3-001) |
| `9999-12-31T23:59:59Z` | accepted → UTC naive:9999-12-31T23:59:59 | WRONG VALUE: offset discarded (naive result) (vector 3339-5.6-005 has no offset field to compare; the same loss is WRONG VALUE on 3339-4.3-001) |
| `2024-02-29T12:00:00Z` | accepted → UTC naive:2024-02-29T12:00:00 | WRONG VALUE: offset discarded (naive result) (vector 3339-5.7-003 has no offset field to compare; the same loss is WRONG VALUE on 3339-4.3-001) |

### `dateutil.parser.isoparse`

Legacy probe only (no vector adapter). 42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT (→ 2026-09-25 00:00:00) |
| `2016-12-31T23:59:60Z` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: ValueError: second must be in 0..59 | too strict (no leap second) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00 | TOO LENIENT (naive/local result) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00 | TOO LENIENT (naive/local result) |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-W39-4T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-267T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: ValueError: year 0 is out of range | too strict (range limit) |

### `dateutil.parser.parse`

Legacy probe only (no vector adapter). 40 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: ParserError: second must be in 0..59: 2016-12-31T23:59:60Z | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: ParserError: second must be in 0..59: 2016-12-31T18:59:60-05:00 | too strict (no leap second) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00 | TOO LENIENT (naive/local result) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00 | TOO LENIENT (naive/local result) |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: ParserError: year 0 is out of range: 0000-01-01T00:00:00Z | too strict (range limit) |
| `-0001-01-01T00:00:00Z` | accepted → UTC 0001-01-01T00:00:00.000000 | TOO LENIENT |

### `pydantic TypeAdapter(datetime).validate_python`

Legacy probe only (no vector adapter). 47 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: ValidationError: 1 validation error for datetime | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: ValidationError: 1 validation error for datetime | too strict (no leap second) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | accepted → UTC naive:2026-09-24T12:00:00 | TOO LENIENT (naive/local result) |
| `2026-09-24` | accepted → UTC naive:2026-09-24T00:00:00 | TOO LENIENT (naive/local result) |
| `0000-01-01T00:00:00Z` | rejected: ValidationError: 1 validation error for datetime | too strict (range limit) |

### `pydantic TypeAdapter(AwareDatetime).validate_json`

Legacy probe only (no vector adapter). 49 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: ValidationError: 1 validation error for datetime | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: ValidationError: 1 validation error for datetime | too strict (no leap second) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456 | conforming (lossy: fraction truncated to 6 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000 | TOO LENIENT |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: ValidationError: 1 validation error for datetime | too strict (range limit) |

### `jsonschema FormatChecker date-time (rfc3339-validator)`

Legacy probe only (no vector adapter). 55 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2016-12-31T23:59:60Z` | rejected: ValidationError: '2016-12-31T23:59:60Z' is not a 'date-time' | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: ValidationError: '2016-12-31T18:59:60-05:00' is not a 'date-time' | too strict (no leap second) |
| `2026-09-24T12:00:00Z\n` | accepted → valid | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: ValidationError: '0000-01-01T00:00:00Z' is not a 'date-time' | too strict (range limit) |

## Vector runs (310 vectors, probed Python 3.13.9)

`python3 probes/run_vector_probes.py --lang python` (2026-09-26; baseline
`evals/baselines/probes/vector-runs/python.txt`). All four keys are `--target-kind rfc3339` with fixed options, so
157 vectors are skipped (128 IXDTF, 29 non-default options). Pass % excludes the 6 interpretation vectors.

| Key (API) | pass | too lenient | too strict | wrong value | interpretation | pass % |
|---|---|---|---|---|---|---|
| `fromisoformat` | 108 | 24 | 15 | 0 | 6 | 73.5 |
| `strptime-z` (`'%Y-%m-%dT%H:%M:%S%z'`) | 109 | 10 | 28 | 0 | 6 | 74.1 |
| `strptime-f-z` (`'%Y-%m-%dT%H:%M:%S.%f%z'`) | 95 | 1 | 51 | 0 | 6 | 64.6 |
| `strptime-literal-z` (`'%Y-%m-%dT%H:%M:%SZ'`) | 104 | 6 | 35 | 2 | 6 | 70.7 |

Behaviour the legacy tables do not show (vector IDs):

- **`fromisoformat`, too lenient (24):**
  - Separators: space (3339-5.6-015), `_` (3339-5.6-018), fullwidth `Ｔ` U+FF34 (3339-5.6-069), NBSP U+00A0
    (3339-5.6-071). Any single character is taken as the separator.
  - Offsets: `+0100` (3339-5.6-023), `+01` (3339-5.6-024), `+01:60` read as `+02:00` (3339-5.6-027: a wrong
    instant as well as too lenient), offsets with seconds `+01:00:00` (3339-5.6-063), `-00:44:30` (3339-5.6-084)
    and `+00:09:21` (3339-5.6-085); the seconds are kept in the `tzinfo`. A space before `Z` (3339-5.6-029).
  - Trailing NUL `…Z\u0000` accepted (3339-5.6-064). Trailing `\n` and `\r\n` are rejected.
  - Basic format `20240101T120000Z` (3339-5.6-052) and basic time `T120000Z` (3339-errata-001); week date
    (3339-5.6-054).
  - Missing parts: date only (3339-5.6-020), no seconds (3339-5.6-021), no offset (3339-5.6-022, naive result).
  - Fractions: empty `.Z` (3339-5.6-032, 3339-A-005), comma `,5` (3339-5.6-033). A fraction on the **minute**,
    `T12:00.5Z` (3339-A-001) and `T12:00,5Z` (3339-A-002), and on the **hour**, `T12.5Z` (3339-A-006), are read as
    12:00:00.5: too lenient and, under ISO 8601's meaning (12:00:30, 12:30), a different instant.
- **`fromisoformat`, too strict (15):** lower-case `z` (3339-5.6-001/002, 3339-5.7-026), year 0000
  (3339-5.6-004, 3339-5.7-007), every real leap second (3339-5.8-003/004, 3339-5.7-025, -027 to -032, -038).
- **`strptime('%z')`, too lenient (10):** 1-digit month, day, hour, minute (3339-5.6-039, -040, -045, -048);
  fullwidth and Arabic-Indic digits (3339-5.6-059, -060); `+0100` (3339-5.6-023); offsets with seconds `+01:00:00`,
  `-00:44:30`, `+00:09:21` (3339-5.6-063, -084, -085).
- **`strptime('%z')`, too strict (28):** every fraction (`%S` takes none: 3339-5.8-001, 3339-5.6-006/007/008/013/014,
  -073, -074, -080 to -082, 3339-A-007), lower-case `z`, year 0000, leap seconds.
- **`strptime('.%f%z')`:** rejects every string **without** a fraction (51 too strict, for example 3339-5.8-002,
  3339-4.3-001, 3339-5.7-003) and every fraction longer than 6 digits (3339-5.6-006, -013, -073). Its one too-lenient
  vector is a 1-digit second `T00:00:0.5Z` (3339-A-004).
- **`strptime('…%SZ')`:** the literal `Z` gives a naive value: WRONG VALUE on 3339-4.3-001 and 3339-5.6-075 (the
  offset is lost; other `Z` vectors list no offset field). Too lenient on 1-digit fields and non-ASCII digits
  (3339-5.6-039, -040, -045, -048, -059, -060). Too strict on every numeric offset and every fraction.
- Leap seconds: no Python API accepts second 60, so the leap-second representation rule never applies. The 6
  interpretation vectors (non-table leap dates, 3339-5.7-039/040/042/045/047, and 3339-5.7-055) were all rejected.

## Producers (formatters)

| Call | Output | RFC verdict |
|---|---|---|
| `datetime(..., tzinfo=utc).isoformat()` | `2026-09-24T12:00:00+00:00` | conforming |
| `datetime(..., microsecond=123000, tzinfo=utc).isoformat()` | `2026-09-24T12:00:00.123000+00:00` | conforming |
| `naive datetime(...).isoformat()` | `2026-09-24T12:00:00` | WRONG OUTPUT (no offset) |
| `datetime.utcnow().isoformat()  [naive]` | `2026-09-25T06:03:58.705584` | WRONG OUTPUT (no offset) |
| `str(aware datetime)` | `2026-09-24 12:00:00+00:00` | WRONG OUTPUT (space separator) |
| `aware.isoformat(timespec='minutes')` | `2026-09-24T12:00+00:00` | WRONG OUTPUT (no seconds) |
| `aware.isoformat(sep=' ')` | `2026-09-24 12:00:00+00:00` | WRONG OUTPUT (space separator) |
| `timezone(timedelta(seconds=30)) .isoformat()` | `2026-09-24T12:00:00+00:00:30` | WRONG OUTPUT (offset has seconds) |
| `datetime(1850,1,1,tzinfo=ZoneInfo('Europe/Paris')).isoformat()  [LMT]` | `1850-01-01T00:00:00+00:09:21` | WRONG OUTPUT (offset has seconds) |
| `datetime(2026,9,24,14,tzinfo=ZoneInfo('Europe/Paris')).isoformat()` | `2026-09-24T14:00:00+02:00` | conforming |
| `aware.strftime('%Y-%m-%dT%H:%M:%S%z')` | `2026-09-24T12:00:00+0200` | WRONG OUTPUT (offset without colon) |
| `aware.strftime('%Y-%m-%dT%H:%M:%S%:z')` | `2026-09-24T12:00:00+02:00` | conforming |
| `time.strftime('%Y-%m-%dT%H:%M:%S%z') [local]` | `2026-09-24T08:00:00-0400` | WRONG OUTPUT (offset without colon) |
| `naive local datetime(...).strftime('%Y-%m-%dT%H:%M:%SZ')  [lies about Z]` | `2026-09-24T08:00:00Z` | WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z) |
| `datetime(1,1,1,tzinfo=utc).isoformat()` | `0001-01-01T00:00:00+00:00` | conforming |
| `datetime(999,1,1,tzinfo=utc).strftime('%Y-%m-%dT%H:%M:%SZ')` | `0999-01-01T00:00:00Z` | conforming |
| `pydantic TypeAdapter(datetime).dump_json(aware utc)` | `\"2026-09-24T12:00:00Z\"` | conforming |
| `pydantic TypeAdapter(datetime).dump_json(naive)` | `\"2026-09-24T12:00:00\"` | WRONG OUTPUT (no offset) |
| `json.dumps(datetime)` | ✗ Object of type datetime is not JSON serializable | n/a |
| `json.dumps(datetime, default=str)` | `2026-09-24 12:00:00+00:00` | WRONG OUTPUT (space separator) |

See also `protobuf.md` (Python `Timestamp.FromJsonString` / `json_format`) and `jsonschema.md` (jsonschema format assertion, 2026-09-25 re-probe).

## Detect in code

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `datetime\.utcnow\(\|datetime\.now\(\s*\)\|\.replace\(tzinfo=None\)` | Gives a naive value. `.isoformat()` then prints no offset (**WRONG OUTPUT**). | `datetime.now(timezone.utc)` and keep values aware |
| `\.isoformat\((.*timespec=['"](minutes\|hours)\|.*sep=)` | `12:00+00:00` has no seconds. The `sep=' '` form uses a space. | plain `.isoformat()` on an aware value |
| `str\(\w*(dt\|date\|time)\w*\)\|default=str` | `str(dt)` gives `2026-09-24 12:00:00+00:00` (space) | `dt.isoformat()` |
| `strftime\([^)]*%z` | `+0200` has no colon (**WRONG OUTPUT**) | `%:z` (Python ≥ 3.12) or `.isoformat()` |
| `(strftime\|strptime)\([^)]*[0-9%]Z['"]` | A literal `Z`: formatting prints local wall time as `Z` (a 4 h error in the probe). Parsing gives a naive value and rejects `+00:00`. | aware datetime + `.isoformat()`. Parse with the strict regex + `fromisoformat` |
| `fromisoformat\(` used as a *validator* | It accepts a missing offset (naive result), `+0200`, `+02`, `+01:60`, offsets with seconds, `,5`, `.Z` (empty fraction), `T12:00Z`, `T12.5Z`, week dates, the basic format, a space or `_`/NBSP/fullwidth separator, and a trailing NUL. It rejects `z` and `:60`. It truncates to µs. | the strict regex first. Then reject naive results (`dt.tzinfo is None`). |
| `strptime\([^)]*%(Y\|z\|f)` | `%Y`/`%z` accept Arabic-Indic digits and 1-digit months. `%f` accepts at most 6 digits (**TOO STRICT** on `.1234567`). | the strict regex + `fromisoformat` |
| `re\.(match\|search\|compile)\(.*\\d` · `\$['"]\)` in date regexes | `\d` is Unicode. `$` accepts a trailing `\n` (rfc3339-validator does this). | `[0-9]`, `re.ASCII`, `re.fullmatch` or `\Z` |
| `format.*date-time` with `jsonschema` · missing `rfc3339-validator` / `jsonschema\[format\]` in requirements | Without the extra, `date-time` is not checked at all ("not a date" passed) | depend on `jsonschema[format]` (or `rfc3339-validator`) and pass `format_checker=` |
| `: datetime\b` in pydantic models | It accepts a naive value, `+0200`, `,5`, `T12:00Z` and a space. `dump_json(naive)` prints no offset. | `AwareDatetime` + a strict-regex validator |
| `ZoneInfo\(` with historic dates → `.isoformat()` | For dates before 1911 in Paris it prints `+00:09:21` (offset with seconds, **WRONG OUTPUT**) | `.astimezone(timezone.utc)` before you serialize |
| `dateutil.*parse\(` | It accepts almost anything, including a trailing `\n` and Arabic-Indic digits | the strict regex |

# Swift (Apple Foundation): RFC 3339 / RFC 9557 behaviour

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts). A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Environment and method (probed 2026-09-25)

**Environment:** macOS 27.0 (build 26A428) arm64, Xcode SDK 27.0, Apple Swift 6.4 (swiftlang-6.4.0.34.1,
swift-driver 1.168.6), system Foundation (swift-foundation based) and ICU, host `TZ=America/New_York`, `Locale.current`
= `en_US`, system tzdata 2026c. Probe: `probes/swift/main.swift` + `probes/swift/RFC3339Strict.swift`
(build: `swiftc -O -o swiftrfc probes/swift/main.swift probes/swift/RFC3339Strict.swift`;
`swiftrfc probe probes/inputs.json`, `swiftrfc produce`, `swiftrfc adapter <key>`; `swiftrfc list` prints the keys).
Foundation behaviour follows the OS, not the Swift toolchain: re-probe on the target OS (iOS, older macOS, Linux
swift-corelibs-foundation) before you rely on a row.

`Date` is an instant (a `Double` of seconds since 2001-01-01Z). It keeps no offset and no leap second, so the adapters
return `"utc"` (computed from `timeIntervalSince1970` with proleptic-Gregorian arithmetic, printed to 1 µs), not vector
`fields`. `probes/swift/instant_check.py` compares that instant with the instant rfcdt derives from the string for every
accepted vector. `Date` resolution is about 0.1 µs near 2026, so 7–9 fraction digits are always lossy.

APIs with identical results on all 59 inputs (merged below):
- `Date(s, strategy: .iso8601)` = `Date.ISO8601FormatStyle(includingFractionalSeconds: true).parse` =
  `JSONDecoder` `.dateDecodingStrategy = .iso8601`. On this OS `.iso8601` decoding **accepts fractions** (it is the
  swift-foundation `ISO8601FormatStyle` parser; older OS releases used `ISO8601DateFormatter` and rejected them).
- "try `ISO8601DateFormatter` with `.withFractionalSeconds`, then without" = the common `JSONDecoder` `.custom` closure
  that does the same.
- `DateFormatter` with `Locale.current` (`en_US` here) = with `en_US_POSIX`. The Thai row shows what a user locale
  with a non-Gregorian default calendar does.

## At a glance (consumers)

Same columns as the README matrix (these rows are also there). One column is not in the matrix but matters for every Foundation parser: `0001-01-01T00:00:00Z` is read
in the **Julian** calendar (Foundation's Gregorian calendar has the 1582 cutover), so every date before 1582-10-15 is
off by 2 to 10 days (**W** for all Foundation rows; ✓ for `parseRFC3339Strict`).

| API | `lc-z` | `space` | `off-minus0` | `off-nocolon` | `no-sec` | `no-off` | `comma` | `h24` | `leap-real` | `leap-fake` | `feb30-2024` | `frac12` | `trail-ws` | `y+10000` | `x-tz` | `x-unk!` | `x-incons!` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swift: `ISO8601DateFormatter() [default: .withInternetDateTime]` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | s | ✓ | **L** | **S** | **L** | ✓ | L | **L** | **L** |
| swift: `ISO8601DateFormatter [.withInternetDateTime, .withFractionalSeconds]` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **W** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `ISO8601DateFormatter: try .withFractionalSeconds, then default` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | s | ✓ | **L** | **W** | **L** | ✓ | L | **L** | **L** |
| swift: `Date(s, strategy: .iso8601)` / `JSONDecoder .iso8601` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | **S** | **L** | ✓ | L | **L** | **L** |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX")` | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX")` | **S** | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX", isLenient=true)` | ✓ | **L** | ✓ | **L** | ✓ | ✓ | ✓ | **L** | ✓ | **L** | **L** | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss'Z'") [default TZ]` | **S** | ✓ | **S** | ✓ | ✓ | **L** | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `DateFormatter(th_TH, "yyyy-MM-dd'T'HH:mm:ssXXXXX") [no en_US_POSIX]` | **W** | ✓ | **W** | **L** | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | ✓ | ✓ | ✓ | ✓ |
| swift: `parseRFC3339Strict` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓~ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Consumers: per-API results

Each table lists only deviations and notable rows. Full rows: `swiftrfc probe probes/inputs.json` (JSON lines; the run reports were not committed; re-run the probe to regenerate them). Rows are the legacy probe strings (`probes/inputs.json` "legacy"); a vector ID in the verdict cites the vector of the same case, and "legacy probe only" marks a row that no vector covers.

### `ISO8601DateFormatter() [default: .withInternetDateTime]`

22 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT (read as `+02:00`; the rest is ignored) |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T13:00:00.000000 | TOO LENIENT (read as `+23:00`; `:60` ignored) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT (→ 2026-09-25 00:00:00) |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.1Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: returned nil | TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000 | WRONG VALUE (read as Julian calendar: 2 days early) |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0002-12-30T00:00:00.000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-03-01) |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2024-03-01) |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-05-01) |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000 | conforming (MAY; offset wins) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T14:00:00+02:00[+02:00]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (legacy probe only; suffix class: 3339-5.6-062) |

### `ISO8601DateFormatter [.withInternetDateTime, .withFractionalSeconds]`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+00:00` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00-00:00` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: returned nil | too strict (offset range) |
| `2026-09-24T12:00:00+05:30` | rejected: returned nil | TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.123456Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T11:59:59.999000 | WRONG VALUE (12-digit fraction overflows: 1 ms early) (legacy probe only: the 12-digit vector 3339-5.6-006, `.000000000001`, is accepted with no visible error) |
| `0000-01-01T00:00:00Z` | rejected: returned nil | too strict (range limit) |
| `0001-01-01T00:00:00Z` | rejected: returned nil | TOO STRICT |
| `9999-12-31T23:59:59Z` | rejected: returned nil | TOO STRICT |
| `2024-02-29T12:00:00Z` | rejected: returned nil | TOO STRICT |

### `ISO8601DateFormatter: try .withFractionalSeconds, then default`

24 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT (read as `+02:00`; the rest is ignored) |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T13:00:00.000000 | TOO LENIENT (read as `+23:00`; `:60` ignored) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT (→ 2026-09-25 00:00:00) |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.123456Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T11:59:59.999000 | WRONG VALUE (12-digit fraction overflows: 1 ms early) (legacy probe only: 3339-5.6-006 `.000000000001` is accepted with no visible error) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000 | WRONG VALUE (read as Julian calendar: 2 days early) |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0002-12-30T00:00:00.000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-03-01) |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2024-03-01) |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-05-01) |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000 | conforming (MAY; offset wins) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T14:00:00+02:00[+02:00]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (legacy probe only; suffix class: 3339-5.6-062) |

### `Date(s, strategy: .iso8601)`

27 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: Error Domain=NSCocoaErrorDomain Code=2048 "Cannot parse 2026-09-24t12:00:00Z. St | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: Error Domain=NSCocoaErrorDomain Code=2048 "Cannot parse 2026-09-24T12:00:00+23:5 | too strict (offset range) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT (→ 2026-09-25 00:00:00) |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00.000000 | conforming (→ 00:00:00) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00.000000 | conforming (→ 00:00:00) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123457 | conforming (lossy: Date is a Double, about 0.1 µs; the probe prints µs) (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123457 | conforming (lossy: Date is a Double, about 0.1 µs; the probe prints µs) |
| `2026-09-24T12:00:00.123456789012Z` | rejected: Error Domain=NSCocoaErrorDomain Code=2048 "Cannot parse 2026-09-24T12:00:00.1234 | TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000 | WRONG VALUE (read as Julian calendar: 2 days early) |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-03-01) |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2024-03-01) |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-05-01) |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000 | conforming (MAY; offset wins) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T14:00:00+02:00[+02:00]` | accepted → UTC 2026-09-24T12:00:00.000000 | lenient (accepts suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (suffix) (legacy probe only; suffix class: 3339-5.6-062) |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT (legacy probe only; suffix class: 3339-5.6-062) |

### `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX")`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.1Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: returned nil | TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: returned nil | too strict (range limit) |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000 | WRONG VALUE (read as Julian calendar: 2 days early) |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000 | TOO LENIENT |

### `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX")`

42 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+00:00` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00-00:00` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: returned nil | too strict (offset range) |
| `2026-09-24T12:00:00+05:30` | rejected: returned nil | TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.123456Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123000 | conforming (lossy: fraction truncated to 3 digits) |
| `2026-09-24T12:00:00.123456789012Z` | rejected: returned nil | TOO STRICT (legacy probe only: 3339-5.6-006 `.000000000001` is **accepted**; the 1050-digit 3339-5.6-073 is rejected) |
| `0000-01-01T00:00:00Z` | rejected: returned nil | too strict (range limit) |
| `0001-01-01T00:00:00Z` | rejected: returned nil | TOO STRICT |
| `9999-12-31T23:59:59Z` | rejected: returned nil | TOO STRICT |
| `2024-02-29T12:00:00Z` | rejected: returned nil | TOO STRICT |

### `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX", isLenient=true)`

35 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT (→ 2026-09-25 00:00:00) |
| `2016-12-31T23:59:60Z` | accepted → UTC 2017-01-01T00:00:00.000000 | conforming (→ 00:00:00) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2017-01-01T00:00:00.000000 | conforming (→ 00:00:00) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-25T00:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:01:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: returned nil | TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000000 | TOO LENIENT |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T00:00:00.000000 | WRONG VALUE (read as Julian calendar: 2 days early) |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T00:00:00.000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | accepted → UTC -0002-12-30T00:00:00.000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-03-01) |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000000 | TOO LENIENT (rolled over to 2024-03-01) |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000000 | TOO LENIENT (rolled over to 2026-05-01) |

### `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss'Z'") [default TZ]`

35 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T16:00:00.000000 | WRONG VALUE (Z ignored: read as host-local time) |
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+00:00` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00-00:00` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | rejected: returned nil | too strict (offset range) |
| `2026-09-24T12:00:00+05:30` | rejected: returned nil | TOO STRICT |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.1Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.000000 | TOO LENIENT (as host-local time) |
| `2026-9-24T12:00:00Z` | accepted → UTC 2026-09-24T16:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T16:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 2026-09-24T16:00:00.000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: returned nil | too strict (range limit) |
| `0001-01-01T00:00:00Z` | accepted → UTC 0000-12-30T04:56:02.000000 | WRONG VALUE (Julian calendar and host-local LMT) |
| `9999-12-31T23:59:59Z` | accepted → UTC 10000-01-01T04:59:59.000000 | WRONG VALUE (Z ignored: read as host-local time) |
| `10000-01-01T00:00:00Z` | accepted → UTC 10000-01-01T05:00:00.000000 | TOO LENIENT |
| `2024-02-29T12:00:00Z` | accepted → UTC 2024-02-29T17:00:00.000000 | WRONG VALUE (Z ignored: read as host-local time) |

### `DateFormatter(th_TH, "yyyy-MM-dd'T'HH:mm:ssXXXXX") [no en_US_POSIX]`

34 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | accepted → UTC 1483-10-03T12:00:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `2026-09-24t12:00:00Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00z` | accepted → UTC 1483-10-03T12:00:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `2026-09-24T12:00:00+00:00` | accepted → UTC 1483-10-03T12:00:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `2026-09-24T12:00:00-00:00` | accepted → UTC 1483-10-03T12:00:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `2026-09-24T12:00:00+23:59` | accepted → UTC 1483-10-02T12:01:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `2026-09-24T12:00:00+05:30` | accepted → UTC 1483-10-03T06:30:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 1483-10-03T10:00:00.000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → UTC 1483-10-03T10:00:00.000000 | TOO LENIENT |
| `2016-12-31T23:59:60Z` | rejected: returned nil | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: returned nil | too strict (no leap second) |
| `2026-09-24T12:00:00.1Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.1234567Z` | rejected: returned nil | TOO STRICT (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | rejected: returned nil | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | rejected: returned nil | TOO STRICT |
| `2026-9-24T12:00:00Z` | accepted → UTC 1483-10-03T12:00:00.000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | accepted → UTC 1483-10-03T12:00:00.000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | accepted → UTC 1483-10-03T12:00:00.000000 | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: returned nil | too strict (range limit) |
| `0001-01-01T00:00:00Z` | accepted → UTC -0543-12-26T00:00:00.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `9999-12-31T23:59:59Z` | accepted → UTC 9456-12-31T23:59:59.000000 | WRONG VALUE (Buddhist calendar: year read as B.E., 543 years early) |
| `10000-01-01T00:00:00Z` | accepted → UTC 9457-01-01T00:00:00.000000 | TOO LENIENT |
| `2024-02-29T12:00:00Z` | rejected: returned nil | TOO STRICT |

### `parseRFC3339Strict (RFC3339Strict.swift: byte parser + civil arithmetic)`

54 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59.000000 | conforming (→ 23:59:59) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59.000000 | conforming (→ 23:59:59) |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123457 | conforming (lossy: Date is a Double, about 0.1 µs; the probe prints µs) (legacy probe only) |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123457 | conforming (lossy: Date is a Double, about 0.1 µs; the probe prints µs) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123457 | conforming (lossy: Date is a Double, about 0.1 µs; the probe prints µs) |

### Extra inputs (not in `inputs.json`)

Columns: **ISO** = `ISO8601DateFormatter()` default (the "try fractional, then default" pattern gives the same);
**Style** = `Date(s, strategy: .iso8601)` / `JSONDecoder .iso8601`; **DF** = `DateFormatter(en_US_POSIX,
"yyyy-MM-dd'T'HH:mm:ssXXXXX")`; **DF-lenient** = same with `isLenient = true`. "→ x" means accepted as UTC instant x.

| Input | ISO | Style | DF | DF-lenient | RFC verdict |
|---|---|---|---|---|---|
| `2026-09-24T12:00:00Zgarbage` | → 12:00Z | → 12:00Z | rejected | rejected | TOO LENIENT (ISO, Style: any trailing text is ignored) |
| `2026-09-24T12:00:00+02:00xyz` | → 10:00Z | → 10:00Z | rejected | rejected | TOO LENIENT (same) |
| `2024-01-01T00:00:00Z/P1D` · `1985-04-12T23:20:50Z Fri` · `…Z\u0000` · `…Z\r\n` (vectors) | accepted | accepted | rejected | rejected | TOO LENIENT (same) |
| `2026-09-24T12:00:00+24:60` / `+25:00` | → 10:00Z (as `+02:00`) | rejected | rejected | rejected | TOO LENIENT + WRONG VALUE (ISO) |
| `2026-09-24T12:00:00+99:59` | → 03:00Z (as `+09:00`) | rejected | rejected | rejected | TOO LENIENT + WRONG VALUE (ISO) |
| `2024-01-01T12:00:00+1:00` (vector) | → 02:00Z (as `+10:00`) | → 11:00Z | rejected | – | TOO LENIENT; ISO also WRONG VALUE |
| `2026-09-24T12:00:00+02:00:30` | → 09:59:30Z | → 09:59:30Z | → 09:59:30Z | → 09:59:30Z | TOO LENIENT (offset seconds applied) |
| `2026-09-24T12:00:00+14:00` / `+18:00` | accepted | accepted | accepted | accepted | conforming |
| `2026-09-24T12:00:00+18:01` | accepted | rejected | accepted | accepted | Style: too strict (offset range, max ±18:00); `+23:59` is rejected the same way |
| `12024-01-01T12:00:00Z` (vector) | → **2024**-01-01 | → 12024-01-01 | → **2024**-01-01 | – | TOO LENIENT; ISO and DF also WRONG VALUE (5-digit year silently read as `2024`) |
| `24-01-01T12:00:00Z` (vector) | → 0023-12-30 (year 24, Julian) | same | same | – | TOO LENIENT |
| `2024-01-01T12:00:00UTC` / `…GMT+1` (vectors) | → 12:00Z / 11:00Z | same | same | – | TOO LENIENT (zone names parsed by ICU) |
| `2024/01/01T12:00:00Z` (vector) | accepted | rejected | accepted | – | TOO LENIENT |
| `2026-09-24T1:00:00Z` | → 01:00Z | → 01:00Z | → 01:00Z | → 01:00Z | TOO LENIENT |
| `2026-09-24T12:60:00Z` / `12:00:61Z` / `2024-01-01T12:00:99Z` (vector) | rejected | → 13:00Z / 12:01:01Z / accepted | rejected | → 13:00Z / 12:01:01Z / not run | TOO LENIENT (Style rolls invalid minutes and seconds over) |
| `2016-12-31T23:59:60+01:00` (60 not at 23:59:60 UTC) | rejected | → 23:00Z | rejected | → 23:00Z | TOO LENIENT |
| `2026-13-01T12:00:00Z` / `2026-09-00T12:00:00Z` | rejected | rejected | rejected | → 2027-01-01 / 2026-08-31 | TOO LENIENT (DF-lenient) |
| `2026-09-24T12:00:00\u00a0Z` (NBSP) / `…12:00:00 Z` | accepted | rejected | accepted | accepted | TOO LENIENT |
| `2026-09-24t12:00:00z` | rejected | rejected | rejected | rejected | TOO STRICT (lower-case `t` is rejected by every Foundation parser) |
| `2026-09-24T12:00:00.5Z` | rejected | accepted | rejected | rejected | ISO, DF: TOO STRICT (fraction needs its own option / pattern) |
| `2026-09-24T12:00:00.12345678901Z` (11 digits) | rejected | rejected | rejected | rejected | TOO STRICT; with `.withFractionalSeconds`: → 11:59:59.995Z (WRONG VALUE, fraction overflow) |
| `2026-09-24T12:00:00.1234567891Z` (10 digits) | rejected | rejected | rejected | rejected | TOO STRICT (Style accepts at most 9 digits); `.withFractionalSeconds`: → .123 |
| `0099-01-01T00:00:00Z` | → 0098-12-30 | same | same | same | WRONG VALUE (Julian, −2 days) |
| `1000-01-01T00:00:00Z` | → 1000-01-06 | same | same | same | WRONG VALUE (Julian, +5 days) |
| `1582-10-10T00:00:00Z` (in the Julian→Gregorian gap) | → 1582-10-20 | same | same | same | WRONG VALUE (+10 days) |
| `1583-01-01T00:00:00Z` | correct | correct | correct | correct | conforming |

## Conformance vectors (`run_vectors.py`)

`vectors/vectors.json` with 310 vectors; `--target-kind rfc3339 --target-options fixed --target-has-tzdata yes`, so 147
are scored, 6 are interpretations and 157 are skipped. "Pass" is the runner's verdict. The runner cannot see
instants, so "wrong instant" comes from `probes/swift/instant_check.py` (tolerance 1 ms; a leap second read as `:59` or
as the next second is not counted). Adapter: `swiftrfc adapter <key>`. `probes/run_vector_probes.py --lang swift` runs
both steps; the committed baseline `evals/baselines/probes/vector-runs/swift.txt` has each key's report and the
instant-check lines.

Instant-check columns: **compared** = accepted vectors that rfcdt can parse (valid or not); **wrong** = the instant
differs by 1 ms or more (a WRONG VALUE, even on a vector the runner counted as "pass"); **lossy** = below 1 ms (the
`Date` / millisecond precision); **leap** = a `:60` read as `:59` or as the next second (a representation limit of
`Date`, graded as INTERPRETATION by `references/interpretation.md`; on an invalid leap second it is part of the
TOO LENIENT count, not an extra finding).

| Adapter key | API | Pass | Too lenient | Too strict | Compared | Wrong instant | Lossy | Leap |
|---|---|---|---|---|---|---|---|---|
| `iso` | `ISO8601DateFormatter()` default | 78/147 | 43 | 26 | 43 | 5 | 0 | 0 |
| `isofrac` | `ISO8601DateFormatter` `.withFractionalSeconds` | 98/147 | 1 | 48 | 11 | 0 | 2 | 0 |
| `isoboth` / `jsonfrac` | try fractional, then default (also as `JSONDecoder .custom`) | 88/147 | 44 | 15 | 54 | 5 | 2 | 0 |
| `isostyle` / `isostylefrac` / `jsoniso` | `Date(s, strategy: .iso8601)`, `ISO8601FormatStyle(includingFractionalSeconds: true)`, `JSONDecoder .iso8601` | 95/147 | 45 | 7 | 72 | 5 | 2 | 21 |
| `dfposix` / `dfdefault` | `DateFormatter` `en_US_POSIX` (or `en_US`) `…ssXXXXX` | 99/147 | 20 | 28 | 33 | 4 | 0 | 0 |
| `dfposixfrac` | `DateFormatter` `en_US_POSIX` `…ss.SSSXXXXX` | 98/147 | 1 | 48 | 11 | 0 | 2 | 0 |
| `dfposixlenient` | same as `dfposix`, `isLenient = true` | 87/147 | 44 | 16 | 55 | 5 | 0 | 20 |
| `dfliteralz` | `DateFormatter` `…ss'Z'` (default time zone) | 96/147 | 13 | 38 | 23 | 23 | 0 | 0 |
| `dfth` | `DateFormatter` `th_TH` `…ssXXXXX` | 96/147 | 21 | 30 | 31 | 31 | 0 | 0 |
| `strict` | `parseRFC3339Strict` (`probes/swift/RFC3339Strict.swift`) | **147/147** | 0 | 0 | 62 | 0 | 3 (`Date` precision) | 14 (valid leap seconds; `Date` has no `:60`) |

The 4–5 wrong instants in the Foundation rows are all years 0000–0099, 2 days early (Julian): 3339-5.6-004
(`0000-01-01T00:00:00Z` → `-0001-12-30`; not accepted by the `DateFormatter` keys), 3339-5.6-075, 3339-5.6-076,
3339-5.6-077 (`0001-01-01T00:00:00Z` → `0000-12-30`) and 3339-5.6-078. In `dfliteralz` every accepted `Z` string
is read as New York time (+4 h / +5 h; e.g. 3339-4.3-001 `2024-06-01T12:00:00Z` → 16:00Z, 3339-5.6-005
`9999-12-31T23:59:59Z` → year 10000). In `dfth` every year is read as a Thai Buddhist-era year (−543 years; e.g.
3339-5.8-002 → 1453). The leap column of `isostyle` / `dfposixlenient` counts the invalid `:60` vectors they accept
(3339-5.7-033 … 3339-5.7-037 and others: `:60` rolled to the next minute at any position). The only too-lenient vector in `isofrac` / `dfposixfrac` is `2020-01-01T00:00:0.5Z`
(1-digit second). The instant check cannot see wrong values on inputs that rfcdt rejects (for example `+24:00` read as
`+02:00`, `12024-…` read as `2024`); those are in the extra-inputs table above.

## Producers (formatters)

Every output was checked with `rfcdt.py check --json`. The true instant is 2026-09-24T12:00:00Z unless the row says
otherwise.

| Call | Output | RFC verdict |
|---|---|---|
| `ISO8601DateFormatter().string(from:)` (default `timeZone` = GMT) | `2026-09-24T12:00:00Z` | conforming |
| same, `timeZone = .current` (New York) / Europe/Paris | `2026-09-24T08:00:00-04:00` / `…14:00:00+02:00` | conforming |
| same, Europe/London in January (offset 0 but known) | `2026-01-15T12:00:00Z` | conforming (Advisory, rule 2: offset 0 always prints `Z`) |
| `ISO8601DateFormatter.string(from:timeZone:formatOptions: [.withInternetDateTime])` (Paris) | `2026-09-24T14:00:00+02:00` | conforming |
| `ISO8601DateFormatter` `.withFractionalSeconds`, +0.123456789 s | `2026-09-24T12:00:00.123Z` | conforming (lossy: always 3 digits) |
| same, +0 s | `2026-09-24T12:00:00.000Z` | conforming |
| same, +0.9996 s / −0.0004 s | `2026-09-24T12:00:01.000Z` / `2026-09-24T12:00:00.000Z` | conforming (lossy: **rounds** to the millisecond, so it can print a later second) |
| `ISO8601DateFormatter()` (no fraction option), +0.9 s | `2026-09-24T12:00:00Z` | conforming (lossy: fraction truncated) |
| same, `TimeZone(secondsFromGMT: 30)` / `(secondsFromGMT: -2670)` | `2026-09-24T12:01:00+00:01` / `2026-09-24T11:15:00-00:45` | conforming (offset rounded to the minute and the wall time moved with it: the instant is right) |
| **same**, `Africa/Monrovia`, 1970-01-01T12:00:00Z (MMT −00:44:30) | `1970-01-01T11:15:30-00:44:30` | WRONG OUTPUT (offset has seconds) |
| **same**, `Europe/Paris`, 1850-01-01 00:00 LMT (+00:09:21) | `1850-01-01T00:00:00+00:09:21` | WRONG OUTPUT (offset has seconds) |
| **same**, 0001-01-01T00:00:00Z (proleptic Gregorian instant) | `0001-01-03T00:00:00Z` | WRONG VALUE (Julian calendar date; the string denotes an instant 2 days later) |
| **same**, 0000-01-01T00:00:00Z / −0001-01-01T00:00:00Z | `0001-01-03T00:00:00Z` / `0002-01-03T00:00:00Z` | WRONG VALUE (era dropped: 1 BC prints as year 1, 2 BC as year 2, plus Julian) |
| same, 9999-12-31T23:59:59Z | `9999-12-31T23:59:59Z` | conforming |
| **same**, 10000-01-01T00:00:00Z | `10000-01-01T00:00:00Z` | WRONG OUTPUT (5-digit year; no error path) |
| `ISO8601DateFormatter` `[.withInternetDateTime, .withSpaceBetweenDateAndTime]` | `2026-09-24 12:00:00Z` | WRONG OUTPUT (space separator) |
| `date.formatted(.iso8601)` / `date.ISO8601Format()` | `2026-09-24T12:00:00Z` | conforming |
| **`Date.ISO8601FormatStyle(timeZone: Europe/Paris).format`** (also `timeZone: .current`) | `2026-09-24T14:00:00+0200` / `…08:00:00-0400` | WRONG OUTPUT (offset without colon: the default `timeZoneSeparator` is `.omitted`) |
| `Date.ISO8601FormatStyle(timeZoneSeparator: .colon, timeZone: Paris)` | `2026-09-24T14:00:00+02:00` | conforming |
| `Date.ISO8601FormatStyle(includingFractionalSeconds: true)`, +0.123456789 s / +0.9996 s | `…12:00:00.123Z` / `…12:00:00.999Z` | conforming (lossy: 3 digits, **truncated**; differs from `ISO8601DateFormatter`, which rounds) |
| `Date.ISO8601FormatStyle(timeZone: secondsFromGMT 30)` | `2026-09-24T12:00:30+000030` | WRONG OUTPUT (offset `hhmmss`) |
| `Date.ISO8601FormatStyle`, Monrovia 1970 / Paris 1850 LMT | `1970-01-01T11:15:30-004430` / `1850-01-01T00:00:00+000921` | WRONG OUTPUT (offset `hhmmss`) |
| `date.formatted(.iso8601)`, 0001-01-01T00:00:00Z / 0000-01-01T00:00:00Z | `0001-01-03T00:00:00Z` / `0000-01-03T00:00:00Z` | WRONG VALUE (Julian calendar date, +2 days) |
| `date.formatted(.iso8601)`, −0001-01-01T00:00:00Z | `-0001-01-03T00:00:00Z` | WRONG OUTPUT (signed year) |
| `date.formatted(.iso8601)`, 10000-01-01T00:00:00Z | `10000-01-01T00:00:00Z` | WRONG OUTPUT (5-digit year) |
| `Date.ISO8601FormatStyle(dateTimeSeparator: .space)` | `2026-09-24 12:00:00Z` | WRONG OUTPUT (space separator) |
| `JSONEncoder` `.dateEncodingStrategy = .iso8601`, +0.5 s | `["2026-09-24T12:00:00Z"]` | conforming (lossy: fraction dropped; there is no fractional `.iso8601` encoding strategy) |
| `JSONEncoder` `.iso8601`, 10000-01-01T00:00:00Z | `["10000-01-01T00:00:00Z"]` | WRONG OUTPUT (5-digit year) |
| **`JSONEncoder()` default (`.deferredToDate`)** | `[811944000]` | WRONG OUTPUT (a number: seconds since 2001-01-01, not a timestamp string; a contract that says `date-time` gets a number) |
| `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssXXXXX")` (default time zone, New York) | `2026-09-24T08:00:00-04:00` | conforming |
| `DateFormatter(en_US_POSIX, "…ss.SSSXXXXX")`, UTC | `2026-09-24T12:00:00.000Z` | conforming |
| `DateFormatter(en_US_POSIX, "…ssZZZZZ")` / `"…ssxxx"`, UTC | `…12:00:00Z` / `…12:00:00+00:00` | conforming (`xxx` prints `+00:00`, never `Z`: rule 2 Advisory) |
| same `XXXXX`, `TimeZone(secondsFromGMT: -2670)` | `2026-09-24T11:15:00-00:45` | conforming (offset rounded, wall time moved) |
| **`DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ss'Z'")`** (default time zone) | `2026-09-24T08:00:00Z` | WRONG VALUE (local wall time labelled Z; −4 h) |
| `DateFormatter(en_US_POSIX, "yyyy-MM-dd'T'HH:mm:ssZ")` (New York) | `2026-09-24T08:00:00-0400` | WRONG OUTPUT (offset without colon) |
| **`DateFormatter(en_US_POSIX, "YYYY-MM-dd'T'HH:mm:ssXXXXX")`**, 2026-12-28 | `2027-12-28T12:00:00Z` | WRONG VALUE (week-based year) |
| `DateFormatter(en_US_POSIX, "yyyy…XXXXX")`, UTC, 0001-01-01T00:00:00Z | `0001-01-03T00:00:00Z` | WRONG VALUE (Julian calendar, +2 days) |
| `DateFormatter(Locale.current = en_US, "yyyy…XXXXX")` / `fi_FI` / `en-US-u-hc-h12` | `2026-09-24T12:00:00Z` | conforming (these locales keep the pattern; a user's 12/24-hour override is not reproducible in a CLI and was not probed) |
| **`DateFormatter(th_TH, "yyyy…XXXXX")`** (also `en_US_POSIX` with `calendar = .buddhist`) | `2569-09-24T12:00:00Z` | WRONG VALUE (Buddhist-era year from the locale's calendar) |
| **`DateFormatter(ar_SA, "yyyy…XXXXX")`** | `١٤٤٨-٠٤-١٣T١٢:٠٠:٠٠Z` | WRONG OUTPUT (Arabic-Indic digits, Islamic Umm al-Qura date) |
| `"\(date)"` / `date.description` | `2026-09-24 12:00:00 +0000` | WRONG OUTPUT (space separator, `+0000`; debug format) |
| `formatRFC3339UTC(date, fractionDigits: 3)` (`RFC3339Strict.swift`), +0.9996 s | `2026-09-24T12:00:00.999Z` | conforming (fixed width, truncated) |
| same, 0001-01-01T00:00:00Z / 0000-01-01T00:00:00Z | `0001-01-01T00:00:00.000000Z` / `0000-01-01T00:00:00Z` | conforming (proleptic Gregorian) |
| same, 10000-01-01T00:00:00Z | ✗ `range("year 10000 outside 0000-9999")` | refuses (safe) |

## Detect in code

`rfcdt.py scan` covers part of this with `SCAN-SWIFT-ISO8601-DEFAULT`, `SCAN-SWIFT-FRACTIONAL-ONLY`,
`SCAN-SWIFT-POSIX-LOCALE` and the shared `SCAN-JAVA-OFFSET-PATTERN` (added after this probe). The greps below (ERE, macOS `grep -nE`) were tested on
`probes/swift/testdata/risky_swift.txt`: each defect row hits its sample lines.

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `ISO8601DateFormatter\(\)` · `\.date\(from:` | `date(from:)` ignores **any trailing text** (`Zgarbage`, `…Z/P1D`, `Z\r\n`, NUL, a whole `[!…]` suffix). It reads `+24:00` as `+02:00`, `+99:59` as `+09:00`, `+1:00` as `+10:00`, `12024-…` as year 2024. It accepts `+0200`, `+02`, 1-digit fields, NBSP, Arabic-Indic digits and `T24:00`, and rolls `02-30` over. It rejects any fraction unless `.withFractionalSeconds` is set, and then it rejects strings **without** a fraction. | `parseRFC3339Strict` (`probes/swift/RFC3339Strict.swift`: 147/147 vectors), or the strict regex in front and a round-trip check |
| `withFractionalSeconds` · `\.SSS` | Fixed 3 digits: with the option (or a `.SSS` pattern) every string without a fraction is rejected. A 12-digit fraction becomes 1 ms early (11 digits: 5 ms early). On output it **rounds** (`.9996` → next second). | parse with the strict helper; format with `formatRFC3339UTC(_:fractionDigits:)` (truncates, fixed width) |
| `dateDecodingStrategy *= *\.iso8601` · `Date\([^)]*strategy: *\.iso8601` · `ISO8601FormatStyle\([^)]*\)\.parse` | The swift-foundation parser also ignores trailing text, accepts `+0200`, `+02`, `+02:00:30`, 1-digit fields, `UTC`/`GMT+1`, `T24:00`, `12:60`, `:61`, `:99`, and `:60` on any date (rolled to the next minute). It rejects `+23:59` (max ±18:00), lower-case `t` and more than 9 fraction digits. Older OS releases used `ISO8601DateFormatter` for `.iso8601` decoding and rejected all fractions (from docs and issue reports; not probed here). | `.custom { try parseRFC3339Strict(container.decode(String.self)).date }` |
| `ISO8601FormatStyle\([^)]*timeZone:` · `timeZoneSeparator: *\.omitted` · `dateTimeSeparator: *\.space` · `withSpaceBetweenDateAndTime` | `Date.ISO8601FormatStyle` defaults to `timeZoneSeparator: .omitted`: any non-UTC zone prints `+0200` (and `+000030` for offsets with seconds). The space options print a space separator. | format in UTC (`date.formatted(.iso8601)`), or pass `timeZoneSeparator: .colon`; never the space options on the wire |
| `ss'Z'` · `:ss\.S+'Z'` | A literal `'Z'` in a `DateFormatter` pattern: output is local wall time labelled Z (−4 h in the probe). On parse, `Z` is ignored and the string is read as host-local time (+4 h), and every other offset is rejected. | `XXXXX` with `timeZone = TimeZone(identifier: "UTC")`, or `ISO8601DateFormatter` for output |
| `dateFormat *= *"[^"]*(ss\|S)(Z\|ZZ\|ZZZ\|xx\|XX\|X)"` | `Z` printed `-0400` (probed). By the ICU pattern spec, `ZZ`/`ZZZ`/`xx`/`XX` also print `±hhmm` and `X` prints `±hh` (not probed). | `XXXXX` (prints `Z` for 0) or `xxx` (always `±hh:mm`; both probed) |
| `dateFormat *= *"YYYY` | `YYYY` is the week-based year: 2026-12-28 printed as `2027-12-28` | `yyyy` |
| `(^\|[^0-9A-Za-z])DateFormatter\(\)` without `Locale\(identifier: *"en_US_POSIX"\)` nearby | The user's locale sets the calendar and digits: `th_TH` prints `2569-…` and parses 2026 as 1483 CE; `ar_SA` prints Arabic-Indic Hijri digits. | `locale = Locale(identifier: "en_US_POSIX")`, `calendar = Calendar(identifier: .gregorian)`, explicit `timeZone` |
| `isLenient *= *true` | Accepts month 13, day 00, `12:60`, `:61`, `T24:00`, `:60` anywhere, space separator | leave `isLenient` false and validate first |
| `JSONEncoder\(\)` · `dateEncodingStrategy *= *\.deferredToDate` | The default encodes `Date` as a number of seconds since 2001-01-01 (`811944000`) | `.iso8601` (seconds only) or `.custom` with `formatRFC3339UTC` |
| `"\\\(date\)"` · `\.description\b` on a `Date` | `2026-09-24 12:00:00 +0000` (debug format) | `date.formatted(.iso8601)` |
| any Foundation formatter or parser on dates before 1583 (history, genealogy, `0001-01-01` sentinels) | Foundation's Gregorian calendar switches to Julian before 1582-10-15: `0001-01-01T00:00:00Z` parses as `0000-12-30`, and the instant for proleptic `0001-01-01` prints as `0001-01-03`. Year 0 and BC years print without an era (`0001-…`, `0002-…`) or signed (`-0001-…`). | civil arithmetic (as in `RFC3339Strict.swift`), or reject years before 1583 at the boundary |

Portable strict check in Swift: use a byte parser (as in `RFC3339Strict.swift`) or a Swift `Regex` with `[0-9]` (not `\d`,
which matches any Unicode digit) and `wholeMatch`. Then do the date arithmetic without `Calendar(identifier: .gregorian)`,
because of the Julian cutover.

## Top defects (Swift)

1. **Foundation parsers ignore trailing text.** `ISO8601DateFormatter.date(from:)`, `Date(s, strategy: .iso8601)` and
   `JSONDecoder .iso8601` accept `…Zgarbage`, `…Z\r\n`, NUL, intervals (`…Z/P1D`) and any RFC 9557 suffix, critical ones
   included. The suffix is silently dropped (TOO LENIENT; for `[!…]` a consumer that claims RFC 9557 violates §3.3).
2. **`ISO8601DateFormatter` misreads offsets and years.** `+24:00`, `+24:60` and `+25:00` become `+02:00`, `+99:59`
   becomes `+09:00`, `+1:00` becomes `+10:00`, `+23:60` becomes `+23:00`, and `12024-01-01…` becomes year 2024
   (well-formed-looking input, wrong instant).
3. **Julian calendar before 1582-10-15 in every Foundation API.** `0001-01-01T00:00:00Z` parses 2 days early, and
   `1582-10-10` becomes `1582-10-20`. On output, proleptic `0001-01-01` prints as `0001-01-03`, and BC years lose the era
   (`ISO8601DateFormatter`) or print signed (`ISO8601FormatStyle`). A zero-date sentinel does not round-trip.
4. **`Date.ISO8601FormatStyle` prints offsets without a colon by default** (`+0200`, `-0400`; `+000030` for
   offsets with seconds). It is correct only for UTC.
5. **Fraction handling differs by API.** `ISO8601DateFormatter` needs an option, and then it requires exactly the
   fraction form (strings without one are rejected, so the "try both formatters" pattern is common). It keeps 3 digits,
   rounds on output and overflows on 11–12 digits. `ISO8601FormatStyle` truncates and rejects more than 9 digits.
   `JSONEncoder .iso8601` drops the fraction.
6. **`DateFormatter` pitfalls repeat the Java and .NET ones.** A literal `'Z'` is a 4 h error in both directions,
   `YYYY` gives the week year, and without `en_US_POSIX` the locale's calendar and digits leak in (`2569-…`, Arabic-Indic
   Hijri, and on parse 2026 → 1483 CE).
7. **Leap seconds.** `ISO8601DateFormatter` and strict `DateFormatter` reject a real `23:59:60Z`. `ISO8601FormatStyle`
   and lenient `DateFormatter` accept `:60` (and `:61`, `:99`) on any date and roll it into the next minute.
8. **`JSONEncoder()` default date strategy is a number** (seconds since 2001-01-01), not a timestamp.

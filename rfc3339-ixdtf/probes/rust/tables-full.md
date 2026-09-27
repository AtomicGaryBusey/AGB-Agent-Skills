
### rust

#### `chrono DateTime::parse_from_rfc3339` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24T12:00:00+23:59 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T12:00:00+05:30 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+0200` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00+02` | ✗ premature end of input | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T18:59:60-05:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60+00:00 ⇒ UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60+00:00 ⇒ UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.100+00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123+00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456+00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.123456700+00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00Z` | ✗ premature end of input | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input | conforming |
| `2026-09-24` | ✗ premature end of input | conforming |
| `20260924T120000Z` | ✗ premature end of input | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-267T12:00:00Z` | ✗ premature end of input | conforming |
| `2026-9-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ trailing input | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00+00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00+00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59+00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+002026-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `-0001-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-02-29T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00+00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input | conforming |

#### `chrono DateTime::<FixedOffset>::from_str` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24T12:00:00+23:59 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T12:00:00+05:30 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T12:00:00+02:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | ✗ premature end of input | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T18:59:60-05:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60+00:00 ⇒ UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60+00:00 ⇒ UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.100+00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123+00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456+00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.123456700+00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input | conforming |
| `2026-09-24` | ✗ premature end of input | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-9-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00+00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00+00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59+00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+10000-01-01T00:00:00Z` | +10000-01-01T00:00:00+00:00 ⇒ UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | -0001-01-01T00:00:00+00:00 ⇒ UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00+00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input | conforming |

#### `chrono DateTime::<Utc>::from_str` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-23T12:01:00+00:00 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T06:30:00+00:00 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T10:00:00+00:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | ✗ premature end of input | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60+00:00 ⇒ UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60+00:00 ⇒ UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.100+00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123+00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456+00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.123456700+00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input | conforming |
| `2026-09-24` | ✗ premature end of input | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-9-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00+00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00+00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59+00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+10000-01-01T00:00:00Z` | +10000-01-01T00:00:00+00:00 ⇒ UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | -0001-01-01T00:00:00+00:00 ⇒ UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00+00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input | conforming |

#### `chrono serde_json::from_str::<DateTime<Utc>>` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-23T12:01:00+00:00 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T06:30:00+00:00 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range at line 1 column 27 | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range at line 1 column 27 | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T10:00:00+00:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | ✗ premature end of input at line 1 column 24 | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60+00:00 ⇒ UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60+00:00 ⇒ UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.100+00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123+00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456+00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.123456700+00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters at line 1 column 23 | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters at line 1 column 24 | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters at line 1 column 19 | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input at line 1 column 21 | conforming |
| `2026-09-24` | ✗ premature end of input at line 1 column 12 | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters at line 1 column 18 | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters at line 1 column 22 | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range at line 1 column 20 | conforming |
| `2026-9-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters at line 1 column 26 | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00+00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00+00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59+00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters at line 1 column 23 | conforming |
| `+10000-01-01T00:00:00Z` | +10000-01-01T00:00:00+00:00 ⇒ UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | -0001-01-01T00:00:00+00:00 ⇒ UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00+00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input at line 1 column 41 | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input at line 1 column 42 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input at line 1 column 36 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input at line 1 column 37 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input at line 1 column 35 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input at line 1 column 33 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input at line 1 column 34 | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input at line 1 column 41 | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input at line 1 column 42 | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input at line 1 column 35 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input at line 1 column 52 | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input at line 1 column 37 | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input at line 1 column 35 | conforming |

#### `chrono serde_json::from_str::<DateTime<FixedOffset>>` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24T12:00:00+23:59 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T12:00:00+05:30 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range at line 1 column 27 | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range at line 1 column 27 | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T12:00:00+02:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | ✗ premature end of input at line 1 column 24 | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T18:59:60-05:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60+00:00 ⇒ UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60+00:00 ⇒ UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.100+00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123+00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456+00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.123456700+00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters at line 1 column 23 | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters at line 1 column 24 | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters at line 1 column 19 | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input at line 1 column 21 | conforming |
| `2026-09-24` | ✗ premature end of input at line 1 column 12 | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters at line 1 column 18 | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters at line 1 column 22 | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range at line 1 column 20 | conforming |
| `2026-9-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters at line 1 column 26 | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00+00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00+00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59+00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters at line 1 column 23 | conforming |
| `+10000-01-01T00:00:00Z` | +10000-01-01T00:00:00+00:00 ⇒ UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | -0001-01-01T00:00:00+00:00 ⇒ UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00+00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ input is out of range at line 1 column 22 | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input at line 1 column 41 | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input at line 1 column 42 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input at line 1 column 36 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input at line 1 column 37 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input at line 1 column 35 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input at line 1 column 33 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input at line 1 column 34 | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input at line 1 column 41 | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input at line 1 column 42 | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input at line 1 column 35 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input at line 1 column 52 | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input at line 1 column 37 | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input at line 1 column 35 | conforming |

#### `chrono DateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f%:z")` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24t12:00:00Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24 12:00:00Z` | ✗ input contains invalid characters | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24T12:00:00+23:59 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T12:00:00+05:30 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T12:00:00+02:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | ✗ premature end of input | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range | conforming |
| `2016-12-31T23:59:60Z` | ✗ input contains invalid characters | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T18:59:60-05:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:60Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00.1Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.1234567Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input | conforming |
| `2026-09-24` | ✗ premature end of input | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-9-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ input contains invalid characters | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `0000-01-01T00:00:00Z` | ✗ input contains invalid characters | too strict (range limit) |
| `0001-01-01T00:00:00Z` | ✗ input contains invalid characters | TOO STRICT |
| `9999-12-31T23:59:59Z` | ✗ input contains invalid characters | TOO STRICT |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+002026-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `-0001-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-02-29T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2024-02-30T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2024-02-29T12:00:00Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-04-31T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ input contains invalid characters | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ input contains invalid characters | conforming |

#### `chrono DateTime::parse_from_str(s, "%+")` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24T12:00:00+23:59 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T12:00:00+05:30 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input is out of range | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T12:00:00+02:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | ✗ premature end of input | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60+00:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T18:59:60-05:00 ⇒ UTC 2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60+00:00 ⇒ UTC 2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60+00:00 ⇒ UTC 2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.100+00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123+00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456+00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.123456700+00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24T12:00:00.123456789+00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input | conforming |
| `2026-09-24` | ✗ premature end of input | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-9-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` | ✗ trailing input | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00+00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00+00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59+00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+10000-01-01T00:00:00Z` | +10000-01-01T00:00:00+00:00 ⇒ UTC 10000-01-01T00:00:00.000000000 | TOO LENIENT |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00+00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | -0001-01-01T00:00:00+00:00 ⇒ UTC -0001-01-01T00:00:00.000000000 | TOO LENIENT |
| `2026-02-29T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00+00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ trailing input | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ trailing input | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input | conforming |

#### `chrono NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%SZ")` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00 ⇒ UTC naive:2026-09-24T12:00:00.000000000 | WRONG VALUE: offset discarded (naive result) |
| `2026-09-24t12:00:00Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24 12:00:00Z` | ✗ input contains invalid characters | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00-00:00` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00+23:59` | ✗ input contains invalid characters | too strict (offset range) |
| `2026-09-24T12:00:00+05:30` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00+24:00` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00+0200` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00+02` | ✗ input contains invalid characters | conforming |
| `2026-09-24T24:00:00Z` | ✗ input is out of range | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:60 ⇒ UTC naive:2016-12-31T23:59:60.000000000 | conforming (→ 23:59:60) |
| `2016-12-31T18:59:60-05:00` | ✗ input contains invalid characters | too strict (no leap second) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:60 ⇒ UTC naive:2026-09-24T23:59:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:60 ⇒ UTC naive:2026-09-24T12:00:60.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.1234567Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.123456789012Z` | ✗ input contains invalid characters | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00Z` | ✗ input contains invalid characters | conforming |
| `2026-09-24T12:00:00` | ✗ premature end of input | conforming |
| `2026-09-24` | ✗ premature end of input | conforming |
| `20260924T120000Z` | ✗ input contains invalid characters | conforming |
| `2026-W39-4T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `2026-267T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-9-24T12:00:00Z` | 2026-09-24T12:00:00 ⇒ UTC naive:2026-09-24T12:00:00.000000000 | TOO LENIENT (naive/local result) |
| ` 2026-09-24T12:00:00Z` | 2026-09-24T12:00:00 ⇒ UTC naive:2026-09-24T12:00:00.000000000 | TOO LENIENT (naive/local result) |
| `2026-09-24T12:00:00Z\n` | ✗ trailing input | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ input contains invalid characters | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00 ⇒ UTC naive:0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00 ⇒ UTC naive:0001-01-01T00:00:00.000000000 | WRONG VALUE: offset discarded (naive result) |
| `9999-12-31T23:59:59Z` | 9999-12-31T23:59:59 ⇒ UTC naive:9999-12-31T23:59:59.000000000 | WRONG VALUE: offset discarded (naive result) |
| `10000-01-01T00:00:00Z` | ✗ input contains invalid characters | conforming |
| `+10000-01-01T00:00:00Z` | +10000-01-01T00:00:00 ⇒ UTC naive:+10000-01-01T00:00:00.000000000 | TOO LENIENT (naive/local result) |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00 ⇒ UTC naive:2026-09-24T12:00:00.000000000 | TOO LENIENT (naive/local result) |
| `-0001-01-01T00:00:00Z` | -0001-01-01T00:00:00 ⇒ UTC naive:-0001-01-01T00:00:00.000000000 | TOO LENIENT (naive/local result) |
| `2026-02-29T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-30T12:00:00Z` | ✗ input is out of range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00 ⇒ UTC naive:2024-02-29T12:00:00.000000000 | WRONG VALUE: offset discarded (naive result) |
| `2026-04-31T12:00:00Z` | ✗ input is out of range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ trailing input | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ trailing input | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ input contains invalid characters | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ input contains invalid characters | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ input contains invalid characters | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ trailing input | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ trailing input | conforming |

#### `time OffsetDateTime::parse(s, &Rfc3339)` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24 12:00:00.0 +23:59:00 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24 12:00:00.0 +05:30:00 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ the 'offset hour' component could not be parsed | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ offset minute was not in range | conforming |
| `2026-09-24T12:00:00+0200` | ✗ a character literal was not valid | conforming |
| `2026-09-24T12:00:00+02` | ✗ a character literal was not valid | conforming |
| `2026-09-24T24:00:00Z` | ✗ hour was not in range | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31 23:59:59.999999999 +00:00:00 ⇒ UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31 18:59:59.999999999 -05:00:00 ⇒ UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2026-09-24T23:59:60Z` | ✗ second was not in range | conforming |
| `2026-09-24T12:00:60Z` | ✗ second was not in range | conforming |
| `2026-09-24T12:00:00.1Z` | 2026-09-24 12:00:00.1 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24 12:00:00.123 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24 12:00:00.123456 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24 12:00:00.1234567 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24 12:00:00.123456789 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24 12:00:00.123456789 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ the 'subsecond' component could not be parsed | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ the 'offset hour' component could not be parsed | conforming |
| `2026-09-24T12:00Z` | ✗ a character literal was not valid | conforming |
| `2026-09-24T12:00:00` | ✗ the 'offset hour' component could not be parsed | conforming |
| `2026-09-24` | ✗ the 'separator' component could not be parsed | conforming |
| `20260924T120000Z` | ✗ a character literal was not valid | conforming |
| `2026-W39-4T12:00:00Z` | ✗ the 'month' component could not be parsed | conforming |
| `2026-267T12:00:00Z` | ✗ a character literal was not valid | conforming |
| `2026-9-24T12:00:00Z` | ✗ the 'month' component could not be parsed | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01 0:00:00.0 +00:00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01 0:00:00.0 +00:00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31 23:59:59.0 +00:00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ a character literal was not valid | conforming |
| `+10000-01-01T00:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `+002026-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `-0001-01-01T00:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `2026-02-29T12:00:00Z` | ✗ day was not in range | conforming |
| `2024-02-30T12:00:00Z` | ✗ day was not in range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29 12:00:00.0 +00:00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ day was not in range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ unexpected trailing characters; the end of input was expected | conforming |

#### `time serde_json (time::serde::rfc3339)` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24 12:00:00.0 +23:59:00 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24 12:00:00.0 +05:30:00 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | ✗ the 'offset hour' component could not be parsed at line 1 column 27 | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ offset minute was not in range at line 1 column 27 | conforming |
| `2026-09-24T12:00:00+0200` | ✗ a character literal was not valid at line 1 column 26 | conforming |
| `2026-09-24T12:00:00+02` | ✗ a character literal was not valid at line 1 column 24 | conforming |
| `2026-09-24T24:00:00Z` | ✗ hour was not in range at line 1 column 22 | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31 23:59:59.999999999 +00:00:00 ⇒ UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31 18:59:59.999999999 -05:00:00 ⇒ UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2026-09-24T23:59:60Z` | ✗ second was not in range at line 1 column 22 | conforming |
| `2026-09-24T12:00:60Z` | ✗ second was not in range at line 1 column 22 | conforming |
| `2026-09-24T12:00:00.1Z` | 2026-09-24 12:00:00.1 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24 12:00:00.123 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24 12:00:00.123456 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24 12:00:00.1234567 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24 12:00:00.123456789 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24 12:00:00.123456789 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ the 'subsecond' component could not be parsed at line 1 column 23 | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ the 'offset hour' component could not be parsed at line 1 column 24 | conforming |
| `2026-09-24T12:00Z` | ✗ a character literal was not valid at line 1 column 19 | conforming |
| `2026-09-24T12:00:00` | ✗ the 'offset hour' component could not be parsed at line 1 column 21 | conforming |
| `2026-09-24` | ✗ the 'separator' component could not be parsed at line 1 column 12 | conforming |
| `20260924T120000Z` | ✗ a character literal was not valid at line 1 column 18 | conforming |
| `2026-W39-4T12:00:00Z` | ✗ the 'month' component could not be parsed at line 1 column 22 | conforming |
| `2026-267T12:00:00Z` | ✗ a character literal was not valid at line 1 column 20 | conforming |
| `2026-9-24T12:00:00Z` | ✗ the 'month' component could not be parsed at line 1 column 21 | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed at line 1 column 23 | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 24 | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed at line 1 column 26 | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01 0:00:00.0 +00:00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01 0:00:00.0 +00:00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31 23:59:59.0 +00:00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ a character literal was not valid at line 1 column 23 | conforming |
| `+10000-01-01T00:00:00Z` | ✗ the 'year' component could not be parsed at line 1 column 24 | conforming |
| `+002026-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed at line 1 column 25 | conforming |
| `-0001-01-01T00:00:00Z` | ✗ the 'year' component could not be parsed at line 1 column 23 | conforming |
| `2026-02-29T12:00:00Z` | ✗ day was not in range at line 1 column 22 | conforming |
| `2024-02-30T12:00:00Z` | ✗ day was not in range at line 1 column 22 | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29 12:00:00.0 +00:00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ day was not in range at line 1 column 22 | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 41 | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 42 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 36 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 37 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 35 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 33 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 34 | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 41 | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 42 | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 35 | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 52 | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 37 | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ unexpected trailing characters; the end of input was expected at line 1 column 35 | conforming |

#### `time OffsetDateTime::parse(s, &Iso8601::DEFAULT)` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | TOO STRICT |
| `2026-09-24T12:00:00z` | ✗ unexpected trailing characters; the end of input was expected | TOO STRICT |
| `2026-09-24 12:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-24 12:00:00.0 +23:59:00 ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24 12:00:00.0 +05:30:00 ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | 2026-09-24 12:00:00.0 +24:00:00 ⇒ UTC 2026-09-23T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+23:60` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24 12:00:00.0 +02:00:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | 2026-09-24 12:00:00.0 +02:00:00 ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31 23:59:59.999999999 +00:00:00 ⇒ UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31 18:59:59.999999999 -05:00:00 ⇒ UTC 2016-12-31T23:59:59.999999999 | conforming (→ 23:59:59) |
| `2026-09-24T23:59:60Z` | ✗ second was not in range | conforming |
| `2026-09-24T12:00:60Z` | ✗ second was not in range | conforming |
| `2026-09-24T12:00:00.1Z` | 2026-09-24 12:00:00.1 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24 12:00:00.123 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24 12:00:00.123456 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24 12:00:00.1234567 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24 12:00:00.123456789 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | 2026-09-24 12:00:00.123456789 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00.Z` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T12:00:00,5Z` | 2026-09-24 12:00:00.5 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.500000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | ✗ the `Parsed` struct did not include enough information to construct the type | conforming |
| `2026-09-24` | ✗ the `Parsed` struct did not include enough information to construct the type | conforming |
| `20260924T120000Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-W39-4T12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-267T12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-9-24T12:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ the 'year' component could not be parsed | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01 0:00:00.0 +00:00:00 ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01 0:00:00.0 +00:00:00 ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | 9999-12-31 23:59:59.0 +00:00:00 ⇒ UTC 9999-12-31T23:59:59.000000000 | conforming |
| `10000-01-01T00:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `+10000-01-01T00:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `+002026-09-24T12:00:00Z` | 2026-09-24 12:00:00.0 +00:00:00 ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-02-29T12:00:00Z` | ✗ day was not in range | conforming |
| `2024-02-30T12:00:00Z` | ✗ day was not in range | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29 12:00:00.0 +00:00:00 ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ day was not in range | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | ✗ unexpected trailing characters; the end of input was expected | conforming (3339-only) |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ unexpected trailing characters; the end of input was expected | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ unexpected trailing characters; the end of input was expected | conforming |

#### `jiff Timestamp::from_str` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24t12:00:00Z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24 12:00:00Z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | lenient (allowed local ext.) |
| `2026-09-24T12:00:00+00:00` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00-00:00` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00+23:59` | 2026-09-23T12:01:00Z ⇒ UTC 2026-09-23T12:01:00.000000000 | conforming |
| `2026-09-24T12:00:00+05:30` | 2026-09-24T06:30:00Z ⇒ UTC 2026-09-24T06:30:00.000000000 | conforming |
| `2026-09-24T12:00:00+24:00` | 2026-09-23T12:00:00Z ⇒ UTC 2026-09-23T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+23:60` | ✗ failed to parse minutes in UTC numeric offset: failed to parse minutes (requires a two digit integer): param | conforming |
| `2026-09-24T12:00:00+0200` | 2026-09-24T10:00:00Z ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00+02` | 2026-09-24T10:00:00Z ⇒ UTC 2026-09-24T10:00:00.000000000 | TOO LENIENT |
| `2026-09-24T24:00:00Z` | ✗ failed to parse two digit integer as hour: parameter 'hour' is not in the required range of 0..=23 | conforming |
| `2016-12-31T23:59:60Z` | 2016-12-31T23:59:59Z ⇒ UTC 2016-12-31T23:59:59.000000000 | conforming (→ 23:59:59) |
| `2016-12-31T18:59:60-05:00` | 2016-12-31T23:59:59Z ⇒ UTC 2016-12-31T23:59:59.000000000 | conforming (→ 23:59:59) |
| `2026-09-24T23:59:60Z` | 2026-09-24T23:59:59Z ⇒ UTC 2026-09-24T23:59:59.000000000 | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 2026-09-24T12:00:59Z ⇒ UTC 2026-09-24T12:00:59.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00.1Z` | 2026-09-24T12:00:00.1Z ⇒ UTC 2026-09-24T12:00:00.100000000 | conforming |
| `2026-09-24T12:00:00.123Z` | 2026-09-24T12:00:00.123Z ⇒ UTC 2026-09-24T12:00:00.123000000 | conforming |
| `2026-09-24T12:00:00.123456Z` | 2026-09-24T12:00:00.123456Z ⇒ UTC 2026-09-24T12:00:00.123456000 | conforming |
| `2026-09-24T12:00:00.1234567Z` | 2026-09-24T12:00:00.1234567Z ⇒ UTC 2026-09-24T12:00:00.123456700 | conforming |
| `2026-09-24T12:00:00.123456789Z` | 2026-09-24T12:00:00.123456789Z ⇒ UTC 2026-09-24T12:00:00.123456789 | conforming |
| `2026-09-24T12:00:00.123456789012Z` | ✗ parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains (expected no unparsed input) | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ failed to parse fractional seconds in time: found decimal after seconds component, but did not find any digi | conforming |
| `2026-09-24T12:00:00,5Z` | 2026-09-24T12:00:00.5Z ⇒ UTC 2026-09-24T12:00:00.500000000 | TOO LENIENT |
| `2026-09-24T12:00Z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-09-24T12:00:00` | ✗ failed to find offset component, which is required for parsing a timestamp | conforming |
| `2026-09-24` | ✗ failed to find time component, which is required for parsing a timestamp | conforming |
| `20260924T120000Z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `2026-W39-4T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got W | conforming |
| `2026-267T12:00:00Z` | ✗ failed to parse two digit integer as month: parameter 'month' is not in the required range of 1..=12 | conforming |
| `2026-9-24T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got   | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ parsed value '2026-09-24T12:00:00Z', but unparsed input "\n" remains (expected no unparsed input) | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got \xD9 | conforming |
| `0000-01-01T00:00:00Z` | 0000-01-01T00:00:00Z ⇒ UTC 0000-01-01T00:00:00.000000000 | conforming |
| `0001-01-01T00:00:00Z` | 0001-01-01T00:00:00Z ⇒ UTC 0001-01-01T00:00:00.000000000 | conforming |
| `9999-12-31T23:59:59Z` | ✗ failed to convert civil datetime to timestamp with offset +00: converting datetime with time zone offset `+0 | TOO STRICT |
| `10000-01-01T00:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| `+10000-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `+002026-09-24T12:00:00Z` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `2026-02-29T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-02` is invalid, must be in range `1..=28` | conforming |
| `2024-02-30T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2024-02` is invalid, must be in range `1..=29` | conforming |
| `2024-02-29T12:00:00Z` | 2024-02-29T12:00:00Z ⇒ UTC 2024-02-29T12:00:00.000000000 | conforming |
| `2026-04-31T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-04` is invalid, must be in range `1..=30` | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[Europe/Paris]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[x-foo=bar]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | 2025-12-31T19:00:00Z ⇒ UTC 2025-12-31T19:00:00.000000000 | conforming (MAY; offset wins) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | 2025-12-31T19:00:00Z ⇒ UTC 2025-12-31T19:00:00.000000000 | VIOLATES 9557 MUST (accepted) |
| `2026-09-24T14:00:00+02:00[+02:00]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | 2026-09-24T12:00:00Z ⇒ UTC 2026-09-24T12:00:00.000000000 | VIOLATES 9557 MUST (accepted) |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ expected lowercase alphabetic byte (or underscore) at the start of an RFC 9557 annotation key, but found `U` | conforming |

#### `jiff Zoned::from_str [offset_conflict=Reject, default]` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24t12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24 12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00-00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+23:59` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+05:30` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+24:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ failed to parse minutes in UTC numeric offset: failed to parse minutes (requires a two digit integer): param | conforming |
| `2026-09-24T12:00:00+0200` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+02` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T24:00:00Z` | ✗ failed to parse two digit integer as hour: parameter 'hour' is not in the required range of 0..=23 | conforming |
| `2016-12-31T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2016-12-31T18:59:60-05:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00.1Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.1234567Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789012Z` | ✗ parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains (expected no unparsed input) | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ failed to parse fractional seconds in time: found decimal after seconds component, but did not find any digi | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `20260924T120000Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-W39-4T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got W | conforming |
| `2026-267T12:00:00Z` | ✗ failed to parse two digit integer as month: parameter 'month' is not in the required range of 1..=12 | conforming |
| `2026-9-24T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got   | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ parsed value '2026-09-24T12:00:00Z', but unparsed input "\n" remains (expected no unparsed input) | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got \xD9 | conforming |
| `0000-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `0001-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `9999-12-31T23:59:59Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `10000-01-01T00:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| `+10000-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `+002026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `-0001-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `2026-02-29T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-02` is invalid, must be in range `1..=28` | conforming |
| `2024-02-30T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2024-02` is invalid, must be in range `1..=29` | conforming |
| `2024-02-29T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-04-31T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-04` is invalid, must be in range `1..=30` | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | ✗ datetime could not resolve to a timestamp since `reject` conflict resolution was chosen, and because datetim | conforming (rejects; MAY) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | ✗ datetime could not resolve to a timestamp since `reject` conflict resolution was chosen, and because datetim | conforming |
| `2026-09-24T14:00:00+02:00[+02:00]` | 2026-09-24T14:00:00+02:00[+02:00] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ failed to find time zone `Mars/Olympus` in time zone database | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ expected lowercase alphabetic byte (or underscore) at the start of an RFC 9557 annotation key, but found `U` | conforming |

#### `jiff DateTimeParser.offset_conflict(AlwaysOffset).parse_zoned` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24t12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24 12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00-00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+23:59` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+05:30` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+24:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ failed to parse minutes in UTC numeric offset: failed to parse minutes (requires a two digit integer): param | conforming |
| `2026-09-24T12:00:00+0200` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+02` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T24:00:00Z` | ✗ failed to parse two digit integer as hour: parameter 'hour' is not in the required range of 0..=23 | conforming |
| `2016-12-31T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2016-12-31T18:59:60-05:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00.1Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.1234567Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789012Z` | ✗ parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains (expected no unparsed input) | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ failed to parse fractional seconds in time: found decimal after seconds component, but did not find any digi | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `20260924T120000Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-W39-4T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got W | conforming |
| `2026-267T12:00:00Z` | ✗ failed to parse two digit integer as month: parameter 'month' is not in the required range of 1..=12 | conforming |
| `2026-9-24T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got   | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ parsed value '2026-09-24T12:00:00Z', but unparsed input "\n" remains (expected no unparsed input) | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got \xD9 | conforming |
| `0000-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `0001-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `9999-12-31T23:59:59Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `10000-01-01T00:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| `+10000-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `+002026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `-0001-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `2026-02-29T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-02` is invalid, must be in range `1..=28` | conforming |
| `2024-02-30T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2024-02` is invalid, must be in range `1..=29` | conforming |
| `2024-02-29T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-04-31T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-04` is invalid, must be in range `1..=30` | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | 2025-12-31T20:00:00+01:00[Europe/Paris] ⇒ UTC 2025-12-31T19:00:00.000000000 | conforming (MAY; offset wins) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | 2025-12-31T20:00:00+01:00[Europe/Paris] ⇒ UTC 2025-12-31T19:00:00.000000000 | VIOLATES 9557 MUST (accepted) |
| `2026-09-24T14:00:00+02:00[+02:00]` | 2026-09-24T14:00:00+02:00[+02:00] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ failed to find time zone `Mars/Olympus` in time zone database | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ expected lowercase alphabetic byte (or underscore) at the start of an RFC 9557 annotation key, but found `U` | conforming |

#### `jiff DateTimeParser.offset_conflict(AlwaysTimeZone).parse_zoned` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24t12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24 12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00-00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+23:59` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+05:30` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+24:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ failed to parse minutes in UTC numeric offset: failed to parse minutes (requires a two digit integer): param | conforming |
| `2026-09-24T12:00:00+0200` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+02` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T24:00:00Z` | ✗ failed to parse two digit integer as hour: parameter 'hour' is not in the required range of 0..=23 | conforming |
| `2016-12-31T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2016-12-31T18:59:60-05:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00.1Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.1234567Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789012Z` | ✗ parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains (expected no unparsed input) | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ failed to parse fractional seconds in time: found decimal after seconds component, but did not find any digi | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `20260924T120000Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-W39-4T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got W | conforming |
| `2026-267T12:00:00Z` | ✗ failed to parse two digit integer as month: parameter 'month' is not in the required range of 1..=12 | conforming |
| `2026-9-24T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got   | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ parsed value '2026-09-24T12:00:00Z', but unparsed input "\n" remains (expected no unparsed input) | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got \xD9 | conforming |
| `0000-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `0001-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `9999-12-31T23:59:59Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `10000-01-01T00:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| `+10000-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `+002026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `-0001-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `2026-02-29T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-02` is invalid, must be in range `1..=28` | conforming |
| `2024-02-30T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2024-02` is invalid, must be in range `1..=29` | conforming |
| `2024-02-29T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-04-31T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-04` is invalid, must be in range `1..=30` | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | 2026-01-01T00:00:00+01:00[Europe/Paris] ⇒ UTC 2025-12-31T23:00:00.000000000 | conforming (MAY; zone wins, local time kept) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | 2026-01-01T00:00:00+01:00[Europe/Paris] ⇒ UTC 2025-12-31T23:00:00.000000000 | VIOLATES 9557 MUST (accepted) |
| `2026-09-24T14:00:00+02:00[+02:00]` | 2026-09-24T14:00:00+02:00[+02:00] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ failed to find time zone `Mars/Olympus` in time zone database | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ expected lowercase alphabetic byte (or underscore) at the start of an RFC 9557 annotation key, but found `U` | conforming |

#### `jiff DateTimeParser.offset_conflict(PreferOffset).parse_zoned` (parse)

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24t12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24 12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming (strict ABNF) |
| `2026-09-24T12:00:00+00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00-00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+23:59` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+05:30` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00+24:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+23:60` | ✗ failed to parse minutes in UTC numeric offset: failed to parse minutes (requires a two digit integer): param | conforming |
| `2026-09-24T12:00:00+0200` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00+02` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T24:00:00Z` | ✗ failed to parse two digit integer as hour: parameter 'hour' is not in the required range of 0..=23 | conforming |
| `2016-12-31T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2016-12-31T18:59:60-05:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T23:59:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:60Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00.1Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.1234567Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00.123456789012Z` | ✗ parsed value '2026-09-24T12:00:00.123456789', but unparsed input "012Z" remains (expected no unparsed input) | TOO STRICT |
| `2026-09-24T12:00:00.Z` | ✗ failed to parse fractional seconds in time: found decimal after seconds component, but did not find any digi | conforming |
| `2026-09-24T12:00:00,5Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24T12:00:00` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-09-24` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `20260924T120000Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `2026-W39-4T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got W | conforming |
| `2026-267T12:00:00Z` | ✗ failed to parse two digit integer as month: parameter 'month' is not in the required range of 1..=12 | conforming |
| `2026-9-24T12:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| ` 2026-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got   | conforming |
| `2026-09-24T12:00:00Z\n` | ✗ parsed value '2026-09-24T12:00:00Z', but unparsed input "\n" remains (expected no unparsed input) | conforming |
| `\u0662\u0660\u0662\u0666-09-24T12:00:00Z` | ✗ failed to parse four digit integer as year: invalid digit, expected 0-9 but got \xD9 | conforming |
| `0000-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `0001-01-01T00:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `9999-12-31T23:59:59Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `10000-01-01T00:00:00Z` | ✗ failed to parse two digit integer as month: invalid digit, expected 0-9 but got - | conforming |
| `+10000-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `+002026-09-24T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | conforming |
| `-0001-01-01T00:00:00Z` | ✗ failed to parse six digit integer as year: invalid digit, expected 0-9 but got - | conforming |
| `2026-02-29T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-02` is invalid, must be in range `1..=28` | conforming |
| `2024-02-30T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2024-02` is invalid, must be in range `1..=29` | conforming |
| `2024-02-29T12:00:00Z` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-04-31T12:00:00Z` | ✗ parsed date is not valid: parameter 'day' for `2026-04` is invalid, must be in range `1..=30` | conforming |
| `2026-09-24T14:00:00+02:00[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T14:00:00+02:00[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[!Europe/Paris]` | 2026-09-24T14:00:00+02:00[Europe/Paris] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=hebrew]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[x-foo=bar]` | ✗ failed to find time zone annotation in square brackets, which is required for parsing a zoned datetime | n/a (API requires [zone]) |
| `2026-09-24T12:00:00Z[!x-foo=bar]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | 2026-01-01T00:00:00+01:00[Europe/Paris] ⇒ UTC 2025-12-31T23:00:00.000000000 | conforming (MAY; zone wins, local time kept) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | 2026-01-01T00:00:00+01:00[Europe/Paris] ⇒ UTC 2025-12-31T23:00:00.000000000 | VIOLATES 9557 MUST (accepted) |
| `2026-09-24T14:00:00+02:00[+02:00]` | 2026-09-24T14:00:00+02:00[+02:00] ⇒ UTC 2026-09-24T12:00:00.000000000 | conforming |
| `2026-09-24T12:00:00Z[u-ca=chinese][!u-ca=japanese]` | ✗ found unsupported RFC 9557 annotation with the critical flag (`!`) set | conforming |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | ✗ failed to find time zone `Mars/Olympus` in time zone database | conforming |
| `2026-09-24T12:00:00Z[U-CA=hebrew]` | ✗ expected lowercase alphabetic byte (or underscore) at the start of an RFC 9557 annotation key, but found `U` | conforming |

#### rust formatters (produce)

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
| `chrono to_rfc3339_opts(Secs, true) [+02:00, use_z ignored]` | `2026-09-24T14:00:00+02:00` | conforming |
| `chrono DateTime<Utc> Display (to_string)` | `2026-09-24 12:00:00 UTC` | WRONG OUTPUT (space separator, ' UTC' suffix) |
| `chrono DateTime<FixedOffset> Display` | `2026-09-24 14:00:00 +02:00` | WRONG OUTPUT (space separator) |
| `chrono DateTime<Utc> Debug` | `2026-09-24T12:00:00Z` | conforming |
| `chrono DateTime<FixedOffset> Debug` | `2026-09-24T14:00:00+02:00` | conforming |
| `chrono serde_json::to_string(DateTime<Utc>)` | `\"2026-09-24T12:00:00Z\"` | conforming |
| `chrono serde_json::to_string(DateTime<FixedOffset>)` | `\"2026-09-24T14:00:00+02:00\"` | conforming |
| `chrono serde_json::to_string(DateTime<Utc>) [120ms]` | `\"2026-09-24T12:00:00.120Z\"` | conforming |
| `chrono serde_json::to_string(NaiveDateTime)` | `\"2026-09-24T12:00:00\"` | WRONG OUTPUT (no offset) |
| `chrono NaiveDateTime Display` | `2026-09-24 12:00:00` | WRONG OUTPUT (space separator) |
| `chrono format("%+") [UTC]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono format("%Y-%m-%dT%H:%M:%S%z")` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (offset without colon) |
| `chrono format("%Y-%m-%dT%H:%M:%S%:z")` | `2026-09-24T14:00:00+02:00` | conforming |
| `chrono Local naive_local().format("%Y-%m-%dT%H:%M:%SZ") [lies]` | `2026-09-24T08:00:00Z` | WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z) |
| `chrono DateTime<Local>::to_rfc3339()` | `2026-09-24T08:00:00-04:00` | conforming |
| `chrono to_rfc3339() [FixedOffset -00:44:30]` | `2026-09-24T11:15:30-00:45` | conforming |
| `chrono to_rfc3339() [FixedOffset +00:00:30]` | `2026-09-24T12:00:30+00:01` | WRONG VALUE (offset seconds dropped: string denotes 12:00:30Z, true instant 12:00:00Z) |
| `chrono to_rfc3339_opts(Secs,true) [FixedOffset -00:44:30]` | `2026-09-24T11:15:30-00:45` | conforming |
| `chrono serde_json [FixedOffset -00:44:30]` | `\"2026-09-24T11:15:30-00:45\"` | conforming |
| `chrono Display [FixedOffset -00:44:30]` | `2026-09-24 11:15:30 -00:44:30` | WRONG OUTPUT (space separator, offset has seconds) |
| `chrono to_rfc3339() [year 0]` | `0000-01-01T00:00:00+00:00` | conforming |
| `chrono to_rfc3339() [year 50]` | `0050-01-01T00:00:00+00:00` | conforming |
| `chrono to_rfc3339() [year 10000]` | `+10000-01-01T00:00:00+00:00` | WRONG OUTPUT (expanded/signed year) |
| `chrono to_rfc3339() [year -1]` | `-0001-01-01T00:00:00+00:00` | WRONG OUTPUT (expanded/signed year) |
| `chrono serde_json [year 10000]` | `\"+10000-01-01T00:00:00Z\"` | WRONG OUTPUT (expanded/signed year) |
| `chrono serde_json [year -1]` | `\"-0001-01-01T00:00:00Z\"` | WRONG OUTPUT (expanded/signed year) |
| `chrono to_rfc3339() [leap 2016-12-31 23:59:59 + 1.5e9 ns]` | `2016-12-31T23:59:60.500+00:00` | conforming |
| `chrono to_rfc3339_opts(Secs,true) [leap 2016-12-31, nanos=1e9]` | `2016-12-31T23:59:60Z` | conforming |
| `chrono to_rfc3339_opts(Secs,true) [leap-nanos on 2026-09-24 12:00:59]` | `2026-09-24T12:00:60Z` | conforming |
| `chrono to_rfc3339_opts(Secs,true) [leap on 2016-12-31 at +01:00]` | `2017-01-01T00:59:60+01:00` | conforming |
| `chrono serde_json [leap 2016-12-31, 1.5e9 ns]` | `\"2016-12-31T23:59:60.500Z\"` | conforming |
| `time format(&Rfc3339) [UTC]` | `2026-09-24T12:00:00Z` | conforming |
| `time format(&Rfc3339) [120ms]` | `2026-09-24T12:00:00.12Z` | conforming |
| `time format(&Rfc3339) [+02:00]` | `2026-09-24T14:00:00+02:00` | conforming |
| `time format(&Rfc3339) [offset -00:44:30]` | ✗ The offset_second component cannot be formatted into the requested format. | n/a |
| `time format(&Rfc3339) [offset +00:00:30]` | ✗ The offset_second component cannot be formatted into the requested format. | n/a |
| `time format(&Rfc3339) [year 0]` | `0000-01-01T00:00:00Z` | conforming |
| `time format(&Rfc3339) [year 50]` | `0050-01-01T00:00:00Z` | conforming |
| `time format(&Rfc3339) [year -1]` | ✗ The year component cannot be formatted into the requested format. | n/a |
| `time format(&Iso8601::DEFAULT) [UTC]` | `2026-09-24T12:00:00.000000000Z` | conforming |
| `time format(&Iso8601::DEFAULT) [+02:00]` | `2026-09-24T14:00:00.000000000+02:00` | conforming |
| `time OffsetDateTime Display` | `2026-09-24 12:00:00.0 +00:00:00` | WRONG OUTPUT (space separator, offset has seconds) |
| `time OffsetDateTime Display [+02:00]` | `2026-09-24 14:00:00.0 +02:00:00` | WRONG OUTPUT (space separator, offset has seconds) |
| `time serde_json (time::serde::rfc3339) [UTC]` | `\"2026-09-24T12:00:00Z\"` | conforming |
| `time serde_json (time::serde::rfc3339) [offset -00:44:30]` | ✗ The offset_second component cannot be formatted into the requested format. | n/a |
| `time serde_json default Serialize (no well-known attr)` | `[2026,267,12,0,0,0,0,0,0]` | WRONG OUTPUT (not ISO-shaped) |
| `time format("[year]-[month]-[day]T[hour]:[minute]:[second]Z") [lies on +02:00]` | `2026-09-24T14:00:00Z` | WRONG VALUE (local wall-clock labelled Z; true instant 12:00:00Z) |
| `time format("...[offset_hour sign:mandatory][offset_minute]") [no colon]` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (offset without colon) |
| `jiff Timestamp Display` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp Display [120ms]` | `2026-09-24T12:00:00.12Z` | conforming |
| `jiff Timestamp Display {:.3} [120ms]` | `2026-09-24T12:00:00.120Z` | conforming |
| `jiff Timestamp Display {:.0} [120ms]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp::display_with_offset(+02)` | `2026-09-24T14:00:00+02:00` | conforming |
| `jiff Timestamp::display_with_offset(-00:44:30)` | `2026-09-24T11:15:30-00:45` | conforming |
| `jiff Timestamp Display [year 0]` | `0000-01-01T00:00:00Z` | conforming |
| `jiff Timestamp Display [year -1]` | `-000001-01-01T00:00:00Z` | WRONG OUTPUT (expanded/signed year) |
| `jiff Timestamp Display [year 50]` | `0050-01-01T00:00:00Z` | conforming |
| `jiff Timestamp Display [Timestamp::MAX]` | `9999-12-30T22:00:00.999999999Z` | conforming |
| `jiff Timestamp Display [Timestamp::MIN]` | `-009999-01-02T01:59:59Z` | WRONG OUTPUT (expanded/signed year) |
| `jiff Zoned Display [Europe/Paris]` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display [UTC]` | `2026-09-24T12:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [Etc/UTC]` | `2026-09-24T12:00:00+00:00[Etc/UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [TimeZone::UTC]` | `2026-09-24T12:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [TimeZone::fixed(-00:44:30)]` | `2026-09-24T11:15:30-00:45[-00:45]` | conforming (RFC 9557) |
| `jiff Zoned Display [TimeZone::fixed(+05)]` | `2026-09-24T17:00:00+05:00[+05:00]` | conforming (RFC 9557) |
| `jiff Zoned Display [1970 Africa/Monrovia]` | `1969-12-31T23:15:30-00:45[Africa/Monrovia]` | conforming (RFC 9557) |
| `jiff Zoned Display [1850 Europe/Paris, LMT]` | `1850-01-01T00:09:21+00:09[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned.timestamp().display_with_offset(zoned.offset()) [1970 Monrovia]` | `1969-12-31T23:15:30-00:45` | conforming |
| `jiff Zoned Display [year 0 UTC]` | `0000-01-01T00:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `jiff Zoned Display [year -1 UTC]` | `-000001-01-01T00:00:00+00:00[UTC]` | WRONG OUTPUT (expanded/signed year) |
| `jiff Zoned Display [Paris, 120ms]` | `2026-09-24T14:00:00.12+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display {:.0} [Paris]` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display after parsing [!Europe/Paris] (round trip)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display after parsing [u-ca=hebrew] (round trip)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff Zoned Display after parsing Z[Europe/Paris] (round trip)` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `jiff DateTimePrinter::new().lowercase(true).timestamp_to_string` | `2026-09-24t12:00:00z` | conforming (but SHOULD use upper case) |
| `jiff DateTimePrinter::new().separator(b' ').zoned_to_string` | `2026-09-24 14:00:00+02:00[Europe/Paris]` | WRONG OUTPUT (space separator) |
| `jiff Zoned::strftime("%Y-%m-%dT%H:%M:%S%z")` | `2026-09-24T14:00:00+0200` | WRONG OUTPUT (offset without colon) |
| `jiff Zoned::strftime("%Y-%m-%dT%H:%M:%S%:z")` | `2026-09-24T14:00:00+02:00` | conforming |
| `jiff civil::DateTime Display [no offset]` | `2026-09-24T14:00:00` | WRONG OUTPUT (no offset) |
| `jiff Zoned::strftime("%Y-%m-%dT%H:%M:%S%:z") [1970 Monrovia]` | `1969-12-31T23:15:30-00:44:30` | WRONG OUTPUT (offset has seconds) |
| `chrono parse_from_rfc3339(2026-09-24T12:00:00Z).to_rfc3339() [round trip]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono serde_json DateTime<FixedOffset> from 2026-09-24T12:00:00Z [round trip]` | `\"2026-09-24T12:00:00Z\"` | conforming |
| `time parse+format(&Rfc3339) 2026-09-24T12:00:00Z [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp parse+Display 2026-09-24T12:00:00Z [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `chrono parse_from_rfc3339(2026-09-24T12:00:00+00:00).to_rfc3339() [round trip]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono serde_json DateTime<FixedOffset> from 2026-09-24T12:00:00+00:00 [round trip]` | `\"2026-09-24T12:00:00Z\"` | conforming |
| `time parse+format(&Rfc3339) 2026-09-24T12:00:00+00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp parse+Display 2026-09-24T12:00:00+00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `chrono parse_from_rfc3339(2026-09-24T12:00:00-00:00).to_rfc3339() [round trip]` | `2026-09-24T12:00:00+00:00` | conforming |
| `chrono serde_json DateTime<FixedOffset> from 2026-09-24T12:00:00-00:00 [round trip]` | `\"2026-09-24T12:00:00Z\"` | conforming |
| `time parse+format(&Rfc3339) 2026-09-24T12:00:00-00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Timestamp parse+Display 2026-09-24T12:00:00-00:00 [round trip]` | `2026-09-24T12:00:00Z` | conforming |
| `jiff Zoned parse("1969-12-31T23:15:30-00:45[Africa/Monrovia]").timestamp() Display` | `1970-01-01T00:00:00Z` | conforming |
| `jiff Timestamp parse("1969-12-31T23:15:30-00:45[Africa/Monrovia]") Display` | `1970-01-01T00:00:30Z` | conforming |


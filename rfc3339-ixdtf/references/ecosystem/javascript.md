# JavaScript / TypeScript: RFC 3339 / RFC 9557 behaviour

**Probed 2026-09-24.** Node 26.8.1 / V8 14.6 with native `Temporal` (+ ajv 8.20.0, ajv-formats 3.0.1). macOS arm64, host `TZ=America/New_York` (UTC−4 on the probe date; a non-UTC zone shows the "silently local" defaults), system tzdata 2026c.

Probe program: `probes/probe_js.mjs` (reads `probes/inputs.json`, 59 strings; `probes/analyze.py` turns its JSON-lines results into the tables below). The raw result tables of the 2026-09-24 run were not committed: re-run the probe to regenerate them. The same program's `adapter` mode ran the 310 conformance vectors on 2026-09-26 (Node 26.8.1; `evals/baselines/probes/vector-runs/js.txt`, section "Conformance vectors").

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts); the at-a-glance matrix is there too. A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Notes the matrix cannot show (all probed)

- **JavaScript `Date.parse`** (V8) rolls invalid calendar dates forward (`2024-02-30` became `2024-03-01`). It reads
  `T24:00` as the next day. It reads a string without an offset as host-local time (`12:00` became `16:00Z`).
  It truncates to milliseconds. The vector runs add: it accepts a NUL at the end (`…Z\u0000`, 3339-5.6-064) and
  even **inside** the time (`T00:00\u0000:00Z`, 3339-5.6-065), and a no-break space (U+00A0) as the separator
  (3339-5.6-071). It rejects every `:60`, real leap seconds included (11 vectors).
- **Temporal**:
  - `Temporal.Instant.from` ignores the time-zone annotation. It accepted an inconsistent **critical** zone and an
    unknown critical zone (`[!Mars/Olympus]`). jiff `Timestamp::from_str` does the same (see `rust.md`). The
    vector runs find 41 too-lenient results in 7 categories (see "Conformance vectors" below): besides the
    critical suffixes, it accepts malformed suffixes (`[Europe/../Paris]`, `[u-ca=a--b]`, a NUL in the zone
    name), experimental `[_foo=bar]` keys, offsets with seconds (`+00:09:21`, `-00:44:30`) and `:60` at any
    minute or offset.
  - `ZonedDateTime.from` rejected both (default `offset:'reject'`). It rejected `[!x-foo=bar]` and
    `[u-ca=chinese][!u-ca=japanese]` correctly. It **drops the `!`** when it prints again
    (`[!Europe/Paris]` became `[Europe/Paris]`). The vector runs find it is not fully strict: it accepts no
    seconds (`T00:00+01:00[Europe/Paris]`), a missing offset (`T00:14:07[Europe/Paris]`), a date only
    (`2022-07-08[Europe/Paris]`), `[+0500]` and a `:60` that is not a leap second at that offset. It rejects the
    valid `-00:00[!Europe/London]` and the valid duplicate `[!u-ca=hebrew][!u-ca=hebrew]`.
  - `Temporal.PlainDateTime.from` rejects `…Z`, but it accepts `…+00:00` and `…+05:30` and **discards the offset**
    (not an instant parser). It reads the leap second `1990-12-31T15:59:60-08:00` as `15:59:59` (3339-5.8-004;
    graded INTERPRETATION "leap-second representation", `references/interpretation.md`).
  - `ZonedDateTime.from` gives `Z[Europe/Paris]` as `+02:00[Europe/Paris]`, which is correct (§3.4 Figure 2).

## Consumers: per-API results

Each table lists only deviations and notable rows; the header line counts the inputs with the plain verdict
"conforming". The tables come from the 2026-09-24 probe strings (`probes/inputs.json` `legacy`). The last column
names the 310-vector set's vector that confirms the verdict (run 2026-09-26, "Conformance vectors" below).
**legacy probe only** = no vector exercises that form for this API (for example, the `Date` adapter returns no
fields, so the ms truncation is not checked by a vector), or the API has no vector adapter (ajv-formats).

### `Date.parse / new Date(s)`

43 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000Z | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00.000Z | TOO LENIENT (3339-5.6-023) |
| `2026-09-24T24:00:00Z` | accepted → UTC 2026-09-25T00:00:00.000Z | TOO LENIENT (→ 2026-09-25 00:00:00) (3339-5.7-001) |
| `2016-12-31T23:59:60Z` | rejected: RangeError: Invalid Date (NaN) | too strict (no leap second) (3339-5.7-025) |
| `2016-12-31T18:59:60-05:00` | rejected: RangeError: Invalid Date (NaN) | too strict (no leap second) (3339-5.7-031) |
| `2026-09-24T12:00:00.123456Z` | accepted → UTC 2026-09-24T12:00:00.123Z | conforming (lossy: fraction truncated to 3 digits); legacy probe only |
| `2026-09-24T12:00:00.1234567Z` | accepted → UTC 2026-09-24T12:00:00.123Z | conforming (lossy: fraction truncated to 3 digits); legacy probe only |
| `2026-09-24T12:00:00.123456789Z` | accepted → UTC 2026-09-24T12:00:00.123Z | conforming (lossy: fraction truncated to 3 digits); legacy probe only |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123Z | conforming (lossy: fraction truncated to 3 digits); legacy probe only |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00.000Z | TOO LENIENT (3339-5.6-021) |
| `2026-09-24T12:00:00` | accepted → UTC 2026-09-24T16:00:00.000Z | TOO LENIENT (as host-local time) (3339-5.6-022) |
| `2026-09-24` | accepted → UTC 2026-09-24T00:00:00.000Z | TOO LENIENT (3339-5.6-020) |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00.000Z | TOO LENIENT; legacy probe only |
| `2026-02-29T12:00:00Z` | accepted → UTC 2026-03-01T12:00:00.000Z | TOO LENIENT (rolled over to 2026-03-01) (3339-5.7-002) |
| `2024-02-30T12:00:00Z` | accepted → UTC 2024-03-01T12:00:00.000Z | TOO LENIENT (rolled over to 2024-03-01) (3339-5.7-008) |
| `2026-04-31T12:00:00Z` | accepted → UTC 2026-05-01T12:00:00.000Z | TOO LENIENT (rolled over to 2026-05-01) (3339-5.7-010) |
| `2024-01-01T00:00:00Z\u0000` (vector only) | accepted | TOO LENIENT (3339-5.6-064) |
| `2024-01-01T00:00\u0000:00Z` (vector only) | accepted | TOO LENIENT (3339-5.6-065) |
| `2024-01-01 00:00:00Z` (NBSP, vector only) | accepted | TOO LENIENT (3339-5.6-071) |

### `Temporal.Instant.from`

44 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+0200` | accepted → UTC 2026-09-24T10:00:00Z | TOO LENIENT (3339-5.6-023) |
| `2026-09-24T12:00:00+02` | accepted → UTC 2026-09-24T10:00:00Z | TOO LENIENT (3339-5.6-024) |
| `2016-12-31T23:59:60Z` | accepted → UTC 2016-12-31T23:59:59Z | conforming (→ 23:59:59; leap-second representation) (3339-5.7-025) |
| `2016-12-31T18:59:60-05:00` | accepted → UTC 2016-12-31T23:59:59Z | conforming (→ 23:59:59; leap-second representation) (3339-5.7-031) |
| `2026-09-24T23:59:60Z` | accepted → UTC 2026-09-24T23:59:59Z | TOO LENIENT (3339-5.7-035) |
| `2026-09-24T12:00:60Z` | accepted → UTC 2026-09-24T12:00:59Z | TOO LENIENT (3339-5.7-037) |
| `2026-09-24T12:00:00.123456789012Z` | rejected: RangeError: Temporal error: Fractional time exceeds nine digits. | TOO STRICT (3339-5.6-006) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.5Z | TOO LENIENT (3339-5.6-033) |
| `2026-09-24T12:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT (3339-5.6-021) |
| `20260924T120000Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT (3339-5.6-052) |
| `+002026-09-24T12:00:00Z` | accepted → UTC 2026-09-24T12:00:00Z | TOO LENIENT; legacy probe only |
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | conforming (MAY; offset wins) (9557-3.4-001, interpretation) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | VIOLATES 9557 MUST (accepted) (9557-3.4-002) |
| `2026-09-24T12:00:00Z[!Mars/Olympus]` | accepted → UTC 2026-09-24T12:00:00Z | VIOLATES 9557 MUST (accepted) (9557-3.4-020) |

### `Temporal.ZonedDateTime.from` / `{offset:'reject'}` [default]

The two keys behave the same on every vector. On the 2026-09-24 probe strings, all 38 applicable inputs behaved as
the RFCs require; 21 plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation
(by design; n/a). The vector runs find deviations that the probe strings did not contain:

| Input | Result | RFC verdict |
|---|---|---|
| `2020-01-01T00:00+01:00[Europe/Paris]` | accepted | TOO LENIENT (no seconds) (9557-1.2-002) |
| `2022-07-08T00:14:07[Europe/Paris]` | accepted | TOO LENIENT (no offset; wall time in the zone) (9557-4.1-040) |
| `2022-07-08[Europe/Paris]` | accepted | TOO LENIENT (date only) (9557-4.1-045) |
| `2022-07-08T00:14:07Z[+0500]` | accepted | TOO LENIENT (offset zone without colon) (9557-4.1-010) |
| `2016-12-31T23:59:60+01:00[Europe/Paris]` | accepted | TOO LENIENT (`:60` is not the leap second at `+01:00`) (9557-3.4-025) |
| `2022-07-08T00:14:07-00:00[!Europe/London]` | rejected: Offsets could not be determined … | TOO STRICT (`-00:00` = unknown local offset, RFC 9557 §2) (9557-3.4-009) |
| `2022-07-08T00:14:07Z[!u-ca=hebrew][!u-ca=hebrew]` | rejected: Duplicate calendar value with critical flag | TOO STRICT (9557-3.3-006) |
| any string without `[time-zone]` (63 vectors, e.g. `1985-04-12T23:20:50.52Z`) | rejected: Time zone annotation is required | n/a (by design) |

### `Temporal.ZonedDateTime.from({offset:'use'})`

36 of 59 probe inputs behaved as the RFCs require (not listed). 21 plain RFC 3339 inputs were rejected because this API requires a `[time-zone]` annotation (by design; n/a). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-01-01T00:00:00+05:00[Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | conforming (MAY; offset wins) (9557-3.4-001, interpretation) |
| `2026-01-01T00:00:00+05:00[!Europe/Paris]` | accepted → UTC 2025-12-31T19:00:00Z | conforming (caller opted into offset:'use' = programmed resolution, §3.4) (9557-3.4-002, interpretation "resolved") |
| the 5 `ZonedDateTime` leniencies above (vector only) | accepted | TOO LENIENT (9557-1.2-002, -4.1-040, -4.1-045, -4.1-010, -3.4-025) |
| `0000-01-01T00:00:00+01:00[!Europe/Paris]` (vector only) | accepted | TOO LENIENT (LMT offset `+00:09:21` cannot match `+01:00`; the critical zone is unprocessable) (9557-3.4-026) |
| `2022-07-08T00:14:07-00:44:30[Europe/Dublin]` (vector only) | accepted | TOO LENIENT (offset with seconds) (9557-4.1-049) |
| `2022-07-08T00:14:07Z[!u-ca=hebrew][!u-ca=hebrew]` (vector only) | rejected | TOO STRICT (9557-3.3-006) |

With `'use'`, `-00:00[!Europe/London]` (9557-3.4-009) is accepted.

### `ajv-formats format:date-time (full)`

55 of 59 probe inputs behaved as the RFCs require (not listed). ajv-formats has no vector adapter: every row is
legacy probe only. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted → valid | too lenient (space; OK only under a stated profile) |
| `2026-09-24T12:00:00+0200` | accepted → valid | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → valid | TOO LENIENT |
| `2026-09-24T23:59:60Z` | accepted → valid | TOO LENIENT |

### `ajv-formats format:date-time (mode:'fast')`

49 of 59 probe inputs behaved as the RFCs require (not listed). ajv-formats has no vector adapter: every row is
legacy probe only. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00+24:00` | accepted → valid | TOO LENIENT |
| `2026-09-24T12:00:00+23:60` | accepted → valid | TOO LENIENT |
| `2026-09-24T12:00:00+0200` | accepted → valid | TOO LENIENT |
| `2026-09-24T12:00:00+02` | accepted → valid | TOO LENIENT |
| `2026-09-24T24:00:00Z` | accepted → valid | TOO LENIENT |
| `2016-12-31T18:59:60-05:00` | rejected: Error: invalid | too strict (no leap second) |
| `2026-09-24T23:59:60Z` | accepted → valid | TOO LENIENT |
| `2026-02-29T12:00:00Z` | accepted → valid | TOO LENIENT |
| `2024-02-30T12:00:00Z` | accepted → valid | TOO LENIENT |
| `2026-04-31T12:00:00Z` | accepted → valid | TOO LENIENT |

## Conformance vectors (`run_vectors.py`, 310-vector set, 2026-09-26)

All runs: `probes/run_vector_probes.py --lang js` (`--batch --target-options fixed --target-has-tzdata yes`,
`TZ=America/New_York`; Node 26.8.1). Report: `evals/baselines/probes/vector-runs/js.txt`. "Scored" excludes skips
and interpretations. `Date` runs as `--target-kind rfc3339` (157 skipped: 128 IXDTF-only, 29 non-default
options); the Temporal keys run as `--target-kind ixdtf` (33 skipped: non-default options).

| Adapter | Pass/scored | Too lenient | Too strict | Wrong value | Interpretation |
|---|---|---|---|---|---|
| `Date.parse` | 119/147 (81.0%) | 17 | 11 | 0 | 6 (rejected all 5 `:60` policy vectors; accepted 3339-5.7-055) |
| `Temporal.Instant.from` | 197/242 (81.4%) | 41 | 4 | 0 | 35 (accepted 32, rejected 3) |
| `Temporal.ZonedDateTime.from` (default) | 172/242 (71.1%) | 5 | 65 (63 n/a: no annotation) | 0 | 35 (accepted 9, rejected 26) |
| `Temporal.ZonedDateTime.from({offset:'reject'})` | 172/242 (71.1%) | 5 | 65 (63 n/a) | 0 | identical to the default |
| `Temporal.ZonedDateTime.from({offset:'use'})` | 163/234 (69.7%) | 7 | 64 (63 n/a) | 0 | 43 (accepted 22, incl. 10 critical inconsistencies "resolved"; rejected 21) |
| `Temporal.PlainDateTime.from` (not an instant parser) | 166/241 (68.9%) | 24 | 51 | 0 | 36 (incl. 3339-5.8-004 leap-second representation `:59`) |

- **`Date.parse` too lenient (17):** space `3339-5.6-015`; date only `-020`; no seconds `-021`; no offset `-022`
  (host-local); `+0100` `-023`; `T24:00` `3339-5.7-001`; 8 impossible days rolled forward (`3339-5.7-002`, `-004`,
  `-006`, `-008`, `-010`, `-012`, `-014`, `-016`); NUL after `Z` `3339-5.6-064`; NUL inside the time `3339-5.6-065`;
  NBSP separator `3339-5.6-071`. **Too strict (11):** every `:60` (`3339-5.8-003`, `-004`, `3339-5.7-025`…`-032`,
  `-038`).
- **`Temporal.Instant.from` too lenient (41)**, by category:
  - RFC 3339 syntax (8): space `3339-5.6-015`; no seconds `3339-5.6-021`, `9557-1.2-002`; `+0100` `3339-5.6-023`;
    `+01` `-024`; `,5` `-033`; basic format `-052`; `T120000` `3339-errata-001`.
  - Offsets with seconds (4): `+01:00:00` `3339-5.6-063`, `-00:44:30` `3339-5.6-084` and `9557-4.1-049`,
    `+00:09:21` `3339-5.6-085`.
  - `:60` without the §5.7 check (6): at the wrong offset `3339-5.7-033`, `-034`, `9557-3.4-025`; at the wrong
    day or minute `3339-5.7-035`, `-036`, `-037`.
  - Critical time zone ignored (11, **VIOLATES 9557 MUST**): inconsistent `9557-3.4-002`, `-005`, `-012`, `-015`,
    `-018`, `-030`, `-034`, `-037`; unknown `9557-3.4-020`, `9557-4.1-043` (`[!u-ca]`); unprocessable
    `9557-3.4-026`.
  - Critical unknown tag value (1): `[!u-ca=klingon]` `9557-3.3-009`.
  - Experimental `_` keys (2): `9557-3.2-001`, `9557-4.2-004`.
  - Malformed suffix syntax (9): `[+0500]` `9557-4.1-010`; zone names `[Europe/]`, `[.]`, `[..]`,
    `[Europe/../Paris]`, NUL in the name (`9557-4.1-017`…`-020`, `-046`); tag values `hebrew-`, `-hebrew`, `a--b`
    (`9557-4.1-028`…`-030`).
  **Too strict (4):** more than 9 fraction digits (`3339-5.6-006`, `-073`, `-074`); `[!u-ca=hebrew][!u-ca=hebrew]`
  (`9557-3.3-006`).
- **`ZonedDateTime` (default / `'reject'`):** too lenient (5) and too strict beyond the annotation rule (2) are in the
  table above. It rejects every elective inconsistency, unknown elective key or value and duplicate elective tag
  (interpretations, allowed by §3.3/§3.4). `'use'` adds 2 more leniencies (`9557-3.4-026`, `9557-4.1-049`) and
  resolves the critical inconsistencies.
- **`Temporal.PlainDateTime.from` too lenient (24):** it drops every offset and zone, so it accepts no offset
  (`3339-5.6-022`), a date only (`-020`, `9557-4.1-045`), `+0100`/`+01`/offsets with seconds (`3339-5.6-023`,
  `-024`, `-063`, `-084`, `-085`, `9557-4.1-049`), `:60` at a wrong offset (`3339-5.7-033`, `-034`, `9557-3.4-025`),
  every critical inconsistency and unprocessable zone (`9557-3.4-002`, `-005`, `-012`, `-015`, `-018`, `-026`,
  `-030`, `-034`, `-037`), `9557-1.2-002`, `9557-4.1-040` and `[_foo=bar]` (`9557-4.2-004`). **Too strict (51):**
  49 strings with `Z` ("UTC designator is not valid"), more than 9 fraction digits (`3339-5.6-074`) and
  `9557-3.3-006`. The leap second `1990-12-31T15:59:60-08:00` becomes `15:59:59` (`3339-5.8-004`, INTERPRETATION
  "leap-second representation").

## Producers (formatters)

| Call | Output | RFC verdict |
|---|---|---|
| `new Date(...).toISOString()` | `2026-09-24T12:00:00.000Z` | conforming |
| `JSON.stringify(new Date(...))` | `2026-09-24T12:00:00.000Z` | conforming |
| `Date#toString()` | `Thu Sep 24 2026 08:00:00 GMT-0400 (Eastern Daylight Time)` | WRONG OUTPUT (not ISO-shaped) |
| `Date#toUTCString()` | `Thu, 24 Sep 2026 12:00:00 GMT` | WRONG OUTPUT (not ISO-shaped) |
| `new Date('+010000-01-01T00:00:00Z').toISOString()` | `+010000-01-01T00:00:00.000Z` | WRONG OUTPUT (expanded/signed year) |
| `new Date(Date.UTC(-1,0,1)).toISOString()` | `-000001-01-01T00:00:00.000Z` | WRONG OUTPUT (expanded/signed year) |
| `new Date(Date.UTC(99,0,1)).toISOString()  [2-digit year → 1999]` | `1999-01-01T00:00:00.000Z` | conforming |
| `toLocaleString('sv-SE')  [common 'ISO-ish' hack]` | `2026-09-24 12:00:00` | WRONG OUTPUT (space separator) |
| `Temporal.Instant#toString()` | `2026-09-24T12:00:00Z` | conforming |
| `Temporal.Instant#toString({timeZone:'Europe/Paris'})` | `2026-09-24T14:00:00+02:00` | conforming |
| `Temporal.ZonedDateTime#toString()` | `2026-09-24T14:00:00+02:00[Europe/Paris]` | conforming (RFC 9557) |
| `Temporal.ZonedDateTime#toString() [non-ISO calendar]` | `2026-09-24T14:00:00+02:00[Europe/Paris][u-ca=hebrew]` | conforming (RFC 9557) |
| `Temporal.ZonedDateTime#toString({timeZoneName:'critical'})` | `2026-09-24T14:00:00+02:00[!Europe/Paris]` | conforming (RFC 9557) |
| `Temporal.ZonedDateTime (UTC zone) #toString()` | `2026-09-24T12:00:00+00:00[UTC]` | conforming (RFC 9557) |
| `Temporal.ZonedDateTime (1850 Europe/Paris, LMT) #toString()` | `1850-01-01T00:00:00+00:09[Europe/Paris]` | WRONG VALUE (LMT +00:09:21 rounded to +00:09, wall time kept: string denotes 1849-12-31T23:51:00Z; true instant 23:50:39Z, +21 s. See §5 item 4) |
| `Temporal.Instant (year 10000) #toString()` | `+010000-01-01T00:00:00Z` | WRONG OUTPUT (expanded/signed year) |
| `Temporal.PlainDateTime#toString()  [no offset]` | `2026-09-24T12:00:00` | WRONG OUTPUT (no offset) |
| `Temporal.ZonedDateTime#toString({smallestUnit:'minute'})` | `2026-09-24T14:00+02:00[Europe/Paris]` | WRONG OUTPUT (no seconds) |

See also `jsonschema.md` (openapi-generator `typescript-fetch` uses `new Date(value)`).

## Detect in code

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `new Date\(\s*[a-zA-Z_$][\w.$]*\s*\)\|Date\.parse\(` on external strings | It reads a missing offset as host-local time. It rolls `2024-02-30` forward to `2024-03-01`. It reads `T24:00` as the next day. It accepts `+0200`, `T12:00Z`, a NUL and an NBSP separator. It rejects leap seconds. It truncates to ms. | the strict regex, then `Temporal.Instant.from(s)` (or `Date` if ms precision is enough) |
| `\.toISOString\(\)` | Years outside 0000–9999 print as `+010000-…` / `-000001-…` (**WRONG OUTPUT**) | range-check the year before you serialize |
| `toLocaleString\(\|toLocaleDateString\(\|\.toString\(\)\|toUTCString\(` used for the wire | Not RFC 3339 (`sv-SE` hack gives `2026-09-24 12:00:00`, no offset) | `toISOString()` / `Temporal.Instant#toString()` |
| `Temporal\.Instant\.from\(` on IXDTF input | It ignores the zone annotation, even when critical: it accepted `+05:00[!Europe/Paris]` and `[!Mars/Olympus]` (**VIOLATES 9557 MUST**). It also accepts `,5`, the basic format, `+002026`, offsets with seconds, malformed suffixes and `:60` on any date (41 too-lenient vectors). It rejects more than 9 fraction digits. | `Temporal.ZonedDateTime.from(s)` (default `offset:'reject'`) when a suffix is present |
| `ZonedDateTime\.from\([^)]*offset:\s*['"](use\|ignore\|prefer)` | It silently resolves the §3.4 inconsistency. This is legal only if it is the documented, programmed policy. | leave the default `'reject'` for critical input |
| `ZonedDateTime\.from\(` as a validator | Even with the default it accepts no seconds, no offset (`T00:14:07[Europe/Paris]`), a date only and `[+0500]` (vectors 9557-1.2-002, -4.1-040, -4.1-045, -4.1-010) | the strict regex on the part before `[`, then `ZonedDateTime.from` |
| `Temporal\.PlainDateTime\.from\(` on timestamps | It discards `+05:30` and keeps the wall time | `Instant.from` / `ZonedDateTime.from` |
| `toString\(\{[^}]*smallestUnit:\s*['"](minute\|hour)` | It drops the seconds field (**WRONG OUTPUT**) | the default precision |
| `addFormats\([^)]*mode:\s*['"]fast` | Fast mode accepts `+24:00`, `+23:60`, `T24:00`, `2024-02-30` and `+0200` | full mode + the strict regex (`ajv.addFormat`) |
| `format:\s*['"]date-time['"]` (ajv full) | It accepts `+0200`, `+02`, a space separator and `:60` on any date | a custom format that uses the strict regex |

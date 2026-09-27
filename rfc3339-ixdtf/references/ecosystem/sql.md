# SQL engines (SQLite, PostgreSQL): RFC 3339 / RFC 9557 behaviour

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts). A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Environment and method (probed 2026-09-25)

**Environment.** macOS arm64, `TZ=America/New_York` for every probe process (the PostgreSQL server itself was
started with the same `TZ`; each session sets `TimeZone` explicitly). System tzdata 2026c; PostgreSQL uses the
tz database bundled in its Homebrew build.
SQLite **3.51.0** (the library linked into Python 3.13.9 `sqlite3`; the Homebrew `sqlite3` CLI is 3.53.4 and was
not used) · PostgreSQL **17.11** (Homebrew bottle `postgresql@17`, `aarch64-apple-darwin27.0.0`, Apple clang 21)
driven through psycopg 3.3.6 (libpq 18.6), server defaults except `TimeZone` / `DateStyle` set per row.
MySQL/MariaDB: **not probed** (no lightweight server option: Homebrew `mysql` pulls a full server plus
dependencies, several hundred MB; SQLite covers the embedded case). Its rows stay "unverified (from docs)" (end of this file).

Probe sources: `probes/sql/` (`probe_sqlite.py`, `probe_pg.py`, shared `common.py`; commands in each file's
docstring; grep sample `testdata/risky_sql.txt`). Probe inputs: `probes/inputs.json` (59 strings). Vector
runs: `run_vectors.py --target-kind rfc3339 --target-options fixed --target-has-tzdata yes` against
vectors.json (310 vectors, sha256 `4e700dd49a20`; 147 scored under these options). Neither engine keeps
the written offset (`timestamptz` and SQLite results are UTC instants), so the adapters return no `fields`.
They add `"utc"` instead, and `probes/swift/instant_check.py` compares each accepted vector's instant with
rfcdt's.

## Conformance vectors (`run_vectors.py`)

Instant-check columns (`probes/swift/instant_check.py`, run by `probes/run_vector_probes.py`): **compared** =
accepted vectors that rfcdt can parse (valid or not); **wrong** = the instant differs by 1 ms or more (a WRONG
VALUE even where the runner says "pass", because the runner sees no fields); **lossy** = below 1 ms; **leap** = a `:60`
read as `:59` or as the next second (a representation limit on a valid leap second; on an invalid one it is part of
the TOO LENIENT count).

| Target (adapter) | Pass / scored | TOO LENIENT | TOO STRICT | Compared | Wrong | Lossy | Leap | Notes |
|---|---|---|---|---|---|---|---|---|
| SQLite `datetime(s)` | 110 / 147 | 22 | 15 | 50 | 10 | 0 | 0 | the 10 = every accepted vector with a fraction (whole-second API: 3339-5.8-001, 3339-5.6-008, 3339-A-007, …) |
| SQLite `strftime('%Y-%m-%dT%H:%M:%fZ', s)` | 110 / 147 | 22 | 15 | 49 | 0 | 2 | 0 | same accept set for all four SQLite functions; 1 malformed output (`…00:00:  nullZ`, 3339-5.6-073) |
| SQLite `julianday(s)` | 110 / 147 | 22 | 15 | 50 | 1 | 2 | 0 | 3339-5.6-073 (1050-digit fraction dropped) |
| SQLite `unixepoch(s, 'subsec')` | 110 / 147 | 22 | 15 | 50 | 1 | 2 | 0 | same |
| SQLite strict regex + upper-case `T` + `strftime` + `date()` round-trip check | **134 / 147** | 0 | 13 | 45 | 0 | 2 | 0 | rejects leap seconds (by choice) and offsets beyond ±14:59 |
| PostgreSQL `s::timestamptz` (TimeZone America/New_York or UTC) | 99 / 147 | 41 | 7 | 70 | 1 | 2 | 20 | 3339-1-003 (`…Z/P1D` read as +1 h); leap seconds roll to the next second |
| PostgreSQL `s::timestamp` (without time zone) | 99 / 147 | 41 | 7 | 70 | **15** | 1 | 14 | offset silently dropped (3339-5.8-002, 3339-5.6-011, 3339-5.6-079, …) |
| PostgreSQL `to_timestamp(s, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM')` | 87 / 147 | 8 | **52** | 7 | 0 | 0 | 0 | `TZH` rejects `Z`; accepts `''` |
| PostgreSQL `jsonb_path_query(to_jsonb(s), '$.datetime()')` | 107 / 147 | 22 | 18 | 46 | 0 | 1 | 0 | `$.timestamp_tz()` identical; the "lossy" one is 3339-5.6-006 `.000000000001` → `.000001` (see below) |
| PostgreSQL strict regex (`~`) then `::timestamptz` | **130 / 147** | 0 | 17 | 43 | 0 | 2 | 0 | rejects `:60`, ±16:00–23:59, year 0000, fractions > 128 digits |

The instant check cannot see a wrong value on an input that rfcdt rejects, and it counts a valid leap second
read as the next second as "leap", not as wrong (`references/interpretation.md`, "Grading vector results").

Adapters: `probe_sqlite.py adapter <api>`, `probe_pg.py adapter <api>`. Baseline (each key's report and instant-check lines): `evals/baselines/probes/vector-runs/sql.txt`.

## Consumers: per-API results

The four SQLite functions share one parser (`parseDateOrTime` in `date.c`), so the accept set is identical and
the rows are merged. They differ only in what they return. Rows are the legacy probe strings (`probes/inputs.json` "legacy"); a vector ID in the verdict cites the vector of the same case, and "legacy probe only" marks a row that no vector covers.

### SQLite `datetime(s)` / `strftime(fmt, s)` / `julianday(s)` / `unixepoch(s, 'subsec')`

39 of 59 probe inputs (41 for `strftime`/`julianday`/`unixepoch`, which keep milliseconds) behaved as the RFCs
require (not listed). SQLite applies the offset and returns UTC; `NULL` = rejected. Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | `NULL` (lower-case `z` **is** accepted) | TOO STRICT |
| `2026-09-24 12:00:00Z` | `2026-09-24 12:00:00` | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+23:59` | `NULL` (offsets limited to ±14:59; `+14:59` accepted, `+15:00` NULL) | too strict (offset range) |
| `2026-09-24T24:00:00Z` | `datetime` → `2026-09-24 24:00:00`; `strftime` → `2026-09-24T24:00:00.000Z` (hour 24 echoed); `julianday`/`unixepoch` → 2026-09-25T00:00Z | TOO LENIENT (and invalid output) |
| `2016-12-31T23:59:60Z` · `2016-12-31T18:59:60-05:00` | `NULL` | too strict (no leap second) |
| `…:00.1Z` … `…:00.123456789012Z` | `datetime` drops the fraction; others keep 3 digits, **truncated** (`.9999` → `.999`) | conforming (lossy) |
| `2024-01-01T00:00:00.` + 309 digits + `Z` | fraction silently dropped (`julianday`/`unixepoch` → `…00:00:00.000`) | WRONG VALUE (−0.123 s) |
| same, ≥ 310 digits | `strftime('…%fZ')` → `2024-01-01T00:00:  nullZ` | **WRONG OUTPUT** |
| `2026-09-24T12:00Z` | 12:00:00Z | TOO LENIENT |
| `2026-09-24T12:00:00` | 12:00:00 (read as **UTC**, not host-local) | TOO LENIENT |
| `2026-09-24` | 00:00:00 | TOO LENIENT |
| `2026-09-24T12:00:00Z\n` (also trailing space, `\t`, `\r`, `\r\n`) | 12:00:00Z | TOO LENIENT |
| `2024-01-01T00:00:00Z\0…` · `2024-01-01T00:00\0:00Z` (vectors) | accepted; the parser stops at NUL, so the second reads as `T00:00` | TOO LENIENT |
| `2024-01-0112:00:00Z` (no separator; vector) · `2024-01-01T12:00:00 Z` | 12:00:00Z | TOO LENIENT |
| `-0001-01-01T00:00:00Z` | `datetime` → `-0001-01-01 00:00:00`; `strftime` → `-001-01-01T…` | TOO LENIENT (and malformed output) |
| `2026-02-29T12:00:00Z` · `2024-02-30…` · `2026-04-31…` | rolled over to `03-01`, `03-01`, `05-01` | TOO LENIENT (silently normalized) |
| `0000-01-01T00:00:00Z` | `0000-01-01 00:00:00` | conforming |
| every `[…]` suffix, `+0200`, `+02`, `,5`, `.Z`, basic/week/ordinal, 5-digit and signed-5/6-digit years | `NULL` | conforming |

Also accepted (not in `inputs.json`): `'now'`, bare `12:00:00` (→ `2000-01-01 12:00:00`), and numbers (Julian day
or, with a modifier, Unix seconds).

### PostgreSQL `s::timestamptz` (session `TimeZone` America/New_York; UTC gives the same verdicts)

38 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | `2026-09-24 08:00:00-04` (12:00Z) | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+23:59` | rejected: time zone displacement out of range (limit ±15:59) | too strict (offset range) |
| `2026-09-24T12:00:00+0200` · `…+02` | 10:00Z | TOO LENIENT |
| `2026-09-24T24:00:00Z` | 2026-09-25T00:00Z (`24:00:00.1` and `24:00:01` rejected) | TOO LENIENT |
| `2016-12-31T23:59:60Z` · `…18:59:60-05:00` | 2017-01-01T00:00:00Z (rolled to the next second) | conforming (leap-second representation: next second; 3339-5.7-025, 3339-5.7-031) |
| `2026-09-24T23:59:60Z` | 2026-09-25T00:00Z: `:60` accepted at any minute, no §5.7 check | TOO LENIENT |
| `2026-09-24T12:00:60Z` | 12:01:00Z | TOO LENIENT |
| `…:60.5Z` / `…:60.999Z` | rejected: field value out of range | too strict (no leap second) (3339-5.7-027) |
| `…:00.1234567Z` … `…:00.123456789012Z` | `.123457`: rounded to microseconds, half to even (`.1234565` → `.123456`, `.1234575` → `.123458`; `.9999995` → next second) | conforming (lossy) |
| fraction of more than 128 digits | rejected: invalid input syntax | too strict (length limit) |
| `2026-09-24T12:00:00.Z` | 12:00:00Z | TOO LENIENT |
| `2026-09-24T12:00Z` | 12:00:00Z | TOO LENIENT |
| `2026-09-24T12:00:00` | `12:00:00-04` = 16:00Z (host **session** zone; with `TimeZone=UTC` it is 12:00Z) | TOO LENIENT (session-zone result) |
| `2026-09-24` | midnight in the session zone | TOO LENIENT |
| `20260924T120000Z` · `2026-267T12:00:00Z` · `2026-9-24…` · `2024/01/01T12:00:00Z` | 12:00Z | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` · `…Z\n` · `…Z\r\n` · `…Z ` | 12:00Z | TOO LENIENT |
| `10000-01-01T00:00:00Z` (also `12026-…`) | accepted (range is 4713 BC – 294276 AD) | TOO LENIENT |
| `0000-01-01T00:00:00Z` | rejected: field value out of range (there is no year 0; `1 BC` syntax instead) | too strict (range limit) |
| `…T12:00:00+05:30:15` · `…-00:44:30` · `…+00:09:21` | accepted, offset seconds applied | TOO LENIENT |
| `…T12:00:00UTC` · `… PST` · `… Europe/Paris` · `…GMT+1` · `1985-04-12T23:20:50Z Fri` | accepted (zone names, abbreviations, POSIX specs, day names) | TOO LENIENT |
| `2024-01-01_12:00:00Z` · `…T12:00:00 Z` · `T1:00:00Z` · `T12:0:00Z` · `+1:00` · `T120000Z` · `T12:00.5Z` · `T12:00:.5Z` · `T00:00:0.5Z` · `T00:00:05.Z` (vectors 3339-5.6-018, -029, -045, -048, -025, 3339-errata-001, 3339-A-001, -003, -004, -005) | accepted | TOO LENIENT |
| `2024-01-01T00:00:00Z/P1D` (vector) | 2024-01-01T01:00:00Z (`…Z/P2D` gives 02:00Z: the tail is misread as a zone/offset) | TOO LENIENT + WRONG VALUE (+1 h) |
| every `[…]` suffix, `+24:00`, `+23:60`, `,5`, week date, `+10000`, `+002026`, `-0001`, Feb 29/30, Apr 31, Arabic digits | rejected | conforming |

Also accepted: `'epoch'`, `'now'`, `'today'`, `'tomorrow'`, `'infinity'`, `'-infinity'`, `J2461308` (Julian day),
`Thu Sep 24 12:00:00 2026 PST`, `September 24, 2026 12:00 pm` and the `4714-11-24 … BC` era syntax. (`'allballs'`
is a `time` literal only: rejected here.) `DateStyle` field order does not affect ISO-shaped input (`2026-09-04T…` is 4 September under both `ISO, MDY` and `ISO, DMY`), but it does flip slashed input (`04/09/2026` = 9 April vs 4 September).

### PostgreSQL `s::timestamp` (without time zone)

Same accept set as `timestamptz` (37 of 59 conforming); the difference is the value: **any offset is silently
discarded** (documented: "PostgreSQL will silently ignore any time zone indication").

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00+05:30` | `2026-09-24 12:00:00` (true instant 06:30Z) | **WRONG VALUE** (−5 h 30 min if read as UTC) |
| every vector with a non-zero offset (15 accepted vectors, e.g. `1996-12-19T16:39:57-08:00`) | wall time kept, offset dropped | **WRONG VALUE** (instant check: 15) |
| `2026-09-24T12:00:00Z` / `+00:00` | `2026-09-24 12:00:00` | conforming only by coincidence |
| other rows | as for `timestamptz` | |

### PostgreSQL `to_timestamp(s, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM')`

35 of 59 conforming, mostly because it rejects nearly everything with `Z`.

| Input | Result | RFC verdict |
|---|---|---|
| `…Z` / `…z` (incl. `0001-…Z`, `9999-…Z`, `2024-02-29…Z`) | rejected: invalid value "Z" for "TZH" | **TOO STRICT** (52 vectors) |
| any fraction (`.1Z`, `.5+05:45`) | rejected: invalid value ".1" for "TZH" (the template has no fraction) | TOO STRICT |
| `2026-09-24T12:00:00+02` · `…+1:00` | 10:00Z | TOO LENIENT |
| `2026-09-24T12:00:00` · `2026-09-24` | midnight / 12:00 in the **session** zone | TOO LENIENT |
| `''` (empty string; vector) | `0001-01-01 00:00:00+00 BC` | TOO LENIENT |
| `…+01:00:00` · `…-00:44:30` | accepted (trailing text ignored) | TOO LENIENT |
| `…+02:00[Europe/Paris]` · `…+05:00[!Europe/Paris]` · `…[+02:00]` | accepted, suffix ignored (critical ones too) | lenient (accepts suffix; RFC 3339-only consumer) (legacy probe only: the one RFC 3339-profile suffix vector, 3339-5.6-062 `Z[Europe/Paris]`, is rejected because `TZH` rejects `Z`) |
| `2016-12-31T18:59:60-05:00` | rejected: field value out of range | too strict (no leap second) |

### PostgreSQL `jsonb_path_query(to_jsonb(s), '$.datetime()')` (and `$.timestamp_tz()`)

41 of 59 conforming. SQL/JSON tries a fixed list of ISO templates.

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: datetime format is not recognized | TOO STRICT |
| `…+23:59` | rejected | too strict (offset range) |
| `…:00.1234567Z` and longer | rejected (templates stop at 6 fraction digits) | **TOO STRICT** (3339-5.6-013) |
| `…:00.0000001Z` · `…:00.000000000001Z` (leading zeros) | accepted as `.000001` (the digits after the zeros are read as microseconds) | WRONG VALUE (+1 µs; neither truncation nor rounding: 3339-5.6-006, seen by the instant check as "lossy") |
| `2016-12-31T23:59:60Z` | rejected | too strict (no leap second) |
| `2026-09-24 12:00:00Z` | `2026-09-24T12:00:00+00:00` | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00+02` · `…+1:00` | 10:00Z | TOO LENIENT |
| `2026-09-24T12:00:00` · `2026-09-24` | `datetime()` returns a `timestamp`/`date` (no zone); `timestamp_tz()` casts it in the **session** zone (16:00Z) | TOO LENIENT |
| `2026-9-24…` · `2024-01-1…` · `T1:00:00Z` · `2024-00-10` · `2024-01-00` (vectors) | accepted | TOO LENIENT |
| ` 2026-09-24T12:00:00Z` · `…Z\n` · `…Z\r\n` · `…Z ` | accepted | TOO LENIENT |
| `…T12:00:00UTC` · `T12:0:00Z` · `T00:00:0.5Z` (vectors 3339-5.6-030, 3339-5.6-048, 3339-A-004) | accepted | TOO LENIENT |
| `24-01-01T12:00:00Z` | year **0024** | TOO LENIENT |
| `10000-…Z` · `+10000-…Z` · `+002026-…Z` | accepted (`+002026` → 2026) | TOO LENIENT (3339-5.6-036, 3339-5.6-037 `+2024-…`; the `+10000` / `+002026` forms: legacy probe only) |
| `-0001-01-01T00:00:00Z` | `0001-01-01T00:00:00+00:00 BC` (= astronomical year 0, not −1) | TOO LENIENT (and one year off) |
| `0000-01-01T00:00:00Z` | `0001-…+00:00 BC` (the correct instant) | conforming |

## Producers (formatters)

Every output was checked with `rfcdt.py check`. The value is 2026-09-24T12:00:00Z unless the row says otherwise.

| Call (session `TimeZone`) | Output | RFC verdict |
|---|---|---|
| PG `v::text` / implicit text cast, `DateStyle ISO` (America/New_York) | `2026-09-24 08:00:00-04` | **WRONG OUTPUT** (space separator, hour-only offset) |
| same, UTC | `2026-09-24 12:00:00+00` | WRONG OUTPUT |
| same, Asia/Kolkata / America/St_Johns | `2026-09-24 17:30:00+05:30` / `2026-09-24 09:30:00-02:30` | WRONG OUTPUT (space separator) |
| same, fractions | `…12:00:00.5+00`, `…12:00:00.123456+00`; 7 digits in → `.123457` | WRONG OUTPUT (variable-length fraction, trailing zeros trimmed) |
| `v::text`, `DateStyle SQL` / `Postgres` / `German` | `09/24/2026 08:00:00 EDT` / `Thu Sep 24 08:00:00 2026 EDT` / `24.09.2026 08:00:00 EDT` | WRONG OUTPUT (not RFC 3339 at all) |
| `v::text`, Africa/Monrovia, 1970-01-01T12:00:00Z | `1970-01-01 11:15:30-00:44:30` | WRONG OUTPUT (offset with seconds; instant right) |
| `v::text`, Europe/Paris, 1850-01-01 00:00 local | `1850-01-01 00:00:00+00:09:21` | WRONG OUTPUT (same) |
| `v::text`, year 10000 / 1 BC / `infinity` | `10000-01-01 23:59:59+00` / `0001-12-31 00:00:00+00 BC` / `infinity` | WRONG OUTPUT |
| `timestamp` (no tz) `::text` | `2026-09-24 12:00:00` | WRONG OUTPUT (no offset) |
| **`to_json(v)` / `to_jsonb(v)` / `json_build_object` / `row_to_json`** (America/New_York) | `"2026-09-24T08:00:00-04:00"` | conforming (ignores `DateStyle`: German gave the same) |
| same, UTC | `"2026-09-24T12:00:00+00:00"` | conforming (Advisory, rule 2: never `Z`, even when the session zone is UTC) |
| same, Asia/Kolkata | `"2026-09-24T17:30:00+05:30"` | conforming |
| `to_json(v)`, fraction .5 | `"2026-09-24T12:00:00.5+00:00"` | conforming (variable-length fraction: §5.1 string sort breaks) |
| `to_json(v)`, Africa/Monrovia 1970 / Europe/Paris 1850 | `"1970-01-01T11:15:30-00:44:30"` / `"1850-01-01T00:00:00+00:09:21"` | **WRONG OUTPUT** (offset with seconds) |
| `to_json(v)`, America/New_York, 0001-01-01T00:00:00Z | `"0001-12-31T19:03:58-04:56:02 BC"` | WRONG OUTPUT (LMT offset seconds and ` BC`; every zone has an LMT era) |
| `to_json(v)`, year 10000 / 1 BC / `infinity` | `"10000-01-01T23:59:59+00:00"` / `"0001-12-31T00:00:00+00:00 BC"` / `"infinity"` | **WRONG OUTPUT** (no error path) |
| `to_json(timestamp without tz)` or `to_json(v AT TIME ZONE 'UTC')` | `"2026-09-24T12:00:00"` | **WRONG OUTPUT** (no offset) |
| `to_char(v, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM')` (New York / UTC / St_Johns) | `2026-09-24T08:00:00-04:00` / `…12:00:00+00:00` / `…09:30:00-02:30` | conforming |
| same, Africa/Monrovia 1970 | `1970-01-01T11:15:30-00:44` | **WRONG VALUE** (denotes 11:59:30Z; true 12:00:00Z, −30 s) |
| `to_char(v, '…SSOF')` / `'…SS.USOF'` (New York) | `2026-09-24T08:00:00-04` / `…08:00:00.000000-04` | **WRONG OUTPUT** (`OF` prints hours only when minutes are 0; `+05:30` in Kolkata) |
| `to_char(v, '…SSOF')`, Africa/Monrovia, year 0001 (LMT −00:43:08) | `0001-01-01T11:16:52-00:43` | **WRONG VALUE** (−8 s) |
| `to_char(v, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')` (New York) | `2026-09-24T08:00:00Z` | **WRONG VALUE** (local wall time labelled Z; −4 h) |
| `to_char(v AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')` | `2026-09-24T12:00:00.000000Z` | conforming (fixed width) |
| same pattern, year 10000 | `10000-01-01T23:59:59.000Z` | WRONG OUTPUT (5-digit year) |
| same pattern, 1 BC | `0001-12-31T00:00:00Z` | **WRONG VALUE** (1 BC printed as AD 1: `YYYY` carries no era, so the string denotes an instant one year later) |
| `to_char(v, '…"T"HH:MI:SSOF')` (15:00Z) | `2026-09-24T03:00:00+00` | WRONG VALUE (`HH` = 12-hour clock) and WRONG OUTPUT |
| `to_char(v, '…"T"HH24:MM:SSOF')` | `2026-09-24T12:09:00+00` | WRONG VALUE (`MM` = month) |
| `to_char(v, 'IYYY-MM-DD…')`, 2029-12-31 | `2030-12-31T12:00:00+00` | WRONG VALUE (ISO week-numbering year, like Java `YYYY`) |
| `to_char(v, '…SS.FF6OF')` | `2026-09-24T12:00:00.123456+00` | WRONG OUTPUT (`OF`) |
| SQLite `datetime('now')` / `CURRENT_TIMESTAMP` / `datetime('now','subsec')` | `2026-09-26 05:37:43` / same / `…43.400` | **WRONG OUTPUT** (space separator, no offset; the value is UTC by definition) |
| SQLite `strftime('%Y-%m-%dT%H:%M:%fZ', x)` | `2026-09-24T12:00:00.123Z` | conforming (fixed 3 digits, truncated) |
| SQLite `strftime('%Y-%m-%dT%H:%M:%SZ', x)` / `'%FT%TZ'` | `2026-09-24T12:00:00Z` | conforming |
| SQLite `strftime('…%SZ', 'now', 'localtime')` | `2026-09-26T01:37:43Z` | **WRONG VALUE** (local wall time labelled Z; −4 h) |
| SQLite `datetime(…, 'localtime')` | `2026-09-26 01:37:43` | WRONG OUTPUT (no offset; host-local) |
| SQLite `strftime('…%z', …)` | `NULL` (`%z` unsupported) | refuses (NULL) |
| SQLite `strftime('%Y-%m-%dT%H:%M:%SZ', '2026-09-24T24:00:00Z')` | `2026-09-24T24:00:00Z` | **WRONG OUTPUT** (echoes hour 24) |
| SQLite `datetime(x, '-1 day')` below year 1 / `datetime('0000-01-01…')` | `0000-12-31 00:00:00` | WRONG OUTPUT (space); year 0000 in range |
| SQLite past year 9999 (`+1 second`, `253402300800, 'unixepoch'`) | `NULL` | refuses (safe) |

## Detect in code

`rfcdt.py scan` covers part of this for `.sql` files: `SCAN-SQL-TO-CHAR-Z`, `SCAN-SQL-TO-CHAR-OFFSET`,
`SCAN-SQL-MYSQL-FORMAT-Z` and `SCAN-SQL-TEXT-CAST` (added after this probe). SQL embedded in other languages' strings is
not scanned by these rules; grep for it.

Grep patterns are ERE, case-insensitive (`grep -niE`); tested on `probes/sql/testdata/risky_sql.txt` (each row hits
its risky lines). A hit is a lead, not a finding.

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `::timestamp([^tz_]\|$)` · `\btimestamp( *\([0-6]\))?( without time zone)? *(,\|\)\|not null\|null\|default\|;)` | `timestamp` without time zone **drops the offset** of every input (15 WRONG VALUE vectors) and prints no offset | `timestamptz` columns and casts |
| `::timestamptz\b` · `::timestamp with time zone` · `as timestamptz\)` on API/ingest input | Accepts `+0200`, `+02`, `T12:00Z`, `.Z`, basic/ordinal dates, 1-digit fields, whitespace, `24:00`, `:60` at any minute, zone names/abbreviations, 5-digit years, offset seconds; a missing offset takes the **session** `TimeZone` | validate first: `CASE WHEN s ~ '^[0-9]{4}-(0[1-9]\|1[0-2])-(0[1-9]\|[12][0-9]\|3[01])[Tt]([01][0-9]\|2[0-3]):[0-5][0-9]:([0-5][0-9]\|60)(\.[0-9]+)?([Zz]\|[+-]([01][0-9]\|2[0-3]):[0-5][0-9])$' THEN s::timestamptz END` (or a `CHECK`/domain). ARE `$` is end of string (not before `\n`) unless `(?n)`. Passed 130/147 |
| `::(text\|varchar)\b` · `as (text\|varchar)\)` · `\|\| *[a-z_]*(_at\|time\|ts)\b` | `DateStyle ISO` text: space, `-04` hour-only offsets, trimmed fractions, `BC`, offset seconds; other DateStyles are not ISO at all | `to_json(v) #>> '{}'` or `to_char(v AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')` |
| `to_char\([^;]*"Z"` | A literal `Z` on session-local wall time: `08:00:00Z` for 12:00Z. Correct **only** after `AT TIME ZONE 'UTC'` (confirm by reading the line) | `to_char(v AT TIME ZONE 'UTC', '…"Z"')` |
| `to_char\([^;]*(SS\|US\|MS\|FF[1-6])OF'` | `OF` prints `-04` / `+00` (hours only) | `TZH:TZM` |
| `to_char\([^;]*\bHH:` · `HH24:MM` · `IYYY` | 12-hour `HH`, `MM` (month) for minutes, ISO week-year | `HH24`, `MI`, `YYYY` |
| `to_timestamp\([^,]+, *'` | Template parsing: `TZH` rejects `Z` (52 TOO STRICT vectors), no fraction unless `.US`, trailing text and `[…]` suffixes ignored, `''` becomes `0001-01-01 BC`, a missing offset uses the session zone | strict regex, then `::timestamptz` |
| `\.datetime\(` · `\.timestamp_tz\(` (SQL/JSON path) | Rejects `t` and more than 6 fraction digits; accepts `+02`, 1-digit fields, surrounding whitespace, `24-01-01…` (year 24), `+002026`; zone-less input becomes session-local | strict regex on the extracted string (`->>`), then `::timestamptz` |
| `to_jsonb?\([^)]*at time zone` | `v AT TIME ZONE 'UTC'` is a `timestamp` without zone: `to_json` prints no offset | `to_json(v)` under `SET TimeZone = 'UTC'`, or the `to_char` form above |
| `set( session\| local)? time ?zone` · `set +datestyle` · `timezone *=` in `postgresql.conf`/connection strings | Every text/JSON output and every zone-less input depends on the session `TimeZone`; LMT eras print offsets with seconds (Monrovia `-00:44:30`, Paris `+00:09:21`, New York year 1 `-04:56:02`) | serialize with `TimeZone = 'UTC'` (gives `+00:00`), or `to_char(v AT TIME ZONE 'UTC', …"Z")` |
| SQLite `(^\|[^.])\bdatetime\(` · `current_timestamp` · `datetime\('now'` | Space separator, no offset (the value is UTC, but readers cannot know) | `strftime('%Y-%m-%dT%H:%M:%fZ', …)` |
| SQLite `'localtime'` together with `Z` in a `strftime` format | Local wall time labelled `Z` (−4 h in the probe) | drop `'localtime'` for anything stored or sent |
| SQLite `datetime\([^)]*\) +is not null` (as a `CHECK` or validator) | Accepts `T24:00`, Feb 30 (→ Mar 1), no seconds, no offset (as UTC), date only, trailing whitespace, NUL-truncated text; rejects `t`, `+15:00`…`+23:59`, `:60` | strict `GLOB`/app-side regex, then `strftime`; also require `date(substr(s,1,10)) = substr(s,1,10)` to catch roll-over (passed 134/147 with the regex and upper-casing `t`) |
| SQLite `%f` on untrusted text | ≥ 309 fraction digits drop the fraction; ≥ 310 make `strftime` print `  null` | cap the length (the strict regex plus a length limit) |

## Top defects (SQL)

1. **PostgreSQL `timestamp` (without time zone) silently discards offsets.** `'…12:00:00+05:30'::timestamp` is
   `12:00:00`; 15 of 70 accepted vectors got a different instant. Nonconformity for any column fed RFC 3339 text.
2. **PostgreSQL text output is not RFC 3339.** `::text`, `||`, and drivers that read text use `2026-09-24 08:00:00-04`
   (space, hour-only offset); `DateStyle` SQL/Postgres/German are not ISO at all. `to_json`/`to_jsonb` is the
   RFC 3339 form (`T`, `±hh:mm`), but it still fails for LMT-era offsets (`-00:44:30`), years > 9999, BC
   (`… BC` suffix) and `infinity`, and never emits `Z`.
3. **Very lenient `timestamptz` input.** 41 TOO LENIENT vectors: `+0200`, `+02`, no seconds, no offset (→
   session zone), date only, basic and ordinal dates, whitespace, `24:00:00`, `:60` at any minute, 5-digit
   years, offset seconds, zone names and abbreviations, and `…Z/P1D` read as +1 h.
4. **Literal-`Z` and wrong-letter `to_char` templates** (`"Z"` without `AT TIME ZONE 'UTC'`, `OF`, `HH`, `MM`,
   `IYYY`) print well-formed but wrong instants, or hour-only offsets. `TZH:TZM` truncates LMT offset seconds
   (Monrovia: −30 s).
5. **`to_timestamp` with `TZH:TZM` is unusable as an RFC 3339 parser**: it rejects `Z` and fractions, ignores
   trailing text and critical `[!…]` suffixes, and turns `''` into `0001-01-01 BC`.
6. **SQLite date functions validate almost nothing and print a non-RFC form by default.** `datetime(s) IS NOT NULL`
   accepts Feb 30 (rolled to Mar 1), `T24:00:00` (echoed as `24:00:00` by `datetime`/`strftime`), no offset
   (taken as UTC), trailing whitespace and NUL-truncated strings; it rejects lower-case `t` and offsets beyond
   ±14:59. `datetime()`/`CURRENT_TIMESTAMP` print `2026-09-26 05:37:43` with no offset. More than 308 fraction
   digits drop the fraction; more than 309 make `strftime('%f')` print `  null`.
7. **Precision.** PostgreSQL rounds to microseconds (half-to-even; `.9999995` becomes the next second) and rejects
   fractions longer than 128 digits; SQL/JSON `.datetime()` rejects more than 6 digits; SQLite truncates to
   milliseconds (`datetime` to seconds).
8. **Leap seconds.** PostgreSQL accepts `:60` at any minute and rolls it to the next second (no §5.7 check) but
   rejects `:60.5`; SQLite and SQL/JSON reject every `:60`.

## Not probed: unverified (from docs)

- MySQL/MariaDB (not re-read or probed here): MySQL `DATETIME`/`TIMESTAMP` accept offsets only since 8.0.19 and discard them
after converting; output is `YYYY-MM-DD hh:mm:ss` (space, no offset). https://dev.mysql.com/doc/refman/8.4/en/date-and-time-literals.html

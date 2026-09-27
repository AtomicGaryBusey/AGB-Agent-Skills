# RFC 3339 / RFC 9557 adherence audit: Tempo timestamp consumers

**Scope:** I audited the consumer role only, in `timeutil.parse_timestamp` (RFC 3339), `timeutil.parse_ixdtf` (IXDTF) and `client/parse.mjs` `parseTimestamp`/`parseSuffix` (IXDTF). I included `api.ingest` where it uses parser output.

**Profiles and grading:**
- `docs/API.md` claims RFC 3339 and RFC 9557 handling. It also declares lower-case `t`/`z` accepted (docs/API.md:43-44), any number of fraction digits accepted (docs/API.md:38-39), unknown elective tags ignored (docs/API.md:49), and first-wins for duplicate keys (docs/API.md:52).
- Neither parser states a leap-second policy, a tz database, or any experimental keys.
- `parse_ixdtf` is the ingest boundary for partner feeds (timeutil.py:3-4, api.py:48-49). So is the web client, whose contract claims the RFCs. That is why accepting invalid input counts as a **Nonconformity** for both.

**Evidence:** Static review only. The scanner, the vectors and the semantic probes were not run because there is no shell. Every input → output pair below comes from reading the code, not from running it.

**Summary:** 15 nonconformities, 1 deviation, 7 advisories, 6 interpretation notes.

Check IDs are written as `section/topic`. The skill's `references/` catalog could not be read (permission denied), so these are not the catalog's own IDs.

## Findings

### Python: `timeutil.py` / `api.py`

| # | Severity | Check | Section | Location | Finding | Evidence (input → output) | Fix |
|---|---|---|---|---|---|---|---|
| P1 | **Nonconformity** (wrong instant) | 3339-5.6/offset-required; 9557-4.1/date-time | 3339 §5.6 (`date-time = full-date "T" full-time`, `full-time` needs `time-offset`); 9557 §4.1 | timeutil.py:25 (offset group is `?`), timeutil.py:107-108, timeutil.py:16; reached from `parse_ixdtf` at timeutil.py:116 | A missing offset is accepted and replaced with `default_tz` or `LOCAL_TZ`. `LOCAL_TZ` is also a fixed offset captured at import, so it is wrong after the next DST change. With an elective zone, `api.ingest` then converts this host-dependent instant into the zone. | `2026-04-02T18:00:00[Europe/Berlin]` → accepted. The instant is 18:00 at the host's import-time offset (for example 16:00Z on a UTC host), not 16:00Z because of Berlin's +02:00. | Make the offset group mandatory and raise when it is missing. Remove `default_tz`/`LOCAL_TZ`, or move them into a separately named lenient API. |
| P2 | **Nonconformity** | 3339-5.6/trailing-garbage (`$` newline) | 3339 §5.6 | timeutil.py:25 (`...)?$` with `re.match`) | Python `$` also matches just before a final `\n`, so a trailing newline is accepted. In `parse_ixdtf` a newline between the time and the suffix is also accepted, and it then breaks the `head[-1]` Z test at timeutil.py:145. | `"2026-03-14T13:30:00Z\n"` → accepted. `"...Z\n[!Europe/London]"` → `offset_known` becomes True and a spurious inconsistency error is raised. | Use `_TS_RE.fullmatch(text)` or end the pattern with `\Z`. |
| P3 | **Nonconformity** (too strict) | 3339-5.7/leap-second | 3339 §5.6 (`time-second = 2DIGIT ; 00-58, 00-59, 00-60`), §5.7 | timeutil.py:103-106 | `datetime(..., 60)` raises, so every leap second is rejected, including real ones. | `1990-12-31T23:59:60Z` → `ValueError: second must be in 0..59`. `1990-12-31T15:59:60-08:00` → the same error. | Check `:60` against the offset-adjusted UTC time (23:59:60 UTC at month end). Map it to a stated value, such as `:59.999999` or the next second, and return a leap flag. |
| P4 | **Nonconformity** (too strict, minor) | 3339-5.6/date-fullyear | 3339 §5.6 (`date-fullyear = 4DIGIT`) | timeutil.py:103-104 | Year `0000` is valid in the grammar, but `datetime` has no year 0, so the parse fails. | `0000-01-01T00:00:00Z` → `ValueError: year 0 is out of range` | Document this as a stated profile restriction (§5.6 NOTE) and raise a clear error. |
| P5 | **Nonconformity** (too lenient, wrong value) | 9557-4.1/time-numoffset suffix; 9557-3.3/critical | 9557 §4.1 (`time-zone = "[" critical-flag (time-zone-name / time-numoffset) "]"`) | timeutil.py:91 (fixed slicing, no length or colon check), timeutil.py:139, timeutil.py:149 | An offset zone in the suffix goes through `_offset()`. That function slices fixed positions and never checks the length or the colon, and the raw string is then returned as `Stamp.zone`. | `...+01:00[!+01:00junk]` → accepted, zone `"+01:00junk"`. `...+01:30[!+0130]` → `text[4:6]="0"` gives offset +01:00, so the call fails with a false "inconsistent" error. `...+01:00[!+0100]` → accepted. `[+ 1:00]` → `int(" 1")` gives +01:00 and the call is accepted. | Validate the suffix with `^[+-](?:[01][0-9]\|2[0-3]):[0-5][0-9]$` before converting it. |
| P6 | **Nonconformity** | 9557-3.3/critical-unprocessable; 9557-3.3/duplicate-critical | 9557 §3.3 (an unknown critical key or value MUST be treated as erroneous; conflicting duplicates where any is critical are erroneous) | timeutil.py:127 (`critical` is computed and then ignored for tags), timeutil.py:133-135 | The critical flag is used only for the zone. `u-ca` values are never checked, and a conflicting critical duplicate is dropped silently by `setdefault`. | `...Z[!u-ca=klingon]` → accepted, calendar `"klingon"`. `...Z[u-ca=chinese][!u-ca=japanese]` → accepted, calendar `"chinese"` (it must be rejected). | Keep `critical` for each tag. Validate `u-ca` against the supported calendars. Reject an unsupported critical value, and reject any duplicate key whose values differ where one copy is critical. |
| P7 | **Nonconformity** (too lenient) | 9557-4.1/suffix-key, suffix-values | 9557 §4.1 (`suffix-key = key-initial *key-char`, `suffix-values = suffix-value *("-" suffix-value)`, `suffix-value = 1*alphanum`) | timeutil.py:27 | `_TAG_RE` accepts any value made of non-bracket characters (spaces, `=`, punctuation) and does not check the key grammar. Only the `KNOWN_SUFFIX_KEYS` gate stops bad keys. | `...Z[u-ca=he brew]` → calendar `"he brew"`. `...Z[u-ca=a=b]` → calendar `"a=b"`. The value is then emitted again by `format_ixdtf`. | Use the ABNF: `\[(!?)([a-z_][a-z0-9_-]*)=([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\]`. `client/parse.mjs:15-16` already has correct regexes. |
| P8 | Advisory | 9557-3.3/elective-unknown | 9557 §3.3 (the recipient is free to ignore an unknown elective key) | timeutil.py:133-134 | Every unknown key is rejected, elective ones included. This removes the elective/critical distinction, and it contradicts the stated contract "Unknown elective tags are ignored" (docs/API.md:49). | `...Z[Europe/Paris][foo=bar]` → `ValueError: unsupported suffix key 'foo'` | Ignore unknown elective keys (after validating their grammar). Reject them only when they are critical. |
| P9 | **Nonconformity** (too strict on valid input) | 9557-4.1/offset-time-zone | 9557 §4.1, §1.2 | api.py:50 | `api.ingest` calls `ZoneInfo(start.zone)` on whatever zone `parse_ixdtf` kept. A valid offset zone therefore raises `ZoneInfoNotFoundError` (a `KeyError`, which escapes `except ValueError` handlers). P5's junk values also reach this line. | `2026-05-04T10:00:00+05:30[+05:30]` → `ZoneInfoNotFoundError` | Have `parse_ixdtf` return the resolved `tzinfo` next to the name, and use that `tzinfo` in `ingest`. |
| P10 | Advisory | 3339-6/precision | 3339 §5.6 (`time-secfrac = "." 1*DIGIT`); docs/API.md:38-39 | timeutil.py:102 | Fraction digits after the sixth are truncated, not rounded, and this is undocumented. | `...T00:00:00.9999999Z` → `.999999` | State microsecond truncation in the contract, or round deliberately. |
| P11 | Advisory | 9557-2/Z-semantics | 9557 §2 (`Z`/`-00:00` means "local offset unknown", `+00:00` means UTC is the preferred reference) | timeutil.py:88-89, timeutil.py:94 (`timezone(-0)` is `timezone.utc`) | `Z`, `-00:00` and `+00:00` all become `timezone.utc`, and `Stamp` has no field that records "offset unknown". | `...Z` and `...+00:00` → identical results | Add `offset_known: bool` to `Stamp` or to the return value of `parse_timestamp`. |
| P12 | Advisory | robustness | — | timeutil.py:140, timeutil.py:147 | Only `ZoneInfoNotFoundError`/`ValueError` are caught, so `astimezone` near year 1 or year 9999 raises `OverflowError`. | `0001-01-01T00:00:00+00:00[!America/New_York]` → `OverflowError` rather than `ValueError` | Catch `OverflowError` and treat it as an out-of-range zone evaluation (a critical zone becomes an error). |

### Web client: `client/parse.mjs`

| # | Severity | Check | Section | Location | Finding | Evidence (input → output) | Fix |
|---|---|---|---|---|---|---|---|
| J1 | **Nonconformity** (too lenient, wrong value) | 3339-5.6/unanchored-regex | 3339 §5.6 | client/parse.mjs:13 (no `^`) | `STAMP_RE` is anchored only at the end, so leading text is skipped. | `x2026-03-14T09:30:00Z` → accepted. `12026-03-14T09:30:00Z` → accepted as year 2026. | Use `new RegExp('^' + DATE + ...)`. |
| J2 | **Nonconformity** (too strict) | 3339-5.6/case-insensitive | 3339 §5.6 NOTE ("T" and "Z" may be lower case); docs/API.md:43-44 | client/parse.mjs:10 (`'T(...'`), :11 (`Z\|`), :20, :89 | Lower-case `t` and `z` are rejected, which contradicts the documented contract. | `1985-04-12t23:20:50.52z` → `RangeError: invalid timestamp` | Use `[Tt]` and `[Zz]`, and compare the offset case-insensitively at :20 and :89. |
| J3 | **Nonconformity** (too lenient, wrong instant) | 3339-5.7/day-of-month | 3339 §5.7 (date-mday ranges by month and year) | client/parse.mjs:17, :68, :77 | Every month is checked against a limit of 31, and `Date.UTC` rolls overflow into the next month. | `2023-02-30T10:00:00Z` → accepted, `iso: "2023-03-02T10:00:00.000Z"`. `2023-04-31T00:00:00Z` → May 1. | Check against the month length, with leap years handled per App. C. |
| J4 | **Nonconformity** (wrong instant) | 3339-5.6/year-0-99 | 3339 §5.6 (`date-fullyear = 4DIGIT`) | client/parse.mjs:77 | `Date.UTC` maps years 0–99 to 1900–1999. | `0050-06-01T00:00:00Z` → `iso: "1950-06-01T00:00:00.000Z"` | Build the date with `new Date(0); d.setUTCFullYear(year, month-1, day); d.setUTCHours(...)`, or use `Temporal.PlainDateTime`. |
| J5 | **Nonconformity** (too lenient) | 3339-5.7/leap-second-position | 3339 §5.7 (`:60` only at the end of a leap-second month, in offset-adjusted UTC) | client/parse.mjs:71, :77, :99 | `second === 60` is accepted at any date and time. Mapping it to `:59` with a `leapSecond` flag is a reasonable stated mapping. The missing validation is the problem. | `2026-03-14T09:30:60Z` → accepted with `leapSecond: true`. `2016-12-31T23:59:60+01:00` → accepted (that is 22:59:60 UTC). | When `second === 60`, require the offset-adjusted UTC time to be 23:59 on the last day of a month (optionally only Mar/Jun/Sep/Dec, per App. D). |
| J6 | **Nonconformity** | 9557-3.3/critical-unprocessable | 9557 §3.3 (an unknown critical key or value MUST be treated as erroneous) | client/parse.mjs:33-34 (`critical` computed), :50-51 (used only for the zone) | Unknown critical keys are skipped by `continue`, and `u-ca` values are never checked. | `...Z[!foo=bar]` → accepted. `...Z[!u-ca=klingon]` → accepted, `calendar: "klingon"`. | When `critical` is set, throw for keys outside `KNOWN_KEYS` and for unsupported `u-ca` values. |
| J7 | **Nonconformity** (wrong effective tags) | 9557-3.3/duplicate-keys | 9557 §3.3 (first occurrence wins; conflicting duplicates with any critical copy are erroneous); docs/API.md:52 | client/parse.mjs:51 | `out.tags[key] = value` makes the last copy win, and critical conflicts are not detected. | `2022-07-08T00:14:07Z[Europe/Paris][u-ca=chinese][u-ca=japanese]` → `calendar: "japanese"` (expected `"chinese"`). `...[u-ca=chinese][!u-ca=japanese]` → accepted. | `if (key in out.tags) { if ((critical \|\| seenCritical[key]) && out.tags[key] !== value) throw ...; continue; }`. |
| J8 | Advisory | 3339-6/precision | docs/API.md:38-39 | client/parse.mjs:76 | Any number of fraction digits is accepted, but `epochMs` truncates to milliseconds. Nothing in the result says so. | `...T00:00:00.123456789Z` → `epochMs` ends in `.123` | Document millisecond resolution, or also return the full fraction (for example as `Temporal.Instant`). |
| J9 | Advisory | 9557-3.3/tzdata-availability | 9557 §3.3 | client/parse.mjs:57-59, :83-88 | This file is a web client, and it depends on a global `Temporal`. Where `Temporal` is missing, the `ReferenceError` is caught as "unknown zone". Critical zones are then always rejected, which conforms, but elective zones are silently set to `null`. | In a browser without `Temporal`: `...-04:00[America/New_York]` → `timeZone: null` | Feature-detect `Temporal` and surface "tz unavailable" separately, or ship a polyfill. |
| J10 | Advisory | 9557-2/Z-semantics | 9557 §2 | client/parse.mjs:20, :98 | `Z`, `-00:00` and `+00:00` all return `offsetMinutes: 0` (or `-0`), and nothing in the result says "offset unknown". | `...Z` and `...+00:00` → the same `offsetMinutes` | Return `offsetKnown` (already computed at :89). |

### Contract and docs

| # | Severity | Check | Section | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|
| D1 | Deviation | contract/iso8601-claim | 3339 §5.6; rule "Docs promise ISO 8601 but mean RFC 3339" | docs/API.md:19-21 | Clients are told to "accept any ISO 8601 representation", including the compact form `20260314T133000Z`. That form is not RFC 3339, and neither parser accepts it. The same document's case and duplicate-key promises are also broken by J2, J7 and P8. | `20260314T133000Z` → rejected by timeutil.py:25 and parse.mjs:13 | Replace this with "RFC 3339 `date-time`; `start` is RFC 9557 IXDTF" and remove the compact example. |

## Interpretation notes (readings used, not graded)

1. **RFC 9557 §4.1 `time-zone` ABNF precedence:** I read it as `"[" critical-flag (time-zone-name / time-numoffset) "]"`. P5 uses this reading.
2. **Elective zone inconsistent with the offset (MAY act):** Both parsers accept it. In Python, `api.ingest` (api.py:54) keeps the instant and moves it into the named zone. Both choices are allowed.
3. **Unknown elective zone name:** Python (timeutil.py:143) and JS (parse.mjs:87) both drop it silently. The RFC permits this.
4. **`Z` / `-00:00` with a critical zone:** Both treat this as consistent (timeutil.py:145, parse.mjs:89), which matches §3.4. The Python test at tests/test_timeutil.py:60-62 covers it. The `Z[+hh:mm]` case is implementation-defined, and both parsers accept it.
5. **Critical zones with sub-minute historical offsets** (LMT, for example `Africa/Monrovia` before 1972): a `time-numoffset` cannot carry seconds, so both parsers (timeutil.py:147 compares `timedelta` with seconds; parse.mjs:59 produces fractional minutes) always find an inconsistency and reject. That is a defensible way to act on a critical inconsistency. I record it as the chosen policy.
6. **Zone-name case:** Python `ZoneInfo` depends on the filesystem. On case-insensitive macOS, `europe/paris` resolves and keeps the non-canonical key. Temporal canonicalizes case-insensitively. Both behaviours are implementation-defined.

Experimental `[_key=…]` tags: both parsers reject them. No experiments are configured, so this conforms. It is by accident in Python, which rejects every unknown key, and explicit in JS at parse.mjs:49.

## Not run / not applicable

- **Not run: `rfcdt.py scan`, the `run_vectors.py` conformance vectors (274), and the semantic probes.** There is no shell in this environment. None of the vector groups (TOO LENIENT, TOO STRICT, WRONG VALUE) are verified, and there may be other defects that only the vectors would find. The next step is to run the adapters sketched below.
- **Check catalog:** I could not read `references/check-index.md` (permission denied), so the check IDs above are section-based labels.
- **Producers and schema:** out of scope, so not graded. Things I noticed while reading, for a follow-up audit:
  - `format_offset` uses `%z` and so emits `+0200` with no colon (timeutil.py:13, :56).
  - `format_utc` puts `Z` on non-UTC wall time (timeutil.py:51).
  - `format_reminder` drops the seconds (timeutil.py:61; the test at tests/test_timeutil.py:32 locks in `09:15-04:00`).
  - `format_ixdtf` emits `[UTC+05:30]` for fixed-offset `tzinfo` (timeutil.py:70).
  - `created_at` is naive, so no offset is emitted (api.py:25, :36).
  - `format_epoch` emits `+00:00` for a timestamp whose local offset is unknown (timeutil.py:66).
  - `all_day_date` is declared `format: date-time` but holds a date (schema/event.schema.json:50).
  - The CI "guarantee" at docs/API.md:13-15 is not backed by a configured format assertion.

## Reproduction (to run once a shell is available)

Python adapter (`adapter.py`):
```python
import json, os, sys; sys.path.insert(0, ".")
import timeutil
s = sys.stdin.read()
try:
    if os.environ.get("RFCDT_PROFILE") == "ixdtf":
        st = timeutil.parse_ixdtf(s); f = {"effective_tags": {"u-ca": st.calendar} if st.calendar else {}}
        dt = st.instant
    else:
        dt = timeutil.parse_timestamp(s); f = {}
    f.update(year=dt.year, offset_minutes=int(dt.utcoffset().total_seconds() // 60))
    print(json.dumps({"ok": True, "fields": f}))
except Exception:
    print(json.dumps({"ok": False}))
```
```
python3 scripts/run_vectors.py --target "python3 adapter.py" --target-has-tzdata yes --target-kind both --target-options fixed --json
```

Node adapter (`adapter.mjs`, Node 26 with Temporal):
```js
import { parseTimestamp } from './client/parse.mjs';
let s = ''; for await (const c of process.stdin) s += c;
try { const r = parseTimestamp(s);
  console.log(JSON.stringify({ ok: true, fields: { year: new Date(r.epochMs).getUTCFullYear(), offset_minutes: r.offsetMinutes, effective_tags: r.tags } }));
} catch { console.log(JSON.stringify({ ok: false })); }
```
```
python3 scripts/run_vectors.py --target "node adapter.mjs" --target-has-tzdata yes --target-kind ixdtf --target-options fixed --json
```

Library versions and tzdata version were not collected, because nothing was executed.

# RFC 3339 / RFC 9557 audit: Tempo timestamp consumers

**Scope:** I audited the consumers only: `timeutil.parse_timestamp`, `timeutil.parse_ixdtf` and the ingest code that calls them (`api.py:46-58`), plus `client/parse.mjs` (`parseTimestamp`, `parseSuffix`). Both parsers accept the IXDTF profile, which also covers plain RFC 3339. The only options the project declares are in `docs/API.md`: accept lower-case `t`/`z` (`:43-44`), accept any number of fractional digits (`:38-39`), ignore unknown elective tags, reject unprocessable critical tags, and let the first repeated key win (`:48-54`). No leap-second policy, no production restriction and no experimental keys are declared.

**How this was checked:** I only read the code; nothing was run. There was no shell, so the static scan and the conformance vectors were not run, there are no pass counts, and every input → output pair below comes from reading the code. The Reproduction section has adapters to confirm them.

**Summary:** 15 nonconformities, 1 deviation, 7 advisories, 6 interpretation notes.

## Findings

### Python: `timeutil.py` and `api.py`

| # | Severity | Section | Location | Finding | Input → output (traced) | Fix |
|---|---|---|---|---|---|---|
| P1 | **Nonconformity** | 3339 §5.6 (`time-offset` is required), §4.4 | `timeutil.py:25`, `timeutil.py:107-108`, `timeutil.py:16`; reached through `timeutil.py:116` | The offset is optional (`)?$`). A string with no offset is read as host-local time. `LOCAL_TZ` is a fixed offset captured when the module is imported, not a zone, so it is also wrong across DST changes. The partner-feed ingest path is a gate for untrusted input, so this is a Nonconformity. Through `parse_ixdtf`, the critical-zone check at `:145-148` then compares against the host's offset, so whether input is accepted depends on the host. | `2026-04-02T18:00:00` → accepted with the host offset (+00:00 on a UTC host). `2026-04-02T18:00:00[!Europe/Berlin]` → rejected on a UTC host, accepted on a +02:00 host. | Make the offset group mandatory. Remove `default_tz`/`LOCAL_TZ` from the RFC parser. |
| P2 | **Nonconformity** | 3339 §5.6 grammar | `timeutil.py:25`, `timeutil.py:99` | `re.match` with `$` also matches just before a trailing `\n`. | `2026-04-02T18:00:00Z\n` → accepted. `2026-04-02T18:00:00+02:00\n[Europe/Berlin]` → accepted: the head ends in `\n` and the suffix still parses. | Use `_TS_RE.fullmatch(text)`, or end the pattern with `\Z`. |
| P3 | **Nonconformity** (too strict) | 3339 §5.6 (`time-second` 00-60, `date-fullyear` 4DIGIT), §5.7 | `timeutil.py:103-106` | Python's `datetime` cannot hold second 60 or year 0, so every leap second and year `0000` is rejected. No profile restriction is stated. | `1990-12-31T23:59:60Z` → `ValueError`. `1990-12-31T15:59:60-08:00` → `ValueError`. `0000-01-01T00:00:00Z` → `ValueError`. | Accept `:60` only when the offset-adjusted UTC time is 23:59:60 on a valid leap-second date. Then either map it to :59.999999 and set a leap flag, or document "leap seconds and year 0 are not supported" as the profile. |
| P4 | **Nonconformity** | 9557 §4.1 (`time-numoffset` in `time-zone`); 9557 §3.3 when critical | `timeutil.py:91`, `timeutil.py:139` | The offset-zone suffix is read by slicing `[1:3]`/`[4:6]` with no length or format check. Python's `int()` also accepts spaces and non-ASCII digits. Junk after the offset, or a malformed offset, is accepted even when the suffix is critical. | `…+01:00[!+01:00junk]` → accepted with zone `+01:00junk`. `[+01-30]` → +01:30. `[+01:3]` → +01:03. `[+ 1:00]` and `[+٠١:00]` → +01:00. | Before calling `_offset` on a suffix, check it with `re.fullmatch(r"[+-][0-9]{2}:[0-9]{2}", zone)`. |
| P5 | **Nonconformity** | 9557 §4.1 (`suffix-value = 3*8alphanum`, `suffix-values`) | `timeutil.py:27`, `timeutil.py:135` | The tag value is `[^\[\]]+`, so it can contain anything except brackets. Spaces, `=`, `!`, newlines and values that are too short or too long all pass. The key is only checked by the allow-list. | `…Z[u-ca=hebrew junk]` → `calendar="hebrew junk"`. `…Z[u-ca=x]` → accepted. | Match keys with `[a-z_][a-z0-9_-]*` and values with `[A-Za-z0-9]{3,8}(-[A-Za-z0-9]{3,8})*`. |
| P6 | **Nonconformity** | 9557 §3.3 (a critical tag that cannot be processed MUST be treated as erroneous; conflicting duplicates where one is critical are erroneous) | `timeutil.py:127`, `timeutil.py:133-135` | `crit` is parsed but never used for key=value tags. Any value of the known key `u-ca` is accepted even when critical, and a critical duplicate that conflicts is dropped without an error. | `…Z[!u-ca=klingon]` → accepted, `calendar="klingon"`. `…Z[u-ca=chinese][!u-ca=japanese]` → accepted, `calendar="chinese"`. | Check `u-ca` values against the supported calendar IDs and raise when the tag is critical. Track the critical flag per key and raise when copies conflict and any of them is critical. |
| P7 | Advisory | 9557 §3.3 (unknown elective tag: free to ignore) | `timeutil.py:133-134` | Every unknown key raises, elective ones included. This removes the elective/critical distinction and contradicts `docs/API.md:49` (see D1). | `…Z[Europe/Paris][foo=bar]` → `ValueError: unsupported suffix key 'foo'` | Ignore unknown elective keys. Raise only for unknown critical keys and `_`-prefixed keys. |
| P8 | **Nonconformity** (too strict) | 9557 §1.2, §4.1 (offset time zones are valid) | `api.py:50` | `parse_ixdtf` accepts `[+02:00]` and returns `zone="+02:00"`. `ingest` then calls `ZoneInfo("+02:00")`, which raises `ZoneInfoNotFoundError`, and nothing catches it. A valid partner record crashes ingest. | `{"start": "2026-04-02T18:00:00+02:00[+02:00]", …}` → uncaught `ZoneInfoNotFoundError` | Have `Stamp` carry the resolved `tzinfo` (the `tz` already built at `timeutil.py:139`) instead of the raw name. |
| P9 | Advisory | 9557 §2 (`Z`/`-00:00` means UTC known, local offset unknown; `+00:00` means UTC preferred) | `timeutil.py:88-89`, `timeutil.py:149`, `api.py:50,54` | `Z`, `z`, `+00:00` and `-00:00` all become `timezone.utc`, and `Stamp` does not keep which one was used. Only the check at `:145` sees the difference. On ingest, a `Z` feed with no zone is re-emitted as a known UTC offset. | `2026-04-02T16:00:00Z` and `…+00:00` → identical `Stamp` | Add a field such as `offset_known: bool` to `Stamp` and keep it on round-trip. |
| P10 | Advisory | 3339 §5.6 (`time-secfrac` has no digit limit) | `timeutil.py:102` | Fractional seconds are cut to 6 digits by truncation. That is fine, but the limit is not documented, and `docs/API.md:38-39` suggests any precision is handled. | `…:00.1234569Z` → `microsecond=123456` | Document the microsecond limit. |

### Web client: `client/parse.mjs`

| # | Severity | Section | Location | Finding | Input → output (traced) | Fix |
|---|---|---|---|---|---|---|
| J1 | **Nonconformity** (gives the wrong instant) | 3339 §5.6 grammar, §5.1 | `client/parse.mjs:13`, `client/parse.mjs:63` | `STAMP_RE` has `$` but no `^`, so `exec` matches anywhere in the string. Leading junk is ignored, and a 5-digit year is silently cut to its last 4 digits. | `12026-03-14T09:30:00Z` → accepted as 2026-03-14T09:30:00Z. `junk2026-03-14T09:30:00Z` and `-2026-…Z` → accepted. | Start the pattern with `'^'`. |
| J2 | **Nonconformity** (too strict) | 3339 §5.6 NOTE, §2 (ABNF strings are case-insensitive) | `client/parse.mjs:10`, `client/parse.mjs:11`, `client/parse.mjs:20`, `client/parse.mjs:89` | Only upper-case `T` and `Z` are accepted, which contradicts `docs/API.md:43-44`. The `off === 'Z'` checks at `:20`/`:89` would also have to handle `z`. | `1985-04-12t23:20:50.52z` → `RangeError: invalid timestamp` | Use `[Tt]` and `[Zz]`, and normalise `off` to upper case before `:20`/`:89`. |
| J3 | **Nonconformity** (gives the wrong instant) | 3339 §5.7 (day must be valid for the month and year) | `client/parse.mjs:17`, `client/parse.mjs:68`, `client/parse.mjs:77` | Every month is allowed 31 days, and `Date.UTC` rolls overflow into the next month. | `2023-02-30T10:00:00Z` → accepted, `iso` = `2023-03-02T10:00:00.000Z`. `2023-02-29T…Z` → March 1. `2026-04-31T…Z` → May 1. | Check the day against the month length, with leap-year Februaries (Appendix C). |
| J4 | **Nonconformity** (gives the wrong instant) | 3339 §5.6 (`date-fullyear` 4DIGIT) | `client/parse.mjs:77` | `Date.UTC` maps years 0-99 to 1900-1999. | `0050-01-01T00:00:00Z` → `iso` = `1950-01-01T00:00:00.000Z` | Build the date with `new Date(0)` and `setUTCFullYear(year, month-1, day)`, or use `Temporal.PlainDateTime`. |
| J5 | **Nonconformity** | 3339 §5.7 (`:60` only at a leap second, checked against the offset-adjusted UTC time), App. D | `client/parse.mjs:71`, `client/parse.mjs:77`, `client/parse.mjs:99` | `second <= 60` is accepted at any hour, minute or date and then clamped to :59, so an invalid leap second silently becomes a real instant. For a valid leap second, `23:59:60.5` becomes the same `epochMs` as `23:59:59.5`. | `2026-03-14T09:30:60Z` → accepted, `leapSecond: true`, instant 09:30:59Z. | Accept `:60` only when the UTC-adjusted time is 23:59:60 at the end of a leap-second month (the policy is yours to choose; see the notes below). |
| J6 | **Nonconformity** | 9557 §3.3 (an unknown critical key or value MUST be treated as erroneous) | `client/parse.mjs:33-34`, `client/parse.mjs:50` | `critical` is computed and then ignored for key=value tags. Unknown critical keys are skipped by `continue`, and unknown critical `u-ca` values are accepted. This contradicts `docs/API.md:50-51`. | `2026-03-14T13:30:00Z[!foo=bar]` → accepted, `tags: {}`. `…Z[!u-ca=klingon]` → `calendar: "klingon"`. | `if (!KNOWN_KEYS.has(key)) { if (critical) throw …; continue; }`, and validate `u-ca` values, for example with `Intl.supportedValuesOf('calendar')`. |
| J7 | **Nonconformity** (gives the wrong value) | 9557 §3.3 (a repeated elective key: MUST use the first; conflicting critical copies are erroneous) | `client/parse.mjs:51` | `out.tags[key] = value` means the last copy wins. This contradicts `docs/API.md:52` and the Python behaviour pinned by `tests/test_timeutil.py:50-54`. | `2022-07-08T00:14:07Z[Europe/Paris][u-ca=chinese][u-ca=japanese]` → `calendar: "japanese"` (should be `chinese`) | Skip a key already in `out.tags`, and throw when copies conflict and any of them is critical. |
| J8 | **Nonconformity** | 9557 §4.1 (`suffix-value = 3*8alphanum`; `time-zone` needs a name or offset) | `client/parse.mjs:16`, `client/parse.mjs:37-41`, `client/parse.mjs:81` | `VALUES_RE` allows value parts of 1 character or more than 8. An empty critical zone `[!]` gives `timeZone = ""`, which is falsy, so it skips the zone branch at `:81` and is accepted. | `…Z[u-ca=a]` → accepted. `…Z[!]` → accepted, `timeZone: ""`. | Use `/^[A-Za-z0-9]{3,8}(?:-[A-Za-z0-9]{3,8})*$/`, and reject an empty zone body. |
| J9 | Advisory | 9557 §3.3 | `client/parse.mjs:57-58`, `client/parse.mjs:83-88` | Any exception counts as "unknown zone", including `ReferenceError` when a browser has no global `Temporal`. On those browsers every elective zone is silently dropped, and every critical zone is rejected as "unknown". That outcome is conformant, but it is accidental and the error message is misleading. | Runtime without Temporal: `…-04:00[America/New_York]` → `timeZone: null` | Check `typeof Temporal` once, and catch only `RangeError`. |
| J10 | Advisory | 9557 §2 | `client/parse.mjs:20`, `client/parse.mjs:98` | `Z` and `+00:00` both give `offsetMinutes: 0` (`-00:00` gives `-0`, which is hard to see). Callers cannot tell "local offset unknown" apart from "UTC preferred". | `…Z` and `…+00:00` → same result | Return a field such as `offsetKnown`. |
| J11 | Advisory | 3339 §5.6 | `client/parse.mjs:76` | Fractional seconds are truncated to milliseconds. The limit is not documented. | `…:00.1239Z` → 123 ms | Document it, or keep the full fraction. |
| J12 | Advisory | 3339 §5.6 (derived output) | `client/parse.mjs:97` | The `iso` field comes from `toISOString()`, which writes an expanded year once the UTC instant is past 9999, so the field is not RFC 3339. | `9999-12-31T23:30:00-01:00` → `iso: "+010000-01-01T00:30:00.000Z"` | Leave `iso` out, or mark it as not RFC 3339 for years outside 0000-9999. |

### Contract and documentation

| # | Severity | Section | Location | Finding | Fix |
|---|---|---|---|---|---|
| D1 | Deviation (the docs make false claims) | 3339 §5.6; 9557 §3.3 | `docs/API.md:19-21`, `:43-44`, `:49`, `:50-51`, `:52` | The documented contract does not match either parser. `:19-21` says clients accept "any ISO 8601 representation", including `20260314T133000Z`, but both parsers reject the basic format (`timeutil.py:20-26`, `client/parse.mjs:9-13`), and RFC 3339 does not allow it. The other claims fail as recorded above: lower case (J2), elective tags ignored (P7), critical tags invalid (P6, J6), first occurrence wins (J7). | State the contract as "RFC 3339 `date-time`; `start` is RFC 9557", remove the basic-format example, and fix the parsers to match the suffix rules. |

### What the parsers already get right

These points were checked and are not findings:
- **Python:**
  - Invalid calendar dates and `T24:00` are rejected by the `datetime` constructor (`tests/test_timeutil.py:46-48`).
  - Offset hours and minutes are range-checked (`timeutil.py:92`).
  - `[0-9]` is ASCII-only.
  - The first elective duplicate wins (`:135`).
  - A critical zone that disagrees with the offset is rejected, and `Z`/`-00:00` are exempt (`:145-148`).
  - The time zone must come first (`:129-130`).
  - `_` experimental keys are rejected, via the allow-list.
- **JS:**
  - The offset is required.
  - `$` without the `m` flag does not match before `\n`.
  - `\d` is ASCII-only in ECMAScript.
  - The key grammar is checked (`:15`), and `_` keys are rejected (`:49`).
  - The zone must come first (`:38`).
  - The critical-zone consistency check has the correct `Z`/`-00:00` exemption (`:89-91`).
  - Hour, minute and offset ranges are checked.

## Interpretation notes (ambiguous RFC text; these choices are not graded)

1. **Elective zone that disagrees with the offset:** neither parser acts on it (`timeutil.py:146`, `client/parse.mjs:90`). RFC 9557 §3.4 says the consumer MAY act, so both are acceptable. `api.py:50,54` then effectively lets the offset/instant win and shows the result in the zone.
2. **`Z[+08:45]` / `Z[!+08:45]`:** both parsers accept it, because `Z` means the offset is not asserted. This behaviour is implementation-defined (§1.2 compared with §3.4).
3. **Unknown elective zone name:** both parsers drop it silently (`timeutil.py:143`, `client/parse.mjs:87`). This is allowed.
4. **Zone-name case:** Temporal matches names case-insensitively. `ZoneInfo` may load `europe/paris` on a case-insensitive filesystem such as default macOS APFS. I have not verified either here.
5. **Leap-second policy:** Python has none because it rejects all (P3), and JS has none because it accepts all (J5). Both are findings only because they reject clearly valid input or accept clearly invalid input. Which leap-second months count as valid is your choice.
6. **RFC 9557 §4.1 `time-zone` ABNF:** I read it as `"[" critical-flag (time-zone-name / time-numoffset) "]"`.

## Not run / out of scope

- **Not run:** the `rfcdt.py scan`, `run_vectors.py`, and executed semantic probes. No shell was available, so every input → output above is traced by reading the code, not executed. I am not claiming vector pass rates.
- **Producers and schema were out of scope,** but I saw problems in passing that are worth their own audit. Each item below is also traced statically, not run:
  - `format_offset` uses `%z`, which gives `-0400` with no colon (`timeutil.py:13,56`).
  - `format_utc` labels non-UTC wall time as `Z`, which is the wrong instant (`timeutil.py:51`).
  - `format_reminder` drops the seconds (`timeutil.py:61`; `tests/test_timeutil.py:32` asserts the invalid output).
  - `created_at` is naive (`api.py:25,36`).
  - `format_epoch` emits `+00:00` where `Z` is meant (`timeutil.py:66`).
  - `format_ixdtf` emits `[UTC+05:30]` for a fixed-offset `tzinfo` (`timeutil.py:70,77`).
  - The schema has `all_day_date` as `format: date-time` although it holds a date (`schema/event.schema.json:50`), and the `start` pattern `\[.+\]` is too loose (`:21`).
  - Nothing enforces `format`, even though `docs/API.md:13-15` says CI does.

## Reproduction (to confirm these traces)

Python adapter (`adapter_py.py`):
```python
import json, os, sys; sys.path.insert(0, ".")
import timeutil
s = sys.stdin.read()
try:
    if os.environ.get("RFCDT_PROFILE") == "ixdtf":
        st = timeutil.parse_ixdtf(s); dt = st.instant
        f = {"effective_tags": {"u-ca": st.calendar} if st.calendar else {}}
    else:
        dt = timeutil.parse_timestamp(s); f = {}
    off = dt.utcoffset()
    f.update(year=dt.year, offset_minutes=None if off is None else int(off.total_seconds() // 60))
    print(json.dumps({"ok": True, "fields": f}))
except Exception:
    print(json.dumps({"ok": False}))
```
Node adapter (`adapter.mjs`):
```js
import { parseTimestamp } from './client/parse.mjs';
let s = ''; for await (const c of process.stdin) s += c;
try { const r = parseTimestamp(s);
  console.log(JSON.stringify({ ok: true, fields: { year: new Date(r.epochMs).getUTCFullYear(),
    offset_minutes: r.offsetMinutes, effective_tags: r.tags } }));
} catch { console.log(JSON.stringify({ ok: false })); }
```
Commands:
```
python3 ~/.claude/skills/rfc3339-ixdtf/scripts/run_vectors.py --target "python3 adapter_py.py" --target-has-tzdata yes --target-kind both --target-options fixed
python3 ~/.claude/skills/rfc3339-ixdtf/scripts/run_vectors.py --target "node adapter.mjs" --target-has-tzdata yes --target-kind both --target-options fixed
python3 ~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py scan timeutil.py api.py client/ schema/
```
Versions assumed: Python 3.13 with the system or `tzdata` zone data; Node 26 with global `Temporal` and ICU tzdata. Neither was checked in this session.

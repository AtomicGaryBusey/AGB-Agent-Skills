# Answer key: rfc-target (Tempo event scheduling service)

Target: `scratchpad/rfc-target/`. Paths below are relative to that folder.
Seeded defects: 18 (producer 6, consumer 9, schema/docs 3). Decoys: 3.
The sample output is from `python3 api.py` (see the `events` array). The "Contract" column shows where `docs/API.md` states the intended behavior, when it does.

Expected severity follows the SKILL.md rule 1 mapping (MUST/grammar, well-formed-but-wrong instant, too-lenient validator or too-strict parser = Nonconformity; SHOULD or false contract/docs claim = Deviation; MAY/informative = Advisory; ambiguous text = Interpretation note, graded as "Review"). "alt" names a severity that a reasonable auditor may also assign; graders accept either. Decoys expect no finding.

## Producer defects (Python)

| ID | Location | RFC section | Level | Expected severity | Input → wrong output (expected) |
|---|---|---|---|---|---|
| P1 | `timeutil.py:51` (`format_utc`), used at `api.py:33` | RFC 3339 §4.1, §5.6 (`time-offset = "Z"` means UTC) | Semantic: wrong instant | Nonconformity | `datetime(2026,3,14,9,30,tzinfo=America/New_York)` → `"2026-03-14T09:30:00Z"`. The literal `Z` is put on local wall time with no `astimezone(utc)`. Expected: `"2026-03-14T13:30:00Z"`. The value is 4 h off, and 5.5 h off for evt_0002. Contract: API.md:26 says "same instant as start, in UTC". |
| P2 | `timeutil.py:13` (`RFC3339_FMT` uses `%z`), `timeutil.py:56`, used at `api.py:34` | RFC 3339 §5.6 `time-numoffset = ("+"/"-") time-hour ":" time-minute` | Grammar | Nonconformity | end `11:00 America/New_York` → `"2026-03-14T11:00:00-0400"`. There is no colon. Expected: `"...-04:00"` (use `isoformat()` or `%:z`). |
| P3 | `api.py:36` (naive `created_at.isoformat`), source at `api.py:25` (`default_factory=datetime.now`) | RFC 3339 §5.6 (`full-time = partial-time time-offset`, offset required) and §4.4 (unqualified local time is "deemed unacceptable"; MUST sync with UTC) | Grammar + MUST (§4.4) | Nonconformity | `datetime.now()` → `"2026-09-24T23:13:18"`. There is no offset. Expected: `"2026-09-25T06:13:18Z"` or a value with a numeric offset. |
| P4 | `timeutil.py:14` (`REMINDER_FMT` has no `:%S`), `timeutil.py:61`, used at `api.py:35` | RFC 3339 §5.6 (`partial-time = time-hour ":" time-minute ":" time-second`) | Grammar | Nonconformity | start 09:30-04:00 minus 15 min → `"2026-03-14T09:15-04:00"`. Expected: `"2026-03-14T09:15:00-04:00"`. The dev test `tests/test_timeutil.py:32` asserts the wrong value. |
| P5 | `timeutil.py:66` (`format_epoch` → `isoformat()` gives `+00:00`), used at `api.py:42` | RFC 9557 §2.2 and §2.3 (updates RFC 3339 §4.3: when the local offset is unknown, use `Z`; `+00:00` means "UTC is the preferred reference point") | lower-case "should" / semantic (RFC 9557 §2.2 "can be represented") | Advisory (Deviation also accepted) | `seen=1774540800` (bare POSIX time, local offset unknown per API.md:32) → `"2026-03-26T16:00:00+00:00"`. Expected: `"2026-03-26T16:00:00Z"`. |
| P6 | `timeutil.py:70` (`zone_label` falls back to `str(tz)`), used at `timeutil.py:77` / `api.py:32` | RFC 9557 §4.1 (`time-zone-char` excludes `:`; the bracket holds an IANA `time-zone-name` or a `time-numoffset`) | Grammar | Nonconformity | `timezone(timedelta(hours=5, minutes=30))` → `"2026-05-04T10:00:00+05:30[UTC+05:30]"`. `UTC+05:30` is neither a valid time-zone-name (it has `:`) nor a time-numoffset. Expected: `[+05:30]`, or no zone suffix. Contract: API.md:25 promises `[Area/City]`. |

## Consumer defects

| ID | Location | RFC section | Level | Expected severity | Input → wrong output (expected) |
|---|---|---|---|---|---|
| C1 | `timeutil.py:25` (the pattern ends in `$` and is used with `re.match` at `:99`) | RFC 3339 §5.6 grammar (the whole string must be a `date-time`) | Grammar (lenient acceptance) | Nonconformity | `"2026-03-14T09:30:00Z\n"` → accepted as `2026-03-14 09:30:00+00:00`. Expected: reject. The fix is `re.fullmatch` or `\Z`. |
| C2 | `timeutil.py:103-106` (`datetime(...)` with `second=60`) | RFC 3339 §5.6 (`time-second` 00-60), §5.7, §5.8 example `1990-12-31T23:59:60Z` | Grammar (rejects a valid value) | Nonconformity | `"1990-12-31T23:59:60Z"` → `ValueError: second must be in 0..59`. Expected: accept, for example by mapping to :59 or keeping a leap flag. |
| C3 | `timeutil.py:25` (offset group made optional with `?`) and `timeutil.py:107-108` (fills in `LOCAL_TZ`) | RFC 3339 §5.6 (`time-offset` required), §4.4 | Grammar + MUST (§4.4) | Nonconformity | `"2026-03-14T09:30:00"` → accepted silently as `09:30:00-07:00`, using the host's zone. Expected: reject. |
| C4 | `timeutil.py:133-134` (raises on any key not in `KNOWN_SUFFIX_KEYS`, even without `!`) | RFC 9557 §3.3 (suffix tags are elective by default; the recipient is free to ignore them; "an unknown suffix may be entirely ignored") | Elective semantics (the RFC permits extra processing, so this is not a hard MUST violation). It breaks the stated contract at API.md:49. | Deviation (alt: Advisory) | `"2022-07-08T00:14:07+01:00[knort=blargel]"` → `ValueError: unsupported suffix key 'knort'`. Expected: parse and ignore the tag. Critical `[!knort=…]` is rejected correctly. |
| C5 | `client/parse.mjs:13` (`new RegExp(... + '$')` has no `^`) | RFC 3339 §5.6 grammar | Grammar (lenient acceptance) | Nonconformity | `"junk2026-03-14T09:30:00Z"` → accepted, `iso 2026-03-14T09:30:00.000Z`. Expected: reject. |
| C6 | `client/parse.mjs:10` (`'T'`), `client/parse.mjs:11` (`'Z'`), and the regex has no `i` flag | RFC 3339 §5.6 NOTE (ABNF literals are case-insensitive; `t` and `z` are allowed. Only an explicit spec restriction may forbid them, and API.md:43-44 says parsers accept them) | Grammar / NOTE | Nonconformity | `"2026-03-14t09:30:00z"` → `invalid timestamp`. Expected: accept. |
| C7 | `client/parse.mjs:17` (`MAX_MDAY = 31`), `:68` range check, `:77` `Date.UTC` rolls over | RFC 3339 §5.7 (maximum `date-mday` depends on the month and year) | Grammar restriction (§5.7) | Nonconformity | `"2023-02-30T10:00:00Z"` → accepted as `2023-03-02T10:00:00.000Z`. Expected: reject. Also affects `2023-04-31` and `2023-02-29`. |
| C8 | `client/parse.mjs:50` (`if (!KNOWN_KEYS.has(key)) continue;` ignores `critical`) | RFC 9557 §3.3 (a critical tag that cannot be processed: recipient "MUST NOT act on the IXDTF string"; MUST reject or perform other error handling) | MUST | Nonconformity | `"2022-07-08T00:14:07Z[!knort=blargel]"` → accepted, `tags: {}`. Expected: error. Contract: API.md:50-51. |
| C9 | `client/parse.mjs:51` (`out.tags[key] = value` overwrites) | RFC 9557 §3.3 (for duplicate elective keys the application "MUST choose the first suffix that has that key") | MUST | Nonconformity | `"2022-07-08T00:14:07Z[u-ca=chinese][u-ca=japanese]"` → `calendar: "japanese"`. Expected: `"chinese"`. The Python side (`setdefault`, `timeutil.py:135`) is correct. |

## Schema / docs defects

| ID | Location | RFC section | Level | Expected severity | Input → wrong output (expected) |
|---|---|---|---|---|---|
| S1 | `schema/event.schema.json:2` (plain 2020-12 dialect, no format-assertion vocabulary) with `"format": "date-time"` at lines 26, 31, 36, 40, 45, 50, 55; claim at `docs/API.md:12-15` | RFC 3339 §5.6 (the production that `format` names). JSON Schema 2020-12 Validation §7.2: `format` is annotation-only by default. | Contract / validation gap | Deviation | Validating P2's `"-0400"`, P3's `"2026-09-24T23:13:18"`, or P4's `"09:15-04:00"` with a default 2020-12 validator → valid. The docs claim CI "guarantees" well-formed timestamps. Expected: enable the `format-assertion` vocabulary or add `pattern`s. |
| S2 | `docs/API.md:19-21` | RFC 3339 §5.6 (the Internet profile is extended format with `-`, `:`, `T`, and a mandatory offset; ISO 8601 allows much more, such as basic format and omitted offsets) | SHOULD (profile) / contract inconsistency | Deviation | The docs say "ISO 8601" and list `20260314T133000Z` as valid. The client (`parse.mjs`) and `timeutil.parse_timestamp` both reject it, while the table requires "RFC 3339". Expected: specify the RFC 3339 `date-time` (or RFC 9557 `date-time-ext`) and drop the basic-format example. |
| S3 | `schema/event.schema.json:47-50` (`all_day_date` has `"format": "date-time"`) | RFC 3339 §5.6 (`full-date` vs `date-time` productions) | Wrong production | Nonconformity (alt: Deviation) | The emitted `"all_day_date": "2026-06-19"` (api.py:40) would fail a date-time assertion. Expected: `"format": "date"` (full-date). |

## Decoys (compliant, but may look suspicious)

| ID | Location | Expected severity | Why it is compliant |
|---|---|---|---|
| D1 | `timeutil.py:46` (`format_instant`: exactly 3 fractional digits, `Z`), used for `received_at` at `api.py:37`; profile at `docs/API.md:35-39` | no finding | `time-secfrac = "." 1*DIGIT` sets no fixed precision, so a generator may choose milliseconds. It is a documented output profile, and consumers are told to accept any number of digits. `Z` fits a server receipt instant that carries no local-time meaning (RFC 9557 §2.2). The value is truncated, not rounded, so it never produces `.1000`. |
| D2 | `timeutil.py:22` (`[Tt]`), `timeutil.py:25` (`[Zz]`), `timeutil.py:88` | no finding | RFC 3339 §5.6 NOTE: "T" and "Z" may be lower case. Only generators SHOULD use upper case. Accepting `1985-04-12t23:20:50.52z` is correct (dev test line 42). |
| D3 | `timeutil.py:145-146` and `client/parse.mjs:89-90` (skip the critical-zone vs. offset consistency check when the offset is `Z` or `-00:00`) | no finding | RFC 9557 §3.4 Figure 2 and §3.3 note: `2022-07-08T00:14:07Z[!Europe/London]` is not inconsistent, because `Z` (and `-00:00`, which has the same meaning per §2) asserts no local offset. Numeric offsets are still checked (`+00:00[!Europe/London]` is rejected), which is correct per Figure 1. |

## Unseeded issues (a skill may reasonably flag these; they are not scored as misses)

- `parse.mjs:77`: a leap second is accepted but clamped to :59, with `leapSecond: true` returned. This is a representational loss, not a rejection.
- `timeutil.py` `parse_timestamp`: year `0000` is rejected because of Python's `MINYEAR=1`, although the grammar allows it.
- `parse.mjs` does not validate the `time-zone-name` grammar. It depends on Temporal to reject unknown names; elective unknown names are dropped.
- `timeutil._TAG_RE` does not enforce the `suffix-key` or `suffix-values` grammar. It is harmless in practice because unknown keys are rejected (see C4).
- `api.py:50` `ingest` re-projects `start` into the named zone. This is fine.

# RFC 3339 / RFC 9557 audit of Tempo's timestamp producers

**Scope:** I audited the producers only: the `format_*` helpers in `timeutil.py` and every JSON field built by `api.py` `serialize()`. Field `start` claims the IXDTF (RFC 9557) profile. The other timestamp fields claim RFC 3339 `date-time` (`docs/API.md:25-32`, `schema/event.schema.json`). Declared options, from `docs/API.md:36-44`:
- Generators use upper-case `T` and `Z`.
- `received_at` has millisecond precision.
- No space separator, leap-second policy or production restriction is declared.

**Evidence:** static only. You said there is no shell, so I did not run `rfcdt.py scan`, `run_vectors.py` or `rfcdt.py check`. I worked out each output below by hand from the code and the sample data in `api.py:61-103`, and checked it by hand against the RFC 3339 §5.6 and RFC 9557 §4.1 grammar. My samples: 5 events × 8 fields. 6 of the 8 fields produce at least one invalid string or a wrong instant.

**Summary:** 8 nonconformities, 2 deviations, 4 advisories, 2 interpretation notes.

## What `GET /v1/events` emits (worked out from the code)

| Field | evt_0001 (New York, 09:30 EDT) | Should be | Verdict |
|---|---|---|---|
| `start` | `2026-03-14T09:30:00-04:00[America/New_York]` | same | ✅ valid IXDTF |
| `start_utc` | `2026-03-14T09:30:00Z` | `2026-03-14T13:30:00Z` | ❌ wrong instant (off by 4 h) |
| `end` | `2026-03-14T11:00:00-0400` | `…-04:00` | ❌ not valid under the grammar |
| `reminder_at` | `2026-03-14T09:15-04:00` | `…T09:15:00-04:00` | ❌ not valid under the grammar |
| `created_at` | e.g. `2026-09-25T14:03:07` | offset required | ❌ not valid under the grammar |
| `received_at` | e.g. `2026-09-25T18:03:07.123Z` | same | ✅ valid |
| evt_0002 `start` | `2026-05-04T10:00:00+05:30[UTC+05:30]` | `2026-05-04T10:00:00+05:30` | ❌ not valid under the grammar |
| evt_0003 `all_day_date` | `2026-06-19` | schema says `date-time` | ❌ schema and output disagree |
| feed `source_seen_at` | `2026-03-26T16:00:00+00:00` | `2026-03-26T16:00:00Z` | ⚠ Advisory |

## Findings

| # | Severity | Section | Location | Finding | Input → output | Fix |
|---|---|---|---|---|---|---|
| 1 | **Nonconformity** (wrong instant) | 3339 §4.1, §5.6 (meaning of `Z`) | `timeutil.py:51`, used at `api.py:33` | `format_utc` adds a literal `Z` to the datetime's **own wall time** and never converts to UTC. Every non-UTC event gets a false `start_utc`. The docs call this field the sort key (`docs/API.md:26`), so sorting is wrong too. A naive datetime gets host-local wall time labelled `Z`. | NY 09:30 EDT → `2026-03-14T09:30:00Z` (should be `13:30:00Z`). IST 10:00 → `…T10:00:00Z` (should be `04:30:00Z`). LA 2026-09-11 19:00 → `2026-09-11T19:00:00Z` (should be `2026-09-12T02:00:00Z`, a different day). | Reject naive input, then `dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")` |
| 2 | **Nonconformity** (grammar) | 3339 §5.6 `time-numoffset = ("+" / "-") time-hour ":" time-minute` | `timeutil.py:13`, `timeutil.py:56`, used at `api.py:34` | `RFC3339_FMT` uses `%z`, which prints `+HHMM` with no colon. A naive datetime gets an empty `%z`, so the offset is missing entirely. | NY 11:00 → `2026-03-14T11:00:00-0400`. IST → `2026-05-04T10:15:00+0530`. | Use `dt.isoformat(timespec="seconds")` after rejecting naive input (also see #8), or use `%:z` on Python 3.12+. |
| 3 | **Nonconformity** (grammar) | 3339 §5.6 `partial-time = time-hour ":" time-minute ":" time-second` (seconds are required) | `timeutil.py:14`, `timeutil.py:61`, used at `api.py:35`. The invalid output is also locked in by the test at `tests/test_timeutil.py:32`. | `REMINDER_FMT` drops the seconds. Minute precision is a fine policy, but under §5.6 NOTE a profile may restrict values, not drop required fields. `isoformat()[-6:]` also breaks: for an offset with seconds it takes `:44:30`, and for a naive datetime it takes digits of the time. | `09:30 − 15 min` → `2026-03-14T09:15-04:00` | `dt.replace(second=0, microsecond=0).isoformat(timespec="seconds")`. Update the test to expect `…T09:15:00-04:00`. |
| 4 | **Nonconformity** (grammar) | 3339 §5.6 `full-time = partial-time time-offset` (offset required); §4.4 | `api.py:25` (`default_factory=datetime.now`), `api.py:36` | `created_at` is a **naive** host-local time. `isoformat()` then prints no offset, so the value's instant depends on whichever host produced it. | → `2026-09-25T14:03:07` | `default_factory=lambda: datetime.now(timezone.utc)` and serialize with `timeutil.format_instant`. |
| 5 | **Nonconformity** (grammar + MUST NOT) | 9557 §4.1 `time-zone-char` has no `:`; 9557 producer rule: MUST NOT copy the offset into an offset time zone | `timeutil.py:69-70`, `timeutil.py:77`, used at `api.py:32` | `zone_label` falls back to `str(tz)`. For a fixed-offset `timezone` that gives `UTC+05:30`, which is not a valid zone name. Writing it as `[+05:30]` would still break the MUST NOT on copying the offset. The same path runs when a partner sends an offset with no suffix: `ingest` sets `tz = start.instant.tzinfo` (`api.py:50`). The schema does not catch it: its pattern ends `\[.+\]` (`schema/event.schema.json:21`). | IST 10:00 → `2026-05-04T10:00:00+05:30[UTC+05:30]` | Add a suffix only when `tz` has an IANA `key`. Otherwise emit plain RFC 3339. Tighten the schema pattern to the RFC 9557 zone-name grammar. |
| 6 | **Nonconformity** (schema and producer disagree) | 3339 §5.6 `full-date` vs `date-time`; erratum 5624 (held) | `api.py:40` vs `schema/event.schema.json:47-51` | `all_day_date` emits a `full-date`, but the schema says `"format": "date-time"`. Any validator that enforces `format` rejects every all-day event. The docs (`docs/API.md:31`) don't name the production either. | `date(2026,6,19)` → `2026-06-19` (not a `date-time`) | Change the schema to `"format": "date"`. In the docs, say "RFC 3339 `full-date`". |
| 7 | **Nonconformity** (wrong instant) | 3339 §4.2 (offset meaning) | `api.py:35` (`event.start - event.reminder`) | Subtracting from an aware `ZoneInfo` datetime works on wall-clock time. Across a DST gap the reminder can come out **later than the start**. The string is well-formed; the instant is wrong. (The cause is arithmetic, but it shows up as an emitted timestamp.) | Start `2026-03-08T03:05:00-04:00` (07:05Z) − 15 min → wall time 02:50 does not exist; fold=0 gives −05:00 → `…T02:50-05:00` = 07:50Z, 45 min **after** the start | Subtract in UTC: `(event.start.astimezone(timezone.utc) - event.reminder).astimezone(event.start.tzinfo)` |
| 8 | **Nonconformity** (grammar, latent) | 3339 §5.6 `time-numoffset` has no seconds field | `timeutil.py:56` (`%z`), `timeutil.py:61`, `timeutil.py:77` (`isoformat`) | `isoformat()` and `%z` print offsets that have seconds as `±HH:MM:SS` / `±HHMMSS`. Real zones have such offsets for historical dates (e.g. Africa/Monrovia 1970, −00:44:30; check against the tzdata you ship). Silently cutting the seconds would give a wrong instant, so that is not a fix either. | Monrovia 1970-06-01 12:00 → `1970-06-01T12:00:00-00:44:30[Africa/Monrovia]` | Detect `utcoffset() % 60s != 0`. Then either raise, or emit the UTC instant with `Z` (and no suffix). |
| 9 | **Deviation** (false contract) | 3339 §5.6; JSON Schema 2020-12 format-annotation vocabulary | `docs/API.md:13-15` | The docs say every response is validated against the schema in CI, which "guarantees that all timestamp fields are well-formed". The repo has no CI config, no validator dependency and no format-assertion setup. In 2020-12, `format` is annotation-only by default. The invalid rows in #2–#6 would pass. | See #2–#6 | Add a CI step that turns on format assertion with a strict checker (or a `pattern` per field), and runs it on `python3 api.py` output. |
| 10 | **Deviation** (docs) | 3339 §5.6 (extended format only) | `docs/API.md:19-21` | The docs say timestamps are "ISO 8601" and give `20260314T133000Z` as an example. That basic format is not RFC 3339, and it contradicts the RFC 3339 / RFC 9557 claims in the table at `docs/API.md:25-29`. | `20260314T133000Z` → rejected by any RFC 3339 parser | State that timestamps are RFC 3339 `date-time` (IXDTF for `start`) and drop the basic-format example. |
| 11 | Advisory | 9557 §2 (`Z` = local offset unknown; `+00:00` = UTC is the preferred reference) | `timeutil.py:66`, used at `api.py:42` | The docs say the local offset for `source_seen_at` is unknown (`docs/API.md:32`), but `isoformat()` emits `+00:00`. | `1774540800` → `2026-03-26T16:00:00+00:00` | Use `timeutil.format_instant`, or at least a `…Z` formatter. |
| 12 | Advisory | 9557 §2 (round-trip turns `Z` into `+00:00`) | `api.py:50` → `timeutil.py:77` | A partner `start` of `…Z` with no suffix comes back as `+00:00[UTC]`. That claims a UTC local context the partner never gave. | `2026-04-02T16:00:00Z` → `2026-04-02T16:00:00+00:00[UTC]` | If the input offset was `Z`/`-00:00` and there was no zone, emit `Z` with no suffix. |
| 13 | Advisory (platform-dependent, not checked here) | 3339 §5.6 `date-fullyear = 4DIGIT` | `timeutil.py:46`, `:51`, `:56`, `:61` | `strftime("%Y")` does not zero-pad years below 1000 on some libc builds. `isoformat()` always pads. | year 999 → possibly `999-…` | Build from `isoformat()`, or format the year as `f"{dt.year:04d}"`. |
| 14 | Advisory | 9557 §4.1 `suffix-values = 1*alphanum *("-" 1*alphanum)` | `timeutil.py:79` (partner value accepted at `timeutil.py:27`) | `u-ca` values are passed through without checking. The ingest regex accepts any value without `[`/`]`, so a value like `he brew` would be re-emitted invalid. | `[u-ca=he brew]` → re-emitted as-is | Check the value against `[A-Za-z0-9]+(-[A-Za-z0-9]+)*` before emitting. |

**Checked and conformant:**
- `format_instant` (`timeutil.py:41-46`): rejects naive input, converts to UTC, rounds down to exactly 3 fraction digits, uses `Z`. This matches `docs/API.md:36-37`.
- `format_ixdtf` with IANA zones (`api.py:32`) gives valid IXDTF, e.g. `2026-09-11T19:00:00-07:00[America/Los_Angeles][u-ca=hebrew]`.
- Every producer uses upper-case `T`/`Z`, as §5.6 NOTE recommends.

## Interpretation notes

- **`format_ixdtf(datetime.now(timezone.utc))` → `…+00:00[UTC]`.** `UTC` is a valid zone name (the tzdata link to `Etc/UTC`), so I did not grade the suffix itself. The `Z` vs `+00:00` question is covered in #12.
- **Minute-precision reminders (#3).** I read §5.6 NOTE as letting a profile limit *values* (seconds always `:00`), not remove the required `time-second` field. That is why #3 is a nonconformity even though the minute-precision rule is stated in a code comment.

## Not run / not applicable

- **Static scan, conformance vectors and `rfcdt.py check` on the samples:** not run, because there is no shell. Every output above was worked out by hand from the code, so none of these checks has a clean result on record. Run `python3 api.py` and `rfcdt.py check` on each field to confirm.
- **Consumers (`parse_timestamp`, `parse_ixdtf`, `client/parse.mjs`):** out of scope for this producer audit and not graded. In passing, I noticed two things worth a separate consumer audit:
  - `parse_timestamp` treats a missing offset as host-local time (`timeutil.py:107-108`).
  - `parse_ixdtf` rejects every unknown elective key (`timeutil.py:133-134`), which contradicts `docs/API.md:49`.
- **Leap seconds:** Python `datetime` cannot represent `:60`, so no producer can emit one.

## Reproduction

After fixing, run `python3 api.py`. Pass each timestamp field to `python3 ~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py check '<s>' --json`, and the `start` field with `--profile ixdtf` as well. Also probe:
- an event at `2026-03-08T03:05` America/New_York with a 15-minute reminder (#7)
- a 1970 Africa/Monrovia datetime (#8)
- a `timezone(timedelta(hours=5, minutes=30))` start (#5)

Library versions and tzdata version were not recorded, because nothing was run.

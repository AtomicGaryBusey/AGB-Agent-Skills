# RFC 3339 / RFC 9557 adherence audit: Tempo timestamp producers

**Scope:** I audited the producers only: the `format_*` helpers in `timeutil.py` and the JSON fields built in `api.py` `serialize()`. I used the schema, the docs and the tests only to find out what is claimed. The profile is IXDTF (RFC 9557) for `start` and RFC 3339 `date-time` for every other field. Declared options, from `docs/API.md`: upper-case `T`/`Z`, and `received_at` uses exactly 3 fraction digits with `Z`. `start_utc` is used as a sort key.

**Evidence:** This was a static review only, because no shell was available. I did not run `rfcdt.py scan`, the vectors, `rfcdt.py check` or `selfcheck`. I worked out the output of each field by hand for the 5 sample events in `api.py:79-105`. I relied on the probed CPython behaviour in the skill's `ecosystem/python.md` (rows 220, 223, 225-231) and on the snapshot in `tests/test_timeutil.py:30-32`. Of the 8 timestamp fields, 5 give invalid or wrong-instant output on the shipped sample data, and 2 more do so under the probe inputs.

**Summary:** 9 nonconformities, 2 deviations, 1 advisory, 5 review notes.

## Worked-out output of `python3 api.py` (evt_0001, New York, 2026-03-14 09:30 EDT)

| Field | Emitted | Valid? |
|---|---|---|
| `start` | `2026-03-14T09:30:00-04:00[America/New_York]` | yes |
| `start_utc` | `2026-03-14T09:30:00Z` | grammatical, **wrong instant** (true: `13:30:00Z`) |
| `end` | `2026-03-14T11:00:00-0400` | **no**: offset has no colon |
| `reminder_at` | `2026-03-14T09:15-04:00` | **no**: no seconds |
| `created_at` | `2026-09-26T…:…:…` (naive local) | **no**: no offset |
| `received_at` | `2026-09-26T…​.123Z` | yes |

For evt_0002 (fixed offset IST), `start` is `2026-05-04T10:00:00+05:30[UTC+05:30]`, which is **invalid**. For evt_feed_0092, `start_utc` is `2026-09-11T19:00:00Z`, but the true instant is `2026-09-12T02:00:00Z`, so even the date is wrong.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | R3339-4.4-03, R3339-5.1-02, R3339-2-02 | 3339 §4.3, §5.1; 9557 §2 | producer | `timeutil.py:51` (used by `api.py:33`) | `format_utc` puts a literal `Z` on the datetime's own wall time. It never calls `astimezone(timezone.utc)`, so every non-UTC event gets a false instant. Naive input is also accepted silently. Because `start_utc` is the documented sort key (`docs/API.md:26`), events in different zones also sort in the wrong order. | NY `09:30-04:00` → `2026-03-14T09:30:00Z` (should be `13:30:00Z`). LA `19:00-07:00` → `2026-09-11T19:00:00Z` (should be `2026-09-12T02:00:00Z`). Berlin `18:00+02:00` → `18:00:00Z` (should be `16:00:00Z`). | Reject naive values, then `dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`, or reuse `format_instant`. |
| 2 | Nonconformity | R3339-5.6-09, R3339-5.6-19 (and R3339-5.6-10 for naive input) | 3339 §5.6 `time-numoffset` | producer | `timeutil.py:13`, `timeutil.py:56` (used by `api.py:34`) | `RFC3339_FMT` uses `%z`, which prints `±HHMM` with no colon. Despite its name, the output is outside the grammar. A naive datetime makes `%z` expand to an empty string, so there is no offset at all. | NY `end` → `2026-03-14T11:00:00-0400`. IST → `2026-05-04T10:15:00+0530`. Berlin → `2026-04-02T20:30:00+0200`. | Use `dt.isoformat(timespec="seconds")` or `%:z` (Python ≥ 3.12), and reject naive values. |
| 3 | Nonconformity | R3339-5.6-07 | 3339 §5.6 `partial-time` (seconds mandatory) | producer | `timeutil.py:14`, `timeutil.py:61` (used by `api.py:35`) | `REMINDER_FMT` drops seconds. `dt.isoformat()[-6:]` also assumes the last 6 characters are always `±HH:MM`. That is false for a naive value (you get the time instead) and for sub-minute offsets (you get a fragment). The test `tests/test_timeutil.py:30-32` locks the invalid output in. | NY → `2026-03-14T09:15-04:00`. IST → `2026-05-04T09:55+05:30`. Naive `09:15:42` → `2026-03-14T09:15:15:42`. | `dt.replace(second=0, microsecond=0).isoformat()` → `2026-03-14T09:15:00-04:00`, and update the test. |
| 4 | Nonconformity | R3339-4.2-02, R3339-4.4-03 | 3339 §4.2, §5.6 (offset meaning) | producer | `api.py:35` | `event.start - event.reminder` subtracts in wall-clock time within a `ZoneInfo` zone. Near a DST change this gives a nonexistent or ambiguous local time, and Python then attaches the offset from the wrong side of the transition. The reminder instant is wrong. | NY 2026-03-08, start `03:10-04:00` (07:10Z), minus 15 min → wall `02:55`, fold 0 → `…T02:55-05:00` = 07:55Z. That is 45 min *after* the start instead of 15 min before (should be 06:55Z = `01:55-05:00`). | Subtract in UTC: `(event.start.astimezone(timezone.utc) - event.reminder).astimezone(event.start.tzinfo)`. |
| 5 | Nonconformity | R3339-5.6-10, R3339-3-05, R9557-2-01 | 3339 §5.6, §3 | producer | `api.py:25`, `api.py:36` | `created_at` defaults to `datetime.now()`, which is naive local time. `.isoformat()` on it prints no offset, and the schema (`event.schema.json:38-41`) and docs (`docs/API.md:29`) both claim RFC 3339 "with offset". | `created_at` → `2026-09-26T10:15:00` (no `time-offset`; see `python.md` row 220). | `default_factory=lambda: datetime.now(timezone.utc)` and serialise with `timeutil.format_instant`. |
| 6 | Nonconformity | R9557-4.1-03, R9557-1.2-01 | 9557 §4.1 `time-zone-name`; §1.2 | producer | `timeutil.py:69-70`, `timeutil.py:77` (used by `api.py:32`) | `zone_label` falls back to `str(tz)` for any tzinfo without `.key`. For `datetime.timezone` this gives `UTC+05:30`, and `:` is not a `time-zone-char`. Correcting it to `[+05:30]` would still be an offset time zone made up from the offset, which §1.2 forbids. Other tzinfo types give labels like `tzlocal()`, or abbreviations such as `EDT` that are grammatical but are not IANA names. The same problem hits partner records whose offset has no zone: `api.py:50` falls back to `start.instant.tzinfo`. | evt_0002 → `2026-05-04T10:00:00+05:30[UTC+05:30]`. A `Z` partner record → `…+00:00[UTC]`. | Add the suffix only when `getattr(tz, "key", None)` is an IANA name. Otherwise emit the plain RFC 3339 `date-time`. |
| 7 | Nonconformity | R9557-4.1-08, R9557-5-01, R9557-3.1-01 | 9557 §4.1 `suffix-value`, §5 | producer | `timeutil.py:79` (data from `timeutil.py:27`, `api.py:56`) | `format_ixdtf` puts `calendar` into `[u-ca=…]` without validating it. Ingest accepts any value matching `[^\[\]]+`, so partner input passes straight through to the output. | Feed `start` `…[u-ca=hebrew lunar]` → emitted `…[America/Los_Angeles][u-ca=hebrew lunar]` (a space is outside `1*alphanum`). | Validate the value against `^[a-z0-9]{3,8}(-[a-z0-9]{3,8})*$` (a Unicode calendar identifier) before emitting it, or drop it. |
| 8 | Nonconformity | R3339-4.2-03, R3339-5.6-09 | 3339 §4.2, §5.6 | producer | `timeutil.py:77` (`isoformat`), `timeutil.py:56` (`%z`), `timeutil.py:61` (slice) | Offsets that are not whole minutes (LMT and other historical `ZoneInfo` offsets) come out with seconds, which is outside `time-numoffset`. `format_ixdtf` and `format_offset` pass them through, and `format_reminder` cuts them into fragments. | Paris 1850: `isoformat` → `1850-01-01T00:00:00+00:09:21` (`python.md` row 226). `%z` → `+000921`. The reminder slice gives `:09:21`. | Convert to UTC (or round the offset *and* shift the wall time) before formatting, or reject such values. |
| 9 | Nonconformity | R3339-5.6-01 (production choice), erratum 5624 | 3339 §5.6 `full-date` vs `date-time` | schema / producer | `api.py:40` ↔ `schema/event.schema.json:47-51` | `all_day_date` emits a valid `full-date`, but the schema declares `"format": "date-time"`, so the field is claimed as a production it does not match. | `date(2026,6,19).isoformat()` → `2026-06-19`, which fails `date-time`. | Change the schema to `"format": "date"`, since the value is correct. |
| 10 | Deviation | — (false contract claim) | 3339 §5.6 | docs | `docs/API.md:13-15` | The docs claim that CI validation "guarantees that all timestamp fields are well-formed". The repo has no CI config or validator setup, 2020-12 `format` is annotation-only by default, and findings #2, #3, #5, #6 and #9 are invalid in the shipped sample response. | See the rows above. | Remove the claim, or add a real check: a format-assertion validator plus `rfcdt.py check` over `api.py` output. |
| 11 | Deviation | R3339-5.2-02 | 3339 §5.6 (profile) | docs | `docs/API.md:19-21` | The contract says timestamps are "ISO 8601" and tells clients to accept the basic format `20260314T133000Z`. That is not RFC 3339, and the field table (lines 25-32) and schema contradict it. | `20260314T133000Z` fails the `date-time` ABNF. | State "RFC 3339 `date-time` (RFC 9557 for `start`)" and drop the basic-format example. |
| 12 | Advisory | R9557-2-01, R9557-2-02, R3339-4.3-01 | 9557 §2 | producer | `timeutil.py:66` (used by `api.py:42`) | `source_seen_at` comes from a bare POSIX time, and the docs say the local offset is unknown (`docs/API.md:32`). `isoformat()` on a `timezone.utc` value still emits `+00:00`, which asserts that UTC is the preferred reference. RFC 9557 §2 recommends `Z`. | `1774540800.0` → `2026-03-26T16:00:00+00:00`. `1788000000.0` → `2026-08-29T10:40:00+00:00`. | `datetime.fromtimestamp(s, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`, or reuse `format_instant`. |

## Review notes
- **`received_at` complies** (`timeutil.py:41-46`, `api.py:37`). It rejects naive values, converts to UTC, uses exactly 3 fraction digits (truncated) and a `Z`. That matches the stated profile (`docs/API.md:36-37`). Using `Z` for server receipt time fits RFC 9557 §2.
- **`start` complies for IANA-keyed zones.** Examples are `…-04:00[America/New_York]`, `…+02:00[Europe/Berlin]` and `…-07:00[America/Los_Angeles][u-ca=hebrew]`. It is in the grammar and the offset matches the zone. RFC 9557 §3 does not require producers to keep criticality, but ingest drops the partner's `!` flag (`timeutil.py:119`, not stored in `Stamp`), so re-emitted suffixes are always elective.
- **Schema `start` pattern** (`event.schema.json:21`): `\[.+\]$` accepts `[UTC+05:30]` and `[u-ca=hebrew lunar]`, so it would not catch #6 or #7 even if it were enforced. The other fields depend on `format`, which only annotates unless assertion is turned on.
- **`%Y` for years below 1000:** padding depends on the platform's `strftime`. The probe in `python.md` row 233 printed `0999` on its platform. Tempo's sample data is well above 1000, so I did not grade this.
- **Case:** every producer emits upper-case `T` and `Z`, as the docs require (`docs/API.md:43`).

## Not run / not applicable
- I did not run `rfcdt.py scan`, `rfcdt.py check`, `run_vectors.py` or `selfcheck`, because there is no shell. The outputs above are derived by hand from the code and the probed library behaviour in `references/ecosystem/python.md`, not captured from a run.
- I did not grade the consumer role (`timeutil.parse_timestamp`/`parse_ixdtf`, `client/parse.mjs`) because it was out of scope. Two things are worth a follow-up: `parse_timestamp` reads a missing offset as host-local time (`timeutil.py:107-108`), and `api.py:50` calls `ZoneInfo(start.zone)` on an offset zone such as `[+08:45]`, which raises.

## Assumptions
- CPython ≥ 3.9 with `zoneinfo` and a current tzdata. The first 2026 DST change in New York is on 2026-03-08, so on 2026-03-14 the offset is −04:00, which agrees with `tests/test_timeutil.py:27`.
- I treat every field in the schema as claimed RFC 3339 `date-time` (IXDTF for `start`), as `schema/event.schema.json` and `docs/API.md:25-32` state.

## Reproduction
Once a shell is available, confirm with:
```bash
S=~/.claude/skills/rfc3339-ixdtf/scripts
python3 $S/rfcdt.py selfcheck
python3 $S/rfcdt.py scan timeutil.py api.py --json
python3 api.py > out.json
# validate every timestamp field in out.json:
python3 $S/rfcdt.py check '2026-03-14T11:00:00-0400' --json                      # expect invalid (#2)
python3 $S/rfcdt.py check '2026-05-04T10:00:00+05:30[UTC+05:30]' --profile ixdtf --json  # expect invalid (#6)
python3 -m unittest tests/test_timeutil.py   # test_reminder_is_minute_precision should fail once #3 is fixed
```

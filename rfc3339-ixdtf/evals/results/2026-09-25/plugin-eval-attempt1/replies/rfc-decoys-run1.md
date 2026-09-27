I couldn't run anything (no shell), and I couldn't open the skill's check index, so the findings cite RFC sections instead of check IDs. Everything below comes from reading the code.

# Verdict on the three flagged items

None of the three is an RFC 3339 or RFC 9557 violation. All three can be closed.

| # | Flagged behaviour | Violation? | Why |
|---|---|---|---|
| 1 | `format_instant` always emits `.mmm` + `Z` (`timeutil.py:41-46`) | **No** | RFC 3339 §5.6 defines fractional seconds as `"." 1*DIGIT`, so three digits is valid. The §5.6 NOTE lets an application restrict the syntax, and `docs/API.md` states this restriction ("Precision profile"). Using `Z` for a server receipt instant fits RFC 9557 §2. The code truncates to milliseconds instead of rounding, which is allowed. Example: `2026-03-14T13:30:05.987Z` is valid. |
| 2 | The `timeutil` parser accepts lower-case `t`/`z` (`timeutil.py:22,25,88`) | **No, this is required behaviour** | ABNF literals are case-insensitive (RFC 5234 §2.3), and the RFC 3339 §5.6 NOTE says `T` and `Z` "may alternatively be lower case". Only producers SHOULD use upper case, and Tempo's producers do. The real defect is the reverse: `client/parse.mjs` rejects lower case (finding N13). |
| 3 | Both parsers skip the critical zone/offset consistency check when the offset is `Z` or `-00:00` (`timeutil.py:145`, `parse.mjs:89`) | **No, this is required behaviour** | Under RFC 9557 §2, `Z` and `-00:00` mean "the UTC time is known, the local offset is unknown". An unknown offset cannot disagree with a zone (§3.4), so `…Z[!Europe/London]` is consistent. Running the check would make the parsers too strict. The test at `tests/test_timeutil.py:60` covers this case. |

The reviewer missed a large number of real defects in these files. Here is the full report.

---

# RFC 3339 / RFC 9557 adherence — Tempo

**Scope:**
- **Producer:** `api.serialize` and the `timeutil.format_*` functions.
- **Consumers:**
  - `timeutil.parse_timestamp` / `parse_ixdtf`, used at the partner ingest boundary.
  - `client/parse.mjs`, which parses Tempo API responses.
- **Schema:** `schema/event.schema.json`.
- **Profile:** IXDTF for `start`, RFC 3339 for the other fields.
- **Declared options (docs):**
  - `received_at` has millisecond precision.
  - Parsers accept lower case.
  - Unknown elective tags are ignored.
  - For repeated keys, the first one wins.

**Evidence:** static reading of 6 files. Producer outputs were derived by hand from `api.sample_events`. No scan, vectors or dynamic probes were run.

**Summary:** 17 nonconformities, 2 deviations, 3 advisories, 2 interpretation notes.

## Findings

| # | Severity | Section | Role | Location | Finding | Evidence (input → output) | Fix |
|---|---|---|---|---|---|---|---|
| N1 | Nonconformity (wrong instant) | 3339 §4.2, §5.6 | producer | `timeutil.py:51`, used for `start_utc` | Uses `strftime` on an aware non-UTC datetime, so local wall time is labelled `Z` | NY 09:30 EDT → `2026-03-14T09:30:00Z` (should be `13:30:00Z`). IST 10:00 → `…T10:00:00Z` (should be `04:30:00Z`) | `dt.astimezone(timezone.utc)` first |
| N2 | Nonconformity | 3339 §5.6 `time-numoffset` | producer | `timeutil.py:13,56` (`end`) | `%z` gives an offset with no colon | → `2026-03-14T11:00:00-0400` | `dt.isoformat(timespec="seconds")` |
| N3 | Nonconformity | 3339 §5.6 `partial-time` | producer | `timeutil.py:14,61` (`reminder_at`) | Seconds are dropped, and the test at `test_timeutil.py:30` locks this in | → `2026-03-14T09:15-04:00` | Keep `:00` (`dt.replace(second=0, microsecond=0).isoformat()`) and fix the test |
| N4 | Nonconformity | 3339 §5.6 `time-offset` | producer | `api.py:25,36` (`created_at`) | `datetime.now` is naive, so the output has no offset | → `2026-09-25T10:00:00` | `default_factory=lambda: datetime.now(timezone.utc)` |
| N5 | Nonconformity | 9557 §4.1 `time-zone-name` | producer | `timeutil.py:69-77` (`start`) | Fixed-offset `tzinfo` is turned into `str(tz)`, which is not valid in a suffix. LMT zones would also print `+HH:MM:SS` offsets | IST event → `2026-05-04T10:00:00+05:30[UTC+05:30]` | Omit the suffix, or emit `[+05:30]`, when the tzinfo has no IANA `key`. Truncate offsets that have seconds only after adjusting the wall time |
| N6 | Nonconformity (too lenient, at the ingest boundary) | 3339 §5.6, §4.4 | consumer | `timeutil.py:25,107-108` | A missing offset is silently read as host-local time | `2026-03-14T13:30:00` → accepted with the host zone | Make the offset mandatory |
| N7 | Nonconformity (too lenient) | 3339 §5.6 | consumer | `timeutil.py:25,99` | In Python, `$` also matches before a trailing newline | `2026-03-14T13:30:00Z\n` → accepted | `re.fullmatch` or `\Z` |
| N8 | Nonconformity (too strict, no stated profile) | 3339 §5.7 | consumer | `timeutil.py:103` | `datetime(...,60)` raises, so every leap second is rejected | `2016-12-31T23:59:60Z` → ValueError | Map a valid `:60` to `:59` (or the next second), or document the restriction |
| N9 | Nonconformity (too lenient) | 9557 §4.1 `time-numoffset` | consumer | `timeutil.py:87-94,139` | Suffix offsets are sliced, not validated | `…+01:00[!+01:00junk]` → accepted as `+01:00`. `[+0100]` → accepted | Match `^[+-]\d{2}:\d{2}$` exactly |
| N10 | Nonconformity | 9557 §3.3 | consumer | `timeutil.py:127-135` | The critical flag on tags is ignored, so conflicting duplicates where one copy is critical are accepted | `…Z[u-ca=hebrew][!u-ca=chinese]` → accepted, calendar=hebrew | Reject when any copy of a repeated key is critical and the values differ |
| N11 | Nonconformity | 9557 §3.3 | consumer | `parse.mjs:50` | Unknown keys are skipped even when marked critical | `…Z[!x-foo=bar]` → accepted | `if (!KNOWN_KEYS.has(key)) { if (critical) throw …; continue; }` |
| N12 | Nonconformity (wrong effective tags) | 9557 §3.3 | consumer | `parse.mjs:51` | Last copy of a repeated key wins, which contradicts the RFC and docs | `…Z[u-ca=chinese][u-ca=japanese]` → `japanese` | Assign only if the key is absent. Apply the critical-conflict rule from N10 |
| N13 | Nonconformity (too strict, contradicts docs) | 3339 §5.6 NOTE | consumer | `parse.mjs:10,11,20,89` | Lower-case `t`/`z` are rejected | `1985-04-12t23:20:50.52z` → RangeError | Use `[Tt]` and `[Zz]`, and normalise before the `Z`/`-00:00` checks |
| N14 | Nonconformity (too lenient, wrong instant) | 3339 §5.7 | consumer | `parse.mjs:17,68,77` | The only day limit is 31, and `Date.UTC` normalises overflow | `2023-02-30T10:00:00Z` → `2023-03-02T10:00:00.000Z` | Check the day against the real month length (including leap years) |
| N15 | Nonconformity (wrong instant) | 3339 §5.6 `date-fullyear` | consumer | `parse.mjs:77` | `Date.UTC` maps years 0–99 to 1900–1999 | `0050-06-01T00:00:00Z` → 1950 | Use `new Date(0).setUTCFullYear(...)` or Temporal |
| N16 | Nonconformity (too lenient) | 3339 §5.7 | consumer | `parse.mjs:71,77` | `:60` is accepted at any time of day and silently becomes `:59` | `2026-03-14T09:30:60Z` → accepted | Allow `:60` only at 23:59 UTC (after adjusting for the offset) at month end |
| N17 | Nonconformity (schema) | 3339 §5.6, erratum 5624 | schema | `event.schema.json:47-51` | `all_day_date` is declared `date-time`, but the producer emits `full-date` | `2026-06-19` fails `date-time` | `"format": "date"` |
| D1 | Deviation | 3339 §5.6, rule 1 contract | docs | `docs/API.md:13-21` | The docs say CI "guarantees well-formed" timestamps, but N1–N5 ship invalid or false values. They also promise "any ISO 8601", including `20260314T133000Z`, which is not RFC 3339 and which `parse.mjs` rejects. The repo has no CI config, and JSON Schema `format` is annotation-only by default | See N1–N5 | Restrict the docs to RFC 3339/9557, enable format assertion in CI, and tighten the `start` pattern (`\[.+\]` accepts anything) |
| D2 | Deviation (docs); Advisory under RFC | 9557 §3.3 | consumer | `timeutil.py:133-134` | Every unknown elective tag is rejected, which contradicts "Unknown elective tags are ignored" | `…Z[x-foo=bar]` → ValueError | Ignore unknown elective tags. Reject only critical ones |
| A1 | Advisory | 9557 §2 | producer | `timeutil.py:66` (`source_seen_at`) | Emits `+00:00` for an instant whose local offset the docs say is unknown | → `…T…:…:…+00:00` | Emit `Z` |
| A2 | Advisory | 9557 §4.1 | ingest | `api.py:50` | For an offset-zone suffix, `ZoneInfo(start.zone)` raises (not strictly an RFC issue, but it crashes on valid input) | `…+01:00[+01:00]` → ZoneInfoNotFoundError | Reuse the tz that `parse_ixdtf` already resolved |
| A3 | Advisory | 3339 §5.6 | consumer | `parse.mjs:76` | Fractions are silently truncated to milliseconds | `.123456789` → `.123` | Document this, or keep the full fraction |

## Interpretation notes
- For item (3), I read RFC 9557 §2 and §3.4 as saying `Z` or `-00:00` followed by any zone is never an inconsistency. Both parsers follow this reading.
- Leap-second policy is left to the implementation (iers-months, table, or any month end). N8 and N16 are graded on "rejects all" and "accepts anywhere", not on which policy is chosen.

## Not run / not applicable
- **Not run (no shell):** `rfcdt.py scan`, the vector runner and producer probes. So no vector pass counts are reported. Every finding comes from reading code, with the input → output pairs derived by hand.
- **Not checked:** whether CI enforces the schema, because there is no CI config in the repo.

## Reproduction
To confirm these findings, run `python3 api.py`, then `python3 -m unittest tests/test_timeutil.py`, then `node client/parse.mjs '<input>'` with each input string above. The runtime assumptions are Python 3.13 and Node 26 with Temporal.

I checked all three flagged items against the RFC text: **none of them violates RFC 3339 or RFC 9557.** Each one is either explicitly allowed or required by the RFCs. While checking them I found other timestamp problems in the same files that are real violations. They're in the report below.

## The three flagged items

**(1) `format_instant` always writes three fractional digits and `Z`: not a violation.**
- The grammar allows any number of fraction digits (`time-secfrac = "." 1*DIGIT`, §5.6). The §5.6 NOTE says a specification may restrict the format further as long as the output stays inside the grammar, and `docs/API.md:34-39` states this millisecond restriction.
- Cutting off extra digits rather than rounding is fine.
- `Z` is also correct. Under RFC 9557 §2, `Z` means "UTC is known, local offset unknown", which fits a server receipt time. Sample output: `2026-03-14T13:30:05.987Z` (from `tests/test_timeutil.py:17`), which is valid.
- Severity: none.

**(2) `timeutil` accepts lower-case `t` and `z`: not a violation.**
- The §5.6 NOTE says `T` and `Z` "may alternatively be lower case". ABNF strings are case-insensitive, so `1985-04-12t23:20:50.52z` is valid input and rejecting it would be too strict.
- The code handles it consistently: `_TS_RE` at `timeutil.py:22,25`, `_offset` at `:88`, and the `"Zz"` test at `:145`.
- One small related point: `client/parse.mjs:10-11` accepts upper case only. The §5.6 NOTE allows that restriction, but it contradicts `docs/API.md:43-44` ("Parsers accept lower-case"). That's a documentation problem, folded into finding 13.

**(3) Both parsers skip the critical-zone consistency check for `Z` and `-00:00`: not a violation, and required.**
- RFC 9557 §3.4 and the §2 update say `Z` or `-00:00` assert no local offset. So `2022-07-08T00:14:07Z[!Europe/London]` is consistent and must not be rejected. Running the check here would be the error.
- Both parsers still reject an explicit mismatch such as `+00:00[!Europe/London]` (`timeutil.py:145-148`, `parse.mjs:89-91`, test at `tests/test_timeutil.py:56-62`).
- One catch: in `timeutil`, a date-time with no offset at all counts as "offset known" and gets compared using the host's local zone. The root cause is finding 6.

---

# RFC 3339 / RFC 9557 adherence — Tempo (api.py, timeutil.py, client/parse.mjs, docs/API.md)

Scope: producer (`api.serialize`, `timeutil.format_*`) and consumer (`timeutil.parse_*`, `client/parse.mjs`), IXDTF profile for `start`, RFC 3339 elsewhere. Declared options: millisecond `Z` for `received_at`, upper-case output, lower-case accepted, first key wins.
Evidence: static review only. No scan, vectors, producer checks or selfcheck were run (no shell). Every "input → output" below is worked out by hand from the code.
Summary: 10 nonconformities, 1 deviation, 2 advisories, 3 review notes (the flagged items).

## Findings
| # | Severity | Ref | Target | Location | Finding | Evidence (derived) | Fix |
|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | 3339 §4.2, §5.6 | producer | `timeutil.py:51`, `api.py:33` | `format_utc` writes local wall time with a literal `Z` and never converts to UTC, so the instant is wrong | NY 09:30 EDT → `start_utc: 2026-03-14T09:30:00Z` (should be `13:30:00Z`) | `dt.astimezone(timezone.utc)` first |
| 2 | Nonconformity | 3339 §5.6 `time-numoffset` | producer | `timeutil.py:13,56`, `api.py:34` | `%z` writes the offset without a colon | `end: 2026-03-14T11:00:00-0400` | `dt.isoformat(timespec="seconds")` |
| 3 | Nonconformity | 3339 §5.6 `partial-time` | producer | `timeutil.py:59-61`, `api.py:35` | `reminder_at` drops the seconds field (the test locks this in) | `2026-03-14T09:15-04:00` | Keep `:00` seconds; fix the test |
| 4 | Nonconformity | 3339 §5.6 `time-offset` | producer | `api.py:25,36` | `created_at` defaults to a naive `datetime.now`, so the output has no offset | `2026-09-26T10:00:00` | `datetime.now(timezone.utc)`, or reject naive values |
| 5 | Nonconformity | 9557 §4.1 `time-zone-name` | producer | `timeutil.py:69-70,77` | For fixed-offset tzinfo, `zone_label` falls back to `str(tz)`, which gives an invalid suffix | evt_0002 → `2026-05-04T10:00:00+05:30[UTC+05:30]` (`:` is not a valid tzchar) | Leave out the suffix for fixed offsets, or require a `ZoneInfo` |
| 6 | Nonconformity | 3339 §5.6, §4.4 | consumer (ingest gate) | `timeutil.py:25,107-108,16` | The offset is optional. When it's missing, the parser uses the host's local offset, frozen at import time, so the same input gives different instants on different hosts. The offset-less head also skips item (3) correctly: it's treated as a known offset and compared | `2026-04-02T18:00:00` → host-dependent instant | Make the offset required |
| 7 | Nonconformity | 9557 §3.3 (critical MUST) | consumer | `parse.mjs:50` | An unknown **critical** key is silently ignored | `…Z[!foo=bar]` accepted | Throw when `critical && !KNOWN_KEYS.has(key)` |
| 8 | Nonconformity | 9557 §3.3 (first wins) | consumer | `parse.mjs:51` | A repeated key uses the last value, so the effective tags are wrong (docs say first wins) | `…[u-ca=chinese][u-ca=japanese]` → `japanese` | Assign only if the key isn't already set; error if either copy is critical and they conflict |
| 9 | Nonconformity | 3339 §5.7 | consumer | `parse.mjs:17,68-77` | Day is checked against 31 regardless of month, and `Date.UTC` rolls invalid dates forward (wrong instant). `:60` is accepted at any minute and then clamped | `2026-02-30T00:00:00Z` → 2026-03-02. `2026-03-14T10:15:60Z` accepted | Check days per month; allow `:60` only at 23:59 UTC |
| 10 | Nonconformity | 3339 §5.6 `time-second` 00-60, §5.7 | consumer | `timeutil.py:103-106` | A valid leap second makes `datetime()` raise, and no profile documents that restriction | `2016-12-31T23:59:60Z` → `ValueError` | Handle `:60` (e.g. map to :59.999999 with a flag) or document the restriction |
| 11 | Advisory | 9557 §2 | producer | `timeutil.py:66`, `api.py:42` | `source_seen_at` uses `+00:00` even though the docs say its local offset is unknown | `2026-03-26T16:00:00+00:00` | Write `Z` |
| 12 | Advisory | 9557 §3.3 | consumer | `timeutil.py:133-134` | Every unknown **elective** tag is rejected, which erases the difference between elective and critical tags (docs say electives are ignored) | `…[foo=bar]` → `ValueError` | Ignore unknown electives; reject only critical ones and `_` keys |
| 13 | Deviation | docs vs. rows 1-5 | schema/docs | `docs/API.md:12-21,43-44` | The docs claim the non-existent `schema/event.schema.json` is enforced in CI. They list the ISO 8601 basic form `20260314T133000Z`, which isn't RFC 3339 and which both parsers reject. They say parsers accept lower case, but `parse.mjs` doesn't | see rows 1-5 | Add the schema and validation, or correct the docs |

## Review notes
- **(1) Millisecond `Z` precision profile:** a documented restriction that stays inside the grammar (§5.6 NOTE). Compliant.
- **(2) Lower-case `t`/`z` accepted by `timeutil`:** valid input under §5.6 NOTE. `parse.mjs` rejecting it is a MAY-level restriction; the only issue is the doc mismatch in row 13.
- **(3) Consistency check skipped for `Z`/`-00:00`:** required behaviour under RFC 9557 §2/§3.4. Compliant in both parsers.
- `parse.mjs` needs a global `Temporal`. Without it, every zone lookup throws: critical zones are rejected and elective zones are dropped. Whether that happens depends on the runtime.

## Not run / not applicable
None of `rfcdt.py scan`, `run_vectors.py`, `rfcdt.py check` or `selfcheck` were run (no shell). That's why there are no vector counts, and I'm not claiming anything passed. `schema/event.schema.json` isn't in the repo.

## Assumptions
- `start` follows the IXDTF profile; all other fields follow RFC 3339 as `docs/API.md` states.
- `timeutil.parse_*` sits at an ingest gate (partner feeds).
- Python 3.11+ (`zoneinfo`); tz data is whatever the host provides.

## Reproduction
Static reading of the files at the lines cited. To confirm the findings, run `python3 $S/rfcdt.py check` on the `python3 api.py` output, and `run_vectors.py --target-kind both` with thin adapters around `timeutil.parse_ixdtf` and `parseTimestamp`.

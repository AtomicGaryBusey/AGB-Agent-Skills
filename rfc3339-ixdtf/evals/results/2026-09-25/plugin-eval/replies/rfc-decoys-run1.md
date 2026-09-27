# RFC 3339 / RFC 9557 review of Tempo (`timeutil.py`, `api.py`, `client/parse.mjs`)

## The three reviewer flags: none of them violates the RFCs

| # | Flag | Violation? | Severity | Reasoning |
|---|---|---|---|---|
| 1 | `format_instant` always emits 3 fractional digits plus `Z` (`timeutil.py:41-46`) | **No** | None | `time-secfrac = "." 1*DIGIT`, so any fixed digit count is valid. §5.6 NOTE lets an application limit the syntax, and `docs/API.md:34-39` states this precision profile. `Z` is correct under RFC 9557 §2 for an instant that carries no meaningful local offset. The output (`2026-03-14T13:30:05.987Z`, `tests/test_timeutil.py:17`) is valid. Truncating rather than rounding is a precision choice, not a conformance issue. One latent caveat that `received_at` can't reach: `%Y` isn't zero-padded for years below 1000 on some platforms. |
| 2 | `timeutil`'s parser accepts lower-case `t` and `z` (`timeutil.py:22,25,88,145`) | **No** | None | This is required behaviour, not leniency. ABNF literals are case-insensitive, and RFC 3339 §5.6 NOTE says `T` and `Z` may be lower case. The real problem is the opposite one, in `client/parse.mjs` (finding J1 below). |
| 3 | Both parsers skip the critical zone-vs-offset check when the offset is `Z` or `-00:00` (`timeutil.py:145-148`, `parse.mjs:89-92`) | **No** | None | RFC 9557 §2 says `Z` and `-00:00` mean "UTC known, local offset unknown", so there is nothing to disagree with the zone (§3.4). `…Z[!Europe/London]` is consistent. Both parsers still reject a critical zone they can't evaluate (`timeutil.py:141-142`, `parse.mjs:86`), which is the obligation that does apply. The test at `tests/test_timeutil.py:60-62` pins the right behaviour. |

All three flags are false positives. The same files do have real nonconformities, listed below.

---

# RFC 3339 / RFC 9557 adherence: Tempo

**Scope:**
- **Roles:**
  - Producer: `api.serialize` and the `timeutil.format_*` helpers.
  - Consumer: `timeutil.parse_timestamp`/`parse_ixdtf`, which handle partner-feed ingest (an untrusted boundary), and `client/parse.mjs`.
  - Schema: `schema/event.schema.json`.
- **Profiles:** RFC 3339, plus IXDTF for `start`.
- **Declared options:** millisecond precision with `Z` for `received_at`, and upper-case output with lower-case accepted on input (`docs/API.md`).

**Evidence:** static reading only. The scan, the conformance vectors and the producer runs were **not run**, because no shell was available. The output strings below are what the code produces when traced by hand, not captured output.

**Summary:** 15 nonconformities, 2 deviations, 2 advisories, 1 interpretation note.

## Findings

### Producer (`timeutil.py` / `api.py`)

| # | Severity | Location | Finding | Input → output (derived) | Fix |
|---|---|---|---|---|---|
| P1 | **Nonconformity** (wrong instant) | `timeutil.py:49-51`, `api.py:33` | `format_utc` puts a literal `Z` after local wall time without converting to UTC. `start_utc` is also the sort key, so sorting is wrong too. | NY 09:30-04:00 → `2026-03-14T09:30:00Z` (should be `13:30:00Z`) | Call `dt.astimezone(timezone.utc)` first. |
| P2 | **Nonconformity** (grammar) | `timeutil.py:13,54-56`, `api.py:34` | `%z` produces `-0400` with no colon. | `end` → `2026-03-14T11:00:00-0400` | Use `dt.isoformat(timespec="seconds")`. |
| P3 | **Nonconformity** (grammar) | `timeutil.py:59-61`, `api.py:35` | `reminder_at` drops `time-second`, which the grammar requires. The test at `test_timeutil.py:30-32` locks this in. | → `2026-03-14T09:15-04:00` | Set `second=0, microsecond=0` and format with seconds (`09:15:00-04:00`). |
| P4 | **Nonconformity** (grammar, missing offset) | `api.py:25,36` | `created_at` comes from naive `datetime.now`, so `isoformat()` has no offset. The value also depends on the host's zone. | → `2026-09-25T10:00:00` | Use `datetime.now(timezone.utc)`. |
| P5 | **Nonconformity** (suffix grammar) | `timeutil.py:69-80` | For a fixed-offset tzinfo, `zone_label` falls back to `str(tz)`. That puts `:` into a zone name, which the grammar forbids, and the zone is invented from the offset anyway. | Bangalore event → `2026-05-04T10:00:00+05:30[UTC+05:30]` | Emit a suffix only for a real IANA `key`. Otherwise use plain RFC 3339 or a deliberate offset zone; never copy the offset into a zone just to have one (§1.2). |
| P6 | **Advisory** (RFC 9557 §2) | `timeutil.py:64-66`, `api.py:42` | `source_seen_at` has an unknown local offset (the docs say so at `API.md:32`) but is emitted with `+00:00` instead of `Z`. | → `…T…:…:…+00:00` | Emit `Z`. |

### Consumer: `timeutil.py` (partner ingest)

| # | Severity | Location | Finding | Input → output (derived) | Fix |
|---|---|---|---|---|---|
| T1 | **Nonconformity** (too lenient, wrong instant) | `timeutil.py:25,107-108` | The offset is optional. A missing offset is read as host-local time. | `2026-03-14T09:30:00` → accepted, instant depends on the host | Make the offset mandatory. |
| T2 | **Nonconformity** (too lenient) | `timeutil.py:25,99` | Python's `$` matches before a trailing newline. | `2026-03-14T09:30:00Z\n` → accepted | Use `fullmatch` or `\Z`. |
| T3 | **Nonconformity** (RFC 9557 §3.3) | `timeutil.py:133-135` | The critical flag is ignored on tags, so conflicting duplicates where one copy is critical are accepted. `[!u-ca=<unsupported>]` is also accepted because values are never checked. | `…Z[u-ca=hebrew][!u-ca=chinese]` → accepted | Reject when conflicting copies include a critical one. Validate critical values. |
| T4 | **Nonconformity** (too strict, §5.7) | `timeutil.py:103-106` | `datetime` rejects `second=60`, so every valid leap second fails and no policy is stated. | `2016-12-31T23:59:60Z` → `ValueError` | Accept `:60` where §5.7 allows it and map it explicitly (e.g. clamp to :59), or state a profile restriction. |
| T5 | **Advisory** (plus a docs deviation, D2) | `timeutil.py:133-134` | Every unknown *elective* tag is rejected, which removes the difference between elective and critical tags. `API.md:49` says such tags are ignored. | `…[foo=bar]` → `ValueError` | Ignore unknown elective tags. Reject only critical ones. |

### Consumer: `client/parse.mjs`

| # | Severity | Location | Finding | Input → output (derived) | Fix |
|---|---|---|---|---|---|
| J1 | **Nonconformity** (too strict; contradicts `API.md:43-44`) | `parse.mjs:10-11,20` | Lower-case `t` and `z` are rejected even though they are valid input. This is the real issue near flag 2. | `1985-04-12t23:20:50.52z` → `RangeError` | Use `[Tt]`/`[Zz]` or the `i` flag, and make `parseOffset` and `offsetKnown` case-insensitive. |
| J2 | **Nonconformity** (too lenient) | `parse.mjs:13` | The regex has no `^` anchor, so a match anywhere in the string is accepted. | `junk2026-03-14T09:30:00Z` and `12026-…` → accepted | Add `^`. |
| J3 | **Nonconformity** (wrong instant) | `parse.mjs:17,68,77` | Days are only checked against 31, and `Date.UTC` silently rolls impossible dates forward. | `2023-02-30T10:00:00Z` → `2023-03-02T10:00:00Z` | Validate against the real length of the month. |
| J4 | **Nonconformity** (wrong instant) | `parse.mjs:77` | `Date.UTC` maps years 0–99 to 1900–1999. | `0050-01-01T00:00:00Z` → 1950 | Use `new Date(0).setUTCFullYear(...)` or Temporal. |
| J5 | **Nonconformity** (§5.7) | `parse.mjs:71` | `:60` is accepted at any hour and minute, not only at 23:59 UTC at month end. | `2026-03-14T12:34:60Z` → accepted | Check against the offset-adjusted UTC time and a stated policy. |
| J6 | **Nonconformity** (RFC 9557 §3.3) | `parse.mjs:50` | Unknown keys are skipped before the critical flag is checked, so unknown critical tags are silently ignored. | `…Z[!foo=bar]` → accepted | Throw when `critical && !KNOWN_KEYS.has(key)`. |
| J7 | **Nonconformity** (§3.3, first wins) | `parse.mjs:51` | For duplicate keys, the last one wins. | `…[u-ca=chinese][u-ca=japanese]` → `japanese` | Keep the first value (`??=`). Reject conflicts that involve a critical copy. |

### Schema and docs

| # | Severity | Location | Finding | Fix |
|---|---|---|---|---|
| S1 | **Nonconformity** (schema production) | `event.schema.json:47-50` | `all_day_date` is a `full-date` but is declared `format: date-time`. | Use `"format": "date"`. |
| D1 | **Deviation** (false contract) | `API.md:12-15` | "CI guarantees well-formed timestamps" is false. Draft 2020-12 `format` is only an annotation unless assertion is configured, and P1–P5 produce invalid output. | Enable format assertion with a real checker, or remove the claim. |
| D2 | **Deviation** | `API.md:19-21,49` | The contract says "any ISO 8601", including `20260314T133000Z`, which isn't RFC 3339 and which both parsers reject. The elective-tag rule doesn't match T5. | Say RFC 3339 / RFC 9557 and drop the compact example. |

## Interpretation notes
- `Z[!zone]` and `-00:00[!zone]` are treated as consistent (flag 3), following RFC 9557 §2/§3.4. `Z[+08:45]` is ambiguous in the RFC; neither parser treats it as inconsistent, which is an allowed reading.
- An inconsistent *elective* zone is not checked by either parser. That's allowed (MAY). `api.ingest` then silently re-projects the instant into that zone.

## Not run / not applicable
- Nothing was run: no `rfcdt scan`, no conformance vectors (`run_vectors.py`), no producer captures, no semantic probes. The "no shell" constraint prevented all of them.
- Every input → output pair above comes from reading the code and should be confirmed with the vector runner.
- `parse.mjs` assumes a global `Temporal` (Node 26 has it). On older runtimes, every critical zone would be rejected.

## Reproduction (once a shell is available)
```bash
python3 api.py | jq -r '.events[] | .[]' | xargs -I{} python3 ~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py check '{}' --json
python3 ~/.claude/skills/rfc3339-ixdtf/scripts/run_vectors.py --target "<adapter around timeutil.parse_ixdtf>" --target-has-tzdata yes --target-kind both --target-options fixed
```

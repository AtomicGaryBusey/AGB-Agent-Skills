# RFC 3339 / RFC 9557 adherence: Tempo timestamp contract

**Scope:** the schema (`schema/event.schema.json`) and the contract docs (`docs/API.md`). The contract claims two profiles: `start` is IXDTF (RFC 9557) and the other fields are RFC 3339 `date-time`. Options it declares:
- Generators emit upper-case `T`/`Z` and parsers accept `t`/`z` (API.md:43-44).
- `received_at` has exactly 3 fraction digits and ends in `Z` (API.md:36-37).
- Clients accept fractions of any length (API.md:38-39).
- `start` must carry a zone suffix (schema:19-21).
- Suffix rules are at API.md:46-54.

**Evidence:** I reviewed everything statically. No shell was available, so I didn't run `rfcdt.py scan`, the vector runner or `selfcheck`. To check the contract's claims, I worked out producer output by hand from `api.py` and `timeutil.py`. I did not execute those outputs; they are marked "traced" below.

**Summary:** 5 nonconformities, 2 deviations, 2 advisories, 7 review notes. A further 6 implementation defects are listed after the table but not counted.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | **Nonconformity** | R3339-5.6-03/04/05/06/07/09/16, R9557-4.1-01/02, R9557-3.2-01 (schema side), R9557-3.3-04 | 3339 §5.6; 9557 §3.1, §4.1 | schema | schema/event.schema.json:21 (claim at :19) | The `start` pattern is the only check on `start` (it has no `format`). It uses `[0-9]{2}` with no range limits, and `\[.+\]$` accepts any text in brackets. The suffix grammar is not enforced: it doesn't require the zone first, doesn't limit key characters (lower case only), doesn't validate the `!` flag, and doesn't stop trailing text. It also accepts a string with only a calendar tag and no zone, although API.md:25 says the zone is always there. | These all match the pattern: `2026-13-45T25:61:99+99:99[x]`, `…+05:30[UTC+05:30]` (`:` is not allowed in `time-zone-part`), `…Z[U-CA=hebrew]` (upper-case key), `…Z[_foo=bar]` (experimental key), `…Z[Europe/Paris] junk]`, `…-04:00[u-ca=hebrew]` (no zone), `…Z[!!x]`. | Put a strict RFC 3339 core in the pattern (month `0[1-9]\|1[0-2]`, hour `[01][0-9]\|2[0-3]`, …, offset `[+-]([01][0-9]\|2[0-3]):[0-5][0-9]`). Then use `\[!?(zone-name\|[+-]HH:MM)\](\[!?[a-z][a-z0-9-]*=[A-Za-z0-9]+(-[A-Za-z0-9]+)*\])*$`, where the name parts follow §4.1 `time-zone-part`. Add `"not":{"pattern":"\n"}` because Python and .NET let `$` match before a trailing newline. |
| 2 | **Nonconformity** | R9557-1.2-01, R9557-4.1-02 | 9557 §1.2 (MUST NOT), §4.1 | schema + producer | schema/event.schema.json:19-21, docs/API.md:25; produced at timeutil.py:70,77 | The contract requires a zone suffix on every `start`. Some events have no IANA zone: fixed-offset events, and partner records with no zone (api.py:50). For those, `format_ixdtf` builds a suffix from `str(tzinfo)`. The result is invalid, and it is also the offset-copied-into-a-suffix pattern that §1.2 forbids. Finding #1 means the schema lets it through. | evt_0002 (traced): `2026-05-04T10:00:00+05:30[UTC+05:30]` | Make the suffix optional for events with no IANA zone (§3.3: suffixes are optional). Emit a suffix only when `tzinfo.key` exists. Never write `[+05:30]` or `[UTC+05:30]`. |
| 3 | **Nonconformity** | R3339-5.6-18 | 3339 §5.6 (`full-date`, erratum 5624); JSON Schema `date` | schema | schema/event.schema.json:47-51; docs/API.md:31 | `all_day_date` is described as a "calendar date" but declared `format: date-time`. A plain date can never be a valid `date-time`, so every correct value fails once format checks are on. | `all_day_date` = `2026-06-19` (api.py:40, traced) fails `date-time`. | Change it to `"format": "date"` (`full-date`). |
| 4 | **Nonconformity** | R9557-3.2-01 | 9557 §3.2 (MUST reject) | docs (consumer contract) | docs/API.md:49 | The docs say unknown elective tags are ignored. They make no exception for experimental keys (starting with `_`). §3.2 says those keys MUST be rejected, with or without `!`, unless the consumer is configured for the experiment. Clients that follow the docs will accept `[_foo=bar]`. | `1996-12-19T16:39:57-08:00[_foo=bar]`: the docs say ignore it, the RFC says reject it. | Add: "Tags whose key starts with `_` are rejected unless the client is configured for that experiment." |
| 5 | **Nonconformity** | R9557-3.3-06 (and -05) | 9557 §3.3 (MUST treat as erroneous) | docs (consumer contract) | docs/API.md:52 | "The first occurrence is used" is stated for every repeated key. §3.3 allows first-wins only when all copies are elective. If any copy of a conflicting key is critical, the string is erroneous in either order. timeutil.py:135 (`setdefault`) does what the docs say. | `2022-07-08T00:14:07Z[u-ca=chinese][!u-ca=japanese]`: the docs give chinese, the RFC says erroneous. | Change it to: "If all copies are elective, the first is used. If any copy is critical and the values differ, the timestamp is invalid." |
| 6 | **Deviation** | R3339-5.6-01, R3339-5.6-19, R3339-5.6-16 | 3339 §5.6, App. A | docs | docs/API.md:19-21 | The docs call every timestamp "ISO 8601" and tell clients to accept "any ISO 8601 representation". The example given, `20260314T133000Z`, is ISO 8601 basic format, which is outside the RFC 3339 grammar. That conflicts with the table below it (API.md:25-30) and with `format: date-time`. It also pushes clients to be more lenient than the RFC. | `20260314T133000Z` fails RFC 3339 `date-time`. | Say "RFC 3339 §5.6 `date-time` (and RFC 9557 IXDTF for `start`)". Remove the basic-format example and the "any ISO 8601" wording. |
| 7 | **Deviation** | (contract claim, rule 1) | 3339 §5.6 | docs + schema | docs/API.md:13-15; schema/event.schema.json:2 | The docs say CI validation "guarantees that all timestamp fields are well-formed". That is false for two reasons. (a) Under draft 2020-12, `format` is only an annotation unless format assertion is turned on, and the repo has no CI config or validator setup. (b) Traced output breaks the schema's own `date-time` in several fields. | Traced sample output: `end` = `2026-03-14T11:00:00-0400` (no colon; timeutil.py:13,56), `reminder_at` = `2026-03-14T09:15-04:00` (no seconds; timeutil.py:14,61, locked in by tests/test_timeutil.py:32), `created_at` = `2026-09-26T…` with no offset (naive `datetime.now`, api.py:25,36), and `all_day_date` = `2026-06-19` (#3). | Turn format assertion on and use a real checker (e.g. `jsonschema[format]` with `FORMAT_CHECKER`), add strict `pattern`s, and add the CI step. Until then, remove the guarantee. |
| 8 | Advisory | R3339-5.1-01/02 | 3339 §5.1 | schema + docs | docs/API.md:26, docs/API.md:30; schema/event.schema.json:23-26, :42-45 | `start_utc` is "used for sorting", but the schema accepts any offset and any fraction length. Sorting the strings gives the correct order only when every value has the same offset and precision. The UTC-only rule (and for `received_at`, milliseconds plus `Z`) appears only in prose, even though API.md:13 calls the schema "the source of truth". | `2026-03-14T09:30:00-04:00` and `2026-03-14T13:30:00.5Z` both pass as `start_utc` and sort in the wrong order. | Pin the profiles with patterns: `start_utc` `…:[0-5][0-9]Z$`, and `received_at` `…\.[0-9]{3}Z$`. |
| 9 | Advisory | R9557-2-01/02 | 9557 §2 | docs + schema | docs/API.md:32; schema/event.schema.json:52-56 | The docs say the local offset of `source_seen_at` is unknown. Under RFC 9557 that should be written `Z`, but the contract doesn't require it. The producer writes `+00:00`, which claims UTC is the preferred reference. | timeutil.py:66: `fromtimestamp(…, tz=utc).isoformat()` gives `…+00:00`. | Specify `Z` in the docs and in a schema pattern, and emit it with `strftime("%Y-%m-%dT%H:%M:%SZ")` on the UTC value. |

### Where the code breaks the contract (evidence only, not counted)
These fall outside the scope you gave me (schema and docs), but they show where rows of the contract are broken:
- **Wrong time in `start_utc`.** timeutil.py:51 adds a literal `Z` to local wall time without converting to UTC. evt_0001 gives `2026-03-14T09:30:00Z` where it should be `13:30:00Z`. That breaks API.md:26 ("the same instant as `start`"). The string is well-formed, so no schema can catch it. This is the most serious defect in the service.
- **Offsets without a colon.** timeutil.py:13 and :56 use `%z`, which writes `-0400`.
- **Seconds dropped.** timeutil.py:61 leaves the seconds out of `reminder_at`.
- **No offset on `created_at`.** api.py:25 uses naive `datetime.now`, so `created_at` has no offset.
- **Ingest assumes host time.** On the ingest side (API.md:58-59), timeutil.py:25 makes the offset optional and timeutil.py:108 then assumes host-local time. `2026-04-02T18:00:00[Europe/Berlin]` is accepted.
- **Unknown tags rejected.** timeutil.py:133-134 rejects every unknown tag, which contradicts API.md:49. This is an Advisory under rule 4.

## Review notes
- **Case, schema:21 vs API.md:43-44.** The `start` pattern accepts only upper-case `T`/`Z`. §5.6 NOTE lets a producer profile restrict case, so this is fine for checking server output. But clients that reuse the schema to check input would be too strict compared with API.md:44. Say which use the schema is for.
- **Required suffix, schema:21.** RFC 9557 §3.3 lets an application require suffix tags, so requiring one is a valid profile choice in itself. Finding #2 is only about how the requirement is met.
- **`[Area/City]`, API.md:25.** This wording is narrower than the RFC 9557 grammar and the tz database. It leaves out `UTC`, `Etc/GMT+5`, three-part names like `America/Argentina/Buenos_Aires`, and offset zones. I read it as descriptive, not as a restriction.
- **`Z` in `start`, API.md:25 vs schema:21.** The docs say "numeric offset" but the pattern allows `Z`. `Z[zone]` is valid and means the local offset is unknown (9557 §3.4 Fig. 2). Pick one.
- **API.md:50-54.** It says unprocessable critical *tags* are errors, but not that an unknown critical *zone name* is also an error (9557 §3.3/§4.1). The code handles that case (timeutil.py:141-142). The rule "with `Z` there is no disagreement" should also cover `-00:00` (9557 §2); timeutil.py:145 already does.
- **API.md:48.** "Zone suffix comes first" is correct (§4.1: `suffix = [time-zone] *suffix-tag`).
- **Not stated anywhere:** the leap-second policy (whether `:60` is accepted and on which dates), and the fraction precision for fields other than `received_at`. RFC 3339 allows these to vary, so this isn't a defect, but clients need to know.

## Not run / not applicable
- `rfcdt.py scan`, `run_vectors.py`, `rfcdt.py check` and `selfcheck` were not run because no shell was available. So there are no vector pass rates and no tool-verified producer samples. All producer strings above are traced by hand from the source.
- I did not audit the client (`client/parse.mjs`) because it was out of scope.
- I found no CI or validator configuration in the repo (the only files are `api.py`, `timeutil.py`, `tests/`, `client/`, `schema/` and `docs/`), so I had no configured validator to test against.

## Assumptions
- The schema is checked with a draft 2020-12 validator and default settings (format is annotation only), since the repo sets up nothing else.
- Patterns follow ECMA-262 semantics, as JSON Schema specifies. The trailing-newline problem only applies on Python and .NET validators.
- tz data: New York on 2026-03-14 is UTC−04:00 (DST starts 2026-03-08).

## Reproduction
Once a shell is available (S=`~/.claude/skills/rfc3339-ixdtf/scripts`):
```bash
python3 api.py > /tmp/sample.json
python3 $S/rfcdt.py check '2026-03-14T11:00:00-0400' --json             # end: expect invalid
python3 $S/rfcdt.py check '2026-05-04T10:00:00+05:30[UTC+05:30]' --profile ixdtf --json  # start: expect invalid suffix
python3 $S/rfcdt.py scan schema docs timeutil.py api.py --json
python3 $S/rfcdt.py selfcheck
```
To test the `start` pattern, write an adapter that applies the pattern from schema:21 with ECMA-262 `u`-flag semantics. Run it with `run_vectors.py --target-kind ixdtf --target-options fixed --target-has-tzdata no`. I expect a large TOO LENIENT bucket, which would confirm #1.

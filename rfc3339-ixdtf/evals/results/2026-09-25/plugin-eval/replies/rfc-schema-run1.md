# RFC 3339 / RFC 9557 adherence audit: Tempo timestamp contract

**Scope:** I audited `schema/event.schema.json` and `docs/API.md` as the schema/contract role. They use two profiles: `start` is IXDTF (RFC 9557), and every other timestamp field is RFC 3339 `date-time`. The contract also declares these options:
- producers write upper-case `T`/`Z` (API.md:43)
- `received_at` has exactly 3 fractional digits and ends in `Z` (API.md:36-37)
- consumers must accept any number of fractional digits (API.md:38)
- consumers accept lower-case `t`/`z` (API.md:43-44)

The contract does not state a leap-second policy, which suffixes are required, or which experimental keys are configured.

**Evidence:** everything here comes from reading the files. I did not run `rfcdt.py scan`, `run_vectors.py`, or `rfcdt.py check`, and I did not execute any code, because there is no shell. The producer outputs quoted below are what I traced by hand through `api.py` and `timeutil.py` for the sample events in `api.py:79-105`. I also read `api.py`, `timeutil.py`, `client/parse.mjs` and `tests/` to check whether the contract's claims are true.

**Summary (contract):** 3 nonconformities, 3 deviations, 4 advisories, 4 interpretation notes. A separate table lists 9 implementation defects that show the contract's claims are false.

## Findings: contract

| # | Severity | Check / Section | Location | Finding | Evidence (input → output) | Fix |
|---|---|---|---|---|---|---|
| 1 | **Deviation** (false contract claim) | JSON Schema `format` is annotation-only; RFC 3339 §5.6 | `docs/API.md:13-15`, `schema/event.schema.json:2`, `:26,31,36,40,45,50,55` | The docs say CI validation "guarantees that all timestamp fields are well-formed". But under draft 2020-12, `format: "date-time"` is only an annotation unless format-assertion is turned on and a checker is configured. The repo has no CI config, no schema-validation test and no checker (`tests/test_timeutil.py` only tests `timeutil`). Real outputs break the grammar anyway (see table B, rows B2–B6). | `end` → `2026-03-14T11:00:00-0400`; `reminder_at` → `2026-03-14T09:15-04:00`; `created_at` → `2026-09-25T10:00:00` (no offset); `start` → `…+05:30[UTC+05:30]`; `all_day_date` → `2026-06-19`. None of these would be caught. | Add a CI step that validates real responses with format assertion enabled (for example ajv + `ajv-formats` in `full` mode, or `jsonschema` + `rfc3339-validator`). Test that checker against conformance vectors, because both are known to be lenient (ajv-formats accepts `+0200`). Until that exists, remove the guarantee from the docs. |
| 2 | **Nonconformity** | 3339 §5.6 ABNF range comments (`date-month 01-12`, `time-hour 00-23`, `time-minute 00-59`, `time-second 00-58/59/60`, `time-numoffset`), §5.7 | `schema/event.schema.json:21` | The `start` pattern uses plain `[0-9]{2}` for every field. This is the only enforced check (`start` has no `format`), and it accepts strings outside the grammar. | Accepted: `2026-13-45T25:61:99+24:00[Europe/Paris]`, `2026-02-30T09:00:00+23:60[Europe/Paris]` | Constrain the ranges (pattern below). Day-of-month and leap-second rules can't be expressed as a regex, so a real validator still has to check those (finding 1). |
| 3 | **Nonconformity** | 9557 §4.1 `suffix` / `time-zone` / `suffix-key` ABNF; §3.3 experimental keys | `schema/event.schema.json:21` (`\[.+\]$`) | The suffix part is `\[.+\]`, which accepts any text containing brackets. It does not require the zone to come first, it allows characters outside `time-zone-char`, and it allows invalid keys and values. | Accepted: `…+05:30[UTC+05:30]` (`:` is not a `time-zone-char`; the producer really emits this, see B5), `…Z[Europe/Paris]junk]`, `…Z[ ]`, `…Z[u-ca=hebrew]` (no zone, but API.md:25 implies one), `…Z[!_exp=1]` | Use the grammar pattern below. |
| 4 | **Nonconformity** | 3339 §5.6 production choice (erratum 5624 held: `full-date` → JSON Schema `date`) | `schema/event.schema.json:47-50`; `docs/API.md:31` | `all_day_date` is described as a "calendar date" but declared as `format: "date-time"`. The producer (`api.py:40`) emits a `full-date`, which is not a valid `date-time`. The docs don't name a production. | `date(2026,6,19).isoformat()` → `2026-06-19`, which fails `date-time` | Change to `"format": "date"` and state "RFC 3339 `full-date`" in API.md:31. |
| 5 | **Deviation** (false contract claim) | 3339 §5.6 (the Internet profile of ISO 8601) | `docs/API.md:19-21` | The docs say "All timestamps are ISO 8601" and "Clients should accept any ISO 8601 representation". That contradicts the field table (API.md:25-30) and the schema, which require RFC 3339/9557. The example `20260314T133000Z` is ISO 8601 basic format, which is not RFC 3339. Tempo's own parsers reject it (`client/parse.mjs:13`, `timeutil.py:20-26`). | `20260314T133000Z` → rejected by every RFC 3339 parser in the repo | Replace with: "All timestamps are RFC 3339 §5.6 `date-time`, except `start` (RFC 9557 IXDTF) and `all_day_date` (RFC 3339 `full-date`)." Remove the compact example. |
| 6 | **Deviation** (false contract claims) | 3339 §5.6 NOTE (case); 9557 §3.3 (critical/elective/duplicate keys) | `docs/API.md:43-44`, `:49`, `:50-51`, `:52` | The documented consumer rules don't match what the parsers do: lower-case accepted (API.md:43-44), unknown elective tags ignored (:49), unprocessable critical tags make the timestamp invalid (:50-51), first duplicate wins (:52). Details and the implementation severities are in table B, rows B7–B9. | `1985-04-12t23:20:50.52z` → rejected by `client/parse.mjs`; `…Z[Europe/Paris][!foo=bar]` → accepted by the client with the critical tag dropped; `…[u-ca=chinese][u-ca=japanese]` → client reports `japanese` | Fix the parsers (table B). The docs describe the correct behaviour. |
| 7 | **Advisory** | 3339 §5.1 (string sorting needs a fixed offset and precision) | `schema/event.schema.json:24-26`, `:43-45`; `docs/API.md:26`, `:36-37` | `start_utc` ("used for sorting") and `received_at` ("UTC, millisecond precision") state their UTC and precision limits only in prose. The schema allows any offset and any number of fractional digits, so string sorting on `start_utc` is not safe by contract. | `2026-03-14T09:30:00-04:00` and `2026-03-14T13:30:00.5Z` would both validate as `start_utc` | Add patterns: `start_utc` `^…:[0-5][0-9](Z)$` (seconds, `Z`); `received_at` `^…\.[0-9]{3}Z$`. |
| 8 | **Advisory** | 9557 §2 (updates 3339 §4.3): `Z` means "local offset unknown", `+00:00` means UTC is the preferred reference | `docs/API.md:32`; `schema/event.schema.json:52-55` | The docs say the local offset of `source_seen_at` is unknown, which is exactly what `Z` means. The contract doesn't require `Z`, and the producer (`timeutil.py:66`, `isoformat()` on a UTC datetime) emits `+00:00`, which asserts UTC is the preferred reference. | `seen: 1774540800.0` → `2026-03-26T16:00:00+00:00` | Say `Z` in the docs, add `Z$` to the schema pattern, and emit with `.strftime('%Y-%m-%dT%H:%M:%SZ')` or `.isoformat().replace('+00:00','Z')`. |
| 9 | **Advisory** | 9557 profile statement (§1.2 offset zones, §3.2 critical flag) | `docs/API.md:25`; `schema/event.schema.json:19` | The IXDTF profile for `start` leaves these questions open. (a) Is a zone suffix required? API.md:25 implies yes; the schema requires only *some* bracket. (b) Are offset zones (`[+05:30]`) allowed, or only `[Area/City]`? (c) Do producers ever emit the critical flag `!`? (d) Which keys other than `u-ca` may appear? `api.py:61-76` also shows that ingest re-emission drops critical flags. That isn't stated either. | `start` for a fixed-offset event is `…[UTC+05:30]` (B5); the contract says nothing about this case | State: zone suffix required, IANA name only (or offset zone allowed, but not copied from the offset just to satisfy a consumer, per §1.2), critical flag not emitted, only `u-ca` keys. |
| 10 | **Advisory** | 9557 §3.3 (experimental keys, conflicting duplicates), §2 (`-00:00`) | `docs/API.md:46-54` | The suffix rules leave out some RFC 9557 requirements. (a) An experimental `_key` MUST be treated as erroneous unless the consumer is configured for it. (b) Duplicate keys where any copy is critical and the values conflict make the string erroneous; "first wins" applies only to elective keys. (c) `-00:00` counts the same as `Z` for zone-consistency checks. (d) The docs don't say how an unknown *elective* zone name is handled. | `…Z[Europe/Paris][!u-ca=hebrew][u-ca=gregory]` isn't covered by API.md:52 | Add these rules to the "Suffix handling" section. |

### Suggested `start` pattern (fixes findings 2 and 3; JSON-escape the backslashes)

```
^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])\[!?[A-Za-z._][A-Za-z0-9._+-]{0,13}(/[A-Za-z._][A-Za-z0-9._+-]{0,13})*\](\[!?[a-z_][a-z0-9_-]*=[A-Za-z0-9]+(-[A-Za-z0-9]+)*\])*$
```

This enforces upper-case `T`/`Z`, as the producer profile at API.md:43 says it should. It still can't reject `02-30`, or `:60` outside a leap-second month-end. That needs an asserted validator (finding 1).

## B. Implementation defects that show the contract's claims are false

I found these while checking the contract's claims. This was not a full producer/consumer audit, and no vectors were run.

| # | Severity | Location | Defect | Input → output |
|---|---|---|---|---|
| B1 | **Nonconformity** (well-formed, wrong instant; 3339 §2, §5.6) | `timeutil.py:49-51` (used at `api.py:33`) | `format_utc` puts a literal `Z` after the local wall time without converting to UTC. `start_utc` is not "the same instant as `start`" (API.md:26), and sorting on it is wrong across zones. | `09:30 America/New_York` → `2026-03-14T09:30:00Z` (should be `13:30:00Z`) |
| B2 | **Nonconformity** (grammar) | `timeutil.py:13,54-56` (`api.py:34`) | `%z` gives an offset without the colon | `end` → `2026-03-14T11:00:00-0400` |
| B3 | **Nonconformity** (grammar: `partial-time` needs seconds) | `timeutil.py:14,59-61` (`api.py:35`); the test at `tests/test_timeutil.py:30-32` locks this behaviour in | seconds dropped | `reminder_at` → `2026-03-14T09:15-04:00` |
| B4 | **Nonconformity** (grammar: `time-offset` is required) | `api.py:25` (`datetime.now` gives a naive value), `api.py:36` | `created_at` has no offset; API.md:29 says "with offset" | → `2026-09-25T10:00:00` |
| B5 | **Nonconformity** (9557 §4.1 `time-zone-name`) | `timeutil.py:69-70,77` | For a fixed-offset `tzinfo`, `str(tz)` becomes the zone suffix | `ist` event → `2026-05-04T10:00:00+05:30[UTC+05:30]` |
| B6 | **Nonconformity** (production) | `api.py:40` | full-date in a `date-time` field (finding 4) | `2026-06-19` |
| B7 | **Nonconformity** (the contract claims lower-case is accepted) | `client/parse.mjs:10-11` | the regex allows only upper-case `T` and `Z` | `1985-04-12t23:20:50.52z` → `invalid timestamp` |
| B8 | **Nonconformity** (9557 §3.3 MUST) | `client/parse.mjs:33-34,50` | the `!` is removed before the known-key check, so unknown critical keys are silently ignored | `2022-07-08T00:14:07Z[Europe/Paris][!foo=bar]` → accepted |
| B9 | **Nonconformity** (wrong value; 9557 §3.3 first wins) | `client/parse.mjs:51` | the last duplicate wins | `…[u-ca=chinese][u-ca=japanese]` → `calendar: "japanese"` |
| B10 | **Advisory** (rule 4: this removes the elective/critical distinction; it also contradicts API.md:49) | `timeutil.py:133-134` | every unknown key is rejected, elective ones included | `…Z[Europe/Paris][foo=bar]` → `ValueError` |
| B11 | **Nonconformity** (a gating consumer that is too lenient) | `timeutil.py:25,107-108` (the ingest path, `api.py:48-49`) | a missing offset is read as host-local time instead of being rejected | `2026-04-02T18:00:00[Europe/Berlin]` → accepted, with the offset taken from the host |

## Interpretation notes

- **9557 §4.1 `time-zone` precedence:** I read it as `"[" critical-flag (time-zone-name / time-numoffset) "]"`. The suggested pattern follows that reading.
- **`Z` with a critical zone:** API.md:53-54 says `Z` asserts no offset, so there is nothing inconsistent. That matches §2 and the §3.4 reasoning, so I didn't mark it. `Z[+08:45]` is implementation-defined, and the contract doesn't need to settle it.
- **Upper-case-only schema pattern:** this is a stated producer restriction (API.md:43, §5.6 NOTE allows an application to limit the syntax), not a defect. It does mean the schema can't be reused to validate consumer input.
- **Leap seconds:** the contract has no policy. The suggested pattern allows `:60` at the grammar level. `timeutil.parse_timestamp` rejects every `:60` (`datetime(second=60)` raises), and `client/parse.mjs:77` clamps it to `:59`. Neither is graded, but the contract should state one policy.

## Not run / not applicable

- `rfcdt.py scan`, `run_vectors.py` and `rfcdt.py check` were not run (no shell). So there are no vector pass/fail counts, and I'm not reporting a clean result for any vector group.
- The producer outputs above were traced by hand from the code and were not executed. `created_at` depends on the time of the run. The UTC value of `source_seen_at` for `1774540800` was worked out by hand.
- The ECMA-262 behaviour of the schema pattern was reasoned about, not tested against the vectors.

## Reproduction (once a shell is available)

1. `python3 ~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py scan api.py timeutil.py client/ schema/`
2. `python3 api.py`, then run `rfcdt.py check '<value>'` on each field (use `--profile ixdtf` for `start`).
3. Write an adapter that compiles the `start` pattern with `new RegExp(p, 'u')` and run `run_vectors.py --profile ixdtf --target-kind ixdtf --target-has-tzdata no --target-options fixed`.
4. Write an adapter for `client/parse.mjs` (Node 26, Temporal) and for `timeutil.parse_ixdtf` (Python 3.13) that returns `effective_tags`, then run with `--target-has-tzdata yes`.

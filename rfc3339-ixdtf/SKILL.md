---
name: rfc3339-ixdtf
description: "Audit code for RFC 3339 (Internet timestamps, the usual 'ISO timestamp format' of APIs and logs) and RFC 9557 (IXDTF: suffixes such as 2026-09-24T12:00:00+02:00[Europe/Paris] and [u-ca=hebrew] tags; Z now means 'local offset unknown'). USE FOR: parsing, validating or emitting these timestamps in any language (Python, JS and Temporal ZonedDateTime, Java, .NET, Go, Rust, Swift); choosing Z or +00:00 when the offset is unknown; leap second 23:59:60 legality; reviewing producers, consumers and schemas (JSON Schema/OpenAPI format date-time, protobuf Timestamp, API contracts); ServiceNow GlideDateTime and Fluent SDK date handling; running conformance vectors against a parser; scanning source for risky date-time APIs (strftime %z, literal 'Z'). DO NOT USE FOR: ISO 8601 durations, week or ordinal dates, intervals; HTTP-date or RFC 5322 email dates; time-zone arithmetic unrelated to serialization."
metadata:
  author: local
  version: "1.0.0"
  sources: "RFC 3339 (July 2002) + errata 293,1584,3710,4110,5624,5783,6533; RFC 9557 (April 2024) + erratum 8192; IANA Internet Date/Time Format registry (snapshot 2026-09-24)"
---

# RFC 3339 + RFC 9557 (IXDTF) adherence audit

RFC 3339 is the Internet profile of ISO 8601 (`2026-09-24T12:00:00.5+02:00`). RFC 9557 **updates** it (`Z` now
means "UTC known, local offset unknown") and adds an optional suffix: `…+02:00[Europe/Paris][u-ca=hebrew]`.

| Role (Target) | What it is | Main sections |
|---|---|---|
| **producer** | Code that emits timestamps | 3339 §3, §4, §5.6 NOTE (case), §5.7; 9557 §1.2, §2 (Z vs +00:00), §3 |
| **consumer** | Code that parses or validates timestamps | 3339 §5.6–5.7, App. C/D; 9557 §3.2–3.4, §4.1 |
| **schema** | JSON Schema, OpenAPI, IDL, DB column docs | 3339 §5.6 productions (erratum 5624); 9557 profile choice |

**Sources.** Quote ABNF and short normative sentences with a section (IETF Trust, BCP 78): the catalogs hold the
verbatim ABNF and every erratum. Verified errata apply; Held for Document Update errata (5624 partial productions,
5783 space separator) are profile options; the Rejected erratum 9557 #8192 is a note only. Library behaviour is in
`references/ecosystem/`: probed versions, otherwise "unverified (from docs)". Re-probe the target's version before
you rely on a row.

## Severity (rule 1)

| RFC level | Report as |
|---|---|
| `MUST`/`MUST NOT`, or grammar (ABNF incl. range comments, §5.7 restrictions) | **Nonconformity** |
| `SHOULD`/`SHOULD NOT` | **Deviation** (departing needs a stated reason) |
| `MAY`, lower-case should/may, informative | **Advisory** |
| Ambiguous RFC text, profile readings, choices the RFC leaves open | **Review note** (never a defect) |

- Consumer too lenient: Nonconformity if it gates input or claims RFC 3339/9557, unless documented; else Advisory.
- Producer outside the grammar: Nonconformity when claimed or consumed as RFC 3339.
- Well-formed but wrong instant or tags (local time labelled `Z`, last-wins duplicate keys, years 0–99 → 19xx):
  Nonconformity.
- False contract or docs claim: Deviation, reported once.
- `+00:00` for an unknown local offset, or `Z`↔`+00:00` rewritten on a round trip: Advisory (9557 §2).
- MAY-level or optional items about compliant code are not findings; mention them only in Review notes if useful.

**Read `references/interpretation.md` before step 3**: the full rules (1 grading, 2 `Z` semantics, 3 profiles,
4 RFC 9557 consumer obligations, 5 known ambiguities and leap-second policies) and how to grade vector results.

## Workflow

Clone or copy audit targets **outside iCloud-synced folders** (`~/Documents`, `~/Desktop`): files that are not
available locally are skipped and counted, and reading them can stall. Below, `S=~/.claude/skills/rfc3339-ixdtf/scripts`.
Flags and output shapes: `references/tools.md`.

1. **Scope.** Roles, claimed profile (RFC 3339 only, or IXDTF), declared options (space separator, lower case,
   productions, fraction precision, leap-second policy, tz database, experimental keys). A stated restriction is
   fine (§5.6 NOTE) if its output stays in the grammar. Platform formats (ServiceNow `yyyy-MM-dd HH:mm:ss` UTC)
   are profiles: judge them at boundaries (`references/servicenow.md` §1). Filter `references/check-index.md`
   (109 checks) by role.
2. **Static scan.** `python3 $S/rfcdt.py scan <paths> --json [--include-dist] [--max-bytes N]` (86 patterns;
   languages in `references/tools.md`). Output `{meta, summary, findings}`; `summary` is the denominator (files
   seen, scanned, skipped by reason and extension). Hits are leads: confirm each in context. `# rfcdt: ignore`
   suppresses a line. Never call a skipped file clean.
3. **Dynamic vectors (strongest evidence).** Write an adapter that calls the target's real parser: string on
   stdin, prints `{"ok": true|false}`, `{"skip": true}`, or `{"ok": true, "resolved": true}`, plus `fields` it
   exposes (`year`…`second`, `offset_minutes`, `effective_tags`, …). Examples: `run_vectors.py` docstring.
   ```bash
   python3 $S/run_vectors.py --target "<adapter cmd>" --target-kind rfc3339|ixdtf|both \
       --target-options fixed --target-has-tzdata yes|no [--batch | --jobs N] \
       [--tz-matrix UTC,America/St_Johns,Asia/Kathmandu] [--report md|json]
   ```
   310 vectors (`vectors/vectors.json`); each lists its check IDs, and every objective consumer/grammar check has
   one. Buckets: **TOO LENIENT**, **TOO STRICT**, **WRONG VALUE** (returned `fields` differ), **HOST-TZ
   DEPENDENT** (`--tz-matrix`), ADAPTER ERROR; **INTERPRETATION** records choices the RFC allows (Review notes,
   not failures). Route by `RFCDT_PROFILE`; use `--target-kind ixdtf` for a suffix-only parser. `--batch` for
   JVM/.NET/Node. `--report md` prints a findings-table skeleton.
4. **Producers.** Capture real output and validate each string:
   `python3 $S/rfcdt.py check '<string>' [--profile ixdtf] [--leap-seconds …] [--lmt-tolerance nearest|any-sub-minute] --json`.
   Probe with the instants in `references/hotspots.md` (read it before this step). `rfcdt.py adapter` is rfcdt
   as a vector target; `rfcdt.py selfcheck` confirms the leap-second table, calendars and tz release: record it.
5. **Code review.** Read `references/hotspots.md`, `references/ecosystem/README.md` (Top 10, matrix), then only
   the target language's file in `references/ecosystem/`. Also: semantic probes for consumers, schemas without a
   configured validator, and checks the grammar cannot see (string sorting, leap-second mapping, zone vs offset
   on reload).
6. **Report** in the format below.

## Report format

```
# RFC 3339 / RFC 9557 adherence — <target>

Scope: targets <producer|consumer|schema>, profile <rfc3339|ixdtf>, declared options: <...>
Evidence: <tool runs with counts, e.g. scan 412 files (3 skipped) 9 hits; vectors per adapter 140/147 (5 too lenient, 2 too strict, 0 wrong value, 6 interpretation); producer samples 2 invalid of 30; semantic probes 5; selfcheck OK>
Summary: N nonconformities, N deviations, N advisories, N review notes

## Findings
| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |

## Review notes
(ambiguous RFC text and the reading used; INTERPRETATION choices; optional items worth knowing)
## Not run / not applicable
(tools, vectors or roles not run, and why; scan skips)
## Assumptions
(profile, options and tz data assumed where the target does not state them)
## Reproduction
(adapter source, commands, library and tzdata versions, rfcdt/runner versions, selfcheck result)
```

`Ref` = the RFC section (`§5.6`, `9557 §3.3`); `Target` = producer, consumer or schema; `Location` = `file:line`;
`Evidence` = a concrete input → output pair. Report one root cause once and list the other check IDs it breaks in
the same row. Never report a clean result for vectors or checks you did not run.

## Files

| Path | Contents |
|---|---|
| `references/interpretation.md` | Rules 1–5 in full, severity vocabulary, grading vector results |
| `references/hotspots.md` | Producer and semantic probes, schema checks, code hotspots by role, semantic checks |
| `references/tools.md` | `rfcdt.py` (`check`, `adapter`, `scan`, `selfcheck`) and `run_vectors.py`: flags, JSON shapes, buckets |
| `references/check-index.md` | All 109 checks: ID, level, roles, judgment. Filter this first |
| `references/rfc3339-checks.md` | RFC 3339: verbatim ABNF, errata, checks for §1–§7 and App. A–D |
| `references/rfc9557-checks.md` | RFC 9557: consumer decision table, ABNF, checks, examples, erratum, IANA registry |
| `references/ecosystem/` | Probed behaviour per language (Python, JS, Java, .NET, Ruby, Go, Rust, Swift, SQL, protobuf, JSON Schema); `README.md` has the legend, matrix, strict regex, Top 10 |
| `references/servicenow.md` | ServiceNow profile, Glide/REST/Flow/Fluent APIs, Fluent SDK 4.13.0 findings, audit steps |
| `scripts/rfcdt.py`, `scripts/run_vectors.py` | Reference validator and scanner; conformance runner |
| `vectors/vectors.json` | 310 vectors with check IDs, options, `requires`, `fields`, `interpretation` |
| `probes/` | Probe programs behind `ecosystem/` (`inputs.json`; `servicenow/` has its own README) |
| `evals/` | Skill eval harness (plugin-eval cases, trigger prompts, fixtures); see `evals/README.md` |

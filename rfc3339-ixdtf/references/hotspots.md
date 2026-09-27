# Code review hotspots and probes

Read this before step 5 of the SKILL.md workflow (code review), and before step 4 when you probe a producer.
Severity words and "rule N" refer to `interpretation.md`. Library behaviour and safe replacements per language are
in `ecosystem/` (start with `ecosystem/README.md`).

## Producer probes

Capture real output (run the code, or read its test snapshots) and validate each string with
`rfcdt.py check '<string>' [--profile ixdtf] --json`.
Probe the producer with instants that expose bugs:
- a zone with a non-whole-minute historical offset (for example
  `Africa/Monrovia` in 1970 is −00:44:30. Old European LMT offsets change
  between tzdata releases, so check with the target's own tz data)
- a fixed-offset `tzinfo` or zone object with no IANA name (it must not be
  turned into a suffix like `[UTC+05:30]`)
- a year before 1000 and after 9999, and a date before 1583 (Julian-calendar libraries: Swift Foundation,
  `SimpleDateFormat`, Ruby `DateTime`)
- a leap second, if the platform can represent one
- a `th-TH` or `ar-SA` culture or locale (.NET/Java/Swift)
- the last days of December (for `YYYY`)
- whole seconds (a formatter may drop `:00`)
- sub-microsecond precision

## Semantic probes (consumers)

Accept/reject vectors can't catch every defect. For each consumer, also feed
a few valid strings and compare the **resulting instant and tags** with
rfcdt's parse output:
- a year below 100
- a critical offset suffix with trailing junk (`[!+01:00junk]`)
- duplicate elective keys
- a leap second
- a large fractional part

Record these in the report's Evidence line.

## Schemas without a configured validator

If the repository doesn't enforce `format` (no assertion vocabulary, no checker,
no CI step), report that once. Then test any `pattern` keywords directly
with a small adapter (ECMA-262 regex with the `u` flag) against the vectors
for that field's profile. Also check that each field's `format` names the
right production (`date-time`, `date` for `full-date`, `time` for
`full-time`).
See `ecosystem/jsonschema.md` for how each validator turns format assertion on, and for the trailing-newline
leak of `^…$` patterns on Python and .NET (add `"not": {"pattern": "\n"}`).

## Hotspots by role

Read `ecosystem/README.md` (Top 10) and the file for the target's language first. Checks with the highest
yield:

- **Producer:**
  - offset missing (naive or local values serialized)
  - a literal `Z` on local wall time
  - `+0200` without the colon
  - seconds dropped (Java `toString`)
  - space separator
  - offsets with seconds: printed as `+00:09:21` (invalid), or cut to the
    minute with the wall time kept, a **wrong instant** (Go `Format`/`MarshalJSON`,
    chrono `to_rfc3339`/serde, jiff, Temporal; 21–30 s off in the probes)
  - signed or 5-digit years
  - week-year `YYYY`
  - non-invariant culture or calendar
  - lower-case `t`/`z`
  - `+00:00` where `Z` is meant (rule 2)
  - offset time zones copied from the offset
  - Java/Temporal bracket output sent to consumers that expect plain RFC 3339
- **Consumer:**
  - "strict" entry points that are not: Go `time.Parse(time.RFC3339)` and
    `UnmarshalJSON`/`UnmarshalText` (strict checks disabled, issue 54580) accept
    `+24:00`, `+23:60`, `,5` and `T1:00:00Z`; `encoding/json/v2` is the strict
    option. chrono `FromStr`/serde `Deserialize` is far more lenient than
    `parse_from_rfc3339`. The time crate's `Rfc3339` accepts any byte as the
    `T` separator
  - a missing offset silently read as host-local time
  - invalid dates normalized instead of rejected (Feb 30, `T24:00`)
  - leap seconds rejected everywhere, or accepted everywhere
  - `\d` matching non-ASCII digits
  - `$` matching before a trailing newline
  - fractional digits capped at 6 or 9 without a stated limit
  - lower-case `t`/`z` rejected
  - `-00:00` rejected, or read as `+00:00` against a zone (jiff `Zoned`;
    RFC 9557 §2 makes it `Z`)
  - suffixes silently dropped (critical ones included)
  - critical flag ignored
  - all unknown elective tags rejected (Advisory; see rule 4)
  - "last wins" on repeated keys
  - experimental `[_key=…]` accepted without configuration (jiff `Zoned`)
  - instant parsers ignoring a critical zone: `Temporal.Instant.from` and jiff
    `Timestamp::from_str` accept `…+05:00[!Europe/Paris]` and
    `…Z[!Mars/Olympus]`; `ZonedDateTime.from` and jiff `Zoned` reject both
- **Schema:**
  - JSON Schema `format` is annotation-only by default. It needs format
    assertion turned on and a checker (jsonschema needs `rfc3339-validator`;
    ajv needs `ajv-formats` in `full` mode, not `fast`). Even these are
    imperfect (probed): `rfc3339-validator` accepts a trailing `\n`, and
    ajv-formats `full` accepts `+0200` and `:60` on any date. Run the vectors
    through the configured validator instead of trusting its name.
  - `date`/`time` formats map to 3339 productions (erratum 5624).
  - Docs promise "ISO 8601" but mean RFC 3339.
  - The IXDTF profile is not stated where suffixes may appear.
- **ServiceNow** (`references/servicenow.md`; SDK rows probed offline, instance
  rows documented or unverified):
  - `getValue()`/display values sent to integrations; `getValue()+'Z'` is right
    only while `glide.sys.internal.tz` is unset or UTC; display values labelled
    `Z` are a wrong instant
  - ISO input through `new GlideDateTime(s)`/`setValue(s)` or "replace `T` with
    a space" (offset dropped); `sysparm_display_value=true` or
    `sysparm_input_display_value=true` in clients
  - Fluent SDK 4.13.0: `Time()` 60 min early east of UTC and host-zone without
    a zone; host-dependent `ScheduledScript` DST-gap values and durations; years
    0–99 remapped; builds that exit 0 but drop records; cast strings (and NUL)
    written to XML verbatim. Build under several `TZ` values and diff `dist/`
    (`probes/servicenow/`)
- **Other ecosystems probed 2026-09-25** (details in `ecosystem/`):
  - Swift Foundation: parsers ignore trailing text and suffixes, `ISO8601DateFormatter` misreads `+24:00` and
    5-digit years, Julian calendar before 1582, `ISO8601FormatStyle` prints `+0200`, `JSONEncoder()` default is a
    number (`swift.md`)
  - SQL: PostgreSQL `timestamp` drops offsets, `::text` is not RFC 3339, `to_char` with `"Z"`/`OF`/`HH`/`IYYY`;
    SQLite `datetime()` has no offset and rolls Feb 30 over (`sql.md`)
  - protobuf Timestamp: a stated profile (always `Z`, 0/3/6/9 digits, 0001–9999); Python `FromJsonString`
    accepts `+-1:00` (sign inverted) and `.1e-3` (`protobuf.md`)
  - JSON Schema validators and openapi-generator clients (`jsonschema.md`)

## Semantic checks the grammar cannot see

- Sorting as strings (§5.1) is correct only with a fixed offset, fixed precision and
  no suffix. Flag string sorts over mixed offsets or precisions.
- Leap seconds: validate against the offset-adjusted UTC time (§5.7). Say what
  the code maps `:60` to.
- `Z` against `+00:00` meaning on round-trip (rule 2).
- Zone suffix against offset when the tz database changes. Store both, and re-check
  on load.

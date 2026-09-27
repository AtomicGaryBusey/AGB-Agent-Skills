# JSON Schema validators and OpenAPI generated clients: RFC 3339 / RFC 9557 behaviour

Verdict words (**TOO LENIENT**, **TOO STRICT**, **WRONG VALUE**, **WRONG OUTPUT**, lossy, …) are defined in [`README.md`](README.md#how-to-read-the-verdicts). A grep hit is a lead, not a finding: confirm it with the probe input named in the "Why" column.

## Scope and environment (probed 2026-09-25)

**Scope.** Validators that assert JSON Schema `format`. JSON Schema 2020-12 defines `date-time` as RFC 3339 §5.6
`date-time`, `date` as `full-date` and `time` as `full-time` (so `time` needs an offset). A validator
**validates, it does not parse**: it returns accept or reject only. So there is no WRONG VALUE column here. The
verdict is about the grammar alone. Any RFC 9557 suffix is outside `date-time`, so every accepted suffix is
**TOO LENIENT (suffix)**, not "lenient (accepts suffix)" as it is for general parsers.

**Environment.** Same host as the other files: macOS arm64, `TZ=America/New_York`, tzdata 2026c.

| Validator | Version | How format assertion was turned on |
|---|---|---|
| Go `github.com/santhosh-tekuri/jsonschema/v6` | v6.0.3 (Go 1.27.1) | `c := jsonschema.NewCompiler(); c.AssertFormat()` |
| Java `com.networknt:json-schema-validator` | 3.0.7 (+ `com.ethlo.time:itu` 1.14.0, Jackson 3.2.1, JDK Temurin 25.0.1) | `SchemaRegistry.withDefaultDialect(DRAFT_2020_12, b -> b.schemaRegistryConfig(SchemaRegistryConfig.builder().formatAssertionsEnabled(true).build()))` |
| .NET `JsonSchema.Net` | 9.4.0 (.NET SDK 10.0.300, runtime 10.0.8) | `new EvaluationOptions { RequireFormatValidation = true }` |
| Python `jsonschema` | 4.26.0 + `rfc3339-validator` 0.1.4 (from `jsonschema[format]`); Python 3.13.9 | `Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)` |
| openapi-generator (code-generator defaults, section "openapi-generator" below) | `openapi-generator-cli` 7.25.0 | n/a |

Schema under test: `{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"string","format":"date-time"}`
(also `"date"`, `"time"`, a draft-07 variant, and a variant with the strict `pattern`).

networknt picks its `date-time` checker at class-load time: `com.ethlo.time.ITU.parseDateTime` when `itu` is on
the classpath (it is a normal compile dependency, so this is the default), else `java.time.OffsetDateTime.parse`.
Both were probed. The rows marked "no itu" are what you get when `itu` is excluded (for example by a shaded or
`<exclusions>` build).

To re-run: the probe sources are in `probes/jsonschema/` (`go/`, `JsonSchemaProbe.java`, `dotnet/`,
`py_adapter.py`, `probe_all.py`, `extras.json`). Every program is a `run_vectors.py` adapter that takes a variant
name (`assert`, `default`, `draft7`, `date`, `time`, `pattern`, and `pattern-nl` for .NET and Python). Build
commands are in each file's header. `probe_all.py --set date-time|date|time --target 'NAME=CMD' …` prints the
tables below. `extras.json` adds 13 `date-time` inputs to the 59 in `probes/inputs.json` (72 in all), plus 13 `date`
and 19 `time` inputs.

## Format assertion is off by default (2020-12)

Input `"not a date"`. "accepted" means the validator only collected `format` as an annotation.

| Validator | 2020-12, no option | draft-07, no option | 2020-12 + option above |
|---|---|---|---|
| Go santhosh-tekuri v6 | accepted | **rejected** (asserts) | rejected |
| Java networknt 3.0.7 | accepted | **rejected** (asserts) | rejected |
| .NET JsonSchema.Net 9.4.0 | accepted | accepted | rejected |
| Python jsonschema 4.26.0 `[format]` | accepted (no `format_checker`) | accepted (no `format_checker`) | rejected |
| Python jsonschema 4.26.0 without `rfc3339-validator` | accepted | accepted | **accepted** (the checker is silently not registered) |

This confirms the 2020-12 rule (the format-annotation vocabulary: assertion "MUST be disabled by default"; https://json-schema.org/draft/2020-12/json-schema-validation),
which was earlier listed as "unverified (from docs)". Note: moving the same schema from draft-07 to
2020-12 **silently turns off** `date-time` checking in Go and Java.

## At a glance (format assertion on)

Same legend as the README matrix (the first 17 columns are also there). Columns are `inputs.json` IDs, plus `js-plus-hour` = `2026-09-24T+1:00:00Z` and
`js-crlf` = `…Z\r\n` from `extras.json`.

| API | `lc-z` | `space` | `off-minus0` | `off-nocolon` | `no-sec` | `no-off` | `comma` | `h24` | `leap-real` | `leap-fake` | `feb30-2024` | `frac12` | `trail-ws` | `y+10000` | `x-tz` | `x-unk!` | `x-incons!` | `js-plus-hour` | `js-crlf` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| go: santhosh-tekuri/jsonschema/v6 `AssertFormat()` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ |
| java: networknt 3.0.7 (itu, default) | ✓ | **L** | **S** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **S** | **L** | ✓ | ✓ | **L** | ✓ | ✓ | **L** |
| java: networknt 3.0.7 (no itu: `OffsetDateTime.parse`) | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | s | ✓ | ✓ | **S** | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ |
| dotnet: JsonSchema.Net `RequireFormatValidation` | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: jsonschema `FORMAT_CHECKER` + rfc3339-validator | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | s | ✓ | ✓ | ✓ | **L** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| python: jsonschema `FORMAT_CHECKER`, no rfc3339-validator | ✓ | **L** | ✓ | **L** | **L** | **L** | **L** | **L** | ✓ | **L** | **L** | ✓ | **L** | **L** | **L** | **L** | **L** | **L** | **L** |

## Conformance vectors (`run_vectors.py`, vectors.json sha256:4e700dd49a20, 310 vectors)

Flags: `--target-kind rfc3339 --target-options fixed --target-has-tzdata yes`. 147 scored, 6 interpretation
(leap-second months, excluded), 157 skipped (IXDTF-profile and non-default-option vectors). A validator returns no
fields, so the "wrong" column is always 0, and the runner 0.4.0 grading changes (leap-second representation,
fraction rounding) cannot change a row. Adapters: the programs in `probes/jsonschema/`. The Go rows were re-run with
runner 0.4.0 (baseline `evals/baselines/probes/vector-runs/jsonschema.txt`, keys `assert`, `draft7`, `pattern`,
`default`: same counts); the Java, .NET and Python rows are from the 2026-09-25 run with runner 0.3.0 (the re-run host
lacked the jars, the NuGet package and the Python package, so the baseline lists them as skipped).

| Target (adapter variant) | Pass / scored | Too lenient | Too strict | Wrong value |
|---|---|---|---|---|
| Go santhosh-tekuri v6.0.3, `AssertFormat()` | 146/147 (99.3%) | 1 | 0 | 0 |
| same + strict `pattern` | 146/147 | 1 | 0 | 0 |
| same, draft-07 schema | 146/147 | 1 | 0 | 0 |
| same, 2020-12 schema **without** `AssertFormat()` (annotation only) | 59/147 (40.1%) | 88 | 0 | 0 |
| Java networknt 3.0.7, itu 1.14.0 | 127/147 (86.4%) | 11 | 9 | 0 |
| same + strict `pattern` | 138/147 | 0 | 9 | 0 |
| Java networknt 3.0.7, no itu (`OffsetDateTime.parse`) | 123/147 (83.7%) | 8 | 16 | 0 |
| .NET JsonSchema.Net 9.4.0, `RequireFormatValidation` | 143/147 (97.3%) | 4 | 0 | 0 |
| same + strict `pattern` | 145/147 | 2 (`Z\n`, 2016-12-30 `:60`) | 0 | 0 |
| same + `pattern` + `"not":{"pattern":"\n"}` | 146/147 | 1 | 0 | 0 |
| Python jsonschema 4.26.0 + rfc3339-validator 0.1.4 | 133/147 (90.5%) | 1 | 13 | 0 |
| same + `pattern` + `"not":{"pattern":"\n"}` | 134/147 | 0 | 13 | 0 |
| Python jsonschema 4.26.0, no rfc3339-validator (`FORMAT_CHECKER` passed) | 59/147 (40.1%) | 88 | 0 | 0 |
| openapi-generator 7.25.0 C# `DateTimeJsonConverter` (generated code) | 119/147 (81.0%) | 5 | 23 | 0 (not compared) |

The one Go/.NET vector left is `2016-12-30T23:59:60Z`: both check "23:59 UTC" for `:60` but not the date.

## Per-validator results

Each table lists only deviations. The header counts the inputs with the plain verdict "conforming". Full rows: `probes/jsonschema/probe_all.py
--set date-time|date|time` (JSON lines; the run reports were not committed; re-run the probe to regenerate them). Rows are the legacy probe strings (`probes/inputs.json` "legacy"); a vector ID in the verdict cites the vector of the same case, and "legacy probe only" marks a row that no vector covers.

### go: `santhosh-tekuri/jsonschema/v6` `format: date-time` (`AssertFormat()`)

65 of 72 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T23:59:60Z` | accepted | TOO LENIENT (`:60` on any date if it is 23:59 UTC; 3339-5.7-035) |
| `1971-12-31T23:59:60Z` | accepted | interpretation (3339-5.7-045: a leap second before 1972 is an "either" vector; the default IERS-months policy rejects it) |
| `2026-09-24T+1:00:00Z` | accepted | TOO LENIENT (sign in the hour) (legacy probe only: no vector has a signed field) |
| `2026-09-24T-0:00:00Z` | accepted | TOO LENIENT (legacy probe only: no vector has a signed field) |
| `2026-09-24T12:+0:00Z` | accepted | TOO LENIENT (sign in the minute) (legacy probe only: no vector has a signed field) |
| `2026-09-24T12:00:00++2:00` | accepted | TOO LENIENT (sign in the offset hour) (legacy probe only: no vector has a signed field) |
| `2026-09-24T12:00:00+-0:00` | accepted | TOO LENIENT (legacy probe only: no vector has a signed field) |

Cause (`format.go` `validateTime`, v6.0.3): each 2-character field is read with `strconv.Atoi`, which accepts a
leading `+` or `-`. The only guard is `i < 0`, so `+1` and `-0` pass. The leap check is
`s >= 60 && (h != 23 || m != 59)` after the offset shift. It checks the UTC time but not the month. `date` (13/13) uses `time.Parse("2006-01-02")` and is correct. `time` (18/19) accepts
`+1:00:00Z`.

### java: networknt `json-schema-validator` 3.0.7 `format: date-time` (default: itu 1.14.0 on the classpath)

56 of 72 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2026-09-24T12:00:00-00:00` | rejected | TOO STRICT (itu: "Unknown 'Local Offset Convention' date-time not allowed"; RFC 9557 §2 makes `-00:00` equal to `Z`) |
| `2026-09-24T12:00:00+23:59` | rejected | TOO STRICT (itu uses `ZoneOffset`: ±18 h) |
| `2026-09-24T12:00:00.123456789012Z` | rejected | TOO STRICT (more than 9 fraction digits) |
| `2017-01-01T00:59:60+01:00` (vector 3339-5.7-030) | rejected | TOO STRICT (a real leap second at a non-zero offset) |
| `2026-09-24T12:00:00Z\n` · `…Z\r\n` · `…Z\u0000` · `…Z ` · `…ZZ` · `…Z Fri` · `…Z/P1D` | accepted | TOO LENIENT (any text after `Z`) |
| `2026-09-24T12:00:00Z[Europe/Paris]` and the other 7 `Z[…]` suffix inputs (incl. `[!x-foo=bar]`, `[U-CA=hebrew]`) | accepted | TOO LENIENT (suffix) (3339-5.6-062; the other 7: legacy probe only) |
| `1971-12-31T23:59:60Z` | accepted | interpretation (3339-5.7-045, "either"; itu throws `LeapSecondException`; networknt accepts it because `isVerifiedValidLeapYearMonth()` is true for this December) |

Cause: `com.ethlo.time.ITU.parseDateTime` 1.14.0 **stops reading after a `Z` when there is no fraction**. Probed
directly: `…12:00:00Zjunk` gave `2024-01-01T12:00Z`, while `…12:00:00.5Zjunk` and `…+01:00junk` threw "Trailing
junk data". So `…+02:00[Europe/Paris]` is rejected, but `…Z[!Mars/Olympus]` is accepted.
`time` (17/19) accepts `12:00:00.Z` and rejects 12 fraction digits. `date` (12/13) accepts `+002026-09-24`.

### java: networknt 3.0.7 `format: date-time`, itu **not** on the classpath (`OffsetDateTime.parse` fallback)

61 of 72 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00+23:59` | rejected | TOO STRICT (±18 h) |
| `2026-09-24T12:00:00.123456789012Z` | rejected | TOO STRICT |
| `2016-12-31T23:59:60Z` · `2016-12-31T18:59:60-05:00` · `2015-06-30T23:59:60Z` | rejected | too strict (no leap second) |
| `2026-09-24T12:00:00+02` · vectors `+01:00:00`, `-00:44:30`, `+00:09:21` | accepted | TOO LENIENT (`ISO_OFFSET_DATE_TIME` offset forms) |
| `2026-09-24T12:00:00.Z` | accepted | TOO LENIENT (dot with no digits) |
| `2026-09-24T12:00Z` | accepted | TOO LENIENT (no seconds) |
| `+10000-01-01T00:00:00Z` · `+002026-09-24T12:00:00Z` · `-0001-01-01T00:00:00Z` | accepted | TOO LENIENT (signed or expanded year) (3339-5.6-038 `-0001`; `+10000` / `+002026`: legacy probe only) |

The same schema therefore gives **different verdicts depending on the classpath**: one build rejects `-00:00` and
accepts `Z\n`, the other accepts `T12:00Z` and `+02`.

### dotnet: `JsonSchema.Net` 9.4.0 `format: date-time` (`RequireFormatValidation = true`)

68 of 72 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24 12:00:00Z` | accepted | too lenient (space; OK only under a stated profile) (3339-5.6-015) |
| `2024-01-01_12:00:00Z` (vector 3339-5.6-018) | accepted | TOO LENIENT (underscore separator) |
| `2026-09-24T12:00:00Z\n` | accepted | TOO LENIENT (.NET `$` matches before a final `\n`; `\r\n` and `\r` are rejected) |
| `2026-09-24T23:59:60Z` · `2016-12-30T23:59:60Z` · `1971-12-31T23:59:60Z` | accepted | TOO LENIENT (`:60` on any date if it is 23:59 UTC; 3339-5.7-035; the 1971 input is the "either" vector 3339-5.7-045) |

Cause (json-everything `src/JsonSchema/Formats.cs`, current source; it matches the probed behaviour): the regex is
`^(…[0-9]{4}-[0-9]{2}-[0-9]{2})([Tt_]| )(…)([Zz]|[\+-][0-9]{2}:[0-9]{2}))$`. The `_` and space are explicit, and
`$` is used, not `\z`. `date` 13/13 and `time` 19/19 were conforming, including `0000-01-01` and leap seconds.

### python: `jsonschema` 4.26.0 `FORMAT_CHECKER` + `rfc3339-validator` 0.1.4

Re-probed for comparison with the 2026-09-24 row in the README matrix (and `python.md`). It matches: 67 of 72 conforming. Deviations: `…Z\n`
accepted (**TOO LENIENT**, `re` `$`); real leap seconds rejected (too strict (no leap second)); `0000-01-01T00:00:00Z`
rejected (too strict (range limit)). The 13 TOO STRICT vectors are 11 real leap seconds (with `Z`, `z`, `+00:00`,
`-00:00` and non-zero offsets) and 2 year-0000 dates. `time` rejects `23:59:60Z` and `18:59:60-05:00` and accepts `12:00:00Z\n`.
`date` rejects `0000-01-01`.

**Without `rfc3339-validator`** (plain `pip install jsonschema`): 20 of 72 conforming, 88 TOO LENIENT vectors.
Passing `format_checker=` is not enough: `date-time` and `time` are not registered, so every string passes. `date`
is still checked (it uses `datetime.date.fromisoformat` plus a regex, no extra package).

### Adding the strict `pattern` (`README.md`, "Portable strict check")

`"pattern": "^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)([.][0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$"`
next to `format` (assertion on):

| Validator | Effect |
|---|---|
| Go | no change (146/147); RE2 `$` is end of text, and `format` already rejected everything the pattern rejects |
| Java networknt (itu) | all 11 TOO LENIENT fixed (138/147); the 9 TOO STRICT remain, because `format` still rejects `-00:00`, `+23:59`, and >9 digits |
| .NET JsonSchema.Net | `_` and space fixed; **`…Z\n` still accepted** (.NET `$`). Adding `"not": {"pattern": "\n"}` fixes it (146/147) |
| Python jsonschema | **`…Z\n` still accepted** (`re.search` with `$`). Adding `"not": {"pattern": "\n"}` fixes it (134/147) |

JSON Schema says `pattern` is ECMA-262, where `$` without the `m` flag is end of input. But Python and .NET run it
with their own engines, where `$` also matches before a final newline. A pattern that is correct on paper
therefore leaks `\n` on two of four validators.

## openapi-generator 7.25.0: what the generated clients use for `format: date-time`

Generated from a one-model spec (`at: {type: string, format: date-time}`) with the default library of each
generator. The generated code was read. Only the C# converter was run (the others use APIs already probed in the language files).

| Generator (default library) | Generated type / code for `date-time` | Behaviour (from the probes in this file) |
|---|---|---|
| `java` (okhttp-gson) | `OffsetDateTime`; `JSON.OffsetDateTimeTypeAdapter`: rewrites a trailing `+0000` to `Z`, then `OffsetDateTime.parse(s, ISO_OFFSET_DATE_TIME)`; writes `ISO_OFFSET_DATE_TIME.format` | `java.md`, `OffsetDateTime.parse`: `T12:00Z` accepted, >9 digits rejected, `+10000` accepted, and **`+0000` is accepted by design** (only that exact suffix; `+0200` is still rejected). The writer keeps `:00` seconds but trims fraction zeros (`12:00:00.12Z`: variable length; checked on JDK 25) |
| `kotlin` (jvm-okhttp4, moshi) | `java.time.OffsetDateTime`; `OffsetDateTimeAdapter`: `OffsetDateTime.parse(v, ISO_OFFSET_DATE_TIME)` / `ISO_OFFSET_DATE_TIME.format` | same as Java |
| `python` (pydantic v2) | model field `at: datetime` validated by pydantic; `ApiClient.__deserialize_datetime` uses `dateutil.parser.parse` | `python.md`, pydantic `datetime`: `+0200`, `T12:00Z`, `,5` accepted, and **no offset accepted as naive**. dateutil `parse`: very lenient |
| `typescript-fetch` | `Date`; `runtime.ts` `parseDateTime(value) { return new Date(value) }`; `serializeDateTime` = `toISOString()` | `javascript.md`, `Date.parse`: no offset read as **host-local**, `2024-02-30` rolls over; `toISOString` gives `+010000-…` for big years |
| `typescript-axios` | `string` (no parsing) | the value is passed through unchecked |
| `go` | `time.Time` with `json:"at"` | `go.md`, `encoding/json` v1: `+24:00`, `,5`, `T1:00:00Z` accepted (strict mode dead code) |
| `rust` (reqwest) | `chrono::DateTime<chrono::FixedOffset>` via serde | `rust.md`, chrono serde: 22 invalid forms accepted (`+0100`, trailing `\n`, 1-digit fields) |
| `csharp` (generichost) | **`DateTime`** (not `DateTimeOffset`); `Client/DateTimeJsonConverter`: `DateTime.TryParseExact` over 16 formats with `AdjustToUniversal \| AssumeUniversal`; writes `yyyy'-'MM'-'dd'T'HH':'mm':'ss'.'fffffffK` | **probed**, see below |

C# generated `DateTimeJsonConverter` (vectors 119/147; 5 TOO LENIENT, 23 TOO STRICT):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T12:00:00` | accepted → 12:00:00Z | TOO LENIENT (no offset read as **UTC** by `AssumeUniversal`) |
| `20260924T120000Z` | accepted | TOO LENIENT (basic format is in the format list) |
| `2026-09-24T12:00:00+0200` · `…+1:00` · `﻿…Z` | accepted | TOO LENIENT |
| `2026-09-24T12:00:00z` · `2026-09-24t12:00:00Z` | rejected (`NotSupportedException`) | TOO STRICT |
| `2026-09-24T12:00:00.123456789Z` (and any >7 digits) | rejected | TOO STRICT |
| `+23:59`, year `0000`, every `:60` | rejected | TOO STRICT (platform limits) |
| writer, `DateTime` with `Kind=Unspecified` | `"2026-09-24T12:00:00.0000000"` | **WRONG OUTPUT** (no offset; `K` prints nothing) |
| writer, `Kind=Local` (New York) | `"2026-09-24T08:00:00.0000000-04:00"` | conforming |
| writer, `Kind=Utc` | `"2026-09-24T12:00:00.0000000Z"` | conforming |

Not run: other generator libraries (`java` `native`/`resttemplate`/`webclient` use Jackson `JavaTimeModule`,
`python-pydantic-v1`, `typescript-angular`), and the server generators. Those are **unverified**.

## Detect in code

`rfcdt.py scan` flags `format: date-time` in `.json`/`.yaml`/`.yml` schemas (`SCAN-SCHEMA-DATE-TIME`) as a lead to
check how format assertion is configured.

ERE patterns for `rg -n -e` / `grep -nE`. A hit is a lead: confirm it with the input named in "Why".

| Grep | Why (probed) | Safer replacement |
|---|---|---|
| `"\$schema":\s*"https://json-schema\.org/draft/(2020-12\|2019-09)` together with `"format":\s*"date(-time)?"` or `"time"` and no assertion option in the validator setup | Format is an annotation by default in 2020-12. All four validators accepted `"not a date"`. Go and networknt assert under draft-07, so an upgrade to 2020-12 silently drops the check | turn assertion on (rows below), or add `pattern` and `"not":{"pattern":"\n"}` so the schema is safe under any validator |
| Go: `jsonschema\.NewCompiler\(\)` without `\.AssertFormat\(\)` nearby | no `date-time` check under 2020-12 | `c.AssertFormat()` |
| Go: `santhosh-tekuri/jsonschema/v[56]` with `format` `date-time`/`time` | accepts `T+1:00:00Z`, `++2:00`, `+-0:00` (`strconv.Atoi` signs) and `:60` on any date | add the strict `pattern` (RE2 `$` is safe), or check with a strict parser after validation |
| Java: `SchemaRegistry\.withDefaultDialect\|JsonSchemaFactory\.getInstance` without `formatAssertionsEnabled\(true\)\|setFormatAssertionsEnabled\(true\)` | no check under 2020-12 | `SchemaRegistryConfig.builder().formatAssertionsEnabled(true)` |
| Java: `com\.networknt:json-schema-validator` · `ITU\.parseDateTime` · `com\.ethlo\.time` | itu 1.14.0 accepts **any text after `Z`** (`Z\n`, `Z\u0000`, `Z[!x-foo=bar]`, `ZZ`, `Z/P1D`) and rejects `-00:00` and `+23:59`. Without itu the fallback accepts `T12:00Z`, `+02`, `+10000` | add the strict `pattern` (it fixed all 11 lenient vectors); pin whether itu is on the classpath, because the verdicts differ |
| .NET: `JsonSchema\.FromText\|JsonSchema\.FromFile\|\.Evaluate\(` without `RequireFormatValidation\s*=\s*true` | no check (2020-12 **and** draft-07) | `new EvaluationOptions { RequireFormatValidation = true }` |
| .NET: `JsonSchema\.Net` with `date-time` | accepts `_` and space separators, `Z\n`, and `:60` on any date | `pattern` + `"not":{"pattern":"\n"}` |
| Python: `jsonschema` in requirements without `jsonschema\[format\]\|rfc3339-validator` · `format_checker=` not passed to `validate\|Draft\w*Validator\(` | without the package, `date-time`/`time` pass **everything** even with `FORMAT_CHECKER`; without `format_checker=`, nothing is checked | depend on `jsonschema[format]` (or `rfc3339-validator`) and pass `format_checker=Draft202012Validator.FORMAT_CHECKER` |
| Python / .NET: a `"pattern"` ending in `\$"` used as the strict gate | `$` matches before a final `\n` in Python `re` and .NET, so `…Z\n` passes | add `"not": {"pattern": "\n"}` (portable; RE2 has no lookahead) |
| openapi C#: `DateTimeJsonConverter` · `AssumeUniversal` · `public DateTime \w+ \{ get` in `Model/` | no-offset input read as UTC; `Kind=Unspecified` written without an offset; `t`/`z` and >7 digits rejected | generator option `useDateTimeOffset=true` (documented, default false; not probed), and validate with the strict regex |
| openapi TS: `parseDateTime\(value: any\)` · `return new Date\(value\)` in `runtime.ts` | `Date.parse`: no offset → host-local time, `2024-02-30` rolls over | validate with the strict regex before `new Date` |
| openapi Java/Kotlin: `OffsetDateTime\.parse\(date, formatter\)` · `endsWith\("\+0000"\)` | accepts `T12:00Z`, `+10000-…` and `+0000`; `ISO_OFFSET_DATE_TIME.format` trims fraction zeros (variable length) | strict regex before parse; a fixed-width pattern such as `uuuu-MM-dd'T'HH:mm:ss.SSSXXX` if the contract needs sortable strings |
| openapi Python: `from dateutil\.parser import parse` in `api_client\.py` · pydantic `datetime` fields | accepts almost anything; a missing offset gives a naive value | `AwareDatetime` + the strict regex in a validator |

### Schemas and contracts in general (2026-09-24)

| Grep | Why | Safer replacement |
|---|---|---|
| `"format":\s*"date-time"` · `format: date-time` | In JSON Schema 2020-12, `format` is an annotation by default. Validators assert it only when you enable it (see above). Probed validators still differ: ajv-formats accepts `+0200` and `:60` on any date (`javascript.md`), and rfc3339-validator accepts a trailing `\n` (`python.md`). | add `"pattern"` with the strict regex (anchored `^…$`, `[0-9]`) plus `"not": {"pattern": "\n"}`, and turn format assertion on |
| `x-.*timezone\|\[.*\]` in examples for IXDTF fields | Many consumers reject suffixes (every RFC 3339-only parser), and Java rejects `!` and tags | document whether a suffix is allowed and whether critical tags are allowed |

ajv / ajv-formats (Node) rows are in `javascript.md`; python-jsonschema without its extra is also in `python.md`.

## Top defects (JSON Schema and generated clients)

1. **Format is not checked at all, silently.** JSON Schema 2020-12 makes `format` an annotation by default, and all
   four validators follow it. Go and networknt assert under draft-07, so moving a schema to 2020-12 turns the check
   off with no error. python-jsonschema without `rfc3339-validator` does not check `date-time` even when you pass
   `FORMAT_CHECKER` (88 of 147 vectors TOO LENIENT). .NET needs `RequireFormatValidation` even for draft-07.
2. **networknt + itu accepts any text after `Z`.** `ITU.parseDateTime` (itu 1.14.0, the default dependency) stops
   after `Z` when there is no fraction. So `…Z\n`, `…Z\u0000`, `…ZZ`, `…Z Fri`, `…Z/P1D` and every `Z[…]` suffix
   (including critical `[!x-foo=bar]` and `[!Mars/Olympus]`) pass. The same parser rejects `-00:00` (valid, and
   equal to `Z` per RFC 9557 §2) and `+23:59`.
3. **Verdicts depend on the classpath.** Without itu, networknt falls back to `OffsetDateTime.parse`: `T12:00Z`,
   `+02`, `.Z`, `+10000-…` and `-0001-…` pass, and real leap seconds are rejected.
4. **Go santhosh-tekuri v6 accepts signed fields.** `strconv.Atoi` reads `+1`, `-0`, `+2`: `T+1:00:00Z`,
   `T12:+0:00Z`, `…++2:00`, `…+-0:00` are all "valid" `date-time` (also `time`: `+1:00:00Z`). These inputs are not
   in `vectors.json` (146/147 there). Add them to the vector set.
5. **Trailing newline passes, even with a `pattern`.** rfc3339-validator, JsonSchema.Net and networknt+itu accept
   `…Z\n`. A strict `^…$` pattern does not help on Python or .NET, because their `$` matches before a final `\n`.
   `"not": {"pattern": "\n"}` fixes it on every validator probed.
6. **Leap seconds: no validator does the §5.7 month check.** Go and .NET accept `:60` at 23:59 UTC on any date
   (`2026-09-24`, `2016-12-30`; 3339-5.7-035). `1971-12-31T23:59:60Z` is an "either" vector (3339-5.7-045: before
   1972), not a finding. networknt+itu rejects most fake dates but accepts `1971-12-31` and
   rejects a real one at `+01:00`. rfc3339-validator and the `OffsetDateTime` fallback reject every `:60`.
7. **Separator leniency.** JsonSchema.Net's regex allows `_` and a space (`[Tt_]| `); networknt+itu allows a space.
   Both are too lenient for a `date-time` check: the space is outside the ABNF and is allowed only under a stated
   application profile (§5.6 NOTE; erratum 5783 is Held), which JSON Schema `date-time` does not state (3339-5.6-015);
   `_` is outside the RFC in every case (3339-5.6-018).
8. **Generated clients do not share the schema's `date-time`.** openapi-generator 7.25.0 defaults: C# maps to
   `DateTime` with `AssumeUniversal` (no-offset input read as UTC; `Unspecified` values written with **no offset**;
   `z`/`t` and >7 fraction digits rejected), TypeScript uses `new Date(value)` (host-local for no offset), Go uses
   `encoding/json` v1 (`+24:00` accepted), Rust uses chrono serde (22 invalid forms), Python uses pydantic/dateutil.
   A server that validates with a strict schema can still receive, or emit, what these clients produce.

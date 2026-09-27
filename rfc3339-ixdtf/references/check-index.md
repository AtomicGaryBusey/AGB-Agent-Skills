# Check index

Generated from the two check catalogs. Filter by Roles (producer / consumer / schema), then open the catalog for Detect tactics and test inputs.

| ID | Check | Level | Roles | Judgment | File |
|---|---|---|---|---|---|
| R3339-1-01 | Years 0000–9999 are in scope; no expanded or negative years | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-1-02 | Every timestamp has a stated UTC relationship | informative | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-1-03 | Timestamps before UTC existed are allowed | informative | consumer, schema | heuristic | rfc3339-checks.md |
| R3339-1-04 | Instants only; intervals, durations and periods are out of scope | informative | schema, consumer | objective | rfc3339-checks.md |
| R3339-2-01 | Leap-year definition is Gregorian (4 / 100 / 400) | informative | producer, consumer | objective | rfc3339-checks.md |
| R3339-2-02 | "Z" denotes a UTC offset of 00:00 — UPDATED BY RFC 9557 §2.2 | informative (definition) | consumer, producer | objective | rfc3339-checks.md |
| R3339-2-03 | A minute can have 59, 60 or 61 seconds | informative | consumer | heuristic | rfc3339-checks.md |
| R3339-3-01 | Generate four-digit years | MUST | producer | objective | rfc3339-checks.md |
| R3339-3-02 | Two-digit years are deprecated; accept only if misinterpretation is harmless | informative | consumer | heuristic | rfc3339-checks.md |
| R3339-3-03 | Robust handling of 3-digit "year − 1900" output | informative (lower-case "may") | consumer | heuristic | rfc3339-checks.md |
| R3339-3-04 | Robust handling of non-numeric decades (":0", ";0") | informative (lower-case "should") | consumer | heuristic | rfc3339-checks.md |
| R3339-3-05 | Dates and times used in Internet protocols must be fully qualified | MUST | producer, schema | objective | rfc3339-checks.md |
| R3339-4.1-01 | Prefer UTC; no local-time-zone rules in the format | informative | producer, schema | heuristic | rfc3339-checks.md |
| R3339-4.2-01 | Offsets are numeric; alphabetic zone labels are not allowed (except Z) | informative (grammar — definitional) | producer, consumer | objective | rfc3339-checks.md |
| R3339-4.2-02 | Offset sign: offset = local − UTC; UTC = local − offset | informative | producer, consumer | objective | rfc3339-checks.md |
| R3339-4.2-03 | Offsets are whole minutes; sub-minute historical offsets must be converted | informative | producer, consumer | objective | rfc3339-checks.md |
| R3339-4.3-01 | "-00:00" = UTC known, local offset unknown — UPDATED BY RFC 9557 §2.2 | informative | producer, consumer, schema | editorial | rfc3339-checks.md |
| R3339-4.3-02 | Consumers must accept "-00:00" syntactically and as a UTC instant | informative (grammar — definitional) | consumer, schema | objective | rfc3339-checks.md |
| R3339-4.3-03 | Keep the Z vs +00:00 (vs -00:00) distinction when you re-serialise — UPDATED BY RFC 9557 §2.2/§2.3 | informative | producer, consumer | heuristic | rfc3339-checks.md |
| R3339-4.4-01 | Local-clock systems that sync with others MUST use a UTC-correct mechanism | MUST | producer | heuristic | rfc3339-checks.md |
| R3339-4.4-02 | A gateway host MUST correct unqualified local times it forwards | MUST | producer | heuristic | rfc3339-checks.md |
| R3339-4.4-03 | Never emit unqualified local time or append Z to local time | informative | producer | objective | rfc3339-checks.md |
| R3339-5.1-01 | Lexical sort equals time order only under stated conditions (errata 293) | informative | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.1-02 | Producers intended for sortable output use a canonical form | informative | producer | objective | rfc3339-checks.md |
| R3339-5.2-01 | Clients should transform timestamps for local display | SHOULD | consumer | heuristic | rfc3339-checks.md |
| R3339-5.2-02 | Never use locale-dependent or ctime-style formats on the wire | informative | producer, schema | objective | rfc3339-checks.md |
| R3339-5.3-01 | Fractional seconds is the one optional part; consumers must handle it | informative (grammar — definitional) | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.3-02 | Emit fractional seconds only when ordering/precision needs them | informative (lower-case "should") | producer, schema | heuristic | rfc3339-checks.md |
| R3339-5.4-01 | Do not include redundant fields (day of week) | informative (lower-case "should") | producer, schema, consumer | objective | rfc3339-checks.md |
| R3339-5.5-01 | Only the §5.6 profile: full extended format, mandatory punctuation, no other ISO 8601 forms | informative (grammar — definitional) | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-01 | The profile SHOULD be used in new protocols | SHOULD | schema | editorial | rfc3339-checks.md |
| R3339-5.6-02 | date-fullyear: exactly 4 ASCII digits | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-03 | date-month: exactly 2 digits, 01–12 | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-04 | date-mday: exactly 2 digits, 01–28/29/30/31 by month/year | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-05 | time-hour: exactly 2 digits, 00–23 | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-06 | time-minute: exactly 2 digits, 00–59 | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-07 | time-second: exactly 2 digits, mandatory | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-08 | time-secfrac: "." then one or more digits, unbounded length | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-09 | time-numoffset: sign, 2-digit hour 00–23, colon, 2-digit minute 00–59 | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-10 | time-offset is mandatory in full-time / date-time | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-11 | date-time uses a single "T" separator between full-date and full-time | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-12 | Consumers accept lower-case "t" and "z" (ABNF case-insensitivity) | informative | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-13 | Producers SHOULD emit upper-case "T" and "Z" | SHOULD | producer | objective | rfc3339-checks.md |
| R3339-5.6-14 | Specs in case-sensitive contexts MAY require upper-case T/Z | MAY | schema, consumer | editorial | rfc3339-checks.md |
| R3339-5.6-15 | Space separator: allowed only as a documented application choice (errata 5783) | informative | producer, consumer, schema | heuristic | rfc3339-checks.md |
| R3339-5.6-16 | The whole string must match; no surrounding white space or trailing data | informative (grammar — definitional) | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-17 | DIGIT is ASCII 0–9 only | informative (grammar — definitional) | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.6-18 | Sub-productions (full-date, partial-time, full-time) are legitimate on their own (errata 5624) | informative | schema, consumer | objective | rfc3339-checks.md |
| R3339-5.6-19 | Hyphen and colon separators are mandatory and exact | informative (grammar — definitional) | consumer, producer | objective | rfc3339-checks.md |
| R3339-5.7-01 | Day-of-month maximum by month and year | informative | consumer, schema, producer | objective | rfc3339-checks.md |
| R3339-5.7-02 | Leap-year computation (Appendix C) for February 29 | informative (grammar — definitional) | consumer, producer | objective | rfc3339-checks.md |
| R3339-5.7-03 | time-second "60" is valid at a positive leap second | informative (grammar — definitional) | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.7-04 | Leap second position shifts with the offset | informative (grammar — definitional) | consumer, producer | objective | rfc3339-checks.md |
| R3339-5.7-05 | Negative leap second: maximum second "58" | informative (grammar — definitional) | consumer, producer | heuristic | rfc3339-checks.md |
| R3339-5.7-06 | Leap seconds happen at the end of a month (not only June/December) | informative | consumer | heuristic | rfc3339-checks.md |
| R3339-5.7-07 | Do not generate leap-second timestamps before they are announced | informative (lower-case "should") | producer | heuristic | rfc3339-checks.md |
| R3339-5.7-08 | Hour "24" is not allowed | informative (grammar — definitional) | producer, consumer, schema | objective | rfc3339-checks.md |
| R3339-5.7-09 | Parsing ":60" must not corrupt the instant | informative | consumer | heuristic | rfc3339-checks.md |
| R3339-5.8-01 | All §5.8 examples parse with the stated meaning | informative | consumer, schema | objective | rfc3339-checks.md |
| R3339-5.8-02 | The fraction is part of the seconds value (no fraction semantics beyond decimal) | informative | consumer | objective | rfc3339-checks.md |
| R3339-7-01 | Emitting a local offset discloses location/work-hours information | informative (lower-case "may wish") | producer | editorial | rfc3339-checks.md |
| R3339-A-01 | Appendix A is not the RFC 3339 grammar | informative | consumer, schema | objective | rfc3339-checks.md |
| R3339-A-02 | No mixing of basic and extended format (errata 1584) | informative | consumer | objective | rfc3339-checks.md |
| R3339-A-03 | Fraction digits always follow a full 2-digit seconds field (errata 4110) | informative | consumer | objective | rfc3339-checks.md |
| R3339-A-04 | Durations and periods are not RFC 3339 date-times | informative | schema | editorial | rfc3339-checks.md |
| R3339-B-01 | Zeller-based sample is valid only on/after 0000-03-01 | informative | producer, consumer | objective | rfc3339-checks.md |
| R3339-B-02 | If a weekday is also present, it must agree with the date | informative | consumer | heuristic | rfc3339-checks.md |
| R3339-C-01 | leap_year() requires a full 4-digit year | informative | consumer, producer | objective | rfc3339-checks.md |
| R3339-D-01 | The Appendix D table is stale; use a maintained source | informative | consumer | objective | rfc3339-checks.md |
| R3339-D-02 | A leap second is the same instant in every offset | informative | consumer, producer | objective | rfc3339-checks.md |
| R3339-D-03 | The first leap second in the table is 1972-06-30 | informative | consumer | objective | rfc3339-checks.md |
| R9557-2-01 | `Z` means "UTC known, local offset unknown" (updated RFC 3339 §4.3) | informative | producer, consumer, schema | heuristic | rfc9557-checks.md |
| R9557-2-02 | `+00:00` semantics unchanged | informative | producer, consumer | heuristic | rfc9557-checks.md |
| R9557-2-03 | Prefer `Z` over `-00:00`; do not reject `-00:00` | informative | producer, consumer | objective | rfc9557-checks.md |
| R9557-1.2-01 | Do not synthesize an offset time zone from the offset | MUST NOT | producer | heuristic | rfc9557-checks.md |
| R9557-1.2-02 | Offset time zone must repeat the timestamp's offset | informative | consumer, producer | objective | rfc9557-checks.md |
| R9557-1.1-01 | The suffix is fully optional (backward compatibility) | informative (grammar consequence) | consumer, schema | objective | rfc9557-checks.md |
| R9557-1.1-02 | IXDTF is still a fixed instant (no floating or zone-only time) | informative (scope) | consumer, producer, schema | objective | rfc9557-checks.md |
| R9557-3.1-01 | Keys are lowercase only | informative (grammar; objective reject) | producer, consumer | objective | rfc9557-checks.md |
| R9557-3.1-02 | Values are case-sensitive unless the key's spec says otherwise | informative | consumer | heuristic | rfc9557-checks.md |
| R9557-3.2-01 | Experimental (`_`) keys: never interchanged, rejected unless configured | MUST NOT | producer, consumer | objective | rfc9557-checks.md |
| R9557-3.2-02 | Keys used should be registered (or experimental) | informative | producer | heuristic | rfc9557-checks.md |
| R9557-3.3-01 | Suffix tags are optional for producers | informative | producer, consumer, schema | heuristic | rfc9557-checks.md |
| R9557-3.3-02 | Elective tags: the recipient may ignore unknown or unusable tags | informative | consumer | heuristic | rfc9557-checks.md |
| R9557-3.3-03 | Critical unknown key or unprocessable value: MUST NOT act, MUST treat as erroneous | MUST NOT | consumer | objective | rfc9557-checks.md |
| R9557-3.3-04 | Critical flag is a single `!` directly after `[` | informative (grammar; objective reject) | consumer, producer | objective | rfc9557-checks.md |
| R9557-3.3-05 | Duplicate elective keys: use the first occurrence | MUST | consumer | objective | rfc9557-checks.md |
| R9557-3.3-06 | Duplicate key where any occurrence is critical: erroneous | MUST | consumer | objective | rfc9557-checks.md |
| R9557-3.3-07 | Extra processing of elective tags is allowed | MAY | consumer | editorial | rfc9557-checks.md |
| R9557-3.4-01 | Offset/zone inconsistency with a critical zone: MUST act | MUST | consumer | objective | rfc9557-checks.md |
| R9557-3.4-02 | Offset/zone inconsistency with an elective zone: MAY act | MAY | consumer | heuristic | rfc9557-checks.md |
| R9557-3.4-03 | `Z` / `-00:00` with a zone is never inconsistent | informative | consumer | objective | rfc9557-checks.md |
| R9557-3.4-04 | Producers must not emit offset/zone combinations they know to be inconsistent | informative | producer | heuristic | rfc9557-checks.md |
| R9557-4.1-01 | Only after a full `date-time` | informative (grammar; objective reject) | consumer, producer, schema | objective | rfc9557-checks.md |
| R9557-4.1-02 | Time-zone element: at most one, and it must come first | informative (grammar; objective reject) | consumer, producer | objective | rfc9557-checks.md |
| R9557-4.1-03 | Time-zone name syntax | informative (grammar; objective reject) | consumer, producer | objective | rfc9557-checks.md |
| R9557-4.1-04 | No 14-character limit on time-zone-part in syntax | informative ("deliberately permissive") | consumer | heuristic | rfc9557-checks.md |
| R9557-4.1-05 | Offset time zone in brackets uses `time-numoffset` only | informative (grammar) | consumer, producer | objective | rfc9557-checks.md |
| R9557-4.1-06 | Unknown zone name: treat as inconsistency | informative | consumer | objective | rfc9557-checks.md |
| R9557-4.1-07 | Suffix key syntax | informative (grammar; objective reject) | consumer, producer | objective | rfc9557-checks.md |
| R9557-4.1-08 | Suffix value syntax | informative (grammar; objective reject) | consumer, producer | objective | rfc9557-checks.md |
| R9557-4.1-09 | No whitespace, no empty brackets, nothing after the last `]` | informative (grammar; objective reject) | consumer, producer | objective | rfc9557-checks.md |
| R9557-4.1-10 | Schema contracts: IXDTF is not JSON Schema `date-time` | informative | schema | heuristic | rfc9557-checks.md |
| R9557-5-01 | `u-ca` values are Unicode Calendar Identifiers | informative (defines the value set) | consumer, producer | objective | rfc9557-checks.md |
| R9557-5-02 | `u-ca` affects presentation, not the instant | informative | consumer | objective | rfc9557-checks.md |
| R9557-6-01 | Registry entries: key identifier must conform to `suffix-key` | informative (registration procedure) | schema (key tables or enums in code and docs) | objective | rfc9557-checks.md |
| R9557-7.1-01 | Data minimization in suffixes | informative | producer | editorial | rfc9557-checks.md |
| R9557-7.2-01 | Parser hardening for the extended syntax | informative | consumer | heuristic | rfc9557-checks.md |
| R9557-7.3-01 | Security-relevant timestamps: only extensions with shared inconsistency resolution | informative | consumer, producer, schema | heuristic | rfc9557-checks.md |

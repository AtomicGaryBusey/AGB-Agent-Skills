# R9557 — RFC 9557 (IXDTF) check catalog

Source: `rfc/rfc9557.txt` (RFC 9557, Standards Track, April 2024, "Date and Time on the Internet: Timestamps with Additional Information"; **Updates: 3339**).
Errata: `rfc/errata9557.html` (one erratum, 8192, **Rejected**; see "Errata").
IANA registry: fetched live 2026-09-24 (see "IANA registry snapshot").

Quotes are from the RFC text with section citations (IETF Trust, BCP 78). BCP 14 keywords are recorded exactly as written. Lowercase "should"/"may" in the RFC are **not** BCP 14 keywords and are recorded as `informative`.

---

## Section summary

- **§1 / §1.1 Scope:** IXDTF adds an optional bracketed suffix to an RFC 3339 `date-time`. The result is still a fixed instant referenced to UTC. Out of scope: future local time that moves with zone rule changes, "floating" time without an offset, and non-UTC timescales (for example TAI).
- **§1.2 Definitions:** Defines UTC, Z, Time Zone, IANA Time Zone, and Offset Time Zone. Contains one normative sentence: programs MUST NOT copy the timestamp's UTC offset into an offset time zone suffix just to satisfy a consumer that requires a suffix.
- **§2 Update to RFC 3339:** Changes RFC 3339 §4.3. **`Z` now means the same as `-00:00`**: "the time in UTC is known, but the offset to local time is unknown". `+00:00` keeps its meaning: UTC is the preferred reference point. `-00:00` is not deprecated, but Z "should now be used in its place" (§2.3; lowercase "should").
- **§3.1 Format:** A suffix is made of tags. Each tag is `key=value`, and the value is one or more items joined by `-`. "Keys are lowercase only. Values are case-sensitive unless otherwise specified."
- **§3.2 Registration:** Registry fields. Keys that start with `_` are experimental. They cannot be registered, "MUST NOT be used for interchange and MUST be rejected by implementations not specifically configured to take part in such an experiment."
- **§3.3 Elective vs critical:** Tags are optional to generate and elective by default, so a recipient may ignore them. With `!` a tag is critical: the recipient "MUST NOT act on the IXDTF string unless it can process the suffix tag as specified". An inconsistent or unrecognized critical tag makes the string erroneous: "the application MUST reject the data or perform some other error handling". Duplicate elective keys: when the application does not do extra processing, it "MUST choose the first suffix that has that key".
- **§3.4 Offset vs time zone:** When the offset and the zone disagree, a critical zone means the application "MUST act on the inconsistency", and an elective zone means it "MAY act on the inconsistency". `Z` (and `-00:00`) never conflicts with a zone, because it asserts no local offset.
- **§4.1 ABNF:** The grammar, `date-time-ext = date-time suffix`. At most one time-zone element, and it comes first. Keys follow `[a-z_][a-z0-9_-]*`. Values are ASCII alphanumerics separated by `-`. Time-zone parts may not be `.` or `..`. There is deliberately no 14-character limit on a part.
- **§4.2 Examples:** Figures 4–7.
- **§5 u-ca:** The `u-ca` key names the calendar in which the date/time is "preferably presented". Its values are Unicode Calendar Identifiers (UTS #35).
- **§6 IANA:** The "Timestamp Suffix Tag Keys" registry, in the "Internet Date/Time Format" group. Permanent entries need Specification Required; Provisional entries need Expert Review. Initial entry: `u-ca`.
- **§7 Security:** Excessive disclosure (data minimization), parser vulnerabilities (nothing unusual), and inconsistent data in security contexts.

---

## Consumer obligations: decision table (core of this catalog)

| Situation | Elective tag (no `!`) | Critical tag (`!`) | Source |
|---|---|---|---|
| Syntax does not match `date-time-ext` | Not IXDTF: **reject** (objective grammar failure) | same | §4.1 |
| Key starts with `_` (experimental), recipient not configured for the experiment | **MUST reject**, even without `!` | **MUST reject** | §3.2 |
| Unknown/unregistered key, or known key whose value cannot be acted on | Free to ignore. MAY do extra processing | **MUST NOT act on the string.** MUST treat it as erroneous: reject or do other error handling | §3.3 |
| Offset conflicts with the time-zone suffix (numeric offset, **not** Z / -00:00) | MAY act (reject, resolve, ask the user) or ignore it and use the RFC 3339 part | **MUST act on the inconsistency** (reject, or resolve by user input or programmed behaviour) | §3.3, §3.4 |
| Offset time zone `[+hh:mm]` differs from the timestamp offset | Inconsistent, so same as the row above | same as the row above | §1.2, §3.4 |
| `Z` or `-00:00` with a zone | **Not** an inconsistency. The local offset is derived from the zone rules | Not an inconsistency, but the recipient must be able to process the zone (it must know the name) | §3.3 note, §3.4 Fig. 2 |
| Zone name unknown to the local TZDB | Treat "as any other inconsistency" (lowercase *should*), so it may be ignored | Cannot process a critical tag, so erroneous (MUST reject or do error handling) | §4.1, §3.3 |
| Same key repeated, all elective | Either do extra processing, or **MUST use the first occurrence** | n/a | §3.3 |
| Same key repeated with conflicting values, any occurrence critical | n/a | Erroneous. MUST reject or do error handling (both orders are shown in §3.3) | §3.3 |

Note: "reject **or** perform some other error handling" means that rejecting is not the only conforming result for a critical failure. **Silently accepting the string and using its value as if nothing were wrong is non-conforming.**

---

## Checks

### R9557-2-01 — `Z` means "UTC known, local offset unknown" (updated RFC 3339 §4.3)
- **Section:** §2.2 (updates RFC 3339 §4.3)
- **Level:** informative (semantic redefinition; the revised text uses "can be represented", not a BCP 14 keyword)
- **Roles:** producer, consumer, schema
- **Requirement:** "If the time in UTC is known, but the offset to local time is unknown, this can be represented with an offset of "Z"." This "differs semantically from an offset of +00:00, which implies that UTC is the preferred reference point". Before RFC 9557, RFC 3339 grouped Z with +00:00. After RFC 9557, Z is grouped with -00:00.
- **Detect:**
  - *Producer:* find code that emits `+00:00` for an unknown or absent local offset. Examples: `strftime('%z')` on a value converted to UTC for storage, and `isoformat()` on an aware UTC datetime, which gives `+00:00`. Also find code that emits `Z` when the local offset is known and meaningful. Grep: `isoformat\(`, `%z`, `"+00:00"`, `replace("+00:00","Z")`, `ToString("o")`, `ISO_OFFSET_DATE_TIME`.
  - *Consumer:* check whether the code attaches different meaning to Z and +00:00, for example "display in UTC" versus "display in the viewer's local time". Under RFC 9557 a Z timestamp gives no preference for UTC display.
  - *Schema/docs:* find text such as "Z indicates the time is in UTC (the preferred zone)". Flag it as outdated relative to RFC 9557.
- **Test inputs:** `2022-07-08T00:14:07Z` means an instant with an unknown local offset. `2022-07-08T00:14:07+00:00` means an instant with UTC as the intended local reference.
- **Judgment:** heuristic

### R9557-2-02 — `+00:00` semantics unchanged
- **Section:** §2.3
- **Level:** informative
- **Roles:** producer, consumer
- **Requirement:** "the semantics of the local offset +00:00 is not updated; this retains the implication that UTC is the preferred reference point". Code that normalizes `+00:00` to `Z` (or `Z` to `+00:00`) loses this distinction.
- **Detect:** Look for normalization when re-serializing: `.replace('+00:00', 'Z')`, `toISOString()` applied to a value parsed from `+00:00`, and formatter options such as `XXX` versus `xxx` in Java (`XXX` prints `Z` for a zero offset). Flag this only where the code claims to round-trip RFC 3339/9557 semantics.
- **Test inputs:** A round-trip of `2022-07-08T00:14:07+00:00` that returns `...Z` loses meaning (heuristic finding). A round-trip of `...Z` that returns `...+00:00` adds a UTC preference that the input did not state.
- **Judgment:** heuristic

### R9557-2-03 — Prefer `Z` over `-00:00`; do not reject `-00:00`
- **Section:** §2.3, §3.4 (last paragraph)
- **Level:** informative (lowercase "should now be used"; "the present specification does not formally deprecate this syntax")
- **Roles:** producer, consumer
- **Requirement:** Producers should emit `Z`, not `-00:00`, for "offset unknown", because ISO 8601:2000 and later do not allow `-00:00`. Consumers of RFC 3339/IXDTF must still accept `-00:00`: it matches `time-numoffset` and is not deprecated. It has the same meaning as `Z`.
- **Detect:** *Producer:* grep for a literal `-00:00`. *Consumer:* feed `-00:00` and confirm that it parses and is treated like `Z` (in particular, with no inconsistency against a zone suffix, see R9557-3.4-03). Parsers built on an ISO 8601 library often reject `-00:00`, or turn it into `+00:00` and lose the meaning.
- **Test inputs:** `2022-07-08T00:14:07-00:00` is valid and means the same as Z. `2022-07-08T00:14:07-00:00[Europe/London]` is valid and consistent.
- **Judgment:** objective (consumer acceptance); heuristic (producer preference)

### R9557-1.2-01 — Do not synthesize an offset time zone from the offset
- **Section:** §1.2 (Offset Time Zone)
- **Level:** MUST NOT
- **Roles:** producer
- **Requirement:** "programs MUST NOT copy the UTC offset from a timestamp into an offset time zone in order to satisfy another program that requires a time zone suffix in its input." Offset time zones are "strongly discouraged" in general (informative).
- **Detect:** Look for producer code that builds `[` + offset + `]` from the value's own offset, for example `f"{ts}[{ts.strftime('%:z')}]"`, `ZonedDateTime.of(ldt, ZoneOffset.of(...))` serialized with `ISO_ZONED_DATE_TIME`, or `atZone(offset)` followed by `toString()`. Java `ZonedDateTime.toString()` on a value with only a `ZoneOffset` prints `...+01:00` with no bracket, but `withZoneSameInstant(ZoneId.of("+01:00"))` style code or explicit formatting can produce `[+01:00]`. Flag fallback code that adds a bracketed offset when no real zone is known.
- **Test inputs:** For a value whose real zone is unknown, emitting `2020-01-01T00:00:00+01:00[+01:00]` fails. Emitting `2020-01-01T00:00:00+01:00` (no suffix) or `...[Europe/Paris]` (the real zone) passes.
- **Judgment:** heuristic (intent to "satisfy another program" must be inferred)

### R9557-1.2-02 — Offset time zone must repeat the timestamp's offset
- **Section:** §1.2, §3.4
- **Level:** informative (defines inconsistency; the obligations are in R9557-3.4-01/02)
- **Roles:** consumer, producer
- **Requirement:** "An offset in the suffix that does not repeat the offset of the timestamp is inconsistent." The bracketed `time-numoffset` is the name of an Offset Time Zone.
- **Detect:** *Consumer:* feed a mismatched bracketed offset and apply the elective/critical rules. *Producer:* never emit a bracketed offset that differs from the leading offset.
- **Test inputs:** `2022-07-08T00:14:07+08:45[+08:45]` is valid and consistent. `2022-07-08T00:14:07+08:00[!+08:45]` is erroneous (MUST act). `2022-07-08T00:14:07+08:00[+08:45]` is inconsistent and elective (MAY act). `2022-07-08T00:14:07Z[+08:45]` gives no inconsistency by the Z rule of §3.4 (the local time is derived as 08:59:07+08:45).
- **Judgment:** objective

### R9557-1.1-01 — The suffix is fully optional (backward compatibility)
- **Section:** §1.1, §3.3, §4.1 (`suffix = [time-zone] *suffix-tag`)
- **Level:** informative (grammar consequence)
- **Roles:** consumer, schema
- **Requirement:** Every valid RFC 3339 `date-time` is a valid IXDTF string with an empty suffix. An IXDTF consumer must accept bare RFC 3339 timestamps, unless the application itself requires particular tags ("An application might require the presence of specific suffix tags, though", §3.3).
- **Detect:** Feed a bare RFC 3339 string to the IXDTF parser. Check any regex that requires `\[`.
- **Test inputs:** `1996-12-19T16:39:57-08:00` is accepted. `1985-04-12T23:20:50.52Z` is accepted.
- **Judgment:** objective

### R9557-1.1-02 — IXDTF is still a fixed instant (no floating or zone-only time)
- **Section:** §1.1
- **Level:** informative (scope)
- **Roles:** consumer, producer, schema
- **Requirement:** The RFC 3339 part carries a required offset (`Z` or numeric), so the string always names a fixed UTC-referenced instant. A zone name does **not** replace the offset. Future local times that should follow later rule changes, and floating times, are out of scope.
- **Detect:** Look for a producer that emits `2025-03-01T09:00:00[America/New_York]` (no offset), or a consumer that accepts it as IXDTF. Such a string is not valid under §4.1. Some libraries, for example Temporal `ZonedDateTime.from` and `PlainDateTime` parsing, accept a wider grammar; flag this if the code claims RFC 9557 conformance.
- **Test inputs:** `2025-03-01T09:00:00[America/New_York]` is rejected (no offset). `2025-03-01[America/New_York]` is rejected (the suffix requires a full `date-time`). `2025-03-01T09:00:00-05:00[America/New_York]` is valid.
- **Judgment:** objective

### R9557-3.1-01 — Keys are lowercase only
- **Section:** §3.1, §4.1 (`key-initial = lcalpha / "_"`, `lcalpha = %x61-7A`)
- **Level:** informative (grammar; objective reject)
- **Roles:** producer, consumer
- **Requirement:** "Keys are lowercase only." `%x61-7A` is a case-sensitive range, unlike quoted ABNF strings, so uppercase key letters do not match.
- **Detect:** *Consumer:* feed an uppercase key. A conforming parser rejects it as a syntax error. It must not lowercase the key and then accept it. Look for `(?i)` or `re.IGNORECASE` on the whole suffix regex, or `.lower()` applied to the key before validation. *Producer:* check that key constants are lowercase.
- **Test inputs:** `2022-07-08T00:14:07Z[U-CA=hebrew]` is rejected. `2022-07-08T00:14:07Z[u-CA=hebrew]` is rejected. `2022-07-08T00:14:07Z[u-ca=hebrew]` is valid.
- **Judgment:** objective

### R9557-3.1-02 — Values are case-sensitive unless the key's spec says otherwise
- **Section:** §3.1
- **Level:** informative
- **Roles:** consumer
- **Requirement:** "Values are case-sensitive unless otherwise specified." A consumer must not case-fold values in general. Per-key specifications may relax this. §5 does not state case-insensitivity for `u-ca`. UTS #35 identifiers are canonically lowercase.
- **Detect:** Look for `.lower()`/`toLowerCase()` applied to generic suffix values. For `u-ca`, check whether `Hebrew` is treated as `hebrew`. If so, record the deviation as a documented local choice, not as a failure.
- **Test inputs:** `...Z[u-ca=hebrew]` is recognized. `...Z[u-ca=Hebrew]` is syntactically valid. Whether it is a recognized value is a heuristic question (a strict reading says it is an unknown value, so ignore it if elective and treat it as an error if critical).
- **Judgment:** heuristic

### R9557-3.2-01 — Experimental (`_`) keys: never interchanged, rejected unless configured
- **Section:** §3.2 (also Figure 7)
- **Level:** MUST NOT (use for interchange) / MUST (be rejected)
- **Roles:** producer, consumer
- **Requirement:** Keys that start with `_` "MUST NOT be used for interchange and MUST be rejected by implementations not specifically configured to take part in such an experiment." **This applies whether or not the tag carries `!`.** It overrides the default elective "free to ignore" rule.
- **Detect:** *Consumer:* feed `[_foo=bar]` without `!`. A parser that ignores it like an unknown elective key fails. Check for a configuration switch (an allow-list of experimental keys). The default must be reject. *Producer:* grep for emitted keys that match `\[!?_`. Their presence in outbound or API output fails.
- **Test inputs:** `1996-12-19T16:39:57-08:00[_foo=bar][_baz=bat]` is rejected by default and accepted only when configured. `2022-07-08T00:14:07Z[!_x=1]` is rejected by default.
- **Judgment:** objective (consumer); heuristic (producer: "interchange" versus a controlled experiment)

### R9557-3.2-02 — Keys used should be registered (or experimental)
- **Section:** §3.2, §6
- **Level:** informative (the RFC defines a registry but does not forbid unregistered non-underscore keys in so many words)
- **Roles:** producer
- **Requirement:** Non-experimental keys are expected to come from the IANA "Timestamp Suffix Tag Keys" registry. On 2026-09-24 the only registered key is `u-ca` (see the registry snapshot). A producer that invents keys such as `[tz=...]` or `[loc=...]` for interchange risks collisions. §6 lets the experts register deployed keys on their own initiative "to avert potential future collisions".
- **Detect:** Grep for suffix keys that producers emit and compare them with the registry snapshot.
- **Test inputs:** Emitting `[u-ca=gregory]` passes. Emitting `[myapp-ctx=abc]` for public interchange is a heuristic finding.
- **Judgment:** heuristic

### R9557-3.3-01 — Suffix tags are optional for producers
- **Section:** §3.3
- **Level:** informative
- **Roles:** producer, consumer, schema
- **Requirement:** "suffix tags are always _optional_. They can be added or left out as desired by the generator of the string. (An application might require the presence of specific suffix tags, though.)" A generic IXDTF consumer must not require any tag. An application-level schema may require one and should document it.
- **Detect:** *Schema:* if a contract requires `[zone]`, check that this is documented as an application profile and not presented as RFC 9557 itself.
- **Test inputs:** A generic parser accepts `2022-07-08T00:14:07Z`.
- **Judgment:** heuristic

### R9557-3.3-02 — Elective tags: the recipient may ignore unknown or unusable tags
- **Section:** §3.3
- **Level:** informative (permission; the text says "free to ignore")
- **Roles:** consumer
- **Requirement:** "Without further indication, suffix tags are also _elective_. The recipient is free to ignore any suffix tag". This includes unknown keys and known keys whose value cannot be acted on. A consumer that **rejects** a string only because an elective tag is unknown is stricter than needed. That is allowed ("applications MAY also perform additional processing"), but it hurts interoperability. Flag it as a heuristic interoperability finding, not a violation.
- **Detect:** Feed an unknown elective key. Record whether the parser accepts it (expected) or throws. Also feed a known key with an unsupported value, for example `[u-ca=unknowncal]`.
- **Test inputs:** `2022-07-08T00:14:07+01:00[knort=blargel]` is accepted and equals `2022-07-08T00:14:07+01:00`. `2022-07-08T00:14:07Z[u-ca=notacalendar]` is accepted with the tag ignored (or given optional extra processing).
- **Judgment:** heuristic

### R9557-3.3-03 — Critical unknown key or unprocessable value: MUST NOT act, MUST treat as erroneous
- **Section:** §3.3
- **Level:** MUST NOT (act on the string) / MUST (treat as erroneous; reject or do error handling)
- **Roles:** consumer
- **Requirement:** For a critical tag, "The recipient is advised that it MUST NOT act on the IXDTF string unless it can process the suffix tag as specified." For strings with "an unrecognized suffix key/value that is marked as critical ... a recipient MUST treat these IXDTF strings as erroneous. This means that the application MUST reject the data or perform some other error handling". Conformance fails when the tag is silently dropped and the timestamp is used.
- **Detect:** Feed `[!knort=blargel]`. It must raise an error or reach an error-handling path. Inspect parser code: a common bug is to strip `!` with `lstrip('!')` or `replace('!','')` and then apply the elective ignore logic. Grep `'!'` near suffix parsing. Check that the parsed result keeps a `critical` boolean per tag. Also check the value side: a critical *known* key with an unsupported value is also erroneous.
- **Test inputs:** `2022-07-08T00:14:07Z[!knort=blargel]` is erroneous. `2022-07-08T00:14:07Z[!u-ca=notacalendar]` is erroneous (unless the implementation supports that value). `2022-07-08T00:14:07Z[!u-ca=hebrew]` is accepted by an implementation that supports the Hebrew calendar and is erroneous for one that does not implement `u-ca` or `hebrew`.
- **Judgment:** objective

### R9557-3.3-04 — Critical flag is a single `!` directly after `[`
- **Section:** §3.3, §4.1 (`critical-flag = [ "!" ]`)
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer
- **Requirement:** The flag is an optional single `!` immediately after the opening bracket. It is allowed on the time-zone element and on key=value tags. No other position, no repeat, and no whitespace is allowed.
- **Detect:** Feed malformed flags. Regexes such as `\[!*` or `\[\s*!?` are too permissive.
- **Test inputs:** `...Z[!!u-ca=hebrew]` is rejected. `...Z[ !u-ca=hebrew]` is rejected. `...Z[u-ca=!hebrew]` is rejected. `...Z[!Europe/London]` is valid.
- **Judgment:** objective

### R9557-3.3-05 — Duplicate elective keys: use the first occurrence
- **Section:** §3.3
- **Level:** MUST (conditional: "and does not want to perform additional processing on this inconsistency")
- **Roles:** consumer
- **Requirement:** "An application that encounters duplicate use of a suffix key in elective suffixes and does not want to perform additional processing on this inconsistency MUST choose the first suffix that has that key". `...Z[u-ca=chinese][u-ca=japanese]` is then treated like `...Z[u-ca=chinese]`.
- **Detect:** A common bug is building a dict or map from tags, which gives **last-wins** (`dict(tags)`, `Object.fromEntries`, `map[key]=value` in a loop). Look for `setdefault`, `if key not in`, or a `putIfAbsent` guard. Feed a duplicate and read back the value.
- **Test inputs:** `2022-07-08T00:14:07Z[u-ca=chinese][u-ca=japanese]` gives `chinese` (or explicit extra processing such as an error or a prompt). Getting `japanese` silently fails.
- **Judgment:** objective

### R9557-3.3-06 — Duplicate key where any occurrence is critical: erroneous
- **Section:** §3.3 (examples 2 and 3 of the critical list)
- **Level:** MUST (treat as erroneous; reject or do error handling)
- **Roles:** consumer
- **Requirement:** Both `Z[!u-ca=chinese][u-ca=japanese]` and `Z[u-ca=chinese][!u-ca=japanese]` are listed as having "an internal inconsistency ... marked as critical", so "a recipient MUST treat these IXDTF strings as erroneous". The first-wins rule does **not** save the second form: a later critical duplicate still triggers the error.
- **Detect:** Feed both orders. An implementation that uses first-wins and never looks at later tags accepts the second form and fails.
- **Test inputs:** `2022-07-08T00:14:07Z[!u-ca=chinese][u-ca=japanese]` is erroneous. `2022-07-08T00:14:07Z[u-ca=chinese][!u-ca=japanese]` is erroneous. `...Z[!u-ca=chinese][u-ca=chinese]` (identical values) is not addressed by the RFC. Not inconsistent is the reasonable reading, so record whatever it does as a local choice.
- **Judgment:** objective (conflicting values); heuristic (identical values)

### R9557-3.3-07 — Extra processing of elective tags is allowed
- **Section:** §3.3
- **Level:** MAY
- **Roles:** consumer
- **Requirement:** "applications MAY also perform additional processing on inconsistent or unrecognized elective suffix tags, such as asking the user how to resolve the inconsistency." Reject, warn, and prompt are all conforming for elective problems. So is ignoring the tag.
- **Detect:** Informational. Record the behaviour so the report can state the policy. It is never a failure alone.
- **Test inputs:** `2022-07-08T00:14:07+00:00[Europe/London]`: accept, warn, or reject are all conforming.
- **Judgment:** editorial

### R9557-3.4-01 — Offset/zone inconsistency with a critical zone: MUST act
- **Section:** §3.4 (Figure 1, first line); §3.3 (`[!Europe/Paris]` example)
- **Level:** MUST
- **Roles:** consumer
- **Requirement:** "if the critical flag is used on the time zone suffix, an application MUST act on the inconsistency ... Acting on the inconsistency may involve rejecting the timestamp or resolving the inconsistency via additional information, such as user input and/or programmed behavior." Silently using either the offset or the zone without detecting the conflict fails. (Erratum 8192, Rejected, only concerns the hyphenation of "critical flag" in this paragraph and changes nothing.)
- **Detect:** Check that the parser (a) resolves the zone with TZDB at the instant, (b) compares the zone's offset with the stated numeric offset, and (c) on a mismatch with `!`, raises an error or calls a resolver or strategy hook. Java `ZonedDateTime.parse` resolves a mismatch silently (it keeps the offset if valid, otherwise it adjusts), which fails under `!` unless it is wrapped. Temporal's `offset: 'reject'` option conforms, and `'use'`/`'ignore'`/`'prefer'` are "programmed behaviour" and conform only if chosen deliberately for `!` input.
- **Test inputs:** `2022-07-08T00:14:07+00:00[!Europe/London]` is erroneous or resolved. `2022-07-08T00:14:07+01:00[!Europe/Paris]` is erroneous or resolved. `2022-07-08T01:14:07+01:00[!Europe/London]` is consistent and accepted.
- **Judgment:** objective

### R9557-3.4-02 — Offset/zone inconsistency with an elective zone: MAY act
- **Section:** §3.4 (Figure 1, second line); §3.3 (Europe/Paris example)
- **Level:** MAY
- **Roles:** consumer
- **Requirement:** "If the critical flag is not used, it MAY act on the inconsistency." Ignoring the zone and using the RFC 3339 part is explicitly allowed: the recipient "can treat the Internet Date/Time Format string as if it were" the string without the suffix.
- **Detect:** Record the policy. Flag a consumer that silently **uses the zone's offset and discards the stated offset**, because that changes the instant. The RFC allows "resolving", but that resolution should be deliberate and documented (heuristic).
- **Test inputs:** `2022-07-08T00:14:07+01:00[Europe/Paris]`: treating it as the instant `2022-07-07T23:14:07Z` (the offset wins) conforms, and rejecting or prompting also conforms.
- **Judgment:** heuristic

### R9557-3.4-03 — `Z` / `-00:00` with a zone is never inconsistent
- **Section:** §3.4 (Figure 2), §3.3 note, §2
- **Level:** informative (it defines what counts as inconsistent; misclassifying it causes false errors)
- **Roles:** consumer
- **Requirement:** Z asserts no local offset, so `Z[Europe/London]` and `Z[!Europe/London]` are consistent. The consumer derives the local time from the zone rules, so `2022-07-08T00:14:07Z[Europe/Paris]` equals `2022-07-08T02:14:07+02:00[Europe/Paris]`. The same applies to `-00:00`.
- **Detect:** Look for code that compares a parsed offset of 0 with the zone offset without checking whether the source token was `Z`/`-00:00` or `+00:00`. Parsers that turn Z into offset 0 early lose this information. A tell-tale sign is an offset stored as a plain integer with no "unknown" or Z flag.
- **Test inputs:** `2022-07-08T00:14:07Z[!Europe/London]` is accepted with local time 01:14:07+01:00. `2022-07-08T00:14:07-00:00[!Europe/London]` is accepted with the same result. `2022-07-08T00:14:07+00:00[!Europe/London]` is erroneous (contrast case). `2022-07-08t00:14:07z[!Europe/London]` is accepted (RFC 3339 allows lowercase `t`/`z`).
- **Judgment:** objective

### R9557-3.4-04 — Producers must not emit offset/zone combinations they know to be inconsistent
- **Section:** §3.4, §1.1
- **Level:** informative (no producer keyword; the inconsistency definition implies it)
- **Roles:** producer
- **Requirement:** When a producer emits `offset[zone]`, the offset should be the zone's offset at that instant under the producer's TZDB. For "UTC known, local unknown" it should use `Z[zone]`. Mismatches from stale TZDB data are expected over time (§3.4 far-future meeting example), but mismatches from code bugs are not.
- **Detect:** Look for producers that concatenate a stored offset with a separately stored zone name, for example `f"{dt.isoformat()}[{user.tz}]"` where `dt` is in UTC or server-local time. Round-trip a sample through a validating parser.
- **Test inputs:** Emitting `2022-07-08T00:14:07+00:00[Europe/Paris]` for a Paris user fails. Emitting `2022-07-08T02:14:07+02:00[Europe/Paris]` or `2022-07-08T00:14:07Z[Europe/Paris]` passes.
- **Judgment:** heuristic

### R9557-4.1-01 — Only after a full `date-time`
- **Section:** §4.1 (`date-time-ext = date-time suffix`)
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer, schema
- **Requirement:** The suffix may only follow an RFC 3339 `date-time`, which has a date, a time with seconds, and an offset. Suffixes on `full-date`, `partial-time`, or offset-less date-times are not IXDTF.
- **Detect:** Feed the inputs below. Check whether the grammar or regex makes the offset or the seconds optional.
- **Test inputs:** `2022-07-08[u-ca=hebrew]` is rejected. `2022-07-08T00:14[Europe/Paris]` is rejected (seconds are required, and there is no offset). `2022-07-08T00:14+02:00[Europe/Paris]` is rejected (`partial-time` requires seconds). **Caution:** §1.2 of the RFC itself writes `2020-01-01T00:00+01:00[Europe/Paris]`, without seconds, in prose. Per §4.1 that string is not valid IXDTF. Do not use it as a positive test vector.
- **Judgment:** objective

### R9557-4.1-02 — Time-zone element: at most one, and it must come first
- **Section:** §4.1 (`suffix = [time-zone] *suffix-tag`)
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer
- **Requirement:** A bracket without `=` is a time-zone element. Only one is allowed, and it must come before all key=value tags. A second zone, or a zone after a tag, does not match the grammar.
- **Detect:** Feed the inputs below. A parser that splits on `][` and classifies each bracket independently usually accepts them wrongly.
- **Test inputs:** `...-08:00[America/Los_Angeles][u-ca=hebrew]` is valid. `...-08:00[u-ca=hebrew][America/Los_Angeles]` is rejected. `...Z[Europe/Paris][Europe/London]` is rejected. `...Z[Europe/Paris][tz=Europe/London]`: the second bracket is a syntactically valid unknown key (`tz` is not registered), so it is ignored if elective.
- **Judgment:** objective

### R9557-4.1-03 — Time-zone name syntax
- **Section:** §4.1 (`time-zone-initial`, `time-zone-char`, `time-zone-part`, `time-zone-name`)
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer
- **Requirement:** The name is one or more `/`-separated parts. Each part starts with `ALPHA`, `.` or `_`, followed by `ALPHA`, `DIGIT`, `.`, `_`, `-` or `+`. A part may not be exactly `.` or `..` ("but not "." or ".."", a prose constraint that the ABNF matches but the comment excludes). ASCII only. Empty parts are not allowed, so there can be no leading, trailing, or doubled `/`.
- **Detect:** Check for path traversal and generic-regex issues. Parsers that pass the name to a filesystem-backed zoneinfo loader (`/usr/share/zoneinfo/` + name) must reject `.`/`..` parts. This is also the security angle of §7.2. Feed the inputs below.
- **Test inputs:** `...Z[America/Argentina/Buenos_Aires]` is valid. `...Z[Etc/GMT+5]` is valid. `...Z[../etc/passwd]` is rejected (`..` part). `...Z[Europe//Paris]` is rejected. `...Z[1Europe]` is rejected (a digit cannot start a part). `...Z[Europe/Zürich]` is rejected (non-ASCII).
- **Judgment:** objective

### R9557-4.1-04 — No 14-character limit on time-zone-part in syntax
- **Section:** §4.1 (Note)
- **Level:** informative ("deliberately permissive")
- **Roles:** consumer
- **Requirement:** TZDB naming rules cap a part at 14 characters, but the grammar deliberately does not. Name length is left to the local database lookup. A long, unknown name is therefore an unknown zone (inconsistency handling, see R9557-4.1-06), not a syntax error.
- **Detect:** Look for `{1,14}` in zone regexes. Feed a long part.
- **Test inputs:** `...Z[America/Argentina/ComodRivadavia]` (`ComodRivadavia` has 14 characters; it is a real TZDB backward link) is valid. `...Z[Abcdefghijklmnopqrstu]` is syntactically valid and is an unknown zone (ignored if elective, an error if `!`).
- **Judgment:** heuristic

### R9557-4.1-05 — Offset time zone in brackets uses `time-numoffset` only
- **Section:** §4.1 (`time-zone = "[" critical-flag time-zone-name / time-numoffset "]"`)
- **Level:** informative (grammar)
- **Roles:** consumer, producer
- **Requirement:** A bracketed offset must be `(+|-)HH:MM`. `Z` is not a `time-numoffset`. `[Z]` does parse, but as a *time-zone-name* (`Z` is an ALPHA), and `Z` is not a TZDB zone name. Offsets without a colon or with seconds do not match. **ABNF precedence caveat:** under RFC 5234 §3.10, concatenation binds more tightly than alternation, so the rule *as literally written* reads as `("[" critical-flag time-zone-name) / (time-numoffset "]")`. The evident intent, confirmed by §1.2's `[+08:45]` example, is `"[" critical-flag (time-zone-name / time-numoffset) "]"`. Implement the intent. This is not an erratum: no erratum was filed, and only 8192 exists.
- **Detect:** Feed the inputs below. For grammar-driven parsers generated mechanically from the ABNF (abnf-to-regex tools), check that grouping parentheses were added.
- **Test inputs:** `...+08:45[+08:45]` is valid. `...+08:45[!+08:45]` is valid. `...+08:45[+0845]` is rejected. `...Z[Z]` is syntactically valid, with an unknown zone name.
- **Judgment:** objective

### R9557-4.1-06 — Unknown zone name: treat as inconsistency
- **Section:** §4.1 (paragraph after Figure 3)
- **Level:** informative (lowercase "should treat such a situation as any other inconsistency"); combined with §3.3 it is MUST for critical
- **Roles:** consumer
- **Requirement:** The producer and the recipient may use different TZDB versions. An unknown `time-zone-name` is handled like an inconsistency: with an elective tag it may be ignored (fall back to the offset), and with `!` the recipient cannot process the tag and MUST treat the string as erroneous (§3.3).
- **Detect:** Feed an unknown zone with and without `!`. A common bug is to throw on every unknown zone (for example `ZoneId.of`, `ZoneInfo(name)`, or `pytz.timezone` raising), even when the tag is elective. That is stricter than needed (heuristic). Accepting a critical unknown zone is an objective failure.
- **Test inputs:** `2022-07-08T00:14:07Z[Mars/Olympus_Mons]` is accepted as an instant (zone ignored) or handled extra. `2022-07-08T00:14:07Z[!Mars/Olympus_Mons]` is erroneous.
- **Judgment:** objective (critical); heuristic (elective)

### R9557-4.1-07 — Suffix key syntax
- **Section:** §4.1 (`key-initial = lcalpha / "_"`, `key-char = key-initial / DIGIT / "-"`, `suffix-key = key-initial *key-char`)
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer
- **Requirement:** A key starts with `a-z` or `_`, then continues with `a-z`, `_`, `0-9` or `-`. It must not be empty.
- **Detect:** Feed the inputs below.
- **Test inputs:** `...Z[1ab=x]` is rejected. `...Z[-ab=x]` is rejected. `...Z[=x]` is rejected. `...Z[a.b=x]` is rejected. `...Z[a-1_b=x]` is valid (an unknown elective key).
- **Judgment:** objective

### R9557-4.1-08 — Suffix value syntax
- **Section:** §4.1 (`suffix-value = 1*alphanum`, `suffix-values = suffix-value *("-" suffix-value)`)
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer
- **Requirement:** A value is one or more ASCII alphanumeric items separated by single `-`. It must not be empty. Leading, trailing, or doubled hyphens are not allowed, and neither are `_`, `.`, `/`, `=`, spaces, or non-ASCII characters. Only one `=` is allowed.
- **Detect:** Feed the inputs below. Regexes such as `[^\]]+` for the value are too permissive.
- **Test inputs:** `...Z[u-ca=islamic-umalqura]` is valid. `...Z[u-ca=]` is rejected. `...Z[u-ca=a--b]` is rejected. `...Z[u-ca=hebrew-]` is rejected. `...Z[u-ca=a_b]` is rejected. `...Z[u-ca=a=b]` is rejected.
- **Judgment:** objective

### R9557-4.1-09 — No whitespace, no empty brackets, nothing after the last `]`
- **Section:** §4.1
- **Level:** informative (grammar; objective reject)
- **Roles:** consumer, producer
- **Requirement:** The grammar has no whitespace in the suffix, no `[]`, no separators between brackets, and no trailing characters.
- **Detect:** Feed the inputs below. Check whether the parser uses an unanchored match (`re.match` without `$`/`\Z`, or `search`).
- **Test inputs:** `...Z[]` is rejected. `...Z [Europe/Paris]` is rejected. `...Z[Europe/Paris] ` is rejected. `...Z[Europe/Paris]x` is rejected. `...Z[Europe/Paris],[u-ca=hebrew]` is rejected.
- **Judgment:** objective

### R9557-4.1-10 — Schema contracts: IXDTF is not JSON Schema `date-time`
- **Section:** §4.1 (IXDTF is a superset of RFC 3339 `date-time`)
- **Level:** informative
- **Roles:** schema
- **Requirement:** A field that carries IXDTF values fails validation under JSON Schema/OpenAPI `format: date-time` (RFC 3339 only). A field declared `date-time` must not be documented or used as accepting `[...]` suffixes. Such fields should use a custom format or pattern and document the elective/critical policy.
- **Detect:** Grep schemas for `format: date-time` / `"format": "date-time"` on fields whose examples or docs contain `[`. Check `pattern` values for the problems in R9557-4.1-02..09.
- **Test inputs:** A schema field `format: date-time` with example `2022-07-08T00:14:07Z[Europe/Paris]` fails.
- **Judgment:** heuristic

### R9557-5-01 — `u-ca` values are Unicode Calendar Identifiers
- **Section:** §5
- **Level:** informative (defines the value set)
- **Roles:** consumer, producer
- **Requirement:** The value set for `u-ca` is "the set of values defined for the Unicode Calendar Identifier [TR35]". Examples: `gregory`, `hebrew`, `chinese`, `japanese`, `islamic-umalqura`, `iso8601`, `buddhist`, `persian`. Note that the Gregorian calendar is `gregory`, not `gregorian`. A producer must emit only UTS #35 identifiers. A consumer that does not support a given identifier treats it as an unusable value: ignore it if elective, and treat the string as erroneous if critical.
- **Detect:** *Producer:* grep for emitted `u-ca=` values and check them against UTS #35 `calendar` keys. Frequent mistakes are `gregorian`, `islamic_civil`, and `Hebrew`. *Consumer:* check the mapping table and the unknown-value branch.
- **Test inputs:** `...-08:00[America/Los_Angeles][u-ca=hebrew]` is valid. `...Z[u-ca=gregorian]` is syntactically valid but not a UTS #35 id (ignored if elective). `...Z[!u-ca=gregorian]` is erroneous.
- **Judgment:** objective (producer vs UTS #35 list); heuristic (consumer support)

### R9557-5-02 — `u-ca` affects presentation, not the instant
- **Section:** §5 ("the calendar in which the date/time is preferably presented"), §4.2 Figure 6
- **Level:** informative
- **Roles:** consumer
- **Requirement:** `u-ca` does not change the instant or how the RFC 3339 part is parsed. The Gregorian date in the string stays authoritative. The tag only asks calendar-aware applications to *project* the date for display.
- **Detect:** Flag consumers that re-interpret the numeric Y-M-D fields as dates in the named calendar, for example reading `2022-07-08[u-ca=hebrew]` as Hebrew year 2022.
- **Test inputs:** `1996-12-19T16:39:57-08:00[America/Los_Angeles][u-ca=hebrew]` is the same instant as `1996-12-20T00:39:57Z`.
- **Judgment:** objective

### R9557-6-01 — Registry entries: key identifier must conform to `suffix-key`
- **Section:** §3.2, §6
- **Level:** informative (registration procedure)
- **Roles:** schema (key tables or enums in code and docs)
- **Requirement:** Registered keys match `suffix-key`. `_`-prefixed keys "cannot be registered". Registry fields: Key Identifier, Registration Status (Provisional/Permanent), Description, Change Controller, Reference. Policy: Specification Required (Permanent) and Expert Review (Provisional).
- **Detect:** If the target code keeps a known-keys table, check that it matches the IANA snapshot below and does not list `_` keys as "registered".
- **Test inputs:** A known-keys enum `{u-ca}` passes as of 2026-09-24.
- **Judgment:** objective

### R9557-7.1-01 — Data minimization in suffixes
- **Section:** §7.1
- **Level:** informative ("need to consider", "need to err on the side of minimizing")
- **Roles:** producer
- **Requirement:** Producers should add ancillary information (zone, calendar, and so on) only when it is appropriate to disclose. Zone names and calendar preferences can reveal a user's location or culture. When the recipients are not under the originator's control, the producer should lean toward leaving the information out.
- **Detect:** Flag public API or log outputs that append the user's personal `[Zone]` or `[u-ca=...]` to timestamps where the consumer does not need them.
- **Test inputs:** n/a (editorial review).
- **Judgment:** editorial

### R9557-7.2-01 — Parser hardening for the extended syntax
- **Section:** §7.2
- **Level:** informative
- **Roles:** consumer
- **Requirement:** The RFC notes that extending syntax can introduce parser vulnerabilities ("no considerations ... out of the ordinary"). Practical checks: bound the number and length of suffix tags (the grammar allows `*suffix-tag`, so there is no limit), avoid catastrophic-backtracking regexes, and never use the zone name as a filesystem path without validation (see R9557-4.1-03).
- **Detect:** Look for nested quantifiers such as `(\[[^\]]*\])*` combined with alternation, and for unbounded loops. Feed 10k tags or a 1 MB suffix and measure the time.
- **Test inputs:** `"2022-07-08T00:14:07Z" + "[a=b]"*100000` is rejected or handled in bounded time.
- **Judgment:** heuristic

### R9557-7.3-01 — Security-relevant timestamps: only extensions with shared inconsistency resolution
- **Section:** §7.3
- **Level:** informative ("only extensions that have a well-understood and shared resolution of such inconsistent data can be employed")
- **Roles:** consumer, producer, schema
- **Requirement:** When timestamps drive security decisions (access-control validity windows, token expiry), every party must resolve inconsistencies the same way. In practice: base the decision on the RFC 3339 instant only, or require one documented policy (for example "reject all inconsistencies, elective or critical").
- **Detect:** Look for auth, ACL, or expiry code that parses IXDTF and uses zone-resolved (not offset-derived) instants, or that relies on a library's default conflict resolution. Check that producer and verifier use the same policy.
- **Test inputs:** `notAfter=2022-07-08T00:14:07+01:00[Europe/Paris]`: if the verifier uses the zone-derived instant and the issuer used the offset, a one-hour window opens (finding).
- **Judgment:** heuristic

---

## ABNF (verbatim)

RFC 9557 §4.1, Figure 3 (verbatim):

```abnf
   time-zone-initial = ALPHA / "." / "_"
   time-zone-char    = time-zone-initial / DIGIT / "-" / "+"
   time-zone-part    = time-zone-initial *time-zone-char
                       ; but not "." or ".."
   time-zone-name    = time-zone-part *("/" time-zone-part)
   time-zone         = "[" critical-flag
                           time-zone-name / time-numoffset "]"

   key-initial       = lcalpha / "_"
   key-char          = key-initial / DIGIT / "-"
   suffix-key        = key-initial *key-char

   suffix-value      = 1*alphanum
   suffix-values     = suffix-value *("-" suffix-value)
   suffix-tag        = "[" critical-flag
                           suffix-key "=" suffix-values "]"
   suffix            = [time-zone] *suffix-tag

   date-time-ext     = date-time suffix

   critical-flag     = [ "!" ]

   alphanum          = ALPHA / DIGIT
   lcalpha           = %x61-7A
```

Imports stated in §4.1: "date-time and time-numoffset are imported from Section 5.6 of [RFC3339], and ALPHA and DIGIT are imported from Appendix B.1 of [RFC5234]."

Imported from RFC 3339 §5.6 (verbatim; this is the full closure needed by `date-time` and `time-numoffset`):

```abnf
   date-fullyear   = 4DIGIT
   date-month      = 2DIGIT  ; 01-12
   date-mday       = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on
                             ; month/year
   time-hour       = 2DIGIT  ; 00-23
   time-minute     = 2DIGIT  ; 00-59
   time-second     = 2DIGIT  ; 00-58, 00-59, 00-60 based on leap second
                             ; rules
   time-secfrac    = "." 1*DIGIT
   time-numoffset  = ("+" / "-") time-hour ":" time-minute
   time-offset     = "Z" / time-numoffset

   partial-time    = time-hour ":" time-minute ":" time-second
                     [time-secfrac]
   full-date       = date-fullyear "-" date-month "-" date-mday
   full-time       = partial-time time-offset

   date-time       = full-date "T" full-time
```

RFC 3339 §5.6 NOTE (it applies to the `date-time` part of IXDTF): "Per [ABNF] and ISO8601, the "T" and "Z" characters in this syntax may alternatively be lower case "t" or "z" respectively."

Imported from RFC 5234 Appendix B.1 (RFC 5234 is not in the local `rfc/` sources; transcribed from the published RFC — re-verify against rfc5234.txt if byte-exactness matters):

```abnf
         ALPHA          =  %x41-5A / %x61-7A   ; A-Z / a-z
         DIGIT          =  %x30-39
                                ; 0-9
```

Grammar notes (from §4.1 prose and ABNF semantics):
- "a time-zone is syntactically similar to a suffix-tag but does not include an equals sign. This special case is only available for time zone tags."
- The `; but not "." or ".."` comment is a normative prose exclusion that the ABNF alone does not express.
- **Precedence caveat:** per RFC 5234 §3.10, alternation (`/`) binds more loosely than concatenation. The `time-zone` rule as literally written therefore groups as `("[" critical-flag time-zone-name) / (time-numoffset "]")`. The evident intent, from the §1.2 example `2022-07-08T00:14:07+08:45[+08:45]` and all the prose, is `"[" critical-flag ( time-zone-name / time-numoffset ) "]"`. No erratum records this (as of 2026-09-24 the only erratum, 8192, is Rejected and unrelated).
- Quoted strings in ABNF are case-insensitive, but `lcalpha = %x61-7A` is a case-sensitive range, so keys are lowercase only. `ALPHA` in zone names allows both cases.
- Equivalent regex for implementers, informative, intent-grouped. Replace `DT` with an RFC 3339 `date-time` regex:
  `DT(?:\[!?(?:TZN|[+-]\d{2}:\d{2})\])?(?:\[!?[a-z_][a-z0-9_-]*=[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\])*`
  where `TZN = TZP(?:/TZP)*`, `TZP = [A-Za-z._][A-Za-z0-9._+-]*`, with an extra check that no TZP equals `.` or `..`.

---

## Examples from the RFC (with expected consumer outcome)

| String | Source | Outcome |
|---|---|---|
| `2022-07-08T00:14:07+08:45[+08:45]` | §1.2 | Valid, consistent offset time zone (discouraged) |
| `2020-01-01T00:00+01:00[Europe/Paris]` | §1.2 prose | **Not valid per §4.1** (no seconds). Illustrative only |
| `2022-07-08T00:14:07+01:00[Europe/Paris]` | §3.3 | Inconsistent (Paris was +02:00), elective: MAY act, or treat as `...+01:00` |
| `2022-07-08T00:14:07Z[Europe/Paris]` | §3.3 | Consistent; equals `2022-07-08T02:14:07+02:00[Europe/Paris]` |
| `2022-07-08T00:14:07+01:00[knort=blargel]` | §3.3 | Unknown elective key, may be ignored |
| `2022-07-08T00:14:07+01:00[!Europe/Paris]` | §3.3 | Critical inconsistency: MUST treat as erroneous |
| `2022-07-08T00:14:07Z[!u-ca=chinese][u-ca=japanese]` | §3.3 | Critical duplicate conflict: erroneous |
| `2022-07-08T00:14:07Z[u-ca=chinese][!u-ca=japanese]` | §3.3 | Critical duplicate conflict: erroneous |
| `2022-07-08T00:14:07Z[!knort=blargel]` | §3.3 | Critical unknown key: erroneous |
| `2022-07-08T00:14:07Z[u-ca=chinese][u-ca=japanese]` | §3.3 | Elective duplicate: first wins, so the same as `...Z[u-ca=chinese]` |
| `2022-07-08T00:14:07+00:00[!Europe/London]` | §3.4 Fig. 1 | Inconsistent, critical: MUST act |
| `2022-07-08T00:14:07+00:00[Europe/London]` | §3.4 Fig. 1 | Inconsistent, elective: MAY act |
| `2022-07-08T00:14:07Z[!Europe/London]` | §3.4 Fig. 2 | Consistent; the recipient must understand the zone |
| `2022-07-08T00:14:07Z[Europe/London]` | §3.4 Fig. 2 | Consistent; the zone is extra information |
| `1996-12-19T16:39:57-08:00` | §4.2 Fig. 4 | Plain RFC 3339 (= `1996-12-20T00:39:57Z`) |
| `1996-12-19T16:39:57-08:00[America/Los_Angeles]` | §4.2 Fig. 5 | Same instant, with a zone |
| `1996-12-19T16:39:57-08:00[America/Los_Angeles][u-ca=hebrew]` | §4.2 Fig. 6 | Same instant; present in the Hebrew calendar |
| `1996-12-19T16:39:57-08:00[_foo=bar][_baz=bat]` | §4.2 Fig. 7 | Experimental: MUST be rejected unless configured |

---

## Errata

| ID | Type | Status | Section | Summary | Effect on checks |
|---|---|---|---|---|---|
| 8192 | Editorial | **Rejected** (by the RFC Editor, 2024-12-11; reported by Robert Wishlaw, 2024-12-01) | §3.4 | Proposed writing "critical-flag" (hyphenated) instead of "critical flag" in the prose paragraph about offset/zone inconsistency. Rejected per the author (C. Bormann): the hyphenated form is only the ABNF rule name. Because `critical-flag` is defined as an *optional* `!`, the rule is always present, so the prose term "critical flag" (meaning the `!` itself) is the correct wording. | **None.** It does not shape any check. Common-misreading note: `critical-flag` (the ABNF rule, always present, possibly empty) is not the same as "the critical flag is used" (a `!` is present). Code that checks "critical-flag matched" instead of "`!` present" marks every tag critical. |

---

## IANA registry snapshot

- **Registry:** Timestamp Suffix Tag Keys (registry group "Internet Date/Time Format")
- **URL:** https://www.iana.org/assignments/internet-date-time-format/internet-date-time-format.xhtml (XML: https://www.iana.org/assignments/internet-date-time-format/internet-date-time-format.xml). The suggested URL `https://www.iana.org/assignments/timestamp-suffix-tag-keys/` returns **404**. The registry lives under the group page.
- **Fetch date:** 2026-09-24
- **Registry metadata:** group created 2023-10-24, last updated 2024-05-22. Reference RFC 9557. Registration rules: Permanent = Specification Required; Provisional = Expert Review. Experts: Ujjwal Sharma, Bron Gondwana.

| Key | Status | Description | Change Controller | Reference | Record date |
|---|---|---|---|---|---|
| `u-ca` | Permanent | Preferred Calendar for Presentation | IETF | RFC 9557, Section 5 | 2023-10-03 |

As of the fetch date, `u-ca` is the **only** registered key. There are no Provisional entries.

---

## Not checkable (with reason)

- **§1 Introduction, §1.1 motivation, and the list of out-of-scope features** (future local time, floating time, TAI): these describe scope. The only checkable consequence (an offset is required) is R9557-1.1-02.
- **§1.2 definitions of UTC, GMT, ABNF, IXDTF, Timestamp, CLDR, and the timescale references:** definitions with no conformance content.
- **§1.2 "IANA Time Zone" (current rules apply at the time of interpretation):** a semantic intent. The observable effect is the stale-TZDB inconsistency covered by R9557-3.4-01/02 and R9557-4.1-06. A consumer's choice of TZDB version is not checkable from code.
- **§2.1 Background:** historical rationale.
- **§3.2 the "Media Types" analogy and the expectation that registrants improve provisional specs:** registrant process, not an implementation property.
- **§6 expert instructions** (frugal allocation, self-initiated registration): IANA and expert process.
- **§7.2 "No considerations are known ... out of the ordinary":** no requirement. General hardening is in R9557-7.2-01.
- **Acknowledgements, Contributors, References:** non-normative.

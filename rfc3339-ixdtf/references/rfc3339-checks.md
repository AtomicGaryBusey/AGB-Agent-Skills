# R3339 — RFC 3339 check catalog (Date and Time on the Internet: Timestamps)

Source: `rfc/rfc3339.txt` (July 2002, Standards Track), errata `rfc/errata3339.html` (7 errata), update `rfc/rfc9557.txt` §2 (updates §4.3).
Scope: §1–§7 and Appendices A–D. RFC text © IETF Trust; short quotes are cited by section.

## Conventions used in this catalog

- **Level** is the BCP 14 keyword *as written in upper case*. RFC 3339 also uses lower-case "must/should/may" in several places (§3, §4.2 NOTE, §5.4, §5.6 NOTE, §5.7). RFC 2119 gives lower-case words no special meaning, so those checks are **informative**, and the lower-case word is quoted.
- **Grammar checks** (§5.6 ABNF + §5.7 range restrictions) have no BCP 14 keyword. They are *definitional*: a string that does not match `date-time` is not an RFC 3339 date-time. They are marked `informative (grammar — definitional)` with **Judgment: objective**. For a consumer that *claims* RFC 3339 validation, a mismatch is an objective defect. It is not a MUST violation of RFC 3339 itself.
- The §5.6 profile as a whole is only **SHOULD** for new protocols (§5.6 first sentence). A protocol may adopt it with extra constraints (for example, the §5.6 NOTE lets it require upper case), but it cannot loosen it and still claim the profile.
- **UPDATED BY RFC 9557 §x** marks a check whose meaning RFC 9557 changes.
- Errata status is shown as it appears on the errata page. Rejected errata: none exist for RFC 3339.
- Test-input notation: `✓` = must be accepted (valid) · `✗` = must be rejected (invalid) · `≡` = same instant.

---

## ABNF (verbatim)

### §5.6 Internet Date/Time Format (normative profile)

```
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

The two NOTEs that follow the rules (§5.6, verbatim):

```
      NOTE: Per [ABNF] and ISO8601, the "T" and "Z" characters in this
      syntax may alternatively be lower case "t" or "z" respectively.

      This date/time format may be used in some environments or contexts
      that distinguish between the upper- and lower-case letters 'A'-'Z'
      and 'a'-'z' (e.g. XML).  Specifications that use this format in
      such environments MAY further limit the date/time syntax so that
      the letters 'T' and 'Z' used in the date/time syntax must always
      be upper case.  Applications that generate this format SHOULD use
      upper case letters.

      NOTE: ISO 8601 defines date and time separated by "T".
      Applications using this syntax may choose, for the sake of
      readability, to specify a full-date and full-time separated by
      (say) a space character.
```

Core rules imported from [ABNF] (RFC 2234 at publication, now RFC 5234): `DIGIT = %x30-39` (ASCII 0–9 only). Quoted string literals in ABNF are **case-insensitive** (RFC 2234 §2.3). This is why `"T"`/`"Z"` also match `t`/`z`.

### Appendix A ISO 8601 Collected ABNF (informative; "informational only and may contain errors")

```
   date-century    = 2DIGIT  ; 00-99
   date-decade     =  DIGIT  ; 0-9
   date-subdecade  =  DIGIT  ; 0-9
   date-year       = date-decade date-subdecade
   date-fullyear   = date-century date-year
   date-month      = 2DIGIT  ; 01-12
   date-wday       =  DIGIT  ; 1-7  ; 1 is Monday, 7 is Sunday
   date-mday       = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on
                             ; month/year
   date-yday       = 3DIGIT  ; 001-365, 001-366 based on year
   date-week       = 2DIGIT  ; 01-52, 01-53 based on year

   datepart-fullyear = [date-century] date-year ["-"]
   datepart-ptyear   = "-" [date-subdecade ["-"]]
   datepart-wkyear   = datepart-ptyear / datepart-fullyear

   dateopt-century   = "-" / date-century
   dateopt-fullyear  = "-" / datepart-fullyear
   dateopt-year      = "-" / (date-year ["-"])
   dateopt-month     = "-" / (date-month ["-"])
   dateopt-week      = "-" / (date-week ["-"])

   datespec-full     = datepart-fullyear date-month ["-"] date-mday
   datespec-year     = date-century / dateopt-century date-year
   datespec-month    = "-" dateopt-year date-month [["-"] date-mday]
   datespec-mday     = "--" dateopt-month date-mday
   datespec-week     = datepart-wkyear "W"
                       (date-week / dateopt-week date-wday)
   datespec-wday     = "---" date-wday
   datespec-yday     = dateopt-fullyear date-yday

   date              = datespec-full / datespec-year
                       / datespec-month /
   datespec-mday / datespec-week / datespec-wday / datespec-yday

Time:

   time-hour         = 2DIGIT ; 00-24
   time-minute       = 2DIGIT ; 00-59
   time-second       = 2DIGIT ; 00-58, 00-59, 00-60 based on
                              ; leap-second rules
   time-fraction     = ("," / ".") 1*DIGIT
   time-numoffset    = ("+" / "-") time-hour [[":"] time-minute]
   time-zone         = "Z" / time-numoffset

   timeopt-hour      = "-" / (time-hour [":"])
   timeopt-minute    = "-" / (time-minute [":"])

   timespec-hour     = time-hour [[":"] time-minute [[":"] time-second]]
   timespec-minute   = timeopt-hour time-minute [[":"] time-second]
   timespec-second   = "-" timeopt-minute time-second
   timespec-base     = timespec-hour / timespec-minute / timespec-second

   time              = timespec-base [time-fraction] [time-zone]

   iso-date-time     = date "T" time

Durations:

   dur-second        = 1*DIGIT "S"
   dur-minute        = 1*DIGIT "M" [dur-second]
   dur-hour          = 1*DIGIT "H" [dur-minute]
   dur-time          = "T" (dur-hour / dur-minute / dur-second)
   dur-day           = 1*DIGIT "D"
   dur-week          = 1*DIGIT "W"
   dur-month         = 1*DIGIT "M" [dur-day]
   dur-year          = 1*DIGIT "Y" [dur-month]
   dur-date          = (dur-day / dur-month / dur-year) [dur-time]

   duration          = "P" (dur-date / dur-time / dur-week)

Periods:

   period-explicit   = iso-date-time "/" iso-date-time
   period-start      = iso-date-time "/" duration
   period-end        = duration "/" iso-date-time

   period            = period-explicit / period-start / period-end
```

(The page-break header/footer lines inside Appendix A have been removed. Nothing else has changed.)

### Reference regex for the §5.6 `date-time` production (syntax only; §5.7 range checks are still necessary)

```
^([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(\.[0-9]+)?([Zz]|[+-][0-9]{2}:[0-9]{2})$
```
Use `[0-9]` and not `\d`, because `\d` matches non-ASCII digits in Unicode-aware engines (see R3339-5.6-17). Anchor the whole string.

---

## Errata (all 7)

| ID | Type | Status | Section | What it changes | Effect on checks |
|---|---|---|---|---|---|
| 293 | Editorial | Verified | §5.1 (notes also propose an Appendix A change) | §5.1 last sentence becomes: "If the format allows optional punctuation or white space then this characteristic can be violated." The notes also propose that Appendix A `time-hour` becomes `00-23` and that `timespec-midnight = "24" [[":"] "00" [[":"] "00"]]` is added (ISO 8601:2000: hour 24 only for midnight). | Shapes **R3339-5.1-01/02**: white space (for example, a space separator) and optional punctuation also break string sortability. Appendix A part: informative only. §5.6 already forbids hour 24 (R3339-5.7-08). |
| 1584 | Editorial | Verified | Appendix A | Deletes the claim that ISO 8601 is unclear on mixing basic and extended format. It keeps only "This grammar permits mixtures of basic and extended format." ISO 8601:2000 §5.4.2 d) forbids mixtures. | Informative. Supports **R3339-A-02**: mixed basic/extended strings are not ISO-conformant and are never valid RFC 3339 (§5.6 is fully extended format). |
| 3710 | Editorial | Verified | §6 [IERS] | Corrects the IERS bulletins URL (adds the missing `bulletins/` path segment). | No check. Listed under non-checkable content (reference hygiene). |
| 4110 | Technical | Verified | Appendix A | Replaces the "fraction preceded by a '0'" paragraph: "ISO 8601/Cor1:1991 also requires (in section 5.3.1.3) that a decimal fraction be proceeded by "00" if less than unity." Notes: the RFC 3339 grammar "never allowed just one zero" and complies with Cor 1. Authors' note: 5.3.1.3 and Annex B.2 need not conflict. AD note: ISO 8601:2004 exists but is not normative for this RFC. | No change to the §5.6 grammar. It shapes **R3339-A-03**: do not accept "fraction without its integer part" forms such as `23:20:.5` or `23:20:50.`. Seconds are always `2DIGIT`, followed by `"." 1*DIGIT`. |
| 5624 | Editorial | Held for Document Update | §5.6 | Proposes a paragraph: 'full-time' is for precise timestamps. Other productions ('full-date', 'full-time', 'partial-time') "may be referenced by applications that have different requirements". | Shapes **R3339-5.6-18**: schemas may legitimately reference `full-date`/`full-time`/`partial-time` alone (JSON Schema `date`, `time`). Such values are not full timestamps. Held status: guidance, not text of record. |
| 5783 | Technical | Held for Document Update | §5.6 | Reports an ambiguity: the ABNF allows only `T`/`t`, but the NOTE says applications "may choose" a space separator. No fix proposed. | Shapes **R3339-5.6-15**: space-separated values do not match `date-time`. Accepting or emitting a space is an application profile choice, and the profile must document it. Held status: the ambiguity is acknowledged and unresolved. |
| 6533 | Editorial | Held for Document Update | Table of Contents | Changes a stray comma to a period in the ToC dot leader for Appendix D. | No check (typographic). |

Notes: RFC 3339 has no Rejected or Reported errata, so no "common misreading from rejected erratum" notes apply. The errata page lists RFC 3339 as "Updated by: RFC9557".

---

## §1 Introduction

### R3339-1-01 — Years 0000–9999 are in scope; no expanded or negative years
- **Section:** §1 ("somewhere between 0000AD and 9999AD"), with §5.6 `date-fullyear = 4DIGIT`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** All dates are in the "current era", 0000–9999. The grammar allows exactly four digits, so `0000` is syntactically valid and years ≥10000, signed years and BCE years cannot be represented.
- **Detect:** *producer*: formatting of `datetime.min`, `year < 1000` without zero-pad (`%Y` on some platforms gives `"999"`), and years > 9999 (JS `toISOString()` emits `+010000-01-01T…`). *Consumer*: check that the parser does not reject `0000`/`0001`–`0999` and does reject `+002020`/`-0001`/`10000`. *Schema*: `minimum`/`maximum` year constraints and their documentation.
- **Test inputs:** `0000-01-01T00:00:00Z` ✓ · `0999-12-31T23:59:59Z` ✓ · `+012020-01-01T00:00:00Z` ✗ · `10000-01-01T00:00:00Z` ✗
- **Judgment:** objective

### R3339-1-02 — Every timestamp has a stated UTC relationship
- **Section:** §1 ("All times expressed have a stated relationship (offset) to Coordinated Universal Time"), §4.4
- **Level:** informative (grammar — definitional; `full-time` requires `time-offset`)
- **Roles:** producer, consumer, schema
- **Requirement:** A timestamp without an offset (floating or local time) is outside RFC 3339. See R3339-5.6-10 for the grammar check and R3339-4.4-03 for producers.
- **Detect:** grep for docs or schemas that call offset-less strings "RFC 3339" (`"format": "date-time"` fields filled from naive datetimes; OpenAPI examples such as `2024-01-01T10:00:00`).
- **Test inputs:** `2005-03-23T17:00:00` ✗ (no offset) · `2005-03-23T17:00:00-05:00` ✓
- **Judgment:** objective

### R3339-1-03 — Timestamps before UTC existed are allowed
- **Section:** §1 ("Timestamps can express times that occurred before the introduction of UTC … using the best available practice")
- **Level:** informative
- **Roles:** consumer, schema
- **Requirement:** Consumers and schemas must not reject pre-1972 (or pre-1960) timestamps on the grounds that UTC did not exist.
- **Detect:** validators with `year >= 1970` guards, and Unix-epoch-only parsing (`strptime` → `mktime` failing on negative epoch, Windows `localtime` failing before 1970).
- **Test inputs:** `1937-01-01T12:00:27.87+00:20` ✓ · `1066-10-14T09:00:00Z` ✓
- **Judgment:** heuristic

### R3339-1-04 — Instants only; intervals, durations and periods are out of scope
- **Section:** §1 ("Date and time expressions indicate an instant in time. Description of time periods, or intervals, is not covered here.")
- **Level:** informative
- **Roles:** schema, consumer
- **Requirement:** Do not describe ISO 8601 durations (`P1D`), intervals (`a/b`) or recurring times as "RFC 3339". (RFC 3339's Appendix A shows duration/period ABNF, but it is informative only.)
- **Detect:** schema docs "RFC 3339 duration"; validators whose `date-time` accepts `/` or a `P` prefix.
- **Test inputs:** `P1DT2H` ✗ as date-time · `2020-01-01T00:00:00Z/2020-01-02T00:00:00Z` ✗ as date-time
- **Judgment:** objective

---

## §2 Definitions

### R3339-2-01 — Leap-year definition is Gregorian (4 / 100 / 400)
- **Section:** §2 "leap year", Appendix C
- **Level:** informative (definition; enforced through §5.7)
- **Roles:** producer, consumer
- **Requirement:** A year is a leap year if it is divisible by 4, except centennial years, which must also be divisible by 400.
- **Detect:** grep `% 4 == 0` / `%4==0` / `& 3` without a matching `% 100` / `% 400` test. Check hand-written day-of-month validators.
- **Test inputs:** `2000-02-29T00:00:00Z` ✓ · `1900-02-29T00:00:00Z` ✗ · `2100-02-29T00:00:00Z` ✗ · `2024-02-29T00:00:00Z` ✓
- **Judgment:** objective

### R3339-2-02 — "Z" denotes a UTC offset of 00:00 — UPDATED BY RFC 9557 §2.2
- **Section:** §2 "Z" ("denotes a UTC offset of 00:00"); RFC 9557 §2.2
- **Level:** informative (definition)
- **Roles:** consumer, producer
- **Requirement:** For instant computation, `Z`, `+00:00` and `-00:00` all identify the same instant as UTC. *UPDATED BY RFC 9557 §2.2:* the **semantics** of `Z` changed. `Z` now means "the time in UTC is known, but the offset to local time is unknown" (previously this was `-00:00`). `+00:00` keeps the meaning "UTC is the preferred reference point". The instant value is unchanged.
- **Detect:** consumers that reject `Z` or treat it as "local"; code that maps `Z` → the *local* system zone.
- **Test inputs:** `2020-06-01T12:00:00Z` ≡ `2020-06-01T12:00:00+00:00` ≡ `2020-06-01T12:00:00-00:00`
- **Judgment:** objective (instant) / editorial (semantic label)

### R3339-2-03 — A minute can have 59, 60 or 61 seconds
- **Section:** §2 "minute" ("However, see also the restrictions in section 5.7 and Appendix D for how leap seconds are denoted within minutes."), "day"
- **Level:** informative
- **Roles:** consumer
- **Requirement:** The definitions give 60 s/min and 24 h/day, but the grammar allows `:60` (R3339-5.7-03). Code that computes elapsed time from RFC 3339 strings assumes a fixed 86400 s/day. This is a local matter, but the assumption must be documented.
- **Detect:** date arithmetic on parsed components in which `:60` would overflow or crash; see R3339-5.7-09.
- **Test inputs:** difference between `1990-12-31T23:59:59Z` and `1991-01-01T00:00:00Z` (2 SI seconds; 1 in POSIX time) — document which.
- **Judgment:** heuristic

---

## §3 Two Digit Years

### R3339-3-01 — Generate four-digit years
- **Section:** §3 ("Internet Protocols MUST generate four digit years in dates.")
- **Level:** MUST
- **Roles:** producer
- **Requirement:** Every emitted year has four digits, zero-padded (`0099`, not `99` or `099`).
- **Detect:** format strings with `%y`, `yy` (Java/ICU/.NET patterns `yy-MM-dd`), `getYear()` (JS/Java legacy: returns year−1900), `tm_year` used without `+1900`, `%Y` on platforms that do not zero-pad years < 1000 (glibc `%Y` gives `"99"` for year 99; use `%4Y`/`%04d`).
- **Test inputs:** format year 99 → `0099-…` ✓; `99-01-01T00:00:00Z` ✗; `099-01-01T00:00:00Z` ✗
- **Judgment:** objective

### R3339-3-02 — Two-digit years are deprecated; accept only if misinterpretation is harmless
- **Section:** §3 ("The use of 2-digit years is deprecated. If a 2-digit year is received, it should be accepted ONLY if an incorrect interpretation will not cause a protocol or processing failure (e.g. if used only for logging or tracing purposes).")
- **Level:** informative (lower-case "should"; "ONLY" capitalised for emphasis, not a BCP 14 keyword)
- **Roles:** consumer
- **Requirement:** A lenient legacy parser may accept 2-digit years only on non-critical paths (logging, tracing). It must never accept them as RFC 3339 `date-time`, because the grammar requires `4DIGIT`.
- **Detect:** fallback parsers (`dateutil.parser.parse`, `Date.parse`, `strtotime`, `DateTime.Parse`) on paths that make security or business decisions (expiry, `not-before`, billing).
- **Test inputs:** `96-12-19T16:39:57-08:00` ✗ in a strict path; logging path may accept.
- **Judgment:** heuristic

### R3339-3-03 — Robust handling of 3-digit "year − 1900" output
- **Section:** §3 ("Programs wishing to robustly deal with dates generated by such broken software may add 1900 to three digit years.")
- **Level:** informative (lower-case "may")
- **Roles:** consumer
- **Requirement:** An optional legacy-repair heuristic (`100` → 2000). It is not RFC 3339 syntax; a strict validator rejects the input.
- **Detect:** repair logic present → must be off by default in strict validators.
- **Test inputs:** `101-05-01T00:00:00Z` ✗ strict; legacy-repair mode → 2001.
- **Judgment:** heuristic

### R3339-3-04 — Robust handling of non-numeric decades (":0", ";0")
- **Section:** §3 ("… should detect non-numeric decades and interpret appropriately.")
- **Level:** informative (lower-case "should")
- **Roles:** consumer
- **Requirement:** Only a legacy-repair heuristic (`:0` = 2000s). Strict RFC 3339 parsing rejects the input, because DIGIT is `%x30-39`.
- **Detect:** as R3339-3-03.
- **Test inputs:** `:1-01-01` ✗ strict; legacy mode → 2010s.
- **Judgment:** heuristic

### R3339-3-05 — Dates and times used in Internet protocols must be fully qualified
- **Section:** §3 ("all dates and times used in Internet protocols MUST be fully qualified")
- **Level:** MUST
- **Roles:** producer, schema
- **Requirement:** No truncated or partial forms (no omitted century, and no omitted date or time when a timestamp is meant). Together with §1 and §4.4, a timestamp carries a full date, full time and an offset.
- **Detect:** API fields documented as timestamps but populated with `HH:MM`, `MM-DD`, `YY-MM-DD` or offset-less times.
- **Test inputs:** `12-19T16:39:57Z` ✗ · `16:39` ✗ as a timestamp
- **Judgment:** objective

---

## §4 Local Time

### R3339-4.1-01 — Prefer UTC; no local-time-zone rules in the format
- **Section:** §4.1 ("true interoperability is best achieved by using Coordinated Universal Time (UTC). This specification does not cater to local time zone rules.")
- **Level:** informative
- **Roles:** producer, schema
- **Requirement:** Producers should normally emit UTC. A zone *name* (IANA tz ID, DST rule) cannot be carried in RFC 3339. (RFC 9557 adds this as a suffix — out of scope for this catalog.)
- **Detect:** producers that append `[Europe/Paris]` or ` PST` and call the result RFC 3339.
- **Test inputs:** `2022-07-08T00:14:07+02:00[Europe/Paris]` ✗ as RFC 3339 `date-time` (valid only as RFC 9557 IXDTF).
- **Judgment:** heuristic (preference) / objective (grammar)

### R3339-4.2-01 — Offsets are numeric; alphabetic zone labels are not allowed (except Z)
- **Section:** §4.2 ("Attempts to label local offsets with alphabetic strings have resulted in poor interoperability"), §5.6 `time-offset`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer
- **Requirement:** Only `Z`/`z` or `±HH:MM`. No `UTC`, `GMT`, `EST`, `CEST`, `UT`, military letters other than Z.
- **Detect:** *producer*: `%Z` in format strings, `zzz`/`z` patterns (Java `z` = short name), `toString()` of date objects. *Consumer*: parsers that accept `GMT`/`UTC` suffixes in "RFC 3339" mode.
- **Test inputs:** `2020-01-01T00:00:00UTC` ✗ · `2020-01-01T00:00:00 GMT` ✗ · `2020-01-01T00:00:00A` ✗ · `2020-01-01T00:00:00+00:00` ✓
- **Judgment:** objective

### R3339-4.2-02 — Offset sign: offset = local − UTC; UTC = local − offset
- **Section:** §4.2 ("Numeric offsets are calculated as "local time minus UTC". So the equivalent time in UTC can be determined by subtracting the offset from the local time. For example, 18:50:00-04:00 is the same time as 22:50:00Z.")
- **Level:** informative (definition; objective semantics)
- **Roles:** producer, consumer
- **Requirement:** East of Greenwich is `+`. Converting to UTC *subtracts* the signed offset.
- **Detect:** sign inversions from POSIX `TZ` strings (`EST5EDT` means UTC−5), from `timezone`/`_timezone` globals (seconds *west* of UTC), JS `getTimezoneOffset()` (returns UTC − local in minutes; positive west), and manual `utc = local + offset` code.
- **Test inputs:** `2020-01-01T18:50:00-04:00` ≡ `2020-01-01T22:50:00Z` · `1996-12-19T16:39:57-08:00` ≡ `1996-12-20T00:39:57Z` · `2020-01-01T00:30:00+01:00` ≡ `2019-12-31T23:30:00Z`
- **Judgment:** objective

### R3339-4.2-03 — Offsets are whole minutes; sub-minute historical offsets must be converted
- **Section:** §4.2 NOTE ("numeric offsets represent only time zones that differ from UTC by an integral number of minutes … applications must convert them to a representable time zone"), §5.8 (1937 example)
- **Level:** informative (lower-case "must"; grammar enforces HH:MM)
- **Roles:** producer, consumer
- **Requirement:** No offset seconds (`+00:19:32`). A producer with a sub-minute offset (tzdb LMT, Amsterdam 1909–1937) must round to a representable offset *and adjust the local time so that the instant is kept* (as in §5.8: `12:00:27.87+00:20`), or emit UTC.
- **Detect:** *producer*: Python `datetime.isoformat()` emits `+00:19:32` for such offsets (verified: `datetime(1937,1,1,12,tzinfo=timezone(timedelta(minutes=19,seconds=32))).isoformat()` → `1937-01-01T12:00:00+00:19:32`). Java `OffsetDateTime.toString()` emits `+00:19:32`. Look for truncating the offset *without* shifting the time (this changes the instant). *Consumer*: must reject `±HH:MM:SS` offsets.
- **Test inputs:** `1937-01-01T12:00:00+00:19:32` ✗ · `1937-01-01T12:00:27.87+00:20` ✓ (≡ `1937-01-01T11:40:27.87Z`) · `1937-01-01T11:40:27.87Z` ✓
- **Judgment:** objective

### R3339-4.3-01 — "-00:00" = UTC known, local offset unknown — UPDATED BY RFC 9557 §2.2
- **Section:** §4.3 ("If the time in UTC is known, but the offset to local time is unknown, this can be represented with an offset of "-00:00"."); RFC 9557 §2.2 replaces §4.3; RFC 9557 §2.3
- **Level:** informative ("can be represented"; no BCP 14 keyword)
- **Roles:** producer, consumer, schema
- **Requirement (original):** `-00:00` meant unknown local offset. `Z`/`+00:00` meant UTC is the preferred reference.
  **UPDATED BY RFC 9557 §2.2:** `Z` now means "the time in UTC is known, but the offset to local time is unknown". `-00:00` is described as the original mechanism, "not allowed by [ISO8601:2000] and therefore … less interoperable". RFC 9557 §2.3: "the present specification does not formally deprecate this syntax" and "the local offset Z should now be used in its place" (lower-case should).
  Audit result: a producer that emits `-00:00` to mean "unknown offset" is *allowed but outdated*. It should move to `Z`. A producer that emits `Z` to mean "the user's local zone really is UTC" now carries the wrong semantics. It should emit `+00:00`.
- **Detect:** grep for literal `"-00:00"` in formatters. Check the documented meaning of `Z` in API specs ("Z means the server is in UTC" → should be `+00:00` under RFC 9557).
- **Test inputs:** `2020-01-01T00:00:00-00:00` ✓ (syntax) · semantic: `Z` → "offset unknown" (RFC 9557); `+00:00` → "UTC preferred"
- **Judgment:** editorial

### R3339-4.3-02 — Consumers must accept "-00:00" syntactically and as a UTC instant
- **Section:** §4.3, §5.6 (`time-numoffset = ("+" / "-") time-hour ":" time-minute`); RFC 9557 §2.3 (not deprecated)
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, schema
- **Requirement:** `-00:00` matches the grammar and was not deprecated by RFC 9557. An RFC 3339 consumer must not reject it, although ISO 8601:2000+ parsers do. The instant equals UTC.
- **Detect:** ISO-8601-strict libraries used as "RFC 3339" validators. Code that has `if offset == "-00:00": raise`. Regexes such as `[+-](?!00:00)`.
- **Test inputs:** `2020-01-01T12:00:00-00:00` ✓ ≡ `2020-01-01T12:00:00Z`
- **Judgment:** objective

### R3339-4.3-03 — Keep the Z vs +00:00 (vs -00:00) distinction when you re-serialise — UPDATED BY RFC 9557 §2.2/§2.3
- **Section:** §4.3 ("This differs semantically from an offset of "Z" or "+00:00""); RFC 9557 §2.2, §2.3 ("the semantics of the local offset +00:00 is not updated")
- **Level:** informative
- **Roles:** producer, consumer
- **Requirement:** The three UTC-equivalent spellings carry different meanings. A pipeline that parses and re-emits timestamps (proxy, ETL, canonicaliser) loses that information if it normalises `+00:00`→`Z` or `-00:00`→`Z`. Under RFC 9557, `-00:00`→`Z` keeps the meaning and `+00:00`→`Z` does *not*. Whether to keep the spelling is an application decision. Flag it when a protocol assigns meaning to the difference.
- **Detect:** round-trip tests. Parsers whose result type has no field to hold the distinction (most do not).
- **Test inputs:** round-trip `2020-01-01T00:00:00+00:00` → emitted as `…Z`? (flag if the protocol assigns meaning) · `…-00:00` → `…Z` (fine under RFC 9557)
- **Judgment:** heuristic

### R3339-4.4-01 — Local-clock systems that sync with others MUST use a UTC-correct mechanism
- **Section:** §4.4 ("Systems that are configured with a local time, are unaware of the corresponding UTC offset, and depend on time synchronization with other Internet systems, MUST use a mechanism that ensures correct synchronization with UTC.")
- **Level:** MUST
- **Roles:** producer
- **Requirement:** Suggested mechanisms: NTP, a local-zone gateway host, or prompting the user for the zone and DST rules.
- **Detect:** devices/services that emit timestamps from an RTC in local time with a hard-coded `+00:00`/`Z`. Config that has no TZ/NTP setting.
- **Test inputs:** n/a (deployment review); runtime: compare emitted `Z` time with an NTP reference.
- **Judgment:** heuristic

### R3339-4.4-02 — A gateway host MUST correct unqualified local times it forwards
- **Section:** §4.4 ("This host MUST correct unqualified local times that are transmitted to other hosts.")
- **Level:** MUST
- **Roles:** producer
- **Requirement:** A relay/gateway that receives offset-less local times from local devices must convert them to UTC or add the correct offset before it forwards them.
- **Detect:** log shippers, IoT gateways and syslog relays that forward device timestamps verbatim, or that append `Z` without converting.
- **Test inputs:** device sends `2020-01-01T09:00:00` (local, UTC−5) → gateway must emit `2020-01-01T14:00:00Z` or `…09:00:00-05:00`, never `…09:00:00Z`.
- **Judgment:** heuristic

### R3339-4.4-03 — Never emit unqualified local time or append Z to local time
- **Section:** §4.4 ("the interoperability problems of unqualified local time are deemed unacceptable for the Internet"), §1, §5.6
- **Level:** informative (grammar requires an offset; §4.4 text has no keyword here)
- **Roles:** producer
- **Requirement:** Emitted timestamps include the true offset. A classic bug is formatting local wall-clock time and adding a literal `Z`.
- **Detect:** Python `datetime.now().isoformat()` (naive → no offset), `datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")`; Java `LocalDateTime.toString()`, `SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'")` without `setTimeZone(UTC)`; JS string concatenation of `getHours()` + `"Z"`; Go `t.Format("2006-01-02T15:04:05Z")` (literal Z) on non-UTC `t`; SQL `to_char(now(), '…"Z"')`.
- **Test inputs:** run the producer with `TZ=America/New_York` and compare with `TZ=UTC`. The instant must be the same.
- **Judgment:** objective (when reproduced) / heuristic (static)

---

## §5.1–§5.5 Format properties

### R3339-5.1-01 — Lexical sort equals time order only under stated conditions (errata 293)
- **Section:** §5.1; errata 293 (Editorial, Verified) rewords the last sentence to: "If the format allows optional punctuation or white space then this characteristic can be violated."
- **Level:** informative
- **Roles:** consumer, schema
- **Requirement:** `strcmp` ordering matches time order only if all values (a) use the same offset, (b) use the same spelling for it (all `Z` or all `+00:00`), and (c) have the same number of fractional digits. Per errata 293, (d) no optional punctuation or white space may vary (for example, `T` vs space, or `T` vs `t`, since `'t'` > `'T'`).
- **Detect:** `ORDER BY` on text/varchar timestamp columns. `sorted()`/`Array.prototype.sort()` on raw strings. Key-value stores keyed by timestamp strings (S3 prefixes, DynamoDB sort keys, Redis ZSET lex). Then check whether producers ensure (a)–(d).
- **Test inputs:** `2020-01-01T00:00:00Z` vs `2020-01-01T00:00:00.5Z`: lexical order puts `.5Z` first (`.`=0x2E < `Z`=0x5A), but it is later (verified) ✗ for string sort · `2020-01-01T01:00:00+01:00` vs `2020-01-01T00:30:00Z`: string sort gives the wrong order ✗
- **Judgment:** objective (given the data) / heuristic (static)

### R3339-5.1-02 — Producers intended for sortable output use a canonical form
- **Section:** §5.1, §5.3 (fractions used by "applications which require strict ordering")
- **Level:** informative
- **Roles:** producer
- **Requirement:** If downstream code sorts strings, the producer should emit a fixed offset (normally `Z`), a fixed fractional-digit count (for example, always 3 or always 6, including trailing zeros), upper-case `T`/`Z`, and no space separator.
- **Detect:** `isoformat()` in Python drops the fraction when microseconds == 0 (produces a variable length). JS `toISOString()` is fixed at 3 digits (good). Go `time.RFC3339Nano` *trims trailing zeros* (variable length; for output use a fixed layout `…05.000000000Z07:00` instead. Do not reuse it as a parse layout: it rejects valid input with fewer fraction digits; parse with `time.RFC3339`).
- **Test inputs:** format two instants 500 ms apart, one on a whole second; verify equal length.
- **Judgment:** objective (runtime) / heuristic (static)

### R3339-5.2-01 — Clients should transform timestamps for local display
- **Section:** §5.2 ("Internet clients SHOULD be prepared to transform dates into a display format suitable for the locality. This may include translating UTC to local time.")
- **Level:** SHOULD
- **Roles:** consumer
- **Requirement:** Use the wire format for interchange. User-facing UIs should localise it, and must not show the raw RFC 3339 string as the only presentation (not required).
- **Detect:** UI templates that render timestamp fields raw.
- **Test inputs:** n/a (UI review)
- **Judgment:** heuristic

### R3339-5.2-02 — Never use locale-dependent or ctime-style formats on the wire
- **Section:** §5.2 ("the date format "10/11/1996" is completely unsuitable for global interchange"; translated month abbreviations; ctime substitutions)
- **Level:** informative
- **Roles:** producer, schema
- **Requirement:** Wire/serialised timestamps must not be locale-formatted.
- **Detect:** `toLocaleString()`, `strftime("%c")`, `%x`, `DateFormat.getDateTimeInstance()`, `ctime()`/`asctime()`, `Date.toString()` feeding API/JSON/log output. Culture-sensitive `.ToString()` in .NET without `CultureInfo.InvariantCulture`.
- **Test inputs:** `10/11/1996` ✗ · `Thu Dec 19 16:39:57 1996` ✗
- **Judgment:** objective (grammar) / heuristic (static)

### R3339-5.3-01 — Fractional seconds is the one optional part; consumers must handle it
- **Section:** §5.3 ("The format defined below includes only one rarely used option: fractions of a second."), §5.6 `[time-secfrac]`
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, schema
- **Requirement:** Because fractions are rarely sent, parsers are often untested with them. An RFC 3339 consumer must accept both forms, with and without a fraction.
- **Detect:** parsers built on a single fixed layout (`"%Y-%m-%dT%H:%M:%S%z"`, Java `"yyyy-MM-dd'T'HH:mm:ssXXX"`) that reject fractions. Or the reverse (`…%S.%f%z` requiring a fraction).
- **Test inputs:** `1985-04-12T23:20:50Z` ✓ · `1985-04-12T23:20:50.52Z` ✓ · `1985-04-12T23:20:50.123456789Z` ✓
- **Judgment:** objective

### R3339-5.3-02 — Emit fractional seconds only when ordering/precision needs them
- **Section:** §5.3 ("It is expected that this will be used only by applications which require strict ordering of date/time stamps or which have an unusual precision requirement."), §5.3 ("Rarely used options should be made mandatory or omitted")
- **Level:** informative (lower-case "should")
- **Roles:** producer, schema
- **Requirement:** A protocol should either always or never include fractions ("made mandatory or omitted"). It should not emit them sometimes (compare R3339-5.1-02).
- **Detect:** producers whose fraction presence depends on the value (Python `isoformat()`, Go `RFC3339Nano`). Schemas that leave fraction presence unspecified.
- **Test inputs:** instant with 0 µs → does the output lose `.000000`? Flag it for protocols with fractions.
- **Judgment:** heuristic

### R3339-5.4-01 — Do not include redundant fields (day of week)
- **Section:** §5.4 ("the day of week should not be included in a date/time format")
- **Level:** informative (lower-case "should")
- **Roles:** producer, schema, consumer
- **Requirement:** No weekday or other redundant data. The grammar has no place for it anyway. If a legacy format contains a weekday, consumers must decide which field wins (they can conflict).
- **Detect:** producers `%a`/`EEE`/`ddd` in a "RFC 3339" pattern. Consumers accepting `Fri, 1985-04-12…`.
- **Test inputs:** `Fri 1985-04-12T23:20:50Z` ✗ · `1985-04-12T23:20:50Z` ✓
- **Judgment:** objective (grammar) / editorial (other redundant fields)

### R3339-5.5-01 — Only the §5.6 profile: full extended format, mandatory punctuation, no other ISO 8601 forms
- **Section:** §5.5 ("It is a conformant subset of the ISO 8601 extended format. Simplicity is achieved by making most fields and punctuation mandatory.")
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, schema
- **Requirement:** Reject ISO 8601 forms that are outside the profile: basic format, reduced precision (no seconds, no minutes), week dates, ordinal dates, comma decimal sign, offsets without a colon or minutes, and hour 24.
- **Detect:** consumers that call a general ISO 8601 parser (`dateutil.isoparse`, Python ≥3.11 `datetime.fromisoformat`, Joda/`java.time` `ISO_DATE_TIME` variants, `moment(…, moment.ISO_8601)`) as an "RFC 3339" validator. Verified locally: Python `fromisoformat` accepts `1985-04-12 23:20:50Z` and `1985-04-12T23:20:50,5Z` (both non-RFC 3339 per ABNF) and rejects `1985-04-12t23:20:50z` (valid RFC 3339).
- **Test inputs:** `19850412T232050Z` ✗ · `1985-04-12T23:20Z` ✗ · `1985-W15-5T23:20:50Z` ✗ · `1985-102T23:20:50Z` ✗
- **Judgment:** objective

---

## §5.6 Internet Date/Time Format — grammar

### R3339-5.6-01 — The profile SHOULD be used in new protocols
- **Section:** §5.6 ("The following profile of ISO 8601 [ISO8601] dates SHOULD be used in new protocols on the Internet.")
- **Level:** SHOULD
- **Roles:** schema
- **Requirement:** New protocol and API specs should specify §5.6 `date-time` (or a subset production). If a spec uses another format (epoch numbers, RFC 5322 dates, custom), it should justify that choice.
- **Detect:** OpenAPI/JSON Schema string timestamp fields without `format: date-time`. Proto `string` timestamp fields without a documented format. Field docs that say "ISO 8601" with no profile.
- **Test inputs:** n/a (spec review)
- **Judgment:** editorial

### R3339-5.6-02 — date-fullyear: exactly 4 ASCII digits
- **Section:** §5.6 `date-fullyear = 4DIGIT`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** Exactly four digits; no sign, no expanded representation. Range 0000–9999.
- **Detect:** regexes `\d{4,}`, `\d+`, `[+-]?\d{4}`. JS `toISOString()` for years outside 0–9999 emits `±YYYYYY`.
- **Test inputs:** `2020-01-01T00:00:00Z` ✓ · `202-01-01T00:00:00Z` ✗ · `-2020-01-01T00:00:00Z` ✗ · `20200-01-01T00:00:00Z` ✗
- **Judgment:** objective

### R3339-5.6-03 — date-month: exactly 2 digits, 01–12
- **Section:** §5.6 `date-month = 2DIGIT ; 01-12`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** Zero-padded, 01–12. `00` and `13` are out of range.
- **Detect:** regex `\d{2}` without a range check. `%m` vs `%-m`. `strptime` implementations that accept single digits (glibc `%m` accepts `1`).
- **Test inputs:** `2020-00-10T00:00:00Z` ✗ · `2020-13-10T00:00:00Z` ✗ · `2020-1-10T00:00:00Z` ✗ · `2020-12-10T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-04 — date-mday: exactly 2 digits, 01–28/29/30/31 by month/year
- **Section:** §5.6 `date-mday = 2DIGIT ; 01-28, 01-29, 01-30, 01-31 based on month/year`; §5.7 table
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** Zero-padded; `00` invalid; upper bound per R3339-5.7-01.
- **Detect:** regexes `(0[1-9]|[12]\d|3[01])` with no month-aware check (many JSON Schema validators and hand-written regexes).
- **Test inputs:** `2020-01-00T00:00:00Z` ✗ · `2020-01-32T00:00:00Z` ✗ · `2020-01-5T00:00:00Z` ✗ · `2020-01-31T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-05 — time-hour: exactly 2 digits, 00–23
- **Section:** §5.6 `time-hour = 2DIGIT ; 00-23`; §5.7 (no "24")
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** 00–23 only. 12-hour clock values with AM/PM are invalid.
- **Detect:** `%I`/`hh` (12-hour) in producer patterns (a common Java `hh` vs `HH` bug). Regexes `[0-2]\d`.
- **Test inputs:** `2020-01-01T24:00:00Z` ✗ · `2020-01-01T29:00:00Z` ✗ · `2020-01-01T7:00:00Z` ✗ · `2020-01-01T23:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-06 — time-minute: exactly 2 digits, 00–59
- **Section:** §5.6 `time-minute = 2DIGIT ; 00-59`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** 00–59. There is no leap minute.
- **Detect:** regex `[0-5]\d` vs `\d\d`. Java `mm` vs `MM` confusion in producers (month emitted as minute).
- **Test inputs:** `2020-01-01T00:60:00Z` ✗ · `2020-01-01T00:5:00Z` ✗ · `2020-01-01T00:59:00Z` ✓
- **Judgment:** objective

### R3339-5.6-07 — time-second: exactly 2 digits, mandatory
- **Section:** §5.6 `time-second = 2DIGIT ; 00-58, 00-59, 00-60 based on leap second rules`; `partial-time` requires it
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** Seconds cannot be omitted. The range is 00–59, 60 only at a leap second (R3339-5.7-03/04), and 58 max in a negative leap second minute (R3339-5.7-05).
- **Detect:** producers that use `HH:mm` patterns or `toISOString().slice(0,16)`. Consumers that accept `T12:00Z`.
- **Test inputs:** `2020-01-01T12:00Z` ✗ · `2020-01-01T12:00:61Z` ✗ · `2020-01-01T12:00:5Z` ✗ · `2020-01-01T12:00:05Z` ✓
- **Judgment:** objective

### R3339-5.6-08 — time-secfrac: "." then one or more digits, unbounded length
- **Section:** §5.6 `time-secfrac = "." 1*DIGIT`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** (a) The decimal sign is `.` only (not `,`, which ISO 8601 allows). (b) At least 1 digit. (c) No upper limit on the digit count. The grammar allows any length, so a consumer must accept long fractions. Truncating or rounding to its own resolution is a local matter, but it must not reject the input. (d) The fraction follows seconds only (there are no fractional minutes or hours).
- **Detect:** regexes `\.\d{1,3}`, `\.\d{3}`, `\.\d{1,9}` (reject >9 digits). Java `DateTimeFormatter` patterns with fixed `SSS`. .NET `fffffff` (max 7). Go accepts any length (good). Check the rounding direction: rounding up `59.9999999999` can carry into the next minute/day, while truncation is safer for ordering.
- **Test inputs:** `2020-01-01T00:00:00.Z` ✗ · `2020-01-01T00:00:00,5Z` ✗ · `2020-01-01T00:00:00.5Z` ✓ · `2020-01-01T00:00:00.123456789012Z` ✓
- **Judgment:** objective

### R3339-5.6-09 — time-numoffset: sign, 2-digit hour 00–23, colon, 2-digit minute 00–59
- **Section:** §5.6 `time-numoffset = ("+" / "-") time-hour ":" time-minute`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** The sign is mandatory (ASCII `+`/`-` only; not U+2212 MINUS SIGN), the colon is mandatory, and the minutes are mandatory. The offset hour reuses `time-hour` (00–23) and the minute reuses `time-minute` (00–59). The full grammatical range is −23:59 … +23:59. Consumers must not reject valid offsets beyond real-world zones (for example, `+23:00`). Java `ZoneOffset` caps at ±18:00, which makes `+19:00` unparseable even though it is valid RFC 3339.
- **Detect:** *producer*: `%z` (emits `+0000`, no colon), Java `Z`/`xx` patterns (no colon; use `XXX`/`xxx`), Go layout `-0700` (use `Z07:00`), Moment `ZZ`. *Consumer*: regexes `[+-]\d{2}:?\d{2}`, `[+-]\d{2}(:\d{2})?`, and range caps.
- **Test inputs:** `2020-01-01T00:00:00+0100` ✗ · `2020-01-01T00:00:00+01` ✗ · `2020-01-01T00:00:00+24:00` ✗ · `2020-01-01T00:00:00+23:59` ✓
- **Judgment:** objective

### R3339-5.6-10 — time-offset is mandatory in full-time / date-time
- **Section:** §5.6 `full-time = partial-time time-offset`, `time-offset = "Z" / time-numoffset`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** A `date-time` without an offset is invalid. Consumers must not silently assume local time or UTC for offset-less input when they claim RFC 3339.
- **Detect:** parsers that return a naive or local value for missing offsets (JS `new Date("2020-01-01T00:00:00")` treats it as *local*; `Date.parse` of a date-only string treats it as *UTC*). JSON Schema validators that accept a missing offset.
- **Test inputs:** `2020-01-01T00:00:00` ✗ · `2020-01-01T00:00:00.123` ✗ · `2020-01-01T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-11 — date-time uses a single "T" separator between full-date and full-time
- **Section:** §5.6 `date-time = full-date "T" full-time`
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** Exactly one `T` (or `t`, R3339-5.6-12). No separator, a double separator, `_` or `/` all fail. For a space, see R3339-5.6-15.
- **Detect:** regexes `[T ]`, `[Tt\s]`, `.` (any char).
- **Test inputs:** `2020-01-0100:00:00Z` ✗ · `2020-01-01_00:00:00Z` ✗ · `2020-01-01TT00:00:00Z` ✗ · `2020-01-01T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-12 — Consumers accept lower-case "t" and "z" (ABNF case-insensitivity)
- **Section:** §5.6 NOTE ("Per [ABNF] and ISO8601, the "T" and "Z" characters in this syntax may alternatively be lower case "t" or "z" respectively.")
- **Level:** informative (grammar — definitional via ABNF RFC 2234 §2.3; "may" is lower case)
- **Roles:** consumer, schema
- **Requirement:** A generic RFC 3339 consumer accepts `t`/`z`. The only exception is a spec that invokes the MAY in R3339-5.6-14 to require upper case. A plain "RFC 3339" validator that rejects lower case is non-conformant with the ABNF.
- **Detect:** regexes with literal `T`/`Z` and no `(?i)` or `[Tt]`/`[Zz]`. Verified: Python `datetime.fromisoformat('1985-04-12t23:20:50z')` raises ValueError. Verified: Go 1.27.1 `time.Parse(time.RFC3339, …)` (and `UnmarshalJSON`, `encoding/json/v2`) rejects both `t` and `z`.
- **Test inputs:** `1985-04-12t23:20:50.52z` ✓ · `1985-04-12T23:20:50.52z` ✓ · `1985-04-12t23:20:50-08:00` ✓
- **Judgment:** objective

### R3339-5.6-13 — Producers SHOULD emit upper-case "T" and "Z"
- **Section:** §5.6 NOTE ("Applications that generate this format SHOULD use upper case letters.")
- **Level:** SHOULD
- **Roles:** producer
- **Requirement:** Emit `T` and `Z`, not `t`/`z`.
- **Detect:** format strings containing `'t'`, `'z'` literals; `.toLowerCase()` applied to serialised timestamps (for example, in normalised keys or URLs).
- **Test inputs:** output `2020-01-01t00:00:00z` → flag · `2020-01-01T00:00:00Z` → pass
- **Judgment:** objective

### R3339-5.6-14 — Specs in case-sensitive contexts MAY require upper-case T/Z
- **Section:** §5.6 NOTE ("Specifications that use this format in such environments MAY further limit the date/time syntax so that the letters 'T' and 'Z' used in the date/time syntax must always be upper case.")
- **Level:** MAY
- **Roles:** schema, consumer
- **Requirement:** A profile may restrict to upper case (XML Schema `xs:dateTime` effectively does). If it does, the restriction must be *stated* in the spec, and consumers following that spec may then reject `t`/`z`. Rejecting lower case without such a statement is the defect in R3339-5.6-12.
- **Detect:** compare the validator behaviour with the spec text. Look for an explicit upper-case clause.
- **Test inputs:** under an upper-case-only profile: `2020-01-01t00:00:00z` ✗; otherwise ✓.
- **Judgment:** editorial

### R3339-5.6-15 — Space separator: allowed only as a documented application choice (errata 5783)
- **Section:** §5.6 second NOTE ("Applications using this syntax may choose, for the sake of readability, to specify a full-date and full-time separated by (say) a space character."); errata 5783 (Technical, Held for Document Update: ABNF vs NOTE ambiguity)
- **Level:** informative (lower-case "may"; the ABNF does not match a space)
- **Roles:** producer, consumer, schema
- **Requirement:** `2020-01-01 00:00:00Z` does **not** match `date-time`. An application or spec may define a profile that uses a space, but must say so. Generic RFC 3339 validators (for example, JSON Schema `format: date-time`, which references the ABNF) should reject a space. Producers of machine-interchange data should use `T` (§5.1 sortability, errata 293).
- **Detect:** *producer*: Python `str(datetime)` / `isoformat(sep=' ')`, SQL `timestamptz::text` in PostgreSQL (`2020-01-01 00:00:00+00` — also no colon or minutes in the offset, which is doubly non-conformant), Go `time.DateTime` layouts with an offset. *Consumer*: regexes `[Tt ]`. Check whether the documentation says "space accepted".
- **Test inputs:** `2020-01-01 00:00:00Z` ✗ under strict ABNF, ✓ only under a documented profile · `2020-01-01 00:00:00+00` ✗ always (offset form)
- **Judgment:** heuristic

### R3339-5.6-16 — The whole string must match; no surrounding white space or trailing data
- **Section:** §5.6 (ABNF production defines the entire value)
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, schema
- **Requirement:** Validators must anchor the match. Leading and trailing spaces, newlines and trailing garbage are invalid.
- **Detect:** Python `re.match` without `$`/`\Z`, or with `$` (which matches before a trailing `\n`; use `re.fullmatch` or `\Z`). JS regexes without `^…$`. Lenient `strptime` prefix parsing. `Date.parse` tolerance.
- **Test inputs:** ` 2020-01-01T00:00:00Z` ✗ · `2020-01-01T00:00:00Z\n` ✗ · `2020-01-01T00:00:00Zjunk` ✗ · `2020-01-01T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-17 — DIGIT is ASCII 0–9 only
- **Section:** §5.6 (ABNF core rule `DIGIT = %x30-39`)
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, schema
- **Requirement:** Reject non-ASCII digits (Arabic-Indic, full-width, etc.), even though many runtimes convert them to numbers.
- **Detect:** Python `re` `\d` on `str` patterns matches Unicode digits, and `int()` accepts them (verified: `re.fullmatch(r'\d{4}','٢٠٢٠')` → match, `int('٢٠٢٠')` → 2020). .NET `\d` is also Unicode unless `RegexOptions.ECMAScript`. Use `[0-9]` or ASCII flags.
- **Test inputs:** `٢٠٢٠-01-01T00:00:00Z` ✗ · `２０２０-01-01T00:00:00Z` ✗ (full-width) · `2020-01-01T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.6-18 — Sub-productions (full-date, partial-time, full-time) are legitimate on their own (errata 5624)
- **Section:** §5.6 ABNF; errata 5624 (Editorial, Held for Document Update: "Other productions (e.g. 'full-date', 'full-time', 'partial-time' may be referenced by applications that have different requirements.")
- **Level:** informative
- **Roles:** schema, consumer
- **Requirement:** Schemas may use `full-date` (a date) or `full-time` (a time *with* an offset) on their own. Each must be validated against its own production. `full-time` still requires an offset. `partial-time` has none. Such values are not timestamps (instants) and must not be documented as such.
- **Detect:** JSON Schema `format: "time"` (= RFC 3339 `full-time`) validators that accept `12:00:00` without an offset. `format: "date"` validators that accept `2020-1-1` or a date-time. Docs that call a `full-date` a "timestamp".
- **Test inputs:** `full-date`: `2020-02-29` ✓, `2021-02-29` ✗ · `full-time`: `23:20:50.52Z` ✓, `23:20:50` ✗ · `partial-time`: `23:20:50` ✓
- **Judgment:** objective

### R3339-5.6-19 — Hyphen and colon separators are mandatory and exact
- **Section:** §5.6 `full-date` (`"-"`), `partial-time` (`":"`), `time-numoffset` (`":"`)
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, producer
- **Requirement:** Only ASCII `-` (U+002D) and `:` (U+003A). No `/`, `.`, en-dash, U+2010 hyphen or full-width colon. No omission (that is basic format, R3339-5.5-01).
- **Detect:** regexes that use `.` or `[-/]` between fields. Locale-specific producers.
- **Test inputs:** `2020/01/01T00:00:00Z` ✗ · `2020-01-01T00.00.00Z` ✗ · `2020‐01‐01T00:00:00Z` (U+2010) ✗
- **Judgment:** objective

---

## §5.7 Restrictions

### R3339-5.7-01 — Day-of-month maximum by month and year
- **Section:** §5.7 table (Jan 31, Feb 28 / 29 leap, Mar 31, Apr 30, May 31, Jun 30, Jul 31, Aug 31, Sep 30, Oct 31, Nov 30, Dec 31)
- **Level:** informative (grammar — definitional; restriction on `date-mday`)
- **Roles:** consumer, schema, producer
- **Requirement:** Enforce the table. A validator that checks only `01–31` accepts impossible dates. A parser that normalises (for example, `2021-02-30` → March 2) is a silent-acceptance defect.
- **Detect:** JS `new Date("2021-02-30T00:00:00Z")` behaviour varies by engine: some roll over, some return an Invalid Date. PHP `DateTime` rolls over. Hand-written regex validators. JSON Schema format validators (many check syntax only).
- **Test inputs:** `2021-02-29T00:00:00Z` ✗ · `2021-04-31T00:00:00Z` ✗ · `2021-06-31T00:00:00Z` ✗ · `2021-12-31T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.7-02 — Leap-year computation (Appendix C) for February 29
- **Section:** §5.7 ("Appendix C contains sample C code to determine if a year is a leap year."), §2, Appendix C
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, producer
- **Requirement:** Feb 29 is valid only when `year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)`. The proleptic Gregorian rule applies to all years 0000–9999, including year 0000 (a leap year).
- **Detect:** `year % 4 == 0` only. Julian-calendar libraries for early dates (Java `GregorianCalendar` switches to Julian before 1582-10-15 by default, so `1500-02-29` is accepted as Julian). Check that `java.time` / proleptic mode is used.
- **Test inputs:** `1900-02-29T00:00:00Z` ✗ · `2000-02-29T00:00:00Z` ✓ · `1500-02-29T00:00:00Z` ✗ (proleptic Gregorian) · `0000-02-29T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.7-03 — time-second "60" is valid at a positive leap second
- **Section:** §5.7 ("The grammar element time-second may have the value "60" at the end of months in which a leap second occurs"), §5.8 examples, Appendix D
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, schema
- **Requirement:** Consumers must not reject all `:60` values. At minimum, `23:59:60` in UTC on a real leap second date must be accepted. There are three possible strategies, and the choice is a local matter to be documented: (a) exact validation against an up-to-date leap-second table; (b) accept `:60` only at `23:59:60` UTC (after offset adjustment, R3339-5.7-04) on the last day of a month; (c) accept `23:59:60` UTC on any day. Rejecting every `:60` is non-conformant.
- **Detect:** Python `datetime` (second must be in 0..59 → ValueError), Go `time.Parse` (seconds out of range), Java `LocalTime` (rejects; `DateTimeFormatter.ISO_INSTANT` has special `:60` handling), and regexes `[0-5]\d` for seconds. Check how the library maps `:60` into the value type (R3339-5.7-09).
- **Test inputs:** `1990-12-31T23:59:60Z` ✓ · `1998-12-31T23:59:60Z` ✓ · `2016-12-31T23:59:60Z` ✓ · `1990-12-31T23:58:60Z` ✗
- **Judgment:** objective

### R3339-5.7-04 — Leap second position shifts with the offset
- **Section:** §5.7 ("in time zones other than "Z", the leap second point is shifted by the zone offset (so it happens at the same instant around the globe)"), §5.8, Appendix D
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, producer
- **Requirement:** `:60` is valid only if the *UTC-equivalent* time is `23:59:60`. So in `-08:00` the leap second is `15:59:60` local, and in `+05:30` it is `05:29:60` local (next day). A validator that checks `hour == 23 && minute == 59` against local fields is wrong in both directions.
- **Detect:** leap-second validation code that does not subtract the offset first. JSON Schema validators (a common bug class: accepting `23:59:60+01:00` and rejecting `22:59:60-01:00`, or the reverse).
- **Test inputs:** `1990-12-31T15:59:60-08:00` ✓ · `1990-12-31T23:59:60-08:00` ✗ · `1991-01-01T05:29:60+05:30` ✓ · `1998-12-31T23:59:60+01:00` ✗
- **Judgment:** objective

### R3339-5.7-05 — Negative leap second: maximum second "58"
- **Section:** §5.7 ("It is also possible for a leap second to be subtracted, at which times the maximum value of time-second is "58". At all other times the maximum value of time-second is "59".")
- **Level:** informative (grammar — definitional)
- **Roles:** consumer, producer
- **Requirement:** In a minute with a negative leap second, `:59` would not exist. No negative leap second has occurred to date, so this cannot be tested against real data. Table-driven validators should model it if their table format can express it.
- **Detect:** table-driven validators: does the table support a negative leap second (TAI−UTC decrements)?
- **Test inputs:** n/a with real data (hypothetical: a future negative leap date `YYYY-MM-DDT23:59:59Z` ✗).
- **Judgment:** heuristic

### R3339-5.7-06 — Leap seconds happen at the end of a month (not only June/December)
- **Section:** §5.7 ("to date: June … or December"), Appendix D ("first preference is given to the opportunities at the end of December and June, and second preference to those at the end of March and September")
- **Level:** informative
- **Roles:** consumer
- **Requirement:** Heuristic validators (strategy b in R3339-5.7-03) should allow `:60` at the end of *any* month (or at least Mar/Jun/Sep/Dec), not hard-code June 30 / December 31.
- **Detect:** `(month == 6 && day == 30) || (month == 12 && day == 31)` guards.
- **Test inputs:** `2030-03-31T23:59:60Z`: accept under heuristic (b); reject under an exact-table strategy (a) (no such leap second).
- **Judgment:** heuristic

### R3339-5.7-07 — Do not generate leap-second timestamps before they are announced
- **Section:** §5.7 ("Leap seconds cannot be predicted far into the future … Applications should not generate timestamps involving inserted leap seconds until after the leap seconds are announced.") — the "§5.4 no leap second prediction" requirement is in §5.7
- **Level:** informative (lower-case "should")
- **Roles:** producer
- **Requirement:** Producers must not synthesise `:60` for future dates (for example, schedule generators, test-data fakers, or "smear-to-60" code) unless the IERS has announced the leap second.
- **Detect:** generators or fakers that produce random seconds in `0..60`. Future-scheduled events that contain `:60`.
- **Test inputs:** producer output for 2030-12-31T23:59 + 1 s → must be `2031-01-01T00:00:00Z`, not `…23:59:60Z` (no announced leap second).
- **Judgment:** heuristic

### R3339-5.7-08 — Hour "24" is not allowed
- **Section:** §5.7 ("this profile of ISO 8601 only allows values between "00" and "23" for the hour in order to reduce confusion"); compare errata 293 (Appendix A time-hour → 00-23 + timespec-midnight)
- **Level:** informative (grammar — definitional)
- **Roles:** producer, consumer, schema
- **Requirement:** `24:00:00` (ISO 8601 end-of-day) is invalid. It must be written as `00:00:00` of the next day.
- **Detect:** ISO parsers that accept `T24:00` (Joda, some JS engines, `dateutil`). Producers that emit end-of-day as `24:00`.
- **Test inputs:** `2020-01-01T24:00:00Z` ✗ · `2020-01-02T00:00:00Z` ✓
- **Judgment:** objective

### R3339-5.7-09 — Parsing ":60" must not corrupt the instant
- **Section:** §5.7, §2 "minute" (leap seconds denoted within minutes)
- **Level:** informative (RFC is silent on mapping; the leap-second instant is defined)
- **Roles:** consumer
- **Requirement:** A consumer that accepts `:60` but stores the value in a type without leap seconds (POSIX time, Python `datetime`, JS `Date`) must map it in a documented, monotonic way (for example, clamp to `:59.999…` or roll to `00:00:00` of the next minute). It must not raise an unhandled exception, drop the record, or produce a time earlier than `23:59:59`.
- **Detect:** code paths after regex validation that call `datetime(…, second=60)` or `mktime` with `tm_sec=60` (POSIX normalises this to the next minute, which is acceptable if documented).
- **Test inputs:** `1990-12-31T23:59:60Z` → must be ≥ `1990-12-31T23:59:59Z` and ≤ `1991-01-01T00:00:00Z`; no crash.
- **Judgment:** heuristic

---

## §5.8 Examples

### R3339-5.8-01 — All §5.8 examples parse with the stated meaning
- **Section:** §5.8
- **Level:** informative (worked examples of the normative grammar)
- **Roles:** consumer, schema
- **Requirement:** An RFC 3339 consumer accepts all five examples and computes the stated instants.
- **Detect:** add them to the parser's test vectors.
- **Test inputs:** `1985-04-12T23:20:50.52Z` ✓ · `1996-12-19T16:39:57-08:00` ✓ ≡ `1996-12-20T00:39:57Z` · `1990-12-31T23:59:60Z` ✓ and `1990-12-31T15:59:60-08:00` ✓ (same leap second) · `1937-01-01T12:00:27.87+00:20` ✓ ≡ `1937-01-01T11:40:27.87Z`
- **Judgment:** objective

### R3339-5.8-02 — The fraction is part of the seconds value (no fraction semantics beyond decimal)
- **Section:** §5.8 ("20 minutes and 50.52 seconds after the 23rd hour")
- **Level:** informative
- **Roles:** consumer
- **Requirement:** `.52` = 520 ms, not 52 ms. Parsers that read the fraction as an integer count of ms/µs without scaling by digit count are wrong.
- **Detect:** code such as `int(frac)` → milliseconds; `%f` implementations that treat `.5` as 5 µs.
- **Test inputs:** `1985-04-12T23:20:50.52Z` → 50.520 s · `…:50.5Z` → 50.500 s · `…:50.000001Z` → 1 µs
- **Judgment:** objective

---

## §7 Security Considerations

### R3339-7-01 — Emitting a local offset discloses location/work-hours information
- **Section:** §7 ("the local time zone of a site may be useful for determining a time when systems are less likely to be monitored … some sites may wish to emit times in UTC only")
- **Level:** informative (lower-case "may wish")
- **Roles:** producer
- **Requirement:** Emitting UTC only (`Z`) is a valid privacy/security posture. Producers that expose local offsets in public-facing data (HTTP APIs, logs shipped to third parties, email-like headers) should make this a conscious, configurable choice. Under RFC 9557 §2.2, `Z` also signals "local offset unknown", which fits a policy of not disclosing it.
- **Detect:** public API responses that contain server-local offsets. A config option to force UTC.
- **Test inputs:** n/a (review)
- **Judgment:** editorial

---

## Appendix A — ISO 8601 Collected ABNF (informative)

### R3339-A-01 — Appendix A is not the RFC 3339 grammar
- **Section:** Appendix A ("This is informational only and may contain errors. ISO 8601 remains the authoritative reference.")
- **Level:** informative
- **Roles:** consumer, schema
- **Requirement:** Validators and specs must not use Appendix A (`iso-date-time`, `time-zone` with optional colon or minutes, `time-fraction` with a comma, hour 24, reduced precision, week and ordinal dates) as the RFC 3339 grammar. Only §5.6 defines the RFC 3339 format.
- **Detect:** grammars or regexes copied from Appendix A (look for `time-fraction`, `datespec-`, `("," / ".")`, `00-24`).
- **Test inputs:** `1985-04-12T23:20:50,52Z` ✗ · `1985-04-12T23:20:50+01` ✗ · `1985-04-12T24:00Z` ✗
- **Judgment:** objective

### R3339-A-02 — No mixing of basic and extended format (errata 1584)
- **Section:** Appendix A; errata 1584 (Editorial, Verified). ISO 8601:2000 §5.4.2 d) requires a representation to be all basic or all extended.
- **Level:** informative
- **Roles:** consumer
- **Requirement:** Appendix A's grammar permits mixtures, but ISO 8601 does not, and RFC 3339 §5.6 is fully extended. A consumer must reject strings that are partly basic.
- **Detect:** regexes with optional separators (`-?`, `:?`) or with one-sided optionality.
- **Test inputs:** `1985-04-12T232050Z` ✗ · `19850412T23:20:50Z` ✗ · `1985-04-12T23:20:50+0100` ✗
- **Judgment:** objective

### R3339-A-03 — Fraction digits always follow a full 2-digit seconds field (errata 4110)
- **Section:** Appendix A; errata 4110 (Technical, Verified). ISO 8601/Cor 1:1991 requires "00" before a fraction less than unity. Per its notes, the RFC 3339 grammar "never allowed just one zero ("0") preceding the fraction".
- **Level:** informative (grammar — definitional via §5.6 `time-second` = `2DIGIT`)
- **Roles:** consumer
- **Requirement:** The fraction in §5.6 always follows `2DIGIT` seconds. Forms such as `:0.5`, `:.5` and `:5.` are invalid, as are fractions on minutes or hours. Errata 4110 does not change §5.6. It only corrects the Appendix A prose.
- **Detect:** regexes `\d{1,2}(\.\d*)?` for seconds.
- **Test inputs:** `2020-01-01T00:00:0.5Z` ✗ · `2020-01-01T00:00:.5Z` ✗ · `2020-01-01T00:00:05.Z` ✗ · `2020-01-01T00:00:00.5Z` ✓
- **Judgment:** objective

### R3339-A-04 — Durations and periods are not RFC 3339 date-times
- **Section:** Appendix A "Durations:", "Periods:" (informative ABNF only)
- **Level:** informative
- **Roles:** schema
- **Requirement:** Specs that need durations or intervals must cite ISO 8601 (or another spec such as RFC 5545 for durations), not "RFC 3339 duration". JSON Schema `format: "duration"` cites RFC 3339 Appendix A, but that ABNF is informative and "may contain errors". Note the gaps: for example, `dur-week` cannot be combined with other units, and there are no fractional components.
- **Detect:** docs that say "RFC 3339 duration/interval".
- **Test inputs:** `P1W` (valid per Appendix A) · `P1W2D` ✗ per Appendix A · `PT0.5S` ✗ per Appendix A (no fractions)
- **Judgment:** editorial

---

## Appendix B — Day of the Week

### R3339-B-01 — Zeller-based sample is valid only on/after 0000-03-01
- **Section:** Appendix B ("may be used to obtain the day of the week for dates on or after 0000-03-01")
- **Level:** informative
- **Roles:** producer, consumer
- **Requirement:** Implementations that copy `day_of_week()` must guard the input range. For January and February of year 0000, the adjusted year becomes −1, and C `/` and `%` truncation give wrong results. The code also expects a 4-digit year and month 1–12. (Verified against Python `datetime`: 1985-04-12 → Friday, 1996-12-19 → Thursday, 2000-02-29 → Tuesday, 2000-03-01 → Wednesday.)
- **Detect:** grep for `26 * month - 2` / `dayofweek[]` and check the callers' range.
- **Test inputs:** `day_of_week(12,4,1985)` → Friday · `day_of_week(29,2,2000)` → Tuesday · `day_of_week(1,1,0)` → out of documented range
- **Judgment:** objective

### R3339-B-02 — If a weekday is also present, it must agree with the date
- **Section:** Appendix B, §5.4
- **Level:** informative
- **Roles:** consumer
- **Requirement:** For legacy formats that carry a weekday (not RFC 3339), compute it (Appendix B) and detect mismatches rather than trusting either field silently.
- **Detect:** parsers that ignore a weekday token.
- **Test inputs:** `Sat, 1985-04-12` → mismatch (1985-04-12 was Friday)
- **Judgment:** heuristic

---

## Appendix C — Leap Years

### R3339-C-01 — leap_year() requires a full 4-digit year
- **Section:** Appendix C ("Must use 4 digit year.")
- **Level:** informative (sample-code comment; lower-case "must")
- **Roles:** consumer, producer
- **Requirement:** Leap-year tests must use the full year, not `tm_year` (year − 1900) or a 2-digit year. `leap_year(100)` (from `tm_year` for 2000) returns false, but 2000 is a leap year.
- **Detect:** `leap_year(tm->tm_year)`, `isLeap(date.getYear())` (JS/Java legacy, year − 1900).
- **Test inputs:** `2000-02-29T00:00:00Z` ✓ (a `tm_year` bug would reject it) · `1900-02-29T00:00:00Z` ✗
- **Judgment:** objective

---

## Appendix D — Leap Seconds

### R3339-D-01 — The Appendix D table is stale; use a maintained source
- **Section:** Appendix D (table ends at 1998-12-31, TAI−UTC 32; "excerpt from the table maintained by the United States Naval Observatory")
- **Level:** informative
- **Roles:** consumer
- **Requirement:** Table-driven leap-second validation (R3339-5.7-03 strategy a) must use a current source (IERS Bulletin C, IANA tzdb `leap-seconds.list`), not the RFC table. Leap seconds after publication: 2005-12-31, 2008-12-31, 2012-06-30, 2015-06-30, 2016-12-31 (TAI−UTC 37). The source URLs in Appendix D and §6 are historical (compare errata 3710). A validator that hard-codes Appendix D rejects `2016-12-31T23:59:60Z`.
- **Detect:** hard-coded arrays that end with `1998-12-31`/`19981231`. Presence of an update mechanism and expiry check for `leap-seconds.list`.
- **Test inputs:** `1998-12-31T23:59:60Z` ✓ · `2016-12-31T23:59:60Z` ✓ (a stale table would reject it) · `1999-12-31T23:59:60Z` ✗ (exact strategy)
- **Judgment:** objective

### R3339-D-02 — A leap second is the same instant in every offset
- **Section:** Appendix D ("A leap second occurs simultaneously in all time zones, so that time zone relationships are not affected."), §5.7
- **Level:** informative
- **Roles:** consumer, producer
- **Requirement:** Formatting a leap-second instant in a non-UTC offset must keep `:60` at the shifted local time (producer side of R3339-5.7-04). For example, 1990's leap second in `-08:00` is formatted as `1990-12-31T15:59:60-08:00`.
- **Detect:** producers that can represent leap seconds (rare): check that the offset conversion keeps `:60`.
- **Test inputs:** format `1990-12-31T23:59:60Z` in `-08:00` → `1990-12-31T15:59:60-08:00`
- **Judgment:** objective

### R3339-D-03 — The first leap second in the table is 1972-06-30
- **Section:** Appendix D (table begins 1972-06-30 with TAI−UTC 11)
- **Level:** informative
- **Roles:** consumer
- **Requirement:** Exact-table validators must reject `:60` before 1972-06-30. Pre-1972 UTC used frequency offsets and step adjustments that the table does not represent.
- **Detect:** table lookups that assume a leap second at 1971-12-31 or earlier.
- **Test inputs:** `1972-06-30T23:59:60Z` ✓ · `1971-12-31T23:59:60Z` ✗ (exact strategy)
- **Judgment:** objective

---

## Content that cannot be checked (and why)

| Section | Content | Reason |
|---|---|---|
| Status / Copyright / Acknowledgements / Authors' Addresses / Full Copyright Statement | Boilerplate | Not a requirement on implementations. |
| §1 para 1–2 | Motivation (confusion and interoperability problems) | Descriptive. |
| §2 | Definitions of UTC (BIPM), SI second (caesium-133), hour, day, ABNF, Email Date/Time Format, Internet Date/Time Format, Timestamp; pointers to NTP App. E, ISO 8601 §3, ITU-R TF | Terminology. The only definitions that drive checks are "leap year" (R3339-2-01), "Z" (R3339-2-02) and "minute" (R3339-2-03). |
| §4.2 para 1 | Offset useful as an email "prompt response" heuristic; RFC 2822 made numeric offsets mandatory | Rationale. The testable part is R3339-4.2-01. |
| §4.4 | Third suggested mechanism, "Prompt the user for the local time zone and daylight saving rule settings" | A deployment/UX option under R3339-4.4-01, with no observable wire property. |
| §5.2 para 1 | Human-readability trade-off discussion | Rationale. Testable parts are R3339-5.2-01/02. |
| §5.5 para 1 | "the complete grammar for ISO 8601 is deemed too complex" | Rationale. Testable part is R3339-5.5-01. |
| §6 References | Includes stale URLs ([IERS] fixed by errata 3710, [ITU-R-TF], Appendix D USNO URLs); [ABNF] is now RFC 5234; [NTP] now RFC 5905 | Reference hygiene only. The IERS URL is corrected by erratum 3710 (Verified, editorial). |
| Table of Contents | Stray comma in the dot leader (errata 6533, Held) | Typographic. |
| Appendix A preamble | Based on ISO 8601:1988; "may be some changes in the 2000 revision"; interpretive choices (T required, hour-24 anywhere, fraction preceded by 0) | Informative. Checks derived from it are R3339-A-01…04. Errata 293/1584/4110 correct its prose and grammar, not §5.6. |
| Appendix D intro | CCIR recommendation quote; USNO pointers | Historical. Operational content is in R3339-5.7-06 and R3339-D-01…03. Note (outside RFC 3339): CGPM 2022 Resolution 4 plans to increase the maximum UT1−UTC tolerance by or before 2035, which in effect ends new leap seconds. `:60` handling stays necessary for historical data. |

---

## Most common implementation mistakes (summary)

1. **Leap seconds (§5.7/Appendix D):** rejecting every `:60` (Python, Go and many regexes do), or validating `23:59:60` against the *local* fields instead of the UTC-shifted time (`1990-12-31T15:59:60-08:00` is valid, `…T23:59:60-08:00` is not). Hard-coding the stale 1998 Appendix D table is a related mistake.
2. **Treating a general ISO 8601 parser as an RFC 3339 validator (§5.5/§5.6):** this accepts comma fractions, `+0100`, space separators, missing offsets, hour 24, basic format and 5-digit years. At the same time, it rejects the valid RFC 3339 forms `t`/`z` (ABNF case-insensitivity), `-00:00`, fractions longer than 9 digits and offsets beyond ±18:00.
3. **Offset handling (§4.2–§4.3, RFC 9557 §2):** sign inversion (`getTimezoneOffset`, POSIX TZ), appending a literal `Z` to local wall-clock time, emitting sub-minute offsets (`+00:19:32` from Python/Java for LMT zones), and missing the fact that RFC 9557 changed `Z` to mean "local offset unknown" while `+00:00` keeps "UTC preferred".

(Check count: 71.)

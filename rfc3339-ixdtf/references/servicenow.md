# SERVICENOW — Glide, REST, Flow, import sets, Fluent SDK

How to audit a ServiceNow app with this skill. Verdict words follow `ecosystem/README.md` ("How to read the verdicts").
Severity follows `interpretation.md` rule 1.

**Evidence labels** (every row has one):

| Label | Meaning |
|---|---|
| documented | ServiceNow product docs (Australia release, updated 2026-03-12, unless noted), or the JSDoc of `@servicenow/glide` 27.0.5 / `@servicenow/sdk` 4.13.0 |
| probed offline | Run on 2026-09-25 against the SDK 4.13.0 packages (Node 26.8.1, TypeScript 5.6.2, tzdata 2026c, macOS arm64). **Build-time behaviour only**, not the instance |
| community | ServiceNow Community thread, blog or gist. Not authoritative |
| inference | Our reading, not stated in a source |
| unverified (needs instance) | Nobody ran it on an instance. The probe ID in brackets verifies it (§6) |

No instance was used. No instance behaviour in this file is "probed".

Doc short names (all `https://www.servicenow.com/docs/r/australia/…` unless noted):
[GDT-G] `api-reference/server-api-reference/c_GlideDateTimeAPI.html` ·
[GDT-S] `…/c_GlideDateTimeScoped.html` · [GD-S] `…/c_GlideDateScopedAPI.html` · [GT-S] `…/c_GlideTimeScopedAPI.html` ·
[GS-G] `…/c_GlideSystemAPI.html` · [TABLE] `api-reference/rest-apis/c_TableAPI.html` ·
[FMT] `platform-administration/time-configuration/r_FormatDateAndTimeFields.html` ·
[FIELDS] `…/time-configuration/r_UseDateAndTimeFields.html` · [SYSTZ] `…/time-configuration/t_SetASystemTimeZone.html` ·
[TZ] `https://www.servicenow.com/docs/r/yokohama/platform-administration/time-configuration/r_TimeZones.html` ·
[EXPORT] `…/time-configuration/c_ExportDateAndTimeInformation.html` ·
[DVQ] `platform-administration/table-administration-and-data-management/query-parameters-display-value.html` ·
[IMPDT] `integrate-applications/system-import-sets/importing-date-time-values.html` ·
[FMAP] `integrate-applications/system-import-sets/t_CreatingAFieldMap.html` ·
[FDX] `https://www.servicenow.com/docs/r/yokohama/build-workflows/workflow-studio/date-time-transform-functions.html`.
SDK paths are under `node_modules/@servicenow/`.

## 1. Framing: a platform profile, judged at the boundary

- ServiceNow's native value is `yyyy-MM-dd HH:mm:ss`: UTC, a space separator, no offset, whole seconds
  (documented: [GDT-S] getValue, [TABLE], [SYSTZ]; `sdk-core/dist/db/types/Date.d.ts:3-5`). It is **not** an
  RFC 3339 `date-time` (`rfcdt check '2024-01-01 12:00:00' --allow-space-separator` → `R3339-5.6/time-offset`).
- Treat it as a **platform profile**, like a database column type. Inside the platform it is not a finding.
  Do not report "space separator" or "no offset" on every `getValue()` call.
- Audit the **boundaries**, where a value leaves or enters the platform: outbound REST/SOAP bodies, Scripted
  REST responses, Table API clients, import sets and transform maps, Flow Designer transforms, and Fluent build
  output (`dist/**/*.xml`). Also audit every place that can give a **wrong instant**.

Severity mapping (`interpretation.md` rule 1):

| Pattern | Severity | Why |
|---|---|---|
| Native `yyyy-MM-dd HH:mm:ss` sent where the contract says RFC 3339 / ISO 8601 / `format: date-time` | **Nonconformity** (producer outside the grammar) | consumed as RFC 3339 |
| `getValue().replace(' ','T')+'Z'` | conforming **only if** `glide.sys.internal.tz` is unset or UTC; otherwise **Nonconformity** (well-formed but wrong) | `getValue()` is in the internal zone (documented: `GlideTime.d.ts:69-72`, [GDT-S] toString) [P-ENV] |
| `getDisplayValue()`, `getDisplayValueInternal()`, `gs.nowDateTime()`, `sysparm_display_value=true` in an integration | **Nonconformity**: wrong instant once a `Z` or offset is added; format changes by user (documented) | user zone and user format [GDT-S], [GS-G], [TABLE] |
| ISO input parsed by `new GlideDateTime(s)` / `setValue(s)` / "replace `T` with a space" | **Nonconformity** at an ingest boundary (offset dropped = wrong instant); TOO STRICT or TOO LENIENT otherwise | §2 consumer rows |
| Fluent build output that depends on the build host's zone, or a wrong UTC conversion | **Nonconformity** by analogy ("well-formed but wrong": the SN string names another instant) | §3 |
| Fluent type gate that accepts `2024-02-30 25:61:61` | TOO LENIENT for its own profile: **Advisory** (no RFC claim) unless it gates external input | §3 F8 |
| SDK functions that reject RFC 3339 strings | stated profile restriction, **not** TOO STRICT | `interpretation.md` rule 3 |

## 2. Platform APIs (Glide, REST, Flow, import sets)

Wire model: every stored value is UTC `yyyy-MM-dd HH:mm:ss`. Display values have the same shape, in the user's
zone and format, with no zone marker ("You cannot append the 'z' character" [FMT]). No documented Glide or REST
output is an RFC 3339 `date-time`.

| API | Role | Output / accepted input | Verdict | Evidence |
|---|---|---|---|---|
| `GlideDateTime.getValue()` / `toString()` / `GlideRecord.getValue(dtField)` | producer | `2026-09-24 12:34:56` (UTC; `toString` = "system time zone, UTC by default") | **WRONG OUTPUT** at a boundary (space, no offset); instant correct | documented [GDT-S] |
| `getDisplayValue()` / `getDisplayValueInternal()` / `gs.nowDateTime()` | producer | user zone, user format (12-hour form possible), no offset | **WRONG OUTPUT**; **WRONG VALUE** if `Z` is added | documented [GDT-S], [GS-G] |
| `gs.beginningOfToday()`, `daysAgo()`, `minutesAgo()`, … | producer | UTC `yyyy-MM-dd HH:mm:ss` (the doc writes `yyyy-mm-dd hh:mm:ss`, a typo) | **WRONG OUTPUT** | documented [GS-G] |
| `getNumericValue()` | producer | epoch ms | not a string; the safe basis | documented [GDT-S] |
| `new Date(gdt.getNumericValue()).toISOString()` | producer | `2026-09-24T12:34:56.789Z` | conforming (years 0000–9999) | community; unverified (needs instance) [P-RFC] |
| `getValue().replace(' ','T') + 'Z'` | producer | `2026-09-24T12:34:56Z` | conforming (lossy: seconds) only if the internal zone is UTC | inference; unverified [P-RFC, P-ENV] |
| `getXMLValue()`, `getUTCValue()`, `getDisplayValueWithoutTZ()`, `excludeZFromFormat()`, `GlideScheduleDateTime.setIncludeZFormat()` | producer | types only, not in the docs | unknown | unverified [P-OUT] |
| `JSON.stringify({t: gdt})` / Scripted REST `setBody` with a GlideDateTime or GlideElement | producer | not documented | unknown | unverified [P-JSON, REST-S] |
| Table API GET, `sysparm_display_value=false` (default) | producer | `"2016-01-19 04:52:04"` (UTC) | **WRONG OUTPUT** at the client boundary; instant correct if read as UTC | documented [TABLE] |
| Table API GET, `sysparm_display_value=true\|all` | producer | display value in the API user's zone | **WRONG OUTPUT**; instant depends on the user profile | documented [TABLE] |
| Export CSV/XML vs Excel/PDF | producer | DB value (UTC) vs display value | as the two rows above | documented [EXPORT] |
| Flow *Date to String* preset `yyyy-MM-dd'T'HH:mm:ss'Z'` | producer | literal `Z`; "Runtime Date/Time values are not localized and appear in the UTC … time zone" | conforming if the docs are right | documented [FDX], `sdk-core/dist/external/flow/transform/datetime.d.ts:15,57-89`; runtime unverified [FLOW] |
| Flow custom format with `XXX` | producer | `-08:00` | conforming if the value's zone is right | documented [FDX]; unverified [FLOW] |
| `new GlideDateTime(s)` / `setValue(s)` | consumer | internal format, then 19 alternates in order (`MM/dd/yyyy …`, `dd-MM-yy HH.mm.ss`, …). `yyyy-MM-dd'T'HH:mm:ss.SSSZ` is "not supported" | **TOO LENIENT** (ambiguous day/month, 2-digit years), **TOO STRICT** (ISO); `T`, `Z`, offsets, fractions, `:60`, `t`/`z`: unspecified. Failure = `isValid()` false, "ignored" | documented [GDT-G]; unverified [P-IN] |
| "replace `T` with a space" then `setValue` | consumer | drops any offset | **WRONG VALUE** for `±hh:mm` input | community (m-p/2464306, m-p/1624483) |
| `setValueUTC(s, fmt)` / `setDisplayValue(s, fmt)` | consumer | Java `SimpleDateFormat` pattern (inferred); throws on mismatch | depends on the pattern; a `'Z'` literal rejects every offset (`ecosystem/README.md`, Top 10 item 4); leniency unknown | documented (throws); unverified [P-IN] |
| `setDisplayValue(s)` / `setDisplayValueInternal(s)` | consumer | read in the **session user's** zone | wrong instant when the data came from another system | documented [GDT-S] |
| `GlideDate.setValue` / `GlideTime.setValue` | consumer | `yyyy-MM-dd` / `HH:mm:ss` (internal zone) | offset, fraction, `24:00`, `:60`: unspecified | documented [GD-S], [GT-S]; unverified [P-DATE, P-TIME] |
| `GlideRecord.setValue(f, s)` / `gr.f = s` / `GlideElement.setDisplayValue` | consumer | not documented for dates | unknown | unverified [P-ELEM] |
| Table API POST/PUT/PATCH, `sysparm_input_display_value=false` (default) | consumer | "inserted using the GMT timezone"; accepted string formats not documented | unknown for `T`/`Z`/offsets (community: one thread shows 4 h off) | documented [TABLE]; community m-p/1514888; unverified [REST-W] |
| same, `sysparm_input_display_value=true` | consumer | read in the API user's zone | instant depends on the user profile | documented [TABLE] |
| Import set field map "Date format" | consumer | fixed choices (`yyyy-MM-dd HH:mm:ss`, `MM-dd-yyyy HH:mm:ss z`, …); no `T`, numeric offset or fraction | no RFC 3339 choice; one zone per run (the importing user's) | documented [FMAP], [IMPDT], `sdk-core/dist/app/ImportSet.d.ts:21-24` |
| Server-side JS `new Date()` getters | — | JVM zone, not the user zone | host-dependent | community (sn-nerd.com 2020-04-30) |

Other documented facts that matter:
- Storage: UTC [SYSTZ], [TZ]. [FIELDS] says both MySQL `DATETIME` and "integer numbers, in milliseconds";
  inference: whole seconds are stored [P-DB, P-PREC]. Leap seconds: inference, not representable (Java).
- Fallback zone: `glide.sys.default.tz`, else the JVM's zone [TZ]; [SYSTZ] says America/Los_Angeles.
- DST gap and overlap resolution in `setDisplayValue*`: not documented; unverified [P-DST].
- `yy` in any format uses a 20/80-year window ("51 … 1951") [FMT].

## 3. Fluent SDK 4.13.0 (build time, probed offline)

The SDK has no RFC 3339 parser or formatter. Its defects are wrong instants in its own conversions, a profile it
does not enforce, and build output that depends on the build host. Reproduce everything with
`probes/servicenow/fluent-build-diff/` (no instance).

Ranked by impact. File:line is in the SDK `dist`.

| # | Severity | Location | Finding | Repro → output | Impact |
|---|---|---|---|---|---|
| F1 | Nonconformity (WRONG VALUE) | `sdk-build-core/dist/plugins/time.js:190-191` (`timeFieldToXML`) | `Math.floor(totalMinutes/60)` with a JS `%` that keeps the sign: when the UTC result is on the previous day and the minutes are not a whole hour, the time is **60 min early** | `Time({hours:1},'Asia/Kolkata')` → `1969-12-31 18:30:00` (correct 19:30); `Time({hours:0,minutes:30},'Europe/Berlin')` → `22:30` (correct 23:30) | 2 970 / 40 128 (zone × time) cases in 215 / 418 zones, all east of UTC. Also the default `run_time` of a `ScheduledScript` in `Asia/Kolkata` (`17:30`, correct `18:30`) |
| F12 | Build integrity | `sdk-build-plugins/dist/schedule-script/scheduled-script-plugin.js` → `sdk-cli/dist/command/build/index.js:120` | A plugin exception is logged as `ERROR`, but the build prints "Build completed successfully", exits **0** and **leaves the record out** | `executionStart:'2024-13-01 00:00:00'` → `ERROR … Invalid time value`, exit 0, no `sysauto_script` XML | 8 / 28 test ScheduledScripts silently dropped (month 13, `25:61:61`, `:60`, years `0000/0050/0099`, zone `Mars/Olympus`). CI that trusts the exit code ships an incomplete app |
| F2 | Nonconformity (WRONG VALUE) | `time.js:195` (`timeFieldToXML`, no zone); `sdk-build-core/dist/plugins/data-shape.js:130` | `Time({...})` with no zone uses the **build host's** zone | `Time({hours:12})` → `12:00:00` (TZ=UTC), `17:00:00` (America/New_York), `03:00:00` (Asia/Tokyo), `06:30:00` (Asia/Kolkata) | Same source, different XML on each laptop and CI runner |
| F4 | Nonconformity (WRONG VALUE) | `sdk-build-plugins/dist/schedule-script/timeZoneConverter.js:92` (`dateTimeFieldToXML`) | Zone offset computed from two **host-local** `new Date(y,m,d,…)` values; off by 1 h when the wall time is in the host's DST gap | `executionStart:'2026-03-08 02:30:00', timeZone:'Asia/Kolkata'` → `run_start 2026-03-07 21:00:00` (TZ=UTC, correct), `22:00:00` (TZ=America/New_York or Los_Angeles) | Host-dependent `run_start` |
| F3 | Nonconformity (WRONG VALUE) | `time.js:37-38` (`parseGlideDuration`) | Duration = difference of two host-local 1970 `Date`s; loses 1 h across the host's 1970 DST period. `formatDuration` uses UTC, so the round trip is asymmetric | `parseGlideDuration('1970-07-20 00:00:00')` → `{days:200}` (TZ=UTC), `{days:199,hours:23}` (TZ=America/New_York) | `now-sdk transform` on a US/EU workstation rewrites `run_period`/`max_drift` 1 h short (SLA, assessment, catalog, ATF, playbook timers use the same path) |
| F6 | Nonconformity (WRONG VALUE: year remap) | `timeZoneConverter.js:133` (`Date.UTC(year,…)`), `:92` | Years 0–99 become 1900–1999, or the conversion throws | `convertXMLToDateTime('0050-06-01 00:00:00','America/New_York')` → `1950-05-31 20:00:00`; `dateTimeFieldToXML` of the same value throws `RangeError: Invalid time value`. A transformed source then fails its own build | Round trip `transform` → `build` is broken for years < 100 |
| F9 | TOO LENIENT (no profile enforcement) | Record data plugin (`sdk-build-plugins/dist/data-plugin.js`) + XML writer | After a type-gate bypass (`as any`, `@ts-ignore`, `ScheduleDateTimeColumn` typed `string`, `TimeColumn`/`DurationColumn` strings) **every** string is written to the XML byte for byte | 272 / 272 values emitted verbatim: `2024-01-01T12:00:00Z`, `…+01:00[!Europe/London]`, trailing `\n`, CR, BOM, NBSP, 1 000-digit fractions (`max_length` is 40) | The instance's reaction is unknown [INSTALL] |
| F14 | Build integrity | XML writer | U+0000 is written raw into update-set XML (forbidden in XML 1.0) | 12 generated files fail `xml.dom.minidom` ("not well-formed") | Install behaviour unknown [INSTALL] |
| F13 | Build integrity | Record data plugin; `Duration.d.ts` | `TimeColumn`/`DurationColumn` accept a raw object literal; the build writes `[object Object]`. `Date.now() as any` writes `Symbol(CallExpressionShape)` | `tm: {hours:12, minutes:30}` → `<tm>[object Object]</tm>` (no cast, exit 0) | Garbage field values |
| F8 | TOO LENIENT (Advisory) | `sdk-core/dist/db/types/Date.d.ts:3-5` | The only gate on date columns is `` `${number}-${number}-${number} ${number}:${number}:${number}` `` | tsc accepts `2024-02-30 12:00:00`, `2024-01-01 25:61:61`, `12:00:60`, `2024-1-1 1:2:3`, `1e3-01-01 …`, `0x10-…`, `' 2024-01-01 12:00:00'`, `12:00:00.5`; rejects every RFC 3339 / IXDTF string | Invites `as any`, which leads to F9 |
| F10 | TOO LENIENT | `scheduled-script-plugin.js:398,404` | Shape-only regex; V8 `Date` then rolls over or throws (→ F12) | `2024-02-30 12:00:00` (Paris) → `run_start 2024-03-01 11:00:00`, `entered_run_start` keeps `2024-02-30`; `24:00:00` → next day | Silent date change |
| F11 | TOO LENIENT | `scheduled-script-plugin.js:409-411` | `end <= start` compares host-local `Date`s; both `NaN` for impossible dates, so the check never fires | F10 inputs | Validation skipped |
| F5 | Review note (R9557-3.4) | `timeZoneConverter.js:64-96` | One-pass offset guess: DST gap/overlap resolution depends on the offset sign and matches no single Temporal `disambiguation` | NY gap `02:30` → `07:30Z` (`compatible`); Paris gap `02:30` → `00:30Z` (`earlier`); NY overlap → `earlier`, Paris overlap → `later` | Undocumented policy |
| F7 | WRONG OUTPUT (SN profile) | `time.js:16,26` (`formatDateToPlatformFormat[Local]`), `timeZoneConverter.js:21-27` (`formatToUTC`) | Year not padded to 4 digits, not range-checked | year 50 → `50-06-01 00:00:00`; −1 → `-1-01-01 …`; 10000 → `10000-01-01 …` | Invalid values in XML |
| A1 | Advisory | `time.js:176-187` | `Time(…, tz)` uses the zone's offset on **1970-01-01**, and drops offset seconds | `Time({hours:12},'Asia/Singapore')` → `04:30:00` (today's offset gives 04:00); `Africa/Monrovia` rounded to the minute | Depends on how the instance converts `glide_time` [INSTALL] |
| A2 | Advisory | `data-plugin.js:146-155` (`Intl.DateTimeFormat` as the zone check) | Offsets and wrong case pass as "IANA" and are stored as written | `timeZone:'asia/kolkata'` → `<time_zone>asia/kolkata</time_zone>`; `'+05:30'` accepted | Instance acceptance unknown [INSTALL] |
| A3 | Advisory | `timeZoneConverter.js:44,117` | Separator `\s+` (tab, LF, NBSP, double space) | `'2024-01-01\t12:00:00'` accepted | The plugin regex blocks it for `executionStart`; direct callers are exposed |
| A4 | Advisory (docs) | `sdk-core/src/external/flow/transform/datetime.ts:68,250` | JSDoc examples use `new Date('2021-05-02 09:10:12')` (host-local in JS) | — | Copied into user code |
| P1 | conforming | `sdk-build-plugins/dist/server-module-plugin/sbom-builder.js:95` → `.now/bom.json` | `timestamp: new Date()` serialized by `JSON.stringify` (`toISOString`) | `2026-09-25T18:51:23.111Z` → `rfcdt check` VALID | Not reproducible (wall clock); `Z` is right |

Not a finding: `ScheduledScript` with no `timeZone` or `'floating'` is converted as **UTC** by the plugin
(`scheduled-script-plugin.js:427`), so it is host-independent in a build. Only direct callers of
`dateTimeFieldToXML(s, 'floating')` get the host zone (`timeZoneConverter.js:49`). Whether UTC is what the
instance means by "floating" is unverified [INSTALL]. The build writes no `sys_created_on`/`sys_updated_on`
stamps; `transform` discards them (`sdk-api/dist/context/parser.js:147-155`).

Vector scores (`run_vectors.py --target-kind both --target-options fixed --target-has-tzdata yes`; 216 scored,
27 interpretation, 31 skipped). "Replay" adapters replay per-record verdicts from real bulk builds.

| Surface (adapter) | pass | TOO LENIENT | TOO STRICT | WRONG VALUE | Reading |
|---|---|---|---|---|---|
| `parseDateTime` | 134 | 0 | 82 | 0 | rejects all RFC 3339: profile restriction, n/a |
| `parseGlideTime(·,'UTC')` | 134 | 0 | 82 | 0 | same |
| `parseGlideDuration` | 134 | 0 | 82 | 0 | same (F3 is host-dependent, not shown by vectors) |
| `dateTimeFieldToXML(·,'Europe/Paris')` | 134 | 0 | 82 | 0 | same (throws `Invalid datetime format`) |
| `convertXMLToDateTime(·,'Europe/Paris')` | 134 | 0 | 82 | 0 | same |
| tsc gate `DateTimeColumn` (replay) | 134 | 0 | 82 | 0 | same |
| tsc gate `DateColumn` (replay) | 133 | 1 | 82 | 0 | the 1 is `2024-01-01`, right for `full-date` |
| tsc gate `ScheduleDateTimeColumn` (replay) | 82 | **134** | 0 | 0 | typed `string`: accepts everything |
| Record build with `as any` (replay) | 82 | **134** | 0 | 0 | no build-time validation; verbatim XML (F9) |
| ScheduledScript `executionStart` check (replay) | 133 | 1 | 82 | 0 | the 1 is `''` (treated as unset) |

All 27 interpretation vectors were rejected by every SN surface (or stored as opaque text). No surface interprets
IXDTF suffixes, so RFC 9557 §3.3 does not apply. The vector runs do not show the host-TZ and range defects
(F1–F6, F12): use the build diff and the helper probe for those.

## 4. Detect in code

A hit is a lead. Confirm it with the probe in the "Why" column. `rfcdt.py scan` has no pattern for most of these.

### Glide server scripts (business rules, Script Includes, Scripted REST, Flow script steps)

| Grep (ERE) | Why | Safer replacement |
|---|---|---|
| `\.getValue\(['"][a-z_]*(_on\|_at\|date\|time)['"]\)` or `gdt\.getValue\(\)` flowing into `JSON.stringify\|setBody\|setRequestBody\|setStringParameter` | native profile at a boundary: **WRONG OUTPUT** (documented) | `toRfc3339(gdt)` |
| `getDisplayValue\(\|getDisplayValueInternal\(\|gs\.nowDateTime\(\|gs\.now\(\)` in integration code (`RESTMessageV2`, `SOAPMessageV2`, `sn_ws`, `setBody`) | user zone and format; varies per user (documented) | `toRfc3339(gdt)` |
| `getValue\(\)[^;\n]*\+\s*['"]Z['"]` · `replace\(\s*['"] ['"]\s*,\s*['"]T['"]\s*\)` | right only if the internal zone is UTC [P-ENV]; on a display value, **WRONG VALUE** | `new Date(gdt.getNumericValue()).toISOString()` |
| `['"]T['"]\s*\+\|\+\s*['"]T['"]` with `get(Hour\|Minutes\|Seconds\|DayOfMonth\|Month)` | hand-built timestamps: mixed zones, 1- vs 0-based months, no padding (community) | `toRfc3339` |
| `new GlideDateTime\(\s*[a-zA-Z_$][\w.$]*\s*\)` · `\.setValue\(\s*[a-zA-Z_$][\w.$]*\s*\)` on external strings | ISO "not supported"; other forms unspecified; ambiguous alternates; failures "ignored" (documented) [P-IN] | `fromRfc3339(s)`; check `isValid()` |
| `replace\(\s*['"]T['"]\s*,\s*['"] ['"]\s*\)` | drops the offset: **WRONG VALUE** for `±hh:mm` (community recipe) | `fromRfc3339(s)` |
| `addSeconds\(\s*[-+]?\s*\w*[oO]ffset` | hand offset math; a widely copied gist *adds* `+hh:mm` (off by 2×offset; inference from the code) | `fromRfc3339(s)` (subtracts via epoch ms) |
| `setValueUTC\([^)]*'Z'` · `setDisplayValue\([^,]+,\s*['"][^'"]*'Z'` | literal `'Z'` rejects every offset (`ecosystem/README.md`, Top 10 item 4) | `fromRfc3339(s)` |
| `(setValueUTC\|setDisplayValue\|getByFormat)\([^)]*(YYYY\|yyyy-mm-dd\|hh:mm:ss['"])` | week-year `Y`; `mm` = minutes; 12-hour `hh` without `a` (doc typos copied) | `yyyy-MM-dd'T'HH:mm:ss` |
| `setDisplayValue\(\|setDisplayValueInternal\(` on data from another system | read in the session user's zone (documented) | `fromRfc3339(s)` |
| `new Date\(\)\.get(Day\|Hours\|Date)\(` · `new Date\(\s*\w+\s*\)` | JVM zone (community); host-local parse | GlideDateTime `…UTC()` getters or epoch ms |
| `sysparm_display_value=(true\|all)` · `sysparm_input_display_value=true` in clients | API user's zone and format decide the instant (documented) | `false` (default) and treat the value as UTC |
| `(^\|[^y])yy([^y]\|$)` in `glide.sys.date_format`, field-map formats, `setDisplayValue(…, fmt)` | 20/80-year window (documented) | `yyyy` |

Helpers (`probes/servicenow/glide_rfc3339.js`, ES5). **Evidence: tested under Node against a stand-in
GlideDateTime** (`glide_adapter.cjs`, epoch ms only), **not in real Rhino**; `toISOString` and
`setUTCFullYear` on the instance are unverified [P-RFC]. Vectors: 128/130 on TZ=UTC and TZ=America/New_York;
the 2 WRONG VALUE rows are real leap seconds stored as `:59` (stated policy).

```javascript
// Producer: GlideDateTime -> RFC 3339 (UTC, milliseconds). Years 0000-9999 only.
function toRfc3339(gdt) {
  var ms = Number(String(gdt.getNumericValue()));
  var d = new Date(ms);
  var y = d.getUTCFullYear();
  if (isNaN(ms) || y < 0 || y > 9999) { throw 'toRfc3339: out of range'; }
  return d.toISOString();                         // 2026-09-24T12:34:56.789Z
}

// Consumer: strict RFC 3339 date-time -> GlideDateTime. Rejects everything else.
var RFC3339 = /^([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]|60)(\.[0-9]+)?([Zz]|([+-])([01][0-9]|2[0-3]):([0-5][0-9]))$/;
function fromRfc3339(s) {
  var m = RFC3339.exec(String(s));
  if (!m) { throw 'fromRfc3339: not RFC 3339: ' + s; }
  var y = +m[1], mo = +m[2], d = +m[3], h = +m[4], mi = +m[5], se = +m[6];
  var dim = [31, (y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1];
  if (d > dim) { throw 'fromRfc3339: day out of range: ' + s; }
  var frac = m[7] ? Math.floor(Number('0' + m[7]) * 1000) : 0;   // truncate to ms (lossy, allowed)
  var off = 0;
  if (m[9]) { off = (m[9] === '-' ? -1 : 1) * (+m[10] * 60 + +m[11]); }
  var leap = (se === 60);
  if (leap) { se = 59; }                                      // policy: a valid leap second is stored as :59 (lossy)
  var t = new Date(0);                                        // not Date.UTC(): it maps years 0-99 to 19xx
  t.setUTCFullYear(y, mo - 1, d);
  t.setUTCHours(h, mi, se, frac);
  var ms = t.getTime() - off * 60000;                         // SUBTRACT the offset to get UTC
  if (leap) {                                                 // RFC 3339 §5.7: 23:59:60 UTC on a month's last day
    var u = new Date(ms), nx = new Date(ms + 1000);
    if (u.getUTCHours() !== 23 || u.getUTCMinutes() !== 59 || nx.getUTCDate() !== 1) {
      throw 'fromRfc3339: leap second not at the end of a UTC month: ' + s;
    }
  }
  var gdt = new GlideDateTime();
  gdt.setNumericValue(ms);
  return gdt;
}
```

### Fluent / TypeScript (`*.now.ts`, SDK 4.x) — probed offline

| Grep (ERE) | Why | Safer replacement |
|---|---|---|
| `Time\(\s*\{[^}]*\}\s*\)` (no zone) | build-host zone (F2) | `Time({…}, 'UTC')`; build with `TZ=UTC` |
| `Time\(\s*\{[^}]*\}\s*,\s*['"](Asia\|Europe\|Africa\|Australia\|Pacific\|Indian\|Antarctica)/` | east of UTC: early times with non-whole-hour results are 60 min early (F1); 1970 offset (A1) | pass a UTC time with `'UTC'`; check the XML |
| `ScheduledScript\(` with `timeZone:` east of UTC and no `executionTime` | default `run_time` hit by F1 | set `executionTime: Time({…}, <same zone>)` and check the XML |
| `executionStart\|executionEnd` with a year `0[0-9]{3}`, day `-(29\|30\|31) `, hour `24`, `:60`, or a time in a DST gap/overlap | rollover (F10), year remap (F6), dropped record with exit 0 (F12), host-dependent gap (F4) | strict check below; avoid 01:00–03:00 local on DST days; build with `TZ=UTC` |
| `(DateTime\|DueDate\|CalendarDateTime\|BasicDateTime\|Date\|OtherDate)Column` values with `as any\|as unknown as\|@ts-ignore\|@ts-expect-error` | removes the only gate; verbatim XML (F9, F14) | typed literals + CI regex |
| `['"][0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]` in `.now.ts` `data:` blocks | RFC 3339 in an SN field; ships verbatim when cast | convert in a generator: `Temporal.Instant.from(s).toString().slice(0,19).replace('T',' ')` (`new` is not allowed in Fluent files) |
| `ScheduleDateTimeColumn\(` | typed `string`: accepts anything (134 / 216 invalid vectors) | strict check below |
| `(TimeColumn\|DurationColumn)` set to `\{\s*(hours\|minutes\|days\|seconds)\s*:` without `Time(`/`Duration(` | `[object Object]` (F13) | wrap in `Time(…)` / `Duration(…)` |
| `timeZone:\s*['"]([+-][0-9]\|[a-z])` | offsets and lower case stored as written (A2) | canonical IANA names |
| `Date\.now\(\)\|new Date\(` in `.now.ts` | TS214 build error, or `Symbol(CallExpressionShape)` (F13) | string literals |
| CI uses `now-sdk build` exit code alone | exit 0 with records dropped (F12) | also fail on `grep -q 'ERROR' build.log`; compare record counts |
| `now-sdk transform` / `build` without `TZ=UTC` | F2, F3, F4 | `TZ=UTC now-sdk …` |

Strict check for the `glide_date_time` profile (ASCII, anchored; then check the day of the month; for
`glide_date` use the date part):

```
^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$
```

## 5. How to audit a ServiceNow app

1. **Scope.** List the boundaries: outbound REST/SOAP, Scripted REST, Table API clients, import sets, Flow
   transforms, Fluent `dist/` output. For each, write down the contract (RFC 3339? native? display value?).
   Record the native profile once as a stated platform profile (§1).
2. **Scan, including build output.** `rfcdt.py scan` skips directories named `dist` by default, so add the flag:
   ```sh
   python3 scripts/rfcdt.py scan . --include-dist --json > scan.json   # app root: src/ and dist/
   ```
   Then run the §4 greps (`rg -n -e '<pattern>' src/`). Most Glide and Fluent patterns are not in rfcdt.
3. **Build diff (Fluent apps, offline).** Build under three host zones and diff:
   ```sh
   probes/servicenow/fluent-build-diff/build_diff.sh /path/to/app UTC America/New_York Asia/Kolkata
   ```
   Any diff line is a host-dependent value (F2, F4). `exit=0` with `ERROR` lines means dropped records (F12).
   `Asia/Kolkata` (east, +05:30) and `America/New_York` (west, DST) cover both offset signs and a half-hour zone.
   Also check every date element in `dist/**/*.xml` with the strict check (§4), and look for control characters
   (F14): `python3 -c "import pathlib;[print(p) for p in pathlib.Path('dist').rglob('*.xml') if any(b<32 and b not in (9,10,13) for b in p.read_bytes())]"`.
4. **Helper probe.** `TZ=<zone> node probes/servicenow/fluent-build-diff/helpers_probe.cjs` shows whether the
   installed SDK version still has F1–F4, F6, F7, F10. Re-run it for each SDK upgrade; line numbers in §3 are 4.13.0.
5. **Glide helpers under Node.** If the app's Script Include date code uses only epoch-ms `GlideDateTime`
   methods, run the vectors with the stand-in adapter (see `probes/servicenow/README.md` §2), under `TZ=UTC` and
   `TZ=America/New_York`. Label the result "stand-in, not Rhino". Code that relies on Glide parsing needs step 6.
6. **Instance probe (optional, read-only).** Only for users who have an instance. Run
   `probes/servicenow/instance_probe.js` as a background script as a UTC user and as an `America/New_York` user
   (steps in `probes/servicenow/README.md` §3). It writes nothing unless `WRITE_TABLE` is set. Without an
   instance, report every §6 claim as "unverified (needs instance)", never as clean.
7. **Report.** Use the SKILL.md report format. Put the platform profile in Scope. Grade by the §1 mapping.
   List each §6 item you did not run under "Not run".

## 6. Needs an instance

Each claim below is unverified. The probe ID says what verifies it. P-* rows are in `instance_probe.js`.

| Claim | Probe |
|---|---|
| Session zone, `glide.sys.date_format`/`time_format`, `default.tz`, **`glide.sys.internal.tz`** (is `getValue()+'Z'` safe?) | P-ENV |
| Output of every getter for one instant, incl. undocumented `getXMLValue`, `getUTCValue`, `getDisplayValueWithoutTZ`, `excludeZFromFormat` | P-OUT |
| `JSON.stringify({t: gdt})` (`{}`, a string, or an error) | P-JSON |
| `getValue()+'Z'` and `new Date(ms).toISOString()` in Rhino, incl. year 0000 | P-RFC |
| `gs.now`, `nowNoTZ`, `nowDateTime`, `beginningOfToday`, `minutesAgo(0)`: zone and format | P-GS |
| 28 inputs × 19 setters (`T`, `t`, `Z`, offsets, fractions, `:60`, Feb 30, `24:00`, `setValueUTC` with `'T'…'Z'`, `XXX`, `SSSXXX`): `valid`, `threw`, `kept_sentinel`, `delta_ms` | P-IN |
| `GlideRecord.setValue` / assignment / `GlideElement.setDisplayValue` with ISO strings (uninserted record) | P-ELEM |
| `setTimeZone()` with valid and unknown zones | P-TZ |
| DST gap `2026-03-08 02:30` and overlap `2026-11-01 01:30` (New York); `addDaysLocalTime` vs `addDaysUTC` | P-DST |
| Milliseconds kept in memory, lost through `getValue()` | P-PREC |
| `GlideDate.setValue` / `GlideTime.setValue` with offsets, fractions, `24:00:00`, `23:59:60` | P-DATE, P-TIME |
| Stored precision of `glide_date_time` (opt-in write) | P-DB |
| Table API read format for `sysparm_display_value=false\|true\|all` | REST-R |
| Table API write: which of `T`/`Z`/`t`/offset/fraction/`:60`/Feb 30 are accepted, and the stored instant | REST-W |
| Scripted REST serialization of a GlideDateTime / GlideElement | REST-S |
| Flow *Date to String* `…'Z'` and `…SSSXXX` output; *String to Date* with `Z`, `+02:00`, `z` | FLOW |
| How install treats verbatim RFC 3339 / IXDTF / NUL / `[object Object]` in date fields (F9, F13, F14); `glide_time` 1970 vs current offset (A1); `time_zone` `+05:30` / `asia/kolkata` (A2); what "floating" means | INSTALL (`now-sdk install` to a dev instance, then read the records back with REST-R) |

REST commands (personal developer instance only; `$I` host, `$U:$P` a test user in `America/New_York`; a
throwaway table `u_rfc_probe` with a Date/Time column `u_dt`):

```sh
# [REST-R]
for dv in false true all; do
  curl -s -u "$U:$P" -H 'Accept: application/json' \
    "https://$I/api/now/table/u_rfc_probe?sysparm_limit=1&sysparm_fields=sys_created_on,u_dt&sysparm_display_value=$dv"; echo; done
# [REST-W] expected for RFC-valid inputs (UTC): 2026-09-24 12:34:56 (Z forms), 2026-09-24 10:34:56 (+02:00)
for v in '2026-09-24 12:34:56' '2026-09-24T12:34:56Z' '2026-09-24t12:34:56z' '2026-09-24T12:34:56+02:00' \
         '2026-09-24T12:34:56.789Z' '2026-09-24T12:34:56' '2016-12-31T23:59:60Z' '2024-02-30 12:00:00'; do
  for idv in false true; do
    curl -s -u "$U:$P" -H 'Content-Type: application/json' -H 'Accept: application/json' \
      -X POST "https://$I/api/now/table/u_rfc_probe?sysparm_input_display_value=$idv&sysparm_fields=sys_id,u_dt" \
      -d "{\"u_dt\":\"$v\"}"; echo "  <- input=$v idv=$idv"; done; done
# [REST-S] a Scripted REST resource that does response.setBody({t: new GlideDateTime(), e: current.sys_created_on})
```

[FLOW]: in Workflow Studio, build a flow with *Date to String* (`yyyy-MM-dd'T'HH:mm:ss'Z'` and custom
`yyyy-MM-dd'T'HH:mm:ss.SSSXXX`) and *String to Date* (inputs `…Z`, `…+02:00`, `…z`). Run *Test* as a New York
user and record the pill values.

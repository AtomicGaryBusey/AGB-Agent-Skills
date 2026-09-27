# Rules of interpretation

Read this before grading any finding (SKILL.md, before step 3). Rule numbers are cited as "rule N" in SKILL.md,
`hotspots.md`, `servicenow.md` and `ecosystem/`.

**Severity vocabulary.** Every finding gets exactly one of: **Nonconformity**, **Deviation**, **Advisory**, or
**Review note**. A Review note records how you read ambiguous or silent RFC text (rule 5), a profile reading (for
example a stated template that spells only `T` and `Z`), or a choice the RFC leaves open (INTERPRETATION vectors).
It is never counted as a defect. It replaces the older term "Interpretation note".

**MAY-level and optional items about compliant code are not findings.** Code that meets every MUST and SHOULD
and simply does not use an optional feature (an optional reference, an elective tag, a MAY-level resolution) is
compliant: do not put it in the findings table or count it. Mention it only under Review notes if it helps the
reader. An Advisory needs a concrete weakness, such as the rule 2 `Z`/`+00:00` cases.

## Rules

1. **Severity by level:**

   | Level | Report as |
   |---|---|
   | `MUST` / `MUST NOT`, or grammar (fails the ABNF including its range comments such as `00-23`, or the §5.7 restrictions) | **Nonconformity** |
   | `SHOULD` / `SHOULD NOT` | **Deviation**: departing from it needs a stated reason |
   | `MAY`, lower-case "should/may", informative | **Advisory** |
   | Ambiguous text (see rule 5) | **Review note**: never a Nonconformity |

   Grading consumers and producers:
   - **Consumer, too lenient:** a Nonconformity when the consumer validates or
     gates input (validators, ingest and API boundaries, deserializers of
     untrusted data), or when its contract claims RFC 3339/9557, **unless** it
     documents the leniency. Documented leniency, or a general-purpose parser
     that makes no RFC claim, is an Advisory.
   - **Producer, outside the grammar:** always a Nonconformity when the output
     is claimed or consumed as RFC 3339.
   - **Well-formed but wrong:** a producer that emits a grammatical string for
     the wrong instant (local wall time labelled `Z`, a sign-inverted offset, an
     offset from the wrong zone, years 0–99 remapped to 19xx) is a
     **Nonconformity**, even though the related catalog check is informative.
     The RFC defines what `Z` and offsets *mean* (3339 §2, §4.2, §5.6), and a
     false instant breaks that meaning. The same applies to a consumer that
     accepts a string but produces a different instant or different effective
     tags (e.g. last-wins duplicates, where §3.3 says MUST choose the first).
   - **Contract and docs:** a false claim (for example "CI guarantees
     well-formed timestamps" while output is invalid, or "ISO 8601" examples a
     conforming parser rejects) is a **Deviation**. Report it once, pointing to
     the invalid output rows.
2. **Z semantics (RFC 9557 §2, updates 3339 §4.3).**
   - `Z` (and `-00:00`) now means "the time in UTC is known, but the local offset
     is unknown".
   - `+00:00` still means "UTC is the preferred reference".
   - Findings (**Advisory**: RFC 9557 §2.2 says Z "can be represented" and §2.3 uses a
     lower-case "should", so neither is a BCP 14 requirement):
     - A producer emits `+00:00` for instants with no known local context
       (use `Z`).
     - A round-trip rewrites `+00:00` into `Z`, or `Z` into `+00:00`, where the
       distinction is used downstream.
     - `-00:00` is still valid. It is not deprecated, but `Z` should be used in its
       place (Advisory).
3. **Profiles must be explicit.**
   - The space separator is outside the ABNF (erratum 5783, held) and allowed
     only when a profile states it.
   - Lower-case `t`/`z` are **valid** input (ABNF strings are case-insensitive),
     but producers SHOULD emit upper case.
   - `full-date`/`full-time`/`partial-time` used on their own need a stated
     production (erratum 5624, held).
4. **Consumer obligations under RFC 9557.** These are the core checks; the
   decision table is in `references/rfc9557-checks.md`:
   - **Unknown critical key or value** (`[!k=v]`): the string MUST be treated as
     erroneous. So must a critical time zone the consumer cannot evaluate (no tz
     database, unknown zone, or an instant outside the tz range). rfcdt reports
     `R9557-3.3/critical-unprocessable`.
   - **Unknown elective key or value:** the recipient is free to ignore it, and MAY
     process it further (§3.3). Rejecting it is not forbidden, so vectors grade it
     as an interpretation. But a parser that rejects *every* unknown elective tag
     erases the elective/critical distinction: report that as an **Advisory**.
   - **Experimental `_key`:** MUST be rejected unless the consumer is configured
     for that experiment.
   - **Offset inconsistent with a critical time zone:** the consumer MUST act
     (reject, or resolve explicitly). If the zone is elective, it MAY act.
   - **`Z`/`-00:00` followed by a zone:** never an inconsistency.
   - **Repeated elective keys:** the first one wins. Conflicting copies where any
     is critical make the string erroneous.
   - **An unknown time-zone name** is handled like any other inconsistency.
   - **Producers MUST NOT** copy the UTC offset into an offset time zone
     (`+08:45[+08:45]`) just to satisfy a consumer that requires a suffix.
5. **Known ambiguities.** State your reading; do not grade a target against it.
   - **9557 §4.1 `time-zone` ABNF precedence:** read strictly, it groups wrongly.
     The intended reading is `"[" critical-flag (time-zone-name / time-numoffset) "]"`.
   - **9557 §1.2 prose examples without seconds**
     (`2020-01-01T00:00+01:00[Europe/Paris]`) are invalid under the grammar. Do not
     use them as positive tests.
   - **`Z[+08:45]`:** §1.2 read literally calls it inconsistent; the §3.4 Figure 2
     reasoning says `Z` asserts no offset. It is implementation-defined.
   - **Leap-second months:** §5.7 limits `:60` to "months in which a leap second
     occurs", and Appendix D prefers June/December, then March/September. The
     validator's default `--leap-seconds iers-months` accepts 23:59:60 UTC only at
     the end of Mar/Jun/Sep/Dec from 1972 onward. Other modes are `table` (actual
     insertions through 2016-12-31), `any-month-end` and `grammar` (ABNF only).
     A target that uses a table, or any of the other policies, is not wrong:
     those vectors are graded as interpretations.
   - **Leap second with an offset:** the leap second point moves with the offset
     (§5.7). `1990-12-31T15:59:60-08:00` is valid;
     `2016-12-31T23:59:60+01:00` is not.

## Grading vector results

- A **validator** that is TOO LENIENT is a Nonconformity. A **general-purpose parser** that is too lenient is
  graded by rule 1 (Nonconformity at a gate or under an RFC claim, else Advisory).
- A parser that is TOO STRICT is a Nonconformity, unless it has a stated profile restriction (for example the
  protobuf Timestamp profile: no `:60`, at most 9 fraction digits, years 0001–9999).
- WRONG VALUE and HOST-TZ DEPENDENT results are Nonconformities (a false instant, rule 1).
- **Space separator.** A parser with no stated profile that accepts `2026-09-24 12:00:00Z` is TOO LENIENT
  (the space is outside the ABNF; the §5.6 NOTE lets an application *profile* choose it; erratum 5783 is Held).
  In the ecosystem tables the verdict is "too lenient (space; OK only under a stated profile)".
- **Leap-second representation.** On a valid leap-second vector (expected second 60), a target that returns
  :59 of the same minute, or :00 of the next minute with the date and time correctly rolled over, cannot store
  :60. The runner grades this as INTERPRETATION ("leap-second representation"), not WRONG VALUE. Any other
  value (for example :00 without the roll-over) stays WRONG VALUE. Mention the limit as a Review note when the
  application needs the leap second itself.
- **Fraction precision.** A target that stores fewer fraction digits than the input passes when the returned
  fraction equals the exact fraction truncated, or rounded half-up or half-even, to the returned precision
  (for example .NET ticks: `.12345678…` → `1234568`). Rounding that carries into the seconds is not accepted.
- INTERPRETATION results (`"expect": "either"` vectors, `"resolved": true` answers on `resolvable` vectors, and
  leap-second representations) record the target's choice. List the choices as Review notes; never grade them.
- `run_vectors.py --report md` gives a severity guess from each vector's check levels. Refine it by role.

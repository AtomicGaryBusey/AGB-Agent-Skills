---
name: wcag22-a11y
description: "Audit web content for WCAG 2.2 conformance (also WCAG 2.1/2.0 Level A/AA) with tool-assisted and manual checks. USE FOR: accessibility (a11y) audits and reviews of web pages, sites, HTML, components (React/JSX/TSX, Vue, Svelte, server templates) and CSS; colour contrast; keyboard access, focus order, focus visible, focus not obscured; target size; screen reader issues in markup (names, roles and states, ARIA); forms, labels and error messages; reflow, zoom and text spacing; accessible authentication, consistent help, redundant entry, dragging; status messages; VPAT/ACR evidence and Section 508 / EN 301 549 mapping at the WCAG level. DO NOT USE FOR: native mobile app platform guidelines beyond WCAG applicability, legal advice, PDF remediation (unless the content is HTML), SEO, performance or security audits, ISO 999 indexes, RFC 3339 timestamps, ASD-STE100 writing."
metadata:
  author: local
  version: "1.0.0"
  standard: "WCAG 2.2, W3C Recommendation, 12 December 2024 edition"
---

# WCAG 2.2 conformance audit

WCAG 2.2 has 87 success-criterion (SC) sections: 86 active criteria plus 4.1.1 Parsing, which is obsolete
and removed. Levels are cumulative: **A** = 31 SC, **AA** = A + 24 = **55 SC (the default audit target)**,
**AAA** = all 86. New in 2.2: 2.4.11, 2.4.12, 2.4.13, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8, 3.3.9 (six of them at
A/AA). An AA audit ends with each of the 55 SC as pass, fail, N/A or not evaluated; AAA items are never AA failures.

## Authority and licence

- The authority is **WCAG 2.2, W3C Recommendation, 12 December 2024** (<https://www.w3.org/TR/WCAG22/>).
  Understanding and Techniques documents are informative: they explain an SC but do not add requirements.
- SC text, notes and glossary definitions in `references/` are quoted verbatim under the W3C Document License
  (Copyright © 2024 World Wide Web Consortium). Keep the attribution when you quote them; see `NOTICE`.
  Procedures, patterns, examples and tool mappings are this skill's own work.
- A policy that cites WCAG 2.0 or 2.1 (Section 508, EN 301 549) can still require 4.1.1. Say which version
  the report uses (`references/interpretation.md` §7).

## Conformance requirements (summary)

A page conforms only when all five hold (full text: `references/conformance.md`):

1. **Level** met in full: every SC at the level and below passes or does not apply.
2. **Full pages**: every state and responsive variant, including dialogs, menus and error states.
3. **Complete processes**: one failing step (login, checkout) fails every page of the process.
4. **Accessibility-supported** techniques only: an ARIA pattern that screen readers do not expose does not count.
5. **Non-interference**: 1.4.2, 2.1.2, 2.2.2 and 2.3.1 apply to all content, even content not relied upon.

## Severity

Full rules, per-SC exceptions and the tool-by-tool judgement guide: `references/interpretation.md`.

| Basis | Report as |
|---|---|
| Objective SC failure, confirmed (tool `fail` you verified, or a failed manual test) | **Nonconformity** |
| Likely failure that needs confirmation; heuristic tool finding (`warn`) not yet confirmed | **Deviation** |
| Best practice (`WCAG-BP-<slug>`), AAA item in an AA audit, tool `info` | **Advisory** |
| Manual check or judgement item (`manual`), ambiguous exception, AT-support question | **Review note** |

- An SC with no relevant content (1.2.x on a page with no media) is **N/A** in the coverage table, not a finding.
- Evidence moves the grade: a confirmed Deviation becomes a Nonconformity; a disproved one is dropped (say why
  in Review notes). A tool `fail` that an exception covers is not a finding.
- One root cause is one row; list the other SC it breaks in the same row.
- **Automated coverage is partial.** Each tool gives signal on about 30 of the 55 AA SC (34 together), and
  only on part of each. A clean tool run is never a conformance claim.

## Workflow

`S=~/.claude/skills/wcag22-a11y/scripts`. Flags, JSON shapes, exit codes and limits: `references/tooling.md`.
Detailed steps and a sample report: `references/workflow.md`.

1. **Scope.** List the pages or URLs, the complete processes (every step), the level (default AA), the
   technologies relied upon and, if relevant, the browser and assistive-technology (AT) matrix. Filter
   `references/check-index.md` by level.
2. **Setup (once).** `bash $S/setup_page_runner.sh` installs Playwright, axe-core 4.13.0 and headless Chromium
   into the gitignored `.cache/` (about 220 MB). `bash $S/setup_page_runner.sh --check` verifies it. Without
   it, the static scan still runs and the page runner is listed under "Not run".
3. **Run the tools.**
   ```bash
   python3 $S/wcag_audit.py <src-dir> --url <url|built-html-dir> --pages N --out report.md [--json merged.json]
   python3 $S/wcag_scan.py <paths> --json            # static source scan only
   node $S/wcag_page.mjs <url|file|dir> --json --screenshots shots/   # rendered pages only
   ```
   `wcag_audit.py` merges both tools and writes the report skeleton with an SC coverage table and a "Manual
   checks required" list. Options: `--level A|AA|AAA`, `--no-page`, `--no-scan`.
4. **Confirm every tool finding** in the rendered page and source. Common false positives: logotype or
   incidental text flagged for contrast; inline text links flagged for 2.5.8; sticky headers flagged for 2.4.11
   when `scroll-padding` keeps focus visible; decorative images correctly hidden (`alt=""`, `aria-hidden`);
   generic link text whose purpose is clear from its sentence or list item. Full list:
   `references/interpretation.md` §4.
5. **Manual checks.** Walk the report's "Manual checks required" list with `references/manual-checks.md`:
   keyboard-only walkthrough, screen reader smoke test, zoom/reflow/text spacing, forms and errors, media,
   motion and timing, authentication (3.3.8), consistent help (3.2.6), redundant entry (3.3.7), dragging (2.5.7),
   target-size exceptions (2.5.8), status messages (4.1.3). For each SC, use its **Test procedure** in
   `references/sc-1-perceivable.md` … `references/sc-4-robust.md`.
6. **Report** in the format below. Update each SC status in the coverage table after the manual pass. If no
   assistive technology was used, say so in Assumptions and list what a screen-reader smoke test must confirm
   (`references/workflow.md` Step 6).

## Report format

```
# WCAG 2.2 Level AA audit — <target>

Scope: <pages/URLs>, processes <list>, level AA (55 SC; 4.1.1 obsolete), tools <wcag_scan, wcag_page>, AT/browsers <matrix|none>
Summary: N nonconformities, N deviations, N advisories, N review notes; SC: N fail, N pass, N N/A, N not evaluated
Evidence: <tool runs with counts, e.g. "wcag_scan 0.1.0: 42 files, 31 findings (12 fail, 17 warn, 2 manual); wcag_page 0.1.0: 5 pages, 18 findings; keyboard walk 5/5 pages; NVDA 2026.2 + Firefox smoke test">

## Findings
| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|

## SC coverage          (table from wcag_audit.py, statuses updated after manual checks)
## Review notes
## Manual checks required
## Not run / not applicable
## Assumptions
## Reproduction
```

- **Severity** is exactly one of `Nonconformity`, `Deviation`, `Advisory`, `Review note`; never "Fail",
  "Failure" or "Error" (those words belong only in the SC coverage status).
- **Check ID** is `WCAG-<sc>` (`WCAG-2.5.8`) or `WCAG-BP-<slug>` for best practice. **Ref** is
  `WCAG 2.2 SC 2.5.8 (Level AA)`. **Target** is `page`, `component`, `stylesheet` or `template`. **Location**
  is `file:line` or URL plus CSS selector. **Evidence** is the tool rule and a measured fact (ratio, size,
  selector, keystroke sequence, AT announcement). **Fix** is a concrete code change.
- Rank by severity, then by SC order. "Manual checks required" lists every in-scope SC not yet evaluated;
  it must be empty before any conformance statement.
- **Conformance statements** (optional): only with no open manual checks and no Nonconformity. Give the five
  required components (date; "Web Content Accessibility Guidelines 2.2 at https://www.w3.org/TR/WCAG22/";
  level; pages covered; technologies relied upon). Otherwise say "does not conform" and list the failing SC.
  "Partially conforms" is not a WCAG level. For VPAT/ACR wording, see `references/interpretation.md` §6.
- Never report a clean result for a check or SC you did not run.

## Files

**Blind or eval use:** `evals/` holds answer keys and fixtures; never read it while auditing.

| Path | Contents |
|---|---|
| `references/workflow.md` | Audit steps in detail, scoping a sample, AT matrix, sample report |
| `references/interpretation.md` | Severity rules, judging each tool's findings, per-SC exceptions tools cannot see, AA vs AAA, partial conformance, VPAT/ACR, 508 / EN 301 549 |
| `references/manual-checks.md` | Procedure checklists per area, mapped to SC IDs |
| `references/tooling.md` | All four tools: flags, JSON shapes, rule lists, exit codes, `.cache/` layout, runtime, known limits |
| `references/check-index.md` | All 87 SC sections: ID, level, testability, axe rules, file. Filter this first |
| `references/sc-1-perceivable.md` … `references/sc-4-robust.md` | Verbatim SC text, test procedure, failures, techniques, examples |
| `references/conformance.md` | Conformance requirements and claims (verbatim section 5) with auditor guidance |
| `references/glossary.md` | Verbatim WCAG 2.2 definitions (key terms marked) |
| `scripts/wcag_audit.py` | Orchestrator: runs both tools, merges, writes the report skeleton (Python 3.9+, stdlib) |
| `scripts/wcag_scan.py` | Static scanner for HTML, JSX/TSX, Vue, Svelte, templates, Markdown, CSS/SCSS (stdlib) |
| `scripts/wcag_page.mjs`, `scripts/setup_page_runner.sh` | Rendered-page runner (axe-core + custom checks in Chromium) and its installer |
| `NOTICE` | W3C Document License attribution; third-party components |
| `evals/` | Maintainer eval harness. evals/ holds answer keys for the skill's own tests — auditors must not read it |
| `SOURCES.lock`, `tools/revalidate.py` | Maintainer re-validation: pinned WCAG 2.2 edition, errata, catalogue hashes, engine pins, test counts. See `tools/README-maintenance.md` |

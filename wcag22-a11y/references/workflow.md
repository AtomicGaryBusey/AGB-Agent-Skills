# Audit workflow

> **Attribution.** SC numbers, names and levels are from *Web Content Accessibility Guidelines (WCAG) 2.2*,
> W3C Recommendation, 12 December 2024 edition, <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide
> Web Consortium, <https://www.w3.org/copyright/document-license-2023/>. No SC text is quoted here. The steps and
> the sample report (an invented site) are original to this skill. See `NOTICE`.

`S=~/.claude/skills/wcag22-a11y/scripts`. Tool details: `tooling.md`. Grading: `interpretation.md`. Manual
procedures: `manual-checks.md`.

## Step 1 — Scope

Write these down before you run anything; they go in the report's Scope line and Assumptions.

| Item | Decide |
|---|---|
| Level | AA unless the client says otherwise (55 SC). AAA only on request. |
| Standard edition | WCAG 2.2 by default. If the contract cites Section 508 (WCAG 2.0) or EN 301 549 V3.2.1 (WCAG 2.1), keep WCAG 2.2 grading and also report 4.1.1 (`interpretation.md` §7). |
| Pages | A list of URLs or files. For a large site, a structured sample: home, one of each template, search results, every form, error and empty states, plus a few random pages. State the sampling method. |
| Complete processes | Every step of each process (sign-up, login, checkout, password reset). A failure on any step fails the process. |
| States | Responsive breakpoints in use, open menus and dialogs, error states, logged-in views. |
| Technologies relied upon | HTML, CSS, JavaScript, WAI-ARIA, SVG, and so on. |
| AT/browser matrix | At least one screen reader and browser pair. See below. |
| Source access | Source path (for the static scan) and a way to render it (live URL, staging URL, or a built HTML directory). |

**AT/browser matrix** (pick what the audience uses; record versions):

| Platform | Screen reader | Browser |
|---|---|---|
| Windows | NVDA | Firefox or Chrome |
| Windows | JAWS | Chrome or Edge |
| macOS | VoiceOver | Safari |
| iOS | VoiceOver | Safari |
| Android | TalkBack | Chrome |

For a component library or a code review with no rendered page, scope is the components themselves: say that
page-level SC (2.4.1, 2.4.2, 2.4.5, 3.2.3, 3.2.6) are N/A for isolated components or not evaluated.

## Step 2 — Setup

```bash
bash $S/setup_page_runner.sh --check || bash $S/setup_page_runner.sh
```

The first install needs Node 18+, npm and network access, and uses about 220 MB in `.cache/`. If you cannot
install it, run with `--no-page` and list the page runner under "Not run"; the rendered checks (reflow, focus
visibility, target size, contrast over images) then become manual.

## Step 3 — Run the tools

Typical runs:

```bash
# Source plus a live URL, crawl 10 same-origin pages
python3 $S/wcag_audit.py ./src --url https://staging.example.test/ --pages 10 --out report.md --json merged.json

# Source plus a built static site (served on 127.0.0.1 by the runner)
python3 $S/wcag_audit.py ./src --url ./dist --pages 20 --out report.md

# Only a URL (no source access): the static scan is skipped automatically
python3 $S/wcag_audit.py https://www.example.test/ --pages 5 --out report.md

# Only source (component library, no build)
python3 $S/wcag_audit.py ./packages/ui --no-page --out report.md
```

Standalone runs when you need more:

```bash
python3 $S/wcag_scan.py src/components/Checkout.tsx --json          # one file, JSON
python3 $S/wcag_scan.py src --min-severity warn                      # hide info and manual
node $S/wcag_page.mjs https://staging.example.test/login --rules auth,focus --screenshots shots/
node $S/wcag_page.mjs ./dist/cart.html --viewport 390x844 --max-tabs 200   # phone viewport, long page
node $S/wcag_page.mjs https://staging.example.test/ --level AAA --json      # AAA extras on request
```

Rerun the page runner for each state you can reach by URL (error page, step 2 of a form). Pages behind a login
must be served in a logged-in state some other way, or tested by hand.

## Step 4 — Confirm every tool finding

For each row in the skeleton's Findings table:

1. Open the location (source `file:line`, or the URL and selector in dev tools).
2. Check the SC's exceptions (`interpretation.md` §4) and the verbatim SC text in the `sc-*.md` file.
3. Decide: keep (Nonconformity if confirmed, Deviation if you cannot confirm), downgrade (Advisory for best
   practice), or drop (note the reason in Review notes).
4. Merge rows that share one root cause; move secondary SC into the Finding cell.
5. Replace the skeleton's generic Fix ("Fix per Understanding…") with a concrete code change.

Common false positives to rule out first: logotype and incidental text in contrast results; inline links in
target-size results; sticky headers with `scroll-padding` in focus-obscured notes; decorative images correctly
hidden; generic link text whose context gives the purpose; skipped heading levels (Advisory); ids that another
component renders; toast libraries that create their own live region.

## Step 5 — Manual checks

Work through `manual-checks.md` for every page and state in scope, in this order: keyboard walkthrough,
screen reader smoke test, forms and errors, zoom/reflow/text spacing, contrast edge cases, media, timing and
motion, pointer and target size, authentication, consistency across pages. Use the SC's **Test procedure** in
`sc-*.md` for anything the checklist does not settle. Add each failure as a Findings row with observed
evidence.

## Step 6 — Report

Complete the skeleton:

1. **Scope** line: pages, processes, level, tools, AT/browser pairs.
2. **Summary** line: severity counts, then SC status counts (fail, pass, N/A, not evaluated).
3. **Evidence** line: each tool run with counts, plus the manual passes performed.
4. **Findings**: ranked by severity, then SC order.
5. **SC coverage**: set each status to Fail, Pass, N/A (with a reason) or Not evaluated.
6. **Review notes**: dropped tool findings with reasons, judgement calls, AT-support observations.
7. **Manual checks required**: only SC still not evaluated, with the reason and the next step.
8. **Not run / not applicable**: tools not run and why; AAA out of scope; 4.1.1 obsolete; N/A SC.
9. **Assumptions**: sampling, standard edition, states tested, source/render mismatch risks, and components
   graded without rendering (`interpretation.md` §1 rule 8). If no assistive technology was used, say so
   here ("No screen reader was used; AT/browsers: none") and keep the SC that depend on it Not evaluated.
   List what a screen-reader smoke test must confirm (`manual-checks.md` §2): page title and language;
   headings and landmarks; reading order and image alternatives; name, role and state of each custom
   control, before and after it changes; spoken names that contain the visible label; table headers and
   form group legends; status messages and errors announced without focus moving.
10. **Reproduction**: the commands and versions from the skeleton, plus AT and browser versions.

Conformance statement: only if no Nonconformity and no open manual check (`interpretation.md` §6).

## Sample report (invented site)

```markdown
# WCAG 2.2 Level AA audit — Fernhill Bakery ordering site

Scope: 6 pages (home, menu, product, cart, checkout 1–3) at https://staging.fernhill.example/, process "order", level AA (55 SC; 4.1.1 obsolete), tools wcag_scan, wcag_page, AT/browsers NVDA 2026.1 + Firefox 142, VoiceOver + Safari 19
Summary: 4 nonconformities, 1 deviation, 1 advisory, 1 review note; SC: 4 fail, 36 pass, 10 N/A, 5 not evaluated
Evidence: wcag_scan 0.1.0: 58 files, 14 findings (3 fail, 9 warn, 2 manual); wcag_page 0.1.0: 6 pages, 11 findings (4 fail, 6 warn, 1 manual); 5 tool findings dropped after review; keyboard walk and NVDA smoke test on all 6 pages; zoom 200%/400% and text spacing on all 6 pages

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-3.3.8 | WCAG 2.2 SC 3.3.8 (Level AA) | component | src/auth/CodeInput.tsx:41 | Paste is cancelled on the six one-digit code boxes, so the emailed code must be transcribed; no other sign-in method is offered. | wcag_page `otp-paste-blocked` (fail); manual: pasting "482913" into box 1 did nothing | Remove the `onPaste` preventDefault; on paste, spread the digits across the boxes; add `autocomplete="one-time-code"` |
| 2 | Nonconformity | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (Level AA) | stylesheet | src/styles/layout.css:12 | Fixed 88 px header hides focused "Edit" links in the cart when tabbing backwards. | wcag_page `focus-obscured-fully` (fail) on /cart `a.edit`; confirmed by Shift+Tab | `html { scroll-padding-top: 6rem; }` or make the header `position: sticky` inside the flow |
| 3 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | component | src/ui/QtyStepper.tsx:18 | "+"/"−" icon buttons have no accessible name. | wcag_scan `button-icon-no-name`; NVDA reads "button" | `aria-label="Increase quantity"` / `"Decrease quantity"` |
| 4 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | page | /checkout/2 `form.delivery` | At 320 px the delivery-slot grid scrolls sideways; it is a list of buttons, not two-dimensional content. | wcag_page `reflow-horizontal-scroll` (fail) scroll_width 540 > 320 | Let the grid wrap: `grid-template-columns: repeat(auto-fill, minmax(8rem, 1fr))` |
| 5 | Deviation | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (Level AA) | page | /menu `.allergen-tags a` | Allergen tag links are 20×20 px with 2 px gaps; no equivalent control found yet on the product page. | wcag_page `target-size-undersized` (warn) 20×20, circle hits neighbour at 22 px | `min-width/min-height: 24px` or `gap: 6px` |
| 6 | Advisory | WCAG-BP-heading-order | Best practice (1.3.1) | page | /menu `h4.card-title` | Product cards jump from h2 to h4; the visual hierarchy matches, so 1.3.1 is not failed. | wcag_scan `heading-skip` (warn) | Use h3 for card titles |
| 7 | Review note | WCAG-3.3.7 | WCAG 2.2 SC 3.3.7 (Level A) | page | /checkout/3 | Billing address offers "Same as delivery"; "Confirm email" field repeats the email — judged under the security exception? Client to confirm purpose. | wcag_scan `redundant-entry-same-step` (manual) | If not for security, pre-fill or remove the confirmation field |

## SC coverage
(table from wcag_audit.py with statuses updated: 4 Fail, 36 Pass, 10 N/A, 5 Not evaluated)

## Review notes
- Dropped: 3× `contrast-text` on the logo wordmark (logotype exception); 2× `target-size-small` on footer text links (inline exception).
- NVDA announces the cart count update via the existing `role="status"` region (4.1.3 pass).

## Manual checks required
- WCAG-1.2.2, 1.2.3, 1.2.5: the product video on /product is hosted by a third party and did not load on staging; captions and audio description not evaluated.
- WCAG-2.5.8: row #5 — check whether the product page offers an equivalent full-size allergen control.
- WCAG-3.3.7: row #7 — client to confirm the purpose of the "Confirm email" field.

## Not run / not applicable
- Level AAA SC: out of scope. WCAG-4.1.1: obsolete in 2.2.
- N/A: 1.2.1, 1.2.4 (no audio-only, video-only or live media), 1.4.2, 2.2.1, 2.2.2, 2.3.1, 2.5.1, 2.5.4, 2.5.7, 3.1.2.

## Assumptions
- Staging mirrors production templates. Orders can be cancelled for 30 minutes (3.3.4 treated as met by reversibility — confirm with client).

## Reproduction
python3 $S/wcag_audit.py ./src --url https://staging.fernhill.example/ --pages 6 --out report.md
(wcag_scan 0.1.0; wcag_page 0.1.0, playwright 1.63.0, axe-core 4.13.0, Chromium headless shell; NVDA 2026.1 + Firefox 142; VoiceOver + Safari 19)
```

No conformance statement is possible for this sample: it has Nonconformities and one open manual check.

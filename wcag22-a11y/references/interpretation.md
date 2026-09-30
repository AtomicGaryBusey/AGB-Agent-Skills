# Interpretation: severity, tool findings, exceptions

> **Attribution.** SC numbers, names, levels, and short phrases marked with quotation marks are from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium,
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation. The full verbatim SC text is
> in `sc-1-perceivable.md` … `sc-4-robust.md`. All other text is original to this skill. See `NOTICE`.

Always check an exception against the verbatim SC text and its notes in the `sc-*.md` file before you grade.

## 1. Severity rules

| Basis | Report as |
|---|---|
| Objective failure of an in-scope SC, confirmed in the rendered page or by a manual test | **Nonconformity** |
| Likely failure that needs confirmation: a heuristic tool finding (`warn`), a static finding not yet seen in the browser (unless it fails by construction, rule 8), an exception that may apply but is not shown | **Deviation** |
| Best practice that no SC requires (`WCAG-BP-<slug>`); AAA SC in an A/AA audit; tool `info` | **Advisory** |
| Manual check, judgement item, AT-support question, ambiguous exception (`manual`) | **Review note** |

Rules:

1. **Tool severity is a starting point.** A tool `fail` that you confirm stays a Nonconformity. A tool `fail`
   that an exception covers, or that the rendered page disproves, is dropped; write one line in Review notes
   ("#7 dropped: logotype, 1.4.3 exception").
2. **Evidence moves the grade.** Confirm a Deviation (for example, a keyboard walk shows the icon button is
   18×18 with a neighbour 2 px away) and it becomes a Nonconformity. If you cannot confirm (no browser, no
   access to the process), it stays a Deviation and the SC stays "not evaluated".
3. **N/A is not a finding.** An SC with no matching content (1.2.x with no media, 3.3.8 with no authentication,
   2.5.7 with no dragging) is N/A in the coverage table. N/A counts as satisfied for conformance.
4. **One root cause, one row.** A missing accessible name on an icon button can break 1.1.1, 2.4.4 and 4.1.2:
   report it once under the most specific SC and list the others in the Finding cell. A shared component used
   on 40 pages is one row with the component location and "40 instances".
5. **Best practice is never a Nonconformity.** Examples: heading levels that skip (no SC requires sequence),
   redundant `title` attributes, missing `<main>` when headings or a skip link already bypass blocks, ARIA that
   is valid but unnecessary. Use `WCAG-BP-heading-order`, `WCAG-BP-landmarks` and similar slugs.
6. **Deprecated 4.1.1.** Do not report 4.1.1 in a WCAG 2.2 audit. Route real markup defects to the SC they
   break: a duplicate id that breaks a `for` or `aria-labelledby` reference is 1.3.1 or 4.1.2.
7. **User-agent and AT bugs** are not author failures unless the author relied on a technique that is not
   accessibility-supported (conformance requirement 4). Record the AT/browser pair in a Review note.
8. **Unbuilt components (Vue, Svelte, React single-file components you cannot render).** Ask whether any prop,
   slot, wrapper, context value or consumer could change the outcome.
   - **Fails by construction → may be a Nonconformity.** The defect is fixed in the component and nothing the
     caller passes can change it: hard-coded text and background colours below the ratio, a reorder that has
     only drag handlers and no other pointer path, a clickable `<div>` with no `tabindex`, role or key
     handler and no way to pass them in, `onPaste` cancelled on a code field. State the reasoning in
     Assumptions ("not rendered; colours are literals in `Badge.vue:12`, no prop or CSS variable overrides
     them").
   - **Depends on use → Deviation or Review note.** The outcome turns on props, slots, theme tokens, CSS
     variables, a parent that supplies the label or name, or where the component is placed (an `aria-label`
     prop that callers may omit, a colour from a theme variable, a heading level passed in). Say what the
     caller must do in the Fix cell.

## 2. SC status after the manual pass

| Status | Meaning |
|---|---|
| **Fail** | At least one Nonconformity on the SC |
| **Pass** | Tools and the SC's manual test procedure were both run and found nothing |
| **N/A** | No content the SC applies to (state why in one phrase) |
| **Not evaluated** | Not tested, or only tools ran on an SC that needs human review; list under "Manual checks required" |

"Automated checks passed (partial coverage)" from `wcag_audit.py` is not Pass. Only an SC that
`check-index.md` marks **automated** (1.4.3, 1.4.6, 3.1.1) can move to Pass on tool evidence alone, and 1.4.3
still needs the exceptions and the images-of-text/gradient cases checked.

## 3. Judging each tool

### `wcag_scan.py` (static source)

- It reads one file at a time. The cascade, runtime classes, props from other files, framework output and
  third-party components are invisible to it. Confirm source-only findings in the rendered page when you can;
  if you cannot, keep them as Deviations and say so in Assumptions, unless the component fails by
  construction (§1 rule 8).
- `fail` rules decide on facts in the markup (no `alt`, invalid role, `maximum-scale=1`). They are reliable on
  plain HTML; in components, check that a prop or wrapper does not supply the missing name or label.
- `warn` rules are heuristics (generic link text, small declared sizes, `!important` spacing, drag handlers,
  live regions not found). Confirm each one.
- `manual` rules (`contrast-unresolved`, `focus-obscured-check`, `drag-library-check`,
  `redundant-entry-same-step`) only point at something to test.
- Template placeholders are treated as unknown values; a finding next to a template expression may depend on
  data.

### `wcag_page.mjs` (rendered page)

- It tests one viewport (default 1280×800) and the page's load state. Menus, dialogs, error states, and later
  steps of a process are not tested unless you give their URLs or open them by hand.
- axe *violations* are usually real; axe *incomplete* items are review items. Check axe results against the
  exceptions below (axe does not know about logotypes, the 2.5.8 equivalent-control exception, or essential
  presentation).
- `focus-not-visible` compares screenshots of the element focused and unfocused. A change outside the 8 px
  area around the element (a status line elsewhere) is not detected, so confirm by eye.
- `focus-obscured-fully` is strong evidence for 2.4.11. It samples the element box against fixed and sticky
  content after the browser scrolls, so `scroll-padding` fixes are respected.
- `target-size-undersized` measures the rendered box and applies the 24 px circle test. It marks inline links
  as `target-size-exception` [info]; the equivalent-control and essential exceptions need you.
- `reflow-*` runs only at 320×256 CSS px. `reflow-exempt-content` needs your judgement on two-dimensional
  content.
- `auto-update-no-pause` (2.2.2) watches the page for `--observe` ms only: confirm the content starts by
  itself, lasts over 5 s, and has no pause control elsewhere. `status-message-not-announced` (4.1.3) and
  `ui-boundary-contrast-maybe` (1.4.11) need a screen reader or a visual check respectively.
- `keyboard_walk.stop` = `max-tabs` means the walk did not reach every element; `trap` means focus could not
  leave a group with Tab, Shift+Tab or Escape. Several Tab stops inside one native date or time input are its
  segments, not a trap (see 2.1.2 in §4).
- `contrast-sampled-background` samples pixels in a box around the text. Judge the colour actually behind the
  glyphs; see 1.4.3 in §4.

### `wcag_audit.py` (merge)

- It maps `fail`/`warn`/`manual`/`info` to the four report severities mechanically. Your confirmation step
  (rules 1 and 2) replaces that mapping in the final report.
- Its "SC coverage" table says which tool looked at each SC, not whether the SC passes.

## 4. Exceptions and false positives by SC

The table lists what tools cannot see. "Not a failure" means drop the finding (or never raise it).

| SC | Tool rules | Not a failure / check before grading |
|---|---|---|
| 1.1.1 | `img-missing-alt`, `img-alt-empty-in-control`, `svg-img-no-name`, `svg-icon-no-alt`, `img-alt-suspicious`, axe `image-alt` | Decorative images correctly hidden (`alt=""`, `role="presentation"`, `aria-hidden="true"`, CSS background) are correct. An image inside a link or button with `alt=""` is fine when the control has visible text or `aria-label`. CAPTCHA, tests, sensory experiences and controls have their own exceptions (descriptive text only). Alt quality (says what the image conveys, not "image of") is manual. |
| 1.3.1 | `heading-skip`, `table-no-th`, `radio-group-no-fieldset`, `required-asterisk-only`, `layout-table-with-th` | Skipped heading levels are best practice only (Advisory) unless the markup contradicts the visual hierarchy. A radio group named with `role="radiogroup"` + `aria-labelledby` needs no `fieldset`. A table with one header row can pass. The asterisk rule fails only if "required" is not also exposed (`required`, `aria-required`, or text in the label). |
| 1.3.5 | `autocomplete-missing`, `autocomplete-invalid` | Applies only to fields that collect information about the user themselves and have a matching token. A recipient address, a search box, or a coupon code is out of scope. |
| 1.4.1 | `color-only-reference` (heuristic) | A phrase like "shown in red" is only a lead: it fails when colour is the sole cue in both the visual design and the markup. It passes if there is also text, a symbol, a pattern, or a 3:1 contrast difference with a non-colour cue on hover or focus, such as underlined links. |
| 1.4.2 | `media-autoplay-audio` | Passes if the audio stops within 3 seconds, or a pause/stop or independent volume control is available at the start of the page. |
| 1.4.3 | `contrast-text`, `contrast-unresolved`, `contrast-sampled-background`, axe `color-contrast` | Exempt: text that is part of a **logo or brand name** ("logotypes"); **incidental** text in inactive (disabled) controls, pure decoration, invisible text, or text in a picture with significant other visual content. Large text is at least 18 pt (24 CSS px) or 14 pt (about 18.66 CSS px) bold, and needs 3:1, not 4.5:1. Placeholder text is **not** exempt. For text over images or gradients, test the worst-case area behind the glyphs. **Sampled rendering:** the background is what lies directly behind and between the glyphs. Other shapes that fall inside the sample box (map strokes, icons, borders, a neighbouring image edge) are not the text background: re-measure on the glyph area before grading. A pale logotype is exempt; if it is hard to read, an Advisory is allowed, never a Nonconformity. |
| 1.4.4 | `viewport-zoom-disabled`, `resize-text-*` | `user-scalable=no` or `maximum-scale<2` is a failure even though some mobile browsers ignore it. Captions and images of text are exempt. Overlap warnings need a visual check at 200%. |
| 1.4.10 | `fixed-width-no-max`, `reflow-*` | Exempt: content that needs two-dimensional layout for meaning or use (data tables, maps, diagrams, video, games, presentations, toolbars that must stay in one row). A scrolling data table inside a reflowing page passes; the whole page scrolling sideways does not. |
| 1.4.11 | `ui-border-contrast`, `focus-indicator-contrast` | Exempt: inactive components, components whose appearance the user agent sets and the author did not change, and graphics where a particular presentation is essential. A text input needs a visible boundary only if nothing else identifies it as a field. Focus indicators are judged here against adjacent colours (3:1); the size of the indicator is 2.4.13 (AAA). A low-contrast focus ring is a 1.4.11 finding even in an audit limited to Principle 1: 2.4.7 asks only whether an indicator exists. |
| 1.4.12 | `text-spacing-important`, `text-spacing-*` | `!important` only matters if it stops a user style from applying the four metrics. Fixed-height containers that clip text after the override are the real failure. Languages or scripts that do not use a property are exempt for that property. |
| 1.4.13 | `hover-content-no-dismiss` (heuristic) | All manual: dismissible (Escape, without moving hover or focus), hoverable, persistent. Native `title` tooltips are user-agent controlled and exempt. |
| 2.1.2 | `keyboard_walk.stop` = `trap` | A native `<input>` of type `date`, `time`, `datetime-local`, `month` or `week` gives one Tab stop per segment (day, month, year, hour, AM/PM) and sometimes a picker button before focus leaves. That is not a trap. Verify: focus the input, count Tabs until focus lands on the next control, then Shift+Tab back out. It passes if focus leaves in a fixed number of presses (about one per segment plus any picker button). A trap is focus that cycles inside the control or never leaves. |
| 2.1.1 | `click-no-keyboard`, `click-handler-no-role`, axe `scrollable-region-focusable` | A click handler on a wrapper that delegates to a real `<button>` or `<a>` inside is fine. Path-dependent input (freehand drawing) is exempt. |
| 2.2.1 | `meta-refresh-delay` | A 0-second meta refresh (instant redirect) is not a time limit. Exempt: real-time events, essential limits, and limits over 20 hours. |
| 2.2.2 | `marquee-blink`, `media-autoplay-no-controls` | Applies to movement that starts automatically, lasts more than 5 s, and runs in parallel with other content. A loading spinner shown while nothing else is usable is essential and exempt. |
| 2.4.1 | `bypass-blocks-missing`, axe `bypass` | Headings or landmarks are sufficient techniques; a skip link is not required if they exist. Pages without repeated blocks, and component files that are not full pages, are N/A. |
| 2.4.3 | `tabindex-positive`, `positive-tabindex`, `focus-order-anomaly` | Fails only if the order loses meaning or operability. A positive tabindex that happens to follow the visual order is Advisory (`WCAG-BP-tabindex`). |
| 2.4.4 | `link-text-generic`, `link-empty` | Passes when the purpose is clear from the link text **together with** its programmatically determined context: the same sentence, paragraph, list item, table cell with its header, or `aria-describedby`. "Read more" after a heading in the same list item usually passes. Ambiguous for everyone is also allowed. A link whose destination doesn't match its text (a wrong anchor or a stale target) is a content bug, not a 2.4.4 failure: report it as an Advisory. |
| 2.4.5 | — | Needs two or more ways to reach a page in the set. Each of these counts as one way: site-wide navigation that lists or reaches every page; a home page that links to every page; a site map; site search; a table of contents; links between related pages. On a site of three or four pages, links to and from a home page that lists every page can be enough (the home page doubles as the site map; W3C Understanding). Exempt: a page that is "the result of, or a step in, a process" (checkout step 2, a confirmation page, search results). One nav menu and nothing else is a failure for a larger site; on a tiny site, check whether the home page covers the second way before failing. |
| 2.4.6 | `heading-empty` | Headings and labels are not required by 2.4.6; they must describe when present. Wording quality is manual. |
| 2.4.7 | `focus-outline-removed`, `focus-outline-removed-maybe`, `focus-not-visible` | Before failing, search for a replacement: `:focus-visible` rule, `box-shadow`, `border`, background change, or a design-system focus ring on a parent class. The page runner's `focus-not-visible` is stronger evidence than the static rule. |
| 2.4.11 | `focus-obscured-check`, `focus-obscured-fully` | A sticky or fixed header with `scroll-padding-top` (or `scroll-margin`) at least its height usually keeps focus visible: confirm with the page runner or by Tab, and drop the static note. Partly covered passes AA (only 2.4.12, AAA, needs fully visible). Content the user opened (a menu, a non-modal dialog) that can be dismissed without moving focus is exempt. For user-movable content, only the initial position counts. |
| 2.5.3 | `label-in-name`, axe `label-content-name-mismatch` | The visible text must be contained in the accessible name (best practice: at the start). Case, punctuation and extra words after it are fine. Icon-only controls with no visible text are N/A. |
| 2.5.7 | `drag-no-alternative`, `drag-library-check` | Passes if a single-pointer alternative exists (move up/down buttons, click to pick then click to place, a menu). A keyboard alternative alone does **not** satisfy 2.5.7. Exempt: dragging that is essential, or controlled by the user agent (native scrollbars, `<input type="range">` dragging when clicking the track also works). |
| 2.5.8 | `target-size-small`, `target-size-undersized`, axe `target-size` | Exceptions: **spacing** (the 24 px circles do not intersect other targets or circles), **equivalent** control on the same page that meets the size, **inline** targets in a sentence or constrained by the line height of surrounding text (links in paragraphs never fail), **user-agent control** not modified by the author, **essential** or legally required presentation. A static `width: 16px` may be enlarged by padding: measure the rendered box. |
| 3.1.2 | `lang-invalid` | Proper names, technical terms, words of indeterminate language, and words that have become part of the surrounding language are exempt. |
| 3.2.2 | `onchange-navigates` | Passes if the user was told about the behaviour before using the control. |
| 3.2.6 | `help-order-inconsistent`, `help-single-page` | Applies only when a help mechanism repeats across a set of pages. Providing help is not required, and a page that omits it does not fail. Order is relative to other page content in the serialized (DOM) order, and a change the user starts is exempt. Compare pages in the **same page variation** (same breakpoint, zoom and orientation); a mobile layout against a desktop layout is not a valid comparison. **Multi-step processes:** the steps are pages in the same set. Moving help on one step (header on steps 1 and 3, footer on step 2) changes its order relative to the content around it, so it fails. A visual move that keeps the same DOM order does not fail (unhelpful, but Advisory at most). |
| 3.3.1 | `error-not-described` (heuristic) | Fails when an input error is detected automatically but is shown only by colour, a border or `aria-invalid`, with no text naming the field and the problem. Confirm by triggering the error: text that appears in a linked or nearby container passes. 3.3.1 and 3.3.3 apply only to errors that are **detected**: a form that does no validation at all doesn't fail them. Report missing validation as an Advisory at most, and never against fields an exception covers, such as a password confirmation under 3.3.7. |
| 3.3.2 | `placeholder-only-label`, `control-no-label` | A placeholder gives an accessible name in browsers, but it disappears once the user types, leaving no visible label; grade it under 3.3.2 and do not also fail 4.1.2 for the same field. Placeholder contrast is judged under 1.4.3. A visible adjacent label that is not programmatically linked fails 1.3.1, not 3.3.2. |
| 3.3.7 | `redundant-entry`, `redundant-entry-same-step`, `possible-redundant-entry` | Applies within the same process and session. Passes if the value is auto-populated or selectable. Exempt: re-entry that is essential (memory tests), required for security (password confirmation), or when the earlier value is no longer valid. A "confirm email" field is a Review note: judge whether the security exception applies. |
| 3.3.8 | `paste-blocked`, `password-paste-blocked`, `otp-paste-blocked`, `password-autocomplete-off`, `captcha-on-auth`, `captcha-cognitive-test` | A cognitive function test (remember or transcribe a password or code, solve a puzzle) fails unless there is an alternative method, a mechanism that helps (password-manager autofill, paste), an object-recognition test, or a test that asks for personal content the user gave the site. Blocked paste on a password or code field fails. `autocomplete="off"` on a password field is a Deviation: most browsers ignore it; confirm with a password manager. Passkeys, email links, and OAuth pass. Object recognition and personal content are allowed at AA but not at 3.3.9 (AAA). |
| 4.1.2 | `aria-*`, `aria-state-not-updated`, `button-empty`, `custom-control-no-name`, `aria-idref-missing`, `focusable-no-role`, axe rules | `aria-idref-missing` in one file can resolve at runtime (the id is in another component): confirm in the DOM. `aria-hidden-focusable` is real unless the element is also `inert` or `tabindex="-1"` through a parent. Names, states and value changes need a screen reader check. |
| 4.1.3 | `status-message-no-live`, `status-message-js-no-live` | A status message reports the result of an action, a wait, progress, or errors, and does not move focus ("18 results", "Saved", "Uploading 40%", "3 errors"). A toast library may add its own live region: confirm with a screen reader or the DOM. **Not status messages:** content the user explicitly asked to see (next or previous slide, "Show more", a tab panel, an expanded accordion, the search results list itself); messages that move focus (a change of context, judged under 3.2.x); errors rendered on page reload. Do not ask for a live region on a carousel or tab panel under 4.1.3; judge its controls under 4.1.2. A separate short result line added with the new content ("Showing 40 of 60") is a status message. |

## 5. AA versus AAA

- An AA audit covers the 55 A and AA SC. Do not fail AAA SC; tool findings on AAA SC (2.4.12, 2.4.13, 1.4.6,
  3.3.9) become Advisory, or are omitted if the client did not ask for them.
- When the client asks for AAA, grade AAA SC like any other; note that W3C does not recommend AAA as a
  blanket policy for whole sites.
- If a finding fails an AA SC and a related AAA SC (focus fully hidden: 2.4.11 and 2.4.12), report the AA SC.

## 6. Conformance claims, partial conformance, VPAT/ACR

- **Claim**: allowed only when every in-scope SC is Pass or N/A for every page and process step in scope,
  and no manual check is open. Include the five required components (see `conformance.md`) and the AT and
  browsers tested.
- **Otherwise**: "does not conform to WCAG 2.2 Level AA" and the list of failing SC. "Partially conforms" is
  not a WCAG level.
- **Statement of partial conformance, third-party content (5.4)**: only for content the author does not
  control (user comments, injected ads), described so users can identify it. **Language (5.5)**: only when
  accessibility support does not exist for a language used. Neither turns a failing page into a conforming one.
- **VPAT/ACR** (Accessibility Conformance Report) terms per SC: *Supports* = Pass; *Partially Supports* =
  some content or functions fail; *Does Not Support* = the majority fails; *Not Applicable* = N/A;
  *Not Evaluated* = not tested (allowed only for AAA in most VPAT editions). Never write "Supports" for an SC
  whose manual check is open. The remarks column cites the finding numbers.

## 7. Section 508 and EN 301 549 at the WCAG level

This is a mapping aid, not legal advice. Check which standard edition the contract or procurement cites.

- **Section 508** (US, revised 2017) incorporates **WCAG 2.0 Level A and AA** (38 SC) for web content,
  documents and software UI. WCAG 2.2 AA results cover it, except that 4.1.1 Parsing is still in WCAG 2.0:
  test and report it if the ACR uses the 508 edition. SC added in 2.1 and 2.2 are beyond 508; list them as
  extra information.
- **EN 301 549** (EU) V3.2.1 references **WCAG 2.1 Level A and AA** (clause 9 for web, 10 for non-web
  documents, 11 for software), again with 4.1.1. A later edition may reference WCAG 2.2; use the one cited.
  Clauses outside WCAG (for example, clause 5 generic requirements, 6 two-way voice, 7 video, 12 documentation)
  are out of scope for this skill.
- **Mapping rule:** keep one finding per SC and add the 508 or EN clause in the Ref cell only when the client
  asks (`WCAG 2.2 SC 1.4.3 (AA); EN 301 549 9.1.4.3`). EN 301 549 web clauses follow the pattern
  `9.<WCAG SC number>`.

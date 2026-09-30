# WCAG 2.2 Level AA audit: Brightwater Transit static front end, Principle 1 (Perceivable)

**Scope:** 11 pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, 7 scripts in `js/`, 2 SVGs in `img/` and 4 Vue components in `components/`. Only the Principle 1 success criteria at Level A and AA are covered, which is 20 of the 55 AA criteria. The one multi-step process is the lost item claim (claim-1 → claim-2 → claim-3). Sign in (password, then a one-time code) is also in scope.
**Tools:** none. With no shell, `wcag_scan` and `wcag_page` could not run, so this is a static review of the source. No browser or screen reader was used.
**Summary:** 10 nonconformities, 2 deviations, 1 advisory, 8 review notes. Of the 20 criteria: **8 fail, 4 pass, 6 N/A, 2 not evaluated.**
**Evidence:** I read every file in full: 11 HTML, 1 CSS, 7 JS, 4 Vue and 2 SVG. I worked out contrast ratios by hand from the CSS hex values, using the WCAG relative luminance formula. Reflow was checked by working out widths at a 320 CSS px viewport (`main` has 16px padding, so 288px is usable).

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `planner.html:36`, `css/site.css:103-105` | The "locate me" button has no text alternative. Its only content is a CSS background image. Also breaks 4.1.2. | `<button … id="locate-me"></button>` is empty, with no `aria-label` or `title`. The icon comes from `background: … url("../img/locate.svg")`. Screen readers announce just "button". | Add `aria-label="Use my current location"`, or put inside the button an inline `<svg aria-hidden="true">` plus visually hidden text. |
| 2 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `planner.html:61`, `planner.html:70` | The step-free icon has no text alternative, even though it carries information: trips 1 and 3 are step-free and trip 2 has stairs. | `<svg class="ico" width="20" height="20"><use href="img/sprite.svg#step-free"></use></svg>` has no `role="img"`, `<title>` or `aria-label`. | Use `<svg class="ico" role="img" aria-label="Step-free route" …>`, or add visible text such as "Step-free" beside the icon. |
| 3 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `map.html:37-50`, `js/map.js:15-19` | The route map's text alternative is just a name ("Harbour Line and Route 14"). Which stops each line serves, and that Market Square is the interchange, is shown only by the drawn lines. The text stop details only appear when a mouse user clicks a stop (the `<g>` elements can't be focused). Also relevant to 2.1.1 (out of scope). | `<title id="map-title">` is the only description. The line-to-stop mapping exists only in the `polyline` points. | Next to the map, add a text version: for each line, a list of its stops in order (e.g. "Harbour Line: Keel Street, Market Square, Saltmarsh, Ferry Terminal, Pier 3"). Make each stop a focusable `<a>` or `<button>`. |
| 4 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `fares.html:47-60`, `fares.html:62`, `:70`, `:78`, `:86` | The fare table's column and row headers are `<td class="th">` cells styled to look like headers. Their header role isn't in the code, so screen reader users hear prices with no zone or rider type. | The table has no `<th>`, `<thead>` or `scope` anywhere. Headers are styled only by `.fare-table td.th` (`site.css:121`). | Use `<thead>` with `<th scope="colgroup" colspan="2">` / `<th scope="col">`, and `<th scope="row">` for Adult, Youth, Senior and Reduced fare permit. |
| 5 | Nonconformity | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (Level AA) | page | `claim-1.html:36`, `claim-1.html:40`, `claim-1.html:44` | The user's own name, email and phone fields don't identify their purpose. The email field turns autofill off explicitly. | `c-name` and `c-phone` have no `autocomplete`. `c-email` has `autocomplete="off"`. | Use `autocomplete="name"`, `autocomplete="email"` and `autocomplete="tel"`. |
| 6 | Nonconformity | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | page | `fares.html:42`, `fares.html:63-64`, `:71-72`, `:79-80`, `:87-88`, `css/site.css:122` | Peak fares are marked only by red text. Each cell shows two prices ("$2.50 $3.25") and colour alone says which is the peak price. Also breaks 1.3.1, since the difference isn't in the code either. | `<span class="peak">` with `.fare-table .peak { color: #c0392b; }`. The legend says "Peak fares are shown in red." | Label the value in text (e.g. "$2.50, peak $3.25"), or make separate Off-peak and Peak columns. Rewrite the legend so it doesn't refer to colour. |
| 7 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | page | `css/site.css:180`; `feedback.html:35`, `:39`, `:52` | The floating field labels on the feedback form have too little contrast. | `#a0a0a0` on `#ffffff` is **2.6:1**, below the 4.5:1 minimum. The text is 16px, shrinking to 12px (`.75rem`) once it floats. | Use at least `#595959` (7:1) or `var(--ink)`. |
| 8 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | page | `css/site.css:136`; `alerts.html:53`, `alerts.html:58` | The alert articles are plain text but can't shrink below 880px, so at 320 CSS px they force horizontal scrolling. | `.alert-detail { min-width: 880px; }`. The data-table exception doesn't apply to prose. | Remove `min-width`, or use `max-width: 100%`. |
| 9 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (Level AA) | component | `components/ToggleSwitch.vue:34`, `:38` | In the off state the switch is almost invisible: its track and thumb edges don't contrast with the page or with each other. | Track border `#dddddd` on white is **1.4:1**. Track fill `#f1f1f1` on white is 1.1:1. The thumb's `#e2e2e2` ring is about 1.3:1. The minimum is 3:1. | Give the off-state track a `#6b7785` border or fill (4.6:1) and the thumb a 1px `#6b7785` outline, as `.bw-switch` in `site.css:139` already does. |
| 10 | Nonconformity | WCAG-1.4.13 | WCAG 2.2 SC 1.4.13 (Level AA) | component | `components/ZoneInfoTooltip.vue:8-11`, `:15`, `:43` | The zone tooltip fails two of the three requirements. It can't be **hovered**: it closes on `mouseleave` from the trigger, and there is a 10px gap before the tip. It can't be **dismissed**: Escape isn't handled. | `@mouseleave="open = false"` is on the button only. `top: calc(100% + 10px)`. There is no keydown handler. | Move the `mouseenter`/`mouseleave` handlers to the `.zone-info` wrapper and remove the gap (or add a padding bridge). Add `@keydown.esc="open = false"` that also works while the pointer is hovering. |
| 11 | Deviation | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | page | `js/feedback.js:9-10`, `css/site.css:187`; `feedback.html:40`, `:53` | When a field fails validation, the only visual signal is a red border, going from 1px grey to 2px red. The error message elements stay `hidden` and are never filled in. The main failure is 3.3.1, which is out of scope. | `check()` toggles `.is-invalid` and `aria-invalid` only. `#fb-email-error` and `#fb-message-error` are never written to or unhidden. | Fill in and unhide the `.field-error` text (e.g. "Enter an email address like name@example.com"), and add an icon or prefix such as "Error:". |
| 12 | Deviation | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | page | `login.html:48-56`, `css/site.css:150`, `:152` | At 320 CSS px, the 6-digit code row needs 304px but only 288px is available. The row can't wrap, and a fieldset won't shrink below its content, so the page probably scrolls sideways. Needs confirming in a browser. | 6 × 44px + 5 × 8px gap = 304px. `.otp { display:flex }` with no wrap, and fieldset `min-inline-size` defaults to `min-content`. | Add `flex-wrap: wrap` and `min-inline-size: 0` on `.otp`, or use `width: clamp(2.25rem, 12vw, 44px)` on `.otp-digit`. Better still, use a single `autocomplete="one-time-code"` input. |
| 13 | Advisory | WCAG-BP-logotype-contrast | WCAG 2.2 SC 1.4.3 (Level AA): logotype exception | stylesheet | `css/site.css:48` (wordmark on every page, e.g. `index.html:14`) | The "Brightwater Transit" wordmark is **1.85:1** on white. As part of the logo it is exempt from 1.4.3, but it is also the only visible text of the home link. | `#9cc3e6` on `#ffffff`. | Use `var(--brand)` (6.7:1) or `var(--brand-dark)` for the wordmark. |

## SC coverage (Principle 1, Level A and AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | #1, #2, #3. Icon-font glyphs are all `aria-hidden` next to visible text, the logo SVG is `aria-hidden` with the wordmark next to it, and the swap, banner and zoom buttons have `aria-label`. Those pass. |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | N/A | No `<audio>`, `<video>` or embedded media. |
| 1.2.2 Captions (Prerecorded) | A | N/A | No media. |
| 1.2.3 Audio Description or Media Alternative | A | N/A | No media. |
| 1.2.4 Captions (Live) | AA | N/A | No media. |
| 1.2.5 Audio Description (Prerecorded) | AA | N/A | No media. |
| 1.3.1 Info and Relationships | A | **Fail** | #4, and #6 (peak fares). Labels, fieldsets and legends, headings, lists and the caption are otherwise correct. |
| 1.3.2 Meaningful Sequence | A | Pass | The source order matches the visual order. See review note C. |
| 1.3.3 Sensory Characteristics | A | Pass | No instructions rely on shape, position or sound. The colour-based legend is covered under 1.4.1. |
| 1.3.4 Orientation | AA | Pass | No `orientation` media queries or rotation locks. |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #5. Login, feedback, alerts email and claim-3 use valid `autocomplete` values. |
| 1.4.1 Use of Color | A | **Fail** | #6, and #11 (deviation). |
| 1.4.2 Audio Control | A | N/A | No audio. |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #7. Other pairs checked all pass: brand `#0b5cad` on white 6.7:1, white on `.btn` 6.7:1, footer `#cfe3f7` on `#12324f` 10:1, `.peak` `#c0392b` 5.4:1, `.step-indicator` `#6b7785` 4.56:1. The disabled button is exempt. |
| 1.4.4 Resize Text | AA | Not evaluated | Nothing blocks zoom: the viewport meta allows scaling and `.dock-footer` goes static at ≤30rem height. Needs a browser check at 200%. See review note D. |
| 1.4.5 Images of Text | AA | Pass | No raster images. Map labels are real SVG `<text>`. |
| 1.4.10 Reflow | AA | **Fail** | #8, and #12 (deviation). The fare table's `min-width: 760px` in a scrolling region is exempt as a data table, and so is the map. |
| 1.4.11 Non-text Contrast | AA | **Fail** | #9 (component). On the pages, field borders `#6b7785` are 4.56:1, `.bw-switch` is 4.56:1, and map lines and stop rings are ≥5.4:1, all passing. Focus indicators fall under 2.4.7 and are out of scope. |
| 1.4.12 Text Spacing | AA | Not evaluated | Nothing clearly blocks it (no fixed-height text boxes with `overflow:hidden`). Needs a bookmarklet test. See review note E. |
| 1.4.13 Content on Hover or Focus | AA | **Fail** | #10 (component). The 11 pages have no hover or focus pop-ups and no `title` tooltips. |

## Review notes

- **A. Icon font file missing.** `site.css:4` loads `../fonts/bwicons.woff2`, but there is no `fonts/` directory in this folder, and `font-display: block` means glyphs show nothing if the font fails. The decorative icons still have text next to them. However, the swap button (`planner.html:39`) would then look like an empty box, even though screen readers still get its `aria-label`. Check that the font is deployed. If it's missing, the button fails to show what it does (relevant to 1.1.1 and 1.4.11).
- **B. Map lines told apart by colour and position.** Blue (`#0b5cad`) and red (`#b3261e`) lines are labelled by nearby coloured text (`map.html:41-42`). They follow different paths, so colour isn't the only cue, and I didn't grade it under 1.4.1. The text version in fix #3 would remove the dependency entirely.
- **C. 1.3.2: floating labels come after their inputs** in the source (`feedback.html:34-35`, `:38-39`, `:51-52`) but appear visually above them. Each label is linked to its field with `for`, so the field name is still announced. In screen-reader browse mode, though, the label is read after the field. Not graded as a failure.
- **D. 1.4.4:** `.mini-btn` (`site.css:133-134`, 16px box with 12px text) and `.zoom-btn` (`site.css:161-162`, 20px box) use fixed px sizes. With full-page zoom they scale correctly. With text-only zoom (Firefox "Zoom text only") the glyphs will spill out of the boxes. Check both modes.
- **E. 1.4.12:** the absolutely positioned floating labels (`site.css:179-186`) may wrap at narrow widths once 0.12em letter spacing and 0.16em word spacing are applied, and then overlap the typed text. Test with the text-spacing bookmarklet at 320px.
- **F.** `.step-indicator` (`site.css:155`, `#6b7785`) passes at **4.56:1**, only just above 4.5:1. Any change to the page background will make it fail.
- **G. Components aren't built or used on any page.** Findings #9 and #10 apply wherever `ToggleSwitch` and `ZoneInfoTooltip` ship. `SavedTrips.vue` and `StopSearch.vue` have no Principle 1 failures: the grip glyph is `aria-hidden`, and the result count uses `role="status"`.
- **H. Issues outside Principle 1** (seen but not graded):
  - `fares.html:2` has no `lang` (3.1.1).
  - `alerts.html:41` / `alerts.js:26-28` never update `aria-checked` (4.1.2).
  - `alerts.html:68` has a `<span>` close control (2.1.1, 4.1.2), and `alerts.js:74-78` blocks Escape.
  - `alerts.html:32-34` (16px) and `map.html:34-35` (20px) buttons are too small (2.5.8).
  - `site.css:52` removes the nav focus outline (2.4.7).
  - `login.html:41-42` uses positive `tabindex` (2.4.3).
  - `login.js:12,22` blocks paste (3.3.8).
  - `claim-2.html` has no Help link in the header (3.2.6).
  - claim-1 and claim-3 ask for email and phone again (3.3.7).
  - `fares.js:7-9` navigates as soon as the select changes (3.2.2).
  - `site.css:84` carousel and `alerts.js:16` banner rotate automatically with no pause (2.2.2).
  - Map stops can't be reached by keyboard (2.1.1).
  - `SavedTrips.vue` reordering is drag-only (2.5.7).
  - `alerts.html:51` refresh result isn't announced (4.1.3).
  - Feedback errors have no text (3.3.1).

## Manual checks required

- 1.4.4: zoom each page to 200% (full page and text-only). Confirm nothing is clipped or overlapping, especially `.mini-btn`, `.zoom-btn` and the feedback `.dock-footer`.
- 1.4.12: apply the text-spacing bookmarklet on all 11 pages. Check the floating labels, `.live-banner` and `.saved` rows.
- 1.4.10: at 320 CSS px, confirm #12 (OTP row) and check the whole page width on every page.
- Re-check 1.4.3 and 1.4.11 in a rendered page for hover, focus and error states, and anything that depends on the missing icon font.
- Screen reader smoke test (e.g. NVDA with Firefox, VoiceOver with Safari): the fare table header announcements, the planner result icons and the map.

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs` and `wcag_audit.py` were not run because no shell was available. There is no axe-core data.
- Principles 2 to 4 were excluded as requested (35 of the 55 AA criteria). The observations in note H are not a complete review of them.
- 1.2.1 to 1.2.5 and 1.4.2 are N/A because there is no media or audio.

## Assumptions

- WCAG 2.2 (W3C Recommendation, 12 Dec 2024), Level AA, Principle 1 only.
- I assumed the pages render with `css/site.css` alone, and that the Vue components' scoped styles would apply as written.
- No assistive technology or browser was used. Every status is based on reading the source.
- This site **does not conform** to WCAG 2.2 AA. It fails 1.1.1, 1.3.1, 1.3.5, 1.4.1, 1.4.3, 1.4.10, 1.4.11 and 1.4.13. 1.4.4 and 1.4.12, and all criteria outside Principle 1, have not been evaluated.

## Reproduction

The contrast ratios use WCAG relative luminance (sRGB linearisation), (L1 + 0.05) / (L2 + 0.05):

| Colours | Ratio |
|---|---|
| `#a0a0a0` / `#fff` | 2.61 |
| `#dddddd` / `#fff` | 1.36 |
| `#9cc3e6` / `#fff` | 1.85 |
| `#6b7785` / `#fff` | 4.56 |
| `#0b5cad` / `#fff` | 6.67 |
| `#c0392b` / `#fff` | 5.44 |
| `#cfe3f7` / `#12324f` | 10.0 |

The reflow widths assume a 320px viewport minus `main`'s 2 × 16px padding, which leaves 288px.

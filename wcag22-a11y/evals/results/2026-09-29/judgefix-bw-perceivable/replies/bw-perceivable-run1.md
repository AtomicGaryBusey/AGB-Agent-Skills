# WCAG 2.2 Level AA audit: Brightwater Transit static front end, Principle 1 (Perceivable)

**Scope:** 11 HTML pages (index, planner, fares, alerts, map, claim-1/2/3, login, feedback, help), `css/site.css`, `js/*.js` (7 files), `img/*.svg` (2), `components/*.vue` (4, source only and not built). The process in scope is the lost-item claim (claim-1 → claim-2 → claim-3). The criteria in scope are the 20 Level A and AA criteria under Principle 1 (1.1.1, 1.2.1–1.2.5, 1.3.1–1.3.5, 1.4.1–1.4.5, 1.4.10–1.4.13). Tools: none. The assistive-technology and browser matrix is none.

**Summary:** 11 nonconformities, 2 deviations, 1 advisory, 4 review notes. Of the 20 criteria: 8 fail, 4 pass, 6 N/A, 2 not evaluated.

**Evidence:** This is a static review only. I read every file listed above line by line. Without a shell, neither `wcag_scan` nor `wcag_page` could run, and no pages were rendered. I calculated contrast ratios by hand with the WCAG relative-luminance formula.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `planner.html:36`, `css/site.css:103-106` | The "locate me" button has no text alternative. Its only content is a CSS background image. Also breaks 4.1.2. | `<button … id="locate-me"></button>` is empty, with no `aria-label` or `title`. The icon comes from `background: url("../img/locate.svg")`. Screen readers announce "button" with no name. | Add `aria-label="Use my current location"`, or put visually hidden text inside the button. |
| 2 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `planner.html:61`, `planner.html:70` | The step-free icon is the only indication that trips 1 and 3 are step-free, and it has no text alternative. | The `<svg class="ico">` has no `role="img"`, no `aria-label`, no `<title>`, and is not hidden. The trip text does not mention step-free access; only trip 2 mentions stairs, in its text. | Use `<svg role="img" aria-label="Step-free route" …>`, or add visible text such as "Step-free" next to the icon. |
| 3 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `map.html:37-50` | The route map is a complex image. Its only text alternative is "Harbour Line and Route 14". Nothing in text says which stops are on which line, what order they are in, or where the lines interchange. Also breaks 1.3.1. | `aria-labelledby="map-title"` points to a short title. The stop `<text>` nodes are read as a disconnected list. Line membership exists only in the drawn geometry and in `map.js:6-12`, which shows only on mouse click. | Add a text equivalent next to the map: a list for each line with its stops in order, marking interchanges (Market Square) and temporary or closed stops. Reference it with `aria-describedby`. |
| 4 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `fares.html:46-60`, 62, 70, 78, 86 | The fare table has no programmatic headers. Column and row headers are `<td class="th">`, styled bold only, so screen-reader users hear no header context for any price. The table also has two levels of column headers. | There is no `<th>`, `<thead>` or `scope` anywhere. `site.css:121` gives `td.th` a bold weight and a tinted background. | Put rows 1–2 in `<thead>` as `<th scope="colgroup" colspan="2">` and `<th scope="col">`. Make the rider-type cells `<th scope="row">`. Because the headers are two levels deep, add `id`/`headers` if testing shows `scope` is not enough. |
| 5 | Nonconformity | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (Level AA) | page | `claim-1.html:36`, `:40`, `:44` | The claim form's fields for the user's own name, email and phone do not identify their input purpose. | `c-name` has no `autocomplete`. `c-email` has `autocomplete="off"`. `c-phone` has no `autocomplete`. The same fields are done correctly in `claim-3.html:36,40`. | Add `autocomplete="name"`, `autocomplete="email"` and `autocomplete="tel"`. |
| 6 | Nonconformity | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | page | `fares.html:42`, `:63-64`, `:71-72`, `:79-80`, `:87-88`, `css/site.css:122` | Peak fares are told apart from off-peak fares only by red text. The page's own instructions say "Peak fares are shown in red." | `.peak { color:#c0392b }` is the only difference, with no label, icon or pattern. Red against the neighbouring #1b2a3a text is **2.68:1**, below the 3:1 needed for the colour-plus-contrast technique. | Show the fare type in text, for example "$2.50 off-peak / $3.25 peak", or use separate Off-peak and Peak columns with `<th>`. Change the instructions so they do not refer to colour. |
| 7 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `css/site.css:180`; used at `feedback.html:35`, `:39`, `:52` | The floating field labels have too little contrast. When a label moves up (`site.css:186`) it also shrinks to 0.75rem (12px). | `#a0a0a0` on `#ffffff` = **2.62:1**; normal text needs 4.5:1. | Use `color: var(--line)` (#6b7785, 4.56:1) or darker, for example `var(--ink)`. |
| 8 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | stylesheet | `css/site.css:136`; used at `alerts.html:53`, `:58` | The alert articles force horizontal scrolling at 320 CSS px. This is prose, not two-dimensional content, so the exception does not apply. | `.alert-detail { min-width: 880px }` is wider than the 288px content box (320px viewport minus 2×16px padding). | Remove `min-width`, or use `max-width: 100%`. |
| 9 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (Level AA) | stylesheet | `css/site.css:31` with `:57-58`; footers on every page, for example `index.html:76-78`, `feedback.html:70` | The focus indicator on footer links has too little contrast against the dark footer background. | The `outline: 3px solid #0b5cad` with a 2px offset sits on footer background `#12324f`: **1.97:1**, below the 3:1 required. | Add `.site-footer :focus-visible { outline-color: #fff; }`, which gives about 13:1. |
| 10 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (Level AA) | component | `components/ToggleSwitch.vue:32-38` | In the off state the switch is almost invisible, so users cannot find the control or tell its state. | The track is `#f1f1f1` with a `#dddddd` border on a white page: **1.36:1**. The thumb is white with a `#e2e2e2` ring. | Give the track an off-state border of `#6b7785` (4.56:1) or darker, and outline the thumb in the same colour. |
| 11 | Nonconformity | WCAG-1.4.13 | WCAG 2.2 SC 1.4.13 (Level AA) | component | `components/ZoneInfoTooltip.vue:8-11`, `:15`, `:43` | The tooltip cannot be dismissed without moving the pointer or focus, and the pointer cannot be moved onto it. | There is no Escape handler. The `mouseleave` on the button closes the tip, which sits outside the button with a 10px gap (`top: calc(100% + 10px)`), so moving the pointer to the tip closes it. | Close on `keydown.esc`. Put the `mouseenter`/`mouseleave` handlers on the wrapping `.zone-info` span and remove the gap, or bridge it with padding. |
| 12 | Deviation | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | stylesheet | `css/site.css:150`, `:152`; `login.html:48-56` | The one-time-code row probably overflows at 320 CSS px. | 6 inputs × 44px + 5 gaps × 8px = 304px, against 288px available. The flex row has no `flex-wrap`, and the inputs have a fixed width, which sets their minimum. Needs confirming in a rendered page. | Add `flex-wrap: wrap`, or use `width: min(44px, 13vw)`. A single `autocomplete="one-time-code"` input is simpler and also helps with 3.3.8. |
| 13 | Deviation | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | page | `css/site.css:187`, `js/feedback.js:9-10`, `feedback.html:40`, `:53` | An invalid field is shown mainly by a red border. The border also gets 1px thicker, which is a weak non-colour cue. The error `<p>` elements stay `hidden` and are never filled in. Also relevant to 3.3.1. | `.is-invalid { border: 2px solid var(--danger) }` replaces a 1px grey border. Nothing in `feedback.js` writes into `#fb-email-error` or `#fb-message-error`. | Fill in and unhide the error text, for example "Enter an email address like name@example.com". Optionally add an error icon. |
| 14 | Advisory | WCAG-BP-icon-font | Best practice (relates to 1.1.1 / 1.3.3) | stylesheet | `css/site.css:2-6`, `:33-40`; `planner.html:39` | The icon font file `fonts/bwicons.woff2` is not in the repository. With `font-display: block`, the icons render blank, so the Swap button has no visible label. Icon fonts using private-use codepoints also break when users apply their own fonts. | The glob shows no `fonts/` directory. The button's accessible name is fine (`aria-label="Swap From and To"`). | Replace the icon font with inline SVG (`aria-hidden` next to text). Give the Swap button visible text or an SVG icon. |
| 15 | Review note | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `css/site.css:48` | The "Brightwater Transit" wordmark is `#9cc3e6` on white, **1.85:1**. This is exempt as logotype text. | Brand-name exception in SC 1.4.3. | No change required. Darkening it would help low-vision users, because it is the only visible text of the home link. |
| 16 | Review note | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `css/site.css:68`; `claim-3.html:46` | The disabled Submit button is `#9aa3ad` on `#e4e7ea` (about 2.2:1). This is exempt because the component is inactive. | Inactive-component exception. | None needed for 1.4.3. Consider keeping the button enabled and validating on submit (3.3.1). |
| 17 | Review note | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | page | `map.html:39-42`, `css/site.css:165-167` | Both lines are drawn at the same 6px width and differ only in colour (blue and red). Text labels are placed near each line, but where the lines cross at Market Square, following a line may depend on colour. | This is a judgement call and needs a visual check. | Add a dash pattern to one line (for example `stroke-dasharray` on Route 14) and put the labels along the lines. |
| 18 | Review note | WCAG-1.4.4 | WCAG 2.2 SC 1.4.4 (Level AA) | stylesheet | `css/site.css:189-191`; `feedback.html:29`, `:64` | The fixed footer (`min-height: 12rem`) covers about 37% of the viewport at 200% zoom on a 1280×1024 screen (32rem tall, above the 30rem breakpoint). If its content wraps past 12rem, it covers content that the 12rem bottom padding does not compensate for. Also relevant to 2.4.11. | Static reasoning only, not rendered. | Check at 200% zoom. Consider making the footer static at every size. |

## SC coverage

| SC | Level | Status | Notes |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | #1, #2, #3 |
| 1.2.1–1.2.5 | A/AA | N/A | No audio, video or media anywhere |
| 1.3.1 Info and Relationships | A | **Fail** | #4 (see also #3) |
| 1.3.2 Meaningful Sequence | A | Pass | DOM order matches visual order; no CSS `order` or reversed flex; floating labels keep their reading order |
| 1.3.3 Sensory Characteristics | A | Pass | The "shown in red" instruction is a colour matter and is recorded under 1.4.1 (#6) |
| 1.3.4 Orientation | AA | Pass | No orientation locks in CSS or JS |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #5 |
| 1.4.1 Use of Color | A | **Fail** | #6 (#13 deviation, #17 review) |
| 1.4.2 Audio Control | A | N/A | No audio |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #7. Checked and passing: `--line` #6b7785 on white 4.56:1 (`.step-indicator`), brand #0b5cad 6.67:1, danger #b3261e 6.54:1, peak red #c0392b 5.44:1 against white |
| 1.4.4 Resize Text | AA | Not evaluated | Needs rendering. No blockers in source apart from #18 |
| 1.4.5 Images of Text | AA | Pass | The only images are two SVGs with no text |
| 1.4.10 Reflow | AA | **Fail** | #8 (#12 deviation). The fares table's horizontal scroll is exempt as a data table |
| 1.4.11 Non-text Contrast | AA | **Fail** | #9, #10. Input, button and switch borders use #6b7785 (4.56:1) and pass |
| 1.4.12 Text Spacing | AA | Not evaluated | No fixed-height text boxes with `overflow: hidden` found in source. Needs a spacing bookmarklet test |
| 1.4.13 Content on Hover or Focus | AA | **Fail** | #11 |

## Review notes
- The Vue components are source only and not built. Findings #10 and #11 apply wherever these components ship.
- Correctly handled, so not findings: decorative icons (`aria-hidden` on `.bwi`, the logo SVG and the SavedTrips grip), zoom and banner buttons with `aria-label`, the alerts switch label, the claim-2 hint linked with `aria-describedby`, the fieldsets and legends on feedback and login, and the fares region with its caption.

## Manual checks required
- 1.4.4: check every page at 200% browser zoom and with text-only zoom, including the feedback fixed footer (#18).
- 1.4.10: confirm #12 at a 320×256 viewport and recheck all pages once #8 is fixed.
- 1.4.12: apply the text-spacing override on all pages. Watch the promo carousel (`overflow: hidden`), the 16px `.mini-btn` controls and the floating labels.
- Screen-reader smoke test (for example NVDA with Firefox, VoiceOver with Safari) to confirm #1–#4 and how the map SVG is exposed.

## Not run / not applicable
- `wcag_scan.py`, `wcag_page.mjs` and axe-core were not run because no shell was available. No rendered or screenshot evidence exists.
- **Outside Principle 1, seen but not audited** (listed for follow-up only):
  - `fares.html:2` has no `lang` (3.1.1).
  - `site.css:52` removes the nav focus outline (2.4.7).
  - `alerts.js:74-86` traps focus and blocks Escape, and the close control at `alerts.html:68` is a non-focusable `<span>` (2.1.2 non-interference, 2.1.1, 4.1.2).
  - `alerts.js:26-28` never updates `aria-checked` (4.1.2).
  - `site.css:84` runs the carousel animation with no pause control (2.2.2 non-interference).
  - `map.js:15-20` makes the stops mouse-only (2.1.1).
  - `login.js:8-12,22` blocks paste (3.3.8).
  - `login.html:41-42` uses positive `tabindex` (2.4.3).
  - `claim-2.html:11-27` has no Help link (3.2.6).
  - `claim-3.html:35-40` asks again for the email and phone already given in step 1 (3.3.7).
  - `fares.js:7-9` navigates when the select changes (3.2.2).
  - `alerts.html:51` has no live region for status messages (4.1.3).
  - `.mini-btn` at 16px and `.zoom-btn` at 20px are below the minimum target size (2.5.8).

## Assumptions
- This is WCAG 2.2 (W3C Recommendation, 12 December 2024), Level AA, limited to success criteria 1.x.
- No assistive technology was used. Accessible names and roles were worked out from the markup.
- Contrast ratios were calculated from the declared CSS colours and assume the default white `--surface`.
- **Conformance:** the site does **not conform** to WCAG 2.2 Level AA for Principle 1. The failing criteria are 1.1.1, 1.3.1, 1.3.5, 1.4.1, 1.4.3, 1.4.10, 1.4.11 and 1.4.13.

## Reproduction
Open each `file:line` cited above. To check contrast, enter the hex pairs from the Evidence column into any WCAG 2.x contrast calculator. To check reflow, load `alerts.html` and `login.html` (after submitting the form, so the code step shows) at 320 CSS px wide and look for a horizontal scrollbar.

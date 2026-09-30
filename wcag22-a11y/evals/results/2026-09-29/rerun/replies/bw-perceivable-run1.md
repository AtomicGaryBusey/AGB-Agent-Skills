# WCAG 2.2 Level AA audit: Brightwater Transit static front end (Principle 1 only)

**Scope:** 11 HTML pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, `js/*.js`, `img/*.svg` and the 4 Vue source components. The only process covered is the lost-item claim (claim-1 → claim-2 → claim-3). Criteria covered: the 20 Level A and AA success criteria under Principle 1 (1.1.1 to 1.4.13). Method: I read the source by hand. No tools ran, nothing was rendered, and no screen reader or browser was used.

**Summary:** 10 definite failures, 3 likely failures, 2 minor recommendations, 7 review notes. Of the 20 criteria: **8 fail, 0 pass, 7 do not apply (N/A), 5 not evaluated**.

The site **does not conform** to WCAG 2.2 Level AA. It fails SC 1.1.1, 1.3.1, 1.3.5, 1.4.1, 1.4.3, 1.4.10, 1.4.11 and 1.4.13. Principle 2–4 criteria were not assessed, so this is not a full conformance result either way.

**Severity labels used below:**
- **Failure**: the source proves the criterion fails.
- **Likely failure**: probably fails, but needs a rendered check to confirm.
- **Recommendation**: good practice that no Level A or AA criterion requires.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Failure | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page | `planner.html:36`, `css/site.css:103-105` | The "locate me" button has no text alternative. Its only content is a CSS background image (`img/locate.svg`), so screen readers announce just "button". This also breaks 4.1.2 (outside this audit). | `<button type="button" class="btn-locate" id="locate-me"></button>`: no content, no `aria-label`. The icon is a `background` image. | Add `aria-label="Use my current location"`, or put visually hidden text inside the button. |
| 2 | Failure | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page | `planner.html:61`, `planner.html:70` | The step-free icon has no text alternative, but it carries meaning: only step-free trips show it, and nothing else on the page says which trips are step-free. The information is invisible to screen reader users (also affects 1.3.1). | `<svg class="ico" width="20" height="20"><use href="img/sprite.svg#step-free"></use></svg>`: no `role="img"`, no `aria-label` or `<title>`. | Add `role="img" aria-label="Step-free route"`, or add visible text "Step-free" next to the icon. |
| 3 | Failure | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (A) | page | `fares.html:47-60`, `fares.html:62,70,78,86`, `css/site.css:121` | The fare table's column and row headers are ordinary `<td class="th">` cells styled to look like headers. Screen readers can't link prices to "Zone 1", "Day pass" or "Adult". | There are no `<th>` or `<thead>` elements; the header look comes only from `.fare-table td.th`. The first row uses `colspan="2"` group headers. | Put the two header rows in `<thead>` as `<th>`: the group row with `scope="colgroup"` and the zone row with `scope="col"`. Make each rider-type cell `<th scope="row">`. |
| 4 | Failure | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (AA) | page | `claim-1.html:36`, `claim-1.html:40`, `claim-1.html:44` | The claim form's name, email and phone fields ask for the user's own contact details ("We will use these details to contact you"), but their purpose isn't marked up. Email is explicitly turned off. | Name: no `autocomplete`. Email: `autocomplete="off"`. Phone (`type="tel"`): no `autocomplete`. | Use `autocomplete="name"`, `autocomplete="email"` and `autocomplete="tel"`. (Step 3 already does this at `claim-3.html:36,40`.) |
| 5 | Failure | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (A) | page | `fares.html:42`, `fares.html:63-88` (`span.peak`), `css/site.css:122` | Colour is the only way to tell peak fares from off-peak fares. The page even says "Peak fares are shown in red." | Peak red `#c0392b` against the off-peak text colour `#1b2a3a` is 2.68:1 (below 3:1). There's no text, symbol or style difference, and the markup doesn't say "peak" either. | Add a text label, e.g. `Off-peak $2.50, peak $3.25`, or a visible "Peak" prefix/marker (with the same text in markup). Change the legend so it doesn't rely on colour. |
| 6 | Failure | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (AA) | stylesheet | `css/site.css:180`; used at `feedback.html:35`, `:39`, `:52` | The feedback form's floating labels are too pale. They stay the same colour when they shrink to 0.75rem (12 px) above the typed text. | `#a0a0a0` on `#ffffff` is 2.62:1 (needs 4.5:1). The labels are normal-size text, and label text gets no contrast exemption. | Use `color: var(--ink)` or at least `#767676` (4.54:1). A static label above the field is better. |
| 7 | Failure | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (AA) | stylesheet | `css/site.css:136`; `alerts.html:53`, `alerts.html:58` | The alert articles are forced to be at least 880 px wide, so at 320 CSS px the whole alerts page scrolls sideways. This is ordinary text, not content that needs a two-dimensional layout (the reflow exception doesn't apply). | `.alert-detail { min-width: 880px; }`. There's no scrolling wrapper and no media query to override it. | Remove `min-width` (or use `max-width`). |
| 8 | Failure | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (AA) | stylesheet | `css/site.css:31`, `css/site.css:57-58`; footer links on all 11 pages (e.g. `index.html:76-78`), `feedback.html:70` | In the dark footer, the keyboard focus ring is too faint to see against the background. | Outline `#0b5cad` against footer background `#12324f` is 2.12:1 (needs 3:1). The same rule gives 6.2:1 on white, so the problem is only in the footer. | Add `.site-footer :focus-visible { outline-color: #fff; }` (or `#cfe3f7`, which is about 11:1). |
| 9 | Failure | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (AA) | component | `components/ToggleSwitch.vue:34`, `:38` | When the switch is off, its track and thumb are almost invisible on white, so neither the control nor its state can be made out. This is built into the component: the colours are fixed values with no prop or CSS variable. | Track `#f1f1f1` is 1.13:1 against white. Its border `#dddddd` is 1.36:1. The thumb (`#fff` with a `#e2e2e2` ring) is about 1.3:1. The on state (`#0b5cad`) is fine. | Give the off state a border and track of at least 3:1, e.g. `border: 1px solid #6b7785` (4.56:1). Give the thumb a `#6b7785` ring, or draw it filled in a dark colour. |
| 10 | Failure | WCAG-1.4.13 | WCAG 2.2 SC 1.4.13 (AA) | component | `components/ZoneInfoTooltip.vue:8-11`, `:15`, `:43` | The zone tooltip fails two parts of the criterion. You can't dismiss it without moving the pointer or focus: there's no Escape handler. You can't move the pointer onto it either: `mouseleave` on the trigger hides it, and it sits 10 px below the trigger. Also built into the component (the handlers are hard-coded). | The only handlers are `@mouseenter`, `@mouseleave`, `@focus` and `@blur`, all on the button. The tip is `v-show="open"`, `top: calc(100% + 10px)`. | Put the hover handlers on the `.zone-info` wrapper, not the button, and close the 10 px gap (or add an invisible bridge). Add a `keydown` Escape handler that sets `open = false` without moving focus. |
| 11 | Likely failure | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (AA) | page | `login.html:48-56`, `css/site.css:150`, `css/site.css:152` | At 320 px the one-time-code row is probably too wide for the space available, so the page scrolls sideways. | Six fixed 44 px inputs plus five 8 px gaps = 304 px. `main` has 16 px padding each side, leaving 288 px. The flex row doesn't wrap, and `<fieldset>` won't shrink below its content width by default. Not confirmed in a browser. | Add `flex-wrap: wrap` and `min-inline-size: 0` on `.otp`, or use `width: min(44px, 13vw)`. A single `autocomplete="one-time-code"` input is better. Confirm at 320×256. |
| 12 | Likely failure | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (AA) | page | `map.html:43` (possibly `map.html:48`), `map.html:40` | The red Route 14 line runs through the "Market Square" stop label, so part of the dark text sits on red. | The line from (180,220) to (300,320) crosses the label, whose baseline is at (196,246). Text `#1b2a3a` on stroke `#b3261e` is 2.23:1. "Anchor Lane" at `:48` may touch the line too. Not rendered. | Move the labels off the line paths, or add a white halo (`paint-order: stroke; stroke: #fff; stroke-width: 4px`) to the stop `<text>` elements. |
| 13 | Likely failure | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page | `map.html:37-50`, `js/map.js:15-19` | Which stops are on which line is shown only by the drawn lines. The SVG's text alternative is just "Harbour Line and Route 14". The stop details panel is the only other source, and it only opens on mouse click (a Principle 2 issue). Also affects 1.3.1. | `<title id="map-title">` is the only description. The stop names are SVG `<text>`, but line membership isn't available as text anywhere. | Next to the map, add a text list of the stops on each line (and the stop details), or link to one with `aria-describedby`. |
| 14 | Recommendation | WCAG-BP-logotype-contrast | WCAG 2.2 SC 1.4.3 (AA) (exempt) | stylesheet | `css/site.css:48` | The "Brightwater Transit" wordmark is very pale. Logotypes are exempt from 1.4.3, so this isn't a failure, but it's hard to read. | `#9cc3e6` on white is 1.85:1. | Consider `var(--brand)` for the wordmark. |
| 15 | Recommendation | WCAG-BP-icon-font | none | stylesheet | `css/site.css:2-6`, `css/site.css:34` | The icon font file `fonts/bwicons.woff2` doesn't exist in the project. With `font-display: block` the icons won't render. All uses are `aria-hidden` next to visible text, so no criterion fails. `speak: never` is not a standard property. | There's no `fonts/` directory. | Add the font or switch to inline SVG with `aria-hidden="true"`. Remove `speak`. |

## SC coverage (Principle 1, Level A and AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | #1, #2 (#13 likely) |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | N/A | There's no `<audio>`, `<video>`, `<iframe>` or embedded media on any page or component |
| 1.2.2 Captions (Prerecorded) | A | N/A | No media |
| 1.2.3 Audio Description or Media Alternative | A | N/A | No media |
| 1.2.4 Captions (Live) | AA | N/A | No media |
| 1.2.5 Audio Description (Prerecorded) | AA | N/A | No media |
| 1.3.1 Info and Relationships | A | **Fail** | #3 |
| 1.3.2 Meaningful Sequence | A | Not evaluated | Static read found nothing: no CSS `order` or reordering; the carousel and floating labels keep a logical DOM order. Needs a rendered and screen reader check |
| 1.3.3 Sensory Characteristics | A | Not evaluated | No shape- or position-only instructions found ("Select a stop on the map" also names the stop). The colour-only instruction at `fares.html:42` is covered under 1.4.1 |
| 1.3.4 Orientation | AA | Not evaluated | No `orientation` media queries or JS locks in source. Needs a device check |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #4 |
| 1.4.1 Use of Color | A | **Fail** | #5 |
| 1.4.2 Audio Control | A | N/A | No audio |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #6 (#12 likely). Other pairs I calculated pass: body/nav/link/button colours from 4.56:1 up (e.g. `--brand` on white 6.2:1, `.step-indicator` `#6b7785` 4.56:1, `.peak` 5.44:1, `.field-error` 6.5:1, banner and footer text) |
| 1.4.4 Resize Text | AA | Not evaluated | Viewport meta allows zoom on all pages. `.mini-btn` and `.zoom-btn` use fixed px boxes. Needs a 200% zoom check |
| 1.4.5 Images of Text | AA | N/A | No images of text: the logo symbol, `locate.svg` and the icons have no text in them |
| 1.4.10 Reflow | AA | **Fail** | #7 (#11 likely). The fare table's scroll container (`site.css:118-119`) is allowed as data-table content |
| 1.4.11 Non-text Contrast | AA | **Fail** | #8, #9 |
| 1.4.12 Text Spacing | AA | Not evaluated | No `!important`. Candidates to test: `.mini-btn` (fixed `height`/`line-height` of 16px, `site.css:133-134`) and the absolutely positioned floating labels (`site.css:179-186`) |
| 1.4.13 Content on Hover or Focus | AA | **Fail** | #10 |

## Review notes

- **1.4.1, feedback form errors** (`js/feedback.js:9-10`, `css/site.css:187`): the invalid state changes the border from 1 px grey to 2 px red. The thickness change is a non-colour cue, so I didn't record a 1.4.1 failure. The real defect is that `#fb-email-error` and `#fb-message-error` are never filled in or shown (3.3.1, outside this audit).
- **1.4.1, route map lines**: blue and red lines are each named by a text label next to them (`map.html:41-42`), so line identity doesn't rely on colour alone. Line membership as text is #13.
- **1.4.1, current nav item**: `aria-current` links get bold text and a 3 px underline border (`site.css:53`), not just a colour change. Passes.
- **1.4.3 exemption**: the disabled "Submit claim" button (`claim-3.html:46`, `site.css:68`, 1.9:1) is an inactive control and exempt.
- **1.4.10, `ZoneInfoTooltip.vue:43`**: the fixed `width: 18rem` (288 px) positioned from the trigger may overflow at 320 px. Whether it does depends on where the component is placed; check once it's built.
- **1.4.12**: floating labels (`site.css:179-186`) may wrap onto two lines and overlap typed text when word or letter spacing is increased. Test with the text-spacing bookmarklet.
- **Unbuilt components**: #9 and #10 are graded as failures because the defect is hard-coded and no prop or CSS variable can change it. `SavedTrips.vue` and `StopSearch.vue` have no Principle 1 defects visible in source (the grip glyph is `aria-hidden`, and `autocomplete="off"` on a stop search isn't user data, so 1.3.5 doesn't apply).

## Outside scope, noted but not graded (Principles 2–4)

These came up while reading, but you limited the audit to Principle 1:
- **2.4.7**: `.site-nav a:focus { outline: none; }` (`site.css:52`) overrides `:focus-visible`, so nav links show no focus indicator.
- **2.2.2**: the home carousel auto-animates with no pause (`site.css:84`). The alerts banner rotates every 20 s (`alerts.js:16`).
- **2.1.1 / 2.5.7**: map stops are click-only `<g>` elements (`map.js:16`). The modal close control is a `<span>` (`alerts.html:68`). `SavedTrips.vue` reordering is drag-only.
- **2.4.3**: positive `tabindex` values (`login.html:41-42`).
- **2.5.8**: `.mini-btn` is 16×16 and `.zoom-btn` is 20×20.
- **3.1.1**: `fares.html:2` has no `lang` attribute.
- **3.2.2**: changing the zone `<select>` navigates away immediately (`fares.js:7-9`).
- **3.2.6**: the Help link is missing from the header on `claim-2.html` and moves to the footer.
- **3.3.1**: feedback errors are never described in text.
- **3.3.7**: claim-3 asks again for the email and phone entered on claim-1.
- **3.3.8**: pasting is blocked in the password and one-time-code fields (`login.js:12,22`).
- **4.1.2**: `#notify-switch` never updates `aria-checked` (`alerts.js:26-28`). Also finding #1.
- **4.1.3**: `#refresh-result` isn't a live region (`alerts.html:51`).

## Manual checks required

- **1.3.2**: rendered reading order with a screen reader on all 11 pages and in the alerts modal.
- **1.3.3**: confirm no other instruction relies on shape, size, position or sound.
- **1.3.4**: portrait and landscape on a phone or tablet.
- **1.4.4**: 200% browser zoom on all pages, especially `.mini-btn`, `.zoom-btn` and `.otp-digit`.
- **1.4.12**: text-spacing override on all pages (floating labels, `.mini-btn`, `.live-banner`).
- **Confirm or drop the likely failures:** #11 (login OTP row at 320×256), #12 (map label contrast, rendered), #13 (whether a text equivalent of the map is planned).
- **Screen reader smoke test**: with NVDA + Firefox or VoiceOver + Safari, confirm #1 is announced as an unnamed button, #2 announces nothing, and #3 reads cells without their headers.

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs` and `wcag_audit.py` were not run because no shell was available. Everything here comes from reading the source by hand.
- No rendering, keyboard walk-through or assistive technology testing was done.
- Nothing from Principles 2–4 is graded.

## Assumptions

- The audit uses WCAG 2.2 (W3C Recommendation, 12 December 2024).
- Contrast ratios were calculated by hand from the colour values in the source (WCAG relative-luminance formula) and rounded to two decimals.
- CSS results assume `css/site.css` is the only stylesheet (no inline or user styles apart from `feedback.html:29`).
- The Vue components were judged as written, not rendered. #9 and #10 count as failures because no prop, slot or CSS variable can override the hard-coded colours or handlers.

## Reproduction

To confirm and extend these results, run `python3 ~/.claude/skills/wcag22-a11y/scripts/wcag_audit.py . --url . --pages 11 --out report.md` after `setup_page_runner.sh`. Then re-check #6–#12 at 1280×800 and 320×256.

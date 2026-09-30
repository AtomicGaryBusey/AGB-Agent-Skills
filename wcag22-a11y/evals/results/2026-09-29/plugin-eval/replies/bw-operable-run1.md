# WCAG 2.2 Level AA audit: Brightwater Transit static front end (Principle 2, Operable)

**Scope:** 11 HTML pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, `js/*.js`, `img/*.svg` and `components/*.vue` (source only, not rendered). Processes covered: the lost-item claim (claim-1 → claim-2 → claim-3) and sign-in (password → one-time code). The target is WCAG 2.2 AA, limited to the 20 AA criteria in Principle 2. I used no tools and no assistive technology: the review was done by reading the files. Findings cite WCAG 2.2 (W3C Recommendation, 12 December 2024).

**Summary:** 8 nonconformities, 0 deviations, 2 advisories, 7 review notes. Of the 20 criteria: 8 fail, 8 pass (on the source alone), 4 N/A.

**Evidence:** I read every file in the folder in full and searched them for `tabindex`, `accesskey`, `keydown`, `@keyframes`, `animate` and `meta http-equiv`. `wcag_scan` and `wcag_page` were not run because there is no shell.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-2.1.2 | WCAG 2.2 SC 2.1.2 (A); also SC 2.1.1 (A) | page | `alerts.html:66-77`, `alerts.html:68`, `js/alerts.js:64-67`, `js/alerts.js:74-86` | A keyboard user can't leave the "Email alerts" modal. Tab only moves between the email field and Subscribe. Escape is cancelled on purpose. The only close control is a `<span>` that responds to clicks, and it can't get focus. | `alerts.js:80-85` always calls `preventDefault()` on Tab and toggles focus between `#alert-email` and `#alert-subscribe`. `alerts.js:75-77` cancels Escape. `alerts.html:68` is `<span class="modal__close">` with no `tabindex` and no key handler. Criterion 2.1.2 applies to all content (non-interference rule), so this fails the whole page. | Make the close control `<button type="button" class="modal__close" aria-label="Close">×</button>`. Include it in the focus loop (loop over all focusable elements in `.modal`, and handle Shift+Tab). Let Escape call `closeModal()`. Or replace the whole thing with the native `<dialog>`/`showModal()` pattern already used on index. |
| 2 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (A) | page | `map.html:43-49`, `js/map.js:15-20` | Map stops only respond to the mouse. `<g class="stop">` elements have click handlers but can't get focus and have no key handler. Stop details (lines, step-free access) can only be reached with a mouse, and the page has no other list of stops. | Search found no `tabindex` or `keydown` in `map.js`. Only `g.addEventListener('click', …)` at `map.js:16`. | Put each stop's name in a real `<button>` (for example a stop list next to the SVG), or wrap each `<g>` in `<a href="#" role="button">` / give it `tabindex="0"` and handle Enter and Space. Add an accessible name to each. |
| 3 | Nonconformity | WCAG-2.5.7 | WCAG 2.2 SC 2.5.7 (AA); also SC 2.1.1 (A) | component | `components/SavedTrips.vue:5`, `:7-15`, `:31-40` | Saved trips can only be reordered by dragging. There is no single-pointer alternative (such as Move up/down buttons) and no keyboard method. The instructions at line 5 describe dragging only. | The template has only `draggable="true"`, `@dragstart` and `@drop`. No other control changes `trips` order. The component isn't built yet, so this is a failure in its source. | Reuse the pattern from `planner.html:77-101`: add "Move up"/"Move down" buttons, each with the trip name as hidden text, that splice `trips`. Announce the new position in a `role="status"` region and update the instructions. |
| 4 | Nonconformity | WCAG-2.2.2 | WCAG 2.2 SC 2.2.2 (A) | page + stylesheet | `index.html:31-49`, `css/site.css:82-93` (`animation` at `:84`) | The home-page promo carousel starts moving automatically, shows alongside other content, loops forever (`infinite`, 18 s cycle), and has no pause, stop or hide control. Criterion 2.2.2 applies to all content (non-interference rule). | `.promo-track { animation: promo-slide 18s ease-in-out infinite; }`. The carousel section has no buttons, and no `prefers-reduced-motion` query exists anywhere. | Add a visible Pause/Play button that toggles `animation-play-state: paused`, and pause on hover and focus. Also add `@media (prefers-reduced-motion: reduce) { .promo-track { animation: none; } }`. Simplest option: show the three slides as a static list. |
| 5 | Nonconformity | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (A) | page | `login.html:41`, `login.html:42` | Positive `tabindex` breaks the focus order. The first Tab goes to "Create an account" (`tabindex="1"`) and the next to "Sign in" (`tabindex="2"`). Both come before the skip link, the navigation, and the email and password fields, so the user reaches Submit before the fields it submits. | `<button type="submit" class="btn" tabindex="2">` and `<a href="help.html#account" tabindex="1">`. | Remove both `tabindex` attributes. The DOM order is already logical. |
| 6 | Nonconformity | WCAG-2.4.7 | WCAG 2.2 SC 2.4.7 (AA) | stylesheet (all 11 pages) | `css/site.css:52`; main-nav markup, e.g. `index.html:16-25` (same block at lines 16-25 of every page) | Keyboard focus is invisible on all seven main-navigation links. `.site-nav a:focus { outline: none; }` wins over the global `:focus-visible` outline, and no other focus style replaces it. The `aria-current` underline (`:53`) is always shown, so it doesn't indicate focus. | Specificity: `.site-nav a:focus` is (0,2,1) and `:focus-visible` is (0,1,0), so the outline is removed. Only `:hover` adds an underline (`:51`). | Delete `site.css:52`, or replace it with `.site-nav a:focus-visible { outline: 3px solid var(--brand); outline-offset: 2px; }`. |
| 7 | Nonconformity | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page + stylesheet | `feedback.html:64-72`, `css/site.css:189` (and `feedback.html:29`) | The feedback page's footer is fixed to the bottom of the viewport and is at least 12rem tall, with `z-index: 50`. Browsers don't scroll an element that is already inside the viewport, even if something covers it. So when a keyboard user tabs down the form, a field in the bottom 12rem of the viewport can be completely hidden behind the footer. `padding-bottom: 12rem` on `<main>` only makes room for the last field and doesn't prevent this. The fix at `site.css:191` only applies to viewports 30rem tall or less. | `.dock-footer { position: fixed; bottom: 0; min-height: 12rem; z-index: 50; }`. There is no `scroll-padding-bottom`. | Add `html { scroll-padding-bottom: 13rem; }` on this page. Better: make the footer static and move "Chat with an agent" into the normal page flow. |
| 8 | Nonconformity | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (AA) | page + stylesheet | `alerts.html:32-34`, `css/site.css:132-135` | The Previous alert, Next alert and Hide alert banner buttons are 16 × 16 CSS px, spaced 4 px apart. They don't meet the 24 × 24 minimum, and they don't qualify for the spacing exception either. | `.mini-btn { width: 16px; height: 16px; margin-left: 4px; }`. The buttons' centres are 20 px apart, so 24 px circles centred on neighbouring buttons overlap each other and the next button. None of the exceptions (inline, equivalent, user-agent, essential) apply. | Set `min-width: 24px; min-height: 24px` (44 px is better) and `gap: 8px` on `.live-banner__controls`. |

## Advisories

| # | Check ID | Location | Note |
|---|---|---|---|
| A1 | WCAG-BP-focus-loss (relates to SC 2.4.3) | `js/alerts.js:19-22` | "Hide alert banner" sets `banner.hidden = true` while that button has focus. Focus falls back to `<body>`, and some screen readers restart from the top. Move focus to `#main` or the `<h1>` (with `tabindex="-1"`) after hiding. |
| A2 | WCAG-2.3.3 (AAA, not an AA failure) | `css/site.css:84`, `:141`, `components/ToggleSwitch.vue:34,38` | The motion and transitions ignore `prefers-reduced-motion`. Add a reduced-motion media query. |

## SC coverage (Principle 2, Level A + AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #1, #2, #3 |
| 2.1.2 No Keyboard Trap | A | **Fail** | #1 |
| 2.1.4 Character Key Shortcuts | A | N/A | No single-key shortcuts. The only `keydown` handlers are on focused widgets (`alerts.js:30`, `login.js:27`). |
| 2.2.1 Timing Adjustable | A | N/A | No session or response time limits in the static code. |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #4 (the alerts banner passes, see R1) |
| 2.3.1 Three Flashes or Below | A | Pass (static) | No flashing content. The carousel moves slowly. |
| 2.4.1 Bypass Blocks | A | Pass (static) | A skip link to `#main` plus `header`/`nav`/`main`/`footer` landmarks on all 11 pages |
| 2.4.2 Page Titled | A | Pass | Every `<title>` is unique and descriptive. Claim steps include "step N of 3". |
| 2.4.3 Focus Order | A | **Fail** | #5 |
| 2.4.4 Link Purpose (In Context) | A | Pass | Link text is clear on its own or from its sentence (e.g. `alerts.html:56` "route map"). |
| 2.4.5 Multiple Ways | AA | Pass (see R4) | Main nav on every page plus the home-page quick links. Claim steps 2 and 3 are covered by the process exception. |
| 2.4.6 Headings and Labels | AA | Pass | Headings and form labels are descriptive. |
| 2.4.7 Focus Visible | AA | **Fail** | #6 |
| 2.4.11 Focus Not Obscured (Minimum) | AA | **Fail** | #7 |
| 2.5.1 Pointer Gestures | A | N/A | No multipoint or path-based gestures. Map zoom uses buttons. |
| 2.5.2 Pointer Cancellation | A | Pass | All actions use `click`. No handlers fire on pointer-down. |
| 2.5.3 Label in Name | A | Pass (see R5) | "Move up …", "Help & contact", the switch label and form labels all match their visible text. |
| 2.5.4 Motion Actuation | A | N/A | No device-motion input. |
| 2.5.7 Dragging Movements | AA | **Fail** | #3 (the planner passes, see R2) |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #8 (other small targets, see R3) |

## Review notes

- **R1 (2.2.2, alerts banner):** `alerts.js:16` rotates the banner text every 20 s, and there is no pause. It passes because "Hide alert banner" meets the "hide" option, but only for users who can hit that 16 px button (#8). A Pause button would be better.
- **R2 (2.5.7, planner):** The drag-to-reorder list at `planner.html:79-99` passes because each trip has Move up/Move down buttons (`planner.js:48-59`) that also announce the new position.
- **R3 (2.5.8, other small targets):**
  - Map zoom buttons, 20 × 20 px (`site.css:160-163`): pass only through the spacing exception. Centres are 28 px apart (8 px gap), and 12 px gap in the narrow layout.
  - Modal "×" close (`alerts.html:68`): at `1.5rem` it may be under 24 px wide, though it seems to meet the spacing exception. This goes away with the fix for #1.
  - Map stop circles (`map.html:43-49`): 18 px or less and they shrink as the SVG scales, but stops are far apart, so they pass on spacing.
  - Rendered sizes need measuring in a browser.
- **R4 (2.4.5):** This passes on two techniques: G126 (nav to every page) and G125/G185 (home-page links). A site map or search would be more robust.
- **R5 (2.5.3):** Several controls show symbols rather than words: "+"/"−" named "Zoom in"/"Zoom out", and "‹"/"›"/"×" in the banner. Visible symbols generally aren't treated as text labels, so they pass, but check with speech-input users.
- **R6 (conformance scope):** Findings #1 and #4 break criteria that the non-interference rule applies to all content, so the alerts page and the home page fail no matter what else is fixed. #5 is on the sign-in page, which is a step in a process, so it counts against every step of sign-in.
- **R7 (components):** The `.vue` files are unbuilt. #3 applies once `SavedTrips` is placed on a page. `ToggleSwitch.vue` (native checkbox with a focus ring on the track at `:42`) and `StopSearch.vue` have no Principle 2 issues.

## Manual checks still required (before any conformance statement)

- **Keyboard walk-through of all 11 pages in a browser:** confirm #1, #2, #5 and #6, and confirm the other 2.4.3/2.4.7 passes, including the native `<dialog>` on index (`site.js`).
- **2.4.11:** Tab through `feedback.html` at 1280 × 720 and 1280 × 600 to confirm fields are hidden behind the footer.
- **2.5.8:** Measure rendered target sizes (R3), including at 320 px width.
- **Screen reader smoke test:** not done.

## Not run / not applicable

- `wcag_audit.py`, `wcag_scan.py` and `wcag_page.mjs` (axe-core) were not run because there is no shell.
- Principles 1, 3 and 4 were out of scope.
- `fonts/bwicons.woff2`, referenced at `site.css:4`, is missing from the folder, so the icon glyphs weren't checked. They are all `aria-hidden` and none is a control's only label, except the swap button, which has its own `aria-label`.

## Out-of-scope issues noticed (not audited, listed for follow-up)

- `fares.html:2`: no `lang` (3.1.1).
- `js/fares.js:7-9`: changing the `<select>` navigates the page (3.2.2).
- `planner.html:36`: the locate button has no accessible name (4.1.2 / 1.1.1).
- `js/alerts.js:26-28`: `aria-checked` is never updated (4.1.2).
- `js/login.js:12,22`: paste is blocked on the password and one-time-code fields (3.3.8).
- `claim-3.html:35-40`: asks again for the email and phone already given in step 1 (3.3.7).
- `claim-2.html:27,63`: the Help link moves from the header to the footer (3.2.6).
- `components/ZoneInfoTooltip.vue:8-11`: the tooltip can't be hovered over and can't be dismissed with Escape (1.4.13).
- `css/site.css:136`: `min-width: 880px` (1.4.10).
- `fares.html:47-60`: header cells are marked up as `<td class="th">` (1.3.1).
- `css/site.css:48`: wordmark colour `#9cc3e6` on white (1.4.3).
- `js/feedback.js`: error messages are never filled in (3.3.1).
- `alerts.html:51`: the refresh result is not announced as a status message (4.1.3).

## Assumptions

- Rendering follows current Chromium, Firefox and Safari defaults.
- `:focus-visible` is supported.
- The Vue components are judged as written, as they would render once built.

## Reproduction

Open each page from the folder in a desktop browser and use only the keyboard. For each finding, follow the steps in its Evidence cell: for example, on alerts.html activate "Get email alerts", then try Tab, Shift+Tab and Escape.

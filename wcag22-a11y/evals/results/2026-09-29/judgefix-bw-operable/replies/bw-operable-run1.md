# WCAG 2.2 Level AA audit, Principle 2 (Operable): Brightwater Transit static front end

**Scope:** 11 pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, `js/*.js` (7 files) and `components/*.vue` (4 source-only files). The only multi-step process is the lost-item claim (claim-1 → claim-2 → claim-3). The 20 Level A and AA criteria under Principle 2 were checked. No assistive technology or browser was used.

**Summary:** The site does not meet Principle 2 at Level AA. I found 9 nonconformities, 0 deviations, 2 advisories and 6 review notes. Of the 20 criteria, 8 fail, 10 pass, 2 are N/A and none are left unevaluated.

**Evidence:** This was a static review only. There was no shell, so the scanner and the rendered-page runner were not run. I read every file listed above line by line, and traced keyboard, focus and pointer behaviour by hand from the HTML, CSS and JS.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-2.1.2 | WCAG 2.2 SC 2.1.2 (Level A) | page | `js/alerts.js:74-86`, `alerts.html:66-77` | **Keyboard trap.** Once the "Email alerts" modal is open, keyboard users cannot get out of it. Because of the non-interference rule, this fails the whole alerts page. | `alerts.js:75-77` blocks Escape with `preventDefault()` and returns. `alerts.js:79-85` makes Tab and Shift+Tab switch only between `#alert-email` and `#alert-subscribe`. The only exits are the `<span>` close control (finding 2) and a backdrop click (`alerts.js:65-67`), and both need a mouse. | Let Escape call `closeModal()`. Include the close button in the Tab cycle, or use native `<dialog>` with `showModal()` as `index.html:65` does. |
| 2 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (Level A) | page | `alerts.html:68`, `js/alerts.js:64` | The modal's close control can't be reached or used from the keyboard. It also breaks 4.1.2 (outside this scope). | `<span class="modal__close" id="email-modal-close">&times;</span>` has no tabindex or role and only a `click` listener. | `<button type="button" class="modal__close" aria-label="Close email alerts">&times;</button>` |
| 3 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (Level A) | page | `map.html:43-49`, `js/map.js:15-20` | The map stops only respond to the mouse. The page says "Select a stop on the map…" (`map.html:31`), but keyboard users can't open any stop's details, and there's no other way to reach them. | Each `<g class="stop">` is plain SVG, not focusable, with only `addEventListener('click')`. | Make each stop focusable (`tabindex="0" role="button" aria-label="Market Square"`) and handle Enter and Space, or wrap each one in an SVG `<a>`. A better option is a list of stop buttons next to the map that drives the same panel. |
| 4 | Nonconformity | WCAG-2.5.7 | WCAG 2.2 SC 2.5.7 (Level AA); also SC 2.1.1 (Level A) | component | `components/SavedTrips.vue:7-15` | Saved trips can only be reordered by dragging. There is no single-pointer or keyboard way to do it. | The only reorder handlers are `@dragstart`, `@dragover.prevent` and `@drop`. The grip (`:16`) is `aria-hidden` and there are no buttons. `planner.html:82-97` gets this right with Move up / Move down. | Add Move up / Move down buttons to each item, like the planner, and announce the new position through a `role="status"` region. |
| 5 | Nonconformity | WCAG-2.2.2 | WCAG 2.2 SC 2.2.2 (Level A), non-interference | page, stylesheet | `index.html:31-49`, `css/site.css:82-93` (`:84`) | The home-page promo carousel starts moving on its own, loops forever, and has no way to pause, stop or hide it. | `animation: promo-slide 18s ease-in-out infinite`: three slides, each shown for about 5 s, alongside other content. The page has no controls and the CSS has no `prefers-reduced-motion` rule. | Add a Pause/Play button that toggles `animation-play-state` on `.promo-track`. Pause on hover and focus. Add `@media (prefers-reduced-motion: reduce) { .promo-track { animation: none; } }`. The simplest fix is not to auto-rotate. |
| 6 | Nonconformity | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (Level A) | page | `login.html:41-42` | Positive `tabindex` values scramble the focus order on the sign-in page. | `<a … tabindex="1">Create an account</a>` and `<button … tabindex="2">Sign in</button>`. From the top of the page, the first Tab goes to "Create an account" and the second to "Sign in". Only then does focus reach the skip link, the navigation, username and password, so the button comes before the fields it submits. | Remove both `tabindex` attributes. |
| 7 | Nonconformity | WCAG-2.4.7 | WCAG 2.2 SC 2.4.7 (Level AA) | stylesheet | `css/site.css:52` (affects nav on all 11 pages, e.g. `index.html:16-26`) | The main navigation links show no focus indicator. | `.site-nav a:focus { outline: none; }` has higher specificity (0,1,1) than the global `:focus-visible` rule at `site.css:31` (0,1,0), so the outline is removed. No other focus style replaces it. The `aria-current` underline at `:53` marks the current page, not focus. | Delete `site.css:52`, or replace it with `.site-nav a:focus-visible { outline: 3px solid var(--brand); outline-offset: 2px; }`. |
| 8 | Nonconformity | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (Level AA) | page, stylesheet | `css/site.css:189`, `feedback.html:64`, `feedback.html:29` | On the feedback page, a fixed footer at least 12rem tall covers the bottom of the viewport. Fields brought into view by Tab end up completely hidden behind it. | `.dock-footer { position: fixed; bottom: 0; min-height: 12rem; z-index: 50 }`. `padding-bottom: 12rem` on `<main>` only adds room to scroll; it does not change where the browser scrolls a focused element. Browsers scroll just far enough to put a newly focused element at the bottom edge, which is under the ~192 px opaque footer (the checkboxes, message, radios and "Send feedback"). No `scroll-padding` is set. The `max-height: 30rem` fallback at `:191` only helps on very short viewports. | Add `html { scroll-padding-bottom: 13rem; }` on this page, or better, don't fix the footer in place (use `position: static`, or a small sticky chat button). |
| 9 | Nonconformity | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (Level AA) | page, stylesheet | `alerts.html:32-34`, `css/site.css:132-135` | The live-banner buttons (Previous, Next, Hide) are 16 × 16 px and too close together for the spacing exception. | `.mini-btn { width:16px; height:16px; margin-left:4px }`. Their centres are 20 px apart, so their 24 px circles overlap. The same controls don't exist anywhere else on the page, and none of the other exceptions applies. | Set `min-width: 24px; min-height: 24px` (44 px is better) and add at least an 8px gap. |
| 10 | Advisory | WCAG-BP-target-size-margin | WCAG 2.2 SC 2.5.8 (Level AA), best practice | stylesheet | `css/site.css:160-163`, `map.html:34-35` | The zoom buttons are only 20 × 20 px. They pass today because of the spacing exception, but only just (see the review notes). | Centres are 28 px apart in the column layout (20 + 8 gap) and 32 px apart in the ≤40rem row layout, which is more than 24 px, so no circles overlap. | Make them 24 px or larger (ideally 44 px) so a future layout change can't make them fail. |
| 11 | Advisory | WCAG-BP-reduced-motion | WCAG 2.2 SC 2.3.3 (AAA), best practice | stylesheet | `css/site.css:84, 141, 181` | The site has no `prefers-reduced-motion` handling for the carousel, switch knob or floating-label transitions. | No `@media (prefers-reduced-motion)` rule anywhere in the stylesheet. | Add a reduced-motion block that turns off the animations and transitions. |

## SC coverage (Principle 2, Level A and AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #2, #3, #4 |
| 2.1.2 No Keyboard Trap | A | **Fail** | #1 |
| 2.1.4 Character Key Shortcuts | A | Pass | The only key handlers are Space/Enter on the focused switch (`alerts.js:30-35`), Backspace in the code inputs (`login.js:27-29`) and Tab/Escape inside the modal. There are no single-character shortcuts. |
| 2.2.1 Timing Adjustable | A | N/A | No time limits in the code, including the code step. |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #5. The alerts banner (`alerts.js:16`, 20 s rotation) passes because the Hide button stops it (`alerts.js:19-22`). |
| 2.3.1 Three Flashes or Below | A | Pass | Nothing flashes. The carousel slides every ~6 s. |
| 2.4.1 Bypass Blocks | A | Pass | The skip link to `#main` is on all 11 pages and shows on focus (`site.css:28-29`). |
| 2.4.2 Page Titled | A | Pass | Each page has a distinct title. The claim steps include "step N of 3". |
| 2.4.3 Focus Order | A | **Fail** | #6. The planner keeps focus after moving a trip (`planner.js:57`); the survey dialog returns focus to its opener (`site.js:9-11`). |
| 2.4.4 Link Purpose (In Context) | A | Pass | Link text is descriptive. The inline "route map" link (`alerts.html:56`) is clear from its sentence. |
| 2.4.5 Multiple Ways | AA | Pass | Main nav on every page, plus home-page quick links and footer links. Claim steps 2–3 are exempt as steps in a process. See the review notes. |
| 2.4.6 Headings and Labels | AA | Pass | Headings and labels describe their content. |
| 2.4.7 Focus Visible | AA | **Fail** | #7 |
| 2.4.11 Focus Not Obscured (Minimum) | AA | **Fail** | #8 |
| 2.5.1 Pointer Gestures | A | Pass | No multipoint or path-based gestures. |
| 2.5.2 Pointer Cancellation | A | Pass | All actions fire on `click` or `change`, not on pointer-down. |
| 2.5.3 Label in Name | A | Pass | "Move up Home to Work" starts with its visible text. Switch and fields take their names from their visible labels. Symbol-only buttons (+, −, ‹, ›, ×, swap icon) have no visible text label. |
| 2.5.4 Motion Actuation | A | N/A | No device-motion input. |
| 2.5.7 Dragging Movements | AA | **Fail** | #4, in the component. `planner.html` passes because it has Move up / Move down buttons. |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #9. `.btn-small` is 32 px; `.btn`, fields and OTP inputs are 44 px or more. |

## Review notes

- **Vue components** are source only and not mounted on any page. Finding #4 applies wherever `SavedTrips.vue` is used. `ToggleSwitch.vue` (native checkbox with a visible `:focus-visible` ring), `StopSearch.vue` and the keyboard side of `ZoneInfoTooltip.vue` raise no Principle 2 issues.
- **Map stop targets** (`map.html:43-49`, `r="9"`, so 18 px at 600 px width and smaller on narrow screens) pass 2.5.8 through the spacing exception: the stops are at least ~80 px apart even at 343 px width. Check this again after fixing #3. If you add buttons to the map, make them at least 24 px.
- **2.4.5 is a judgement call.** The main nav and the home-page links to every section count as two ways to find pages, but they overlap a lot. A site map or search on the help page would settle it.
- **2.4.11 (#8) is based on how browsers normally scroll focused elements into view**, not on a rendered test. Confirm it by tabbing through `feedback.html` at 1280 × 800.
- **Fares zone picker** (`js/fares.js:7-9`) loads a new page on `change`. In some browsers, pressing the arrow keys on the closed select navigates at every option. This is mainly SC 3.2.2 (outside this scope), but it makes the control hard to use from the keyboard.
- **Carousel:** the hidden slides are moved off-screen with `transform`, not hidden, so they stay in the reading order. That is fine for 2.4.3 because they contain no focusable elements.

## Manual checks required

None are open for Principle 2. Every criterion was decided from the source. Before relying on these statuses, do these in a browser:

- A keyboard-only walk through all 11 pages. In particular, confirm #1, #6, #7 and #8, and that the carousel fix works.
- A screen-reader check that the alerts modal and the map fixes announce correctly.

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs` and axe-core were not run (no shell). No screenshots or measured rendered sizes; target sizes were worked out from CSS.
- **Found in passing, outside this scope (Principles 1, 3, 4).** These were not audited systematically:
  - `planner.html:36` locate button has no accessible name (4.1.2/1.1.1).
  - `alerts.js:26-28` never updates `aria-checked` on the switch (4.1.2).
  - `login.js:8-12, 22` blocks pasting into the password and code fields (3.3.8).
  - `claim-3.html:35-40` asks again for email and phone already given in step 1 (3.3.7).
  - `claim-2.html:11-27` drops the header Help link (3.2.6).
  - `fares.html:2` has no `lang` (3.1.1).
  - `fares.html:42, 122` shows peak fares by colour only (1.4.1).
  - `fares.html:47-60` uses `td.th` instead of `<th>` (1.3.1).
  - `ZoneInfoTooltip.vue:8-17` tooltip can't be hovered over or dismissed (1.4.13).
  - `site.css:136` sets `min-width: 880px` (1.4.10).
  - `site.css:180` label colour `#a0a0a0` is low contrast (1.4.3).
  - `feedback.js` never fills in the error messages (3.3.1).

## Assumptions

- WCAG 2.2 (W3C Recommendation, 12 December 2024) is the standard used.
- The pages run as written, with JavaScript on, in current Chromium, Firefox and Safari.
- `fonts/bwicons.woff2` and `img/sprite.svg#logo`/`#step-free` are either missing or out of scope. They don't affect Principle 2.
- No assistive technology was used. A screen-reader check (e.g. NVDA + Firefox, VoiceOver + Safari) should confirm:
  - the alerts modal can be escaped once fixed;
  - map stops announce as buttons with their names;
  - the Move up / Move down announcements come through `#saved-status`.

## Reproduction

1. **#1 and #2:** open `alerts.html` and press Tab to "Get email alerts", then Enter. Focus goes to the email field. Tab and Shift+Tab only alternate between email and Subscribe, Escape does nothing, and the × can't be focused.
2. **#6:** open `login.html` and press Tab once. Focus lands on "Create an account".
3. **#7:** on any page, Tab past the logo into the nav. No outline appears.
4. **#3:** open `map.html` and Tab through the page. No stop ever gets focus.
5. **#8:** open `feedback.html` at a viewport taller than 480 px and Tab from the name field downward. Focused fields go under the navy footer.
6. **#5:** open `index.html` and watch the carousel. It rotates with no pause control.

**Conformance:** the site does **not conform** to WCAG 2.2 Level AA. Under Principle 2 it fails SC 2.1.1, 2.1.2, 2.2.2, 2.4.3, 2.4.7, 2.4.11, 2.5.7 and 2.5.8.

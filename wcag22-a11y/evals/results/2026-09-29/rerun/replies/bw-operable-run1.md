# WCAG 2.2 Level AA audit, Principle 2 (Operable): Brightwater Transit static front end

**Scope:** 11 pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, `js/*.js`, `img/*.svg` and 4 Vue source-only components. The process in scope is the lost-item claim (claim-1 → claim-2 → claim-3) and sign-in (password → one-time code). Level AA, limited to the 20 A/AA criteria in Principle 2.
**Method:** I read every file listed. No shell was available, so I didn't run `wcag_scan`, `wcag_page`, axe-core, a browser, or any assistive technology.
**Summary:** 7 nonconformities, 1 deviation, 3 advisories, 8 review notes. Of the 20 criteria: 7 fail, 10 pass (from reading the code only), 1 N/A, 2 need a rendered check.
**Verdict:** the site **does not conform** to WCAG 2.2 AA. It fails 2.1.1, 2.1.2, 2.2.2, 2.4.3, 2.4.7, 2.5.7 and 2.5.8, and 2.4.11 is a likely fail.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-2.1.1 | SC 2.1.1 Keyboard (A) | page | `js/map.js:15-20`, `map.html:43-49` | Route-map stops only work with a mouse. Keyboard users can't get stop details, which is the page's main purpose (`map.html:31`). | A `click` listener is attached to SVG `<g class="stop">`. There's no `tabindex`, role, or key handler. SVG `<g>` isn't focusable. | Make each stop an `<a href="#stop-…">` or `<button>` in the SVG with an accessible name, or add a plain list of stop buttons beside the map that fill `#stop-panel-body`. |
| 2 | Nonconformity | WCAG-2.1.2 (+2.1.1) | SC 2.1.2 No Keyboard Trap (A); SC 2.1.1 (A) | page | `js/alerts.js:74-86`, `alerts.html:68`, `js/alerts.js:64-67` | The "Get email alerts" modal traps keyboard users. Tab and Shift+Tab only move between the email field and Subscribe. Esc is suppressed. The close "×" is a `<span>`, so the keyboard can't reach it. The only way out is clicking the backdrop with a mouse. | Keydown handler: `if (e.key === 'Escape') { e.preventDefault(); return; }` and `if (e.key !== 'Tab') return; e.preventDefault(); …` toggles between 2 elements. `<span class="modal__close" id="email-modal-close">&times;</span>` | Replace the span with `<button type="button" class="modal__close" aria-label="Close">×</button>` and include it in the focus cycle. Make Esc call `closeModal()`. The simplest route is the native `<dialog>` + `showModal()` already used in `js/site.js:7`. |
| 3 | Nonconformity | WCAG-2.5.7 (+2.1.1) | SC 2.5.7 Dragging Movements (AA); SC 2.1.1 (A) | component | `components/SavedTrips.vue:11-14`, `:5` | Saved trips can only be reordered by drag and drop. There's no single-pointer or keyboard alternative. | `draggable="true" @dragstart @dragover.prevent @drop`. The only controls are the trip links. The help text says "Drag a trip…". | Add Move up / Move down buttons, as `planner.html:82-97` / `js/planner.js:48-59` already do, and update the instructions. |
| 4 | Nonconformity | WCAG-2.2.2 | SC 2.2.2 Pause, Stop, Hide (A) | stylesheet/page | `css/site.css:82-93` (`animation: promo-slide 18s ease-in-out infinite` at `:84`), `index.html:31-49` | The home-page "What's new" carousel moves automatically, forever, next to other content. There's no pause, stop, or hide control. Each slide shows for about 5 s (28 % of 18 s) and then slides away. This also bears on 2.2.1: see review note R1. | Infinite CSS keyframe animation. There are no controls in the markup and no `prefers-reduced-motion` override anywhere in `site.css`. | Add a Pause/Play `<button>` that toggles `animation-play-state: paused`, pause on hover and focus-within, and add `@media (prefers-reduced-motion: reduce) { .promo-track { animation: none; } }`. Or show the three items as a static list. |
| 5 | Nonconformity | WCAG-2.4.3 | SC 2.4.3 Focus Order (A) | page | `login.html:41`, `login.html:42` | Positive `tabindex` values reorder focus on the sign-in page. The first Tab goes to "Create an account" and the second to "Sign in". Only after that does focus reach the skip link, header, nav, username and password. Users hit the submit button before the fields it submits. | `<button type="submit" class="btn" tabindex="2">` and `<a href="help.html#account" tabindex="1">` | Remove both `tabindex` attributes so the DOM order applies. |
| 6 | Nonconformity | WCAG-2.4.7 | SC 2.4.7 Focus Visible (AA) | stylesheet | `css/site.css:52`. Affects the main nav links on all 11 pages (`*.html:18-24`) | Keyboard focus on the main navigation links is invisible. | `.site-nav a:focus { outline: none; }` has specificity (0,2,1), which beats the global `:focus-visible { outline: 3px solid … }` at (0,1,0) on `site.css:31`. No other style changes on focus: the underline is `:hover`-only (`:51`), and the `aria-current` border isn't a focus indicator. | Delete `site.css:52`. If you need a custom style, use `.site-nav a:focus-visible { outline: 3px solid var(--brand); outline-offset: 2px; }`. |
| 7 | Nonconformity | WCAG-2.5.8 | SC 2.5.8 Target Size (Minimum) (AA) | stylesheet/page | `css/site.css:132-135`, `alerts.html:32-34` | The service-alert banner's Previous, Next and Hide buttons are 16×16 px and sit 4 px apart, so the spacing exception doesn't apply. The Hide button is also the page's only 2.2.2 control for the auto-rotating banner. | `.mini-btn { width: 16px; height: 16px; margin-left: 4px; }`. The centres are 20 px apart, so 24 px circles around neighbouring buttons overlap (20 < 24). None of the exceptions (inline, equivalent, user-agent, essential) applies. | Make them at least 24×24 px (44×44 is better), e.g. `.mini-btn { min-width: 44px; min-height: 44px; font-size: 1.25rem; }`. |
| 8 | Deviation | WCAG-2.4.11 | SC 2.4.11 Focus Not Obscured (Minimum) (AA) | page/stylesheet | `css/site.css:189`, `feedback.html:64`, `feedback.html:29` | On the feedback page, the footer is `position: fixed` at the bottom with `min-height: 12rem` (≥192 px) and `z-index: 50`. As you Tab down the form, browsers scroll each field just into view at the bottom edge, which puts it behind the footer. The `padding-bottom: 12rem` on `<main>` only helps at the very end of the page, and there's no `scroll-padding-bottom`. The fixed position only turns off below a 30rem viewport height (`:191`). | This was inferred from the CSS. It needs to be confirmed in a browser at, say, 1280×720 by tabbing through `#fb-name` → Send feedback. | Stop fixing the footer (`.dock-footer { position: static; }`), or add `html { scroll-padding-bottom: 13rem; }` on this page. |
| 9 | Advisory | WCAG-2.3.3 | SC 2.3.3 (AAA): not an AA failure | stylesheet | `css/site.css:84`, `:141`, `:181`; `components/ToggleSwitch.vue:34,38` | Nowhere is there a `prefers-reduced-motion` override for the carousel, the switch-knob animation or the floating-label animation. | No `@media (prefers-reduced-motion)` rule in any stylesheet. | Add a reduced-motion block that sets `animation: none; transition: none;`. |
| 10 | Advisory | WCAG-2.5.5 | SC 2.5.5 (AAA): not an AA failure | stylesheet | `css/site.css:160-163` (`.zoom-btn` 20×20), `:69-72` (`.btn-small` 32 px), `components/ZoneInfoTooltip.vue:41` | Several targets are smaller than 44×44. The 20 px zoom buttons are hard to hit, even though they pass AA on spacing (see R2). | Sizes are as declared in the CSS. | Use at least 44×44 px for map controls and small buttons. |
| 11 | Advisory | WCAG-BP-carousel-timer | Best practice (related to 2.2.2) | script | `js/alerts.js:16-18` | Previous and Next on the rotating alert banner don't pause the 20 s timer, so the banner can change right after a user picks a message. | `setInterval(…, 20000)` is only cleared when the banner is dismissed. | Add a Pause button, or `clearInterval(timer)` on the first Previous/Next press. |

## SC coverage (Principle 2, Level A + AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #1, #2, #3 |
| 2.1.2 No Keyboard Trap | A | **Fail** | #2. The native `<dialog>` on index (`js/site.js`) passes: Esc and the Close button work. |
| 2.1.4 Character Key Shortcuts | A | Pass (code reading) | No single-key shortcuts. The OTP Backspace handler (`js/login.js:27-29`) only runs while the field has focus. |
| 2.2.1 Timing Adjustable | A | Review | No session limits, redirects or `meta refresh`. See R1 about the carousel's reading time. |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #4. The alerts banner passes because it can be hidden (R3). |
| 2.3.1 Three Flashes | A | Pass (code reading) | Nothing flashes. The only animations are an 18 s slide and 0.15–0.2 s single transitions. |
| 2.4.1 Bypass Blocks | A | Pass (code reading) | A skip link goes to `#main` on all 11 pages, the target exists, and there are `<nav>`/`<main>` landmarks. |
| 2.4.2 Page Titled | A | Pass (code reading) | Every page has a unique, descriptive title, and the claim steps include "step N of 3". |
| 2.4.3 Focus Order | A | **Fail** | #5 |
| 2.4.4 Link Purpose (In Context) | A | Pass (code reading) | Link text is descriptive. Icon links have visible text. |
| 2.4.5 Multiple Ways | AA | Pass (code reading) | Global nav plus home-page quick links and footer links. Claim steps 2–3 are exempt because they're steps in a process. |
| 2.4.6 Headings and Labels | AA | Pass (code reading) | Headings and labels are descriptive. |
| 2.4.7 Focus Visible | AA | **Fail** | #6 |
| 2.4.11 Focus Not Obscured (Min) | AA | Likely fail (needs a rendered check) | #8. No other sticky or fixed layers. The site header isn't sticky. |
| 2.5.1 Pointer Gestures | A | Pass (code reading) | No multi-point or path-based gestures. |
| 2.5.2 Pointer Cancellation | A | Pass (code reading) | Every action fires on `click` or `change`. There are no `mousedown`/`pointerdown` actions. The tooltip's `mouseenter` only shows content. |
| 2.5.3 Label in Name | A | Pass (code reading) | For example, "Move up Home to Work" starts with its visible text, and "Help & contact" and "Zone N" match. See R4 about glyph buttons. |
| 2.5.4 Motion Actuation | A | N/A | No device-motion input. Geolocation (`js/planner.js:14`) isn't motion. |
| 2.5.7 Dragging Movements | AA | **Fail** | #3. The planner's drag passes because the Move up/down buttons are an alternative (`planner.html:82-97`). |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #7. See R2 for targets that pass on spacing. |

## Review notes

- **R1: 2.2.1 and the carousel.** Each promo slide is visible for about 5 s before it moves away, which works like a reading-time limit that users can't adjust. Fixing #4 with a pause control would also settle this. I'm keeping it as a review item rather than a second failure.
- **R2: 2.5.8 passes on spacing.**
  - `.zoom-btn` (20×20, `site.css:160-163`) sits in a column with an 8 px gap, so the centres are 28 px apart. In the narrow-screen row layout (`:172`) the gap is 12 px and the centres are 32 px apart. Either way the 24 px circles don't overlap, so the spacing exception is met.
  - Map stop circles (r=9, about 18 px at 600 px width, smaller on narrow screens) are 100+ viewBox units apart, so they also pass on spacing. They'll change anyway once #1 is fixed.
  - The alerts modal close span is roughly 14×36 px. Fix it together with #2.
- **R3: 2.2.2 on the alerts banner (`js/alerts.js:16`).** The banner updates by itself every 20 s. `#banner-dismiss` hides it, which is enough for "pause, stop, or hide", but that control is the undersized target in #7.
- **R4: 2.5.3 and glyph buttons.** ‹ › × (`alerts.html:32-34`) and + − (`map.html:34-35`) have `aria-label`s ("Previous alert", "Zoom in"). Single symbols like these generally don't count as visible text labels, so I didn't record a failure. Speech-input users should confirm that "click zoom in" / "click previous alert" work.
- **R5: What was checked and found fine.**
  - The native `<dialog>` on the home page returns focus to its opener (`js/site.js:9-11`).
  - The planner's reorder keeps focus on the button that was pressed (`js/planner.js:57`).
  - The alerts `role="switch"` div is focusable and responds to Space and Enter (`js/alerts.js:30-35`).
  - `ToggleSwitch.vue:42` shows a focus ring on the visible track.
  - The fare-table scroll region is focusable (`fares.html:43`).
- **R6: Vue components.** These aren't built and none of the 11 pages uses them. Findings #3 and #10 apply wherever they're used.
- **R7: Process rule.** Under conformance requirement 3, the nav focus failure (#6) makes the whole claim process and the whole sign-in process fail too. The sign-in process also fails on #5.
- **R8: Other issues outside Principle 2, not graded here.**
  - Unlabelled locate button (`planner.html:36`, 4.1.2).
  - Switch `aria-checked` never updates (`js/alerts.js:26-28`, 4.1.2).
  - Paste blocked on password and OTP (`js/login.js:8-12,22`, 3.3.8).
  - Help link missing on claim-2 (`claim-2.html:27`, 3.2.6).
  - Claim-3 asks again for the email and phone given in claim-1 (3.3.7).
  - Zone select navigates on change (`js/fares.js:7-9`, 3.2.2).
  - No `lang` attribute (`fares.html:2`, 3.1.1).
  - Tooltip can't be dismissed or hovered (`ZoneInfoTooltip.vue`, 1.4.13).
  - Low contrast on labels and wordmark (`site.css:180`, `:48`, 1.4.3).
  - `.alert-detail` has `min-width: 880px` (`site.css:136`, 1.4.10).

## Manual checks required

- 2.4.11: tab through `feedback.html` in a real browser at common viewport sizes (#8).
- 2.2.1: decide R1.
- A keyboard-only walk-through of all 11 pages in a rendered browser, to confirm #1–#7 and the passes that come only from reading the code.
- A screen-reader and speech-input smoke test for R4 and for the dialog behaviour.

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs`, axe-core, browser rendering and assistive-technology testing: none could be run without a shell.
- AAA criteria appear only as advisories.
- Principles 1, 3 and 4 are out of scope (see R8).

## Assumptions

- This is WCAG 2.2 (W3C Recommendation, 12 Dec 2024), Level AA, limited to Principle 2.
- CSS sizes were read as declared, assuming default browser font size (16 px) and no user zoom.
- No assistive technology was used. Every pass is based on reading the code only and should be confirmed in a rendered browser before any conformance claim.

## Reproduction

- **#2:** on `alerts.html`, activate "Get email alerts". Press Tab repeatedly: focus only alternates between the email field and Subscribe. Esc does nothing.
- **#5:** on `login.html`, press Tab from page load. Focus goes to "Create an account" first, then "Sign in".
- **#6:** on any page, Tab to the main nav. No outline appears.
- **#1:** on `map.html`, try to Tab to a stop. None receives focus.

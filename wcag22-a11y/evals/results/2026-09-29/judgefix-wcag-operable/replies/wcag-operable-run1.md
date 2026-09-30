# WCAG 2.2 Level AA audit: Larkspur Library static front end, Principle 2 (Operable) only

**Scope:** index.html, catalog.html, events.html, login.html, signup.html, styles.css, app.js and src/components/*.jsx. The React sources are marked "not built"; I reviewed them as the sources of the matching pages. I covered the 20 Principle 2 success criteria (SC) at Level A and AA. I checked the processes they touch: sign-in (2 steps), sign-up (2 steps), event reservation and adding to the reading list. No automated tools, assistive technology (AT) or browsers were used.

**Summary:** 11 nonconformities, 2 deviations, 3 advisories, 8 review notes. Of the 20 SC: 10 fail, 6 pass, 3 N/A and 1 not evaluated (likely fail).

**Evidence:** I read every in-scope file line by line. I did not run `wcag_scan` or `wcag_page`, because there is no shell. I did not do a rendered keyboard walkthrough; I traced keyboard behaviour from the markup and the handlers in app.js.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (Level A) | page, component | catalog.html:42, :50, :58, :66; src/components/BookCard.jsx:15 | The "Add to reading list" controls are `<div>`s with only an `onclick`. They can't be reached or used with the keyboard. | `<div class="btn add-btn" … onclick="addToList(this)">` has no tabindex, no role and no key handler. | Use `<button type="button" class="btn add-btn" data-title="…">`. In JSX, use `<button type="button" className="btn add-btn" onClick={…}>`. |
| 2 | Nonconformity | WCAG-2.1.2 | WCAG 2.2 SC 2.1.2 (Level A); also 2.1.1 | page, component | app.js:83-92; src/components/Modal.jsx:12-20 | **Keyboard trap in the reservation dialog.** Every Tab is cancelled and focus goes back to "Your name". Escape is also cancelled. The Email field (events.html:97) and the Confirm button (events.html:99) can never get keyboard focus, so a keyboard user can't finish a reservation or leave the dialog. This criterion applies to all content (non-interference), so it fails the whole page. | Sequence: activate "Reserve a seat" → focus on #res-name → Tab → `e.preventDefault(); res-name.focus()` → the same field again. Escape → `preventDefault()` only. | Cycle focus through the dialog's own focusable elements: on Tab from the last one go to the first, and on Shift+Tab the reverse. Close the dialog on Escape. Or use a native `<dialog>` with `showModal()`. |
| 3 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (Level A) | page, component | events.html:88; src/components/Modal.jsx:30 | The dialog's close control is a `<span>` with `onclick`. It isn't focusable and doesn't respond to keys. | `<span class="close" onclick="closeModal()">&times;</span>` | `<button type="button" class="close" aria-label="Close" onclick="closeModal()">×</button>` |
| 4 | Nonconformity | WCAG-2.5.7 | WCAG 2.2 SC 2.5.7 (Level AA); also 2.1.1 | page, component | catalog.html:81-87; app.js:47-65; src/components/ReadingList.jsx:20-26 | The reading list can only be reordered by drag and drop. There is no single-pointer alternative and no keyboard alternative. | `draggable="true"` with only dragstart, dragover and drop handlers. The instruction text (catalog.html:81) says "Drag titles…". | On each item, add "Move up" and "Move down" buttons (or a position `<select>`) that call the same reorder logic. Announce the new position in `#list-status`. |
| 5 | Nonconformity | WCAG-2.2.1 | WCAG 2.2 SC 2.2.1 (Level A) | page | events.html:6 | The page reloads itself every 120 s, and the user can't turn this off, adjust it or extend it. Any open reservation dialog and anything typed into it are lost (failure technique F41). | `<meta http-equiv="refresh" content="120">` | Remove the meta refresh. If the schedule must update, fetch it in the background without reloading, or give the user a "Pause updates" control. |
| 6 | Nonconformity | WCAG-2.2.2 | WCAG 2.2 SC 2.2.2 (Level A) | page, component | app.js:14-17; index.html:34-49; src/components/Carousel.jsx:7-12 | The "What's new" carousel starts on its own, advances every 4 s without end, and appears alongside other content. It has no pause, stop or hide control. This criterion also applies to all content (non-interference). | `setInterval(…, 4000)` with no `clearInterval` path; `transition: transform 0.6s` (styles.css:98). | Add a visible Pause/Play `<button>`, and also pause on hover and focus. Or don't auto-advance at all: show Previous/Next buttons. Respect `prefers-reduced-motion`. |
| 7 | Nonconformity | WCAG-2.4.2 | WCAG 2.2 SC 2.4.2 (Level A) | page | catalog.html:3-7 | The catalog page has no `<title>`. | The `<head>` contains only meta, viewport and stylesheet. | Add `<title>Search the catalog - Larkspur Library</title>`. |
| 8 | Nonconformity | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (Level A) | page | login.html:37, :40 | Positive `tabindex` values change the sign-in focus order. The first Tab goes to "Continue" (tabindex 1), then to PIN (tabindex 2), and only then to the card number, before the Continue button in step 1. The order doesn't follow the task. | `tabindex="2"` on #pin and `tabindex="1"` on the submit button. | Remove both `tabindex` attributes so focus follows the DOM order. |
| 9 | Nonconformity | WCAG-2.4.4 | WCAG 2.2 SC 2.4.4 (Level A) | page | events.html:32 | A link reading "Click here" sits alone in its paragraph, with no context saying what it does. It downloads a calendar file. | `<p><a href="calendar.ics">Click here</a></p>` | Use `<a href="calendar.ics">Add all events to your calendar (.ics)</a>`. |
| 10 | Nonconformity | WCAG-2.4.7 | WCAG 2.2 SC 2.4.7 (Level AA) | stylesheet | styles.css:59 | The focus outline is removed from the main navigation links on all 5 pages, with nothing to replace it. The hover underline (:58) doesn't appear on keyboard focus. | `.site-nav a:focus { outline: none; }` | Replace with `.site-nav a:focus-visible { outline: 3px solid #ffffff; outline-offset: -3px; text-decoration: underline; }`. |
| 11 | Nonconformity | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (Level AA) | stylesheet, page | styles.css:159-169; catalog.html:72-76 | The results pager links are below 24×24 CSS px, and they don't qualify for the spacing exception. | Each target is 16 px plus a 1 px border on each side, so 18×18 px, with `gap: 4px`. Centres are 22 px apart. Circles 24 px across, centred on each link, overlap the neighbouring link's circle. | Set `.pager a { min-width: 24px; min-height: 24px; line-height: 24px; }` (44 px is better) and remove the fixed 16 px width and height. |
| 12 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (Level AA) | page, stylesheet | catalog.html:2, :8; styles.css:5, :19-28 | Above 640 px wide, the catalog page has a sticky header at least 8rem (128 px) tall. Unlike index.html, it has no `pad-for-header` class, so it gets no `scroll-padding-top`. When tabbing backwards (Shift+Tab), the browser scrolls focused links and controls to the top edge, where the header can cover them completely. This needs confirming in a rendered browser. | `body.sticky-page` gives `position: sticky` with `min-height: 8rem`. `<html lang="en">` lacks `class="pad-for-header"`. | Add `scroll-padding-top` to every page that has a sticky header, e.g. put it on `html:has(.sticky-page)` or add the class to catalog.html:2. Better still, make the header shorter. |
| 13 | Deviation | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (Level A) | page, component | app.js:75-77; src/components/Modal.jsx:21-22 | When the dialog closes, focus isn't returned to the "Reserve a seat" button that opened it. Focus ends up on a hidden element or on `<body>`. | `closeModal()` only sets `modal.hidden = true`. The JSX cleanup only removes the listener. | Store `document.activeElement` when the dialog opens and call `.focus()` on it when it closes. |
| 14 | Advisory | WCAG-BP-skip-link | WCAG 2.2 SC 2.4.1 (Level A), best practice | page | index.html:10 (and the same header on all 5 pages) | There is no "Skip to main content" link. SC 2.4.1 is met through landmarks (`<header>`, `<nav>`, `<main id="main">`). But a keyboard user without AT must tab through 5–7 header links on every page. | `#main` exists, but nothing links to it. | Make `<a class="skip-link" href="#main">Skip to main content</a>` the first child of `<body>` and show it on focus. |
| 15 | Advisory | WCAG-2.3.3 | WCAG 2.2 SC 2.3.3 (Level AAA) | stylesheet | styles.css:98 | The carousel's sliding animation ignores the user's reduced-motion setting. This is AAA, so it is not an AA failure. | `transition: transform 0.6s ease` with no `@media (prefers-reduced-motion: reduce)` rule. | Add `@media (prefers-reduced-motion: reduce) { .carousel-track { transition: none; } }` and stop auto-advancing under that setting. |
| 16 | Advisory | WCAG-BP-unique-control-names | WCAG 2.2 SC 2.4.6 (Level AA), best practice | page | events.html:39, :46, :53 | Three buttons are all called "Reserve a seat". The purpose is clear from the surrounding layout, but in a list of controls they can't be told apart. The fixed 112 px width with `overflow: hidden` (styles.css:191-199) can also cut off the label. | Identical accessible names; `.btn-fixed { width: 112px; overflow: hidden; white-space: nowrap }` | Add `aria-describedby` pointing at each event title, and use `min-width` instead of a fixed width. |

## SC coverage (Principle 2, Level A and AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #1, #2, #3, #4 |
| 2.1.2 No Keyboard Trap | A | **Fail** | #2 |
| 2.1.4 Character Key Shortcuts | A | N/A | There are no single-character shortcuts. The key handlers only respond to Enter or Space on the focused sort toggle, and to Tab and Escape inside the dialog. |
| 2.2.1 Timing Adjustable | A | **Fail** | #5 |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #6 |
| 2.3.1 Three Flashes or Below Threshold | A | Pass (static) | There is no flashing content in the source. The carousel slides once every 4 s. |
| 2.4.1 Bypass Blocks | A | Pass | Landmarks (ARIA11) on all 5 pages. See advisory #14. |
| 2.4.2 Page Titled | A | **Fail** | #7. The other 4 pages have descriptive titles. |
| 2.4.3 Focus Order | A | **Fail** | #8; #13 still needs confirming. |
| 2.4.4 Link Purpose (In Context) | A | **Fail** | #9 |
| 2.4.5 Multiple Ways | AA | Pass | Full navigation on every page (G126) plus related links in the content (G125). Login and signup steps are exempt as steps in a process. |
| 2.4.6 Headings and Labels | AA | Pass | Headings and existing labels describe their topic or purpose. Missing labels fall under 3.3.2 and 4.1.2, which are out of scope. |
| 2.4.7 Focus Visible | AA | **Fail** | #10 |
| 2.4.11 Focus Not Obscured (Minimum) | AA | Not evaluated (likely fail) | #12 needs a rendered check. |
| 2.5.1 Pointer Gestures | A | N/A | No multipoint or path-based gestures. |
| 2.5.2 Pointer Cancellation | A | Pass | Actions fire on `click` (the up-event). A drag can be abandoned by dropping the item back in place. |
| 2.5.3 Label in Name | A | Pass | Controls with visible text labels use that text as their name. Icon and image-only controls have no visible text label, so the SC doesn't apply to them. |
| 2.5.4 Motion Actuation | A | N/A | No device-motion input. |
| 2.5.7 Dragging Movements | AA | **Fail** | #4 |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #11. Other targets checked: nav links about 40 px tall, `.icon-btn` 40×40, dialog close 32×32, `.btn-fixed` 112×32, CAPTCHA labels about 104 px. Inline links are exempt. |

## Review notes

1. **2.4.11 on index.html:** `scroll-padding-top: 14rem` (styles.css:5) is larger than my estimate of the header height (about 10rem). So the sticky header probably doesn't hide focused elements on the home page. This is a common false positive. It should still be checked at widths just above 641 px, where the navigation may wrap and make the header taller.
2. **index.html:85-88:** the `.social` wrapper is `aria-hidden="true"` but contains focusable links. Keyboard users stop on links that screen readers don't announce. This is 4.1.2, outside this audit's scope, but it affects the operable experience. Remove `aria-hidden`.
3. **catalog.html:32:** `role="buton"` is misspelled, so there is no valid role (4.1.2, out of scope). Keyboard operation itself works: it has `tabindex="0"` and Enter/Space handlers (app.js:31-33), so it doesn't fail 2.1.1.
4. **catalog.html:28-29 and SearchBar.jsx:14-22:** the search input has no label, and the icon button has no accessible name (`alt=""`). These fall under 1.1.1, 1.3.1, 3.3.2 and 4.1.2, which are out of scope.
5. **login.html:37:** `onpaste="return false;"` stops password managers and pasting into the PIN field. That is likely a 3.3.8 Accessible Authentication (Minimum) failure (Principle 3, out of scope). The picture CAPTCHA at :45-51 uses the object-recognition exception to 3.3.8. Also, the audio alternative (app.js:117-119) only reveals instructions and never plays any audio.
6. **signup.html:34:** "Full name" has only a placeholder as its label (3.3.2, out of scope). The same email is asked for twice, at :38 and :59, which is likely a 3.3.7 Redundant Entry issue (out of scope).
7. **Events dialog background:** the page behind the dialog isn't made `inert`. It isn't reachable now only because of the trap in #2. When #2 is fixed, add `inert` to `<main>`, `<header>` and `<footer>` while the dialog is open.
8. **Pager link text** ("1"–"5", catalog.html:72-76) gets its context from the `<nav aria-label="Results pages">` label. That's acceptable for 2.4.4. Adding a visually hidden "Page" prefix would still help.

## Manual checks required

- **2.4.11:** tab forwards and backwards through catalog.html at 1280 px and at 700 px wide, and confirm whether the header covers focused elements. Repeat on index.html just above the 640 px breakpoint.
- **General:** after the fixes, do a full keyboard-only walkthrough of all 5 pages and the reservation dialog. Also do a screen-reader smoke test (e.g. NVDA with Firefox, VoiceOver with Safari). Confirm: the dialog is announced and focus stays in it, Escape closes it, the reading-list move buttons announce the new position, and the carousel pause control is announced.

## Not run / not applicable

- `wcag_audit.py`, `wcag_scan.py` and `wcag_page.mjs` were not run, because there is no shell.
- No rendered-browser measurement: target sizes and header height were calculated from the CSS.
- No AT testing.
- Principles 1, 3 and 4 were excluded at your request; the related items above are review notes only.

## Assumptions

- The report uses WCAG 2.2 (W3C Recommendation, 12 December 2024).
- The HTML pages are what users actually get. The React components are unbuilt sources that reproduce the same patterns, so I cited both.
- The pages don't conform to WCAG 2.2 Level AA. Principle 2 criteria that fail: 2.1.1, 2.1.2, 2.2.1, 2.2.2, 2.4.2, 2.4.3, 2.4.4, 2.4.7, 2.5.7 and 2.5.8.
- Because of conformance requirement 3 (complete processes), #8 fails the whole sign-in process, and #2 fails the whole event-reservation process.

## Reproduction

With a shell, run: `python3 ~/.claude/skills/wcag22-a11y/scripts/wcag_audit.py . --url . --out report.md`.

Manual:
1. Open events.html, press Tab to reach "Reserve a seat", and press Enter. Then press Tab repeatedly: focus never leaves "Your name". Press Escape: nothing happens.
2. Open login.html and press Tab once: focus lands on "Continue" first.

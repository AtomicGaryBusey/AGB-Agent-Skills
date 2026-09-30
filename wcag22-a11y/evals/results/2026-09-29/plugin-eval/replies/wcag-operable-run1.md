# WCAG 2.2 Level AA audit, Principle 2 (Operable): Larkspur Library static front end

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js` and `src/components/*.jsx`. I audited against WCAG 2.2 (W3C Recommendation, 12 Dec 2024) at Level AA, limited to the 20 A and AA criteria under Principle 2 (2.1.1 through 2.5.8). I did not use any assistive technology or browser.

**Summary:** 11 nonconformities, 3 deviations, 2 advisories and 7 review notes. Of the 20 criteria, 10 fail, 8 pass (based on reading the code), 1 is N/A and 1 is not evaluated.

**Evidence:** I read all 12 files line by line. I did not run the skill's scanner (`wcag_scan.py`), its page runner (`wcag_page.mjs`) or axe-core, because there is no shell in this environment. I did not do a live keyboard walkthrough or a screen reader test. Every finding comes from reading the code.

The `.jsx` files say "not built", so the shipped HTML and `app.js` are the main targets. I cite the JSX wherever it repeats the same defect, so the fix gets made in both places.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-2.1.2 (also 2.1.1) | WCAG 2.2 SC 2.1.2 (A) | page / component | `app.js:83-92`; `src/components/Modal.jsx:12-20`; `events.html:86-101` | **Keyboard trap in the "Reserve a seat" dialog.** Every Tab press is cancelled and focus goes back to `#res-name`. Escape is also cancelled. The close control is a span that can't be focused. A keyboard user can't reach the email field or the Confirm button, and can't leave the dialog. Criterion 2.1.2 is a non-interference criterion, so this fails every page it appears on. | `keydown`: `if (e.key==='Tab'){e.preventDefault(); …('res-name').focus()}`; `if (e.key==='Escape'){e.preventDefault();}` | Replace the handler with a real focus loop that cycles Tab/Shift+Tab through all focusable elements in `.modal`. Make Escape call `closeModal()`. The same fix applies in `Modal.jsx` (call `onClose` on Escape). |
| 2 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (A) | page / component | `catalog.html:42,50,58,66`; `src/components/BookCard.jsx:15-17` | **"Add to reading list" is a `<div onclick>`.** It isn't in the Tab order and doesn't respond to any key. | `<div class="btn add-btn" … onclick="addToList(this)">`, with no `tabindex`, role or key handler | Use `<button type="button" class="btn add-btn" …>`. |
| 3 | Nonconformity | WCAG-2.1.1 (also 2.5.7) | WCAG 2.2 SC 2.1.1 (A); SC 2.5.7 (AA) | page / component | `catalog.html:81-87`; `app.js:48-65`; `src/components/ReadingList.jsx:20-26` | **The reading list can only be reordered by dragging.** It uses HTML5 drag and drop only. The items can't be focused, and there's no keyboard or single-click alternative. The instruction at `catalog.html:81` says "Drag titles…". | Handlers are `dragstart`, `dragover` and `drop` only; items are `<li draggable="true">` with no controls | Give each item "Move up" and "Move down" buttons (or a position `<select>`), and announce the new position. Update the instruction text. Keep drag as an extra option. |
| 4 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (A) | page / component | `events.html:88`; `src/components/Modal.jsx:30` | **The dialog's close "×" is a `<span onclick>`.** It can't be reached or activated with the keyboard. | `<span class="close" onclick="closeModal()">&times;</span>` | Use `<button type="button" class="close" aria-label="Close">×</button>`. |
| 5 | Nonconformity | WCAG-2.2.1 | WCAG 2.2 SC 2.2.1 (A) | page | `events.html:6` | **The Events page reloads itself every 120 seconds.** The user can't turn this off, change it or extend it. The reload also wipes anything typed in the reservation dialog. No exception applies: the content isn't real-time and the limit isn't essential. | `<meta http-equiv="refresh" content="120">` | Remove the meta refresh. If fresh data is needed, update it in the background without reloading, or give the user a control. |
| 6 | Nonconformity | WCAG-2.2.2 | WCAG 2.2 SC 2.2.2 (A) | page / component | `index.html:34-49`; `app.js:14-17`; `src/components/Carousel.jsx:7-12`; `styles.css:98` | **The "What's new" carousel moves on its own with no way to stop it.** It advances every 4 s indefinitely, alongside other content, with no pause, stop or hide control. It doesn't pause on hover or focus either. This is also a non-interference criterion. | `setInterval(…, 4000)` with no `clearInterval` and no UI controls | Add a visible Pause/Play button. Pause while the carousel has hover or focus, and don't auto-start when `prefers-reduced-motion: reduce` is set. Alternatively, stop after 5 s or show all three items without rotation. |
| 7 | Nonconformity | WCAG-2.4.2 | WCAG 2.2 SC 2.4.2 (A) | page | `catalog.html:3-7` | **The Catalog page has no `<title>`.** | The `<head>` contains only `meta` and `link` | Add `<title>Search the catalog - Larkspur Library</title>`. |
| 8 | Nonconformity | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (A) | page | `login.html:37`, `login.html:40` | **Positive `tabindex` values scramble the sign-in focus order.** The first Tab goes to "Continue" (`tabindex="1"`), then PIN (`tabindex="2"`), then the site header. The card-number field comes only after all the header links. | `tabindex="2"` on `#pin`; `tabindex="1"` on the submit button | Remove both `tabindex` attributes and rely on DOM order. |
| 9 | Nonconformity | WCAG-2.4.4 | WCAG 2.2 SC 2.4.4 (A) | page | `events.html:31-33` | **A "Click here" link sits alone in its paragraph.** Nothing around it explains what it does (it downloads `calendar.ics`). | `<p><a href="calendar.ics">Click here</a></p>` | Use `<a href="calendar.ics">Add all events to your calendar (.ics)</a>`. |
| 10 | Nonconformity | WCAG-2.4.7 | WCAG 2.2 SC 2.4.7 (AA) | stylesheet | `styles.css:59` (affects the main nav on all 5 pages, e.g. `index.html:15-19`) | **Main navigation links have no visible focus indicator.** The outline is removed and nothing replaces it. The `:hover` underline at `styles.css:58` doesn't apply on focus. | `.site-nav a:focus { outline: none; }` | Delete the rule, or replace it with `.site-nav a:focus-visible { outline: 3px solid #fff; outline-offset: -5px; text-decoration: underline; }`. |
| 11 | Nonconformity | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (AA) | stylesheet / page | `styles.css:159-169`; `catalog.html:72-76` | **Pagination links are 16×16 px, spaced 20 px apart.** That is under 24 px, so the spacing exception fails too: 24 px circles on neighbouring targets overlap. The inline, equivalent and essential exceptions don't apply. | `.pager a { width:16px; height:16px; }`, `.pager { gap:4px }` (border-box) | Use `min-width: 24px; min-height: 24px` (44 px recommended) with a readable font size, or `gap: 8px` or more. |
| 12 | Deviation | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (A) | page | `app.js:69-77` | **Closing the dialog doesn't send focus back to the button that opened it.** `closeModal()` only hides the dialog, so focus drops to `<body>` (browser-dependent). The user has to start from the top of the page. Tab still reaches the page behind the dialog (no `inert`), apart from the trap in #1. | `closeModal` sets `modal.hidden = true` only | Store the trigger in `openModal` and call `trigger.focus()` in `closeModal`. Set `inert` on `header`, `main` and `footer` while the dialog is open. Confirm in a browser. |
| 13 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page / stylesheet | `catalog.html:2,8`; `styles.css:19-28` | **On Catalog, focused items may end up completely hidden under the sticky header.** The header is at least 8rem tall and sticky (`body.sticky-page`), but `<html>` lacks the `pad-for-header` class, so there's no `scroll-padding-top`. With Shift+Tab, the browser scrolls a focused result link or button to the top of the viewport, underneath the header. | Compare `index.html:2` (has `class="pad-for-header"`, `scroll-padding-top:14rem`) with `catalog.html:2` (no class) | Add `class="pad-for-header"` to `catalog.html:2`, or move `scroll-padding-top` into a `.sticky-page`-scoped rule on `html` (e.g. `html:has(.sticky-page)`). Confirm by tabbing backwards at a width above 640 px. |
| 14 | Deviation | WCAG-2.4.4 | WCAG 2.2 SC 2.4.4 (A) | page | `events.html:29` → `events.html:56` | **The "access guide" link goes to the wrong place.** It promises parking and hearing-loop details, but its target `#access` is the heading "Room schedule this week", which holds no access information. What the link says it does doesn't match what it does. | `href="events.html#access"`; `<h2 id="access">Room schedule this week</h2>` | Point the link at a real access-guide section or page, or move the `access` id to that content. |
| 15 | Advisory | WCAG-BP-skip-link | Best practice (supports SC 2.4.1) | page | All 5 pages, e.g. `index.html:10`, `catalog.html:9` | There's no skip link, even though `<main id="main">` exists. Criterion 2.4.1 is still met through landmarks (see coverage). But keyboard users have to Tab through the logo area, 5 nav links and the help link on every page. | No `<a href="#main">` anywhere | Add `<a class="skip-link" href="#main">Skip to main content</a>` as the first element in `<body>`, visible on focus. |
| 16 | Advisory | WCAG-2.3.3 | WCAG 2.2 SC 2.3.3 (AAA): not an AA failure | stylesheet | `styles.css:98` | The carousel's slide animation ignores the reduced-motion setting. | `transition: transform 0.6s ease;` with no `prefers-reduced-motion` query | `@media (prefers-reduced-motion: reduce) { .carousel-track { transition: none; } }` |

## SC coverage (Principle 2, Level A + AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #2, #3, #4 (and #1: Confirm can't be reached) |
| 2.1.2 No Keyboard Trap | A | **Fail** | #1 |
| 2.1.4 Character Key Shortcuts | A | Pass (static) | The only key handlers are for Enter, Space, Tab and Escape (`app.js:31-33`, `83-92`). There are no single-character shortcuts or `accesskey` attributes. |
| 2.2.1 Timing Adjustable | A | **Fail** | #5 |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #6 |
| 2.3.1 Three Flashes or Below Threshold | A | Pass (static) | No video, `@keyframes` or SVG animation. The carousel slides once every 4 s, which isn't a flash. |
| 2.4.1 Bypass Blocks | A | Pass (static) | Every page has `<header>`, `<nav aria-label="Main">`, `<main>` and `<footer>` landmarks (ARIA11) plus headings. A skip link would be better (#15). |
| 2.4.2 Page Titled | A | **Fail** | #7. The other 4 titles are present and descriptive. |
| 2.4.3 Focus Order | A | **Fail** | #8 (plus #12 to confirm) |
| 2.4.4 Link Purpose (In Context) | A | **Fail** | #9 (plus #14 to confirm) |
| 2.4.5 Multiple Ways | AA | Pass | The main nav on every page links to all 5 pages (G126). Login and signup steps are exempt as steps in a process. |
| 2.4.6 Headings and Labels | AA | Pass (static) | The headings and labels that exist describe their topic or purpose. Missing labels (`catalog.html:28`, `signup.html:34`) fall under 3.3.2 and 4.1.2, which are out of scope. |
| 2.4.7 Focus Visible | AA | **Fail** | #10 |
| 2.4.11 Focus Not Obscured (Minimum) | AA | Not evaluated | #13 needs a rendered check. For index, see review note 2. |
| 2.5.1 Pointer Gestures | A | Pass (static) | No multipoint or path-based gestures. Dragging is covered under 2.5.7. |
| 2.5.2 Pointer Cancellation | A | Pass (static) | All actions use `click` (the up-event). Drag and drop can be abandoned by dropping outside a target. |
| 2.5.3 Label in Name | A | Pass (static) | No `aria-label` or `aria-labelledby` overrides visible text on any control. The icon-only search button has no visible text label, so 2.5.3 doesn't apply to it. |
| 2.5.4 Motion Actuation | A | N/A | No device-motion or orientation handlers. |
| 2.5.7 Dragging Movements | AA | **Fail** | #3 |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #11. Other targets checked and passing: `.btn-fixed` 112×32 px, `.icon-btn` 40×40 px, `.modal .close` 32×32 px, nav links about 40 px tall, CAPTCHA checkboxes enlarged by their 96 px `<label>`s. Inline text links are exempt. |

## Review notes

1. **Static review only.** "Pass (static)" means I found no failing pattern in the code. It isn't a confirmed pass. None of this is a conformance claim.
2. **2.4.11 on index:** `index.html:2` applies `scroll-padding-top: 14rem` (`styles.css:5`). The header comes to roughly 10–11rem (8rem minimum plus the help bar), so focus is probably not hidden. Confirm by tabbing. Below 640 px the header is static (`styles.css:66-68`), so the issue doesn't arise there.
3. **Pagination link text "1" to "5"** (`catalog.html:72-76`): I treated their purpose as clear from the `aria-label="Results pages"` navigation context and the `aria-current` marker. An `aria-label="Page 2"` on each would remove any doubt.
4. **Sort toggle** (`catalog.html:32`): it is focusable and handles Enter and Space (`app.js:31-33`), so it passes 2.1.1. But `role="buton"` is a typo, so it isn't exposed as a button (4.1.2, out of scope). Use `<button type="button">`.
5. **Social links inside `aria-hidden="true"`** (`index.html:85-88`): they still receive focus but are silent to screen readers. axe classifies this under 4.1.2 (out of scope), but it also makes the focus order confusing. Remove the `aria-hidden`.
6. **JSX sources:** `Modal.jsx`, `Carousel.jsx`, `ReadingList.jsx` and `BookCard.jsx` repeat defects #1–#4 and #6, so fix them before any build replaces the static HTML. `SearchBar.jsx:14-22` repeats the unlabelled search field and unnamed icon button (out of scope).
7. **Problems I saw outside Principle 2** (not graded), each to check in a full audit:
   - **3.3.8:** paste is blocked on the PIN field (`login.html:37`), and the login uses an image or audio CAPTCHA (`login.html:43-55`).
   - **3.3.7:** signup asks for the email address twice (`signup.html:38`, `signup.html:59`).
   - **3.3.2:** a field has only a placeholder as its label (`signup.html:34`).
   - **3.2.6:** on Catalog the help link moves to the footer (`catalog.html:93`).
   - **3.1.1:** there's no `lang` attribute (`events.html:2`).
   - **4.1.3:** the status message has no live region (`catalog.html:34`).
   - **1.4.3:** `.event-meta` text is `#999999` (`styles.css:190`), which fails minimum contrast.
   - **1.4.10:** the fixed 4×240 px grid (`styles.css:107`) forces sideways scrolling on narrow screens.

## Manual checks required

- **Keyboard walk on all 5 pages:** confirm #1, #8, #12 and #13 and the static passes for 2.1.4, 2.4.1 and 2.4.6.
- **2.4.11:** tab forwards and backwards on index and catalog at widths above 640 px.
- **2.5.8:** measure rendered target sizes, including the checkbox and label hit areas in the CAPTCHA.
- **Screen reader smoke test** (e.g. NVDA + Firefox, VoiceOver + Safari): check dialog announcement, focus return and the pagination context.

## Not run / not applicable

- `wcag_audit.py`, `wcag_scan.py`, `wcag_page.mjs` and axe-core were not run because there is no shell. No screenshots.
- Principles 1, 3 and 4 were out of scope.
- 2.5.4 is N/A.
- AAA criteria in Principle 2 were not assessed, except the advisory #16.

## Assumptions

- The five HTML files plus `app.js` are the shipped product. The JSX is unbuilt source that mirrors them.
- The catalog detail pages (`catalog.html?item=…`) and `calendar.ics` weren't provided, so they weren't audited.
- No assistive technology was used.

**Result:** the site does **not conform** to WCAG 2.2 Level AA. It fails criteria 2.1.1, 2.1.2, 2.2.1, 2.2.2, 2.4.2, 2.4.3, 2.4.4, 2.4.7, 2.5.7 and 2.5.8. The sign-in process doesn't fail in full on Principle 2 grounds, but #8 disrupts its first step.

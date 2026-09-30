# WCAG 2.2 Level AA audit, Principle 2 (Operable): Larkspur Library static front end

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js`, and `src/components/{SearchBar,BookCard,Modal,Carousel,ReadingList}.jsx`. The processes checked are sign-in (2 steps), card sign-up (2 steps) and event reservation (the modal). The audit covers the 20 Level A and AA success criteria (SC) in Principle 2. AAA criteria are not included.

**Method:** I read the files and did not run anything. With no shell, neither `wcag_scan.py` nor the axe page runner could run. There was also no rendered keyboard walkthrough and no screen reader testing. Keyboard and focus behaviour was worked out from the markup, CSS and event handlers.

**Summary:** 11 nonconformities, 2 deviations, 2 advisories and 4 review notes. Of the 20 criteria, 10 fail, 8 pass, 1 is N/A and 1 was not evaluated (2.4.11, where failure is likely).

**Result:** The site **does not conform** to WCAG 2.2 Level AA. It fails 2.1.1, 2.1.2, 2.2.1, 2.2.2, 2.4.2, 2.4.3, 2.4.4, 2.4.7, 2.5.7 and 2.5.8. Four of these (2.1.2, 2.2.2 and the rest listed under non-interference below) apply to all content, whether or not users rely on it.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (A) | page, component | `catalog.html:42`, `:50`, `:58`, `:66`; `src/components/BookCard.jsx:15` | The "Add to reading list" controls can't be used with a keyboard. | They are `<div class="btn add-btn" onclick="addToList(this)">` elements with no `tabindex`, no role and no key handler, so Tab never reaches them. | Use `<button type="button" class="btn add-btn" data-title="…">`. In JSX: `<button type="button" className="btn add-btn" onClick={() => onAdd(book)}>`. |
| 2 | Nonconformity | WCAG-2.1.1 | WCAG 2.2 SC 2.1.1 (A) | page, component | `events.html:88`; `src/components/Modal.jsx:30` | The dialog's close control (×) can't be used with a keyboard. | `<span class="close" onclick="closeModal()">&times;</span>` can't receive focus. Escape doesn't close the dialog either (see #3). | Use `<button type="button" class="close" aria-label="Close" onclick="closeModal()">×</button>` and close on Escape. |
| 3 | Nonconformity | WCAG-2.1.2 (also 2.1.1, 2.4.3) | WCAG 2.2 SC 2.1.2 (A) | page, component | `app.js:83-92`; `src/components/Modal.jsx:12-20`; dialog at `events.html:86-101` | The reservation dialog is a keyboard trap. | Every Tab and Shift+Tab calls `preventDefault()` and moves focus back to `#res-name`. Escape is also blocked with `preventDefault()`. A keyboard user can't reach the Email field (`events.html:97`) or Confirm (`:99`), and can't leave. SC 2.1.2 is a non-interference criterion. | Keep Tab cycling through the dialog's focusable elements: from the last go to the first, and with Shift+Tab from the first go to the last. Close the dialog on Escape. Alternatively, use a native `<dialog>` with `showModal()`. |
| 4 | Nonconformity | WCAG-2.1.1 / WCAG-2.5.7 | WCAG 2.2 SC 2.1.1 (A), SC 2.5.7 (AA) | page, component | `catalog.html:81-87`; `app.js:48-65`, `:40`; `src/components/ReadingList.jsx:20-26` | Reading-list items can only be reordered by dragging. | The only handlers are HTML5 `dragstart`, `dragover` and `drop` on `<li draggable="true">`. The items can't take focus, have no key handlers, and there's no single-pointer alternative. The instruction at `:81` says only "Drag titles". | Give each item "Move up" and "Move down" `<button>`s that reorder the list and move focus with the item. Buttons satisfy both SC 2.1.1 and SC 2.5.7. Update the instruction text. |
| 5 | Nonconformity | WCAG-2.2.1 | WCAG 2.2 SC 2.2.1 (A) | page | `events.html:6` | The page reloads every 2 minutes and the user can't turn this off, change it or extend it. | `<meta http-equiv="refresh" content="120">` (failure technique F41). The reload wipes anything typed into the open reservation dialog. | Remove the meta refresh. If the data must stay current, update it with script and offer a pause option or a "Refresh" button. |
| 6 | Nonconformity | WCAG-2.2.2 | WCAG 2.2 SC 2.2.2 (A) | page, component | `app.js:14-17`; `src/components/Carousel.jsx:7-12`; markup `index.html:34-49` | The "What's new" carousel starts moving on its own, runs forever and has no pause, stop or hide control. | `setInterval` advances it every 4000 ms with a 0.6 s slide (`styles.css:98`). It runs alongside the rest of the page. SC 2.2.2 is a non-interference criterion. | Add a visible Pause/Play `<button>`. Also pause on hover and on focus within the carousel, and don't auto-rotate when `prefers-reduced-motion: reduce` is set. Or drop auto-rotation and add Previous/Next buttons. |
| 7 | Nonconformity | WCAG-2.4.2 | WCAG 2.2 SC 2.4.2 (A) | page | `catalog.html:3-7` | The catalog page has no `<title>`. | The `<head>` has only `meta` and `link`. The other four pages have titles such as "Events - Larkspur Library". | Add `<title>Catalog - Larkspur Library</title>`. After a search, use a title like `Results for "…" - Catalog - Larkspur Library`. |
| 8 | Nonconformity | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (A) | page | `login.html:40` (`tabindex="1"`), `login.html:37` (`tabindex="2"`) | Positive `tabindex` values scramble the focus order of the sign-in form. | The actual Tab order is Continue, then PIN, then the five nav links and the help link, then Library card number. So focus reaches the submit button before either field, and reaches the card number last. | Remove both `tabindex` attributes so focus follows the DOM order: card number, PIN, the reset link, then Continue. |
| 9 | Nonconformity | WCAG-2.4.4 | WCAG 2.2 SC 2.4.4 (A) | page | `events.html:32` | "Click here" is the only text for the link to `calendar.ics`. | It sits alone in its own `<p>`, so there is no sentence, list item or description to explain it. | Make the link text say what it is, e.g. `<a href="calendar.ics">Add all events to your calendar (.ics)</a>`. |
| 10 | Nonconformity | WCAG-2.4.7 | WCAG 2.2 SC 2.4.7 (AA) | stylesheet | `styles.css:59`; affects the nav on all 5 pages (e.g. `index.html:15-19`) | Main navigation links show no focus indicator. | `.site-nav a:focus { outline: none; }` has no replacement anywhere: no `:focus-visible` rule, box-shadow, border or background change. Only `:hover` adds an underline (`:58`). White text on `#4b2a7b` looks the same focused or not. | Replace it with `.site-nav a:focus-visible { outline: 3px solid #ffffff; outline-offset: -3px; text-decoration: underline; }`, or delete line 59. |
| 11 | Nonconformity | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (AA) | stylesheet, page | `styles.css:159-169`; `catalog.html:72-76` | The results pager links are too small and too close together. | Each link is 16×16 px (border-box, 11 px text) with a 4 px `gap`, so their centres are 20 px apart. 24 px circles centred on each link overlap (they would need at least 24 px), so the spacing exception doesn't apply. There is no larger equivalent control, and the links aren't inline text. | Use `min-width: 24px; min-height: 24px;` (44 px is better), e.g. `.pager a { min-width: 2.75rem; min-height: 2.75rem; line-height: 2.75rem; font-size: 1rem; }`. |
| 12 | Deviation | WCAG-2.4.3 | WCAG 2.2 SC 2.4.3 (A) | page, component | `app.js:75-77`; `src/components/Modal.jsx:25` | Closing the dialog doesn't return focus to the "Reserve a seat" button that opened it. | `closeModal()` only sets `hidden = true`, and the React version just returns `null`. Focus is then lost to `<body>`, and the next Tab starts from the top of the page. This needs checking in a browser once #2 and #3 are fixed. | In `openModal`, save `document.activeElement`. In `closeModal`, call `.focus()` on it. Do the same with a ref in `Modal.jsx` cleanup. |
| 13 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page, stylesheet | `catalog.html:2` (`<html lang="en">`, no `pad-for-header`); `styles.css:5`, `:19-28` | On the catalog page, the sticky header can cover the focused element completely. | `catalog.html` uses `body.sticky-page`, so the header sticks (`min-height: 8rem`) above 640 px. Unlike `index.html:2`, it lacks the `html.pad-for-header` class that sets `scroll-padding-top: 14rem`. With Shift+Tab, the browser scrolls a focused item (book link, pager link, add button) to the top of the viewport, underneath the header. Not confirmed in a rendered browser. | Add `class="pad-for-header"` to `catalog.html:2`, or put `scroll-padding-top` on `html` for every page using `.sticky-page`. Make the value at least the header's rendered height. |

### Advisories
- **A1. WCAG-BP-link-context, pager (`catalog.html:72-76`):** The links read just "1" to "5". The parent `<nav aria-label="Results pages">` gives screen reader users enough context, so this isn't a failure. `aria-label="Page 2"` (and so on) would make the purpose clear everywhere.
- **A2. WCAG-BP-modal-open-focus (`app.js:73`):** Focus goes to the first field when the dialog opens, which passes. Once #3 is fixed, check that the Tab cycle includes the new close button.

## SC coverage (Principle 2, A + AA)

| SC | Level | Status | Notes |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #1, #2, #3, #4. The sort toggle `catalog.html:32` is focusable and handles Enter and Space (`app.js:31-33`), so it passes this criterion. |
| 2.1.2 No Keyboard Trap | A | **Fail** | #3 |
| 2.1.4 Character Key Shortcuts | A | Pass | The only key handlers are Enter/Space on the sort toggle and Tab/Escape in the dialog. There are no single-character shortcuts. |
| 2.2.1 Timing Adjustable | A | **Fail** | #5 |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #6 |
| 2.3.1 Three Flashes or Below Threshold | A | Pass | No video. The SVGs have no animation, SMIL or script. The carousel slides; it doesn't flash. |
| 2.4.1 Bypass Blocks | A | Pass | Every page has `<nav aria-label="Main">` and `<main id="main">` landmarks and headings, which are sufficient techniques. A skip link to `#main` would still help sighted keyboard users. |
| 2.4.2 Page Titled | A | **Fail** | #7 |
| 2.4.3 Focus Order | A | **Fail** | #8 (plus #3). Deviation #12. |
| 2.4.4 Link Purpose (In Context) | A | **Fail** | #9 |
| 2.4.5 Multiple Ways | AA | Pass | On this 5-page site, every page's nav links to every page, and the home page links to all of them. This counts as nav plus a home page acting as a site map. The login and sign-up steps belong to processes and are exempt. |
| 2.4.6 Headings and Labels | AA | Pass | The headings and labels that exist describe their topic or purpose. Missing labels are a Principle 1 and 3 issue (see Review notes). |
| 2.4.7 Focus Visible | AA | **Fail** | #10 |
| 2.4.11 Focus Not Obscured (Minimum) | AA | Not evaluated (likely fail) | Deviation #13. It needs a rendered Tab and Shift+Tab test. |
| 2.5.1 Pointer Gestures | A | Pass | No multipoint or path-based gestures. The carousel has no swipe. |
| 2.5.2 Pointer Cancellation | A | Pass | Every action fires on `click` (the up-event). Dropping a dragged item outside the list cancels the move. |
| 2.5.3 Label in Name | A | Pass | Controls with visible text take their name from that text. The search button has only an icon, so the criterion doesn't apply to it. |
| 2.5.4 Motion Actuation | A | N/A | No device-motion or orientation input. |
| 2.5.7 Dragging Movements | AA | **Fail** | #4 |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #11. Other targets checked pass: `.icon-btn` 40 px; `.btn-fixed` 112×32 px; modal close 32 px; nav links about 40 px tall; captcha checkboxes, which have large wrapping labels as equivalents. |

## Review notes
1. **Non-interference:** SC 2.1.2 (#3) and SC 2.2.2 (#6) apply to every page, even content users don't rely on. So the events page and home page can't conform until these are fixed, whatever other fixes are made.
2. **Complete processes:** Event reservation (#3, #5) and sign-in (#8) fail. Under conformance requirement 3, a failure at one step fails every page in the process.
3. **Index sticky header (SC 2.4.11):** `index.html:2` has `scroll-padding-top: 14rem`, which should clear the header (`min-height` 8rem, taller with the help bar). Below 640 px the header is static (`styles.css:66-68`). No finding for the home page, but confirm it with the page runner.
4. **Out of scope (other WCAG principles), noted but not graded:**
   - Controls without accessible names or labels: the search input and icon button (`catalog.html:28-29`, `SearchBar.jsx:14-22`), and the full-name field, which has only a placeholder (`signup.html:34`).
   - `role="buton"` typo at `catalog.html:32`.
   - Focusable links inside `aria-hidden="true"` at `index.html:85-88` (4.1.2).
   - Paste blocked on the PIN field (`login.html:37`) and an image CAPTCHA whose audio alternative has no audio (`login.html:45-53`). Both are SC 3.3.8 issues.
   - Email asked for twice in sign-up (`signup.html:38` and `:59`, SC 3.3.7).
   - Help link placed in the footer on the catalog page but in the header elsewhere (SC 3.2.6).
   - Missing `lang` at `events.html:2`.
   - Low-contrast `#999999` and `#c9b6ef` text.
   - Fixed 4×240 px grid (`styles.css:107`, SC 1.4.10).
   - Cover images without `alt` text.

## Manual checks required
- **SC 2.4.11:** Tab and Shift+Tab through `catalog.html` at a width of at least 641 px and confirm whether the header hides the focused element. Repeat on `index.html` to confirm the fix there works.
- **Rendered keyboard walkthrough of all 5 pages:** confirm the static conclusions for SC 2.1.1, 2.1.2, 2.4.3 and 2.4.7. Also confirm the default focus rings on `.btn`, `.sort-toggle` and `.table-scroll` are visible against their backgrounds.
- **SC 2.5.8:** measure the rendered pager boxes (the static value is 16 px).

## Not run / not applicable
- `wcag_scan.py`, `wcag_page.mjs` (axe-core) and `wcag_audit.py` were not run because there is no shell.
- No browser rendering, no assistive technology and no zoom or reflow testing.
- The React components are marked "not built", so I checked them as source that mirrors the HTML.
- SC 2.5.4 is N/A.

## Assumptions
- The static HTML is the shipped version. The JSX files are the source for the same behaviour, so each finding cites both.
- Default Chromium and Firefox focus rings are assumed to be visible wherever the author hasn't overridden them.
- No screen reader was used. A smoke test with NVDA and Firefox, or VoiceOver and Safari, should confirm three things: how the reservation dialog is announced, where focus goes after it closes, and that `aria-current` is read on the nav and pager.

## Reproduction
Static review only. To reproduce, open each file at the line cited, then run in a browser with a keyboard. On `events.html`, activate "Reserve a seat" and press Tab or Escape: focus stays in "Your name" (#3). On `login.html`, press Tab from the top of the page: focus lands on "Continue" first (#8). Once a shell is available, run `python3 $S/wcag_audit.py . --url . --pages 5 --out report.md` to add tool evidence.

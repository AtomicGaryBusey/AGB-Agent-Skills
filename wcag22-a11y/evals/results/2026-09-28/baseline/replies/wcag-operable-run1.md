# WCAG 2.2 Level AA audit: Larkspur Library static front end (Principle 2, Operable)

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js`, and `src/components/*.jsx` (these are unbuilt sources that mirror the HTML). The audit covers the 20 Level A and AA success criteria (SC) under Principle 2. It also covers two processes: sign-in (step 1, then step 2) and getting a card (signup step 1, then step 2).

**Method:** static review of the source only. No tools, browser or screen reader were run.

**Summary:** 12 nonconformities, 1 deviation, 1 advisory, 7 review notes. Of the 20 SC, 10 fail, 7 pass, 2 are N/A and 1 is not evaluated.

**Conformance:** the site **does not conform** to WCAG 2.2 Level AA. It fails 2.1.1, 2.1.2, 2.2.1, 2.2.2, 2.4.2, 2.4.3, 2.4.4, 2.4.7, 2.5.7 and 2.5.8. The keyboard trap (2.1.2), the auto-refresh (2.2.1) and the moving carousel (2.2.2) are non-interference SC, so they would block conformance even for content nobody relies on.

## Findings

Rows are ordered by severity, then by SC.

| # | Severity | SC (Level) | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|
| 1 | Nonconformity | **2.1.2 No Keyboard Trap (A)**; also 2.1.1 (A) | `app.js:83-92`; `src/components/Modal.jsx:12-20` | The reservation dialog traps keyboard users. Every Tab goes back to "Your name", so "Email" and "Confirm" can never be reached. Escape is caught and does nothing. | `app.js:85-88`: when the key is Tab, it calls `preventDefault()` and focuses `#res-name`. `app.js:89-91`: Escape only calls `preventDefault()`. The fields are not in a `<form>`, so Enter does nothing. The only other way out is the close control, which can't take focus (#2). | Cycle focus through the dialog's focusable elements instead: Tab from the last one goes to the first, Shift+Tab from the first goes to the last. Make Escape call `closeModal()` / `onClose()`. Or use `<dialog>` with `showModal()`, which does both. |
| 2 | Nonconformity | **2.1.1 Keyboard (A)** | `events.html:88`; `src/components/Modal.jsx:30` | The dialog's "×" close control is a `<span onclick>`. The keyboard can't reach it or activate it. | No `tabindex`, no role and no key handler. | Use `<button type="button" class="close" aria-label="Close">×</button>`. |
| 3 | Nonconformity | **2.1.1 Keyboard (A)** | `catalog.html:42,50,58,66`; `src/components/BookCard.jsx:15` | The "Add to reading list" controls are `<div class="btn" onclick>`. Keyboard users can't add titles. | They have a click handler only: no `tabindex`, no role, no key handler. | Use `<button type="button" class="btn add-btn">`. |
| 4 | Nonconformity | **2.5.7 Dragging Movements (AA)**; also **2.1.1 (A)** | `catalog.html:81-87`; `app.js:47-65`; `src/components/ReadingList.jsx:17-31` | The reading list can only be reordered by drag and drop. There is no single-pointer way to do it and no keyboard way. | The instructions say "Drag titles to put them in the order…". Only `dragstart`/`dragover`/`drop` listeners exist, and the `li` items can't take focus. | Add "Move up" and "Move down" buttons to each item, or a "Move to position" menu. That fixes both SC. |
| 5 | Nonconformity | **2.2.1 Timing Adjustable (A)** | `events.html:6` | The page reloads every 2 minutes, and the user can't turn this off, adjust it or extend it. A reload also throws away anything typed into the reservation dialog. | `<meta http-equiv="refresh" content="120">`. None of the exceptions apply (not real-time, not essential, not over 20 hours). | Remove the meta refresh. If fresh data is needed, update it in place and give the user a way to pause or turn off updates. |
| 6 | Nonconformity | **2.2.2 Pause, Stop, Hide (A)** | `app.js:8-18`; `src/components/Carousel.jsx:7-12`; `index.html:34-49`; `styles.css:96-99` | The "What's new" carousel starts on its own, advances every 4 s forever, and runs alongside other content. There is no pause, stop or hide control. | `setInterval(…, 4000)` is never cleared. Slides move with a 0.6 s transform transition. | Add a visible Pause/Play button before the carousel. Also pause on hover and focus, and respect `prefers-reduced-motion`. Alternatively, don't auto-advance. |
| 7 | Nonconformity | **2.4.2 Page Titled (A)** | `catalog.html:3-7` | The catalog page has no `<title>`. | The `<head>` contains only `meta` and `link`. | Add `<title>Search the catalog - Larkspur Library</title>`. |
| 8 | Nonconformity | **2.4.3 Focus Order (A)** | `login.html:37`, `login.html:40` | Positive `tabindex` values scramble the sign-in order. Focus goes to "Continue" (`tabindex="1"`) first, then PIN (`tabindex="2"`), then the header links, and only then to the card number field. That is before the user has filled in anything. | The browser orders all positive `tabindex` values ahead of every `tabindex=0` element on the page. | Remove both `tabindex` attributes. The DOM order is already correct. |
| 9 | Nonconformity | **2.4.3 Focus Order (A)** | `app.js:75-77`; `src/components/Modal.jsx:25` | Closing the dialog doesn't send focus back to the "Reserve a seat" button that opened it. Focus is left on an element that is now hidden, so it falls back to `<body>` or to wherever the dialog sits in the DOM, after `<main>`. | `closeModal()` only sets `hidden = true`. The React version returns `null` and doesn't restore focus. This is a known failure pattern (F85). | Save `document.activeElement` when the dialog opens and call `.focus()` on it when it closes. |
| 10 | Nonconformity | **2.4.4 Link Purpose (In Context) (A)** | `events.html:32` | The link "Click here" (to `calendar.ics`) sits alone in its own paragraph, so nothing around it explains where it goes. | `<p><a href="calendar.ics">Click here</a></p>` | Use descriptive text, e.g. "Add all events to your calendar (.ics)". |
| 11 | Nonconformity | **2.4.7 Focus Visible (AA)** | `styles.css:59`; affects the main nav on all 5 pages (e.g. `index.html:15-19`) | The focus outline is removed from the main navigation links and nothing replaces it. | `.site-nav a:focus { outline: none; }`. The only other style is an underline on `:hover` (`styles.css:58`), so no `:focus-visible`, border, shadow or colour change appears on focus. | Delete that line, or add `.site-nav a:focus-visible { outline: 3px solid #fff; outline-offset: -3px; }` (or similar). |
| 12 | Nonconformity | **2.5.8 Target Size (Minimum) (AA)** | `styles.css:159-169`; `catalog.html:71-77` | The results pager links are 16×16 px, 4 px apart. They don't qualify for the spacing exception, and there is no other full-size pager on the page. | `*, *::before, *::after { box-sizing: border-box }` (`styles.css:2`) keeps the rendered box at 16×16 px. Centres are 20 px apart, so 24 px circles around each target overlap. | Make each link at least 24×24 px, e.g. `min-width: 2.75rem; min-height: 2.75rem; line-height: 2.75rem;`. |
| 13 | Deviation | **2.4.11 Focus Not Obscured (Minimum) (AA)** | `styles.css:5`, `styles.css:25-28`; `catalog.html:2`, `catalog.html:8` | The catalog page has a sticky header (`body.sticky-page`, at least 8rem / 128 px tall) but no `scroll-padding-top`, because `<html>` doesn't have the `pad-for-header` class. When tabbing backwards (Shift+Tab), the browser scrolls the focused element to the top of the viewport, where the header can cover it completely. Small targets like the pager links (16 px) and the "Add" buttons are most at risk. | This is based on the code only; it wasn't confirmed in a browser. The home page does use `scroll-padding-top: 14rem`. Below 640 px the header stops being sticky (`styles.css:66-68`). | Add `class="pad-for-header"` to `catalog.html:2`, or set `scroll-padding-top` on every `.sticky-page`. Then confirm with Shift+Tab at widths above 640 px. |
| 14 | Advisory | 2.4.1 best practice (`WCAG-BP-skip-link`) | every page, before `<header>` | There is no "Skip to main content" link. 2.4.1 is still met because the pages have `<header>`, `<nav>` and `<main>` landmarks. But sighted keyboard users have to Tab through 5 nav links plus the help link on every page. | `main#main` already exists on every page. | Make `<a class="skip-link" href="#main">Skip to main content</a>` the first element in `<body>`, visible when it has focus. |

## SC coverage (Principle 2, Levels A and AA)

"Pass" means a pass on static review only; see "Manual checks required".

| SC | Level | Status | Notes |
|---|---|---|---|
| 2.1.1 Keyboard | A | **Fail** | #2, #3, #4, and the unreachable dialog fields in #1 |
| 2.1.2 No Keyboard Trap | A | **Fail** | #1 |
| 2.1.4 Character Key Shortcuts | A | N/A | No single-key shortcuts; the only key handlers are Enter/Space on the sort toggle and Tab/Escape in the dialog |
| 2.2.1 Timing Adjustable | A | **Fail** | #5 |
| 2.2.2 Pause, Stop, Hide | A | **Fail** | #6 |
| 2.3.1 Three Flashes or Below | A | Pass | Nothing flashes; the carousel slides every 4 s |
| 2.4.1 Bypass Blocks | A | Pass | Landmarks are present (#14 is advisory) |
| 2.4.2 Page Titled | A | **Fail** | #7 (the other four titles are descriptive) |
| 2.4.3 Focus Order | A | **Fail** | #8, #9 |
| 2.4.4 Link Purpose (In Context) | A | **Fail** | #10 |
| 2.4.5 Multiple Ways | AA | Pass | Small 5-page site; every page has a nav listing all pages (see review note 5) |
| 2.4.6 Headings and Labels | AA | Pass | Headings and labels that exist are descriptive; missing labels are outside Principle 2 |
| 2.4.7 Focus Visible | AA | **Fail** | #11 |
| 2.4.11 Focus Not Obscured (Minimum) | AA | Not evaluated | #13 is an open deviation that needs a browser check; the home page looks OK (review note 3) |
| 2.5.1 Pointer Gestures | A | Pass | No multi-finger or path-based gestures; dragging is covered under 2.5.7 |
| 2.5.2 Pointer Cancellation | A | Pass | All actions use `click` (fires on release); no `mousedown`/`pointerdown` handlers |
| 2.5.3 Label in Name | A | Pass | Controls with visible text get their name from that text; the icon-only search button is N/A for this SC |
| 2.5.4 Motion Actuation | A | N/A | No device-motion input |
| 2.5.7 Dragging Movements | AA | **Fail** | #4 |
| 2.5.8 Target Size (Minimum) | AA | **Fail** | #12. The other targets are big enough or exempt: nav links about 40 px tall, `.btn-fixed` 112×32, `.icon-btn` 40×40, CAPTCHA labels about 104 px, dialog close 32×32; the help bar and fine-print links are inline in sentences |

## Review notes

1. **Link to the access guide goes to the wrong place** (`events.html:29` → `events.html:56`). The link promises "details on parking and hearing loops", but `#access` is the "Room schedule this week" heading. The link text itself is clear, so this doesn't fail 2.4.4, but it's a content defect: either add the access guide or fix the target.
2. **Pager links "1"–"5"** (`catalog.html:71-77`). The purpose is clear from `<nav aria-label="Results pages">` and matches the usual pattern. I'm treating it as a 2.4.4 pass. Adding `aria-label="Page 2"` would be more robust.
3. **Home page sticky header** (`styles.css:5`, `index.html:2`). `scroll-padding-top: 14rem` appears to be taller than the header (about 10–13rem, depending on whether the nav wraps). Confirm with Shift+Tab at 641–1024 px widths before recording 2.4.11 as a pass on this page.
4. **Social links are hidden from screen readers but still focusable** (`index.html:85-88`). Keyboard users get focus stops that screen readers announce as nothing. This fails 4.1.2 (outside this scope) and makes the focus order confusing. Remove `aria-hidden`.
5. **2.4.5 pass depends on site size.** If catalog item pages (`catalog.html?item=…`) or other pages are added outside the nav, a second way to find pages is needed, such as site search or a site map.
6. **Sort toggle** (`catalog.html:32`, `app.js:21-34`). It works with the keyboard (it has `tabindex="0"` and handles Enter/Space), so it passes 2.1.1. However, `role="buton"` is a typo, so assistive technology won't announce it as a button (4.1.2, outside scope). Change it to a real `<button>`.
7. **The React sources aren't built.** Their findings are reported alongside the matching HTML rows. If they ship, each fix has to be made in both places.

## Other issues noticed (outside Principle 2, not graded)

These came up during the review, so you may want to schedule them:

- 3.3.8: paste is blocked on the PIN field (`login.html:37`), and the login has an image CAPTCHA.
- 3.3.7: signup asks for the email address twice (`signup.html:38`, `signup.html:59`).
- 3.2.6: the help link is in the footer on the catalog page (`catalog.html:93`) but in the header on the other pages.
- 3.3.2: the full-name field has a placeholder instead of a label (`signup.html:34`).
- 4.1.3: `#list-status` has no live region (`catalog.html:34`).
- 1.1.1: book covers have no `alt` (`catalog.html:38` and others, `BookCard.jsx:7`); the flourish divider has `alt` text even though it's decorative (`index.html:30`).
- 1.4.3: the logo text `#c9b6ef` on white and `.event-meta` `#999999` fail contrast.
- 3.1.1: `events.html` has no `lang` attribute.
- 1.4.10: `.featured-row` uses fixed `repeat(4, 240px)` columns.
- 1.3.1: headings skip a level (`index.html:78` is an `h4`).

## Manual checks required

These are needed before any conformance statement:

- **2.4.11:** Shift+Tab through `catalog.html` (and `index.html`) at widths above 640 px with the sticky header showing.
- **Keyboard walk-through of all 5 pages** in a real browser: confirm the static passes for 2.4.3, 2.4.7 and 2.1.1, and the default focus rings on `.btn` (purple background) and the table's scroll region.
- **2.3.1:** watch the rendered carousel transition.
- **2.5.8:** measure the rendered target boxes, especially whether "Reserve a seat" fits in 112 px or gets clipped.
- **Re-test after fixes:** the dialog (Tab cycling, Escape, focus returned) and the reading-list reorder buttons.

## Not run

- `wcag_scan.py` / `wcag_audit.py` / `wcag_page.mjs`: no shell was available.
- Screen reader and assistive-technology testing.
- Rendered-page measurements and zoom/reflow checks.

## Assumptions

- The HTML files are what gets deployed. The `.jsx` files are unbuilt sources and are reviewed as equivalents.
- Default Chromium/Firefox styles apply where the site's CSS doesn't override them.
- Principles 1, 3 and 4 were out of scope; the notes above are informational only.

## Reproduction

1. **#1, #2, #9:** open `events.html`, activate "Reserve a seat", then press Tab repeatedly. Focus stays on "Your name". Press Escape: nothing happens.
2. **#8:** open `login.html` and press Tab once. Focus lands on "Continue".
3. **#11:** open any page and Tab into the main nav. No focus indicator appears.
4. **#6:** open `index.html` and wait 4 s. The carousel advances with no way to pause it.
5. **#5:** open `events.html` and wait 120 s. The page reloads.

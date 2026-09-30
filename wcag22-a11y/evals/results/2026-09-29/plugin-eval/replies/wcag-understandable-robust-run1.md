# WCAG 2.2 Level AA audit: Larkspur Library static front end (Principles 3 and 4 only)

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `app.js`, `styles.css`, and `src/components/*.jsx`. The processes covered are signing in (2 steps), getting a card (2 steps), reserving an event seat (dialog) and adding to the reading list. The audit checks Level AA but only success criteria (SC) 3.x and 4.x. That is 15 active SC, plus 4.1.1 Parsing, which is obsolete.

**Method:** I read every file listed above and reviewed them statically. No shell was available, so I did not run `wcag_scan` or `wcag_page`. I did not render any page, use a browser or test with assistive technology.

**Summary:** 13 nonconformities, 1 deviation, 1 advisory, 7 review notes. Of the 15 SC: 9 fail, 5 pass (from the source only), 1 N/A, 0 not evaluated.

**Conformance:** the site does **not conform** to WCAG 2.2 Level AA. Failing SC in scope: 3.1.1, 3.2.6, 3.3.1, 3.3.2, 3.3.3, 3.3.7, 3.3.8, 4.1.2, 4.1.3. (It also fails SC outside this audit's scope; see "Outside scope" below.)

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-3.1.1 | WCAG 2.2 SC 3.1.1 (A) | page | `events.html:2` | The page's language can't be determined by software. | `<html>` has no `lang`. The other four pages have `lang="en"`. | `<html lang="en">` |
| 2 | Nonconformity | WCAG-3.2.6 | WCAG 2.2 SC 3.2.6 (A) | page | `catalog.html:93` (compare `index.html:22`, `events.html:23`, `login.html:22`, `signup.html:22`) | The "Need help?" contact block is in a different place relative to other content on the catalog page. | On four pages `.help-bar` is inside the header, before `<main>`. On the catalog page it's in the footer, after `<main>`. | Move `<p class="help-bar">` into `.header-inner` after the `<nav>`, as on the other pages. |
| 3 | Nonconformity | WCAG-3.3.1 (also 3.3.3) | WCAG 2.2 SC 3.3.1 (A), 3.3.3 (AA) | page + script | `app.js:102-106`, `styles.css:250`, `signup.html:30` | Sign-up step 1 errors are shown only as a red border. The field with the error isn't described in text, and no correction is suggested. | `f.classList.add('invalid')` only, with no message text, no `aria-invalid` and no `aria-describedby`. `novalidate` turns off the browser's own messages. `type="email"` format is never checked, so no suggestion like "Enter an email such as name@example.com" is possible. | For each invalid field, set `aria-invalid="true"` and add an error `<p id="full-name-err">Enter your full name</p>` linked with `aria-describedby`. Validate email format and give a correction hint. Move focus to the first invalid field or to an error summary. |
| 4 | Nonconformity | WCAG-3.3.2 | WCAG 2.2 SC 3.3.2 (A) | page | `signup.html:34` | The Full name field has no label. Its only instruction is placeholder text, which disappears when the user starts typing. | `<input id="full-name" … placeholder="Full name (required)">` has no `<label>`. (The placeholder is also very low contrast, `#aaa` at `styles.css:249`; that is SC 1.4.3, outside this audit's scope.) | Add `<label for="full-name">Full name (required)</label>` and remove the placeholder. |
| 5 | Nonconformity | WCAG-3.3.2 (also 4.1.2) | WCAG 2.2 SC 3.3.2 (A), 4.1.2 (A) | page + component | `catalog.html:28`, `src/components/SearchBar.jsx:14-19` | The catalog search field has no visible label and no accessible name. | `<input type="search" id="q">` has no `<label>`, `aria-label`, `title` or placeholder. | `<label for="q">Search the catalog</label>`. Visually hide it if the design needs that, but a visible label is better. |
| 6 | Nonconformity | WCAG-3.3.7 | WCAG 2.2 SC 3.3.7 (A) | page | `signup.html:58-59` | Step 2 asks again for an email address the user already entered in step 1 (`signup.html:38`). It isn't filled in automatically and can't be selected. | `#card-email` starts empty, and `app.js:107-109` only moves focus to it. Confirming the PIN (`:67`) is allowed, because the security exception covers it. | Pre-fill `#card-email` from `#email` when moving to step 2, or replace it with a "Send card notices to the same email" checkbox that is checked by default. |
| 7 | Nonconformity | WCAG-3.3.8 | WCAG 2.2 SC 3.3.8 (AA) | page | `login.html:37` | The PIN field blocks pasting and dropping. This stops password managers and copy-paste, so the user has to recall and type a memorised PIN (a cognitive function test). | `onpaste="return false;" ondrop="return false;"`. `autocomplete="current-password"` is set, but that doesn't help when paste is blocked. | Remove both `onpaste` and `ondrop`. |
| 8 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page + component | `catalog.html:29`, `src/components/SearchBar.jsx:20-22` | The search submit button has no accessible name. | The button's only content is `<img … alt="">`, so screen readers announce just "button". | Use `alt="Search"` on the image, or `aria-label="Search"` on the `<button>`. |
| 9 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page | `catalog.html:32` | The sort toggle has an invalid role, so assistive technology gets no button role. | `role="buton"` is a typo and isn't a valid ARIA role, so the element is exposed as generic text. | Use `<button type="button" id="sort-toggle" class="sort-toggle">Title A–Z</button>`. Then the `keydown` handler at `app.js:31-33` is no longer needed. Consider adding `aria-pressed` or a visible label such as "Sort: Title A–Z". |
| 10 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page + component | `catalog.html:42, 50, 58, 66`; `src/components/BookCard.jsx:15-17` | The "Add to reading list" controls are clickable `<div>`s. They have no role, and they can't be reached by keyboard (SC 2.1.1, outside this audit's scope). | `<div class="btn add-btn" onclick="addToList(this)">` has no `role` and no `tabindex`. | Use `<button type="button" class="btn add-btn" …>`. Also consider an accessible name that includes the book title, e.g. `aria-label="Add The Orchard to reading list"`. |
| 11 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page + component | `events.html:88`, `src/components/Modal.jsx:30` | The dialog's close control is a `<span>` with a click handler. It has no button role, its name is just "×", and it can't be focused. | `<span class="close" onclick="closeModal()">&times;</span>` | `<button type="button" class="close" aria-label="Close" onclick="closeModal()">×</button>` |
| 12 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page | `index.html:85-88` | Keyboard-focusable links sit inside an `aria-hidden` container. They get focus, but screen readers announce no name or role for them. | `<div class="social" aria-hidden="true">` wraps two `<a href>` links (the axe rule `aria-hidden-focus` checks for this pattern). | Remove `aria-hidden="true"`. |
| 13 | Nonconformity | WCAG-4.1.3 | WCAG 2.2 SC 4.1.3 (AA) | page + script | `app.js:44`, `catalog.html:34` | The "Added … to your reading list" confirmation is written into a region that isn't a live region, so screen readers don't announce it. | `#list-status` is a plain `<div>` with no `role="status"` or `aria-live`. `ReadingList.jsx` and `BookCard.jsx` have no status message at all. | `<div id="list-status" role="status"></div>`. Add the same to the React version. |
| 14 | Deviation | WCAG-3.3.1 | WCAG 2.2 SC 3.3.1 (A), 3.3.3 (AA) | page | `signup.html:30, 55-70` | Step 2 of sign-up isn't validated before submitting. A PIN that isn't 4 digits, PINs that don't match, or an empty field go straight to `login.html` with no error. Pressing Enter in a step 1 field may also submit the form and skip the step 1 check. | `novalidate` is set, and there is no submit handler in `app.js`. The action goes to a static page. I couldn't confirm server-side handling. | Add a submit handler that validates all fields, including PIN length and match, and reports errors as in finding #3. Handle Enter in step 1 so it runs the Next step instead. |
| 15 | Advisory | WCAG-BP-announce-sort | related to 4.1.3 | page | `app.js:24-29` | Re-sorting the results isn't announced beyond the toggle's own text changing. | The list is reordered in the DOM without any message. | After fixing #9, add a `role="status"` message such as "Sorted by title Z to A". |

## SC coverage (Principles 3 and 4, Level A + AA)

| SC | Level | Status | Notes |
|---|---|---|---|
| 3.1.1 Language of Page | A | **Fail** | #1 |
| 3.1.2 Language of Parts | AA | Pass (static) | No passages in another language found. "Tai chi" is an everyday English loanword. |
| 3.2.1 On Focus | A | Pass (static) | No focus handlers change context. The dialog moves focus only after a click. |
| 3.2.2 On Input | A | Pass (static) | No change or input handlers change context. |
| 3.2.3 Consistent Navigation | AA | Pass (static) | The main nav has the same 5 links in the same order on all pages. |
| 3.2.4 Consistent Identification | AA | Pass (static) | Repeated components ("Reserve a seat", "Ask a Librarian", nav) are labelled the same everywhere. |
| 3.2.6 Consistent Help | A | **Fail** | #2 |
| 3.3.1 Error Identification | A | **Fail** | #3, #14 |
| 3.3.2 Labels or Instructions | A | **Fail** | #4, #5 |
| 3.3.3 Error Suggestion | AA | **Fail** | #3 |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | N/A | See review note 3. |
| 3.3.7 Redundant Entry | A | **Fail** | #6 |
| 3.3.8 Accessible Authentication (Minimum) | AA | **Fail** | #7 |
| 4.1.1 Parsing | — | Obsolete in 2.2 | Not assessed. |
| 4.1.2 Name, Role, Value | A | **Fail** | #5, #8, #9, #10, #11, #12 |
| 4.1.3 Status Messages | AA | **Fail** | #13 |

## Review notes

1. **3.3.8 image CAPTCHA** (`login.html:45-51`): "Select every picture that shows a book" is an object-recognition test, which the SC explicitly allows at AA, so it isn't a 3.3.8 failure. However, the "audio check" button (`login.html:52`, `app.js:117-119`) only reveals instructions and plays no audio. That is a 1.1.1 issue, outside this audit's scope.
2. **3.3.8 card number** (`login.html:33`): `autocomplete="username"` lets the browser fill it in and paste isn't blocked, so this field is fine. The failure is only the PIN (#7).
3. **3.3.4 N/A:** getting a free library card and reserving a free seat don't create legal or financial commitments, and they don't change or delete user data in the SC's sense. If the card application includes accepting terms of use, re-assess: a review step before "Create my card" would then be needed.
4. **Full name field's accessible name** (`signup.html:34`): the placeholder does supply an accessible name in most browsers, so I recorded this under 3.3.2 (#4) rather than as a 4.1.2 failure.
5. **Event reservation dialog** (`events.html:99`): "Confirm" just closes the dialog. Nothing is submitted, nothing is validated and no confirmation is given. If it is later wired to a real submission, it will need error handling (3.3.1/3.3.3) and a success status message (4.1.3).
6. **React sources** in `src/components/` are marked "not built". I audited them as the future source of the same pages, and they repeat defects #5, #8, #10, #11 and #13.
7. **No assistive-technology testing.** Before relying on the passes above, a screen-reader test (e.g. NVDA + Firefox, VoiceOver + Safari) should confirm:
   - the names and roles of the search button, sort toggle, add buttons and dialog close button after the fixes;
   - that `#list-status` is announced;
   - that sign-up error messages are read out.

## Outside scope: seen in passing, not audited

These are outside Principles 3 and 4 and weren't audited, but they affect conformance. Items marked † fall under the non-interference requirement, so they would stop the site conforming no matter what else is fixed.

- **2.1.2 †** The dialog traps the keyboard. Tab is forced back to `#res-name` and Escape does nothing (`app.js:83-92`, `Modal.jsx:12-20`).
- **2.2.2 †** The carousel rotates automatically with no pause control (`app.js:14-17`, `Carousel.jsx:7-12`).
- **2.2.1** The events page refreshes itself every 120 seconds (`events.html:6`), which would wipe anything typed into the dialog.
- **2.4.2** `catalog.html` has no `<title>`.
- **2.1.1 / 2.5.7** The reading list can only be reordered by dragging (`catalog.html:83-86`, `ReadingList.jsx`).
- **1.1.1** Cover images have no `alt` (`catalog.html:38/46/54/62`, `BookCard.jsx:7`). The decorative flourish has descriptive alt text instead (`index.html:30`).
- **2.4.3** `login.html:37, 40` use positive `tabindex` values (1 and 2), which disrupts the focus order.
- **2.4.4** "Click here" link at `events.html:32`.
- **2.4.7** Nav links remove the focus outline (`styles.css:59`).
- **2.5.8** Pager links are 16×16 px (`styles.css:160-169`).
- **1.4.3** Low-contrast text: the logo `#c9b6ef` and `.event-meta` `#999`.
- **1.4.10 / 1.4.12** The featured grid has a fixed width (`styles.css:107`), and `.btn-fixed` clips its text (`styles.css:191-199`).

## Assumptions

- Static review only: no pages were rendered, no scripts were run and no assistive technology was used.
- Server behaviour for form submissions is unknown. Every `action` points to another static page.

## Reproduction

Open each HTML file in a browser and check the line references above. For #13, tab to an "Add to reading list" control after fixing #10, or click it now, with a screen reader running: no announcement is made. For #3, leave the step 1 fields empty on `signup.html` and press "Next": only the borders turn red.

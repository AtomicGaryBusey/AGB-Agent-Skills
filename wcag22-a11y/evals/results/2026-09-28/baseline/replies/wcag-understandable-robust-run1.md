# WCAG 2.2 Level AA audit: Larkspur Library static front end, Principles 3 and 4

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `app.js`, `styles.css`, and `src/components/*.jsx` (the component sources aren't built; they are the source for the HTML pages).
**Processes:** sign in (card and PIN → CAPTCHA), get a card (step 1 → step 2), reserving a seat for an event, adding a book to the reading list and reordering it.
**Level:** AA, limited to the Principle 3 and 4 criteria: 3.1.1, 3.1.2, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.6, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 3.3.7, 3.3.8, 4.1.2 and 4.1.3. That is 15 criteria. 4.1.1 Parsing is obsolete in WCAG 2.2 and is not assessed.
**Method:** I read the source files only. No shell was available, so `wcag_scan`, `wcag_page`/axe-core, a browser and a screen reader were not run. No assistive technology (AT) or browser was used.
**Summary:** 13 nonconformities, 1 deviation (inside finding 4), 3 advisories, 7 review notes. Of the 15 criteria, **9 fail**, 5 pass (static review only), 1 is N/A and none are unevaluated.
**Result:** The site **does not conform** to WCAG 2.2 Level AA. The failing criteria in scope are 3.1.1, 3.2.6, 3.3.1, 3.3.2, 3.3.3, 3.3.7, 3.3.8, 4.1.2 and 4.1.3. Principles 1 and 2 were outside this audit and also have failures (see "Outside scope").

## Findings

Findings are listed by severity, then by criterion. A finding marked "confirmed from source" is certain from the code alone. It has not been checked with a screen reader.

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-3.1.1 | WCAG 2.2 SC 3.1.1 (Level A) | page | `events.html:2` | The page doesn't declare its language. | `<html>` has no `lang` attribute. The other four pages have `lang="en"`. | `<html lang="en">` |
| 2 | Nonconformity | WCAG-3.2.6 | WCAG 2.2 SC 3.2.6 (Level A) | page | `catalog.html:93` (compare `index.html:22`, `events.html:23`, `login.html:22`, `signup.html:22`) | The "Need help?" block (Ask a Librarian link and phone number) is in the header on four pages but in the footer on the catalog page. Its position relative to other content changes. | `.help-bar` is inside `.header-inner` on 4 pages and inside `<footer>` on the catalog page. | Move it into `.header-inner` after `</nav>` on the catalog page, as on the other pages. |
| 3 | Nonconformity | WCAG-3.3.1 (also 3.3.3) | WCAG 2.2 SC 3.3.1 (Level A); SC 3.3.3 (Level AA) | template | `app.js:103`, `styles.css:250`, `signup.html:30` | When "Next" is pressed with required fields empty, the only sign of an error is a red border. There's no error text, nothing tells the user how to fix it, and screen readers get nothing. | `f.classList.add('invalid')` only changes the border colour to `#c62828`. No text, no `aria-invalid`, no `aria-describedby`, and focus stays on "Next". | For each invalid field: set `aria-invalid="true"`, add text such as `<p id="street-err">Enter your street address.</p>` and link it with `aria-describedby`, then move focus to the first invalid field or to an error summary. |
| 4 | Nonconformity | WCAG-3.3.2 (also 4.1.2, Deviation) | WCAG 2.2 SC 3.3.2 (Level A) | page | `signup.html:34` | The Full name field has no label. Its only label is placeholder text, which disappears when the user types (and is pale grey, `#aaa`). Screen readers only get a name from the placeholder as a last-resort fallback, which some screen readers don't support reliably (4.1.2 Deviation). | `<input id="full-name" placeholder="Full name (required)">` with no `<label>`. | Add `<label for="full-name">Full name (required)</label>` and remove the placeholder. |
| 5 | Nonconformity | WCAG-3.3.2 (also 4.1.2) | WCAG 2.2 SC 3.3.2 (Level A); SC 4.1.2 (Level A) | page, component | `catalog.html:28`; `src/components/SearchBar.jsx:14-19` | The catalog search field has no visible label and no accessible name. | `<input type="search" id="q">` has no `<label>`, `aria-label`, `title` or placeholder. The name is empty. | Add `<label for="q">Search the catalog</label>` (visible or visually hidden). Mirror the change in `SearchBar.jsx`. |
| 6 | Nonconformity | WCAG-3.3.7 | WCAG 2.2 SC 3.3.7 (Level A) | page | `signup.html:59` (compare `signup.html:38`) | Step 2 asks for the email address again even though it was entered in step 1. It is neither filled in automatically nor offered as a choice. | `#card-email` starts empty. `app.js:107-109` shows step 2 without copying `#email`. | Pre-fill `#card-email` from `#email`, or add a "Same as my email above" checkbox, or remove the field. Re-typing the PIN (`confirm-pin`) is allowed as an exception and is fine. |
| 7 | Nonconformity | WCAG-3.3.8 | WCAG 2.2 SC 3.3.8 (Level AA) | page | `login.html:37` | Paste and drop are blocked in the PIN field. This stops password managers and copy-paste, so users have to recall and type the PIN (a cognitive function test). | `onpaste="return false;" ondrop="return false;"` | Remove both handlers. Keep `autocomplete="current-password"`. |
| 8 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page, component | `catalog.html:29`; `src/components/SearchBar.jsx:20-22` | The search submit button has no accessible name. | The button's only content is `<img alt="">`, so its name is empty and it is announced as just "button". | `<img src="images/icon-search.svg" alt="Search">`, or add `aria-label="Search"` to the button. |
| 9 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page | `catalog.html:32` | The sort toggle's role is misspelled, so screen readers aren't told it is a button. | `role="buton"` is not a valid role, so the element is exposed as plain text (a generic element). | Use `<button type="button" id="sort-toggle" class="sort-toggle">Title A–Z</button>` and remove the manual keydown handler at `app.js:31-33`. |
| 10 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page, component | `catalog.html:42, 50, 58, 66`; `src/components/BookCard.jsx:15-17` | The "Add to reading list" controls are plain `div`s with click handlers. They have no role and can't be reached with the keyboard. | `<div class="btn add-btn" onclick="addToList(this)">` with no role and no `tabindex`. | Use `<button type="button" class="btn add-btn" …>`. |
| 11 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page, component | `events.html:88`; `src/components/Modal.jsx:30` | The dialog's close control is a `span` showing "×". It has no role, no meaningful name and can't be focused. | `<span class="close" onclick="closeModal()">&times;</span>` | `<button type="button" class="close" aria-label="Close">&times;</button>` |
| 12 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page | `index.html:85-88` | The footer social links can still be tabbed to but are hidden from screen readers. Keyboard users land on links that are announced with no name or role. | `<div class="social" aria-hidden="true">` wraps 2 `<a href>` links (axe rule `aria-hidden-focus`). | Remove `aria-hidden="true"`. |
| 13 | Nonconformity | WCAG-4.1.3 | WCAG 2.2 SC 4.1.3 (Level AA) | page | `catalog.html:34`; `app.js:44` | The "Added … to your reading list" message is inserted into a container that isn't a live region, so screen readers don't announce it. | `<div id="list-status"></div>` has no `role="status"` or `aria-live`. `app.js:44` sets its `textContent`. | `<div id="list-status" role="status"></div>` |
| A1 | Advisory | WCAG-3.2.5 | WCAG 2.2 SC 3.2.5 (Level AAA) | page | `events.html:6` | The page reloads itself every 120 seconds, which is a change of context the user didn't ask for. This also fails 2.2.1 (Level A), which is outside this scope. | `<meta http-equiv="refresh" content="120">` | Remove it, or give the user a control to refresh. |
| A2 | Advisory | WCAG-3.3.9 | WCAG 2.2 SC 3.3.9 (Level AAA) | page | `login.html:45-51` | The image CAPTCHA ("select every picture that shows a book") is allowed at AA under the object-recognition exception, but that exception doesn't exist at AAA. | Object-recognition CAPTCHA. | Use a non-interactive bot check (for example, a server-side risk signal) or email or passkey verification. |
| A3 | Advisory | WCAG-BP-form-error-summary | Best practice | template | `signup.html:30` | The form uses `novalidate` but has no error summary and no validation for step 2 (see review note R3). | Only step 1 is validated, in `app.js:99-110`. | Add an error summary at the top of the form that receives focus, and validate step 2 (empty fields, PIN is 4 digits, the two PINs match). |

## SC coverage

"Static review" means I read the source only. Nothing was checked in a rendered page or with AT.

| SC | Level | Status | Notes |
|---|---|---|---|
| 3.1.1 Language of Page | A | **Fail** | #1 |
| 3.1.2 Language of Parts | AA | Pass (static review) | No passages in another language found. |
| 3.2.1 On Focus | A | Pass (static review) | No handler changes context when an element receives focus. The modal opens on click (`app.js:81`). |
| 3.2.2 On Input | A | Pass (static review) | No `change` or `input` handlers change context. Forms submit only through buttons. |
| 3.2.3 Consistent Navigation | AA | Pass (static review) | Main navigation is identical and in the same order on all 5 pages. |
| 3.2.4 Consistent Identification | AA | Pass (static review) | Repeated components (navigation, "Reserve a seat", help links) have consistent labels. |
| 3.2.6 Consistent Help | A | **Fail** | #2 |
| 3.3.1 Error Identification | A | **Fail** | #3 |
| 3.3.2 Labels or Instructions | A | **Fail** | #4, #5 |
| 3.3.3 Error Suggestion | AA | **Fail** | #3. A missing required field has an obvious fix ("enter X"), but none is given. |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | N/A | See R4. |
| 3.3.7 Redundant Entry | A | **Fail** | #6 |
| 3.3.8 Accessible Authentication (Minimum) | AA | **Fail** | #7 |
| 4.1.1 Parsing | — | Obsolete | Removed in WCAG 2.2. Not assessed. |
| 4.1.2 Name, Role, Value | A | **Fail** | #5, #8, #9, #10, #11, #12 (plus the deviation in #4) |
| 4.1.3 Status Messages | AA | **Fail** | #13 |

## Review notes

- **R1 (3.3.8, CAPTCHA), `login.html:45-53`:** The image CAPTCHA falls under the object-recognition exception, so it doesn't fail at AA. However, the audio alternative doesn't work. `app.js:117-119` only reveals instruction text (`login.html:53`) and never plays any audio. This isn't a Principle 3/4 failure, but it is likely a 1.1.1 failure. Also, the image alt texts "CAPTCHA picture 1–4" (`login.html:47-50`) don't say what the pictures show.
- **R2 (sign-in process), `login.html:29-55`:** Both steps are visible at the same time, and they are separate forms with different `action` URLs. Nothing handles errors in step 1, such as a wrong card number or PIN. Server behaviour is unknown, so 3.3.1 was only evaluated for errors detected on the page.
- **R3 (3.3.1), `signup.html:30, 55-70`:** Because of `novalidate`, step 2 is submitted without any checks: empty required fields and mismatched PINs aren't caught on the page. 3.3.1 only applies to errors that are detected automatically, so this isn't recorded as a failure. If the server does detect these errors, its error page must meet 3.3.1 and 3.3.3.
- **R4 (3.3.4 N/A):** Getting a library card and reserving a free event seat don't create legal commitments or financial transactions, and don't change or delete user data in the sense of 3.3.4. Re-check this if the card application includes agreeing to terms.
- **R5 (events reservation), `events.html:99`:** The "Confirm" button only calls `closeModal()`. Nothing is submitted and no confirmation is shown. Once reservations actually work, the confirmation message must meet 4.1.3.
- **R6 (4.1.2, carousel), `index.html:34-49`, `src/components/Carousel.jsx`:** Slides that are off-screen are still exposed to screen readers. This doesn't fail 4.1.2, but the auto-rotation with no pause control fails 2.2.2, which is outside this scope.
- **R7 (React sources):** The components in `src/components/` aren't built, and each one has the same defects as the HTML it produces (findings #5, #8, #10, #11). Fix both the components and the static HTML.

## Manual checks required

The list is empty for the purposes of this static audit. Before relying on these results, check them in a browser with a screen reader (for example NVDA + Firefox and VoiceOver + Safari):

- the announcements for findings #8–#13 once fixed;
- the placeholder-only name in finding #4;
- whether the help block is in a consistent position at narrow widths (≤640px, where the header stops being sticky), for 3.2.6.

## Outside scope (Principles 1–2, not audited; recorded so they aren't lost)

- **Keyboard trap (2.1.2, non-interference):** `app.js:85-88` and `src/components/Modal.jsx:13-16` force every Tab press back to the first field, and Escape does nothing. Keyboard users can't leave the dialog. This fails conformance for the whole page regardless of the other criteria.
- **Timing (2.2.1):** `events.html:6` (meta refresh).
- **Moving content (2.2.2):** `app.js:14-17` (the carousel rotates automatically with no pause).
- **Keyboard access and dragging (2.1.1 / 2.5.7):** the div controls, and the reading list at `catalog.html:81-87` / `ReadingList.jsx`, which can only be reordered by dragging.
- **Focus order (2.4.3):** positive `tabindex` at `login.html:37, 40`, and focus isn't returned after the modal closes.
- **Visible focus (2.4.7):** `styles.css:59` sets `outline: none`.
- **Page title (2.4.2):** `catalog.html` has no `<title>`.
- **Link purpose (2.4.4):** "Click here" at `events.html:32`.
- **Text alternatives (1.1.1):** `catalog.html:38, 46, 54, 62` and `BookCard.jsx:7` have no `alt`. `index.html:30` gives a decorative image descriptive alt text.
- **Info and relationships (1.3.1):** `index.html:78` jumps from h2 to h4.
- **Contrast (1.4.3):** `.event-meta` `#999999` (`styles.css:190`).
- **Non-text contrast (1.4.11):** `#d6d6d6` input borders (`styles.css:247`).
- **Reflow (1.4.10):** `styles.css:107`.
- **Text spacing (1.4.12):** `styles.css:191-199`.
- **Target size (2.5.8):** 16px pager links (`styles.css:160-169`).

## Assumptions

- Only the files listed in the scope were reviewed.
- Server-side behaviour for the form actions is unknown.
- The React components are treated as the source for the static pages.

## Reproduction

Open each file at the cited line. With a shell, run `python3 ~/.claude/skills/wcag22-a11y/scripts/wcag_audit.py . --url . --out report.md`. axe-core should independently flag #1 (`html-has-lang`), #5 (`label`), #8 (`button-name`), #9 (`aria-roles`) and #12 (`aria-hidden-focus`).

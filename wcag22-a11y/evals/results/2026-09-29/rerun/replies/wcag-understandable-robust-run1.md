# WCAG 2.2 Level AA audit: Larkspur Library static front end, Principles 3 and 4

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js`, `src/components/*.jsx` (Carousel, SearchBar, BookCard, ReadingList, Modal). The JSX files say they are the unbuilt sources for these pages, so their findings are reported against the component.
**Processes:** sign-up (step 1 → step 2), sign-in (card/PIN → CAPTCHA), event reservation (dialog), reading list (add, reorder).
**Level:** AA, limited to Principles 3 and 4. That is 15 success criteria (SC): 3.1.1, 3.1.2, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.6, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 3.3.7, 3.3.8, 4.1.2, 4.1.3. SC 4.1.1 Parsing is obsolete in WCAG 2.2 and was not assessed.
**Method:** I read every file in scope by hand. No tools, browser or assistive technology were used.
**Summary:** 13 nonconformities, 1 deviation, 2 advisories, 5 review notes. Of the 15 SC: 9 fail, 5 pass (from reading the code, still to be confirmed at runtime), 1 needs a decision (3.3.4), 0 N/A.

**Result:** The site does **not conform** to WCAG 2.2 Level AA. These SC fail: 3.1.1, 3.2.6, 3.3.1, 3.3.2, 3.3.3, 3.3.7, 3.3.8, 4.1.2, 4.1.3.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-3.1.1 | WCAG 2.2 SC 3.1.1 (Level A) | page | `events.html:2` | The page's language can't be determined by software. | `<html>` has no `lang` attribute. The other four pages have `lang="en"`. | `<html lang="en">` |
| 2 | Nonconformity | WCAG-3.2.6 | WCAG 2.2 SC 3.2.6 (Level A) | page | `catalog.html:93` (compare `index.html:22`, `events.html:23`, `login.html:22`, `signup.html:22`) | The help mechanism is not in the same relative order on every page. On four pages the "Ask a Librarian"/phone help bar is in the header, after the main nav and before `<main>`. On the catalog page it moves to the footer, after all main content. | The `p.help-bar` is inside `.header-inner` on 4 pages and inside `.site-footer` on catalog. | Move the help bar in `catalog.html` into `.header-inner` after the `<nav>`, as on the other pages. |
| 3 | Nonconformity | WCAG-3.3.1 | WCAG 2.2 SC 3.3.1 (Level A); also 3.3.3 (AA) | page / script | `app.js:100-105`, `styles.css:250`, `signup.html:30` | **(a)** When a sign-up step 1 field is empty, the only signal is a red border (`.invalid`, `#c62828`). There is no text saying which field is wrong or what to do, and no `aria-invalid`. **(b)** Step 2 is never validated. The form has `novalidate`, and the submit button posts to `login.html` even if the email is invalid, the PIN is not 4 digits, or the two PINs don't match. None of these errors is identified or given a suggestion (3.3.3). | `f.classList.add('invalid')` is the only error output. No error text nodes exist. There is no submit handler for `#step-2`. | For each invalid field: set `aria-invalid="true"`, add an error message such as "Enter your full name" and link it with `aria-describedby`, then move focus to the first invalid field. Add a submit handler that checks email format, `^\d{4}$` for the PIN, and that the two PINs match, with specific messages (e.g. "PINs don't match – type the same 4 digits twice"). |
| 4 | Nonconformity | WCAG-3.3.2 | WCAG 2.2 SC 3.3.2 (Level A); related 4.1.2 | page | `signup.html:34` | The "Full name" field has no label, only placeholder text. The placeholder disappears once the user types. Its accessible name comes only from the browser's placeholder fallback. | `<input id="full-name" … placeholder="Full name (required)">` has no `<label for>`. The placeholder is `#aaaaaa`. | Add `<label for="full-name">Full name (required)</label>` and remove the placeholder. Also add `autocomplete="name"`. |
| 5 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A); also 3.3.2 | page / component | `catalog.html:28`, `src/components/SearchBar.jsx:14-19` | The catalog search field has no label, no instructions and no accessible name. | `<input type="search" id="q">` has no `<label>`, `aria-label` or placeholder. | `<label for="q">Search the catalog</label>`. It can be visually hidden only if the visible heading clearly acts as the label. Otherwise make it visible. |
| 6 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page / component | `catalog.html:29`, `src/components/SearchBar.jsx:20-22` | The search submit button has no accessible name. Its only content is an image with `alt=""`, so it is announced as just "button". | `<button …><img src="images/icon-search.svg" alt=""></button>` | Use `alt="Search"` on the image, or `aria-label="Search"` on the button. |
| 7 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page | `catalog.html:32` | The sort toggle's role is misspelled (`role="buton"`). This is not a valid ARIA role, so the focusable span is exposed as generic text, not as a control. | `<span class="sort-toggle" role="buton" tabindex="0">`. The Enter/Space handler is at `app.js:31-33`. | Use `<button type="button" id="sort-toggle">`. If you keep a span, use `role="button"`. Also give the control a name that states its function, e.g. "Sort: Title A–Z". |
| 8 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page / component | `catalog.html:42, 50, 58, 66`; `src/components/BookCard.jsx:15-17` | The "Add to reading list" controls are `<div onclick>` elements. They have no role, can't receive focus and have no keyboard handling. | `<div class="btn add-btn" … onclick="addToList(this)">` | `<button type="button" class="btn add-btn" …>`. To make each button unique, add the title, e.g. `aria-label="Add The Orchard to reading list"` or visually hidden text. |
| 9 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page / component | `events.html:88`; `src/components/Modal.jsx:30` | The dialog's close control is a `<span onclick>` with no role. Its name is "×" ("times"), and it can't receive focus. | `<span class="close" onclick="closeModal()">&times;</span>` | `<button type="button" class="close" aria-label="Close">×</button>` |
| 10 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page | `index.html:85-88` | The social links are inside an `aria-hidden="true"` container but can still receive focus. Keyboard users land on links that screen readers don't announce. | `<div class="social" aria-hidden="true"><a href=…>Mastodon</a><a …>Photos</a></div>` | Remove `aria-hidden`. The links are real content. |
| 11 | Nonconformity | WCAG-3.3.7 | WCAG 2.2 SC 3.3.7 (Level A) | page | `signup.html:58-59` (compare `signup.html:37-38`) | In the same sign-up process, step 2 asks for the email address again ("Email address for card notices") after it was entered in step 1. It is not auto-filled and there is no option to reuse it. None of the exceptions (essential, security, or previous entry no longer valid) applies. The PIN confirmation at line 66 is covered by the security exception. | `#card-email` starts empty. `app.js:107-109` only moves focus to it. | Pre-fill `#card-email` from `#email`, or offer a "Same as my email address" checkbox (checked by default). Or drop the field. |
| 12 | Nonconformity | WCAG-3.3.8 | WCAG 2.2 SC 3.3.8 (Level AA) | page | `login.html:37` | The PIN field blocks paste and drop. Users can't paste from a password manager or clipboard, so they have to recall and transcribe the PIN (a cognitive function test). There is no alternative method. | `onpaste="return false;" ondrop="return false;"` | Remove `onpaste` and `ondrop`. Keep `autocomplete="current-password"`. |
| 13 | Nonconformity | WCAG-4.1.3 | WCAG 2.2 SC 4.1.3 (Level AA) | page / script | `catalog.html:34`, `app.js:44` | The "Added '…' to your reading list." message is written into a plain `<div>`. It isn't a live region, so screen readers don't announce it, and focus doesn't move. | `<div id="list-status"></div>` has no `role` or `aria-live`. | `<div id="list-status" role="status"></div>`. Add a matching status region in the React tree next to `BookCard`'s `onAdd`. |
| 14 | Deviation | WCAG-3.3.1 | WCAG 2.2 SC 3.3.1 (Level A); related 4.1.3 | page / script | `events.html:99`, `app.js:75-77` | The reservation dialog's "Confirm" button only closes the dialog. It doesn't check the name or email and gives no success or error feedback. If these fields are required (likely, for a reservation), empty or invalid input is silently accepted. | `onclick="closeModal()"`. No validation or status output. | Validate the fields, show text errors linked with `aria-describedby`, and announce success (e.g. "Seat reserved for Fix-it Cafe") in a `role="status"` region. |
| 15 | Advisory | WCAG-3.3.9 | WCAG 2.2 SC 3.3.9 (Level AAA) | page | `login.html:45-50` | The picture CAPTCHA ("select every picture that shows a book") is an object-recognition test. The object-recognition exception lets it pass 3.3.8 at AA, but it fails the AAA 3.3.9. | Image-selection CAPTCHA in the sign-in step. | Use a non-cognitive check (e.g. a server-side risk check or an emailed link) where possible. |
| 16 | Advisory | WCAG-3.2.5 | WCAG 2.2 SC 3.2.5 (Level AAA) | page | `events.html:6` | The page reloads itself every 120 seconds. This changes context without the user asking, and it wipes anything typed in the reservation dialog. Also a Level A failure of 2.2.1, which is outside this scope; see Review notes. | `<meta http-equiv="refresh" content="120">` | Remove the meta refresh. If the data must stay current, update it in place or offer a "Refresh" button. |

## SC coverage

| SC | Level | Status | Basis |
|---|---|---|---|
| 3.1.1 Language of Page | A | **Fail** | #1 |
| 3.1.2 Language of Parts | AA | Pass (static) | No text in another language found. |
| 3.2.1 On Focus | A | Pass (static) | No focus handlers change context. The dialog opens on click (`app.js:81`). |
| 3.2.2 On Input | A | Pass (static) | No change or input handlers change context. The checkboxes and fields have no side effects. |
| 3.2.3 Consistent Navigation | AA | Pass (static) | Main nav is identical and in the same order on all 5 pages. Footer extras on the home page are additions, not reordering. |
| 3.2.4 Consistent Identification | AA | Pass (static) | Nav labels, "Reserve a seat" and "Add to reading list" are consistent. Recheck after fixing #6 and #9. |
| 3.2.6 Consistent Help | A | **Fail** | #2 |
| 3.3.1 Error Identification | A | **Fail** | #3; #14 needs confirmation |
| 3.3.2 Labels or Instructions | A | **Fail** | #4, #5 |
| 3.3.3 Error Suggestion | AA | **Fail** | #3(b) |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | Needs decision | See Review note 1 |
| 3.3.7 Redundant Entry | A | **Fail** | #11 |
| 3.3.8 Accessible Authentication (Minimum) | AA | **Fail** | #12 (the CAPTCHA itself passes via the object-recognition exception) |
| 4.1.1 Parsing | — | Obsolete in 2.2 | Not assessed |
| 4.1.2 Name, Role, Value | A | **Fail** | #5–#10 |
| 4.1.3 Status Messages | AA | **Fail** | #13; related #14 |

## Review notes

1. **3.3.4 on sign-up.** Creating a library card may be a legal commitment, for example accepting borrowing terms and liability for lost items. If so, the sign-up process needs a way to review, confirm or correct before submitting. Right now step 2 submits straight away and there is no review step. The library needs to decide whether card creation counts. If it does, 3.3.4 fails. Neither the event reservation nor the reading-list reorder looks like a legal, financial or data commitment that can't be reversed.
2. **Audio CAPTCHA alternative** (`login.html:52-53`, `app.js:117-119`). The button only reveals instructions. No audio exists and nothing happens next, so the alternative is not actually available. This doesn't change the 3.3.8 result (the image test is covered by the object-recognition exception). It is a serious 1.1.1 issue, outside this scope, for users who can't see the images. The image alt text ("CAPTCHA picture 1" …) also doesn't meet 1.1.1's CAPTCHA requirements.
3. **The dialog traps the keyboard (non-interference, SC 2.1.2).** Outside Principles 3 and 4, but it affects conformance of the whole page. In `app.js:83-92` and `Modal.jsx:12-20`, Tab always goes back to the name field, and Escape is swallowed. The email field, Confirm button and close control can't be reached by keyboard, and there is no way out. Under conformance requirement 5, this alone means `events.html` can't conform.
4. **Reading list** (`catalog.html:81-87`, `app.js:48-60`, `ReadingList.jsx`). Items can only be reordered by dragging (2.5.7 and 2.1.1, outside scope). If you add keyboard or button reordering, announce each move ("The Glass Canal moved to position 1") through a `role="status"` region to meet 4.1.3.
5. **Static review only.** No assistive technology or browser was used. A screen-reader check should confirm:
   - Name and role for the search field and button, sort toggle, add buttons and dialog close (after fixes).
   - That the status in #13 is announced.
   - That signup error text is announced.
   - That focus lands on the dialog heading or first field.

   The "Pass (static)" statuses above for 3.1.2 and 3.2.1–3.2.4 are from reading the code and should be confirmed in a browser.

## Out-of-scope issues seen during the review (not graded)

- **2.2.1:** meta refresh, `events.html:6`.
- **2.2.2:** carousel auto-rotates with no pause, `app.js:14-17`, `Carousel.jsx:7-12`.
- **2.4.2:** no `<title>`, `catalog.html` head.
- **1.1.1:**
  - Cover images have no `alt`: `catalog.html:38,46,54,62`, `BookCard.jsx:7`.
  - Decorative flourish has descriptive alt text: `index.html:30`.
- **2.4.3:** positive `tabindex`, `login.html:37,40`.
- **2.4.7:** `outline: none` on nav links, `styles.css:59`.
- **2.5.8:** pager targets are 16×16 px, `styles.css:160-163`.
- **1.4.3:** `.event-meta` text `#999` on white is about 2.8:1, `styles.css:190`.
- **1.4.10:** fixed 4×240 px grid, `styles.css:107`.
- **1.4.4 / 1.4.12:** fixed-height buttons clip their text, `styles.css:191-199`.
- **2.4.4:** "Click here" link, `events.html:32`.
- **1.3.1:**
  - Heading jumps from h2 to h4: `index.html:78`.
  - Event titles are `<p>`, not headings: `events.html:36`.

## Assumptions

- The report uses WCAG 2.2 (W3C Recommendation, 12 December 2024), so 4.1.1 is treated as obsolete. A policy that cites WCAG 2.0 or 2.1 (Section 508, EN 301 549) would still require 4.1.1.
- The React components are the sources for the matching static pages and will ship with the same markup patterns.
- Server-side behaviour (login and signup error pages, reservation handling) wasn't available and wasn't evaluated. Error handling on those pages must also meet 3.3.1 and 3.3.3.

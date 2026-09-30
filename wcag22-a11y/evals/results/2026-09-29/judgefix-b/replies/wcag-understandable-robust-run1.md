# WCAG 2.2 Level AA audit: Larkspur Library static front end (Principles 3 and 4 only)

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js` and `src/components/*.jsx` (SearchBar, BookCard, Modal, Carousel, ReadingList). The processes are sign-up (2 steps), sign-in (card and PIN, then CAPTCHA) and event reservation (modal). The target is Level AA, restricted as you asked to the 15 active success criteria in Principles 3 and 4. 4.1.1 is obsolete. The tools were none (static source review only), and no assistive technology or browsers were used.

**Summary:** 12 nonconformities, 2 deviations, 2 advisories, 3 review notes. Of the 15 criteria: 9 fail, 5 pass, 0 N/A, 1 not evaluated.

**Evidence:** I read every file in scope line by line. `wcag_scan` and `wcag_page` were not run because there is no shell. There was no keyboard walkthrough, no rendered check and no screen-reader test.

**Result:** The pages **do not conform** to WCAG 2.2 Level AA. The failing criteria are 3.1.1, 3.2.6, 3.3.1, 3.3.2, 3.3.3, 3.3.7, 3.3.8, 4.1.2 and 4.1.3. This audit covers Principles 3 and 4 only, so it can't support a conformance claim either way.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-3.1.1 | WCAG 2.2 SC 3.1.1 (Level A) | page | `events.html:2` | The page has no language set, so the default human language can't be determined. | `<html>` has no `lang` attribute. The other four pages have `lang="en"`. | `<html lang="en">` |
| 2 | Nonconformity | WCAG-3.2.6 | WCAG 2.2 SC 3.2.6 (Level A) | page | `catalog.html:93` (compare `index.html:22`, `events.html:23`, `login.html:22`, `signup.html:22`) | The "Need help? Ask a Librarian / call" block moves. On catalog it is in the footer. On index, events, login and signup it is in the header, after the main nav. Its position relative to other page content therefore changes. | `p.help-bar` sits in `footer.site-footer` on catalog and in `.header-inner` everywhere else. | Move the help bar in `catalog.html` into `.header-inner` after `</nav>`, as on the other pages. |
| 3 | Nonconformity | WCAG-3.3.1 | WCAG 2.2 SC 3.3.1 (Level A); also breaks 3.3.3 (AA) | page / script | `app.js:100-106`, `styles.css:250`, `signup.html:30` | **Sign-up errors:** when a required step-1 field is empty, the only signal is a red border (`.invalid { border-color:#c62828 }`). There is no error text, no `aria-invalid`, and focus does not move. Users therefore get no text identifying the error or suggesting a correction (3.3.3). **Step 2** uses `novalidate` and has no JS check, so an empty or mismatched PIN is not caught at all. | `f.classList.add('invalid')` is the only error output. No element receives an error message. | For each invalid field, set `aria-invalid="true"` and add `aria-describedby` pointing to a text error (e.g. "Enter your postal code"). Move focus to the first invalid field or to an error summary. Validate step 2 on submit, including "PINs do not match" and "PIN must be 4 digits". |
| 4 | Nonconformity | WCAG-3.3.2 | WCAG 2.2 SC 3.3.2 (Level A); also breaks 4.1.2 (A) | page / component | `catalog.html:28`; `src/components/SearchBar.jsx:14-19` | The catalog search field has no label, visible or programmatic, and no placeholder. Its accessible name is empty. | `<input type="search" id="q" name="q">` has no `<label for="q">`, no `aria-label` and no `title`. | Add `<label for="q">Search the catalog</label>`. It may be visually hidden, because the `<h1>` gives visible context. |
| 5 | Nonconformity | WCAG-3.3.7 | WCAG 2.2 SC 3.3.7 (Level A) | page | `signup.html:58-59` (compare `signup.html:37-38`) | Step 2 asks for "Email address for card notices" even though the email was already entered in step 1 of the same process. It is neither auto-filled nor selectable. No exception applies: an email address is not essential re-entry or security content. | `#card-email` is empty when step 2 opens (`app.js:107-109`). | Prefill `#card-email` from `#email` when step 2 opens, or offer a "Same as above" checkbox. (Re-entering the PIN at `signup.html:66-67` is allowed as a security exception.) |
| 6 | Nonconformity | WCAG-3.3.8 | WCAG 2.2 SC 3.3.8 (Level AA) | page | `login.html:37` | The PIN field blocks paste and drop. Users who rely on password managers or copy and paste must then remember or transcribe the PIN, which is a cognitive function test with no alternative. | `onpaste="return false;" ondrop="return false;"` | Remove both handlers. Keep `autocomplete="current-password"`. |
| 7 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page / component | `catalog.html:29`; `src/components/SearchBar.jsx:20-22` | The search submit button has no accessible name. Its only content is an image with `alt=""`. | A `<button>` containing `<img alt="">` has an empty name. | `<img src="images/icon-search.svg" alt="Search">`, or `aria-label="Search"` on the button. |
| 8 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page | `catalog.html:32` | The sort toggle has a misspelled role, `role="buton"`. That is not a valid ARIA role, so the element is exposed as generic text with no button role. | `<span class="sort-toggle" role="buton" tabindex="0">` | Use `<button type="button" id="sort-toggle">Sort: Title A–Z</button>` and drop the manual Enter/Space handler at `app.js:31-33`. |
| 9 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page / component | `catalog.html:42, 50, 58, 66`; `src/components/BookCard.jsx:15-17` | "Add to reading list" controls are `<div>`s with click handlers. They have no role, and they also can't be focused (a 2.1.1 issue, outside scope). | `<div class="btn add-btn" onclick="addToList(this)">` | `<button type="button" class="btn add-btn" data-title="…">Add to reading list</button>`. Adding the book title to the name is a best practice, e.g. `aria-describedby` pointing to the `h2`. |
| 10 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page / component | `events.html:88`; `src/components/Modal.jsx:30` | The modal close control is a `<span>` with `onclick`. It has no role and its only content is "×", which screen readers read as "times" or "multiplication". | `<span class="close" onclick="closeModal()">&times;</span>` | `<button type="button" class="close" aria-label="Close">&times;</button>` |
| 11 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (Level A) | page | `index.html:85-88` | `aria-hidden="true"` is on a container holding two focusable links. Keyboard users can tab to them, but screen readers announce nothing (no name or role). | `<div class="social" aria-hidden="true"><a href=…>Mastodon</a>…` | Remove `aria-hidden` from `.social`. If the block is really meant to be hidden, give it `hidden` instead. |
| 12 | Nonconformity | WCAG-4.1.3 | WCAG 2.2 SC 4.1.3 (Level AA) | page / script | `catalog.html:34`; `app.js:44` | The "Added '…' to your reading list." message is written into a plain `<div>`, so screen readers don't announce it. | `#list-status` has no `role="status"` or `aria-live`. | `<div id="list-status" role="status"></div>` (it must be in the DOM before the text is inserted, which it is). |
| 13 | Deviation | WCAG-3.3.2 | WCAG 2.2 SC 3.3.2 (Level A) | page | `signup.html:34`; `styles.css:249` | "Full name (required)" exists only as a placeholder. It disappears as soon as the user types, so the label and the "required" note are no longer visible. The placeholder is also low contrast (#aaaaaa), which is a 1.4.3 issue outside scope. Browsers do compute a name from the placeholder, so 4.1.2 is met. | `<input id="full-name" placeholder="Full name (required)">` with no `<label>` | Add `<label for="full-name">Full name (required)</label>` and remove the placeholder. |
| 14 | Deviation | WCAG-4.1.3 | WCAG 2.2 SC 4.1.3 (Level AA) | script | `app.js:24-28` | Toggling the sort order reverses the result list with no announcement. Only the toggle's own text changes, and because of #8 it isn't exposed as a control. A screen-reader test is needed to confirm whether anything is announced. | `flip()` reorders `.results` and does not update any live region. | After sorting, write e.g. "Sorted by title, Z to A" into the `role="status"` region from #12. |
| 15 | Advisory | WCAG-3.3.9 | WCAG 2.2 SC 3.3.9 (Level AAA) | page | `login.html:45-53` | The picture CAPTCHA ("select every picture that shows a book") relies on the object-recognition exception. That exception is allowed at AA but not at AAA. | Image checkboxes are labelled "CAPTCHA picture 1–4". | Consider a non-cognitive check instead, such as a honeypot, rate limiting, or a passkey or email link. |
| 16 | Advisory | WCAG-3.2.5 | WCAG 2.2 SC 3.2.5 (Level AAA) | page | `events.html:6` | The page reloads every 120 s, which is a change of context the user did not request. It also wipes any partly completed reservation form. | `<meta http-equiv="refresh" content="120">` | Remove the refresh. Update the schedule on request or via a user-controlled "Refresh" button. (It is also a 2.2.1 issue; see below.) |

## SC coverage

| SC | Level | Status | Notes |
|---|---|---|---|
| 3.1.1 Language of Page | A | **Fail** | #1 |
| 3.1.2 Language of Parts | AA | Pass | No passages in other languages found in any page or component. |
| 3.2.1 On Focus | A | Pass | No focus handlers change context. The modal opens on click (`app.js:81`). |
| 3.2.2 On Input | A | Pass | No `change`/`input` handlers. Forms submit only via buttons. |
| 3.2.3 Consistent Navigation | AA | Pass | The main nav is identical and in the same order on all 5 pages. The help-bar move is recorded under 3.2.6. |
| 3.2.4 Consistent Identification | AA | Pass | Repeated components ("Reserve a seat", nav, "Ask a Librarian") are labelled consistently. |
| 3.2.6 Consistent Help | A | **Fail** | #2 |
| 3.3.1 Error Identification | A | **Fail** | #3 |
| 3.3.2 Labels or Instructions | A | **Fail** | #4, #13 |
| 3.3.3 Error Suggestion | AA | **Fail** | #3 |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | Not evaluated | Review note 1 |
| 3.3.7 Redundant Entry | A | **Fail** | #5 |
| 3.3.8 Accessible Authentication (Minimum) | AA | **Fail** | #6. The CAPTCHA itself passes under the object-recognition exception (#15). |
| 4.1.1 Parsing | — | Obsolete | Removed in WCAG 2.2. Not assessed. |
| 4.1.2 Name, Role, Value | A | **Fail** | #4, #7, #8, #9, #10, #11 |
| 4.1.3 Status Messages | AA | **Fail** | #12, #14 |

The "Pass" results come from static reading of the markup and JS only. They should be rechecked in a rendered browser.

## Review notes

1. **3.3.4:** Creating a library card (`signup.html:30-71`) may count as a legal commitment if the card terms make the holder liable for lost items or fees. If so, the form needs a review, confirm or reverse step before "Create my card". Currently there is none, and step 2 submits directly to `login.html`. The event reservation (`events.html:86-101`) is a free booking and probably falls outside 3.3.4, but its "Confirm" button just closes the modal with no confirmation (`events.html:99`).
2. **3.3.8, CAPTCHA:** The picture task counts as object recognition, which is excepted at AA. The "audio check instead" (`app.js:117-119`) only reveals text instructions and plays no audio. That is a 1.1.1 alternative issue outside this scope, but it means the alternative route doesn't work.
3. **React sources:** The comments say the `src/components/*.jsx` files are "not built". I reported their defects alongside the matching static HTML. If they are ever shipped, the same fixes apply: SearchBar (#4, #7), BookCard (#9), Modal (#10). `Modal.jsx:12-19` also repeats the keyboard trap noted below.

## Manual checks required

- A screen-reader smoke test (e.g. NVDA with Firefox and VoiceOver with Safari) to confirm:
  - the names and roles in #4 and #7–#11;
  - that #12 is not announced today and is announced after the fix;
  - the behaviour in #14;
  - that `events.html` is spoken with the wrong voice before the fix for #1.
- Rendered checks of all "Pass" statuses in 3.2.x, including responsive variants. At ≤640 px the header stops being sticky, but the help-bar order is unchanged.
- A decision by the library on 3.3.4 (review note 1).

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs` / axe-core and `wcag_audit.py` were not run because there is no shell.
- **Outside scope (Principles 1–2), not evaluated, but noticed.** Several of these are serious:
  - **Non-interference:** the reservation modal traps the keyboard. Tab always returns to `#res-name`, Escape is suppressed, and the close control can't be focused (`app.js:83-92`, `Modal.jsx:12-19`). This is 2.1.2, which applies even to content not relied upon.
  - **Non-interference:** the carousel auto-advances with no pause control (`app.js:14-17`, `Carousel.jsx:7-12`). This is 2.2.2.
  - Meta refresh on the events page (`events.html:6`): 2.2.1.
  - The reading list can only be reordered by dragging (`catalog.html:81-87`): 2.1.1 / 2.5.7.
  - The "Add to reading list" divs can't be reached by keyboard: 2.1.1.
  - Positive `tabindex` values on login (`login.html:37,40`): 2.4.3.
  - `.site-nav a:focus { outline:none }` (`styles.css:59`): 2.4.7.
  - The catalog page has no `<title>`: 2.4.2.
  - Cover images have no `alt` (`catalog.html:38,46,54,62`), and the decorative flourish has descriptive alt text (`index.html:30`): 1.1.1.
  - Contrast problems: the logo text (#c9b6ef on white), `.event-meta` (#999) and the sign-up input borders (#d6d6d6): 1.4.3 / 1.4.11.
  - 16 px pager targets (`styles.css:160-165`): 2.5.8.
  - Fixed 240 px grid columns: 1.4.10.
  - Fixed-size `.btn-fixed` buttons: 1.4.12.
  - "Click here" (`events.html:32`): 2.4.4.
  - `h2` → `h4` skip (`index.html:78`): 1.3.1.

## Assumptions

- The pages are served as written, with `app.js` as the only script. The JSX sources are not deployed.
- No assistive technology or browser was used. Every finding comes from reading the source and JS behaviour.
- The report follows WCAG 2.2, where 4.1.1 is obsolete. Policies that cite WCAG 2.0 or 2.1 (Section 508, EN 301 549) would still need 4.1.1 assessed.

## Reproduction

With a shell available, run:
```bash
S=~/.claude/skills/wcag22-a11y/scripts
bash $S/setup_page_runner.sh
python3 $S/wcag_audit.py . --url . --pages 5 --out report.md --json merged.json
```
Expected tool signal:
- axe `html-has-lang` on `events.html`;
- `button-name` and `label` on `catalog.html`;
- `aria-roles` for `role="buton"`;
- `aria-hidden-focus` on `index.html`.

Then walk the manual checks listed above.
